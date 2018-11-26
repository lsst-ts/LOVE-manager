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

    @pytest.mark.asyncio
    async def test_leave_telemetry_stream(self):
        
        # Arrange
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()

        subs_msg = {
            "option": "subscribe", 
            "data": "avoidanceRegions"
        }
        unsubs_msg = {
            "option": "unsubscribe", 
            "data": "avoidanceRegions"
        }

        # Act
        await communicator.send_json_to(subs_msg)
        subs_response = await communicator.receive_json_from()

        await communicator.send_json_to(unsubs_msg)
        unsubs_response = await communicator.receive_json_from()

        # Assert
        assert unsubs_response['data'] == 'Successfully unsubscribed to avoidanceRegions'

        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_receive_telemetry_stream(self):
        
        # Arrange
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()

        subscription_msg = {
            "option": "subscribe", 
            "data": "avoidanceRegions"
        }

        producer_msg = {
            "option": "somethingelse",
            "data":{
                "avoidanceRegions": {
                    "avoidanceRegions": 0,
                    "scale": 0.2633153200149536,
                    "timestamp": 0.3877990729003341,
                    "zero": 0.3617618978023529
                },
                "bulkCloud": {
                    "bulkCloud": 0.6713680575252166,
                    "timestamp": 0.5309269973966433
                }
            }
        }

      
        # Act
        await communicator.send_json_to(subscription_msg)
        subscription_response = await communicator.receive_json_from()
        
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()

        # Assert
        assert producer_msg['data']['avoidanceRegions'] == producer_response['data']
        
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_receive_all_telemetries(self):

        # Arrange
        communicator = WebsocketCommunicator(application,  "/ws/subscription/")
        
        connected, subprotocol = await communicator.connect()        

        subscription_msg = {
            "option": "subscribe", 
            "data": "all"
        }

        producer_msg = {
            "option": "somethingelse",
            "data":{
                "avoidanceRegions": {
                    "avoidanceRegions": 0,
                    "scale": 0.2633153200149536,
                    "timestamp": 0.3877990729003341,
                    "zero": 0.3617618978023529
                },
                "bulkCloud": {
                    "bulkCloud": 0.6713680575252166,
                    "timestamp": 0.5309269973966433
                }
            }
        }

        # Act
        await communicator.send_json_to(subscription_msg)
        subscription_response = await communicator.receive_json_from()
        
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()

        # Assert
        assert producer_msg['data'] == producer_response['data']
        
        await communicator.disconnect()
    

