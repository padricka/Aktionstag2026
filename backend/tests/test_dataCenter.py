# test_dataCenter.py
import json
import pytest
import fakeredis
from unittest.mock import patch
from backend.dataCenter import DataCenter
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "test_session"


@pytest.fixture
def data_center():
    fake_redis = fakeredis.FakeStrictRedis()
    fake_redis.flushall()   # sauberer Zustand pro Test

    with patch("backend.redis_handler.redis.Redis", return_value=fake_redis):
        dc = DataCenter(game_id=GAME)
        yield dc


@pytest.fixture
def button_game(data_center):
    """Gestartetes Spiel mit festem Button-Task (statt zufälliger Task-Art)."""
    data_center.start()
    data_center.new_task("button")
    return data_center


def _state_key(dc):
    return dc.redis._k_state(GAME)


def _register(dc, name, role):
    dc.redis.r.hset(dc.redis._k_players(GAME), name, json.dumps({"name": name, "role": role}))


def _druecke(dc, target, value, spieler="Patrick"):
    return dc.process_input(spieler, {
        "action_type": "button_press", "target": target, "value": value,
    })


# ---------------------------------------------------------------- Grundlagen
def test_data_center_initialization(data_center):
    """Neu angelegt: volle Health, Status 'waiting' bis das Spiel startet."""
    assert data_center.health == 300
    assert data_center.status == "waiting"


def test_start_sets_status_running(data_center):
    """start() setzt waiting -> running."""
    data_center.start()
    assert data_center.status == "running"


def test_claim_game_over_only_once(data_center):
    """Spielende darf nur einmal gemeldet werden (Consumer und Spielschleife)."""
    data_center.start()
    assert data_center.claim_game_over() is True
    assert data_center.claim_game_over() is False


def test_start_resets_game_over_claim(data_center):
    data_center.start()
    data_center.claim_game_over()
    data_center.start()
    assert data_center.claim_game_over() is True


def test_register_mistake_reduces_health(data_center):
    data_center.register_mistake()
    assert data_center.health == 240


def test_multiple_cumulative_mistakes(data_center):
    data_center.register_mistake()
    data_center.register_mistake()
    assert data_center.health == 180


def test_health_reaches_game_over(data_center):
    for _ in range(5):
        data_center.register_mistake()
    assert data_center.health == 0
    assert data_center.status == "game_over"


def test_health_over_zero(data_center):
    for _ in range(6):
        data_center.register_mistake()
    assert data_center.health == 0
    assert data_center.status == "game_over"


# ---------------------------------------------------------------- Start + Tick
def test_tick_reduces_health_in_redis(data_center):
    data_center.start()
    data_center.tick()
    assert data_center.health == 299


def test_tick_snapshot_matches_contract(button_game):
    """Snapshot: health, time_left, tasks. Button-Task ohne target/value/state/views."""
    snap = button_game.tick()

    assert {"health", "time_left", "tasks"} <= set(snap)
    assert snap["time_left"] == 299
    assert set(snap["tasks"][0]) == {"task_id", "assigned_to_player", "instruction"}


def test_tick_to_zero_health_sets_game_over(data_center):
    data_center.start()
    data_center.redis.r.hset(_state_key(data_center), "health", 1)

    snap = data_center.tick()

    assert snap["health"] == 0
    assert data_center.status == "game_over"


# ---------------------------------------------------------------- Button-Task / player_input
def test_correct_input_clears_task_and_heals(button_game):
    """Richtiger Input: Task wird ersetzt, +15 HP."""
    task = button_game.current_task()
    button_game.redis.r.hset(_state_key(button_game), "health", 100)

    res = _druecke(button_game, task["state"]["target"], task["state"]["value"])

    assert res["result"] == "correct"
    assert button_game.health == 115
    assert button_game.current_task()["task_id"] != task["task_id"]


def test_correct_input_health_is_capped_at_max(button_game):
    task = button_game.current_task()
    button_game.redis.r.hset(_state_key(button_game), "health", 295)

    _druecke(button_game, task["state"]["target"], task["state"]["value"])

    assert button_game.health == 300


def test_wrong_input_costs_health_and_keeps_task(button_game):
    task = button_game.current_task()

    assert _druecke(button_game, "nope", "nope")["result"] == "wrong"
    assert button_game.health == 240
    assert button_game.current_task()["task_id"] == task["task_id"]


