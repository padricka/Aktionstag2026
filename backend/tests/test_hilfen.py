"""Hilfe-Notizen (GAME_DESIGN.md, Abschnitt „Hilfe-Notizen“).

Zu jeder Aufgabe kann der Host am Beamer Hilfe-Notizen öffnen – der Reihe nach,
immer konkreter. Jede geöffnete Hilfe kostet HINT_COST Punkte (DEV-Modus: gratis).
Anzahl: Aufgabe 1 → 4, Aufgabe 2 → 5, Aufgabe 3 → 6, Finale → keine.
Die Texte passen zur laufenden Runde (sie nennen z. B. den Platz, der wirklich brennt).
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, HINT_COST, tick_payload
from backend.playableObject import (
    AlarmTask, FireProtocolTask, DataRescueTask, RebootTask, ROLE_M, ROLE_P1, ROLE_P2,
)

GAME = "hilfe_session"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in (("Anna", ROLE_M), ("Ben", ROLE_P1), ("Celim", ROLE_P2)):
            center.redis.r.hset(center.redis._k_players(GAME), name, json.dumps({"name": name, "role": role}))
        center.start()
        yield center


def _hints(dc):
    return dc.snapshot()["hints"]


# ------------------------------------------------------------------ Anzahl und Inhalt
@pytest.mark.parametrize("cls, anzahl", [(AlarmTask, 4), (FireProtocolTask, 5), (DataRescueTask, 6)])
def test_each_task_has_its_number_of_hints(cls, anzahl):
    for _ in range(50):
        hilfen = cls.hints(cls.create({}))
        assert len(hilfen) == anzahl == cls.HINTS
        assert all(isinstance(h, str) and len(h) > 20 for h in hilfen)
        assert len(set(hilfen)) == anzahl


def test_finale_has_no_hints():
    assert RebootTask.HINTS == 0
    assert RebootTask.hints(RebootTask.create({}, digits=[1, 2, 3])) == []


def test_alarm_hints_fit_the_round():
    for _ in range(50):
        st = AlarmTask.create({})
        h = AlarmTask.hints(st)
        cut_slot = AlarmTask._cut_index(st["burning_slot"] - 1) + 1
        assert f"Platz {cut_slot}" in h[1]                        # welches Kabel
        order = list(reversed(st["color_order"])) if st["led"] == "blinkt" else st["color_order"]
        assert " → ".join(order) in h[2]                         # Farbfolge in Code-Reihenfolge
        assert AlarmTask.SYMBOL_NAMES[st["solution"][0]] in h[3]  # erstes Code-Symbol


def test_fire_hints_fit_the_round():
    for _ in range(50):
        st = FireProtocolTask.create({})
        h = FireProtocolTask.hints(st)
        probe = next(e for e in st["log"] if e["test"])
        assert probe["time"] in h[1] and probe["rack"] in h[1]
        assert " → ".join(s["rack"] for s in st["sequence"]) in h[2]
        assert "CO2" in h[3]
        for s in st["sequence"]:
            assert f"{s['rack']}: {s['agent']}" in h[4]


def test_rescue_hints_fit_the_round():
    for _ in range(50):
        st = DataRescueTask.create({})
        h = DataRescueTask.hints(st)
        assert st["serial"] in h[1]
        assert f"0x{ord(st['login'][0]):02X}" in h[2] and f"= {st['login'][0]}" in h[2]
        assert f"Paket {st['corrupt'] + 1}" in h[3]
        assert f"k = {st['k']}" in h[4]
        assert st["word"][0] in h[5]


def test_first_hint_gives_only_the_direction():
    """Hilfe 1 verrät nichts aus der Runde – erst die späteren werden konkret."""
    for _ in range(30):
        st = DataRescueTask.create({})
        erste = DataRescueTask.hints(st)[0]
        assert st["serial"] not in erste and st["login"] not in erste
        st = AlarmTask.create({})
        assert "Platz" not in AlarmTask.hints(st)[0]


# ------------------------------------------------------------------ Öffnen über das DataCenter
def test_snapshot_shows_count_but_no_text_before_opening(dc):
    assert _hints(dc) == {"total": 4, "opened": [], "cost": HINT_COST}


def test_opening_reveals_hints_in_order_and_costs_points(dc):
    alle = AlarmTask.hints(dc.current_task()["state"])
    assert dc.open_hint()["result"] == "opened"
    assert dc.open_hint()["result"] == "opened"
    assert _hints(dc)["opened"] == alle[:2]
    assert dc.snapshot()["hint_penalty"] == 2 * HINT_COST


def test_score_shown_is_reduced_by_the_hints(dc):
    vorher = dc.snapshot()["score"]
    dc.open_hint()
    assert dc.snapshot()["score"] == vorher - HINT_COST


def test_score_never_shows_negative(dc):
    dc.redis.r.hset(dc._key, "health", 0)
    dc.open_hint()
    assert dc.snapshot()["score"] == 0


def test_no_more_than_the_available_hints(dc):
    for _ in range(4):
        assert dc.open_hint()["result"] == "opened"
    res = dc.open_hint()
    assert res["result"] == "error"
    assert dc.snapshot()["hint_penalty"] == 4 * HINT_COST


def test_hints_are_free_in_dev_mode(dc):
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    assert dc.open_hint()["result"] == "opened"
    assert len(_hints(dc)["opened"]) == 1
    assert dc.snapshot()["hint_penalty"] == 0


def test_next_task_starts_with_closed_hints_but_keeps_the_penalty(dc):
    dc.open_hint()
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    dc.skip_task()
    assert _hints(dc) == {"total": 5, "opened": [], "cost": HINT_COST}
    assert dc.snapshot()["hint_penalty"] == HINT_COST


def test_finale_offers_no_hints(dc):
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    for _ in range(3):
        dc.skip_task()
    assert dc.current_task()["kind"] == "reboot"
    assert _hints(dc)["total"] == 0
    assert dc.open_hint()["result"] == "error"


def test_no_hints_when_game_is_not_running(dc):
    dc.finish()
    assert dc.open_hint()["result"] == "error"


def test_new_game_resets_the_penalty(dc):
    dc.open_hint()
    dc.start()
    assert dc.snapshot()["hint_penalty"] == 0


def test_tick_payload_carries_the_hints(dc):
    dc.open_hint()
    payload = tick_payload(dc.snapshot())
    assert payload["hints"]["total"] == 4
    assert len(payload["hints"]["opened"]) == 1
