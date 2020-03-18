import asyncio
import datetime
import json
from channels.layers import get_channel_layer


class HeartbeatManager:

    heartbeat_task = None

    @classmethod
    def initialize(self):
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.dispatch_heartbeats())

    @classmethod
    async def dispatch_heartbeats(self):

        channel_layer = get_channel_layer()
        while True:
            try:
                data = json.dumps({
                    'category': 'heartbeat',
                    'data': [{
                        'csc': 'manager',
                        'salindex': 0,
                        'data': {'timestamp': datetime.datetime.now().timestamp()}
                    }],
                    'subscription': 'heartbeat'
                })
                await asyncio.sleep(3)
                await channel_layer.group_send(
                    'heartbeat-manager-0-stream',
                    {'type': 'send_heartbeat', 'data': data}
                )
            except Exception as e:
                print(e)
                await asyncio.sleep(3)

    @classmethod
    async def reset(self):
        if self.heartbeat_task:
            self.heartbeat_task = None
