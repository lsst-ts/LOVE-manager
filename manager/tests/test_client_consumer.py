import pytest
from channels.testing import WebsocketCommunicator
from manager.routing import application

@pytest.mark.asyncio
async def test_connection():
    communicator = WebsocketCommunicator(application,  "/ws/subscription/")
    
    connected, subprotocol = await communicator.connect()

    assert connected, 'Communicator was not connected'

    await communicator.disconnect()

    # import pdb; pdb.set_trace()
    # # Test sending text
    # await communicator.send_json(text_data='{"option": "subscribe", "data": "avoidanceRegions"}')
    # response = await communicator.receive_from()
    # assert response == "hello"
    # # Close