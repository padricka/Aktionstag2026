import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from backend.redis_handler import ROLES
from backend.hostManager import HostManager
from backend.multiplayerManager import MultiplayerManager
from backend.gameLoop import games

# Close-Code, wenn die Sitzungs-ID nicht existiert (4000-4999 = anwendungsspezifisch)
CLOSE_UNKNOWN_GAME = 4404


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = f"game_{self.game_id}"
        self.lobby = MultiplayerManager(self.game_id)
        self.host = HostManager()
        self.data_center = None
        self.player_name = None
        self.role = None
        self.closed = False

        await self.accept()
        # Vertippte ID: nicht still eine leere Lobby anlegen. Erst annehmen, dann
        # schließen, damit der Browser die Fehlermeldung noch lesen kann.
        if not await self.lobby.exists():
            self.closed = True
            await self.send_error("Unbekannte Sitzungs-ID", code="unknown_game")
            await self.close(code=CLOSE_UNKNOWN_GAME)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        payload = await self.lobby.lobby_payload()
        await self.send_event("lobby_update", payload)
        if payload["status"] == "running":
            from backend.dataCenter import DataCenter
            self.data_center = await asyncio.to_thread(DataCenter, self.game_id)
            snap = await asyncio.to_thread(self.data_center.snapshot)
            await self.send_event("game_tick", {
                "health": snap["health"],
                "time_left": snap["time_left"],
                "tasks": self._tasks_for_me(snap["tasks"]),
                "reboot_digits": snap.get("reboot_digits", [None, None, None]),
            }, status="alive")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # Wer noch keine Rolle hat, blockiert sonst einen der 3 Plätze (z. B. Tab geschlossen)
        if self.player_name and not self.role:
            if await self.lobby.release_player(self.player_name, self.channel_name):
                payload = await self.lobby.lobby_payload()
                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "lobby_update", "payload": payload}
                )

    async def receive(self, text_data=None, bytes_data=None):
        if self.closed:
            return
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self.send_error("invalid json")
            return
        if not isinstance(data, dict):
            await self.send_error("invalid json")
            return

        event = data.get("event")
        payload = data.get("payload") or {}
        if not isinstance(payload, dict):
            await self.send_error("invalid payload")
            return

        if event == "ping":
            await self.send_event("pong", {})
        elif event == "host_register":
            await self.handle_host_register()
        elif event == "player_register":
            await self.handle_player_register(payload)
        elif event == "choose_role":
            await self.handle_choose_role(payload)
        elif event == "owner_settings":
            await self.handle_owner_settings(payload)
        elif event == "player_input":
            await self.handle_player_input(payload)
        elif event == "start_game":
            await self.handle_start_game()
        elif event in ("reset_game", "new_lobby"):
            await self.handle_reset_lobby()
        else:
            await self.send_error(f"unknown event: {event}")

    async def handle_host_register(self):
        payload = await self.lobby.lobby_payload()
        await self.send_event("lobby_update", payload)

    async def handle_reset_lobby(self):
        game = games.pop(self.game_id, None)
        if game:
            await game.stop_game()
        await asyncio.to_thread(self.lobby.redis.create_game, self.game_id)
        payload = await self.lobby.lobby_payload()
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "lobby_update", "payload": payload}
        )

    async def handle_player_register(self, payload):
        name = payload.get("player_name")
        if not name or not isinstance(name, str):
            await self.send_error("player_name required")
            return

        result = await self.lobby.register_player(name, self.channel_name)
        if result["event"] == "error":
            await self.send_error(result["payload"]["message"])
            return

        self.player_name = name
        self.role = result.get("role")  # None bis choose_role

        # Reconnect mit bereits gewählter Rolle
        if self.role:
            await self.send_event("role_assigned", {
                "player_name": name,
                "role": self.role,
                "hints": await self.lobby.role_hints(self.role),
            })

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "lobby_update", "payload": result["payload"]}
        )

        if result["payload"].get("status") == "running":
            if self.data_center is None:
                from backend.dataCenter import DataCenter
                self.data_center = await asyncio.to_thread(DataCenter, self.game_id)
            snap = await asyncio.to_thread(self.data_center.snapshot)
            await self.send_event("game_tick", {
                "health": snap["health"],
                "time_left": snap["time_left"],
                "tasks": self._tasks_for_me(snap["tasks"]),
                "reboot_digits": snap.get("reboot_digits", [None, None, None]),
            }, status="alive")

    async def handle_choose_role(self, payload):
        if not self.player_name:
            await self.send_error("not registered")
            return
        role = payload.get("role")
        if not role:
            await self.send_error("role required")
            return

        result = await self.lobby.choose_role(self.player_name, role)
        if result["event"] == "error":
            await self.send_error(result["payload"]["message"])
            return

        self.role = result["role"]

        await self.send_event("role_assigned", {
            "player_name": self.player_name,
            "role": self.role,
            "hints": await self.lobby.role_hints(self.role),
        })
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "lobby_update", "payload": result["payload"]}
        )

    async def handle_owner_settings(self, payload):
        result = await self.lobby.set_settings(payload)
        if result["event"] == "error":
            await self.send_error(result["payload"]["message"])
            return
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "lobby_update", "payload": result["payload"]}
        )

    async def handle_player_input(self, payload):
        if not self.player_name or not self.role:
            await self.send_error("Rolle muss zuerst gewählt werden")
            return
        if self.data_center is None:
            from backend.dataCenter import DataCenter
            self.data_center = await asyncio.to_thread(DataCenter, self.game_id)

        result = await asyncio.to_thread(
            self.data_center.process_input, self.player_name, payload
        )
        if result["result"] == "error":
            await self.send_event("input_result", {"result": result["result"]})
            await self.send_error(result["message"])
            return

        await self.send_event("input_result", {"result": result["result"]})

        if result.get("won"):
            snap = await asyncio.to_thread(self.data_center.snapshot)
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "game.over",
                "payload": {
                    "result": "victory",
                    "score": snap["score"],
                    "survived_seconds": snap["survived_seconds"],
                },
            })
            return

        snap = await asyncio.to_thread(self.data_center.snapshot)

        if snap["health"] <= 0 or self.data_center.status == "game_over":
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "game.over",
                "payload": {
                    "result": "meltdown",
                    "score": snap["score"],
                    "survived_seconds": snap["survived_seconds"],
                },
            })
        else:
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "game.tick",
                "status": "alive",
                "payload": {
                    "health": snap["health"],
                    "time_left": snap["time_left"],
                    "tasks": snap["tasks"],
                },
            })

    async def handle_start_game(self):
        payload = await self.lobby.lobby_payload()
        if not payload.get("ready_to_start"):
            await self.send_error(f"Es werden {len(ROLES)} Spieler mit Rollen benötigt")
            return

        result = await self.host.start(self.game_id)
        if result != "started":
            await self.send_error(f"start failed: {result}")

    def _tasks_for_me(self, tasks):
        out = []
        for task in tasks or []:
            mine = {k: v for k, v in task.items() if k != "views"}
            view = (task.get("views") or {}).get(self.role)
            if view is not None:
                mine["view"] = view
            out.append(mine)
        return out

    async def send_event(self, event, payload, **extra):
        await self.send(text_data=json.dumps({"event": event, **extra, "payload": payload}))

    async def send_error(self, message, code=None):
        payload = {"message": message}
        if code:
            payload["code"] = code
        await self.send_event("error", payload)

    async def lobby_update(self, event):
        await self.send_event("lobby_update", event["payload"])

    async def game_tick(self, event):
        payload = dict(event["payload"])
        payload["tasks"] = self._tasks_for_me(payload.get("tasks"))
        await self.send_event("game_tick", payload, status=event.get("status", "alive"))

    async def game_over(self, event):
        await self.send_event("game_over", event["payload"])