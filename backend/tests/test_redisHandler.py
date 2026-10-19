"""Vollständige Abdeckung der Lobby-Logik im RedisHandler."""
import json
import threading
import time
from unittest.mock import patch

import fakeredis
import pytest

from backend.redis_handler import RedisHandler, ROLES, _s


# ---------------------------------------------------------------- Fixtures
@pytest.fixture
def env():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    return fake


@pytest.fixture
def handler(env):
    with patch("backend.redis_handler.redis.Redis", return_value=env):
        h = RedisHandler()
    return h


# ---------------------------------------------------------------- _s
def test__s_decodes_bytes():
    assert _s(b"abc") == "abc"


def test__s_passes_through_str():
    assert _s("abc") == "abc"


def test__s_passes_through_none():
    assert _s(None) is None


# ---------------------------------------------------------------- __init__ (Zeile 17)
def test_init_builds_redis_client(env):
    """Cover-Zeile: RedisHandler.__init__ ruft redis.Redis(...) auf."""
    with patch("backend.redis_handler.redis.Redis", return_value=env) as cls:
        h = RedisHandler()
        cls.assert_called_once()
        assert h.r is env


# ---------------------------------------------------------------- create_game / TTL
def test_create_game_sets_state_and_ttl(handler, env):
    handler.create_game("g")
    assert env.hget("game:g:state", "health") == b"300"
    assert env.hget("game:g:state", "status") == b"waiting"
    assert env.ttl("game:g:state") > 0


def test_waiting_lobby_lives_longer_than_an_hour(handler, env):
    """Beamer morgens geöffnet, Spieler kommen später: die Sitzungs-ID muss noch gelten."""
    handler.create_game("g")
    assert env.ttl("game:g:state") > 3600


def test_refresh_ttl_covers_all_keys(handler, env):
    """Cover-Zeile: refresh_ttl pipeline.execute()."""
    handler.create_game("g")
    handler.register_player("g", "A")
    handler.save_role_hints("g", ROLES[0], {"hint": "x"})
    handler.refresh_ttl("g")
    assert env.ttl("game:g:hints:master") > 0


# ---------------------------------------------------------------- game_exists
def test_game_exists_after_create(handler):
    assert handler.game_exists("g") is False
    handler.create_game("g")
    assert handler.game_exists("g") is True


# ---------------------------------------------------------------- register_player
def test_register_creates_state_so_game_can_be_started(handler, env):
    handler.register_player("test_game", "Anna")
    assert env.exists("game:test_game:state")


def test_register_returns_none_role(handler):
    res = handler.register_player("g", "A")
    assert res["role"] is None
    assert res["event"] == "registered"


def test_register_known_player_returns_saved_role(handler):
    """Cover-Zeile 108: known-Zweig bei register_player."""
    handler.register_player("g", "A")
    handler.choose_role("g", "A", "MASTER")
    again = handler.register_player("g", "A")
    assert again["role"] == "MASTER"


def test_register_when_game_running_is_rejected(handler, env):
    """Cover-Zeile 109: 'running'-Zweig."""
    handler.register_player("g", "A")
    env.hset("game:g:state", "status", "running")
    res = handler.register_player("g", "B")
    assert res["event"] == "error"
    assert "läuft" in res["payload"]["message"]


def test_register_when_game_won_is_rejected(handler, env):
    handler.register_player("g", "A")
    env.hset("game:g:state", "status", "won")
    res = handler.register_player("g", "B")
    assert res["event"] == "error"


def test_register_fourth_player_is_rejected(handler):
    for n in ("A", "B", "C"):
        handler.register_player("g", n)
    res = handler.register_player("g", "D")
    assert res["event"] == "error" and "voll" in res["payload"]["message"]
    # Counter zurückgerollt
    assert int(handler.r.hget("game:g:state", "player_counter")) == 3


# ---------------------------------------------------------------- release_player
def test_release_player_without_role_frees_slot(handler):
    for n in ("A", "B", "C"):
        handler.register_player("g", n, conn="c-" + n)
    assert handler.release_player("g", "A", conn="c-A") is True
    names = [p["name"] for p in handler.get_lobby_payload("g")["players"]]
    assert names == ["B", "C"]
    # Der Platz ist wieder frei
    assert handler.register_player("g", "D")["event"] == "registered"


