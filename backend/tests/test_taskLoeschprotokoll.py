"""Task 2 – Löschprotokoll (kind='fire_protocol'), Escape-Room-Variante.

Spezifikation: GAME_DESIGN.md, Abschnitt 4 „Aufgabe 2".

  Drei von vier Racks brennen. Gelöscht wird Rack für Rack mit dem richtigen
  Löschmittel, in der Reihenfolge der Brandmeldungen. Danach gibt die Anlage
  frei, wenn Leitstand und Rückseite (fast) gleichzeitig drücken.

  Leitstand  sieht das Brandmelde-Log (Uhrzeit, Quelle BMZ/RM, Rack, [TEST]).
  Vorderseite sieht, welches Rack unter Strom steht, und löscht (valve_action).
  Rückseite  sieht das Brandgut hinter jedem Rack.

  Löschplan, je Rolle ein Teil mit vollständigen Regeln (notes.FIRE_NOTE):
    ① (Leitstand)   Papier → WASSER, Kabel → SCHAUM, Server → INERTGAS;
                    unter Strom nie Wasser/Schaum → CO2; USV-Akku → ABSCHOTTEN
    ② (Vorderseite) älteste Meldung zuerst, [TEST]-Meldungen ignorieren
    ③ (Rückseite)   BMZ zeigt UTC, Rauchmelder (RM) Ortszeit = UTC + 2 h
    ④ (Rückseite)   Freigabe: Leitstand + Rückseite drücken innerhalb 3 s

Kernidee der Tests: Die Lösung entsteht NUR aus den drei Ansichten und den
Regeln (siehe _schritte_aus_ansichten).
"""
import json
from types import SimpleNamespace

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter
from backend.playableObject import FireProtocolTask, Outcome, ROLE_M, ROLE_P1, ROLE_P2

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


def _views(dc):
    return dc.snapshot()["tasks"][0]["views"]


def _view(dc, role):
    return _views(dc)[role]


# ------------------------------------------------------------------ Regeln (wie auf dem Löschplan)
def _utc_minuten(eintrag):
    """③ BMZ zeigt UTC, Rauchmelder (RM) Ortszeit = UTC + 2 h."""
    h, m = map(int, eintrag["time"].split(":"))
    minuten = h * 60 + m
    return minuten - 120 if eintrag["source"] == "RM" else minuten


def _reihenfolge(log):
    """② älteste Meldung zuerst, [TEST] ignorieren."""
    echte = [e for e in log if not e["test"]]
    return [e["rack"] for e in sorted(echte, key=_utc_minuten)]


def _mittel(material, strom):
    """① Löschmittel je Brandgut, Strom-Regel, Akku-Falle."""
    if material == "AKKU":
        return "ABSCHOTTEN"
    mittel = {"PAPIER": "WASSER", "KABEL": "SCHAUM", "SERVER": "INERTGAS"}[material]
    if strom and mittel in ("WASSER", "SCHAUM"):
        return "CO2"
    return mittel


def _schritte_aus_ansichten(views):
    log = views[ROLE_M]["log"]
    strom = views[ROLE_P1]["power"]
    brandgut = {r["rack"]: r["material"] for r in views[ROLE_P2]["rear"]}
    return [f"{rack}:{_mittel(brandgut[rack], strom[rack])}" for rack in _reihenfolge(log)]


def _loeschen(dc):
    for eingabe in _schritte_aus_ansichten(_views(dc)):
        assert _press(dc, P1_NAME, "valve_action", eingabe)["result"] == "correct", eingabe


def _runden(n=300):
    for _ in range(n):
        st = FireProtocolTask.create({})
        yield st, FireProtocolTask.views(st)


# ------------------------------------------------------------------ Ansichten
def test_every_role_has_its_own_view_type(dc):
    assert dc.current_task()["kind"] == "fire_protocol"
    assert _view(dc, ROLE_M)["type"] == "fire_log"
    assert _view(dc, ROLE_P1)["type"] == "valve_panel"
    assert _view(dc, ROLE_P2)["type"] == "rack_rear"


def test_every_role_has_its_part_of_the_loeschplan(dc):
    teile = {r: _view(dc, r)["note"] for r in (ROLE_M, ROLE_P1, ROLE_P2)}
    assert {n["title"] for n in teile.values()} == {"Löschplan"}
    assert (teile[ROLE_M]["part"], teile[ROLE_P1]["part"], teile[ROLE_P2]["part"]) == (1, 2, 3)


