import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from manager.settings import PROCESS_CONNECTION_PASS


class SubscriptionConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        """
        Called upon connection, rejects connection if no authenticated user
        """
        self.stream_group_names = []
        # Reject connection if no authenticated user:
        if self.scope['user'].is_anonymous:
            if self.scope['password'] and self.scope['password'] == PROCESS_CONNECTION_PASS:
                await self.accept()
            else:
                await self.close()
        else:
            await self.accept()

    async def disconnect(self, close_code):
        """ Called upon disconnection """
        # Leave telemetry_stream group
        for telemetry_stream in self.stream_group_names:
            await self.leave_telemetry_stream(telemetry_stream[0], telemetry_stream[1], telemetry_stream[2])

    async def join_telemetry_stream(self, category, csc, stream):
        key = '-'.join([category, csc, stream])
        if [category, csc, stream] in self.stream_group_names:
            return
        self.stream_group_names.append([category, csc, stream])
        await self.channel_layer.group_add(
            key,
            self.channel_name
        )

    async def leave_telemetry_stream(self, category, csc, stream):
        key = '-'.join([category, csc, stream])
        if [category, csc, stream] in self.stream_group_names:
            self.stream_group_names.remove([category, csc, stream])
        await self.channel_layer.group_discard(
            key,
            self.channel_name
        )

    async def receive_json(self, json_data):
        debug_mode = False
        if debug_mode:
            print('Received', json_data)
            return

        option = None
        if 'option' in json_data:
            option = json_data['option']

        category = 'telemetry'
        if 'category' in json_data:
            category = json_data['category']

        if option:
            if option == 'subscribe':
                # Subscribe and send confirmation
                csc = json_data['csc']
                stream = json_data['stream']
                await self.join_telemetry_stream(category, csc, stream)
                await self.send_json({
                    'data': 'Successfully subscribed to %s-%s' % (csc, stream)
                })
                return

            if option == 'unsubscribe':
                # Unsubscribe nad send confirmation
                csc = json_data['csc']
                stream = json_data['stream']
                await self.leave_telemetry_stream(category, csc, stream)
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
            streams_data = {}
            for stream in telemetry_in_data:
                print('Sending data')
                await self.channel_layer.group_send(
                    '-'.join([category, csc, stream]),
                    {
                        'type': 'subscription_data',
                        'category': category,
                        'data': {csc: {stream: data_csc[stream]}}
                    }
                )
                streams_data[stream] = data_csc[stream]
            await self.channel_layer.group_send(
                '-'.join([category, csc, 'all']),
                {
                    'type': 'subscription_data',
                    'category': category,
                    'data': {csc: streams_data}
                }
            )

        # Send all data to consumers subscribed to "all" telemetry
        await self.channel_layer.group_send(
            'telemetry-all-all',
            {
                'type': 'subscription_data',
                'category': category,
                'data': data
            }
        )

        # Send all data to consumers subscribed to "all" events
        await self.channel_layer.group_send(
            'event-all-all',
            {
                'type': 'subscription_data',
                'category': category,
                'data': data
            }
        )

    async def subscription_data(self, event):
        """
        Receive data from telemetry_stream group
        """
        print('Received data')
        data = event['data']
        category = event['category']
        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'data': data,
            'category': category
        }))
