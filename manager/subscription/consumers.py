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
            await self.leave_telemetry_stream(*telemetry_stream)

    async def join_telemetry_stream(self, category, csc, salindex, stream):
        key = '-'.join([category, csc, salindex, stream])
        if [category, csc, salindex, stream] in self.stream_group_names:
            return
        self.stream_group_names.append([category, csc, salindex, stream])
        await self.channel_layer.group_add(
            key,
            self.channel_name
        )

    async def leave_telemetry_stream(self, category, csc, salindex, stream):
        key = '-'.join([category, csc, salindex, stream])
        if [category, csc, salindex, stream] in self.stream_group_names:
            self.stream_group_names.remove([category, csc, salindex, stream])
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
                salindex = json_data['salindex']
                stream = json_data['stream']
                await self.join_telemetry_stream(category, csc, str(salindex), stream)
                await self.send_json({
                    'data': 'Successfully subscribed to %s-%s-%s-%s' % (category, csc, salindex, stream)
                })
                return

            if option == 'unsubscribe':
                # Unsubscribe and send confirmation
                csc = json_data['csc']
                salindex = json_data['salindex']
                stream = json_data['stream']
                await self.leave_telemetry_stream(category, csc, str(salindex),  stream)
                await self.send_json({
                    'data': 'Successfully unsubscribed to %s-%s-%s-%s' % (category, csc, salindex, stream)
                })
                return

            if option == 'cmd_subscribe':
                print('CMD SUBSCRIBE')
                await self.channel_layer.group_add(
                    'CMD_CHANNEL',
                    self.channel_name
                )
                await self.send_json({
                    'data': 'Successfully subscribed to Commands'
                })
                return

            if option == 'cmd_unsubscribe':
                print('CMD SUBSCRIBE')
                await self.channel_layer.group_add(
                    'CMD_CHANNEL',
                    self.channel_name
                )
                await self.send_json({
                    'data': 'Successfully unsubscribed to Commands'
                })

        data = json_data['data']
        # Send data to telemetry_stream groups
        for csc_message in data:
            csc = csc_message['csc']
            salindex = csc_message['salindex']
            data_csc = csc_message['data']
            csc_message['data'] = data_csc
            streams = data_csc.keys()
            streams_data = {}
            for stream in streams:
                await self.channel_layer.group_send(
                    '-'.join([category, csc, str(salindex), stream]),
                    {
                        'type': 'subscription_data',
                        'category': category,
                        'csc': csc,
                        'salindex': salindex,
                        'data': {stream: data_csc[stream]}
                    }
                )
                streams_data[stream] = data_csc[stream]
            await self.channel_layer.group_send(
                '-'.join([category, csc, str(salindex), 'all']),
                {
                    'type': 'subscription_data',
                    'category': category,
                    'data': {csc: streams_data}
                }
            )

        # Send all data to consumers subscribed to "all" subscriptions of the same category
        await self.channel_layer.group_send(
            '{}-all-all-all'.format(category),
            {
                'type': 'subscription_all_data',
                'category': category,
                'data': data
            }
        )

    async def subscription_data(self, event):
        """
        Receive data from telemetry_stream group
        """
        # print('Received data')
        data = event['data']
        category = event['category']
        salindex = event['salindex']
        csc = event['csc']

        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'category': category,
            'data': [{
                'csc': csc,
                'salindex': salindex,
                'data': data,
            }]
        }))

    async def subscription_all_data(self, event):
        """
        Receive data from telemetry_stream group
        """
        data = event['data']
        category = event['category']

        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'category': category,
            'data': data
        }))
