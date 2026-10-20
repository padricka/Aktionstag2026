import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from backend.redis_handler import ROLES
from backend.hostManager import HostManager
from backend.multiplayerManager import MultiplayerManager
from backend.dataCenter import tick_payload
from backend.gameLoop import announce_game_over, games, resume_game_for

# Close-Code, wenn die Sitzungs-ID nicht existiert (4000-4999 = anwendungsspezifisch)
CLOSE_UNKNOWN_GAME = 4404

# Offene Verbindungen dieses Servers (channel_name). Damit erkennt player_register, ob
# ein gleichnamiger Spieler auf einem anderen Gerät noch da ist (Name vergeben).
_live_conns = set()


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # IDs werden klein erzeugt, der Beamer zeigt sie groß: Schreibweise egal
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"].lower()
        self.room_group_name = f"game_{self.game_id}"
        self.lobby = MultiplayerManager(self.game_id)
        self.host = HostManager()
        self.data_center = None
        self.player_name = None
        self.role = None
        self.is_host = False
        self.closed = False

        await self.accept()
        _live_conns.add(self.channel_name)
        # Vertippte ID: nicht still eine leere Lobby anlegen. Erst annehmen, dann
        # schließen, damit der Browser die Fehlermeldung noch lesen kann.
        if not await self.lobby.exists():
            self.closed = True
            await self.send_error("Unbekannte Sitzungs-ID", code="unknown_game")
            await self.close(code=CLOSE_UNKNOWN_GAME)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        payload = await self.lobby.lobby_payload()
        if payload["status"] == "running":
            # Server neu gestartet? Dann läuft keine Schleife mehr – wieder anhängen
            await resume_game_for(self.game_id)
        if payload["status"] in ("won", "game_over"):
            # Erst das echte Ergebnis, dann der Status – sonst zeigt die Ansicht kurz
            # „Niederlage, 0 Punkte“ (Default) statt z. B. des Siegs
            from backend.dataCenter import DataCenter
            ergebnis = await asyncio.to_thread(lambda: DataCenter(self.game_id).last_game_over())
            if ergebnis:
                await self.send_event("game_over", ergebnis)
        await self.send_event("lobby_update", payload)
        if payload["status"] == "running":
            from backend.dataCenter import DataCenter
            self.data_center = await asyncio.to_thread(DataCenter, self.game_id)
            snap = await asyncio.to_thread(self.data_center.snapshot)
            await self._send_own_tick(snap)

    async def disconnect(self, close_code):
        _live_conns.discard(self.channel_name)
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if self.is_host:
            await asyncio.to_thread(self.lobby.redis.drop_host, self.game_id, self.channel_name)
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
        elif event == "host_ping":
            await self.handle_host_ping()
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
        elif event == "dev_mode":
            await self.handle_dev_mode(payload)
        elif event == "open_hint":
            await self.handle_open_hint(payload)
        elif event == "dev_skip_task":
            await self.handle_dev_skip_task()
        else:
            await self.send_error(f"unknown event: {event}")

    async def handle_host_register(self):
        self.is_host = True
        await asyncio.to_thread(self.lobby.redis.mark_host, self.game_id, self.channel_name)
        payload = await self.lobby.lobby_payload()
        await self.send_event("lobby_update", payload)

    async def handle_host_ping(self):
        """Beamer meldet sich regelmäßig (alle ~10 s): Anwesenheit verlängern."""
        if self.is_host:
            await asyncio.to_thread(self.lobby.redis.mark_host, self.game_id, self.channel_name)

    # ------------------------------------------------------------ DEV-Modus (nur Host)
    async def handle_dev_mode(self, payload):
        enabled = payload.get("enabled")
        if not self.is_host or not isinstance(enabled, bool):
            await self.send_error("DEV-Modus nur vom Host (enabled: true/false)", code="dev_denied")
            return
        result = await asyncio.to_thread(self.lobby.redis.set_dev_mode, self.game_id, enabled)
        if result["event"] == "error":
            await self.send_error(result["payload"]["message"], code="dev_denied")
            return
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "lobby_update", "payload": result["payload"]}
        )

    async def handle_dev_skip_task(self):
        if not self.is_host:
            await self.send_error("Überspringen nur vom Host", code="dev_denied")
            return
        if self.data_center is None:
            from backend.dataCenter import DataCenter
            self.data_center = await asyncio.to_thread(DataCenter, self.game_id)

        result = await asyncio.to_thread(self.data_center.skip_task)
        if result["result"] == "error":
            await self.send_error(result["message"], code="dev_denied")
            return
        if result["result"] == "ignored":
            return

        snap = await asyncio.to_thread(self.data_center.snapshot)
        if result["won"]:
            await announce_game_over(self.data_center, self.game_id, "victory", snap)
            return
        await self._broadcast_tick(snap)

    # ------------------------------------------------------------ Hilfe-Notizen (nur Host)
    async def handle_open_hint(self, payload):
        if not self.is_host:
            await self.send_error("Hilfen öffnet nur der Host", code="hint_denied")
            return
        if self.data_center is None:
            from backend.dataCenter import DataCenter
            self.data_center = await asyncio.to_thread(DataCenter, self.game_id)

        payload = payload or {}
        result = await asyncio.to_thread(
            self.data_center.open_hint, payload.get("id"), payload.get("task_id")
        )
        if result["result"] != "opened":
            await self.send_error(result["message"], code="hint_denied")
            return
        await self._broadcast_tick(await asyncio.to_thread(self.data_center.snapshot))

    async def handle_reset_lobby(self):
        # Spieler dürfen nur eine beendete Runde neu starten; eine laufende Runde
        # (oder die Einsatzbesprechung) beendet nur der Beamer
        if not self.is_host:
            status = (await self.lobby.lobby_payload())["status"]
            if status in ("running", "briefing"):
                await self.send_error("Eine laufende Runde kann nur der Beamer beenden", code="reset_denied")
                return
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

        client = payload.get("client_id") if isinstance(payload.get("client_id"), str) else None
        if await self._name_besetzt(name, client):
            await self.send_error("Name schon vergeben – bitte einen anderen wählen", code="register_denied")
            return

        result = await self.lobby.register_player(name, self.channel_name, client)
        if result["event"] == "error":
            await self.send_error(result["payload"]["message"], code="register_denied")
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
            await self._send_own_tick(snap)

    async def _name_besetzt(self, name, client):
        """In der Lobby darf ein Name nur einmal da sein: Meldet sich ein anderer Tab
        (andere client_id) mit dem Namen an, während dessen Verbindung noch offen ist,
        ist das ein zweiter Spieler. Derselbe Tab (Neuladen) darf immer. Läuft das
        Spiel, gilt es als Wiederkehr (z. B. anderes Gerät) und die neue Verbindung übernimmt."""
        status = (await self.lobby.lobby_payload())["status"]
        if status not in ("waiting", "ready", "briefing"):
            return False
        players = await asyncio.to_thread(self.lobby.redis._load_players, self.game_id)
        bekannt = players.get(name) or {}
        conn, alter_client = bekannt.get("conn"), bekannt.get("client")
        if not (client and alter_client) or client == alter_client:
            return False
        return bool(conn) and conn != self.channel_name and conn in _live_conns

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
        if not self.is_host:
            await self.send_error("Einstellungen ändert nur der Beamer", code="settings_denied")
            return
        if (await self.lobby.lobby_payload())["status"] not in ("waiting", "ready"):
            await self.send_error("Einstellungen nur vor dem Start änderbar", code="settings_denied")
            return
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

        antwort = {"result": result["result"]}
        if result.get("message"):
            antwort["message"] = result["message"]   # was falsch war (z. B. „Stromschlag!“)
        await self.send_event("input_result", antwort)

        snap = await asyncio.to_thread(self.data_center.snapshot)

        if result.get("won"):
            await announce_game_over(self.data_center, self.game_id, "victory", snap)
        elif snap["health"] <= 0 or self.data_center.status == "game_over":
            await announce_game_over(self.data_center, self.game_id, "meltdown", snap)
        else:
            await self._broadcast_tick(snap)

    async def handle_start_game(self):
        payload = await self.lobby.lobby_payload()
        if not payload.get("ready_to_start"):
            await self.send_error(f"Es werden {len(ROLES)} Spieler mit Rollen benötigt", code="start_failed")
            return

        # Mit Beamer: erst die Einsatzbesprechung (Intro), der Host startet danach.
        # Ohne Beamer (oder vom Host selbst) startet das Spiel sofort.
        if not self.is_host and payload["status"] in ("ready", "briefing"):
            beamer = await asyncio.to_thread(self.lobby.redis.hosts_online, self.game_id)
            if beamer:
                if await asyncio.to_thread(self.lobby.redis.begin_briefing, self.game_id):
                    await self.channel_layer.group_send(self.room_group_name, {
                        "type": "lobby_update", "payload": await self.lobby.lobby_payload(),
                    })
                else:
                    # Besprechung läuft schon und der Beamer ist da: gestartet wird dort
                    await self.send_error("Die Einsatzbesprechung läuft am Beamer – gestartet wird dort.")
                return

        result = await self.host.start(self.game_id)
        if result != "started":
            meldung = {"not_ready": "Lobby nicht vollständig – alle drei Rollen nötig.",
                       "already_running": "Das Spiel läuft bereits.",
                       "not_found": "Sitzung nicht gefunden."}.get(result, f"Start fehlgeschlagen: {result}")
            await self.send_error(meldung, code="start_failed")

    async def _send_own_tick(self, snap):
        """Aktueller Stand nur an diese Verbindung (später Beitritt / Reconnect)."""
        payload = tick_payload(snap)
        payload["tasks"] = self._tasks_for_me(payload["tasks"])
        await self.send_event("game_tick", payload, status="alive")

    async def _broadcast_tick(self, snap):
        """Sofort-Tick an alle; die Ansichten filtert jede Verbindung in game_tick selbst."""
        await self.channel_layer.group_send(self.room_group_name, {
            "type": "game.tick",
            "status": "alive",
            "payload": tick_payload(snap),
        })

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