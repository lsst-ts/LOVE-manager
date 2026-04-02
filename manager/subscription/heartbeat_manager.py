# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or at
# your option any later version.
#
# This program is distributed in the hope that it will be useful,but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


import asyncio
import datetime
import json
import os

import requests
from channels.layers import get_channel_layer
from django.conf import settings


class HeartbeatManager:
    """Manages the heartbeats of LOVE software components.

    Uses an internal data structure (dictionary) to store
    the heartbeats of LOVE components.
    Runs 2 tasks in order to dispatch the heartbeats and
    request the LOVE-Commander's heartbeat periodically.
    """

    heartbeat_task = None
    """Reference to the task that dispatches the heartbeats."""

    commander_heartbeat_task = None
    """Reference to the task that requests the
    LOVE-commanderheartbeats.
    """

    heartbeat_data = {}
    """Dictionary comntaining the heartbeats data, indexed
    by source or component, e.g. "Commander".
    """

    consumers = set()
    """Set of the WebSocket consumers that are subscribed
    to the heartbeat subscription.
    """

    def __init__(self):
        self.channel_layer = get_channel_layer()

    def add_consumer(self, consumer):
        """Add a WebSocket consumer to the set of consumers subscribed
        to the heartbeat subscription.
        """
        self.consumers.add(consumer)

    def initialize(self):
        """Initialize the HeartbeatManager

        Run 2 async tasks in the event loop, one to dispatch
        the heartbeats periodically, and the other to request
        the heartbeats from the LOVE-Commander periodically.
        The later only runs if
        ``settings.HEARTBEAT_QUERY_COMMANDER`` is `True`.
        """
        type(self).heartbeat_data = {}
        if not type(self).heartbeat_task:
            type(self).heartbeat_task = asyncio.create_task(self.dispatch_heartbeats())
        if settings.HEARTBEAT_QUERY_COMMANDER:
            if not type(self).commander_heartbeat_task:
                type(self).commander_heartbeat_task = asyncio.create_task(self.query_commander())

    @classmethod
    def set_heartbeat_timestamp(cls, source, timestamp):
        """Set a given timestamp as the heartbeat for a given source.

        Parameters
        ----------
        source: `string`
            Name of the component to save the heartbeat, e.g. "Commander"
        timestamp: `float`
            timestamp of the heartbeat
        """
        cls.heartbeat_data[source] = timestamp

    @classmethod
    async def query_commander(cls):
        """Query the heartbeat from the LOVE-Commander periodically.

        This is what the `commander_heartbeat_task` does.
        """
        heartbeat_url = (
            "http://"
            + os.environ.get("COMMANDER_HOSTNAME")
            + ":"
            + os.environ.get("COMMANDER_PORT")
            + "/heartbeat"
        )
        while True:
            try:
                resp = requests.get(heartbeat_url)
                timestamp = resp.json()["timestamp"]
                cls.set_heartbeat_timestamp("Commander", timestamp)
                await asyncio.sleep(3)
            except Exception as e:
                print(e, flush=True)
                await asyncio.sleep(3)

    async def dispatch_heartbeats(self):
        """Dispatch all the heartbeats to the websocket consumer.

        This is what the `heartbeat_task` does.
        """
        while True:
            try:
                self.set_heartbeat_timestamp("Manager", datetime.datetime.now().timestamp())
                data = json.dumps(
                    {
                        "category": "heartbeat",
                        "data": [
                            {
                                "csc": heartbeat_source,
                                "salindex": 0,
                                "data": {"timestamp": self.heartbeat_data[heartbeat_source]},
                            }
                            for heartbeat_source in self.heartbeat_data
                        ],
                        "subscription": "heartbeat",
                    }
                )
                for consumer in self.consumers:
                    await self.channel_layer.group_send(
                        consumer,
                        {"type": "send_heartbeat", "data": data},
                    )
                await asyncio.sleep(3)
            except Exception as e:
                print(e, flush=True)
                await asyncio.sleep(3)

    @classmethod
    async def reset(cls):
        """Reset the `HeartbeatManager`, changing the tasks references
        and heartbeats dictionary back to their default values.
        """
        if cls.heartbeat_task:
            cls.heartbeat_task = None
        if cls.commander_heartbeat_task:
            cls.commander_heartbeat_task = None
        cls.heartbeat_data = {}
        cls.consumers = set()

    @classmethod
    async def stop(cls):
        """Stop (cancel) the tasks."""
        if cls.heartbeat_task:
            cls.heartbeat_task.cancel()
        if cls.commander_heartbeat_task:
            cls.commander_heartbeat_task.cancel()
