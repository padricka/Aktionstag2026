"""Task 3 – Datenrettung (kind="data_rescue"), Escape-Room-Variante, leichte Fassung.

Spezifikation: GAME_DESIGN.md, Abschnitt 4 „Aufgabe 3" (feat/leichter-datenrettung).

  Gerettet wird immer RENTE – als Kette verschlüsselt:
  Wort → um k VOR im Alphabet → ASCII-Zahl → Datenzeile aus 8 Ziffern (0/1).
  Kein Prüfbit, keine kaputten Pakete mehr: 5 Datenzeilen = 5 Buchstaben.

  Leitstand   sieht das Log: Login-Name in Hex (nur Ziffern 0–9, nie A–F),
              Backup-Jobs (Datum, Platte, Status), Schlüsselbund (Nr., k, gültig/gesperrt).
              Trägt k ein (set_key) – danach sehen alle „k = …“.
  Vorderseite sieht die ASCII-Tabelle; meldet sich am Terminal an (terminal_login),
              danach tippt sie das Wort (rescue_word). Sieht k, sobald es eingetragen ist.
  Rückseite   sieht 4 Backup-Platten; legt die richtige ein (mount_disk), danach
              die Schlüssel-Nr. (normale Zahl) und die Datenzeilen mit den Stellenwerten
              128 64 32 16 8 4 2 1 darüber.

  Anleitung, je Rolle ein Teil mit vollständigen Regeln (notes.RESCUE_NOTE):
    ① (Rückseite)   neuestes Backup mit Status OK – erst Monat, dann Tag vergleichen
    ② (Vorderseite) Login: Hex → Zahl (erste Ziffer · 16 + zweite) → Buchstabe
    ③ (Rückseite)   Datenzeile → Zahl: Werte über jeder 1 zusammenzählen
    ④ (Vorderseite) Zahl → Buchstabe in der ASCII-Tabelle
    ⑤ (Leitstand)   Schlüssel k = GÜLTIGER Eintrag mit der Schlüssel-Nr. von der Platte, eintragen
    ⑥ (Leitstand)   jeden Buchstaben um k im Alphabet ZURÜCK; Falle: „ROT13“

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


def _login(views):
    """② Hex: erste Ziffer · 16 + zweite → Buchstabe."""
    tabelle = views[ROLE_P1]["ascii_table"]
    return "".join(_buchstabe(int(h[2]) * 16 + int(h[3]), tabelle) for h in views[ROLE_M]["login_hex"])


def _zahl(zeile, werte):
    """③ die Werte über jeder 1 zusammenzählen."""
    return sum(w for w, z in zip(werte, zeile) if z == "1")


def _k(views):
    """⑤ der GÜLTIGE Schlüssel mit der Schlüssel-Nr. von der Platte."""
    nr = views[ROLE_P2]["key_nr"]
    treffer = [s for s in views[ROLE_M]["keys"] if s["nr"] == nr and s["status"] == "gültig"]
    assert len(treffer) == 1
    return treffer[0]["k"]


def _buchstabe(zahl, tabelle):
    """④ Zahl → Buchstabe in der ASCII-Tabelle."""
    return next(b for b, z in tabelle.items() if z == zahl)


def _zurueck(buchstabe, k):
    """⑥ um k im Alphabet zurück, vor A kommt Z."""
    return chr((ord(buchstabe) - ord("A") - k) % 26 + ord("A"))


def _wort(views, k=None):
    k = _k(views) if k is None else k
    tabelle = views[ROLE_P1]["ascii_table"]
    werte = views[ROLE_P2]["weights"]
    return "".join(_zurueck(_buchstabe(_zahl(z, werte), tabelle), k) for z in views[ROLE_P2]["rows"])


def _runden(n=300):
    """Zufallsrunden, schon mit eingelegter Platte (sonst fehlen die Datenzeilen)."""
    for _ in range(n):
        st = DataRescueTask.create({})
        st["mounted"] = True
        yield st, DataRescueTask.views(st)


def _einlegen(dc):
    assert _press(dc, P2_NAME, "mount_disk", _platte(_views(dc)))["result"] == "correct"


def _anmelden(dc):
    assert _text(dc, P1_NAME, "terminal_login", _login(_views(dc)))["result"] == "correct"


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
    assert {"login_hex", "backups", "keys"} <= set(m) and not {"rows", "ascii_table", "disks", "key_nr"} & set(m)
    assert "ascii_table" in p1 and not {"login_hex", "keys", "rows", "disks", "key_nr"} & set(p1)
    assert {"disks", "rows", "key_nr", "weights"} <= set(p2) and not {"login_hex", "keys", "ascii_table"} & set(p2)
    for view in (m, p1, p2):
        for verboten in ("word", "login", "cipher", "k", "serial", "solution"):
            assert verboten not in view


def test_vorderseite_has_the_full_ascii_table_and_lengths(dc):
    p1 = _view(dc, ROLE_P1)
    assert p1["ascii_table"] == {chr(c): c for c in range(ord("A"), ord("Z") + 1)}
    assert p1["word_len"] == 5
    assert p1["login_len"] == len(_view(dc, ROLE_M)["login_hex"])
    assert p1["logged_in"] is False


def test_public_snapshot_hides_raw_state(dc):
    assert "state" not in dc.snapshot()["tasks"][0]


# ------------------------------------------------------------------ ① Backup-Platte
def test_rueckseite_sees_four_disks_but_no_rows_before_mounting(dc):
    p2 = _view(dc, ROLE_P2)
    assert len(p2["disks"]) == 4
    assert {b["serial"] for b in _view(dc, ROLE_M)["backups"]} == set(p2["disks"])
    assert p2["mounted"] is False
    assert p2["rows"] is None and p2["key_nr"] is None


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


def test_right_disk_mounts_and_shows_rows_and_key_number(dc):
    _einlegen(dc)
    p2 = _view(dc, ROLE_P2)
    assert p2["mounted"] is True
    assert len(p2["rows"]) == 5
    assert isinstance(p2["key_nr"], int) and 1 <= p2["key_nr"] <= 9


def test_wrong_disk_costs_health(dc):
    falsch = next(s for s in _view(dc, ROLE_P2)["disks"] if s != _platte(_views(dc)))
    assert _press(dc, P2_NAME, "mount_disk", falsch)["result"] == "wrong"
    assert dc.health == 270
    assert _view(dc, ROLE_P2)["mounted"] is False


# ------------------------------------------------------------------ ② Login
def test_login_is_a_drv_word_in_hex_without_letters():
    """Hex ohne A–F: Nicht-ITler müssen nie „A = 10“ umrechnen."""
    gesehen = set()
    for _, views in _runden():
        hexe = views[ROLE_M]["login_hex"]
        assert all(h.startswith("0x") and len(h) == 4 and h[2:].isdigit() for h in hexe)
        gesehen.add(_login(views))
    assert gesehen == {"REHA", "DRV"}


def test_login_unlocks_the_terminal(dc):
    _anmelden(dc)
    assert _view(dc, ROLE_P1)["logged_in"] is True


def test_wrong_login_costs_health(dc):
    assert _text(dc, P1_NAME, "terminal_login", "ADMIN")["result"] == "wrong"
    assert dc.health == 270


def test_word_before_login_is_ignored(dc):
    assert _text(dc, P1_NAME, "rescue_word", "RENTE")["result"] == "ignored"
    assert dc.health == 300


# ------------------------------------------------------------------ ③ Datenzeilen
def test_five_rows_of_eight_digits_with_place_values():
    """Keine kaputte Zeile mehr, kein Prüfbit: jede Zeile ist ein Buchstabe.
    Die Stellenwerte stehen in der Ansicht direkt über den Ziffern."""
    for _, views in _runden():
        p2 = views[ROLE_P2]
        assert p2["weights"] == [128, 64, 32, 16, 8, 4, 2, 1]
        assert len(p2["rows"]) == 5
        assert all(len(z) == 8 and set(z) <= {"0", "1"} for z in p2["rows"])
        assert all(65 <= _zahl(z, p2["weights"]) <= 90 for z in p2["rows"])


# ------------------------------------------------------------------ ⑤ Schlüssel
def test_keyring_shows_plain_numbers_and_a_blocked_twin():
    for _, views in _runden():
        nr = views[ROLE_P2]["key_nr"]
        keys = views[ROLE_M]["keys"]
        gleiche_nr = [s for s in keys if s["nr"] == nr]
        assert {s["status"] for s in gleiche_nr} == {"gültig", "gesperrt"}
        assert {s["status"] for s in keys} == {"gültig", "gesperrt"}
        assert all(isinstance(s["k"], int) and 1 <= s["k"] <= 9 for s in keys)
        assert len({s["k"] for s in keys}) == len(keys)


def test_master_enters_k_and_everyone_sees_it(dc):
    _einlegen(dc)
    assert all(_view(dc, r)["key"] is None for r in (ROLE_M, ROLE_P1, ROLE_P2))
    k = _k(_views(dc))
    assert _text(dc, MASTER_NAME, "set_key", str(k))["result"] == "correct"
    assert all(_view(dc, r)["key"] == k for r in (ROLE_M, ROLE_P1, ROLE_P2))


def test_wrong_k_costs_health_and_is_not_shown(dc):
    _einlegen(dc)
    gesperrt = next(s["k"] for s in _view(dc, ROLE_M)["keys"]
                    if s["nr"] == _view(dc, ROLE_P2)["key_nr"] and s["status"] == "gesperrt")
    assert _text(dc, MASTER_NAME, "set_key", str(gesperrt))["result"] == "wrong"
    assert dc.health == 270
    assert _view(dc, ROLE_P1)["key"] is None


def test_k_once_set_stays_and_bad_inputs_are_ignored(dc):
    _einlegen(dc)
    k = _k(_views(dc))
    assert _text(dc, MASTER_NAME, "set_key", "  ")["result"] == "ignored"
    assert _text(dc, MASTER_NAME, "set_key", "drei")["result"] == "ignored"
    assert _text(dc, P1_NAME, "set_key", str(k))["result"] == "ignored"
    assert _text(dc, MASTER_NAME, "set_key", str(k))["result"] == "correct"
    assert _text(dc, MASTER_NAME, "set_key", str(k))["result"] == "ignored"
    assert dc.health == 300


# ------------------------------------------------------------------ ⑥ Wort
def test_rules_always_give_rente():
    for _, views in _runden():
        assert _wort(views) == "RENTE"


def test_traps_always_give_a_wrong_word():
    """Gesperrter Zwilling, ROT13 und „gar nicht zurückschieben“ führen nie zu RENTE."""
    for _, views in _runden():
        nr = views[ROLE_P2]["key_nr"]
        gesperrt = next(s for s in views[ROLE_M]["keys"] if s["nr"] == nr and s["status"] == "gesperrt")
        assert _wort(views, k=gesperrt["k"]) != "RENTE"
        assert _wort(views, k=13) != "RENTE"
        assert _wort(views, k=0) != "RENTE"


def test_variants_change_between_rounds():
    platten, nummern, ks = set(), set(), set()
    for st, views in _runden():
        platten.add(_platte(views))
        nummern.add(views[ROLE_P2]["key_nr"])
        ks.add(_k(views))
    assert len(platten) > 50
    assert len(nummern) > 5
    assert len(ks) > 5


# ------------------------------------------------------------------ Lösen
def test_full_chain_from_views_solves_heals_and_scores(dc):
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    dc.redis.r.hset(dc.redis._k_state(GAME), "time_left", 100)

    _einlegen(dc)
    _anmelden(dc)
    res = _text(dc, P1_NAME, "rescue_word", _wort(_views(dc)))

    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] != task_id
    assert dc.health == 115
    assert dc.task_points == 2 * TASK_POINTS["data_rescue"]   # sofort gelöst → ×2


def test_word_does_not_need_k_entered(dc):
    """k eintragen hilft allen beim Mitlesen, ist aber keine Pflicht."""
    _einlegen(dc)
    _anmelden(dc)
    assert _text(dc, P1_NAME, "rescue_word", "RENTE")["result"] == "correct"


def test_word_is_case_insensitive_and_trimmed(dc):
    _anmelden(dc)
    assert _text(dc, P1_NAME, "rescue_word", "  rente ")["result"] == "correct"


def test_wrong_word_costs_health(dc):
    _anmelden(dc)
    assert _text(dc, P1_NAME, "rescue_word", "RENTEN")["result"] == "wrong"
    assert dc.health == 270


def test_empty_inputs_are_ignored(dc):
    assert _text(dc, P1_NAME, "terminal_login", "   ")["result"] == "ignored"
    _anmelden(dc)
    assert _text(dc, P1_NAME, "rescue_word", "   ")["result"] == "ignored"
    assert dc.health == 300


def test_repeated_login_or_mount_is_ignored(dc):
    _einlegen(dc)
    _anmelden(dc)
    assert _press(dc, P2_NAME, "mount_disk", "SN-0000")["result"] == "ignored"
    assert _text(dc, P1_NAME, "terminal_login", "FALSCH")["result"] == "ignored"
    assert dc.health == 300


# ------------------------------------------------------------------ Rollen
def test_each_input_belongs_to_one_role(dc):
    platte = _platte(_views(dc))
    login = _login(_views(dc))
    assert _press(dc, P1_NAME, "mount_disk", platte)["result"] == "ignored"
    assert _press(dc, MASTER_NAME, "mount_disk", platte)["result"] == "ignored"
    assert _text(dc, P2_NAME, "terminal_login", login)["result"] == "ignored"
    assert _text(dc, MASTER_NAME, "terminal_login", login)["result"] == "ignored"
    _anmelden(dc)
    assert _text(dc, MASTER_NAME, "rescue_word", "RENTE")["result"] == "ignored"
    assert _text(dc, P2_NAME, "rescue_word", "RENTE")["result"] == "ignored"
    assert dc.health == 300


def test_old_targets_are_gone(dc):
    for target in ("ascii_answer", "binary_answer", "sync_button"):
        assert _text(dc, P1_NAME, target, "RENTE")["result"] == "ignored"
    assert dc.health == 300
