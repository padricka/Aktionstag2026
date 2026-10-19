"""Task 3 – Datenrettung (kind="data_rescue"), Escape-Room-Variante.

Spezifikation: GAME_DESIGN.md, Abschnitt 4 „Aufgabe 3".

  Das gerettete Wort ist immer RENTE – aber als Kette verschlüsselt:
  Wort → Caesar um k Buchstaben VOR → ASCII-Code → 7 Bit + Prüfbit vorne.
  Dazu kommt ein beschädigtes Paket (ungerade Anzahl Einsen).

  Leitstand   sieht den Schlüssel k binär (4 Bit).
  Vorderseite sieht die ASCII-Tabelle A–Z und tippt das Wort (target=rescue_word).
  Rückseite   sieht die 6 Datenpakete (je 8 Bit).

  Rettungsanleitung, je Rolle ein Teil mit vollständigen Regeln (notes.RESCUE_NOTE):
    ① (Vorderseite) Einsen zählen: gerade → heil, ungerade → beschädigt, weglassen
    ② (Leitstand)   Binär → Dezimal: erstes Bit = Prüfbit zählt nicht, dann 64 … 1
    ③ (Rückseite)   Zahl → Buchstabe über die ASCII-Tabelle
    ④ (Rückseite)   jeden Buchstaben um k im Alphabet ZURÜCK; Falle: „ROT13“

Kernidee der Tests: Das Wort entsteht NUR aus den drei Ansichten und den Regeln.
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, TASK_MULTIPLIER
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


def _text(dc, name, target, value):
    return dc.process_input(name, {"action_type": "text_input", "target": target, "value": value})


def _views(dc):
    return dc.snapshot()["tasks"][0]["views"]


def _view(dc, role):
    return _views(dc)[role]


# ------------------------------------------------------------------ Regeln (wie auf der Anleitung)
def _heil(paket):
    """① gerade Anzahl Einsen → heil."""
    return paket.count("1") % 2 == 0


def _dezimal(paket):
    """② erstes Bit ist das Prüfbit, der Rest mit 64 32 16 8 4 2 1."""
    return int(paket[1:], 2)


def _buchstabe(zahl, tabelle):
    """③ ASCII-Tabelle der Vorderseite."""
    return next(b for b, z in tabelle.items() if z == zahl)


def _zurueck(buchstabe, k):
    """④ um k im Alphabet zurück, vor A kommt Z."""
    return chr((ord(buchstabe) - ord("A") - k) % 26 + ord("A"))


def _wort_aus_ansichten(views, k_override=None):
    k = int(views[ROLE_M]["key"], 2) if k_override is None else k_override
    tabelle = views[ROLE_P1]["ascii_table"]
    pakete = [p for p in views[ROLE_P2]["packets"] if _heil(p)]
    return "".join(_zurueck(_buchstabe(_dezimal(p), tabelle), k) for p in pakete)


def _runden(n=300):
    for _ in range(n):
        st = DataRescueTask.create({})
        yield st, DataRescueTask.views(st)


# ------------------------------------------------------------------ Ansichten
def test_every_role_has_its_own_view_type(dc):
    assert dc.current_task()["kind"] == "data_rescue"
    assert _view(dc, ROLE_M)["type"] == "rescue_key"
    assert _view(dc, ROLE_P1)["type"] == "rescue_terminal"
    assert _view(dc, ROLE_P2)["type"] == "packet_dump"


def test_every_role_has_its_part_of_the_anleitung(dc):
    teile = {r: _view(dc, r)["note"] for r in (ROLE_M, ROLE_P1, ROLE_P2)}
    assert {n["title"] for n in teile.values()} == {"Datenrettung"}
    assert (teile[ROLE_M]["part"], teile[ROLE_P1]["part"], teile[ROLE_P2]["part"]) == (1, 2, 3)


def test_each_role_sees_only_its_own_facts(dc):
    m, p1, p2 = (_view(dc, r) for r in (ROLE_M, ROLE_P1, ROLE_P2))
    assert "key" in m and "packets" not in m and "ascii_table" not in m
    assert "ascii_table" in p1 and "key" not in p1 and "packets" not in p1
    assert "packets" in p2 and "key" not in p2 and "ascii_table" not in p2
    for view in (m, p1, p2):
        for verboten in ("word", "cipher", "corrupt", "k", "solution"):
            assert verboten not in view


def test_vorderseite_has_the_full_ascii_table(dc):
    tabelle = _view(dc, ROLE_P1)["ascii_table"]
    assert tabelle == {chr(c): c for c in range(ord("A"), ord("Z") + 1)}
    assert _view(dc, ROLE_P1)["word_len"] == 5


def test_public_snapshot_hides_raw_state(dc):
    assert "state" not in dc.snapshot()["tasks"][0]


# ------------------------------------------------------------------ Pakete und Schlüssel
def test_six_packets_of_eight_bits_one_of_them_broken():
    for _, views in _runden():
        pakete = views[ROLE_P2]["packets"]
        assert len(pakete) == 6
        assert all(len(p) == 8 and set(p) <= {"0", "1"} for p in pakete)
        assert sum(not _heil(p) for p in pakete) == 1


def test_key_is_four_bits_between_1_and_9():
    for _, views in _runden():
        key = views[ROLE_M]["key"]
        assert len(key) == 4 and set(key) <= {"0", "1"}
        assert 1 <= int(key, 2) <= 9


def test_rules_always_give_rente():
    for _, views in _runden():
        assert _wort_aus_ansichten(views) == "RENTE"


def test_every_healthy_packet_is_a_letter_in_the_table():
    for _, views in _runden():
        tabelle = views[ROLE_P1]["ascii_table"].values()
        for p in views[ROLE_P2]["packets"]:
            if _heil(p):
                assert _dezimal(p) in tabelle


def test_rot13_is_always_a_trap():
    for _, views in _runden():
        assert _wort_aus_ansichten(views, k_override=13) != "RENTE"


def test_key_and_broken_packet_change_between_rounds():
    keys, kaputt = set(), set()
    for _, views in _runden():
        keys.add(views[ROLE_M]["key"])
        kaputt.add(next(i for i, p in enumerate(views[ROLE_P2]["packets"]) if not _heil(p)))
    assert len(keys) > 3
    assert kaputt == set(range(6))


# ------------------------------------------------------------------ Lösen
def test_word_from_views_solves_heals_and_scores(dc):
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    dc.redis.r.hset(dc.redis._k_state(GAME), "time_left", 100)

    res = _text(dc, P1_NAME, "rescue_word", _wort_aus_ansichten(_views(dc)))

    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] != task_id
    assert dc.health == 115
    assert res["score_gain"] == 100 * TASK_MULTIPLIER["data_rescue"]


def test_word_is_case_insensitive_and_trimmed(dc):
    assert _text(dc, P1_NAME, "rescue_word", "  rente ")["result"] == "correct"


def test_wrong_word_costs_health(dc):
    assert _text(dc, P1_NAME, "rescue_word", "RENTEN")["result"] == "wrong"
    assert dc.health == 240


def test_rot13_word_costs_health(dc):
    falsch = _wort_aus_ansichten(_views(dc), k_override=13)
    assert _text(dc, P1_NAME, "rescue_word", falsch)["result"] == "wrong"
    assert dc.health == 240


def test_word_without_shifting_back_costs_health(dc):
    """Nur ASCII, ohne ④ – das ist noch das verschlüsselte Wort."""
    falsch = _wort_aus_ansichten(_views(dc), k_override=0)
    assert _text(dc, P1_NAME, "rescue_word", falsch)["result"] == "wrong"


def test_empty_input_is_ignored(dc):
    assert _text(dc, P1_NAME, "rescue_word", "   ")["result"] == "ignored"
    assert dc.health == 300


# ------------------------------------------------------------------ Rollen
def test_only_vorderseite_types_the_word(dc):
    assert _text(dc, MASTER_NAME, "rescue_word", "RENTE")["result"] == "ignored"
    assert _text(dc, P2_NAME, "rescue_word", "RENTE")["result"] == "ignored"
    assert dc.health == 300


def test_old_targets_are_gone(dc):
    for target in ("ascii_answer", "binary_answer", "sync_button"):
        assert _text(dc, P1_NAME, target, "RENTE")["result"] == "ignored"
    assert dc.health == 300
