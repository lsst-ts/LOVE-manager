import json
import pytest
import asyncio
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token

msg_template = {
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


class TestSubscriptionCombinations:
    """ Test that clients can or cannot establish to subscriptions depending on different conditions """

    categories = ['event', 'telemetry']

    cscs = ['ScriptQueue', 'ATDome']

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
                    for stream in self.streams:
                        self.combinations.append({
                            "category": category,
                            "csc": csc,
                            "stream": stream,
                        })

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
                "stream": combination["stream"],
                "category": combination["category"]
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert response['data'] == \
                'Successfully subscribed to {}-{}'.format(combination["csc"], combination["stream"])
        # Act 2 (Unsubscribe)
        for combination in self.combinations:
            msg = {
                "option": "unsubscribe",
                "csc": combination["csc"],
                "stream": combination["stream"],
                "category": combination["category"]
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert response['data'] == \
                'Successfully unsubscribed to {}-{}'.format(combination["csc"], combination["stream"])
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
                "stream": combination["stream"],
                "category": combination["category"]
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
        # Act
        for combination in self.combinations:
            msg = {
                'category': combination['category'],
                'data': {
                    combination['csc']: json.dumps({
                        combination['stream']: {
                            'stream1_param_1': {'value': 1, 'dataType': 'Int'},
                            'stream1_param_2': {'value': 1.02813957817852497, 'dataType': 'Float'}
                        }
                    })
                }
            }
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert
            assert json.loads(msg['data'][combination['csc']])[combination['stream']] == \
                response['data'][combination['csc']][combination['stream']]
        await communicator.disconnect()
