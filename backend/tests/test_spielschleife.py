"""Stabilität rund um die Spielschleife (fix/spielschleife).

- tick ändert nur eine laufende Runde (kein Zeitabzug nach Sieg/Neustart) und legt
  keinen abgelaufenen Spielstand neu an
- eine Runde ohne Spieler (z. B. verlassene DEV-Runde) kommt nie ins Leaderboard
- Eingaben, die nach dem Sieg noch unterwegs sind, werden ignoriert (keine −60)
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2
from backend.schemas import PlayerInput

GAME = "schleife_session"


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


@pytest.mark.parametrize("status", ["won", "game_over", "waiting", "briefing"])
def test_tick_only_changes_a_running_game(dc, status):
    dc.redis.r.hset(dc._key, mapping={"status": status, "time_left": 50, "health": 200})
    dc.tick()
    assert dc.time_left == 50
    assert dc.health == 200
    assert dc.status == status


def test_tick_does_not_recreate_an_expired_game(dc):
    dc.redis.r.delete(dc._key)
    dc.tick()
    assert not dc.redis.r.exists(dc._key)


def test_round_without_players_is_not_recorded(dc, tmp_path, monkeypatch):
    monkeypatch.setenv("LEADERBOARD_FILE", str(tmp_path / "lb.json"))
    dc.redis.r.delete(dc.redis._k_players(GAME))
    board = dc.record_result("meltdown", dc.snapshot())
    assert board["rank"] is None
    assert board["top"] == [] and board["total"] == 0


def test_round_with_players_is_still_recorded(dc, tmp_path, monkeypatch):
    monkeypatch.setenv("LEADERBOARD_FILE", str(tmp_path / "lb.json"))
    board = dc.record_result("meltdown", dc.snapshot())
    assert board["rank"] == 1 and board["total"] == 1


def test_input_arriving_after_the_win_is_ignored(dc):
    """Die Status-Prüfung lief schon, dann hat ein anderer Spieler gewonnen:
    unter der Sperre wird neu geprüft – keine −60 auf die Endpunkte."""
    dc.redis.r.hset(dc._key, "status", "won")
    dc.redis.r.hdel(dc._key, "task")
    data = PlayerInput.model_validate({"action_type": "button_press", "target": "main_switch", "value": "x"})
    res = dc._apply_input("Ben", data)
    assert res["result"] == "ignored"
    assert dc.health == dc.max_health
