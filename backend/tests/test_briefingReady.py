"""
Einsatzbesprechung: „Bereit“-Knopf (player_ready) und Startsperre für den Host.
Vertrag: JSON_Vertrag.md, Abschnitt 4 / 4a.
"""
import pytest

from backend.gameLoop import games
from backend.redis_handler import RedisHandler
from tests.test_gameConsumer import (  # noqa: F401  (env/clean_games sind Fixtures)
    beenden, clean_games, env, host_verbinden, recv_until, spieler, state_key,
)

DREI = (("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))


def ready_von(payload, name):
    return next(p["ready"] for p in payload["players"] if p["name"] == name)


async def briefing_oeffnen(gid):
    host = await host_verbinden(gid)
    spielerliste = await spieler(gid, *DREI)
    await spielerliste[0].send_json_to({"event": "start_game", "payload": {}})
    await recv_until(host, "lobby_update", lambda p: p["status"] == "briefing")
    return host, spielerliste


# ---------------------------------------------------------------- Lobby-Payload
def test_lobby_payload_starts_with_nobody_ready(env):
    handler = RedisHandler()
    handler.create_game("rdy_payload")
    handler.register_player("rdy_payload", "A")
    payload = handler.get_lobby_payload("rdy_payload")
    assert payload["all_ready"] is False
    assert payload["players"][0]["ready"] is False


def test_set_ready_is_denied_outside_the_briefing(env):
    handler = RedisHandler()
    handler.create_game("rdy_lobby")
    handler.register_player("rdy_lobby", "A")
    handler.choose_role("rdy_lobby", "A", "MASTER")
    result = handler.set_ready("rdy_lobby", "A", True)
    assert result["event"] == "error"
    assert handler.get_lobby_payload("rdy_lobby")["players"][0]["ready"] is False


# ---------------------------------------------------------------- player_ready
@pytest.mark.asyncio
async def test_ready_is_shown_to_everybody_but_not_all_ready_yet(env):
    gid = "rdy_one"
    host, (a, b, c) = await briefing_oeffnen(gid)
    try:
        await a.send_json_to({"event": "player_ready", "payload": {}})
        msg = await recv_until(host, "lobby_update", lambda p: ready_von(p, "A"))
        assert ready_von(msg["payload"], "B") is False
        assert msg["payload"]["all_ready"] is False
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_all_ready_once_all_three_players_pressed_ready(env):
    gid = "rdy_all"
    host, spielerliste = await briefing_oeffnen(gid)
    try:
        for comm in spielerliste:
            await comm.send_json_to({"event": "player_ready", "payload": {"ready": True}})
        msg = await recv_until(host, "lobby_update", lambda p: p["all_ready"])
        assert all(p["ready"] for p in msg["payload"]["players"])
    finally:
        await beenden(host, *spielerliste, game_ids=[gid])


@pytest.mark.asyncio
async def test_ready_can_be_taken_back(env):
    gid = "rdy_undo"
    host, (a, b, c) = await briefing_oeffnen(gid)
    try:
        await a.send_json_to({"event": "player_ready", "payload": {"ready": True}})
        await recv_until(host, "lobby_update", lambda p: ready_von(p, "A"))
        await a.send_json_to({"event": "player_ready", "payload": {"ready": False}})
        await recv_until(host, "lobby_update", lambda p: not ready_von(p, "A"))
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_ready_outside_the_briefing_is_denied(env):
    gid = "rdy_early"
    (a, b, c) = await spieler(gid, *DREI)
    try:
        await a.send_json_to({"event": "player_ready", "payload": {}})
        msg = await recv_until(a, "error")
        assert msg["payload"]["code"] == "ready_denied"
    finally:
        await beenden(a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_host_cannot_press_ready(env):
    gid = "rdy_host"
    host, (a, b, c) = await briefing_oeffnen(gid)
    try:
        await host.send_json_to({"event": "player_ready", "payload": {}})
        msg = await recv_until(host, "error")
        assert msg["payload"]["code"] == "ready_denied"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_ready_must_be_a_boolean(env):
    gid = "rdy_bad"
    host, (a, b, c) = await briefing_oeffnen(gid)
    try:
        await a.send_json_to({"event": "player_ready", "payload": {"ready": "ja"}})
        msg = await recv_until(a, "error")
        assert msg["payload"]["code"] == "ready_denied"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


# ---------------------------------------------------------------- Startsperre
@pytest.mark.asyncio
async def test_host_cannot_start_until_everybody_is_ready(env):
    gid = "rdy_gate"
    host, (a, b, c) = await briefing_oeffnen(gid)
    try:
        await host.send_json_to({"event": "start_game", "payload": {}})
        msg = await recv_until(host, "error")
        assert msg["payload"]["code"] == "not_ready"
        assert gid not in games
        assert env.hget(state_key(gid), "status").decode() == "briefing"

        for comm in (a, b, c):
            await comm.send_json_to({"event": "player_ready", "payload": {}})
        await recv_until(host, "lobby_update", lambda p: p["all_ready"])
        await host.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(b, "lobby_update", lambda p: p["status"] == "running")
        assert games[gid].is_active
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_dev_mode_lets_the_host_start_without_ready(env):
    gid = "rdy_dev"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, *DREI)
    try:
        await host.send_json_to({"event": "dev_mode", "payload": {"enabled": True}})
        await recv_until(host, "lobby_update", lambda p: p["dev_mode"])
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(host, "lobby_update", lambda p: p["status"] == "briefing")
        await host.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(b, "lobby_update", lambda p: p["status"] == "running")
    finally:
        await beenden(host, a, b, c, game_ids=[gid])
