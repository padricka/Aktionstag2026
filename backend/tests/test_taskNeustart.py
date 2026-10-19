"""Finale – Neustart (kind='reboot') und Belohnungsziffern (GAME_DESIGN.md).

Jede gelöste Aufgabe deckt eine Ziffer des Neustart-Codes auf:
  Aufgabe 1 (alarm) -> Ziffer 1, sichtbar für die Rückseite (FI-AE)
  Aufgabe 2 (fire_protocol) -> Ziffer 2, sichtbar für den Leitstand (MASTER)
  Aufgabe 3 (data_rescue) -> Ziffer 3, sichtbar für die Vorderseite (FI-SI)
Danach kommt das Finale: der Leitstand tippt alle drei Ziffern in Aufgabenreihenfolge.
"""
import json
import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, MISTAKE_DAMAGE
from backend.playableObject import (
    DataRescueTask, Outcome, StepResult, ROLE_M, ROLE_P1, ROLE_P2,
)

GAME = "t4_session"
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
                center.redis._k_players(GAME), name, json.dumps({"name": name, "role": role})
            )
        center.start()
        yield center


def _input(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _kind(dc):
    return dc.current_task()["kind"]


def _state(dc):
    return dc.current_task()["state"]


def _views(dc):
    return dc.snapshot()["tasks"][0]["views"]


def _loese_alarm(dc):
    st = _state(dc)
    # Lösung direkt aus dem State (Regeln der Wartungsnotiz: test_taskAlarm.py)
    _input(dc, P1_NAME, "main_switch", st["target_symbol"])
    return _input(dc, MASTER_NAME, "shutdown_cmd", ",".join(st["solution"]))


def _loese_loeschprotokoll(dc):
    st = _state(dc)
    for step in st["sequence"]:
        _input(dc, P1_NAME, "valve_action", f"{step['rack']}:{step['agent']}")
    _input(dc, MASTER_NAME, "release", "press")          # Vier-Augen-Freigabe
    return _input(dc, P2_NAME, "release", "press")


def _loese_datenrettung(dc):
    st = _state(dc)
    _input(dc, P2_NAME, "mount_disk", st["serial"])
    _input(dc, P1_NAME, "terminal_login", st["login"])
    return _input(dc, P1_NAME, "rescue_word", st["word"])


def _bis_zum_finale(dc):
    _loese_alarm(dc)
    _loese_loeschprotokoll(dc)
    _loese_datenrettung(dc)


def _code(dc):
    return "".join(str(d) for d in dc.reboot_code)


# --------------------------------------------------------------- Belohnungsziffern
def test_neustart_code_hat_drei_ziffern(dc):
    assert len(dc.reboot_code) == 3
    assert all(isinstance(d, int) and 0 <= d <= 9 for d in dc.reboot_code)


def test_zu_beginn_ist_keine_ziffer_aufgedeckt(dc):
    assert dc.snapshot()["reboot_digits"] == [None, None, None]


def test_jede_geloeste_aufgabe_deckt_ihre_ziffer_auf(dc):
    d1, d2, d3 = dc.reboot_code

    _loese_alarm(dc)
    assert dc.snapshot()["reboot_digits"] == [d1, None, None]

    _loese_loeschprotokoll(dc)
    assert dc.snapshot()["reboot_digits"] == [d1, d2, None]

    _loese_datenrettung(dc)
    assert dc.snapshot()["reboot_digits"] == [d1, d2, d3]


def test_falsche_eingabe_deckt_nichts_auf(dc):
    _input(dc, P1_NAME, "main_switch", "gibtsnicht")
    assert dc.snapshot()["reboot_digits"] == [None, None, None]


def test_neues_spiel_wuerfelt_neuen_code_und_verdeckt_alles(dc):
    _loese_alarm(dc)
    with patch("backend.dataCenter.random.randint", side_effect=[1, 2, 3]):
        dc.start()
    assert dc.reboot_code == [1, 2, 3]
    assert dc.snapshot()["reboot_digits"] == [None, None, None]


# --------------------------------------------------------------------- Finale
def test_nach_drei_aufgaben_kommt_das_finale(dc):
    _bis_zum_finale(dc)

    assert _kind(dc) == "reboot"
    assert dc.status == "running"


def test_finale_views_jeder_sieht_genau_seine_ziffer(dc):
    d1, d2, d3 = dc.reboot_code
    _bis_zum_finale(dc)
    views = _views(dc)

    assert views[ROLE_M] == {"type": "reboot", "digit": d2, "terminal": True}
    assert views[ROLE_P1] == {"type": "reboot", "digit": d3, "terminal": False}
    assert views[ROLE_P2] == {"type": "reboot", "digit": d1, "terminal": False}


def test_richtiger_code_gewinnt_das_spiel(dc):
    _bis_zum_finale(dc)
    res = _input(dc, MASTER_NAME, "reboot_code", _code(dc))

    assert res["result"] == "correct"
    assert res["won"] is True
    assert dc.status == "won"


def test_code_mit_leerzeichen_wird_akzeptiert(dc):
    _bis_zum_finale(dc)
    res = _input(dc, MASTER_NAME, "reboot_code", " ".join(_code(dc)))

    assert res["result"] == "correct"


def test_falscher_code_kostet_leben_und_das_spiel_laeuft_weiter(dc):
    _bis_zum_finale(dc)
    hp = dc.health
    falsch = "".join(str((d + 1) % 10) for d in dc.reboot_code)
    res = _input(dc, MASTER_NAME, "reboot_code", falsch)

    assert res["result"] == "wrong"
    assert dc.health == hp - MISTAKE_DAMAGE
    assert dc.status == "running"
    assert _kind(dc) == "reboot"


def test_nur_der_leitstand_darf_den_code_eingeben(dc):
    _bis_zum_finale(dc)
    hp = dc.health

    assert _input(dc, P1_NAME, "reboot_code", _code(dc))["result"] == "ignored"
    assert _input(dc, P2_NAME, "reboot_code", _code(dc))["result"] == "ignored"
    assert dc.health == hp
    assert dc.status == "running"


def test_ohne_finale_gibt_es_keinen_sieg(dc):
    _loese_alarm(dc)
    _loese_loeschprotokoll(dc)
    res = _loese_datenrettung(dc)

    assert "won" not in res
    assert dc.status == "running"


def test_ohne_code_laesst_sich_das_finale_nicht_mit_leerer_eingabe_loesen(dc):
    dc.redis.r.hdel(dc.redis._k_state(GAME), "reboot_code")
    dc.new_task("reboot")
    res = _input(dc, MASTER_NAME, "reboot_code", " ")

    assert res["result"] != "correct"
    assert dc.status == "running"
