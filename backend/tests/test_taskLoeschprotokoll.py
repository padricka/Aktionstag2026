"""Task 2 – Löschprotokoll (kind='fire_protocol'), Escape-Room-Variante.

Spezifikation: GAME_DESIGN.md, Abschnitt 4 „Aufgabe 2".

  Jede Rolle kennt genau EINEN Schritt der 3-stufigen Ventil-Sequenz.
  Die Vorderseite (FI-SI) flutet, braucht dafür aber die Schritte der anderen.
  Das Passwort besteht aus 3 Fragmenten mit 1–3 Punkten; nach Punkten sortiert
  ergeben sie das Passwort. Leitstand und Rückseite haben je ein Fragment, das
  dritte erscheint erst nach dem Fluten. Die Rückseite (FI-AE) gibt es ein.

Kernidee der Tests: Die Lösung entsteht NUR aus den drei Ansichten
(siehe _sequenz_aus_ansichten / _passwort_aus_ansichten).
"""
import json
import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter
from backend.playableObject import *  # noqa
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "t2_session"
MASTER_NAME = "Anna"
P1_NAME = "Ben"
P2_NAME = "Celim"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in ((MASTER_NAME, ROLE_M), (P1_NAME, ROLE_P1), (P2_NAME, ROLE_P2)):
            center.redis.r.hset(
                center.redis._k_players(GAME),
                name,
                json.dumps({"name": name, "role": role}),
            )
        center.start()
        center.new_task("fire_protocol")
        yield center


