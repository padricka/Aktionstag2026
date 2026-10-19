import pytest
import fakeredis
from unittest.mock import patch

@pytest.fixture(autouse=True)
def env():
    server = fakeredis.FakeServer()
    fake_redis = fakeredis.FakeStrictRedis(server=server)

    with patch("backend.redis_handler.redis.Redis", return_value=fake_redis):
        with patch("django_redis.get_redis_connection", return_value=fake_redis, create=True):
            yield fake_redis


@pytest.fixture(autouse=True)
def channel_layer_settings(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }


@pytest.fixture(autouse=True)
async def cleanup_games():
    from backend.gameLoop import games
    yield
    for g in list(games.values()):
        try:
            await g.stop_game()
        except Exception:
            pass
    games.clear()

@pytest.fixture(autouse=True)
def leaderboard_file(tmp_path, monkeypatch):
    """Kein Test schreibt je ins echte Leaderboard."""
    path = tmp_path / "leaderboard.json"
    monkeypatch.setenv("LEADERBOARD_FILE", str(path))
    return path
