import pytest
from unittest.mock import patch, MagicMock
from backend.multiplayerManager import MultiplayerManager

# TRIAGE (siehe TRIAGE.md): Alt-Design. add_player/Heartbeat/try_start_game gibt es im
# aktuellen MultiplayerManager nicht mehr: die Lobby laeuft ueber register_player und
# choose_role (Redis). Heartbeat-Timeouts sind laut TODO_MVP bewusst nach dem Freeze.
pytestmark = pytest.mark.skip(reason="veraltet: altes MultiplayerManager-Design (add_player/Heartbeat), Lobby laeuft ueber register_player/choose_role (TRIAGE.md)")


def test_heartbeat_updates_player_timestamp():
    manager = MultiplayerManager()
    manager.add_player("David")

    # Spieler sendet Heartbeat
    manager.record_heartbeat("David", current_time=100.0)

    assert manager.get_last_heartbeat("David") == 100.0


def test_check_disconnects_flags_inactive_players():
    manager = MultiplayerManager()
    manager.add_player("David")
    manager.record_heartbeat("David", current_time=100.0)

    # Nach 2 Sekunden bei 5s Timeout: Spieler ist noch da
    active = manager.is_player_alive("David", current_time=102.0, timeout=5.0)
    assert active is True

    # Nach 6 Sekunden: Timeout überschritten
    active = manager.is_player_alive("David", current_time=106.0, timeout=5.0)
    assert active is False


@patch("backend.multiplayerManager.start_Game")
def test_start_game_delegates_to_game_loop_when_ready(mock_start_game):
    # Manager mit Verknüpfungen
    mock_player_mgr = MagicMock()
    mock_player_mgr.get_player_names.return_value = ["Patrick", "David", "Anna"]

    mock_host_mgr = MagicMock()
    mock_host_mgr.get_host.return_value = "Patrick"

    manager = MultiplayerManager(player_manager=mock_player_mgr, host_manager=mock_host_mgr)

    # Act: Spiel über Manager starten
    started = manager.try_start_game(time_limit=160)

    # Assert: Start war erfolgreich und gameLoop.start_Game wurde aufgerufen
    assert started is True
    mock_start_game.assert_called_once()



@patch("backend.multiplayerManager.start_Game")
def test_start_game_refused_without_host(mock_start_game):
    mock_player_mgr = MagicMock()
    mock_player_mgr.get_player_names.return_value = ["Patrick", "David", "Anna"]

    mock_host_mgr = MagicMock()
    mock_host_mgr.get_host.return_value = None

    manager = MultiplayerManager(player_manager=mock_player_mgr, host_manager=mock_host_mgr)

    assert manager.try_start_game(time_limit=160) is False
    mock_start_game.assert_not_called()


@patch("backend.multiplayerManager.start_Game")
def test_start_game_refused_with_too_few_players(mock_start_game):
    mock_player_mgr = MagicMock()
    mock_player_mgr.get_player_names.return_value = ["Patrick", "David"]

    mock_host_mgr = MagicMock()
    mock_host_mgr.get_host.return_value = "Patrick"

    manager = MultiplayerManager(player_manager=mock_player_mgr, host_manager=mock_host_mgr)

    assert manager.try_start_game(time_limit=160) is False
    mock_start_game.assert_not_called()