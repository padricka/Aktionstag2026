import asyncio
import uuid
from channels.layers import get_channel_layer
from backend.redis_handler import RedisHandler
from backend.dataCenter import DataCenter   # ← Modul-Ebene (Test kann patchen)

games: dict[str, "GameLoop"] = {}


class GameLoop:
    def __init__(self, game_id: str | None = None):
        self.game_id = game_id
        self.loop_task = None
        self.data_center = None

    @property
    def is_active(self) -> bool:
        return self.loop_task is not None and not self.loop_task.done()

    async def start_game(self):
        if self.game_id is None:
            self.game_id = str(uuid.uuid4())
        self.data_center = await asyncio.to_thread(DataCenter, self.game_id)
        await asyncio.to_thread(self.data_center.start)

        self.loop_task = asyncio.create_task(self._run_tick_loop())
        print(f"[GAMELOOP] Game started with ID: {self.game_id}")
        return self.game_id

    async def _run_tick_loop(self):
        channel_layer = get_channel_layer()
        group = f"game_{self.game_id}"

        async def send_game_over(result, snap):
            await channel_layer.group_send(group, {
                "type": "game.over",
                "payload": {
                    "result": result,
                    "score": snap["score"],
                    "survived_seconds": snap["survived_seconds"],
                },
            })
            print(f"[GAMELOOP] Game over: {result}")

        try:
            while True:
                await asyncio.sleep(1)

                current_status = await asyncio.to_thread(lambda: self.data_center.status)
                if current_status == "game_over":
                    snap = await asyncio.to_thread(self.data_center.snapshot)
                    await send_game_over("meltdown", snap)
                    break
                if current_status == "won":
                    snap = await asyncio.to_thread(self.data_center.snapshot)
                    await send_game_over("victory", snap)
                    break

                snap = await asyncio.to_thread(self.data_center.tick)
                print(f"[GAMELOOP] Tick: {snap['health']} HP, {snap['time_left']}s")

                await channel_layer.group_send(group, {
                    "type": "game.tick",
                    "status": "alive",
                    "payload": {
                        "health": snap["health"],
                        "time_left": snap["time_left"],
                        "tasks": snap["tasks"],
                        "reboot_digits": snap.get("reboot_digits", [None, None, None]),
                    },
                })

                if snap["health"] <= 0:
                    await send_game_over("meltdown", snap)
                    break
                if snap["time_left"] <= 0:
                    await asyncio.to_thread(self.data_center.finish)
                    await send_game_over("meltdown", snap)
                    break

        except asyncio.CancelledError:
            print("[GAMELOOP] Game loop was cancelled.")
            raise
        except Exception as e:
            print(f"[GAMELOOP] Error in game loop: {e}")
        finally:
            if games.get(self.game_id) is self:
                games.pop(self.game_id, None)

    async def stop_game(self):
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
            print("[GAMELOOP] Game loop stopped.")


async def start_game_for(game_id: str) -> str:
    """Rückgabe: "started" | "not_found" | "already_running" """
    redis = RedisHandler()
    state_key = redis._k_state(game_id)

    if not await asyncio.to_thread(redis.r.exists, state_key):
        return "not_found"

    existing = games.get(game_id)
    if existing and existing.is_active:
        return "already_running"

    game = GameLoop(game_id)
    games[game_id] = game

    try:
        await game.start_game()
    except Exception as e:
        games.pop(game_id, None)
        raise e

    payload = await asyncio.to_thread(redis.get_lobby_payload, game_id)
    await get_channel_layer().group_send(
        f"game_{game_id}", {"type": "lobby_update", "payload": payload}
    )
    return "started"