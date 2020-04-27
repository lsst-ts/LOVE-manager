"""Tests for the subscription of consumers to love_csc streams."""
import pytest
import json
from django.contrib.auth.models import User, Permission
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token
from manager import utils


class TestTimeData:
    def setup_method(self):
        """Set up the TestCase, executed before each test of the TestCase."""
        self.user = User.objects.create_user(
            "username", password="123", email="user@user.cl"
        )
        self.token = Token.objects.create(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))
        self.url = "manager/ws/subscription/?token={}".format(self.token)

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_get_time_data(self):
        # Arrange
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        # Act 1 (Subscribe)
        msg = {
            "action": "get_time_data",
            "request_time": 12312312341123,
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()
        time_data = json.loads(response["time_data"])
        request_time = json.loads(response["request_time"])

        # Assert 1
        assert utils.assert_time_data(time_data)
        assert request_time == 12312312341123
        await communicator.disconnect()