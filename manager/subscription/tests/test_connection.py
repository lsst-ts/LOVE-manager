"""Tests for the connection of users."""
import pytest
import asyncio
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from manager.routing import application
from manager.settings import PROCESS_CONNECTION_PASS
from api.models import Token


class TestClientConnection:
    """Test that clients can or cannot connect depending on different conditions."""

    @pytest.mark.django_db(transaction=True)
    @database_sync_to_async
    def setup(self):
        self.user = User.objects.create_user('username', password='123', email='user@user.cl')
        self.token = Token.objects.create(user=self.user)
        self.user2 = User.objects.create_user('username2', password='123', email='user@user.cl')
        self.token2 = Token.objects.create(user=self.user2)

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connection_with_token(self):
        """Test that clients can connect with a valid token."""
        # Arrange
        await self.setup()
        url = 'manager/ws/subscription/?token={}'.format(self.token)
        communicator = WebsocketCommunicator(application, url)
        # Act
        connected, subprotocol = await communicator.connect()
        # Assert
        assert connected, 'Communicator was not connected'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connection_with_password(self):
        """Test that clients can connect with a valid password."""
        # Arrange
        password = PROCESS_CONNECTION_PASS
        url = 'manager/ws/subscription/?password={}'.format(password)
        communicator = WebsocketCommunicator(application, url)
        # Act
        connected, subprotocol = await communicator.connect()
        # Assert
        assert connected, 'Communicator was not connected'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connection_failed_for_invalid_token(self):
        """Test that clients cannot connect with an invalid token."""
        # Arrange
        await self.setup()
        url = 'manager/ws/subscription/?token={}'.format(str(self.token) + 'fake')
        communicator = WebsocketCommunicator(application, url)
        # Act
        connected, subprotocol = await communicator.connect()
        # Assert
        assert not connected, 'Communicator should not have connected'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connection_failed_for_invalid_password(self):
        """Test that clients cannot connect with an invalid password."""
        # Arrange
        password = PROCESS_CONNECTION_PASS + '_fake'
        url = 'manager/ws/subscription/?password={}'.format(password)
        communicator = WebsocketCommunicator(application, url)
        # Act
        connected, subprotocol = await communicator.connect()
        # Assert
        assert not connected, 'Communicator should not have connected'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connection_interrupted_when_logout_message_is_sent(self):
        """Test that a client gets disconnected when a message is sent for it to logout, for only that client"""
        # ARRANGE
        await self.setup()
        password = PROCESS_CONNECTION_PASS
        subscription_msg = {
            "option": "subscribe",
            "csc": "ScriptQueue",
            "salindex": 0,
            "stream": "stream1",
            "category": "event"
        }
        expected_response = 'Successfully subscribed to event-ScriptQueue-0-stream1'
        channel_layer = get_channel_layer()

        # Connect 3 clients (2 users and 1 with password)
        client1 = WebsocketCommunicator(application, 'manager/ws/subscription/?token={}'.format(self.token))
        client2 = WebsocketCommunicator(application, 'manager/ws/subscription/?token={}'.format(self.token2))
        client3 = WebsocketCommunicator(application, 'manager/ws/subscription/?password={}'.format(password))
        for client in [client1, client2, client3]:
            connected, subprotocol = await client.connect()
            assert connected, 'Error, client was not connected, test could not be completed'

        # ACT
        await channel_layer.group_send(
            'token-{}'.format(str(self.token)),
            {'type': 'logout', 'message': ''}
        )
        await asyncio.sleep(1)  # Wait 1 second, to ensure the connection is closed before we continue

        # ASSERT
        # Client 1 should not be able to send and receive messages
        with pytest.raises(AssertionError):
            await client1.send_json_to(subscription_msg)
            response = await client1.receive_json_from()

        # Client 2 should be able to send and receive messages
        await client2.send_json_to(subscription_msg)
        response = await client2.receive_json_from()
        assert response['data'] == expected_response

        # Client 3 should be able to send and receive messages
        await client3.send_json_to(subscription_msg)
        response = await client3.receive_json_from()
        assert response['data'] == expected_response

        # Disconnect all clients
        await client1.disconnect()
        await client2.disconnect()
        await client3.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connection_interrupted_when_token_is_deleted(self):
        """Test that a client gets disconnected when the token is deleted from the database"""
        # ARRANGE
        await self.setup()
        password = PROCESS_CONNECTION_PASS
        subscription_msg = {
            "option": "subscribe",
            "csc": "ScriptQueue",
            "salindex": 0,
            "stream": "stream1",
            "category": "event"
        }
        expected_response = 'Successfully subscribed to event-ScriptQueue-0-stream1'

        # Connect 3 clients (2 users and 1 with password)
        client1 = WebsocketCommunicator(application, 'manager/ws/subscription/?token={}'.format(self.token))
        client2 = WebsocketCommunicator(application, 'manager/ws/subscription/?token={}'.format(self.token2))
        client3 = WebsocketCommunicator(application, 'manager/ws/subscription/?password={}'.format(password))
        for client in [client1, client2, client3]:
            connected, subprotocol = await client.connect()
            assert connected, 'Error, client was not connected, test could not be completed'

        # ACT: delete de token
        # await self.delete_token()
        await database_sync_to_async(self.token.delete)()
        await asyncio.sleep(1)  # Wait 1 second, to ensure the connection is closed before we continue

        # ASSERT
        # Client 1 should not be able to send and receive messages
        with pytest.raises(AssertionError):
            await client1.send_json_to(subscription_msg)
            response = await client1.receive_json_from()

        # Client 2 should be able to send and receive messages
        await client2.send_json_to(subscription_msg)
        response = await client2.receive_json_from()
        assert response['data'] == expected_response

        # Client 3 should be able to send and receive messages
        await client3.send_json_to(subscription_msg)
        response = await client3.receive_json_from()
        assert response['data'] == expected_response

        # Disconnect all clients
        await client1.disconnect()
        await client2.disconnect()
        await client3.disconnect()
