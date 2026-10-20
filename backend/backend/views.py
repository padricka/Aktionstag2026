import asyncio
import secrets
from django.http import JsonResponse
from .gameLoop import start_game_for
from . import leaderboard
from .redis_handler import RedisHandler

_MESSAGES = {
    "started": ("success", 200, "Game started!"),
    "not_found": ("error", 404, "Unknown game_id (noch keine Lobby)."),
    "already_running": ("error", 409, "Game läuft bereits."),
    "not_ready": ("error", 409, "Lobby nicht vollständig (alle drei Rollen nötig)."),
    "finished": ("error", 409, "Game ist bereits beendet."),
}

# Ohne 0/O/1/I, damit der Code am Beamer lesbar bleibt.
_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


def _short_game_id() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(4))


def _json(data, status=200):
    resp = JsonResponse(data, status=status)
    resp["Access-Control-Allow-Origin"] = "*"   # Dev: Frontend :5173 -> Backend :8000
    return resp


async def create_game(request):
    game_id = _short_game_id()
    await asyncio.to_thread(RedisHandler().create_game, game_id)
    return _json({"status": "success", "game_id": game_id})


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


async def leaderboard_page(request):
    """GET /leaderboard/?page=1&per_page=20 – alle Runden, höchste Punktzahl zuerst."""
    data = await asyncio.to_thread(
        leaderboard.page,
        _int(request.GET.get("page"), 1),
        _int(request.GET.get("per_page"), leaderboard.PER_PAGE),
    )
    return _json(data)


async def force_start_game(request):
    game_id = request.GET.get("game_id")
    if not game_id:
        return _json({"status": "error", "message": "game_id required (?game_id=...)"}, 400)
    try:
        result = await start_game_for(game_id)
    except Exception as e:
        return _json({"status": "error", "message": str(e)}, 500)

    status, http_code, message = _MESSAGES[result]
    return _json({"status": status, "message": message, "game_id": game_id}, http_code)