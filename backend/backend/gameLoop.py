import asyncio
import uuid
from channels.layers import get_channel_layer
from backend.redis_handler import RedisHandler, LOBBY_TTL, _s
from backend.dataCenter import DataCenter, tick_payload   # ← Modul-Ebene (Test kann patchen)

games: dict[str, "GameLoop"] = {}
# Ein Start pro Sitzung gleichzeitig (siehe start_game_for)
_start_locks: dict[str, asyncio.Lock] = {}
# So viele Tick-Fehler hintereinander verkraftet eine Runde, bevor die Schleife aufgibt
MAX_TICK_FEHLER = 5


async def announce_game_over(data_center, game_id: str, result: str, snap: dict) -> bool:
    """game_over an alle, aber nur einmal pro Runde (Consumer und Spielschleife melden beide)."""
    if not await asyncio.to_thread(data_center.claim_game_over):
        return False
    # Nach dem Spielende lebt die Sitzung wieder so lange wie eine Lobby (Ergebnis
    # am Beamer, „Neue Runde“) – im Spiel war die Lebensdauer auf 1 h gesenkt
    try:
        await asyncio.to_thread(data_center.redis.refresh_ttl, game_id, LOBBY_TTL)
    except Exception as e:
        print(f"[GAMELOOP] TTL nicht erneuert: {e}")
    # Genau hier einmal pro Runde: ins Leaderboard eintragen. Ein Fehler dort
    # (z. B. Datei nicht schreibbar) darf das Spielende nicht verhindern.
    try:
        board = await asyncio.to_thread(data_center.record_result, result, snap)
    except Exception as e:
        print(f"[GAMELOOP] Leaderboard nicht gespeichert: {e}")
        board = None
    payload = {
        "result": result,
        "score": snap["score"],
        "survived_seconds": snap["survived_seconds"],
        "leaderboard": board,
    }
    # Für alle, die erst nach dem Spielende (neu) verbinden: das echte Ergebnis statt
    # „Niederlage, 0 Punkte“ (der Consumer schickt es beim Verbinden mit)
    try:
        await asyncio.to_thread(data_center.remember_game_over, payload)
    except Exception as e:
        print(f"[GAMELOOP] Ergebnis nicht gemerkt: {e}")
    await get_channel_layer().group_send(f"game_{game_id}", {"type": "game.over", "payload": payload})
    print(f"[GAMELOOP] Game over: {result}")
    return True


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
        fehler = 0

        async def send_game_over(result, snap):
            await announce_game_over(self.data_center, self.game_id, result, snap)

        try:
            while True:
                await asyncio.sleep(1)
                try:
                    current_status = await asyncio.to_thread(lambda: self.data_center.status)
                    if current_status == "game_over":
                        snap = await asyncio.to_thread(self.data_center.snapshot)
                        await send_game_over("meltdown", snap)
                        break
                    if current_status == "won":
                        snap = await asyncio.to_thread(self.data_center.snapshot)
                        await send_game_over("victory", snap)
                        break
                    if current_status != "running":
                        # Lobby zurückgesetzt oder Spielstand abgelaufen: still aufhören,
                        # kein game_over und kein Leaderboard-Eintrag
                        print(f"[GAMELOOP] Runde {self.game_id} nicht mehr aktiv ({current_status}), Schleife endet.")
                        break

                    snap = await asyncio.to_thread(self.data_center.tick)
                    print(f"[GAMELOOP] Tick: {snap['health']} HP, {snap['time_left']}s")

                    await channel_layer.group_send(group, {
                        "type": "game.tick",
                        "status": "alive",
                        "payload": tick_payload(snap),
                    })

                    if snap["health"] <= 0:
                        await send_game_over("meltdown", snap)
                        break
                    if snap["time_left"] <= 0:
                        await asyncio.to_thread(self.data_center.finish)
                        await send_game_over("meltdown", snap)
                        break
                    fehler = 0
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    # Ein kurzer Redis-/Channel-Fehler darf die Runde nicht beenden
                    fehler += 1
                    if fehler >= MAX_TICK_FEHLER:
                        print(f"[GAMELOOP] Error in game loop: {e}")
                        break
                    print(f"[GAMELOOP] Tick-Fehler {fehler}/{MAX_TICK_FEHLER}: {e}")

        except asyncio.CancelledError:
            print("[GAMELOOP] Game loop was cancelled.")
            raise
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
    """Rückgabe: "started" | "not_found" | "already_running" | "not_ready"

    Pro Sitzung immer nur ein Start gleichzeitig (Sperre): sonst sehen zwei fast
    gleichzeitige Starts beide „keine Schleife aktiv“ und starten zwei Schleifen."""
    async with _start_locks.setdefault(game_id, asyncio.Lock()):
        redis = RedisHandler()
        state_key = redis._k_state(game_id)

        if not await asyncio.to_thread(redis.r.exists, state_key):
            return "not_found"

        existing = games.get(game_id)
        if existing and existing.is_active:
            return "already_running"

        # Nur eine vollständige Lobby (3 Rollen) startet – auch nicht, wenn sie
        # gerade zurückgesetzt wurde (z. B. Neustart genau am Ende des Countdowns)
        lobby = await asyncio.to_thread(redis.get_lobby_payload, game_id)
        if lobby.get("status") == "running":
            return "already_running"
        if not lobby.get("ready_to_start") or lobby.get("status") not in ("ready", "briefing"):
            return "not_ready"

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

async def resume_game_for(game_id: str) -> bool:
    """Nach einem Server-Neustart: Laut Redis läuft die Runde noch („running“), aber keine
    Schleife ist aktiv (die lebte nur im Speicher). Dann die Schleife wieder anhängen –
    ohne DataCenter.start(), die Runde läuft einfach weiter. True, wenn angehängt."""
    async with _start_locks.setdefault(game_id, asyncio.Lock()):
        existing = games.get(game_id)
        if existing and existing.is_active:
            return False
        redis = RedisHandler()
        status = _s(await asyncio.to_thread(redis.r.hget, redis._k_state(game_id), "status"))
        if status != "running":
            return False
        game = GameLoop(game_id)
        game.data_center = await asyncio.to_thread(DataCenter, game_id)
        game.loop_task = asyncio.create_task(game._run_tick_loop())
        games[game_id] = game
        print(f"[GAMELOOP] Runde {game_id} nach Neustart wieder aufgenommen")
        return True
