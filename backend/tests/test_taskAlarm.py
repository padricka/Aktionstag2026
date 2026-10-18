"""Task 1 – Alarm verifizieren (kind='alarm'), Escape-Room-Variante.

Spezifikation: GAME_DESIGN.md, Abschnitt 4 „Aufgabe 1".

  Leitstand  (MASTER): sieht WELCHER Steckplatz brennt (ohne Beschriftung) und die
                       Farb-Reihenfolge des Codes. Tippt den Shutdown-Code.
  Vorderseite (FI-SI): sieht die Hauptschalter (Symbole in Steckplatz-Reihenfolge).
                       Drückt den Schalter des brennenden Steckplatzes.
  Rückseite  (FI-AE):  sieht die Code-Symbole auf farbigen Aufklebern, gemischt.
                       Hat keine Eingabe.

Kernidee der Tests: Die Lösung lässt sich NUR durch Kombinieren der drei
Ansichten herleiten (siehe _loesung_aus_ansichten), keine Ansicht allein reicht.
"""
import json
import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "t1_session"
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
        center.new_task("alarm")
        yield center


def _press(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _text(dc, name, target, value):
    return dc.process_input(name, {"action_type": "text_input", "target": target, "value": value})


def _view(dc, role):
    return dc.snapshot()["tasks"][0]["views"][role]


def _loesung_aus_ansichten(dc):
    """So lösen die Spieler die Aufgabe: nur mit dem, was sie auf ihren Bildschirmen sehen."""
    leitstand, vorne, hinten = _view(dc, ROLE_M), _view(dc, ROLE_P1), _view(dc, ROLE_P2)
    schalter = vorne["switches"][leitstand["burning_slot"] - 1]
    rang = {farbe: i for i, farbe in enumerate(leitstand["color_order"])}
    code = [s["symbol"] for s in sorted(hinten["stickers"], key=lambda s: rang[s["color"]])]
    return schalter, ",".join(code)


# ------------------------------------------------------------------ Ansichten
def test_every_role_has_its_own_view_type(dc):
    assert dc.current_task()["kind"] == "alarm"
    assert _view(dc, ROLE_M)["type"] == "alarm_leds"
    assert _view(dc, ROLE_P1)["type"] == "main_switches"
    assert _view(dc, ROLE_P2)["type"] == "code_stickers"


def test_leitstand_sees_burning_slot_and_color_order_but_no_symbols(dc):
    leitstand = _view(dc, ROLE_M)
    assert leitstand["slots"] == 4
    assert 1 <= leitstand["burning_slot"] <= 4
    assert len(leitstand["color_order"]) == 4
    assert len(set(leitstand["color_order"])) == 4
    # Keine Symbole, kein Code: allein kann der Leitstand nichts lösen.
    assert "switches" not in leitstand and "stickers" not in leitstand
    assert "code" not in leitstand and "symbol" not in leitstand


def test_vorderseite_sees_switches_but_not_which_one_burns(dc):
    vorne = _view(dc, ROLE_P1)
    assert len(vorne["switches"]) == 4
    assert "burning_slot" not in vorne
    assert "stickers" not in vorne and "color_order" not in vorne


def test_rueckseite_sees_all_code_symbols_with_colors_but_no_order(dc):
    leitstand, hinten = _view(dc, ROLE_M), _view(dc, ROLE_P2)
    stickers = hinten["stickers"]
    assert len(stickers) == 4
    assert {s["color"] for s in stickers} == set(leitstand["color_order"])
    assert len({s["symbol"] for s in stickers}) == 4
    assert "color_order" not in hinten and "code" not in hinten


def test_burning_slot_matches_the_switch_that_solves(dc):
    schalter, _ = _loesung_aus_ansichten(dc)
    assert _press(dc, P1_NAME, "main_switch", schalter)["result"] == "correct"


def test_public_snapshot_hides_raw_state(dc):
    assert "state" not in dc.snapshot()["tasks"][0]


def test_progress_flags_appear_in_views(dc):
    schalter, code = _loesung_aus_ansichten(dc)
    assert _view(dc, ROLE_P1)["p_done"] is False
    _press(dc, P1_NAME, "main_switch", schalter)
    assert _view(dc, ROLE_P1)["p_done"] is True
    assert _view(dc, ROLE_M)["p_done"] is False


# ------------------------------------------------------------------ Lösen
def test_solving_from_views_completes_task_and_heals(dc):
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    dc.redis.r.hset(dc.redis._k_state(GAME), "time_left", 100)
    schalter, code = _loesung_aus_ansichten(dc)

    assert _press(dc, P1_NAME, "main_switch", schalter)["result"] == "correct"
    assert dc.current_task()["task_id"] == task_id          # erst ein Teil gelöst
    res = _text(dc, MASTER_NAME, "shutdown_cmd", code)

    assert res["result"] == "correct"
    assert dc.health == 115
    assert dc.current_task()["task_id"] != task_id
    assert dc.score >= 100


def test_order_of_the_two_steps_does_not_matter(dc):
    task_id = dc.current_task()["task_id"]
    schalter, code = _loesung_aus_ansichten(dc)
    _text(dc, MASTER_NAME, "shutdown_cmd", code)
    res = _press(dc, P1_NAME, "main_switch", schalter)
    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] != task_id


