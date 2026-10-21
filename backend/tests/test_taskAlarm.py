"""Task 1 – Alarm verifizieren (kind='alarm'), Escape-Room-Variante.

Spezifikation: GAME_DESIGN.md, Abschnitt 4 „Aufgabe 1".

  Leitstand  (MASTER): sieht WELCHER Steckplatz brennt (ohne Beschriftung), ob die LED
                       blinkt oder dauerhaft leuchtet, und die Farbfolge. Tippt den Code.
  Vorderseite (FI-SI): sieht die Kabel (Symbole in Steckplatz-Reihenfolge). Kappt eins.
  Rückseite  (FI-AE):  sieht die Code-Symbole auf farbigen Aufklebern, gemischt;
                       manchmal ist einer zerkratzt. Hat keine Eingabe.

Dazu hat jeder ein Stück der zerrissenen Wartungsnotiz mit den Regeln:
  ① Nie das Kabel des brennenden Platzes: gerade Nummer → links daneben,
    ungerade → rechts daneben.
  ② Code = Farbfolge; blinkt die LED → rückwärts.
  ③ Aufkleber zerkratzt → dort gilt das Symbol vom Kabel am Brandplatz.

Kernidee der Tests: Die Lösung lässt sich NUR durch Kombinieren der drei
Ansichten und der Regeln herleiten (siehe _loesung), keine Ansicht allein reicht.
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


def _loesung(leitstand, vorne, hinten):
    """So lösen die Spieler die Aufgabe: ihre Bildschirme + die zusammengelesenen Regeln."""
    platz = leitstand["burning_slot"]
    # ① nie das eigene Kabel: gerade Nummer → links daneben, ungerade → rechts daneben
    ziel = platz - 1 if platz % 2 == 0 else platz + 1
    kabel = vorne["switches"][ziel - 1]
    # ② Farbfolge, bei blinkender LED rückwärts
    folge = list(leitstand["color_order"])
    if leitstand["led"] == "blinkt":
        folge.reverse()
    # ③ zerkratzter Aufkleber → Symbol vom Kabel am Brandplatz
    am_brandplatz = vorne["switches"][platz - 1]
    symbol = {s["color"]: am_brandplatz if s.get("scratched") else s["symbol"] for s in hinten["stickers"]}
    return kabel, ",".join(symbol[f] for f in folge)


def _loesung_aus_ansichten(dc):
    return _loesung(_view(dc, ROLE_M), _view(dc, ROLE_P1), _view(dc, ROLE_P2))


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
    lesbar = [s["symbol"] for s in stickers if not s.get("scratched")]
    assert len(set(lesbar)) == len(lesbar) >= 3          # höchstens einer zerkratzt
    for s in stickers:
        if s.get("scratched"):
            assert s["symbol"] is None                    # zerkratzt = Symbol unlesbar
    assert "color_order" not in hinten and "code" not in hinten


def test_cable_from_views_and_note_solves(dc):
    # früher: test_burning_slot_matches_the_switch_that_solves – seit der
    # Wartungsnotiz (Regel ①) ist gerade NICHT das Kabel am Brandplatz richtig
    kabel, _ = _loesung_aus_ansichten(dc)
    assert _press(dc, P1_NAME, "main_switch", kabel)["result"] == "correct"


def test_cutting_the_burning_cable_itself_is_wrong(dc):
    """Regel ①: NIE das Kabel des brennenden Platzes."""
    platz = _view(dc, ROLE_M)["burning_slot"]
    eigenes = _view(dc, ROLE_P1)["switches"][platz - 1]
    assert _press(dc, P1_NAME, "main_switch", eigenes)["result"] == "wrong"


def test_led_state_is_only_on_the_leitstand(dc):
    assert _view(dc, ROLE_M)["led"] in ("blinkt", "leuchtet")
    assert "led" not in _view(dc, ROLE_P1) and "led" not in _view(dc, ROLE_P2)


def test_every_role_has_its_piece_of_the_note(dc):
    stuecke = [_view(dc, r)["note"] for r in (ROLE_M, ROLE_P1, ROLE_P2)]
    assert all(s["lines"] for s in stuecke)
    texte = [" ".join(z["text"] for z in s["lines"]) for s in stuecke]
    assert len(set(texte)) == 3                            # drei verschiedene Stücke


def test_rules_hold_in_every_variant():
    """Viele Runden: jede Variante (Platz, Blinken, Kratzer) ist mit den Regeln lösbar,
    und die alte Regel (Kabel am Brandplatz, Farbfolge vorwärts) scheitert, wo es darauf ankommt."""
    from backend.playableObject import AlarmTask
    from backend.schemas import PlayerInput

    gesehen = {"blinkt": 0, "leuchtet": 0, "kratzer": 0, "plaetze": set()}
    for _ in range(300):
        st = AlarmTask.create({})
        v = AlarmTask.views(st)
        kabel, code = _loesung(v[ROLE_M], v[ROLE_P1], v[ROLE_P2])

        def eingabe(rolle, ziel, wert, state):
            data = PlayerInput.model_validate({"action_type": "text_input", "target": ziel, "value": wert})
            return AlarmTask.handle_input(state, "x", rolle, data, 0).outcome.name

        assert eingabe(ROLE_P1, "main_switch", kabel, st) == "PROGRESS"
        assert eingabe(ROLE_M, "shutdown_cmd", code, st) == "SOLVED"

        alt = AlarmTask.create({})
        alt_v = AlarmTask.views(alt)
        platz = alt_v[ROLE_M]["burning_slot"]
        assert eingabe(ROLE_P1, "main_switch", alt_v[ROLE_P1]["switches"][platz - 1], alt) == "WRONG"

        gesehen[v[ROLE_M]["led"]] += 1
        gesehen["kratzer"] += any(s.get("scratched") for s in v[ROLE_P2]["stickers"])
        gesehen["plaetze"].add(v[ROLE_M]["burning_slot"])
    assert gesehen["blinkt"] and gesehen["leuchtet"] and gesehen["kratzer"]
    assert gesehen["plaetze"] == {1, 2, 3, 4}


def test_keyboard_has_every_symbol_the_code_can_need(dc):
    """Regel ③ setzt ein Kabel-Symbol in den Code – das muss man auch tippen können."""
    tastatur = set(_view(dc, ROLE_M)["keyboard"])
    assert set(_view(dc, ROLE_P1)["switches"]) <= tastatur


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
    abgelesen = ",".join(str(s["symbol"]) for s in _view(dc, ROLE_P2)["stickers"])
    if abgelesen == code:
        pytest.skip("Zufall: Aufkleber liegen schon in der richtigen Reihenfolge")
    assert _text(dc, MASTER_NAME, "shutdown_cmd", abgelesen)["result"] == "wrong"


# ------------------------------------------------------------------ Fehler und Rollen
def test_wrong_switch_costs_health(dc):
    assert _press(dc, P1_NAME, "main_switch", "gibt-es-nicht")["result"] == "wrong"
    assert dc.health == 270


def test_wrong_command_costs_health(dc):
    assert _text(dc, MASTER_NAME, "shutdown_cmd", "FALSCH")["result"] == "wrong"
    assert dc.health == 270


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


# ------------------------------------------------------------------ Tastatur kommt vom Backend
def test_leitstand_keyboard_contains_the_code_symbols(dc):
    """Die Tastatur gehört zum Rätsel: kommt aus dem Backend, enthält den Code plus Ablenker."""
    tastatur = _view(dc, ROLE_M)["keyboard"]
    code = dc.current_task()["state"]["code"]
    assert set(code) <= set(tastatur)
    assert len(tastatur) == 12 and len(set(tastatur)) == 12


def test_keyboard_does_not_reveal_the_code_by_position():
    """Die echten Symbole stehen nicht immer an denselben Stellen (sonst Lösung ablesbar)."""
    from backend.playableObject import AlarmTask
    vorne = set()
    for _ in range(30):
        state = AlarmTask.create({})
        vorne.add(frozenset(state["keyboard"][:4]))
    assert len(vorne) > 1


def test_solution_from_views_still_typeable_on_keyboard(dc):
    _, code = _loesung_aus_ansichten(dc)
    assert set(code.split(",")) <= set(_view(dc, ROLE_M)["keyboard"])
