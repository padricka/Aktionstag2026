"""
Foundation-Tests 5–7: WebSocket-Consumer (Django Channels).

ROSETTA-STEIN — async/await (sehr wichtig, neu gegenüber typischem JUnit):

In Java wartet ihr oft blockierend, z.B.:
    Antwort antwort = future.get();   // Thread steht hier still

In Python/JS sagt ihr kooperativ:
    antwort = await irgendetwas()     // „warte hier, bis fertig — gib derweil anderen Code Zeit“

Ohne await:
    - Der Test liest die Antwort, bevor sie da ist → AssertionError oder Timeout
    - Im Produktionscode: Verbindung wird nie akzeptiert / Nachricht nie gesendet

Was ihr im GameConsumer (Produktionscode) beachten müsst:
    - Methoden oft: async def connect(self), async def receive(self, text_data)
    - await self.accept()          # Verbindung annehmen
    - await self.send(...)         # Antwort schicken
    - JSON parsen in try/except — bei Fehlern Error-JSON senden, nicht crashen

WebsocketCommunicator = Test-Werkzeug von Channels (kein echter Browser nötig).
"""

import pytest
from channels.testing import WebsocketCommunicator

# PRODUKTIONSCODE: z.B. game/consumers.py → Klasse GameConsumer (AsyncWebsocketConsumer)
from backend.GameConsumer import GameConsumer


# URL-Pfad ist für den Communicator oft egal, wenn ihr den Consumer direkt übergebt.
# Später muss euer Routing (z.B. /ws/game/) zum echten Client passen.
WEBSOCKET_TEST_PFAD = "/ws/game/"


# TRIAGE (siehe TRIAGE.md): Fundament-Tests 5-7 im alten Protokoll ({"action": "ping"} ->
# {"type": "pong"}) und ohne Route (url_route fehlt). Ersetzt durch test_gameConsumer.py,
# das connect, ping/pong und kaputtes JSON im JSON-Vertrag (event + payload) abdeckt.
pytestmark = pytest.mark.skip(reason="veraltet: altes Protokoll action/type, ersetzt durch test_gameConsumer.py (TRIAGE.md)")

# @pytest.mark.asyncio ist optional, wenn in pytest.ini steht: asyncio_mode = auto
# Wir lassen den Marker dran als Fallback (falls die ini-Datei fehlt/anders heißt).
@pytest.mark.asyncio
async def test_websocket_connects_and_accepts():
    """
    Test 5 — Verbindung wird akzeptiert.

    async def + await:
        Der Test ist asynchron, weil WebSockets asynchron sind.
        „await communicator.connect()“ wartet, bis connect() im Consumer durch ist.

    Produktionscode:
        In GameConsumer.connect: await self.accept()
        (Ohne accept bleibt connected == False.)
    """
    websocket_kommunikator = WebsocketCommunicator(
        GameConsumer.as_asgi(),
        WEBSOCKET_TEST_PFAD,
    )

    # connected, _ = …  → erstes Element = ob akzeptiert, zweites oft der Close-Code
    verbindung_wurde_akzeptiert, _schließen_code = await websocket_kommunikator.connect()

    assert verbindung_wurde_akzeptiert is True, (
        "Der Consumer muss die WebSocket-Verbindung akzeptieren "
        "(await self.accept() in connect)."
    )

    # Aufräumen — wie eine Ressource schließen
    await websocket_kommunikator.disconnect()


@pytest.mark.asyncio
async def test_websocket_receives_ping_sends_pong():
    """
    Test 6 — JSON ping → JSON pong (Basis für euer Nachrichten-Protokoll).

    Ablauf:
        1) verbinden (await)
        2) JSON senden: {"action": "ping"}
        3) auf Antwort warten (await receive_json_from)
        4) erwarten: {"type": "pong"}

    Produktionscode:
        In receive: JSON laden, wenn action == \"ping\" → Antwort mit type \"pong\" senden.
        Wichtig: await self.send(text_data=...) bzw. send_json — ohne await kommt nichts an.
    """
    websocket_kommunikator = WebsocketCommunicator(
        GameConsumer.as_asgi(),
        WEBSOCKET_TEST_PFAD,
    )
    verbindung_wurde_akzeptiert, _ = await websocket_kommunikator.connect()
    assert verbindung_wurde_akzeptiert is True

    ping_nachricht_vom_client = {"action": "ping"}
    await websocket_kommunikator.send_json_to(ping_nachricht_vom_client)

    # Hier MUSS await stehen — sonst lest ihr die Antwort zu früh
    empfangene_antwort_vom_server = await websocket_kommunikator.receive_json_from()

    erwartete_pong_antwort = {"type": "pong"}
    assert empfangene_antwort_vom_server == erwartete_pong_antwort, (
        "Auf {'action': 'ping'} muss {'type': 'pong'} zurückkommen."
    )

    await websocket_kommunikator.disconnect()


@pytest.mark.asyncio
async def test_websocket_rejects_invalid_json():
    """
    Test 7 — Kaputtes JSON darf den Consumer nicht abstürzen lassen.

    Analog zu Java: try/catch um JSON-Parsing, Fehlerantwort statt Exception nach oben.

    Produktionscode:
        - text_data mit json.loads in try/except fangen
        - Bei Fehler z.B. {"type": "error", "message": "..."} zurücksenden
        - Verbindung idealerweise offen lassen (kein unkontrollierter Crash)

    Wir senden absichtlich KEIN gültiges JSON (nur einen kaputten String).
    """
    websocket_kommunikator = WebsocketCommunicator(
        GameConsumer.as_asgi(),
        WEBSOCKET_TEST_PFAD,
    )
    verbindung_wurde_akzeptiert, _ = await websocket_kommunikator.connect()
    assert verbindung_wurde_akzeptiert is True

    kaputter_json_text = "{das ist kein gueltiges json!!!"
    await websocket_kommunikator.send_to(text_data=kaputter_json_text)

    empfangene_fehler_antwort = await websocket_kommunikator.receive_json_from()

    assert isinstance(empfangene_fehler_antwort, dict), (
        "Auch bei Fehlern sollt ihr JSON (ein Dict) zurückgeben, nicht einfach sterben."
    )
    assert empfangene_fehler_antwort.get("type") == "error", (
        "Erwartet wird z.B. {'type': 'error', 'message': '...'}. "
        "So erkennt der Client, dass etwas schiefging."
    )

    # Verbindung sollte noch nutzbar sein (kein hartes Abstürzen des Consumers)
    await websocket_kommunikator.disconnect()
