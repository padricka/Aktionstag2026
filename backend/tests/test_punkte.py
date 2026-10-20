"""Punktevergabe (GAME_DESIGN.md, Abschnitt „Punkte“).

  9 Minuten Startzeit. Der Server brennt: alle 3 s kostet das Feuer 1 Leben, Fehler −60
  (feat/zeit-und-feuer). Läuft die Zeit ab, fallen die Leben auf 0 (Niederlage).

  Endpunkte = restliche Leben                         (Basiswert)
            + Aufgabenpunkte je gelöster Aufgabe      (200 / 250 / 300, Finale 0)
              ×2, wenn innerhalb des Zeitlimits gelöst (1:30 / 2:30 / 3:30 ab Aufgabenstart)
            + Restzeit in Sekunden                    (nur bei Sieg)
            − 50 je geöffneter Hilfe-Notiz
  nie unter 0. Der ×2 ist für die Spieler unsichtbar (kein score_gain in input_result).
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, TASK_POINTS, FAST_LIMIT, HINT_COST, MISTAKE_DAMAGE, TIME_BONUS, FIRE_EVERY
from backend.redis_handler import DEFAULT_TIME
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "punkte_session"
M, V, R = "Anna", "Ben", "Celim"


class Uhr:
    """Steuerbare Uhr fürs DataCenter (dc._now)."""
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


@pytest.fixture
def uhr():
    return Uhr()


@pytest.fixture
def dc(uhr):
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        center._now = uhr
        for name, role in ((M, ROLE_M), (V, ROLE_P1), (R, ROLE_P2)):
            center.redis.r.hset(center.redis._k_players(GAME), name, json.dumps({"name": name, "role": role}))
        center.start()
        yield center


def _eingabe(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _state(dc):
    return dc.current_task()["state"]


def _loese(dc):
    """Löst die aktuelle Aufgabe direkt aus ihrem Stand (Regeln: jeweilige Task-Tests)."""
    kind, st = dc.current_task()["kind"], _state(dc)
    if kind == "alarm":
        _eingabe(dc, V, "main_switch", st["target_symbol"])
        return _eingabe(dc, M, "shutdown_cmd", ",".join(st["solution"]))
    if kind == "fire_protocol":
        for s in st["sequence"]:
            _eingabe(dc, V, "valve_action", f"{s['rack']}:{s['agent']}")
        _eingabe(dc, M, "release", "press")
        return _eingabe(dc, R, "release", "press")
    if kind == "data_rescue":
        _eingabe(dc, R, "mount_disk", st["serial"])
        _eingabe(dc, V, "terminal_login", st["login"])
        return _eingabe(dc, V, "rescue_word", st["word"])
    if kind == "repair":
        # Finale: Teile weitergeben, je Platz Wartung an → einbauen → Wartung aus, drei Schlüssel
        _eingabe(dc, M, "give", "disk:FI-SI")
        _eingabe(dc, M, "give", "fan:FI-SI")
        _eingabe(dc, M, "give", "psu:FI-AE")
        for platz, wer, ziel, wert in (
            (f"bay:{st['disk_bay'] - 1}", V, "install_disk", str(st["disk_bay"])),
            (f"fan:{st['fan_slot'] - 1}", V, "install_fan", f"{st['fan_slot']}:{st['fan_dir']}"),
            (f"psu:{st['psu_bay'] - 1}", R, "install_psu", f"{st['psu_bay']}:{st['volt']}"),
        ):
            _eingabe(dc, M, "maintenance", platz)
            _eingabe(dc, wer, ziel, wert)
            _eingabe(dc, M, "maintenance", platz)
        _eingabe(dc, R, "key", "strom")
        _eingabe(dc, V, "key", "kuehlung")
        return _eingabe(dc, M, "key", "system")
    raise AssertionError(kind)


# ------------------------------------------------------------------ Leben und Zeit
def test_round_lasts_nine_minutes_and_solving_gives_a_minute():
    """feat/zeit-und-feuer: 9 Minuten Startzeit, +60 s pro gelöster Aufgabe."""
    assert DEFAULT_TIME == 540
    assert TIME_BONUS == 60
    assert FIRE_EVERY == 3


def test_the_fire_costs_one_life_every_three_seconds(dc):
    for _ in range(9):
        dc.tick()
    assert dc.time_left == DEFAULT_TIME - 9
    assert dc.health == dc.max_health - 3


def test_the_fire_can_burn_the_server_down(dc):
    dc.redis.r.hset(dc._key, "health", 1)
    for _ in range(FIRE_EVERY):
        dc.tick()
    assert dc.health == 0
    assert dc.status == "game_over"


def test_fire_count_starts_fresh_each_round(dc):
    for _ in range(FIRE_EVERY - 1):
        dc.tick()
    dc.start()
    dc.tick()
    assert dc.health == dc.max_health


def test_time_running_out_sets_lives_to_zero(dc):
    dc.redis.r.hset(dc._key, "time_left", 1)
    snap = dc.tick()
    assert snap["time_left"] == 0
    assert snap["health"] == 0
    assert dc.status == "game_over"


def test_mistakes_still_cost_lives(dc):
    _eingabe(dc, V, "main_switch", "gibtsnicht")
    assert dc.health == dc.max_health - MISTAKE_DAMAGE


# ------------------------------------------------------------------ Aufgabenpunkte und ×2
def test_points_and_limits_per_task():
    assert TASK_POINTS == {"alarm": 200, "fire_protocol": 250, "data_rescue": 300, "repair": 0}
    assert FAST_LIMIT == {"alarm": 90, "fire_protocol": 150, "data_rescue": 210}


@pytest.mark.parametrize("kind", ["alarm", "fire_protocol", "data_rescue"])
def test_fast_solve_doubles_the_task_points(dc, uhr, kind):
    dc.new_task(kind)
    uhr.t += FAST_LIMIT[kind]                      # genau auf der Grenze zählt noch
    _loese(dc)
    assert dc.task_points == 2 * TASK_POINTS[kind]


@pytest.mark.parametrize("kind", ["alarm", "fire_protocol", "data_rescue"])
def test_slow_solve_gives_the_plain_task_points(dc, uhr, kind):
    dc.new_task(kind)
    uhr.t += FAST_LIMIT[kind] + 1
    _loese(dc)
    assert dc.task_points == TASK_POINTS[kind]


def test_timer_starts_when_the_task_starts(dc, uhr):
    """Zeit der vorigen Aufgabe zählt nicht: Aufgabe 2 hat ihr eigenes Limit."""
    uhr.t += 80
    _loese(dc)                                     # Aufgabe 1 schnell
    uhr.t += 140
    _loese(dc)                                     # Aufgabe 2: 140 s seit ihrem Start → schnell
    assert dc.task_points == 2 * 200 + 2 * 250


def test_finale_gives_no_task_points(dc):
    for _ in range(3):
        _loese(dc)
    vorher = dc.task_points
    _loese(dc)
    assert dc.status == "won"
    assert dc.task_points == vorher


def test_double_is_invisible_to_players(dc):
    _eingabe(dc, V, "main_switch", _state(dc)["target_symbol"])
    res = _eingabe(dc, M, "shutdown_cmd", ",".join(_state(dc)["solution"]))
    assert res["result"] == "correct"
    assert "score_gain" not in res


def test_skipping_in_dev_mode_gives_no_points(dc):
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    dc.skip_task()
    assert dc.task_points == 0


# ------------------------------------------------------------------ Endpunkte
def test_score_while_running_is_lives_plus_task_points_minus_hints(dc, uhr):
    _eingabe(dc, V, "main_switch", "gibtsnicht")      # −60 Leben
    uhr.t += 10
    _loese(dc)                                         # +400 (schnell), +15 Leben
    dc.open_hint("probe")                              # −50 (jetzt läuft Aufgabe 2)
    leben = dc.health
    assert leben == dc.max_health - MISTAKE_DAMAGE + 15
    assert dc.snapshot()["score"] == leben + 400 - HINT_COST


def test_victory_adds_the_remaining_time(dc, uhr):
    for _ in range(4):
        uhr.t += 30
        _loese(dc)
    snap = dc.snapshot()
    assert dc.status == "won"
    erwartet = dc.health + (400 + 500 + 600) + snap["time_left"]
    assert snap["score"] == erwartet


def test_defeat_keeps_task_points_but_no_lives_and_no_time(dc, uhr):
    uhr.t += 10
    _loese(dc)                                         # +400
    dc.redis.r.hset(dc._key, "time_left", 1)
    dc.tick()                                          # Zeit abgelaufen → Leben 0
    snap = dc.snapshot()
    assert snap["health"] == 0
    assert snap["score"] == 400


def test_score_never_below_zero(dc):
    dc.redis.r.hset(dc._key, "health", 0)
    for thema in ("cable", "order", "symbols", "scratch"):
        dc.open_hint(thema)
    assert dc.snapshot()["score"] == 0


def test_time_bonus_still_applies(dc):
    dc.redis.r.hset(dc._key, "time_left", 100)
    _loese(dc)
    assert dc.time_left == 100 + TIME_BONUS


def test_leaderboard_gets_the_final_score(dc, uhr, tmp_path, monkeypatch):
    monkeypatch.setenv("LEADERBOARD_FILE", str(tmp_path / "lb.json"))
    uhr.t += 10
    _loese(dc)
    snap = dc.snapshot()
    board = dc.record_result("meltdown", snap)
    assert board["top"][0]["score"] == snap["score"]
