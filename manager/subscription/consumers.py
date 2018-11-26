from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json

class SubscriptionConsumer(AsyncJsonWebsocketConsumer):
    async def join_telemetry_stream(self, telemetry_stream):
        if telemetry_stream in self.telemetry_stream_group_names:
            return
        self.telemetry_stream_group_names.append(telemetry_stream)
        await self.channel_layer.group_add(
            telemetry_stream,
            self.channel_name
        )
        
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

    async def receive_json(self, json_data):

        option = None
        if 'option' in json_data:
            option = json_data['option']
        data = json_data['data']

        if option and option == 'subscribe':
            # Subscribe and send confirmation
            await self.join_telemetry_stream(data)
            await self.send_json({
                'data': 'Successfully subscribed to %s' % data
            })
            return
        
        # Send data to telemetry_stream groups        
        telemetry_in_data = data.keys()
        for telemetry_group in telemetry_in_data:
            await self.channel_layer.group_send(
                telemetry_group,
                {
                    'type': 'subscription_data',
                    'data': data[telemetry_group]
                }
            )

    async def subscription_data(self, event):
        """
            Receive data from telemetry_stream group
        """
        data = event['data']
        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'data': data
        }))