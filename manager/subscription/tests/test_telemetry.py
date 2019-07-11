import json
import pytest
import asyncio
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token

producer_msg = {
    "data": {
        "scheduler": json.dumps({
            "avoidanceRegions": {
                "avoidanceRegions": {"value": 1, "dataType": "Int"},
                "scale": {"value": 0.02813957817852497, "dataType": "Float"}
            }
        }),
        "scriptQueue": json.dumps({"exists": {"item1": {"value": 0, "dataType": "Int"}}})
    }
}
producer_msg_2 = {
    "data": {
        "scheduler": json.dumps({
            "avoidanceRegions": {
                "avoidanceRegions": {"value": 2, "dataType": "Int"},
                "scale": {"value": 0.0456789, "dataType": "Float"}
            }
        }),
        "ATDome": json.dumps({"exists": {"item1": {"value": 0, "dataType": "Int"}}})
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


class TestTelemetrySubscription:
    """ Test that clients can or cannot subscribe/unsubscribe to telemetries depending on different conditions """

    def setup_method(self):
        """ TestCase setup, executed before each test of the TestCase """
        self.user = User.objects.create_user('username', password='123', email='user@user.cl')
        self.token = Token.objects.create(user=self.user)
        self.url = 'manager/ws/subscription/?token={}'.format(self.token)

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_join_telemetry_stream(self):
        """ Test that clients can join a telemetry stream """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        # Act
        await communicator.send_json_to(subscription_msg)
        response = await communicator.receive_json_from()
        # Assert
        assert response['data'] == 'Successfully subscribed to scheduler-avoidanceRegions'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_leave_telemetry_stream(self):
        """ Test that clients can leave a telemetry stream """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_msg)
        await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(unsubscription_msg)
        unsubs_response = await communicator.receive_json_from()
        # Assert
        assert unsubs_response['data'] == 'Successfully unsubscribed to scheduler-avoidanceRegions'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_telemetry_stream(self):
        """ Test that clients can receive messages from a telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_msg)
        await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()
        # Assert
        assert json.loads(producer_msg['data']['scheduler'])[
            'avoidanceRegions'] == producer_response['data']['scheduler']['avoidanceRegions']
        await communicator.disconnect()

    # @pytest.mark.asyncio
    # @pytest.mark.django_db
    # async def test_not_receive_telemetry_from_left_stream(self):
    #     """ Test that clients cannot receive a telemetry of a stream they have left """
    #     # Arrange
    #     communicator = WebsocketCommunicator(application, self.url)
    #     connected, subprotocol = await communicator.connect()
    #     await communicator.send_json_to(subscription_msg)
    #     await communicator.receive_json_from()
    #     await communicator.send_json_to(unsubscription_msg)
    #     unsubs_response = await communicator.receive_json_from()
    #     # Act
    #     await communicator.send_json_to(producer_msg)
    #     # Assert
    #     assert unsubs_response['data'] == 'Successfully unsubscribed to scheduler-avoidanceRegions'
    #     with pytest.raises(asyncio.TimeoutError):
    #         producer_response = await communicator.receive_json_from()
    #         print('producer_response: ', producer_response)
    #         assert producer_response['data'] == 'Successfully unsubscribed to scheduler-avoidanceRegions'
    #     await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_join_all_telemetries(self):
        """ Test that clients can join all the telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        # Act
        await communicator.send_json_to(subscription_all_msg)
        response = await communicator.receive_json_from()
        # Assert
        assert response['data'] == 'Successfully subscribed to all-all'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_all_telemetries(self):
        """ Test that clients can receive messages from all the telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_all_msg)
        # Act
        subscription_response = await communicator.receive_json_from()
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()
        await communicator.send_json_to(producer_msg_2)
        producer_response_2 = await communicator.receive_json_from()
        # Assert
        assert subscription_response['data'] == 'Successfully subscribed to all-all'
        assert producer_msg['data'] == producer_response['data']
        assert producer_msg_2['data'] == producer_response_2['data']
        await communicator.disconnect()
