"""Tests for the subscription of consumers to love_csc streams."""
import asyncio
import pytest
from django.contrib.auth.models import User, Permission
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token


class TestHeartbeat:

    def setup_method(self):
        """Set up the TestCase, executed before each test of the TestCase."""
        self.user = User.objects.create_user('username', password='123', email='user@user.cl')
        self.token = Token.objects.create(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(name='Execute Commands'))
        self.url = 'manager/ws/subscription/?token={}'.format(self.token)

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_join_and_leave_subscription(self):
        # Arrange
        category = 'heartbeat'
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        # Act 1 (Subscribe)
        msg = {
            "option": "subscribe",
            "category": "heartbeat",
            "csc": "manager",
            "salindex": 0,
            "stream": "stream",
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()

        # Assert 1
        assert response['data'] == f'Successfully subscribed to heartbeat-manager-0-stream'

        response = await communicator.receive_json_from(timeout=5)
        assert response['data'][0]['data']['timestamp'] != None  
        # Act 2 (Unsubscribe)
        msg = {
            "option": "unsubscribe",
            "category": "heartbeat",
            "csc": "manager",
            "salindex": 0,
            "stream": "stream",
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()

        # Assert 2
        assert response['data'] == f'Successfully unsubscribed to heartbeat-manager-0-stream'

        await communicator.disconnect()
