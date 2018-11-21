from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json

class SubscriptionConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.telemetry_stream_group_names = []

        await self.accept()

    async def disconnect(self, close_code):
        # Leave telemetry_stream group
        for telemetry_stream in self.telemetry_stream_group_names:
            await self.channel_layer.group_discard(
                telemetry_stream,
                self.channel_name
            )
