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

    class __HeartbeatManager:
    
        heartbeat_task = None
        """Reference to the task that dispatches the heartbeats."""
        
        commander_heartbeat_task = None
        """Reference to the task that requests the LOVE_COmmander heartbeats."""

        heartbeat_data = {}
        """Dictionary comntaining the heartbeats data, indexed by source or component, e.g. "Commander"."""

        @classmethod
        def initialize(cls):
            """Initialize the HeartbeatManager

            Run 2 async tasks in the event loop, one to dispatch the heartbeats periodically,
            and the other to request the heartbeats from the LOVE-Commander periodically.
            """
            cls.heartbeat_data = {}
            if not cls.heartbeat_task:
                cls.heartbeat_task = asyncio.create_task(cls.dispatch_heartbeats())
            if not cls.commander_heartbeat_task:
                cls.commander_heartbeat_task = asyncio.create_task(cls.query_commander())

        @classmethod
        def set_heartbeat_timestamp(cls, source, timestamp):
            """Set a given timestamp as the heartbeat for a given source

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

            This is what the `commander_heartbeat_task` does
            """
            heartbeat_url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/heartbeat"
            while True:
                try:
                    # query commander
                    resp = requests.get(heartbeat_url)
                    timestamp = resp.json()['timestamp']
                    #get timestamp
                    cls.set_heartbeat_timestamp('Commander', timestamp)
                    await asyncio.sleep(3)
                except Exception as e:
                    print(e)
                    await asyncio.sleep(3)

        @classmethod
        async def dispatch_heartbeats(cls):
            """Dispatch all the heartbeats to the corresponding group in the Channels Layer.

            This is what the `heartbeat_task` does
            """
            channel_layer = get_channel_layer()
            while True:
                try:
                    print('sending data')
                    cls.set_heartbeat_timestamp('Manager', datetime.datetime.now().timestamp())
                    data = json.dumps({
                        'category': 'heartbeat',
                        'data': [
                            {
                                'csc': heartbeat_source,
                                'salindex': 0,
                                'data': {'timestamp': cls.heartbeat_data[heartbeat_source]}
                            } for heartbeat_source in cls.heartbeat_data
                        ],
                        'subscription': 'heartbeat'
                    })
                    await channel_layer.group_send(
                        'heartbeat-manager-0-stream',
                        {'type': 'send_heartbeat', 'data': data}
                    )
                    await asyncio.sleep(3)
                except Exception as e:
                    print(e)
                    await asyncio.sleep(3)

        @classmethod
        async def reset(cls):
            """Reset the `HeartbeatManager`, changing the tasks references and heartbeats dictionary back to their default values."""
            if cls.heartbeat_task:
                cls.heartbeat_task = None
            if cls.commander_heartbeat_task:
                cls.commander_heartbeat_task = None
            cls.heartbeat_data = {}
            cls.commander_heartbeat_task = {}

        @classmethod
        async def stop(cls):
            """Stop (cancel) the tasks."""
            if cls.heartbeat_task:
                cls.heartbeat_task.cancel()
            if cls.commander_heartbeat_task:
                cls.commander_heartbeat_task.cancel()

    instance = None
    def __init__(self):
        if not HeartbeatManager.instance:
            HeartbeatManager.instance = HeartbeatManager.__HeartbeatManager()

    def __getattr__(self, name):
        return getattr(self.instance, name)