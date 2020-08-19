import asyncio
import datetime
import json
import requests
import os
from channels.layers import get_channel_layer


class HeartbeatManager:
    """Manages the heartbeats of LOVE software components.

    Uses an internal data structure (dictionary) to store the heartbeats of LOVE components.
    Runs 2 tasks in order to dispatch the heartbeats and request the LOVE-Commander's heartbeat periodically.
    """

    heartbeat_task = None
    """Reference to the task that dispatches the heartbeats."""

    commander_heartbeat_task = None
    """Reference to the task that requests the LOVE_COmmander heartbeats."""

    heartbeat_data = {}
    """Dictionary comntaining the heartbeats data, indexed by source or component, e.g. "Commander"."""

    @classmethod
    def initialize(self):
        """Initialize the HeartbeatManager

        Run 2 async tasks in the event loop, one to dispatch the heartbeats periodically,
        and the other to request the heartbeats from the LOVE-Commander periodically.
        """
        self.heartbeat_data = {}
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.dispatch_heartbeats())
        if not self.commander_heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.query_commander())

    @classmethod
    def set_heartbeat_timestamp(self, source, timestamp):
        """Set a given timestamp as the heartbeat for a given source

        Parameters
        ----------
        source: `string`
            Name of the component to save the heartbeat, e.g. "Commander"
        timestamp: `float`
            timestamp of the heartbeat
        """
        self.heartbeat_data[source] = timestamp

    @classmethod
    async def query_commander(self):
        """Query the heartbeat from the LOVE-Commander periodically.

        This is what the `commander_heartbeat_task` does
        """
        heartbeat_url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/heartbeat"
        while True:
            try:
                # query commander
                resp = requests.get(heartbeat_url)
                timestamp = resp.json()["timestamp"]
                # get timestamp
                self.set_heartbeat_timestamp("Commander", timestamp)
                await asyncio.sleep(3)
            except Exception as e:
                print(e)
                await asyncio.sleep(3)

    @classmethod
    async def dispatch_heartbeats(self):
        """Dispatch all the heartbeats to the corresponding group in the Channels Layer.

        This is what the `heartbeat_task` does
        """
        channel_layer = get_channel_layer()
        while True:
            try:
                self.set_heartbeat_timestamp(
                    "Manager", datetime.datetime.now().timestamp()
                )
                data = json.dumps(
                    {
                        "category": "heartbeat",
                        "data": [
                            {
                                "csc": heartbeat_source,
                                "salindex": 0,
                                "data": {
                                    "timestamp": self.heartbeat_data[heartbeat_source]
                                },
                            }
                            for heartbeat_source in self.heartbeat_data
                        ],
                        "subscription": "heartbeat",
                    }
                )
                await channel_layer.group_send(
                    "heartbeat-manager-0-stream",
                    {"type": "send_heartbeat", "data": data},
                )
                await asyncio.sleep(3)
            except Exception as e:
                print(e)
                await asyncio.sleep(3)

    @classmethod
    async def reset(self):
        """Reset the `HeartbeatManager`, changing the tasks references and heartbeats dictionary back to their default values."""
        if self.heartbeat_task:
            self.heartbeat_task = None
        if self.commander_heartbeat_task:
            self.commander_heartbeat_task = None
        self.heartbeat_data = {}
        self.commander_heartbeat_task = {}

    @classmethod
    async def stop(self):
        """Stop (cancel) the tasks."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.commander_heartbeat_task:
            self.commander_heartbeat_task.cancel()

