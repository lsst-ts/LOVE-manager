from channels.generic.websocket import AsyncWebsocketConsumer
import json

class SubscriptionConsumer(AsyncWebsocketConsumer):

    async def join_telemetry_stream(self, telemetry_stream):
        if telemetry_stream in self.telemetry_stream_group_names:
            return
        self.telemetry_stream_group_names.append(telemetry_stream)
        await self.channel_layer.group_add(
            telemetry_stream,
            self.channel_name
        )

    async def join_telemetry_streams(self, telemetry_streams):
        if isinstance(telemetry_streams, (list,)):
            for telemetry_stream in telemetry_streams:
                await self.join_telemetry_stream(telemetry_stream)
        else:
            await self.join_telemetry_stream(telemetry_streams)

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

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        option = text_data_json['option']
        data = text_data_json['data']
        if option == 'subscribe':
            await self.join_telemetry_streams(data)
            await self.send(text_data=json.dumps({
                'data': 'Successfully subscribed to %s' % json.dumps(data) 
            }))
            return
            
        # Send data to telemetry_stream groups
        for group in self.telemetry_stream_group_names:
            print('group')
            print(group)
            await self.channel_layer.group_send(
                group,
                {
                    'type': 'subscription_data',
                    'data': data
                }
            )

    # Receive data from telemetry_stream group
    async def subscription_data(self, event):
        data = event['data']
        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'data': data
        }))