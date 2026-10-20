import json
import os
import redis
from contextlib import contextmanager

REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 1))

DEFAULT_TIME = 300
ROLES = ["MASTER", "FI-SI", "FI-AE"]

# Eine wartende Lobby lebt lange (Beamer läuft oft stundenlang), ein gestartetes Spiel 1 h.
LOBBY_TTL = 12 * 3600


def _s(val):
    if isinstance(val, bytes):
        return val.decode("utf-8")
    return val


class RedisHandler:
    def __init__(self):
        self.r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=False,
        )

    @contextmanager
    def lock(self, name: str, timeout: float = 5.0, blocking_timeout: float = 3.0):
        lock_obj = self.r.lock(f"lock:{name}", timeout=timeout, blocking_timeout=blocking_timeout)
        acquired = lock_obj.acquire(blocking=True)
        try:
            yield acquired
        finally:
            if acquired:
                try:
                    lock_obj.release()
                except Exception:
                    pass

    def _k_state(self, game_id: str) -> str:
        return f"game:{game_id}:state"

    def _k_players(self, game_id: str) -> str:
        return f"game:{game_id}:players"

    def _k_hints(self, game_id: str, role: str) -> str:
        return f"game:{game_id}:hints:{role.lower()}"

    def create_game(self, game_id: str):
        state_key = self._k_state(game_id)
        players_key = self._k_players(game_id)
        # DEV-Modus gehört zur Sitzung, nicht zur Runde: übersteht den Neustart
        dev_mode = _s(self.r.hget(state_key, "dev_mode")) or "0"
        # Verbundene Beamer gehören ebenfalls zur Sitzung (Einsatzbesprechung vor dem Start)
        hosts_online = _s(self.r.hget(state_key, "hosts_online")) or "0"

        self.r.delete(state_key, players_key)
        self.r.hset(state_key, mapping={
            "health": 300,
            "time_left": DEFAULT_TIME,
            "status": "waiting",
            "dev_mode": dev_mode,
            "hosts_online": hosts_online,
        })
        self.refresh_ttl(game_id, LOBBY_TTL)

    def game_exists(self, game_id: str) -> bool:
        return bool(self.r.exists(self._k_state(game_id)))

    def _load_players(self, game_id: str) -> dict:
        raw_players = self.r.hgetall(self._k_players(game_id)) or {}
        return {_s(k): json.loads(_s(v)) for k, v in raw_players.items()}

    def _ensure_state(self, game_id: str):
        state_key = self._k_state(game_id)
        if not self.r.exists(state_key):
            self.r.hset(state_key, mapping={
                "health": 300,
                "time_left": DEFAULT_TIME,
                "status": "waiting",
            })

    def register_player(self, game_id: str, name: str, conn: str | None = None) -> dict:
        """Spieler registriert sich OHNE Rolle. Rolle wird per choose_role gewählt.

        conn = Kennung der WebSocket-Verbindung, damit release_player nur die
        jeweils neueste Verbindung eines Spielers zählt.
        """
        self._ensure_state(game_id)
        state_key = self._k_state(game_id)
        players_key = self._k_players(game_id)

        known = self.r.hget(players_key, name)
        if known:
            data = json.loads(_s(known))
            if conn is not None:
                with self.lock(f"choose_role:{game_id}"):
                    self.r.hset(players_key, name, json.dumps({**data, "conn": conn}))
            return {
                "event": "registered",
                "role": data.get("role"),
                "payload": self.get_lobby_payload(game_id),
            }

        status = _s(self.r.hget(state_key, "status")) or "waiting"
        if status in ("running", "game_over", "won", "briefing"):
            return {"event": "error", "payload": {"message": "Das Spiel läuft bereits."}}

        slot = self.r.hincrby(state_key, "player_counter", 1)
        if slot > len(ROLES):
            self.r.hincrby(state_key, "player_counter", -1)
            return {"event": "error", "payload": {"message": "Lobby ist bereits voll!"}}

        self.r.hset(players_key, name, json.dumps({"role": None, "conn": conn}))
        return {
            "event": "registered",
            "role": None,
            "payload": self.get_lobby_payload(game_id),
        }

    def release_player(self, game_id: str, name: str, conn: str | None = None) -> bool:
        """Gibt den Platz eines Spielers ohne Rolle frei (Verbindung getrennt).

        Wer schon eine Rolle hat, behält den Platz für den Reconnect. Hat sich der
        Spieler inzwischen über eine neue Verbindung angemeldet, bleibt er ebenfalls.
        """
        status = _s(self.r.hget(self._k_state(game_id), "status")) or "waiting"
        if status not in ("waiting", "ready"):
            return False

        with self.lock(f"choose_role:{game_id}") as acquired:
            if not acquired:
                return False
            player = self._load_players(game_id).get(name)
            if player is None or player.get("role") or player.get("conn") != conn:
                return False
            self.r.hdel(self._k_players(game_id), name)
            self.r.hincrby(self._k_state(game_id), "player_counter", -1)
        return True

    def choose_role(self, game_id: str, name: str, role: str) -> dict:
        if role not in ROLES:
            return {"event": "error", "payload": {"message": "Unbekannte Rolle"}}

        state_key = self._k_state(game_id)
        players_key = self._k_players(game_id)

        status = _s(self.r.hget(state_key, "status")) or "waiting"
        if status in ("running", "game_over", "won", "briefing"):
            return {"event": "error", "payload": {"message": "Das Spiel läuft bereits."}}

        players = self._load_players(game_id)
        if name not in players:
            return {"event": "error", "payload": {"message": "Spieler nicht registriert"}}

        current = players[name].get("role")
        if current == role:
            return {
                "event": "role_assigned",
                "role": role,
                "payload": self.get_lobby_payload(game_id),
            }
        if current:
            return {"event": "error", "payload": {"message": "Du hast bereits eine Rolle."}}

        with self.lock(f"choose_role:{game_id}", timeout=5.0) as acquired:
            if not acquired:
                return {"event": "error", "payload": {"message": "Bitte erneut versuchen"}}

            players = self._load_players(game_id)
            taken = {p.get("role") for p in players.values() if p.get("role")}
            if role in taken:
                return {
                    "event": "error",
                    "payload": {"message": f"Rolle {role} ist bereits vergeben"},
                }

            self.r.hset(players_key, name, json.dumps({**players[name], "role": role}))

        return {
            "event": "role_assigned",
            "role": role,
            "payload": self.get_lobby_payload(game_id),
        }

    def get_lobby_payload(self, game_id: str) -> dict:
        players = self._load_players(game_id)
        state_raw = self.r.hgetall(self._k_state(game_id)) or {}
        state = {_s(k): _s(v) for k, v in state_raw.items()}

        status = state.get("status", "waiting")

        role_map = {name: p.get("role") for name, p in players.items()}
        taken = [r for r in role_map.values() if r]
        free = [r for r in ROLES if r not in taken]

        ready = len(taken) == len(ROLES)
        if status == "waiting" and ready:
            status = "ready"

        player_list = [
            {"name": name, "role": p.get("role")}
            for name, p in players.items()
        ]

        return {
            "players": player_list,
            "status": status,
            "ready_to_start": ready,
            "roles_taken": taken,
            "roles_free": free,
            "dev_mode": state.get("dev_mode") == "1",
        }

    # ------------------------------------------------------------ Beamer / Einsatzbesprechung
    def change_hosts_online(self, game_id: str, delta: int) -> int:
        """Zählt verbundene Beamer der Sitzung (+1 beim host_register, −1 beim Trennen)."""
        state_key = self._k_state(game_id)
        count = self.r.hincrby(state_key, "hosts_online", delta)
        if count < 0:
            self.r.hset(state_key, "hosts_online", 0)
            count = 0
        return count

    def hosts_online(self, game_id: str) -> int:
        return int(_s(self.r.hget(self._k_state(game_id), "hosts_online")) or 0)

    def begin_briefing(self, game_id: str) -> bool:
        """Lobby → Einsatzbesprechung (Intro am Beamer). True, wenn umgeschaltet."""
        state_key = self._k_state(game_id)
        status = _s(self.r.hget(state_key, "status")) or "waiting"
        if status not in ("waiting", "ready"):
            return False
        self.r.hset(state_key, "status", "briefing")
        return True

    def set_dev_mode(self, game_id: str, enabled: bool) -> dict:
        """DEV-Modus nur in der Lobby umschalten (vor dem Start)."""
        status = _s(self.r.hget(self._k_state(game_id), "status")) or "waiting"
        if status not in ("waiting", "ready"):
            return {"event": "error",
                    "payload": {"message": "DEV-Modus nur vor dem Start umschaltbar"}}
        self.r.hset(self._k_state(game_id), "dev_mode", "1" if enabled else "0")
        return {"event": "lobby_update", "payload": self.get_lobby_payload(game_id)}

    def update_owner_settings(self, game_id: str, settings_data: dict) -> dict:
        self._ensure_state(game_id)
        time_val = settings_data.get("time")
        try:
            time_int = int(time_val)
        except (ValueError, TypeError):
            return {
                "event": "error",
                "payload": {"message": "Ungültige Einstellungen für Zeit"},
            }

        self.r.hset(self._k_state(game_id), "time_left", time_int)
        return {
            "event": "settings_updated",
            "payload": self.get_lobby_payload(game_id),
        }

    def save_role_hints(self, game_id: str, role: str, hints: dict):
        serialized = {k: json.dumps(v) for k, v in hints.items()}
        self.r.hset(self._k_hints(game_id, role), mapping=serialized)
        self.refresh_ttl(game_id)

    def get_role_hints(self, game_id: str, role: str) -> dict:
        raw = self.r.hgetall(self._k_hints(game_id, role)) or {}
        if raw:
            return {_s(k): json.loads(_s(v)) for k, v in raw.items()}
        return {"role": role}

    def refresh_ttl(self, game_id: str, ttl: int = 3600):
        pipe = self.r.pipeline()
        pipe.expire(self._k_state(game_id), ttl)
        pipe.expire(self._k_players(game_id), ttl)
        for role in ROLES:
            pipe.expire(self._k_hints(game_id, role), ttl)
        pipe.execute()