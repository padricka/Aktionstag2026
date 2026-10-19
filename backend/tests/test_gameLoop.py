# test_gameLoop.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.gameLoop import GameLoop, games, start_game_for

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------- Fixtures / Helfer
@pytest.fixture(autouse=True)
def clean_games():
    games.clear()
    yield
    games.clear()


@pytest.fixture
def channel_layer():
    layer = MagicMock()
    layer.group_send = AsyncMock()
    with patch("backend.gameLoop.get_channel_layer", return_value=layer):
        yield layer


@pytest.fixture
def fast_sleep():
    real_sleep = asyncio.sleep

    async def _sleep(_):
        await real_sleep(0)

    with patch("backend.gameLoop.asyncio.sleep", _sleep):
        yield


@pytest.fixture
def redis_mock():
    with patch("backend.gameLoop.RedisHandler") as cls:
        inst = cls.return_value
        inst._k_state.return_value = "game:x:state"
        inst.r.exists.return_value = 1
        inst.get_lobby_payload.return_value = {
            "status": "running", "players": [], "ready_to_start": False,
        }
        yield inst


def snap(health=300, time_left=300, survived=0):
    return {"health": health, "time_left": time_left,
            "survived_seconds": survived, "tasks": [], "score": 0}


def fake_dc(status="running", ticks=()):
    dc = MagicMock()
    dc.status = status
    dc.tick.side_effect = list(ticks)
    dc.snapshot.return_value = snap(0, 0, 42)
    return dc


def game_with(dc):
    game = GameLoop("g1")
    game.data_center = dc
    return game


async def _noop(self):
    return


# ---------------------------------------------------------------- __init__ / is_active
async def test_init_defaults():
    game = GameLoop()
    assert game.game_id is None
    assert game.loop_task is None
    assert game.data_center is None


async def test_is_active_states():
    game = GameLoop("g1")
    assert game.is_active is False                       # kein Task

    game.loop_task = asyncio.create_task(asyncio.Event().wait())
    assert game.is_active is True                        # Task läuft

    game.loop_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await game.loop_task
    assert game.is_active is False                       # Task fertig


# ---------------------------------------------------------------- start_game
async def test_start_game_generates_uuid_when_no_id():
    dc = MagicMock()
    with patch("backend.gameLoop.DataCenter", return_value=dc), \
         patch.object(GameLoop, "_run_tick_loop", _noop):
        game = GameLoop()
        game_id = await game.start_game()
        await game.loop_task

    assert game_id == game.game_id
    assert len(game_id) == 36                            # uuid4-String


async def test_start_game_keeps_given_id_and_starts_datacenter():
    dc = MagicMock()
    with patch("backend.gameLoop.DataCenter", return_value=dc) as dc_cls, \
         patch.object(GameLoop, "_run_tick_loop", _noop):
        game = GameLoop("mein_spiel")
        assert await game.start_game() == "mein_spiel"
        await game.loop_task

    dc_cls.assert_called_once_with("mein_spiel")
    dc.start.assert_called_once()
    assert game.data_center is dc


# ---------------------------------------------------------------- _run_tick_loop
async def test_loop_sends_game_over_when_status_already_game_over(channel_layer, fast_sleep):
    dc = fake_dc(status="game_over")
    await game_with(dc)._run_tick_loop()

    dc.tick.assert_not_called()
    channel_layer.group_send.assert_awaited_once_with("game_g1", {
        "type": "game.over",
        "payload": {"result": "meltdown", "score": 0, "survived_seconds": 42,
                    "leaderboard": dc.record_result.return_value},
    })
    dc.record_result.assert_called_once_with("meltdown", dc.snapshot.return_value)


async def test_loop_game_over_when_health_reaches_zero(channel_layer, fast_sleep):
    dc = fake_dc(ticks=[snap(health=0, time_left=200, survived=7)])
    await game_with(dc)._run_tick_loop()

    types = [c.args[1]["type"] for c in channel_layer.group_send.await_args_list]
    assert types == ["game.tick", "game.over"]
    over = channel_layer.group_send.await_args_list[1].args[1]["payload"]
    assert over == {"result": "meltdown", "score": 0, "survived_seconds": 7,
                    "leaderboard": dc.record_result.return_value}
    dc.finish.assert_not_called()