def test_each_role_sees_only_its_own_facts(dc):
    """Log nur am Leitstand, Strom nur vorne, Brandgut nur hinten – nirgends die Lösung."""
    m, p1, p2 = (_view(dc, r) for r in (ROLE_M, ROLE_P1, ROLE_P2))
    assert "log" in m and "power" not in m and "rear" not in m
    assert "power" in p1 and "log" not in p1 and "rear" not in p1
    assert "rear" in p2 and "log" not in p2 and "power" not in p2
    for view in (m, p1, p2):
        for verboten in ("sequence", "solution", "fires", "material"):
            assert verboten not in view


def test_vorderseite_panel_has_all_racks_and_agents(dc):
    vorne = _view(dc, ROLE_P1)
    assert vorne["racks"] == FireProtocolTask.RACKS
    assert vorne["agents"] == FireProtocolTask.AGENTS
    assert set(vorne["power"]) == set(FireProtocolTask.RACKS)
    assert vorne["sequence_len"] == 3 and vorne["step"] == 0 and vorne["p_done"] is False


def test_rueckseite_sees_material_behind_every_rack(dc):
    hinten = _view(dc, ROLE_P2)["rear"]
    assert [r["rack"] for r in hinten] == FireProtocolTask.RACKS
    assert all(r["material"] in FireProtocolTask.MATERIALS and r["label"] for r in hinten)


def test_public_snapshot_hides_raw_state(dc):
    assert "state" not in dc.snapshot()["tasks"][0]


# ------------------------------------------------------------------ Log
def test_log_reports_three_burning_racks_plus_a_probealarm(dc):
    log = _view(dc, ROLE_M)["log"]
    echte = [e for e in log if not e["test"]]
    assert len(echte) == 3
    assert len({e["rack"] for e in echte}) == 3
    assert any(e["test"] for e in log)
    for e in log:
        assert e["rack"] in FireProtocolTask.RACKS
        assert e["source"] in ("BMZ", "RM")


def test_log_is_sorted_by_shown_time_like_a_naive_viewer(dc):
    zeiten = [e["time"] for e in _view(dc, ROLE_M)["log"]]
    assert zeiten == sorted(zeiten)


def test_timezone_rule_always_matters():
    """Wer die angezeigten Zeiten direkt vergleicht (ohne ③), löscht falsch."""
    for _, views in _runden():
        log = views[ROLE_M]["log"]
        naiv = [e["rack"] for e in log if not e["test"]]   # Log ist nach angezeigter Zeit sortiert
        assert naiv != _reihenfolge(log)


def test_power_rule_always_matters():
    """Mindestens ein Rack unter Strom hat Papier/Kabel – „Wasser geht immer“ ist falsch."""
    for st, views in _runden():
        strom = views[ROLE_P1]["power"]
        brandgut = {r["rack"]: r["material"] for r in views[ROLE_P2]["rear"]}
        brennend = _reihenfolge(views[ROLE_M]["log"])
        assert any(strom[r] and brandgut[r] in ("PAPIER", "KABEL") for r in brennend)


def test_rules_give_the_solution_in_every_variant():
    akku_gesehen = set()
    for st, views in _runden():
        erwartet = [f"{s['rack']}:{s['agent']}" for s in st["sequence"]]
        assert _schritte_aus_ansichten(views) == erwartet
        akku_gesehen.add(any(s["agent"] == "ABSCHOTTEN" for s in st["sequence"]))
    assert akku_gesehen == {True, False}     # die Akku-Falle kommt vor, aber nicht immer


# ------------------------------------------------------------------ Löschen
def test_extinguishing_with_the_rules_floods_but_does_not_solve(dc):
    task_id = dc.current_task()["task_id"]
    _loeschen(dc)
    assert dc.current_task()["task_id"] == task_id     # Freigabe fehlt noch
    assert _view(dc, ROLE_P1)["p_done"] is True
    assert _view(dc, ROLE_P1)["step"] == 3


def test_wrong_order_costs_health(dc):
    schritte = _schritte_aus_ansichten(_views(dc))
    assert _press(dc, P1_NAME, "valve_action", schritte[1])["result"] == "wrong"
    assert dc.health == 240


