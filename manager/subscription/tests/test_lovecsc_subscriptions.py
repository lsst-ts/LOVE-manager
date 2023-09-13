# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed for Inria Chile.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or at your option any later version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""Tests for the subscription of consumers to love_csc streams."""
import pytest
from django.contrib.auth.models import User, Permission
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token


class TestLOVECscSubscriptions:
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
    async def test_join_and_leave_subscription(self):
        # Arrange
        category = "love_csc"
        csc = "love"
        salindex = 0
        stream = "observingLog"
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        # Act 1 (Subscribe)
        msg = {
            "option": "subscribe",
            "category": category,
            "csc": csc,
            "salindex": salindex,
            "stream": stream,
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()

        # Assert 1
        assert (
            response["data"]
            == f"Successfully subscribed to {category}-{csc}-{salindex}-{stream}"
        )

        # Act 2 (Unsubscribe)
        msg = {
            "option": "unsubscribe",
            "csc": csc,
            "salindex": salindex,
            "stream": stream,
            "category": category,
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()

        # Assert 2
        assert (
            response["data"]
            == f"Successfully unsubscribed to {category}-{csc}-{salindex}-{stream}"
        )

        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_observinglog_to_lovecsc(self):
        """Test that an observing log sent by a client is
        correctly received by a subscribed LOVE-CSC (producer) client"""

        # Arrange
        client_communicator = WebsocketCommunicator(application, self.url)
        lovecsc_communicator = WebsocketCommunicator(application, self.url)
        await client_communicator.connect()
        await lovecsc_communicator.connect()

        # Act 1: Subscribe love_csc and client
        await lovecsc_communicator.send_json_to(
            {
                "option": "subscribe",
                "category": "love_csc",
                "csc": "love",
                "salindex": "0",
                "stream": "observingLog",
            }
        )

        subscription_response = await lovecsc_communicator.receive_json_from()

        # Assert 1:
        assert subscription_response == {
            "data": "Successfully subscribed to love_csc-love-0-observingLog"
        }

        # Act 2: Client sends observing logs
        message = {
            "category": "love_csc",
            "data": [
                {
                    "csc": "love",
                    "salindex": 0,
                    "data": {"observingLog": {"user": "user", "message": "a message"}},
                }
            ],
        }
        await client_communicator.send_json_to(message)

        # Assert 2: the love_csc receives the observing logs
        log_response = await lovecsc_communicator.receive_json_from()

        expected_message = message.copy()
        expected_message["subscription"] = "love_csc-love-0-observingLog"

        assert log_response == expected_message
