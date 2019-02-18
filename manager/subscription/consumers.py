from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json

class SubscriptionConsumer(AsyncJsonWebsocketConsumer):
    async def join_telemetry_stream(self, csc, stream):
        key = '-'.join([csc, stream])
        if key in self.stream_group_names:
            return
        self.stream_group_names.append([csc, stream])
        await self.channel_layer.group_add(
            key,
            self.channel_name
        )

    async def leave_telemetry_stream(self, csc, stream):
        key = '-'.join([csc, stream])
        if key in self.stream_group_names:
            self.stream_group_names.remove([csc, stream])
        await self.channel_layer.group_discard(
            key,
            self.channel_name
        )        

    async def connect(self):
        self.stream_group_names = []

        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave telemetry_stream group
        for telemetry_stream in self.stream_group_names:
            await self.leave_telemetry_stream(telemetry_stream[0], telemetry_stream[1])

    async def receive_json(self, json_data):
        debug_mode = False
        if debug_mode:
            print('Received', json_data)
            return

        option = None
        if 'option' in json_data:
            option = json_data['option']

        if option:
            if option == 'subscribe':
                # Subscribe and send confirmation
                csc = json_data['csc']
                stream = json_data['stream']
                await self.join_telemetry_stream(csc, stream)
                await self.send_json({
                    'data': 'Successfully subscribed to %s-%s' % (csc, stream)
                })
                return
            
            if option == 'unsubscribe':
                # Unsubscribe nad send confirmation
                csc = json_data['csc']
                stream = json_data['stream']
                await self.leave_telemetry_stream(csc, stream)
                await self.send_json({
                    'data': 'Successfully unsubscribed to %s-%s' % (csc, stream)
                })
                return 
        
        data = json_data['data']
        # Send data to telemetry_stream groups    
        csc_in_data = data.keys()
        for csc in csc_in_data:
            data_csc = json.loads(data[csc])
            telemetry_in_data = data_csc.keys()
            for stream in telemetry_in_data:
                await self.channel_layer.group_send(
                    '-'.join([csc, stream]),
                    {
                        'type': 'subscription_data',
                        'data': {csc: {stream: data_csc[stream]}}
                    }
                )

        # Send all data to consumers subscribed to "all"
        await self.channel_layer.group_send(
            'all-all',
            {
                'type': 'subscription_data',
                'data': data
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