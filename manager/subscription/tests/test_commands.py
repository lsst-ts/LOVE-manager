import asyncio
import json
import pytest
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token


class TestCommands:
    """ Test that clients can or cannot establish to subscriptions depending on different conditions """

    def setup_method(self):
        """ TestCase setup, executed before each test of the TestCase """
        self.user = User.objects.create_user('username', password='123', email='user@user.cl')
        self.token = Token.objects.create(user=self.user)
        self.url = 'manager/ws/subscription/?token={}'.format(self.token)

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_join_and_leave_commands_channel(self):
        """ Test that clients can join and then leave the commands channel """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
        # Act 1  (Subscribe)
        msg = {
            "option": "cmd_subscribe",
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()
        # Assert 1
        assert response['data'] == 'Successfully subscribed to Commands'
        # Act 2 (Unsubscribe)
        msg = {
            "option": "cmd_unsubscribe",
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()
        # Assert 2
        assert response['data'] == 'Successfully unsubscribed to Commands'
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_and_send_commands(self):
        """ Test that clients can receive and (re)send commands """
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()
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
        # msg = {
        #     'option': 'cmd',
        #     'cmd': 'ScriptQueue_add',
        #     'params': '{param1: value1, param2: value2}',
        #     'component': 'ScriptQueue',
        # }
        # expected = {
        #     'cmd': 'ScriptQueue_add',
        #     'params': '{param1: value1, param2: value2}',
        #     'component': 'ScriptQueue',
        # }
        msg = {
            'category': 'cmd',
            'data': [{
                'csc': 'all',
                'salindex': 'all',
                'cmd_stream': {
                    'data': {
                        'cmd': 'Add Script',
                        'params': '{param1: value1, param2: value2}',
                    }
                }
            }]
        }
        expected = {
            'cmd': 'ScriptQueue_add',
            'params': '{param1: value1, param2: value2}',
            'component': 'ScriptQueue',
        }
        # assert False
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()
        # Assert
        print('Response: ', response)
        assert response == expected
        await communicator.disconnect()