def test_release_player_with_role_keeps_player(handler):
    """Wer eine Rolle hat, behält den Platz (Reconnect)."""
    handler.register_player("g", "A", conn="c1")
    handler.choose_role("g", "A", "MASTER")
    assert handler.release_player("g", "A", conn="c1") is False
    assert handler.register_player("g", "A")["role"] == "MASTER"


def test_release_player_ignored_after_newer_connection(handler):
    """Reload: das verspätete disconnect der alten Verbindung wirft den Spieler nicht raus."""
    handler.register_player("g", "A", conn="alt")
    handler.register_player("g", "A", conn="neu")
    assert handler.release_player("g", "A", conn="alt") is False
    assert handler.choose_role("g", "A", "FI-SI")["event"] == "role_assigned"


def test_release_player_ignored_while_running(handler, env):
    handler.register_player("g", "A", conn="c1")
    env.hset("game:g:state", "status", "running")
    assert handler.release_player("g", "A", conn="c1") is False


def test_release_player_lock_not_acquired(handler):
    handler.register_player("g", "A", conn="c1")
    with patch.object(handler, "lock") as mock_lock:
        mock_lock.return_value.__enter__ = lambda self: False
        mock_lock.return_value.__exit__ = lambda *_: None
        assert handler.release_player("g", "A", conn="c1") is False
    assert "A" in handler._load_players("g")


def test_release_unknown_player(handler):
    handler.create_game("g")
    assert handler.release_player("g", "X", conn="c1") is False


def test_choose_role_keeps_connection(handler):
    handler.register_player("g", "A", conn="c1")
    handler.choose_role("g", "A", "MASTER")
    assert handler._load_players("g")["A"] == {"role": "MASTER", "conn": "c1"}


# ---------------------------------------------------------------- choose_role
def test_choose_role_assigns(handler):
    handler.register_player("g", "A")
    res = handler.choose_role("g", "A", "MASTER")
    assert res["event"] == "role_assigned"
    assert res["role"] == "MASTER"


def test_choose_role_unknown_role(handler):
    handler.register_player("g", "A")
    res = handler.choose_role("g", "A", "PIZZA")
    assert res["event"] == "error"
    assert "Unbekannte" in res["payload"]["message"]


def test_choose_role_game_running_is_rejected(handler, env):
    handler.register_player("g", "A")
    env.hset("game:g:state", "status", "running")
    res = handler.choose_role("g", "A", "MASTER")
    assert res["event"] == "error"


def test_choose_role_unknown_player(handler):
    """Cover-Zeile 116: Spieler nicht registriert."""
    handler.create_game("g")
    res = handler.choose_role("g", "Ghost", "MASTER")
    assert res["event"] == "error"
    assert "registriert" in res["payload"]["message"]


def test_choose_role_same_role_again_is_ok(handler):
    handler.register_player("g", "A")
    handler.choose_role("g", "A", "MASTER")
    res = handler.choose_role("g", "A", "MASTER")
    assert res["event"] == "role_assigned"


def test_choose_role_different_role_after_chosen_is_rejected(handler):
    """Cover-Zeile 120: bereits gewählte Rolle."""
    handler.register_player("g", "A")
    handler.choose_role("g", "A", "MASTER")
    res = handler.choose_role("g", "A", "FI-SI")
    assert res["event"] == "error"
    assert "bereits" in res["payload"]["message"]


def test_choose_role_lock_not_acquired(handler):
    """Cover-Zeile 124: Lock konnte nicht geholt werden."""
    handler.register_player("g", "A")
    with patch.object(handler, "lock") as mock_lock:
        mock_lock.return_value.__enter__ = lambda self: False
        mock_lock.return_value.__exit__ = lambda *_: None
        res = handler.choose_role("g", "A", "MASTER")
    assert res["event"] == "error"


def test_choose_role_role_already_taken(handler):
    """Cover-Zeile 130: Rolle schon von anderem Spieler gewählt."""
    handler.register_player("g", "A")
    handler.register_player("g", "B")
    handler.choose_role("g", "A", "MASTER")
    res = handler.choose_role("g", "B", "MASTER")
    assert res["event"] == "error"
    assert "vergeben" in res["payload"]["message"]


