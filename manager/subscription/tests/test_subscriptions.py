import asyncio
import json
import pytest
import random
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token

msg_template = {
    "category": "telemetry",
    "data": [
        {
            "csc": "ScriptQueue",
            "salindex": 1,
            "data": json.dumps({
                "stream1": {
                    "stream1_param_1": {"value": 1, "dataType": "Int"},
                    "stream1_param_2": {"value": 1.02813957817852497, "dataType": "Float"}
                },
                "stream2": {
                    "stream1_param_1": {"value": 1, "dataType": "Int"},
                    "stream1_param_2": {"value": 1.02813957817852497, "dataType": "Float"}
                }
            })
        }
    ]
}


class TestSubscriptionCombinations:
    """ Test that clients can or cannot establish to subscriptions depending on different conditions """

    categories = ['event', 'telemetry']

    cscs = ['ScriptQueue', 'ATDome']

    salindices = [1, 2]

    streams = ['stream1', 'stream2']

    combinations = []

    def setup_method(self):
        """ TestCase setup, executed before each test of the TestCase """
        self.user = User.objects.create_user('username', password='123', email='user@user.cl')
        self.token = Token.objects.create(user=self.user)
        self.url = 'manager/ws/subscription/?token={}'.format(self.token)
        if len(self.combinations) == 0:
            for category in self.categories:
                for csc in self.cscs:
                    for salindex in self.salindices:
                        for stream in self.streams:
                            self.combinations.append({
                                "category": category,
                                "csc": csc,
                                "salindex": salindex,
                                "stream": stream,
                            })

    def build_messages(self, category, csc, salindex, streams):
        """ Builds and returns messages to send and expect, for testing purposes

        Parameters
        ----------
        category: `string`
            category of the message
        csc: `string`
            CSC of the message
        streams: `[string]`
            list of streams for which to add values in the message

        Returns
        -------
        sent: `{}`
            Dictionary containing the message to send in the test
        expected: `{}`
            Dictionary containing the expected response to be received by the client in the test
        """
        sent = {
            'category': category,
            'data': [{
                'csc': csc,
                'salindex': salindex,
                'data': json.dumps(
                    {stream: {'value': 1.02813957817852497, 'dataType': 'Float'}
                        for stream in streams}
                )
            }]
        }
        expected = {
            'category': category,
            'data': [{
                'csc': csc,
                'salindex': salindex,
                'data': {stream: {'value': 1.02813957817852497, 'dataType': 'Float'} for stream in streams}
            }]
        }

        return sent, expected

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_join_and_leave_every_subscription(self):
        """ Test that clients can join and then leave any subscription stream """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        # Act 1  (Subscribe)
        for combination in self.combinations:
            msg = {
                "option": "subscribe",
                "csc": combination["csc"],
                "salindex": combination["salindex"],
                "stream": combination["stream"],
                "category": combination["category"]
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert response['data'] == \
                'Successfully subscribed to {}-{}-{}-{}'.format(
                    combination["category"], combination["csc"], combination["salindex"], combination["stream"])
        # Act 2 (Unsubscribe)
        for combination in self.combinations:
            msg = {
                "option": "unsubscribe",
                "csc": combination["csc"],
                "salindex": combination["salindex"],
                "stream": combination["stream"],
                "category": combination["category"]
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert response['data'] == \
                'Successfully unsubscribed to {}-{}-{}-{}'.format(
                    combination["category"], combination["csc"], combination["salindex"], combination["stream"])
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_all_subscription(self):
        """ Test that clients subscribed to all receive messages from all """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        for combination in self.combinations:
            msg = {
                "option": "subscribe",
                "csc": combination["csc"],
                "salindex": combination["salindex"],
                "stream": combination["stream"],
                "category": combination["category"]
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
        # Act
        for combination in self.combinations:
            msg, expected = \
                self.build_messages(combination['category'], combination['csc'], combination['salindex'], [
                                    combination['stream']])
            # assert False
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert response == expected
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_message_for_subscribed_group_only(self):
        """ Test that clients subscribed to some groups only receive messages from those """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        subscription_msg = {
            'option': 'subscribe',
            'category': 'telemetry',
            'csc': 'ScriptQueue',
            'salindex': 1,
            'stream': 'stream1',
        }
        await communicator.send_json_to(subscription_msg)
        await communicator.receive_json_from()
        # Act
        for combination in self.combinations:
            msg, expected = \
                self.build_messages(combination['category'], combination['csc'], combination['salindex'], [
                                    combination['stream']])
            await communicator.send_json_to(msg)

            if combination['category'] == subscription_msg['category'] and \
                    combination['csc'] == subscription_msg['csc'] and \
                    combination['salindex'] == subscription_msg['salindex'] and \
                    combination['stream'] == subscription_msg['stream']:
                response = await communicator.receive_json_from()
                # Assert
                assert response == expected
            else:
                # Assert
                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(communicator.receive_json_from(), timeout=0.1)
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_message_for_subscribed_groups_only(self):
        """ Test that clients subscribed to some groups only receive messages from those """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        for combination in self.combinations:
            # Arrange: Subscribe to 1
            subscription_msg = {
                "csc": combination["csc"],
                "stream": combination["stream"],
                "category": combination["category"],
                "salindex": combination["salindex"]
            }
            subscription_msg['option'] = 'subscribe'
            await communicator.send_json_to(subscription_msg)
            await communicator.receive_json_from()
            # Act: Send and receive all
            for combination in self.combinations:
                msg, expected = \
                    self.build_messages(combination['category'], combination['csc'], combination['salindex'], [
                                        combination['stream']])
                await communicator.send_json_to(msg)

                if combination['category'] == subscription_msg['category'] and \
                        combination['csc'] == subscription_msg['csc'] and \
                        combination['salindex'] == subscription_msg['salindex'] and \
                        combination['stream'] == subscription_msg['stream']:
                    response = await communicator.receive_json_from()
                    # Assert: receive the one subscribed to
                    assert response == expected
                else:
                    # Assert: not receive all the others
                    with pytest.raises(asyncio.TimeoutError):
                        await asyncio.wait_for(communicator.receive_json_from(), timeout=0.1)
            # Clean: Unsubscribe from 1
            subscription_msg['option'] = 'unsubscribe'
            await communicator.send_json_to(subscription_msg)
            await communicator.receive_json_from()
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_part_of_message_for_subscribed_groups_only(self):
        """ Test that clients subscribed to some groups only receive the corresponding part of incoming messages """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        for combination in self.combinations:
            # Arrange: Subscribe to 1
            subscription_msg = {
                "csc": combination["csc"],
                "stream": combination["stream"],
                "category": combination["category"],
                "salindex": combination["salindex"]
            }
            subscription_msg['option'] = 'subscribe'
            await communicator.send_json_to(subscription_msg)
            await communicator.receive_json_from()
            # Act: Send the big message
            msg, ignore = \
                self.build_messages(
                    combination['category'], combination['csc'],  combination['salindex'], self.streams)
            await communicator.send_json_to(msg)

            if combination['category'] == subscription_msg['category'] and \
                    combination['csc'] == subscription_msg['csc'] and \
                    combination['salindex'] == subscription_msg['salindex'] and \
                    combination['stream'] == subscription_msg['stream']:
                response = await communicator.receive_json_from()
                # Assert: receive the one subscribed to
                ignore, expected = \
                    self.build_messages(combination['category'], combination['csc'],  combination['salindex'], [
                                        combination['stream']])
                assert response == expected
            else:
                # Assert: not receive all the others
                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(communicator.receive_json_from(), timeout=0.1)
            # Clean: Unsubscribe from 1
            subscription_msg['option'] = 'unsubscribe'
            await communicator.send_json_to(subscription_msg)
            await communicator.receive_json_from()
        await communicator.disconnect()