def test_code_accepts_spaces(dc):
    _, code = _loesung_aus_ansichten(dc)
    assert _text(dc, MASTER_NAME, "shutdown_cmd", code.replace(",", ", "))["result"] == "correct"


def test_command_alone_does_not_solve(dc):
    task_id = dc.current_task()["task_id"]
    _, code = _loesung_aus_ansichten(dc)
    _text(dc, MASTER_NAME, "shutdown_cmd", code)
    assert dc.current_task()["task_id"] == task_id


def test_unsorted_sticker_order_is_wrong(dc):
    """Wer die Aufkleber nur abliest statt nach Farbe zu sortieren, liegt (fast immer) falsch."""
    _, code = _loesung_aus_ansichten(dc)
    abgelesen = ",".join(s["symbol"] for s in _view(dc, ROLE_P2)["stickers"])
    if abgelesen == code:
        pytest.skip("Zufall: Aufkleber liegen schon in der richtigen Reihenfolge")
    assert _text(dc, MASTER_NAME, "shutdown_cmd", abgelesen)["result"] == "wrong"


# ------------------------------------------------------------------ Fehler und Rollen
def test_wrong_switch_costs_health(dc):
    assert _press(dc, P1_NAME, "main_switch", "gibt-es-nicht")["result"] == "wrong"
    assert dc.health == 240


def test_wrong_command_costs_health(dc):
    assert _text(dc, MASTER_NAME, "shutdown_cmd", "FALSCH")["result"] == "wrong"
    assert dc.health == 240


def test_rueckseite_has_no_controls_in_this_task(dc):
    schalter, code = _loesung_aus_ansichten(dc)
    assert _press(dc, P2_NAME, "main_switch", schalter)["result"] == "ignored"
    assert _text(dc, P2_NAME, "shutdown_cmd", code)["result"] == "ignored"
    assert dc.health == 300


def test_each_control_belongs_to_exactly_one_role(dc):
    schalter, code = _loesung_aus_ansichten(dc)
    assert _press(dc, MASTER_NAME, "main_switch", schalter)["result"] == "ignored"
    assert _text(dc, P1_NAME, "shutdown_cmd", code)["result"] == "ignored"
    assert dc.health == 300


def test_wrong_attempts_do_not_block_solution(dc):
    task_id = dc.current_task()["task_id"]
    schalter, code = _loesung_aus_ansichten(dc)
    _press(dc, P1_NAME, "main_switch", "falsch")
    _text(dc, MASTER_NAME, "shutdown_cmd", "falsch")
    _press(dc, P1_NAME, "main_switch", schalter)
    res = _text(dc, MASTER_NAME, "shutdown_cmd", code)
    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] != task_id