async def test_game_over_is_sent_even_if_leaderboard_fails(channel_layer, fast_sleep):
    """Kaputte Datei o. Ä. darf das Spielende nicht verhindern."""
    dc = fake_dc(status="game_over")
    dc.record_result.side_effect = OSError("Platte voll")
    await game_with(dc)._run_tick_loop()

    over = channel_layer.group_send.await_args_list[0].args[1]["payload"]
    assert over["result"] == "meltdown"
    assert over["leaderboard"] is None


async def test_loop_finishes_when_time_runs_out(channel_layer, fast_sleep):
    dc = fake_dc(ticks=[snap(health=10, time_left=0, survived=300)])
    await game_with(dc)._run_tick_loop()

    dc.finish.assert_called_once()
    types = [c.args[1]["type"] for c in channel_layer.group_send.await_args_list]
    assert types == ["game.tick", "game.over"]


async def test_loop_keeps_ticking_until_game_over(channel_layer, fast_sleep):
    dc = fake_dc(ticks=[snap(5, 5), snap(0, 4)])
    await game_with(dc)._run_tick_loop()

    assert dc.tick.call_count == 2
    types = [c.args[1]["type"] for c in channel_layer.group_send.await_args_list]
    assert types == ["game.tick", "game.tick", "game.over"]


async def test_loop_swallows_unexpected_exception(channel_layer, fast_sleep, capsys):
    dc = fake_dc()
    dc.tick.side_effect = RuntimeError("boom")

    await game_with(dc)._run_tick_loop()                 # darf nicht raisen

    assert "Error in game loop: boom" in capsys.readouterr().out
    channel_layer.group_send.assert_not_awaited()


async def test_loop_reraises_cancelled_error(channel_layer):
    with patch("backend.gameLoop.asyncio.sleep",
               AsyncMock(side_effect=asyncio.CancelledError)):
        with pytest.raises(asyncio.CancelledError):
            await game_with(fake_dc())._run_tick_loop()


# ---------------------------------------------------------------- stop_game
async def test_stop_game_without_task_does_nothing():
    await GameLoop("g1").stop_game()


async def test_stop_game_cancels_running_task():
    game = GameLoop("g1")
    game.loop_task = asyncio.create_task(asyncio.Event().wait())
    await asyncio.sleep(0)                               # Task anlaufen lassen

    await game.stop_game()

    assert game.loop_task.cancelled()
    assert game.is_active is False


# ---------------------------------------------------------------- start_game_for
async def test_start_game_for_not_found(redis_mock):
    redis_mock.r.exists.return_value = 0
    assert await start_game_for("x") == "not_found"
    assert "x" not in games


async def test_start_game_for_already_running(redis_mock):
    games["x"] = MagicMock(is_active=True)
    assert await start_game_for("x") == "already_running"


async def test_start_game_for_started_and_notifies_lobby(redis_mock, channel_layer):
    with patch.object(GameLoop, "start_game", new=AsyncMock()):
        assert await start_game_for("x") == "started"

    assert isinstance(games["x"], GameLoop)
    channel_layer.group_send.assert_awaited_once_with("game_x", {
        "type": "lobby_update",
        "payload": redis_mock.get_lobby_payload.return_value,
    })


async def test_start_game_for_replaces_finished_game(redis_mock, channel_layer):
    games["x"] = MagicMock(is_active=False)              # alter, beendeter Loop
    with patch.object(GameLoop, "start_game", new=AsyncMock()):
        assert await start_game_for("x") == "started"
    assert isinstance(games["x"], GameLoop)


async def test_start_game_for_cleans_up_when_start_fails(redis_mock, channel_layer):
    with patch.object(GameLoop, "start_game",
                      new=AsyncMock(side_effect=RuntimeError("kaputt"))):
        with pytest.raises(RuntimeError, match="kaputt"):
            await start_game_for("x")

    assert "x" not in games
    channel_layer.group_send.assert_not_awaited()

async def test_tick_sends_reboot_digits_for_beamer(channel_layer, fast_sleep):
    tick = {**snap(5, 5), "reboot_digits": [4, None, None]}
    dc = fake_dc(ticks=[tick, snap(0, 4)])
    await game_with(dc)._run_tick_loop()

    payload = channel_layer.group_send.await_args_list[0].args[1]["payload"]
    assert payload["reboot_digits"] == [4, None, None]


async def test_tick_without_reboot_digits_sends_empty_slots(channel_layer, fast_sleep):
    dc = fake_dc(ticks=[snap(5, 5), snap(0, 4)])
    await game_with(dc)._run_tick_loop()

    payload = channel_layer.group_send.await_args_list[0].args[1]["payload"]
    assert payload["reboot_digits"] == [None, None, None]
