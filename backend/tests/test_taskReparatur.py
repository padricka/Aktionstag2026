"""Finale – Server reparieren (kind="repair"), GAME_DESIGN.md „Finale“.

Die drei Teile aus den Fundorten werden eingebaut, dann fährt der Server mit drei
Schlüsseln hoch. Etiketten (Teilekiste) stammen aus parts_spec der Runde.

  Leitstand   gibt die Teile weiter (give "teil:ROLLE"), schaltet Plätze in der Konsole
              auf Wartung (maintenance "bay:0" / "fan:1" / "psu:0" – die Konsole zählt ab 0!),
              dreht zuletzt den Schlüssel „system“.
  Vorderseite sieht 4 Plattenschächte (LED grün = belegt, rot = defekt, aus = leer) und die
              Lüfterwand mit einer Lücke; baut Platte (install_disk "3") und Lüfter
              (install_fan "2:rechts" – Pfeil nach links oder rechts) ein, Schlüssel „kuehlung“.
  Rückseite   sieht 2 Netzteilschächte (Sicherung ok/durch) und das Schild, auf welcher Seite
              der Warmgang ist (links/rechts, von vorne gesehen); baut das Netzteil ein (install_psu "1:230"), Schlüssel „strom“.

Regeln (zerrissene Einbauanleitung): Reihenfolge Platte → Lüfter → Netzteil · vor jedem
Einbau Platz auf Wartung (sonst Stromschlag) · Platte in den Schacht vom Etikett · Lüfterpfeil
zeigt zum Warmgang (links/rechts) · Netzteil in den Schacht mit heiler Sicherung, Spannung vom Etikett ·
vor dem Hochfahren alle Wartungen aus · Schlüssel Strom → Kühlung → System, je ≤ 5 s Abstand.
Fehler kosten Leben und sagen, was falsch war.
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, MISTAKE_DAMAGE, TASK_POINTS
from backend.playableObject import RepairTask, ROLE_M, ROLE_P1, ROLE_P2

GAME = "repair_session"
M, V, R = "Anna", "Ben", "Celim"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in ((M, ROLE_M), (V, ROLE_P1), (R, ROLE_P2)):
            center.redis.r.hset(center.redis._k_players(GAME), name, json.dumps({"name": name, "role": role}))
        center.redis.r.hset(center._key, "dev_mode", "1")
        center.start()
        for _ in range(3):
            center.skip_task()
        center.redis.r.hset(center._key, "dev_mode", "0")   # im Finale zählen Fehler
        uhr = {"t": 1000.0}
        center._now = lambda: uhr["t"]
        center.uhr = uhr
        yield center


def _in(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _st(dc):
    return dc.current_task()["state"]


def _views(dc):
    return dc.snapshot()["tasks"][0]["views"]


def _loesung(dc):
    st = _st(dc)
    return st["disk_bay"], st["fan_slot"], st["fan_dir"], st["psu_bay"], st["volt"]


def _alles_einbauen(dc):
    bay, slot, richtung, psu, volt = _loesung(dc)
    _in(dc, M, "give", "disk:FI-SI")
    _in(dc, M, "give", "fan:FI-SI")
    _in(dc, M, "give", "psu:FI-AE")
    _in(dc, M, "maintenance", f"bay:{bay - 1}")
    assert _in(dc, V, "install_disk", str(bay))["result"] == "correct"
    _in(dc, M, "maintenance", f"bay:{bay - 1}")
    _in(dc, M, "maintenance", f"fan:{slot - 1}")
    assert _in(dc, V, "install_fan", f"{slot}:{richtung}")["result"] == "correct"
    _in(dc, M, "maintenance", f"fan:{slot - 1}")
    _in(dc, M, "maintenance", f"psu:{psu - 1}")
    assert _in(dc, R, "install_psu", f"{psu}:{volt}")["result"] == "correct"
    _in(dc, M, "maintenance", f"psu:{psu - 1}")


# ------------------------------------------------------------------ Aufbau
def test_after_three_tasks_comes_the_repair(dc):
    assert dc.current_task()["kind"] == "repair"
    assert TASK_POINTS["repair"] == 350          # feat/finale-hilfen-punkte
    assert RepairTask.HINTS == 6


def test_the_round_fits_the_labels_in_the_parts_box(dc):
    st = _st(dc)
    etiketten = {t["id"]: t["label"] for t in dc.snapshot()["parts"]}
    assert etiketten["disk"] == f"Schacht {st['disk_bay']}"
    assert etiketten["psu"] == f"{st['volt']} V"


def test_the_round_is_solvable_and_consistent():
    for _ in range(200):
        st = RepairTask.create({}, {"disk": {"label": "Schacht 3"}, "psu": {"label": "115 V"}})
        assert st["disk_bay"] == 3 and st["volt"] == "115"
        leds = st["bays"]
        assert leds[3 - 1] == "aus"                        # Zielschacht ist leer
        assert leds.count("rot") == 1 and leds.count("gruen") == 1 and leds.count("aus") == 2
        assert st["fan_slot"] in (1, 2, 3)
        assert st["warmgang"] in ("links", "rechts") and st["fan_dir"] == st["warmgang"]   # Pfeil zeigt zum Warmgang
        assert st["fuses"][st["psu_bay"] - 1] == "ok"
        assert st["fuses"].count("durch") == 1


def test_everyone_sees_only_their_part(dc):
    views = _views(dc)
    leit, vorne, hinten = views[ROLE_M], views[ROLE_P1], views[ROLE_P2]
    assert leit["type"] == "repair_console"
    assert {p["id"]: p["label"] for p in leit["parts"]}["disk"].startswith("Schacht ")
    assert leit["console"] == {"bay": 4, "fan": 3, "psu": 2}
    assert vorne["type"] == "repair_front" and len(vorne["bays"]) == 4 and len(vorne["fan_slots"]) == 3
    assert "warmgang" not in vorne and "fuses" not in vorne
    assert hinten["type"] == "repair_back" and len(hinten["psu_bays"]) == 2 and hinten["warmgang"] in ("links", "rechts")
    assert "bays" not in hinten
    for v in views.values():
        assert v["note"]["title"] == "Einbauanleitung"
    # Etiketten stehen nur beim Leitstand, nicht auf den Teilen in der Hand
    _in(dc, M, "give", "disk:FI-SI")
    assert "label" not in _views(dc)[ROLE_P1]["hand"][0]


# ------------------------------------------------------------------ Weitergeben
def test_master_hands_parts_over_and_wrong_person_gives_back(dc):
    assert _in(dc, M, "give", "psu:FI-SI")["result"] == "correct"
    assert [t["id"] for t in _views(dc)[ROLE_P1]["hand"]] == ["psu"]
    assert _in(dc, V, "return", "psu")["result"] == "correct"     # passt vorne nicht: zurück
    assert _views(dc)[ROLE_P1]["hand"] == []
    orte = {p["id"]: p["ort"] for p in _views(dc)[ROLE_M]["parts"]}
    assert orte["psu"] == "kiste"
    assert dc.health == dc.max_health                              # Weitergeben kostet nichts


def test_only_the_master_hands_out_and_switches_maintenance(dc):
    assert _in(dc, V, "give", "disk:FI-SI")["result"] == "ignored"
    assert _in(dc, R, "maintenance", "psu:0")["result"] == "ignored"


def test_maintenance_toggles(dc):
    _in(dc, M, "maintenance", "bay:2")
    assert _views(dc)[ROLE_M]["wartung"] == ["bay:2"]
    _in(dc, M, "maintenance", "bay:2")
    assert _views(dc)[ROLE_M]["wartung"] == []


# ------------------------------------------------------------------ Einbau und Fehler
def test_install_without_maintenance_is_an_electric_shock(dc):
    bay, *_ = _loesung(dc)
    _in(dc, M, "give", "disk:FI-SI")
    res = _in(dc, V, "install_disk", str(bay))
    assert res["result"] == "wrong" and "Stromschlag" in res["message"]
    assert dc.health == dc.max_health - MISTAKE_DAMAGE


def test_console_counts_from_zero(dc):
    """Wartung auf „bay:3“ für Schacht 3 ist der falsche Platz (richtig: bay:2)."""
    bay, *_ = _loesung(dc)
    _in(dc, M, "give", "disk:FI-SI")
    _in(dc, M, "maintenance", f"bay:{bay}")
    assert _in(dc, V, "install_disk", str(bay))["result"] == "wrong"


def test_wrong_bay_is_a_mistake(dc):
    bay, *_ = _loesung(dc)
    falsch = next(n for n in range(1, 5) if n != bay)
    _in(dc, M, "give", "disk:FI-SI")
    _in(dc, M, "maintenance", f"bay:{falsch - 1}")
    res = _in(dc, V, "install_disk", str(falsch))
    assert res["result"] == "wrong" and "Schacht" in res["message"]


def test_order_disk_then_fan_then_psu(dc):
    bay, slot, richtung, psu, volt = _loesung(dc)
    _in(dc, M, "give", "fan:FI-SI")
    _in(dc, M, "maintenance", f"fan:{slot - 1}")
    res = _in(dc, V, "install_fan", f"{slot}:{richtung}")
    assert res["result"] == "wrong" and "Reihenfolge" in res["message"]


def test_fan_the_wrong_way_round(dc):
    bay, slot, richtung, *_ = _loesung(dc)
    _in(dc, M, "give", "disk:FI-SI")
    _in(dc, M, "give", "fan:FI-SI")
    _in(dc, M, "maintenance", f"bay:{bay - 1}")
    _in(dc, V, "install_disk", str(bay))
    _in(dc, M, "maintenance", f"fan:{slot - 1}")
    verkehrt = "links" if richtung == "rechts" else "rechts"
    res = _in(dc, V, "install_fan", f"{slot}:{verkehrt}")
    assert res["result"] == "wrong" and "Lüfter" in res["message"]


def test_psu_needs_the_good_fuse_and_the_right_voltage(dc):
    bay, slot, richtung, psu, volt = _loesung(dc)
    _in(dc, M, "give", "disk:FI-SI")
    _in(dc, M, "give", "fan:FI-SI")
    _in(dc, M, "give", "psu:FI-AE")
    _in(dc, M, "maintenance", f"bay:{bay - 1}")
    _in(dc, V, "install_disk", str(bay))
    _in(dc, M, "maintenance", f"fan:{slot - 1}")
    _in(dc, V, "install_fan", f"{slot}:{richtung}")
    _in(dc, M, "maintenance", "psu:0")
    _in(dc, M, "maintenance", "psu:1")
    andere = "115" if volt == "230" else "230"
    assert "Spannung" in _in(dc, R, "install_psu", f"{psu}:{andere}")["message"]
    assert "Sicherung" in _in(dc, R, "install_psu", f"{3 - psu}:{volt}")["message"]
    assert _in(dc, R, "install_psu", f"{psu}:{volt}")["result"] == "correct"


def test_a_part_must_be_in_your_hand(dc):
    bay, *_ = _loesung(dc)
    _in(dc, M, "maintenance", f"bay:{bay - 1}")
    assert _in(dc, V, "install_disk", str(bay))["result"] == "ignored"


# ------------------------------------------------------------------ Drei-Schlüssel-Start
def test_keys_only_after_everything_is_installed(dc):
    assert _in(dc, R, "key", "strom")["result"] == "ignored"
    _alles_einbauen(dc)
    assert _views(dc)[ROLE_M]["phase"] == "start"


def test_three_keys_in_order_win(dc):
    _alles_einbauen(dc)
    assert _in(dc, R, "key", "strom")["result"] == "correct"
    dc.uhr["t"] += 2
    assert _in(dc, V, "key", "kuehlung")["result"] == "correct"
    dc.uhr["t"] += 2
    res = _in(dc, M, "key", "system")
    assert res["result"] == "correct" and res.get("won") is True
    assert dc.status == "won"


def test_keys_in_the_wrong_order_start_over(dc):
    _alles_einbauen(dc)
    _in(dc, R, "key", "strom")
    res = _in(dc, M, "key", "system")
    assert res["result"] == "wrong" and "Reihenfolge" in res["message"]
    assert _views(dc)[ROLE_M]["keys"] == []


def test_too_slow_between_keys_starts_over_without_penalty(dc):
    _alles_einbauen(dc)
    _in(dc, R, "key", "strom")
    dc.uhr["t"] += 6
    leben = dc.health
    assert _in(dc, V, "key", "kuehlung")["result"] == "wrong"
    assert dc.health == leben - MISTAKE_DAMAGE   # Kühlung ohne Strom = falsche Reihenfolge
    assert _in(dc, R, "key", "strom")["result"] == "correct"


def test_maintenance_still_on_is_an_emergency_stop(dc):
    _alles_einbauen(dc)
    _in(dc, M, "maintenance", "bay:0")
    res = _in(dc, R, "key", "strom")
    assert res["result"] == "wrong" and "Wartung" in res["message"]


def test_installed_disk_shows_a_green_led_in_its_bay(dc):
    bay, *_ = _loesung(dc)
    _in(dc, M, "give", "disk:FI-SI")
    _in(dc, M, "maintenance", f"bay:{bay - 1}")
    _in(dc, V, "install_disk", str(bay))
    assert _views(dc)[ROLE_P1]["bays"][bay - 1] == {"nr": bay, "led": "gruen"}


def test_hints_sprechen_von_schacht_und_links_rechts():
    """feat/leichter-finale: Hilfe-Zettel ohne RAID/Rack, der Lüfter zeigt links oder rechts."""
    for _ in range(30):
        st = RepairTask.create({})
        texte = {h["id"]: h["text"] for h in RepairTask.hints(st)}
        alles = " ".join(texte.values())
        assert "RAID" not in alles and "Rack" not in alles
        assert st["fan_dir"] in texte["fan"] and f"Warmgang ist {st['warmgang']}" in texte["fan"]
