import asyncio
import datetime
import json
import requests
import os
from channels.layers import get_channel_layer


class HeartbeatManager:

    heartbeat_task = None
    commander_heartbeat_task = None
    heartbeat_data = {}

    @classmethod
    def initialize(self):
        self.heartbeat_data = {}
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.dispatch_heartbeats())
        if not self.commander_heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.query_commander())

    @classmethod
    def set_heartbeat_timestamp(self, source, timestamp):
        self.heartbeat_data[source] = timestamp

    @classmethod
    async def query_commander(self):
        heartbeat_url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/heartbeat"
        while True:
            try:
                # query commander
                resp = requests.get(heartbeat_url)
                timestamp = resp.json()['timestamp']
                #get timestamp
                self.set_heartbeat_timestamp('Commander', timestamp)
                await asyncio.sleep(3)
            except Exception as e:
                print(e)
                await asyncio.sleep(3)

    @classmethod
    async def dispatch_heartbeats(self):
        channel_layer = get_channel_layer()
        while True:
            try:
                self.set_heartbeat_timestamp('Manager', datetime.datetime.now().timestamp())
                data = json.dumps({
                    'category': 'heartbeat',
                    'data': [
                        {
                            'csc': heartbeat_source,
                            'salindex': 0,
                            'data': {'timestamp': self.heartbeat_data[heartbeat_source]}
                        } for heartbeat_source in self.heartbeat_data
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
    async def reset(self):
        if self.heartbeat_task:
            self.heartbeat_task = None
        if self.commander_heartbeat_task:
            self.commander_heartbeat_task = None
        self.heartbeat_data = {}
        self.commander_heartbeat_task = {}

    @classmethod
    async def stop(self):
         if self.heartbeat_task:
            self.heartbeat_task.cancel()
         if self.commander_heartbeat_task:
            self.commander_heartbeat_task.cancel()

