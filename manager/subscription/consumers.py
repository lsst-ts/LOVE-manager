from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json

class SubscriptionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.telemetry_stream_group_names = []

        await self.accept()

    async def join_telemetry_stream(self, telemetry_stream):
        if telemetry_stream in self.telemetry_stream_group_names:
            return
        self.telemetry_stream_group_names.append(telemetry_stream)
        await self.channel_layer.group_add(
            telemetry_stream,
            self.channel_name
        )

    async def receive_json(self, json_data):
        data = json_data['data']
        option = json_data['option']
        if option and option == 'subscribe':
            await self.join_telemetry_stream(data)
            await self.send_json({
                'data': 'Successfully subscribed to %s' % data
            })
            return