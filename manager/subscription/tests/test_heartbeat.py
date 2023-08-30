# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile and Vera C. Rubin Observatory Telescope
# and Site Systems.
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
import datetime
import pytest
import asyncio
from django.contrib.auth.models import User, Permission
from django.test import override_settings
from channels.testing import WebsocketCommunicator
from manager.routing import application
from api.models import Token
from subscription.heartbeat_manager import HeartbeatManager


class TestHeartbeat:

    no_reception_timeout = 4

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
    @override_settings(HEARTBEAT_QUERY_COMMANDER=True)
    async def test_join_and_leave_subscription(self):
        # Arrange
        hb_manager = HeartbeatManager()
        await hb_manager.reset()
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        assert connected

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
        assert (
            response["data"] == "Successfully subscribed to heartbeat-manager-0-stream"
        )

        response = await communicator.receive_json_from(timeout=10)
        assert response["data"][0]["data"]["timestamp"] is not None
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
        assert (
            response["data"]
            == "Successfully unsubscribed to heartbeat-manager-0-stream"
        )

        await communicator.disconnect()

        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        assert connected

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
        assert (
            response["data"] == "Successfully subscribed to heartbeat-manager-0-stream"
        )

        response = await communicator.receive_json_from(timeout=10)
        assert response["data"][0]["data"]["timestamp"] is not None
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
        assert (
            response["data"]
            == "Successfully unsubscribed to heartbeat-manager-0-stream"
        )
        await communicator.disconnect()
        await hb_manager.stop()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    @override_settings(HEARTBEAT_QUERY_COMMANDER=True)
    async def test_heartbeat_manager_setter(self):

        hb_manager = HeartbeatManager()
        # Arrange
        await hb_manager.reset()
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        assert connected

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
        assert (
            response["data"] == "Successfully subscribed to heartbeat-manager-0-stream"
        )

        response = await communicator.receive_json_from(timeout=10)
        assert response["data"][0]["data"]["timestamp"] is not None

        # Act 2 Set producer heartbeat
        timestamp = datetime.datetime.now().timestamp()
        hb_manager.set_heartbeat_timestamp("Producer", timestamp)
        response = await communicator.receive_json_from(timeout=4)

        # Assert 2
        heartbeat_sources = [source["csc"] for source in response["data"]]
        assert "Producer" in heartbeat_sources
        await communicator.disconnect()
        await hb_manager.stop()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    @override_settings(HEARTBEAT_QUERY_COMMANDER=True)
    async def test_producer_heartbeat(self):

        # Arrange
        hb_manager = HeartbeatManager()
        await hb_manager.reset()
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        assert connected

        # Act 1 (Subscribe)
        msg = {
            "option": "subscribe",
            "category": "event",
            "csc": "Heartbeat",
            "salindex": 0,
            "stream": "stream",
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()

        # Assert 1
        assert response["data"] == "Successfully subscribed to event-Heartbeat-0-stream"

        # Act 2 (Send producer heartbeat through websocket)
        heartbeat = {
            "csc": "Test",
            "salindex": 1,
            "lost": 0,
            "last_heartbeat_timestamp": 1000,
            "max_lost_heartbeats": 5,
        }
        msg = {
            "category": "event",
            "data": [
                {"csc": "Heartbeat", "salindex": 0, "data": {"stream": heartbeat}},
            ],
        }

        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()

        # Assert 2 (Get producer heartbeat data)
        heartbeat_sources = [source["csc"] for source in response["data"]]
        assert "Heartbeat" in heartbeat_sources
        await communicator.disconnect()
        await hb_manager.stop()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    @override_settings(HEARTBEAT_QUERY_COMMANDER=True)
    async def test_unauthorized_commander(self):

        # Arrange
        hb_manager = HeartbeatManager()
        await hb_manager.reset()
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        assert connected

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
        assert (
            response["data"] == "Successfully subscribed to heartbeat-manager-0-stream"
        )
        response = await communicator.receive_json_from(timeout=5)
        assert response["data"][0]["data"]["timestamp"] is not None

        # Act 2 (Wait for query to commander)
        hb_manager.set_heartbeat_timestamp("Commander", 123123123)
        response = await communicator.receive_json_from(timeout=5)

        # Assert 2 (Get producer heartbeat data)
        heartbeat_sources = [source["csc"] for source in response["data"]]
        assert "Commander" in heartbeat_sources
        commander_heartbeat = [
            source["data"]
            for source in response["data"]
            if source["csc"] == "Commander"
        ][0]
        commander_timestamp = commander_heartbeat["timestamp"]
        assert commander_timestamp == 123123123
        await communicator.disconnect()
        await hb_manager.stop()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    @override_settings(HEARTBEAT_QUERY_COMMANDER=True)
    async def test_heartbeat_commander_with_heartbeat_query_commander_in_true(self):

        hb_manager = HeartbeatManager()
        # Arrange
        await hb_manager.reset()
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        assert connected

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
        assert (
            response["data"] == "Successfully subscribed to heartbeat-manager-0-stream"
        )

        response = await communicator.receive_json_from(timeout=10)
        assert response["data"][0]["data"]["timestamp"] is not None

        # Act 2 Set producer heartbeat
        timestamp = datetime.datetime.now().timestamp()
        hb_manager.set_heartbeat_timestamp("Commander", timestamp)
        response = await communicator.receive_json_from(timeout=4)

        # Assert 2
        heartbeat_sources = [source["csc"] for source in response["data"]]
        assert "Commander" in heartbeat_sources
        await communicator.disconnect()
        await hb_manager.stop()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    @override_settings(HEARTBEAT_QUERY_COMMANDER=False)
    async def test_heartbeat_commander_with_heartbeat_query_commander_in_false(self):

        hb_manager = HeartbeatManager()
        # Arrange
        await hb_manager.reset()
        communicator = WebsocketCommunicator(application, self.url)
        connected, subprotocol = await communicator.connect()

        assert connected

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
        assert (
            response["data"] == "Successfully subscribed to heartbeat-manager-0-stream"
        )

        try:
            response = await communicator.receive_json_from(timeout=10)
            # assert response["data"][0]["data"]["timestamp"] is not None

            # Act 2 Set producer heartbeat
            timestamp = datetime.datetime.now().timestamp()
            hb_manager.set_heartbeat_timestamp("Commander_FAKE", timestamp)
            response = await communicator.receive_json_from(timeout=4)

            # Assert 2
            heartbeat_sources = [source["csc"] for source in response["data"]]
            assert "Commander_FAKE" not in heartbeat_sources

        except asyncio.TimeoutError:
            # Assert 2
            assert True

        finally:
            await communicator.disconnect()
            await hb_manager.stop()
