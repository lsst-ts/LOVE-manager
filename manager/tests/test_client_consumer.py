import pytest
from channels.testing import WebsocketCommunicator
from manager.routing import application
import json

producer_msg = {
    "data": 
        {
        "scheduler": json.dumps({"avoidanceRegions": {"avoidanceRegions": {"value": 1, "dataType": "Int"}, "scale": {"value": 0.02813957817852497, "dataType": "Float"}}}),
        "scriptQueue": json.dumps({"exists": {"item1": {"value": 0, "dataType": "Int"}}})
        }
}
subscription_msg = {
    "option": "subscribe", 
    "csc": "scheduler",
    "stream": "avoidanceRegions"
}

subscription_all_msg = {
    "option": "subscribe", 
    "csc": "all",
    "stream": "all"
}

unsubscription_msg = {
    "option": "unsubscribe", 
    "csc": "scheduler",
    "stream": "avoidanceRegions"
}

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

        # Act
        await communicator.send_json_to(subscription_msg)
        response = await communicator.receive_json_from()

        # Assert
        assert response['data'] == 'Successfully subscribed to scheduler-avoidanceRegions'

        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_leave_telemetry_stream(self):
        
        # Arrange
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()


        # Act
        await communicator.send_json_to(subscription_msg)
        subs_response = await communicator.receive_json_from()

        await communicator.send_json_to(unsubscription_msg)
        unsubs_response = await communicator.receive_json_from()

        # Assert
        assert unsubs_response['data'] == 'Successfully unsubscribed to scheduler-avoidanceRegions'

        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_receive_telemetry_stream(self):
        # Arrange
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()

        # Act
        await communicator.send_json_to(subscription_msg)
        subscription_response = await communicator.receive_json_from()
        
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()

        # Assert
        assert json.loads(producer_msg['data']['scheduler'])['avoidanceRegions'] == producer_response['data']['scheduler']['avoidanceRegions']
        
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_receive_all_telemetries(self):

        # Arrange
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()        

        # Act
        await communicator.send_json_to(subscription_all_msg)
        subscription_response = await communicator.receive_json_from()
        
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()
        # Assert
        assert subscription_response['data'] == 'Successfully subscribed to all-all'
        assert producer_msg['data'] == producer_response['data']
        await communicator.disconnect()
    

