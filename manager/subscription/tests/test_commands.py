"""Tests for the sending of comands."""
import pytest
from django.contrib.auth.models import User, Permission
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token


class TestCommands:
    """Test that clients can or cannot send commands depending on different conditions."""

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
        self.url = 'manager/ws/subscription/?token={}'.format(self.token)

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
    async def test_authorized_user_can_send_command(self):
        """Test that an authorized user can send commands."""
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        self.user.user_permissions.add(Permission.objects.get(name='Execute Commands'))
        connected, subprotocol = await communicator.connect()
        msg = {
            "option": "subscribe",
            "csc": "ScriptQueue",
            "salindex": 1,
            "stream": "stream1",
            "category": "cmd"
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()
        # Act
        msg, expected = self.build_messages('cmd', 'ScriptQueue', 1, ['stream1'])
        await communicator.send_json_to(msg)
        # Assert
        response = await communicator.receive_json_from()
        assert response == expected
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_unauthorized_user_cannot_send_command(self):
        """Test that an unauthorized user cannot send commands."""
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        msg = {
            "option": "subscribe",
            "csc": "ScriptQueue",
            "salindex": 1,
            "stream": "stream1",
            "category": "cmd"
        }
        await communicator.send_json_to(msg)
        await communicator.receive_json_from()
        # Act
        msg, expected = self.build_messages('cmd', 'ScriptQueue', 1, ['stream1'])
        await communicator.send_json_to(msg)
        # Assert
        response = await communicator.receive_json_from()
        assert 'Command not sent' in response['data']
        await communicator.disconnect()
