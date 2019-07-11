import json
import pytest
import asyncio
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token

producer_msg = {
    "category": "telemetry",
    "data": {
        "ScriptQueue": json.dumps({
            "stream1": {
                "stream1_param_1": {"value": 1, "dataType": "Int"},
                "stream1_param_2": {"value": 1.02813957817852497, "dataType": "Float"}
            }
        })
    }
}

producer_msg_2 = {
    "category": "telemetry",
    "data": {
        "ScriptQueue": json.dumps({
            "stream2": {
                "stream2_param_1": {"value": 2, "dataType": "Int"},
                "stream2_param_2": {"value": 2.02813957817852497, "dataType": "Float"}
            }
        })
    }
}

subscription_msg = {
    "option": "subscribe",
    "csc": "ScriptQueue",
    "stream": "stream1",
    "category": "telemetry"
}

subscription_msg_2 = {
    "option": "subscribe",
    "csc": "ScriptQueue",
    "stream": "stream2",
    "category": "telemetry"
}

subscription_all_msg = {
    "option": "subscribe",
    "csc": "all",
    "stream": "all",
    "category": "telemetry"
}

unsubscription_msg = {
    "option": "unsubscribe",
    "csc": "ScriptQueue",
    "stream": "stream1",
    "category": "telemetry"
}

unsubscription_msg_2 = {
    "option": "unsubscribe",
    "csc": "ScriptQueue",
    "stream": "stream2",
    "category": "telemetry"
}

unsubscription_all_msg = {
    "option": "unsubscribe",
    "csc": "all",
    "stream": "all",
    "category": "telemetry"
}


class TestTelemetrySubscription:
    """ Test that clients can or cannot subscribe/unsubscribe to telemetries depending on different conditions """

    def setup_method(self):
        """ TestCase setup, executed before each test of the TestCase """
        self.user = User.objects.create_user('username', password='123', email='user@user.cl')
        self.token = Token.objects.create(user=self.user)
        self.url = 'manager/ws/subscription/?token={}'.format(self.token)

    # Tests for 1 telemetry stream
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
        assert response['data'] == 'Successfully subscribed to ScriptQueue-stream1'
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
        assert unsubs_response['data'] == 'Successfully unsubscribed to ScriptQueue-stream1'
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
        assert json.loads(producer_msg['data']['ScriptQueue'])['stream1'] == \
            producer_response['data']['ScriptQueue']['stream1']
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_not_receive_telemetry_from_left_stream(self):
        """ Test that clients cannot receive a telemetry of a stream they have left """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_msg)
        await communicator.receive_json_from()
        await communicator.send_json_to(unsubscription_msg)
        unsubs_response = await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(producer_msg)
        # Assert
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(communicator.receive_json_from(), timeout=0.1)
        await communicator.disconnect()

    # Tests for all telemetry stream
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
    async def test_leave_all_telemetry_streams(self):
        """ Test that clients can leave all telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_all_msg)
        await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(unsubscription_all_msg)
        unsubs_response = await communicator.receive_json_from()
        # Assert
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_all_telemetries(self):
        """ Test that clients can receive messages from all the telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_all_msg)
        subscription_response = await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()
        await communicator.send_json_to(producer_msg_2)
        producer_response_2 = await communicator.receive_json_from()
        # Assert
        assert producer_msg['data'] == producer_response['data']
        assert producer_msg_2['data'] == producer_response_2['data']
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_not_receive_telemetry_after_leaving_all_streams(self):
        """ Test that clients cannot receive telemetries after unsubscribing to all streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_all_msg)
        await communicator.receive_json_from()
        await communicator.send_json_to(unsubscription_all_msg)
        unsubs_response = await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(producer_msg)
        # Assert
        assert unsubs_response['data'] == 'Successfully unsubscribed to all-all'
        with pytest.raises(asyncio.TimeoutError):
            producer_response = await asyncio.wait_for(communicator.receive_json_from(), timeout=0.1)
        await communicator.disconnect()

    # Tests for 2 telemetry streams
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_join_2_telemetries(self):
        """ Test that clients can join 2 of the telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        # Act
        await communicator.send_json_to(subscription_msg)
        await communicator.send_json_to(subscription_msg_2)
        response_1 = await communicator.receive_json_from()
        response_2 = await communicator.receive_json_from()
        # Assert
        responses = [response_1, response_2]
        expected_responses = ['Successfully subscribed to ScriptQueue-stream' + str(i) for i in [1, 2]]
        for response in responses:
            assert response['data'] in expected_responses
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_2_telemetries(self):
        """ Test that clients can receive messages from 2 of the telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_msg)
        await communicator.send_json_to(subscription_msg_2)
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(producer_msg)
        producer_response = await communicator.receive_json_from()
        await communicator.send_json_to(producer_msg_2)
        producer_response_2 = await communicator.receive_json_from()
        # Assert
        assert json.loads(producer_msg['data']['ScriptQueue'])['stream1'] == \
            producer_response['data']['ScriptQueue']['stream1']
        assert json.loads(producer_msg_2['data']['ScriptQueue'])['stream2'] == \
            producer_response_2['data']['ScriptQueue']['stream2']
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_telemetries_for_subscribed_streams_only(self):
        """ Test that clients can receive messages only for subscribed telemetry streams """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        await communicator.send_json_to(subscription_msg)
        await communicator.send_json_to(subscription_msg_2)
        await communicator.send_json_to(unsubscription_msg)
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        # Act
        await communicator.send_json_to(producer_msg)
        with pytest.raises(asyncio.TimeoutError):
            producer_response = await asyncio.wait_for(communicator.receive_json_from(), timeout=0.1)
        await communicator.send_json_to(producer_msg_2)
        producer_response_2 = await communicator.receive_json_from()
        # Assert
        assert json.loads(producer_msg_2['data']['ScriptQueue'])['stream2'] == \
            producer_response_2['data']['ScriptQueue']['stream2']
        await communicator.disconnect()