def test_simultaneous_choose_distinct_roles(handler):
    def go(name, role):
        handler.register_player("race", name)
        handler.choose_role("race", name, role)

    threads = [
        threading.Thread(target=go, args=("A", "MASTER")),
        threading.Thread(target=go, args=("B", "FI-SI")),
        threading.Thread(target=go, args=("C", "FI-AE")),
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    payload = handler.get_lobby_payload("race")
    assert sorted(payload["roles_taken"]) == sorted(ROLES)
    assert payload["ready_to_start"] is True


# ---------------------------------------------------------------- get_lobby_payload
def test_lobby_becomes_ready(handler):
    for n in ("A", "B", "C"):
        handler.register_player("g", n)
    assert handler.get_lobby_payload("g")["ready_to_start"] is False
    for n, r in zip(("A", "B", "C"), ROLES):
        handler.choose_role("g", n, r)
    payload = handler.get_lobby_payload("g")
    assert payload["ready_to_start"] is True
    assert payload["status"] == "ready"
    assert payload["roles_free"] == []


def test_lobby_payload_lists_players_with_roles(handler):
    """Cover-Zeile 139: player_list-Bau."""
    handler.register_player("g", "A")
    handler.choose_role("g", "A", "MASTER")
    payload = handler.get_lobby_payload("g")
    assert payload["players"] == [{"name": "A", "role": "MASTER"}]


# ---------------------------------------------------------------- update_owner_settings
def test_owner_settings_valid(handler, env):
    ok = handler.update_owner_settings("g", {"time": 120})
    assert ok["event"] == "settings_updated"
    assert int(env.hget("game:g:state", "time_left")) == 120


def test_owner_settings_invalid_time(handler):
    """Cover-Zeile 165: int() schlägt fehl."""
    res = handler.update_owner_settings("g", {"time": "abc"})
    assert res["event"] == "error"


def test_owner_settings_missing_time(handler):
    res = handler.update_owner_settings("g", {})
    assert res["event"] == "error"


# ---------------------------------------------------------------- save_role_hints / get
def test_save_and_read_role_hints(handler, env):
    """Cover-Zeile 198-200: save_role_hints."""
    handler.save_role_hints("g", ROLES[0], {"a": 1, "b": "x"})
    raw = env.hgetall("game:g:hints:master")
    assert b"a" in raw
    assert json.loads(raw[b"a"]) == 1


def test_get_role_hints_empty_default(handler):
    res = handler.get_role_hints("g", ROLES[1])
    assert res == {"role": ROLES[1]}


def test_get_role_hints_reads_saved(handler):
    handler.save_role_hints("g", ROLES[0], {"hint": "hi"})
    res = handler.get_role_hints("g", ROLES[0])
    assert res == {"hint": "hi"}


# ---------------------------------------------------------------- lock ctx manager
def test_lock_context_manager_acquires_and_releases(handler):
    """Cover-Zeile 31-40: Lock-Kontext."""
    with handler.lock("test-lock", timeout=2.0) as acquired:
        assert acquired is True
    # Nach dem Exit sollte der Lock frei sein
    with handler.lock("test-lock", timeout=2.0) as acquired2:
        assert acquired2 is True


def test_lock_ignores_release_error(handler):
    with patch.object(handler.r, "lock") as mock_lock:
        lock_inst = mock_lock.return_value
        lock_inst.acquire.return_value = True
        lock_inst.release.side_effect = Exception("boom")
        with handler.lock("x") as acq:
            assert acq is True
        # Kein Raise nach oben

# ---------------------------------------------------------------- DEV-Modus
def test_lobby_payload_dev_mode_default_off(handler):
    handler.create_game("g")
    assert handler.get_lobby_payload("g")["dev_mode"] is False


def test_set_dev_mode_in_lobby(handler):
    handler.create_game("g")
    res = handler.set_dev_mode("g", True)
    assert res["event"] == "lobby_update"
    assert res["payload"]["dev_mode"] is True
    assert handler.set_dev_mode("g", False)["payload"]["dev_mode"] is False


def test_set_dev_mode_rejected_while_running(handler, env):
    handler.create_game("g")
    env.hset("game:g:state", "status", "running")
    res = handler.set_dev_mode("g", True)
    assert res["event"] == "error"
    assert handler.get_lobby_payload("g")["dev_mode"] is False


def test_create_game_keeps_dev_mode(handler):
    """Neustart (reset_game → create_game) behält den DEV-Modus der Sitzung."""
    handler.create_game("g")
    handler.set_dev_mode("g", True)
    handler.create_game("g")
    assert handler.get_lobby_payload("g")["dev_mode"] is True
