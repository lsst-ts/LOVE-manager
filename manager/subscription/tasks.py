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


"""Background tasks for the subscription app.
Contains the heartbeat dispatch and commander heartbeat query logic
that run as daemon threads, fully independent of WebSocket consumers.
Both loops check ``settings.HEARTBEAT_QUERY_COMMANDER`` on every
iteration so that ``@override_settings`` in tests takes effect
dynamically.
"""

import json
import os
import threading
import time

import requests
from asgiref.sync import async_to_sync


class HeatbeatManagerCommander:
    """Manages the heartbeats of LOVE-commander."""

    _heartbeat_timestamp = None
    _dispatch_thread = None
    _commander_thread = None

    @classmethod
    def set_heartbeat_timestamp(cls, timestamp):
        """Set a given timestamp as the heartbeat for the LOVE-commander.

        Parameters
        ----------
        timestamp : `float`
            Unix timestamp of the heartbeat.
        """
        cls._heartbeat_timestamp = timestamp

    @classmethod
    def _query_commander_loop(cls):
        """Poll the LOVE-Commander ``/heartbeat`` endpoint every 3 seconds.
        Runs in a daemon thread.  Updates the internal heartbeat timestamp
        on each successful response.  Skips polling when
        """
        heartbeat_url = (
            "http://"
            + os.environ.get("COMMANDER_HOSTNAME", "localhost")
            + ":"
            + os.environ.get("COMMANDER_PORT", "8000")
            + "/heartbeat"
        )

        while True:
            try:
                resp = requests.get(heartbeat_url, timeout=5)
                timestamp = resp.json()["timestamp"]
                cls.set_heartbeat_timestamp(timestamp)
            except Exception as e:
                print(e, flush=True)
            time.sleep(3)

    @classmethod
    def _dispatch_heartbeats_loop(cls):
        """Dispatch aggregated heartbeats to the Channels layer
        every 3 seconds. Runs in a daemon thread.
        Uses ``asgiref.async_to_sync`` to call
        ``channel_layer.group_send`` from synchronous code.
        """
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        while True:
            try:
                print(f"Dispatching commander heartbeat to consumers: {cls._heartbeat_timestamp}", flush=True)
                data = json.dumps(
                    {
                        "category": "heartbeat",
                        "data": [
                            {
                                "csc": "Commander",
                                "salindex": 0,
                                "data": {"timestamp": cls._heartbeat_timestamp},
                            }
                        ],
                        "subscription": "heartbeat",
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    "heartbeat-manager-0-stream",
                    {"type": "send_heartbeat", "data": data},
                )
            except Exception as e:
                print(e, flush=True)
            time.sleep(3)

    @classmethod
    def start_heartbeat_tasks(cls):
        """Start both background daemon threads (idempotent).
        Safe to call multiple times — only the first call actually
        spawns threads.  Both threads are daemon threads and will
        be terminated automatically when the main process exits.
        """
        if cls._commander_thread is None:
            cls._commander_thread = threading.Thread(
                target=cls._query_commander_loop,
                daemon=True,
                name="commander-heartbeat-query",
            )
            cls._commander_thread.start()

        if cls._dispatch_thread is None:
            cls._dispatch_thread = threading.Thread(
                target=cls._dispatch_heartbeats_loop,
                daemon=True,
                name="heartbeat-dispatch",
            )
            cls._dispatch_thread.start()