def _press(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _text(dc, name, target, value):
    return dc.process_input(name, {"action_type": "text_input", "target": target, "value": value})


def _view(dc, role):
    return dc.snapshot()["tasks"][0]["views"][role]


def _sequenz_aus_ansichten(dc):
    """Alle drei lesen ihren Schritt vor, nach Schrittnummer sortiert."""
    clues = [_view(dc, r)["clue"] for r in (ROLE_M, ROLE_P1, ROLE_P2)]
    return [f"{c['valve']}:{c['color']}" for c in sorted(clues, key=lambda c: c["step"])]


def _fluten(dc):
    for eingabe in _sequenz_aus_ansichten(dc):
        assert _press(dc, P1_NAME, "valve_action", eingabe)["result"] == "correct"


def _passwort_aus_ansichten(dc):
    """Erst nach dem Fluten möglich: drei Fragmente, nach Punkten sortiert."""
    frags = [_view(dc, ROLE_M)["fragment"], _view(dc, ROLE_P2)["fragment"],
             _view(dc, ROLE_P2)["last_fragment"]]
    return "".join(f["text"] for f in sorted(frags, key=lambda f: f["dots"]))


# ------------------------------------------------------------------ Ansichten
def test_every_role_has_its_own_view_type(dc):
    assert dc.current_task()["kind"] == "fire_protocol"
    assert _view(dc, ROLE_M)["type"] == "fire_log"
    assert _view(dc, ROLE_P1)["type"] == "valve_panel"
    assert _view(dc, ROLE_P2)["type"] == "password_input"


def test_each_role_knows_exactly_one_different_step(dc):
    steps = [_view(dc, r)["clue"]["step"] for r in (ROLE_M, ROLE_P1, ROLE_P2)]
    assert sorted(steps) == [1, 2, 3]


def test_no_view_reveals_the_full_sequence_or_password(dc):
    for role in (ROLE_M, ROLE_P1, ROLE_P2):
        view = _view(dc, role)
        for verboten in ("sequence", "order", "password_preview", "fragments"):
            assert verboten not in view, f"{role} sieht {verboten}"


def test_vorderseite_has_panel_but_no_fragment_before_flooding(dc):
    vorne = _view(dc, ROLE_P1)
    assert vorne["valves"] and vorne["colors"]
    assert vorne["sequence_len"] == 3
    assert vorne["step"] == 0
    assert vorne["last_fragment"] is None
    assert "fragment" not in vorne


def test_fragments_carry_distinct_dots(dc):
    _fluten(dc)
    dots = [_view(dc, ROLE_M)["fragment"]["dots"], _view(dc, ROLE_P2)["fragment"]["dots"],
            _view(dc, ROLE_P2)["last_fragment"]["dots"]]
    assert sorted(dots) == [1, 2, 3]


def test_last_fragment_hidden_until_flooded(dc):
    assert _view(dc, ROLE_P2)["last_fragment"] is None
    _fluten(dc)
    assert _view(dc, ROLE_P1)["last_fragment"] == _view(dc, ROLE_P2)["last_fragment"]
    assert _view(dc, ROLE_P1)["last_fragment"]["text"]


def test_public_snapshot_hides_raw_state(dc):
    assert "state" not in dc.snapshot()["tasks"][0]


# ------------------------------------------------------------------ Fluten
def test_flooding_needs_all_three_steps_in_order(dc):
    task_id = dc.current_task()["task_id"]
    _fluten(dc)
    assert dc.current_task()["task_id"] == task_id     # Passwort fehlt noch
    assert _view(dc, ROLE_P1)["p_done"] is True
    assert _view(dc, ROLE_P1)["step"] == 3


def test_steps_in_wrong_order_cost_health(dc):
    seq = _sequenz_aus_ansichten(dc)
    if seq[0] == seq[1]:
        pytest.skip("Zufall: Schritt 1 und 2 sind identisch")
    assert _press(dc, P1_NAME, "valve_action", seq[1])["result"] == "wrong"
    assert dc.health == 240


def test_wrong_valve_costs_health(dc):
    assert _press(dc, P1_NAME, "valve_action", "V-99:LILA")["result"] == "wrong"
    assert dc.health == 240


def test_greek_valve_aliases_still_work(dc):
    """Das bestehende Ventilpanel sendet ALPHA/BETA/GAMMA statt V-31/32/33."""
    alias = {"V-31": "ALPHA", "V-32": "BETA", "V-33": "GAMMA"}
    erster = _sequenz_aus_ansichten(dc)[0]
    ventil, farbe = erster.split(":")
    assert _press(dc, P1_NAME, "valve_action", f"{alias[ventil]}:{farbe}")["result"] == "correct"


# ------------------------------------------------------------------ Passwort
def test_full_flow_from_views_solves_and_heals(dc):
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    dc.redis.r.hset(dc.redis._k_state(GAME), "time_left", 100)

    _fluten(dc)
    res = _text(dc, P2_NAME, "release_pw", _passwort_aus_ansichten(dc))

    assert res["result"] == "correct"
    assert dc.health == 115
    assert dc.current_task()["task_id"] != task_id
    assert dc.score >= 100


def test_password_accepts_separators(dc):
    _fluten(dc)
    frags = [_view(dc, ROLE_M)["fragment"], _view(dc, ROLE_P2)["fragment"],
             _view(dc, ROLE_P2)["last_fragment"]]
    mit_strichen = "-".join(f["text"] for f in sorted(frags, key=lambda f: f["dots"]))
    assert _text(dc, P2_NAME, "release_pw", mit_strichen.lower())["result"] == "correct"


def test_password_in_wrong_order_is_wrong(dc):
    _fluten(dc)
    richtig = _passwort_aus_ansichten(dc)
    frags = [_view(dc, ROLE_M)["fragment"], _view(dc, ROLE_P2)["fragment"],
             _view(dc, ROLE_P2)["last_fragment"]]
    falsch = "".join(f["text"] for f in sorted(frags, key=lambda f: -f["dots"]))
    if falsch == richtig:
        pytest.skip("Zufall: umgekehrte Reihenfolge ergibt dasselbe Wort")
    assert _text(dc, P2_NAME, "release_pw", falsch)["result"] == "wrong"
    assert dc.health == 240


def test_password_before_flooding_is_ignored(dc):
    assert _text(dc, P2_NAME, "release_pw", "egal")["result"] == "ignored"
    assert dc.health == 300


def test_wrong_password_costs_health(dc):
    _fluten(dc)
    assert _text(dc, P2_NAME, "release_pw", "FALSCH")["result"] == "wrong"
    assert dc.health == 240


# ------------------------------------------------------------------ Rollen
def test_leitstand_has_no_controls(dc):
    erster = _sequenz_aus_ansichten(dc)[0]
    assert _press(dc, MASTER_NAME, "valve_action", erster)["result"] == "ignored"
    assert _text(dc, MASTER_NAME, "release_pw", "x")["result"] == "ignored"
    assert dc.health == 300


def test_each_control_belongs_to_exactly_one_role(dc):
    erster = _sequenz_aus_ansichten(dc)[0]
    assert _press(dc, P2_NAME, "valve_action", erster)["result"] == "ignored"
    assert _text(dc, P1_NAME, "release_pw", "x")["result"] == "ignored"
    assert dc.health == 300
