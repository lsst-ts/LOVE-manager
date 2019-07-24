"""Tests for the connection of users."""
import pytest
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from manager.routing import application
from manager.settings import PROCESS_CONNECTION_PASS
from api.models import Token


class TestClientConnection:
    """Test that clients can or cannot connect depending on different conditions."""

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_connection_with_token(self):
        """Test that clients can connect with a valid token."""
        # Arrange
        user = User.objects.create_user('username', password='123', email='user@user.cl')
        token = Token.objects.create(user=user)
        url = 'manager/ws/subscription/?token={}'.format(token)
        communicator = WebsocketCommunicator(application, url)
        # Act
        connected, subprotocol = await communicator.connect()
        # Assert
        assert connected, 'Communicator was not connected'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
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
    @pytest.mark.django_db
    async def test_connection_failed_for_invalid_token(self):
        """Test that clients cannot connect with an invalid token."""
        # Arrange
        user = User.objects.create_user('username', password='123', email='user@user.cl')
        token = Token.objects.create(user=user)
        url = 'manager/ws/subscription/?token={}'.format(str(token) + 'fake')
        communicator = WebsocketCommunicator(application, url)
        # Act
        connected, subprotocol = await communicator.connect()
        # Assert
        assert not connected, 'Communicator should not have connected'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
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
