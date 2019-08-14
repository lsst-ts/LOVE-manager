"""Tests for the subscription of consumers to streams."""
import asyncio
import pytest
from django.contrib.auth.models import User, Permission
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token


class TestSubscriptionCombinations:
    """Test that clients can or cannot establish to subscriptions depending on different conditions."""

    categories = ['event', 'telemetry', 'cmd']

    cscs = ['ScriptQueue', 'ATDome']

    salindices = [1, 2]

    streams = ['stream1', 'stream2']

    combinations = []

    no_reception_timeout = 0.001

    def setup_method(self):
        """Set up the TestCase, executed before each test of the TestCase."""
        self.user = User.objects.create_user('username', password='123', email='user@user.cl')
        self.token = Token.objects.create(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(name='Execute Commands'))
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
        """Build and return messages to send and expect, for testing purposes.

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
        response = {
            'category': category,
            'data': [{
                'csc': csc,
                'salindex': salindex,
                'data': {stream: {'value': 1.02813957817852497, 'dataType': 'Float'} for stream in streams}
            }]
        }
        return response, response

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_join_and_leave_every_subscription(self):
        """Test that clients can join and then leave any subscription stream."""
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
    async def test_join_and_leave_all_subscription(self):
        """Test that clients can subscribe and leave all streams."""
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        # Act 1 (Subscribe)
        for category in self.categories:
            msg = {
                "option": "subscribe",
                "category": category,
                "csc": 'all',
                "salindex": 'all',
                "stream": 'all',
            }
            await communicator.send_json_to(msg)
            # Assert 1
            response = await communicator.receive_json_from()
            assert response['data'] == 'Successfully subscribed to {}-all-all-all'.format(category)
        # Act 2 (Unsubscribe)
        for category in self.categories:
            msg = {
                "option": "unsubscribe",
                "category": category,
                "csc": 'all',
                "salindex": 'all',
                "stream": 'all',
            }
            await communicator.send_json_to(msg)
            # Assert 2
            response = await communicator.receive_json_from()
            assert response['data'] == 'Successfully unsubscribed to {}-all-all-all'.format(category)
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_messages_from_every_subscription(self):
        """Test that clients subscribed (individually) to every stream receive messages from all of them."""
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
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert response == expected
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_messages_from_all_subscription(self):
        """Test that clients subscribed to all streams receive messages from all of them."""
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        for category in self.categories:
            msg = {
                "option": "subscribe",
                "category": category,
                "csc": 'all',
                "salindex": 'all',
                "stream": 'all',
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
        # Act
        for combination in self.combinations:
            msg, expected = \
                self.build_messages(combination['category'], combination['csc'], combination['salindex'], [
                                    combination['stream']])
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert response == expected
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_message_for_subscribed_group_only(self):
        """Test that clients subscribed to some groups only receive messages from those."""
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
                    await asyncio.wait_for(communicator.receive_json_from(), timeout=self.no_reception_timeout)
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_message_for_subscribed_groups_only(self):
        """Test that clients subscribed to some groups only receive messages from those."""
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
                        await asyncio.wait_for(communicator.receive_json_from(), timeout=self.no_reception_timeout)
            # Clean: Unsubscribe from 1
            subscription_msg['option'] = 'unsubscribe'
            await communicator.send_json_to(subscription_msg)
            await communicator.receive_json_from()
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_part_of_message_for_subscribed_groups_only(self):
        """Test that clients subscribed to some groups only receive the corresponding part of incoming messages."""
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
                    combination['category'], combination['csc'], combination['salindex'], self.streams)
            await communicator.send_json_to(msg)

            if combination['category'] == subscription_msg['category'] and \
                    combination['csc'] == subscription_msg['csc'] and \
                    combination['salindex'] == subscription_msg['salindex'] and \
                    combination['stream'] == subscription_msg['stream']:
                response = await communicator.receive_json_from()
                # Assert: receive the one subscribed to
                ignore, expected = \
                    self.build_messages(combination['category'], combination['csc'], combination['salindex'], [
                                        combination['stream']])
                assert response == expected
            else:
                # Assert: not receive all the others
                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(communicator.receive_json_from(), timeout=self.no_reception_timeout)
            # Clean: Unsubscribe from 1
            subscription_msg['option'] = 'unsubscribe'
            await communicator.send_json_to(subscription_msg)
            await communicator.receive_json_from()
        await communicator.disconnect()
