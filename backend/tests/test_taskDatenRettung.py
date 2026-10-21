"""Task 3 – Datenrettung (kind="data_rescue"), Escape-Room-Variante, leichte Fassung.

Spezifikation: GAME_DESIGN.md, Abschnitt 4 „Aufgabe 3" (feat/leichter-datenrettung,
nach Rückmeldung von Nicht-ITlern: kein Login, kein Rechnen mit langen Codes, kein Verschieben).

  Gerettet wird ein 6-Buchstaben-Wort der Rentenversicherung (RENTEN, ANTRAG, …).

  Leitstand   sieht Backup-Jobs (Datum, Platte, Status) und den Schlüsselbund
              (Nr., Name, gültig/gesperrt – zwei gültige).
  Vorderseite sieht die Code-Tabelle (8-stelliger Code → Buchstabe, frei erfunden)
              und tippt das Wort ein (rescue_word).
  Rückseite   sieht 4 Backup-Platten; legt die richtige ein (mount_disk). Danach: die
              Schlüssel-Nr. der Platte als 4-stellige Binärzahl und ZWEI Tabellen mit je
              6 Codes, überschrieben mit dem Namen eines gültigen Schlüssels.

  Anleitung, je Rolle ein Teil (notes.RESCUE_NOTE):
    ① (Rückseite)   neuestes Backup mit Status OK – erst Monat, dann Tag vergleichen
    ② (Leitstand)   4-stellige Nr. umrechnen: Werte 8 4 2 1 über jeder 1 zusammenzählen
    ③ (Vorderseite) gültiger Schlüssel mit dieser Nr. → sein Name steht über der richtigen Tabelle
    ④ (Rückseite)   die 6 Codes vorlesen, die Vorderseite sucht sie in der Code-Tabelle

Kernidee der Tests: Alles entsteht NUR aus den drei Ansichten und den Regeln.
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, TASK_POINTS
from backend.playableObject import DataRescueTask, ROLE_M, ROLE_P1, ROLE_P2

GAME = "t3_session"
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
        center.new_task("data_rescue")
        yield center


def _press(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _text(dc, name, target, value):
    return dc.process_input(name, {"action_type": "text_input", "target": target, "value": value})


def _views(dc):
    return dc.snapshot()["tasks"][0]["views"]


def _view(dc, role):
    return _views(dc)[role]


# ------------------------------------------------------------------ Regeln (wie auf der Anleitung)
def _datum(d):
    """„TT.MM.“ → (Monat, Tag): erst Monat, dann Tag."""
    tag, monat = d.strip(".").split(".")
    return int(monat), int(tag)


def _platte(views):
    """① neuestes Backup mit Status OK."""
    ok = [b for b in views[ROLE_M]["backups"] if b["status"] == "OK"]
    return max(ok, key=lambda b: _datum(b["date"]))["serial"]


def _nummer(views):
    """② 4-stellige Binärzahl: 8 4 2 1 über jeder 1 zusammenzählen."""
    return sum(w for w, z in zip((8, 4, 2, 1), views[ROLE_P2]["key_id"]) if z == "1")


def _tabelle(views):
    """③ gültiger Schlüssel mit dieser Nr. → sein Name steht über der richtigen Tabelle."""
    treffer = [s for s in views[ROLE_M]["keys"] if s["nr"] == _nummer(views) and s["status"] == "gültig"]
    assert len(treffer) == 1
    return next(t for t in views[ROLE_P2]["tables"] if t["name"] == treffer[0]["name"])


def _lesen(codes, views):
    """④ jeden Code in der Code-Tabelle der Vorderseite nachschlagen."""
    tabelle = {code: buchstabe for buchstabe, code in views[ROLE_P1]["code_table"].items()}
    return "".join(tabelle[c] for c in codes)


def _wort(views):
    return _lesen(_tabelle(views)["rows"], views)


def _runden(n=300):
    """Zufallsrunden, schon mit eingelegter Platte (sonst fehlen Nr. und Tabellen)."""
    for _ in range(n):
        st = DataRescueTask.create({})
        st["mounted"] = True
        yield st, DataRescueTask.views(st)


def _einlegen(dc):
    assert _press(dc, P2_NAME, "mount_disk", _platte(_views(dc)))["result"] == "correct"


# ------------------------------------------------------------------ Ansichten
def test_every_role_has_its_own_view_type(dc):
    assert dc.current_task()["kind"] == "data_rescue"
    assert _view(dc, ROLE_M)["type"] == "rescue_log"
    assert _view(dc, ROLE_P1)["type"] == "rescue_terminal"
    assert _view(dc, ROLE_P2)["type"] == "packet_dump"


def test_every_role_has_its_part_of_the_anleitung(dc):
    teile = {r: _view(dc, r)["note"] for r in (ROLE_M, ROLE_P1, ROLE_P2)}
    assert {n["title"] for n in teile.values()} == {"Datenrettung"}
    assert (teile[ROLE_M]["part"], teile[ROLE_P1]["part"], teile[ROLE_P2]["part"]) == (1, 2, 3)


def test_each_role_sees_only_its_own_facts(dc):
    _einlegen(dc)
    m, p1, p2 = (_view(dc, r) for r in (ROLE_M, ROLE_P1, ROLE_P2))
    assert {"backups", "keys"} <= set(m) and not {"tables", "code_table", "disks", "key_id"} & set(m)
    assert "code_table" in p1 and not {"keys", "tables", "disks", "key_id", "backups"} & set(p1)
    assert {"disks", "tables", "key_id"} <= set(p2) and not {"keys", "code_table", "backups"} & set(p2)
    for view in (m, p1, p2):
        for verboten in ("word", "decoy", "serial", "solution", "login_hex", "ascii_table"):
            assert verboten not in view


def test_no_login_anymore(dc):
    """Die Zugangsdaten (Hex-Login) sind weg: das Terminal nimmt gleich das Wort."""
    assert "login_hex" not in _view(dc, ROLE_M)
    assert "logged_in" not in _view(dc, ROLE_P1)
    assert _text(dc, P1_NAME, "terminal_login", "REHA")["result"] == "ignored"


def test_vorderseite_has_a_code_table_for_every_letter(dc):
    p1 = _view(dc, ROLE_P1)
    tabelle = p1["code_table"]
    assert sorted(tabelle) == [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    assert all(len(c) == 8 and set(c) <= {"0", "1"} for c in tabelle.values())
    assert len(set(tabelle.values())) == 26
    assert p1["word_len"] == 6


def test_public_snapshot_hides_raw_state(dc):
    assert "state" not in dc.snapshot()["tasks"][0]


# ------------------------------------------------------------------ ① Backup-Platte
def test_rueckseite_sees_four_disks_but_nothing_else_before_mounting(dc):
    p2 = _view(dc, ROLE_P2)
    assert len(p2["disks"]) == 4
    assert {b["serial"] for b in _view(dc, ROLE_M)["backups"]} == set(p2["disks"])
    assert p2["mounted"] is False
    assert p2["tables"] is None and p2["key_id"] is None


def test_newest_backup_is_always_broken_and_plain_text_dates_mislead():
    """Falle 1: das allerneueste Backup ist FEHLER. Falle 2: wer „TT.MM.“ als Text
    vergleicht (ohne „erst Monat, dann Tag“), nimmt die falsche Platte."""
    for _, views in _runden():
        backups = views[ROLE_M]["backups"]
        neuestes = max(backups, key=lambda b: _datum(b["date"]))
        assert neuestes["status"] == "FEHLER"
        ok = [b for b in backups if b["status"] == "OK"]
        als_text = max(ok, key=lambda b: b["date"])["serial"]
        assert als_text != _platte(views)


def test_right_disk_mounts_and_shows_number_and_two_tables(dc):
    _einlegen(dc)
    p2 = _view(dc, ROLE_P2)
    assert p2["mounted"] is True
    assert len(p2["key_id"]) == 4 and set(p2["key_id"]) <= {"0", "1"}
    assert len(p2["tables"]) == 2
    for t in p2["tables"]:
        assert t["name"] and len(t["rows"]) == 6
        assert all(len(c) == 8 and set(c) <= {"0", "1"} for c in t["rows"])


def test_wrong_disk_costs_health(dc):
    falsch = next(s for s in _view(dc, ROLE_P2)["disks"] if s != _platte(_views(dc)))
    assert _press(dc, P2_NAME, "mount_disk", falsch)["result"] == "wrong"
    assert dc.health == 270
    assert _view(dc, ROLE_P2)["mounted"] is False


# ------------------------------------------------------------------ ②–③ Schlüssel und Tabelle
def test_keyring_has_two_valid_keys_and_both_tables_belong_to_them():
    for _, views in _runden():
        keys = views[ROLE_M]["keys"]
        gueltig = [s for s in keys if s["status"] == "gültig"]
        assert len(gueltig) == 2
        assert {s["status"] for s in keys} == {"gültig", "gesperrt"}
        assert len({s["nr"] for s in keys}) == len(keys) and len({s["name"] for s in keys}) == len(keys)
        assert all(1 <= s["nr"] <= 15 for s in keys)
        assert {t["name"] for t in views[ROLE_P2]["tables"]} == {s["name"] for s in gueltig}


def test_disk_number_points_to_one_of_the_valid_keys():
    for _, views in _runden():
        assert _nummer(views) in {s["nr"] for s in views[ROLE_M]["keys"] if s["status"] == "gültig"}


# ------------------------------------------------------------------ ④ Wort
def test_rules_always_give_a_six_letter_drv_word():
    gesehen = set()
    for _, views in _runden():
        wort = _wort(views)
        assert wort in DataRescueTask.WORDS and len(wort) == 6
        gesehen.add(wort)
    assert gesehen == set(DataRescueTask.WORDS)


def test_the_other_table_gives_a_different_word():
    """Falle: die Tabelle des anderen gültigen Schlüssels ergibt ein anderes, echtes Wort."""
    for _, views in _runden():
        richtig = _tabelle(views)
        andere = next(t for t in views[ROLE_P2]["tables"] if t is not richtig)
        falsch = _lesen(andere["rows"], views)
        assert falsch in DataRescueTask.WORDS and falsch != _wort(views)


def test_variants_change_between_rounds():
    platten, nummern, tabellen = set(), set(), set()
    for st, views in _runden():
        platten.add(_platte(views))
        nummern.add(_nummer(views))
        tabellen.add(views[ROLE_P1]["code_table"]["A"])
    assert len(platten) > 50
    assert len(nummern) > 5
    assert len(tabellen) > 50


# ------------------------------------------------------------------ Lösen
def test_full_chain_from_views_solves_heals_and_scores(dc):
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    dc.redis.r.hset(dc.redis._k_state(GAME), "time_left", 100)

    _einlegen(dc)
    res = _text(dc, P1_NAME, "rescue_word", _wort(_views(dc)))

    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] != task_id
    assert dc.health == 115
    assert dc.task_points == 2 * TASK_POINTS["data_rescue"]   # sofort gelöst → ×2


def test_word_is_case_insensitive_and_trimmed(dc):
    wort = dc.current_task()["state"]["word"]
    assert _text(dc, P1_NAME, "rescue_word", f"  {wort.lower()} ")["result"] == "correct"


def test_wrong_word_costs_health(dc):
    assert _text(dc, P1_NAME, "rescue_word", "FALSCH")["result"] == "wrong"
    assert dc.health == 270


def test_empty_word_is_ignored(dc):
    assert _text(dc, P1_NAME, "rescue_word", "   ")["result"] == "ignored"
    assert dc.health == 300


def test_repeated_mount_is_ignored(dc):
    _einlegen(dc)
    assert _press(dc, P2_NAME, "mount_disk", "SN-0000")["result"] == "ignored"
    assert dc.health == 300


# ------------------------------------------------------------------ Rollen
def test_each_input_belongs_to_one_role(dc):
    platte = _platte(_views(dc))
    wort = dc.current_task()["state"]["word"]
    assert _press(dc, P1_NAME, "mount_disk", platte)["result"] == "ignored"
    assert _press(dc, MASTER_NAME, "mount_disk", platte)["result"] == "ignored"
    assert _text(dc, MASTER_NAME, "rescue_word", wort)["result"] == "ignored"
    assert _text(dc, P2_NAME, "rescue_word", wort)["result"] == "ignored"
    assert dc.health == 300


def test_old_targets_are_gone(dc):
    for target in ("ascii_answer", "binary_answer", "sync_button", "terminal_login", "set_key"):
        assert _text(dc, MASTER_NAME, target, "3")["result"] == "ignored"
        assert _text(dc, P1_NAME, target, "RENTEN")["result"] == "ignored"
    assert dc.health == 300
