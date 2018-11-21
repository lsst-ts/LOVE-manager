import pytest
from channels.testing import WebsocketCommunicator
from manager.routing import application


class TestClientConsumer:
    @pytest.mark.asyncio
    async def test_connection(self):
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()

        assert connected, 'Communicator was not connected'

        await communicator.disconnect()
        
    @pytest.mark.asyncio
    async def test_join_telemetry_stream(self):
        
        # Arrange
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()

        msg = {
            "option": "subscribe", 
            "data": "avoidanceRegions"
            }

        # Act
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()

        # Assert
        assert response['data'] == 'Successfully subscribed to avoidanceRegions'

        await communicator.disconnect()
