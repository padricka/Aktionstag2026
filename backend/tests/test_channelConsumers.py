import pytest
from channels.testing import WebsocketCommunicator
from backend.ChannelConsumer import ChannelConsumer

WEBSOCKET_TEST_PFAD = "/ws/channel/"

@pytest.mark.asyncio
async def test_channel_consumer_full_flow():
    communicator = WebsocketCommunicator(ChannelConsumer.as_asgi(), WEBSOCKET_TEST_PFAD)
    
    # 1. connect() testen
    connected, _ = await communicator.connect()
    assert connected is True

    # 2. receive() testen (Nachricht senden, um receive auszulösen)
    await communicator.send_to(text_data="Test")
    
    # Erwartete Antworten aus receive() empfangen
    response1 = await communicator.receive_from()
    assert response1 == "Hello World!"
    
    response2 = await communicator.receive_from()
    assert response2 == b"Hello World"

    # 3. disconnect() testen
    await communicator.disconnect()