def test_input_before_start_is_rejected(data_center):
    assert _druecke(data_center, "reactor_vent", "open")["result"] == "error"
    assert data_center.health == 300


def test_invalid_payload_is_error_not_a_mistake(button_game):
    res = button_game.process_input("Patrick", {"action_type": "unbekannt"})

    assert res["result"] == "error"
    assert button_game.health == 300


# ---------------------------------------------------------------- Rollen-Tasks
def test_role_task_hides_state_but_sends_views(data_center):
    """Task mit Rollen: Lösung (state) bleibt geheim, views gehen raus."""
    data_center.start()
    data_center.new_task("fire_protocol")

    pub = data_center.snapshot()["tasks"][0]

    assert "state" not in pub
    assert set(pub["views"]) == {ROLE_M, ROLE_P1, ROLE_P2}


def test_fire_protocol_flow_via_process_input(data_center):
    """P1 macht alle 3 Schritte, P2 gibt das Passwort in der Order ein."""
    data_center.start()
    _register(data_center, "Anna", ROLE_P1)
    _register(data_center, "Ben", ROLE_P2)
    task = data_center.new_task("fire_protocol")
    st = task["state"]
    data_center.redis.r.hset(_state_key(data_center), "health", 100)
    data_center.redis.r.hset(_state_key(data_center), "time_left", 100)

    # P1: falsche Kombination kostet HP
    assert _druecke(data_center, "valve_action", "V9:lila", "Anna")["result"] == "wrong"
    assert data_center.health == 40

    # P1: alle 3 Schritte korrekt
    for step in st["sequence"]:
        res = _druecke(data_center, "valve_action", f"{step['valve']}:{step['color']}", "Anna")
        assert res["result"] == "correct"

    # P2: richtiges Passwort
    # Passwort = alle Fragmente nach Punkten sortiert (Escape-Room, GAME_DESIGN.md)
    pw = "".join(f["text"] for f in sorted(st["fragments"], key=lambda f: f["dots"]))
    assert _druecke(data_center, "release_pw", pw, "Ben")["result"] == "correct"
    assert data_center.current_task()["task_id"] != task["task_id"]
    assert data_center.health == 55

def test_wrong_role_is_ignored(data_center):
    """Falsche Rolle für das Target: ignored, keine Strafe."""
    data_center.start()
    _register(data_center, "Ben", ROLE_P2)
    data_center.new_task("fire_protocol")
    hp = data_center.health

    assert _druecke(data_center, "valve_action", "V1:rot", "Ben")["result"] == "ignored"
    assert data_center.health == hp


# ---------------------------------------------------------------- Randfälle
def test_finish_sets_game_over(data_center):
    data_center.start()
    data_center.finish()
    assert data_center.status == "game_over"


def test_unknown_task_kind_is_error_not_a_mistake(data_center):
    """Kaputter Task in Redis: Fehler, aber kein HP-Abzug für die Spieler."""
    data_center.start()
    data_center.redis.r.hset(_state_key(data_center), "task", json.dumps(
        {"task_id": "task-x", "kind": "gibt_es_nicht", "state": {}}
    ))

    assert _druecke(data_center, "reactor_vent", "open")["result"] == "error"
    assert data_center.health == 300


def test_input_without_active_task_counts_as_mistake(data_center):
    data_center.start()
    data_center.redis.r.hdel(_state_key(data_center), "task")

    assert _druecke(data_center, "reactor_vent", "open")["result"] == "wrong"
    assert data_center.health == 240


def test_solving_an_already_replaced_task_is_ignored(button_game, monkeypatch):
    """Zwei Spieler lösen gleichzeitig: wer zu spät kommt, bekommt 'ignored' und keinen zweiten Bonus."""
    task = button_game.current_task()
    button_game.redis.r.hdel(_state_key(button_game), "task")        # der andere war schneller
    button_game.redis.r.hset(_state_key(button_game), "health", 100)
    monkeypatch.setattr(button_game, "current_task", lambda: task)   # unser Spieler hat den alten Stand gelesen

    res = _druecke(button_game, task["state"]["target"], task["state"]["value"])

    assert res["result"] == "ignored"
    assert button_game.health == 100