def test_ignoring_the_power_rule_costs_health(dc):
    views = _views(dc)
    strom = views[ROLE_P1]["power"]
    brandgut = {r["rack"]: r["material"] for r in views[ROLE_P2]["rear"]}
    for eingabe in _schritte_aus_ansichten(views):
        rack = eingabe.split(":")[0]
        if strom[rack] and brandgut[rack] in ("PAPIER", "KABEL"):
            ohne_strom_regel = f"{rack}:{_mittel(brandgut[rack], False)}"
            assert _press(dc, P1_NAME, "valve_action", ohne_strom_regel)["result"] == "wrong"
            assert dc.health == 240
            return
        assert _press(dc, P1_NAME, "valve_action", eingabe)["result"] == "correct"
    pytest.fail("Strom-Regel kam nicht vor")


def test_unknown_rack_or_agent_costs_health(dc):
    assert _press(dc, P1_NAME, "valve_action", "Z-99:LIMONADE")["result"] == "wrong"
    assert _press(dc, P1_NAME, "valve_action", "kaputt")["result"] == "wrong"
    assert dc.health == 180


def test_input_is_case_insensitive(dc):
    erster = _schritte_aus_ansichten(_views(dc))[0]
    assert _press(dc, P1_NAME, "valve_action", erster.lower())["result"] == "correct"


# ------------------------------------------------------------------ Vier-Augen-Freigabe
def test_release_is_armed_only_after_extinguishing(dc):
    assert _view(dc, ROLE_M)["release"] == {"armed": False, "window": 3}
    assert _press(dc, MASTER_NAME, "release", "press")["result"] == "ignored"
    assert dc.health == 300
    _loeschen(dc)
    assert _view(dc, ROLE_M)["release"]["armed"] is True
    assert _view(dc, ROLE_P2)["release"]["armed"] is True


def test_both_pressing_releases_and_solves(dc):
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    _loeschen(dc)

    assert _press(dc, MASTER_NAME, "release", "press")["result"] == "correct"
    assert dc.current_task()["task_id"] == task_id            # einer allein reicht nicht
    res = _press(dc, P2_NAME, "release", "press")

    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] != task_id
    assert dc.health == 115


def _geloescht():
    st = FireProtocolTask.create({})
    st["step"] = len(st["sequence"])
    st["p1_done"] = True
    return st


def _freigabe(st, role, now):
    data = SimpleNamespace(target="release", value="press")
    return FireProtocolTask.handle_input(st, "x", role, data, now)


def test_release_within_window_solves():
    st = _geloescht()
    assert _freigabe(st, ROLE_P2, 100.0).outcome is Outcome.PROGRESS
    assert _freigabe(st, ROLE_M, 103.0).outcome is Outcome.SOLVED


def test_release_too_late_starts_over():
    st = _geloescht()
    assert _freigabe(st, ROLE_M, 100.0).outcome is Outcome.PROGRESS
    assert _freigabe(st, ROLE_P2, 103.5).outcome is Outcome.PROGRESS   # zu spät: neuer erster Druck
    assert _freigabe(st, ROLE_M, 105.0).outcome is Outcome.SOLVED      # passt zum Druck von 103.5


def test_same_role_twice_does_not_release():
    st = _geloescht()
    assert _freigabe(st, ROLE_M, 100.0).outcome is Outcome.PROGRESS
    assert _freigabe(st, ROLE_M, 101.0).outcome is Outcome.PROGRESS


# ------------------------------------------------------------------ Rollen
def test_only_vorderseite_extinguishes(dc):
    erster = _schritte_aus_ansichten(_views(dc))[0]
    assert _press(dc, MASTER_NAME, "valve_action", erster)["result"] == "ignored"
    assert _press(dc, P2_NAME, "valve_action", erster)["result"] == "ignored"
    assert dc.health == 300


def test_vorderseite_cannot_release(dc):
    _loeschen(dc)
    assert _press(dc, P1_NAME, "release", "press")["result"] == "ignored"
    assert dc.health == 300


def test_extinguishing_after_done_is_ignored(dc):
    _loeschen(dc)
    erster = _schritte_aus_ansichten(_views(dc))[0]
    assert _press(dc, P1_NAME, "valve_action", erster)["result"] == "ignored"
