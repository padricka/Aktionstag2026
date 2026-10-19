import asyncio
import uuid
from backend.redis_handler import RedisHandler


class MultiplayerManager:
    """Lobby-Logik. Der RedisHandler ist synchron, deshalb läuft alles in einem Thread."""

    def __init__(self, game_id: str | None = None):
        self.game_id = game_id
        self.redis = RedisHandler()

    async def create_lobby(self) -> str:
        self.game_id = str(uuid.uuid4())
        await asyncio.to_thread(self.redis.create_game, self.game_id)
        return self.game_id

    async def exists(self) -> bool:
        return await asyncio.to_thread(self.redis.game_exists, self.game_id)

    async def register_player(self, name: str, conn: str | None = None) -> dict:
        return await asyncio.to_thread(self.redis.register_player, self.game_id, name, conn)

    async def release_player(self, name: str, conn: str | None = None) -> bool:
        return await asyncio.to_thread(self.redis.release_player, self.game_id, name, conn)

    async def choose_role(self, name: str, role: str) -> dict:
        return await asyncio.to_thread(self.redis.choose_role, self.game_id, name, role)

    async def set_settings(self, settings: dict) -> dict:
        return await asyncio.to_thread(self.redis.update_owner_settings, self.game_id, settings)

    async def lobby_payload(self) -> dict:
        return await asyncio.to_thread(self.redis.get_lobby_payload, self.game_id)

    async def role_hints(self, role: str) -> dict:
        return await asyncio.to_thread(self.redis.get_role_hints, self.game_id, role)