import asyncio
import datetime
import json
from channels.layers import get_channel_layer


class HeartbeatManager:

    heartbeat_task = None
    heartbeat_data = {}

    @classmethod
    def initialize(self):
        self.heartbeat_data = {}
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.dispatch_heartbeats())

    @classmethod
    def set_heartbeat_timestamp(self, source, timestamp):
        self.heartbeat_data[source] = timestamp

    @classmethod
    async def dispatch_heartbeats(self):

        channel_layer = get_channel_layer()
        while True:
            try:
                self.set_heartbeat_timestamp('manager', datetime.datetime.now().timestamp())
                # self.set_heartbeat_timestamp('producer', datetime.datetime.now().timestamp())
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
        self.heartbeat_data = {}


