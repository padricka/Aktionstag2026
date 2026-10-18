import pytest
from backend.hostManager import HostManager

# TRIAGE (siehe TRIAGE.md): Alt-Design. Diese Tests beschreiben eine Host-Verwaltung
# (set_host/is_host/handle_disconnect, "nur Host darf starten"), die nie gebaut wurde.
# Der aktuelle HostManager ist ein MVP (nur start(), "Host-Check bewusst noch nicht drin").
# Ersetzen, sobald die Host-Logik (host_register / Host-Check) neu spezifiziert ist.
pytestmark = pytest.mark.skip(reason="veraltet: altes HostManager-Design, aktueller HostManager hat nur start() (TRIAGE.md)")


@pytest.fixture
def manager():
    return HostManager()


# --- Host-Zuweisung ---

def test_set_host_assigns_host(manager):
    manager.set_host("p1")
    assert manager.get_host() == "p1"

def test_is_host_true_for_current_host(manager):
    manager.set_host("p1")
    assert manager.is_host("p1") is True

def test_is_host_false_for_non_host(manager):
    manager.set_host("p1")
    assert manager.is_host("p2") is False

def test_no_host_initially(manager):
    assert manager.get_host() is None


# --- Host-Disconnect (Host ist ein eigener Laptop, kein Spieler) ---

def test_host_is_not_transferred_to_players_on_disconnect(manager):
    manager.set_host("p1")
    manager.handle_disconnect("p1", remaining_players=["p2"])
    assert manager.get_host() is None

def test_host_cleared_when_no_players_remain(manager):
    manager.set_host("p1")
    manager.handle_disconnect("p1", remaining_players=[])
    assert manager.get_host() is None

def test_non_host_disconnect_does_not_change_host(manager):
    manager.set_host("p1")
    manager.handle_disconnect("p2", remaining_players=["p1"])
    assert manager.get_host() == "p1"


# --- Spielsteuerung (Start/Reset) ---

def test_only_host_can_start_game(manager):
    manager.set_host("p1")
    manager.start_game(requested_by="p1")
    assert manager.is_started() is True

def test_non_host_cannot_start_game(manager):
    manager.set_host("p1")
    with pytest.raises(PermissionError):
        manager.start_game(requested_by="p2")

def test_game_not_started_initially(manager):
    assert manager.is_started() is False

def test_reset_game_by_host(manager):
    manager.set_host("p1")
    manager.start_game(requested_by="p1")
    manager.reset_game(requested_by="p1")
    assert manager.is_started() is False

def test_non_host_cannot_reset_game(manager):
    manager.set_host("p1")
    manager.start_game(requested_by="p1")
    with pytest.raises(PermissionError):
        manager.reset_game(requested_by="p2")



# --- Es gibt genau einen Host-Laptop ---

def test_second_host_cannot_replace_existing_host(manager):
    manager.set_host("p1")
    with pytest.raises(ValueError):
        manager.set_host("p2")

def test_cannot_start_game_without_host(manager):
    with pytest.raises(PermissionError):
        manager.start_game(requested_by="p1")