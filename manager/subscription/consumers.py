"""Contains the Django Channels Consumers that handle the reception/sending of channels messages."""
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from manager.settings import PROCESS_CONNECTION_PASS


class SubscriptionConsumer(AsyncJsonWebsocketConsumer):
    """Consumer that handles incoming websocket messages."""

    async def connect(self):
        """Handle connection, rejects connection if no authenticated user."""
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
        """Handle disconnection."""
        # Leave telemetry_stream group
        for telemetry_stream in self.stream_group_names:
            await self._leave_group(*telemetry_stream)

    async def receive_json(self, message):
        """Handle a received message.

        Calls handle_subscription_message() if the message is intended to join or leave a group.
        Otherwise handle_data_message() is called

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json
        """
        if 'option' in message:
            await self.handle_subscription_message(message)
        else:
            await self.handle_data_message(message)

    async def handle_subscription_message(self, message):
        """Handle a subscription/unsubscription message.

        Makes the consumer join or leave a group based on the data from the message

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json.

        The expected format of the message is as follows:
        {
            option: 'subscribe'/'unsubscribe'
            category: 'event'/'telemetry'/'cmd',
            csc: 'ScriptQueue',
            salindex: 1,
            stream: 'stream1',
        }

        """
        option = message['option']
        category = message['category']

        if option == 'subscribe':
            # Subscribe and send confirmation
            csc = message['csc']
            salindex = message['salindex']
            stream = message['stream']
            await self._join_group(category, csc, str(salindex), stream)
            await self.send_json({
                'data': 'Successfully subscribed to %s-%s-%s-%s' % (category, csc, salindex, stream)
            })
            return

        if option == 'unsubscribe':
            # Unsubscribe and send confirmation
            csc = message['csc']
            salindex = message['salindex']
            stream = message['stream']
            await self._leave_group(category, csc, str(salindex), stream)
            await self.send_json({
                'data': 'Successfully unsubscribed to %s-%s-%s-%s' % (category, csc, salindex, stream)
            })
            return

    async def handle_data_message(self, message):
        """Handle a data message.

        Sends the message to the corresponding groups based on the data of the message.

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json.

        The expected format of the message for a telemetry or an event is as follows:
        {
            category: 'event'/'telemetry',
            data: [{
                csc: 'ScriptQueue',
                salindex: 1,
                data: {
                    stream1: {....},
                    stream2: {....},
                }
            }]
        }

        The expected format of the message for a command is as follows:
        {
            category: 'cmd',
            data: [{
                csc: 'ScriptQueue',
                salindex: 1,
                data: {
                    cmd: 'CommandPath',
                    params: {
                        'param1': 'value1',
                        'param2': 'value2',
                        ...
                    },
                }
            }]
        }

        """
        data = message['data']
        category = message['category']
        user = self.scope['user']
        if category == 'cmd' and not user.has_perm('api.command.execute_command'):
            await self.send_json({
                'data': 'Command not sent. User does not have permissions to send commands.'
            })
            return

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

    async def _join_group(self, category, csc, salindex, stream):
        """Join a group in order to receive messages from it.

        Parameters
        ----------
        category: `string`
            category of the message, it can be either: 'cmd', 'event' or 'telemetry'
        csc : `string`
            CSC associated to the message. E.g. 'ScriptQueue'
        salindex : `string`
            SAL index of the instance of the CSC associated to the message. E.g. '1'
        stream : `string`
            Stream to subscribe to. E.g. 'stream_1'
        """
        key = '-'.join([category, csc, salindex, stream])
        if [category, csc, salindex, stream] in self.stream_group_names:
            return
        self.stream_group_names.append([category, csc, salindex, stream])
        await self.channel_layer.group_add(
            key,
            self.channel_name
        )

    async def _leave_group(self, category, csc, salindex, stream):
        """Leave a group in order to receive messages from it.

        Parameters
        ----------
        category: `string`
            category of the message, it can be either: 'cmd', 'event' or 'telemetry'
        csc : `string`
            CSC associated to the message. E.g. 'ScriptQueue'
        salindex : `string`
            SAL index of the instance of the CSC associated to the message. E.g. '1'
        stream : `string`
            Stream to subscribe to. E.g. 'stream_1'
        """
        key = '-'.join([category, csc, salindex, stream])
        if [category, csc, salindex, stream] in self.stream_group_names:
            self.stream_group_names.remove([category, csc, salindex, stream])
        await self.channel_layer.group_discard(
            key,
            self.channel_name
        )

    async def subscription_data(self, message):
        """
        Send a message to all the instances of a consumer that have joined the group.

        It is used to send messages associated to subscriptions to all the groups of a particular category

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json
        """
        data = message['data']
        category = message['category']
        salindex = message['salindex']
        csc = message['csc']

        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'category': category,
            'data': [{
                'csc': csc,
                'salindex': salindex,
                'data': data,
            }]
        }))

    async def subscription_all_data(self, message):
        """
        Send a message to all the instances of a consumer that have joined the group.

        It is used to send messages associated to subscriptions to all the groups of a particular category

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json
        """
        data = message['data']
        category = message['category']

        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'category': category,
            'data': data
        }))
