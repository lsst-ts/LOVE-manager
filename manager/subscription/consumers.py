"""Contains the Django Channels Consumers that handle the reception/sending of channels messages."""
import json
import random
import asyncio
import datetime
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from manager.settings import PROCESS_CONNECTION_PASS
from subscription.heartbeat_manager import HeartbeatManager


class SubscriptionConsumer(AsyncJsonWebsocketConsumer):
    """Consumer that handles incoming websocket messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_connection = asyncio.Future()
        HeartbeatManager.initialize()

    async def connect(self):
        """Handle connection, rejects connection if no authenticated user."""
        self.stream_group_names = []
        self.pending_commands = set()
        # Reject connection if no authenticated user:
        if self.scope['user'].is_anonymous:
            if self.scope['password'] and self.scope['password'] == PROCESS_CONNECTION_PASS:
                await self.accept()
                self.first_connection.set_result(True)
            else:
                await self.close()
        else:
            await self.accept()
            self.first_connection.set_result(True)

    async def disconnect(self, close_code):
        """Handle disconnection."""
        # Leave telemetry_stream group
        self.pending_commands = set()
        for telemetry_stream in self.stream_group_names:
            await self._leave_group(*telemetry_stream)

    async def send_heartbeat(self, message):
        """
        Send a heartbeat to all the instances of a consumer that have joined the heartbeat-manager-0-stream.

        It is used to send messages associated to subscriptions to all the groups of a particular category

        Parameters
        ----------
        message: `string`
            dictionary containing the heartbeat message
        """
        # Send data to WebSocket
        await self.send(text_data=message['data'])

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
            The expected format of the message for a command/ack is as follows:
            {
                category: 'cmd'/'ack',
                data: [{
                    csc: 'ScriptQueue',
                    salindex: 1,
                    data: {
                        stream: {
                            cmd: 'CommandPath',
                            params: {
                                'param1': 'value1',
                                'param2': 'value2',
                                ...
                            },
                        }
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
                sub_category = category
                msg_type = "subscription_data"
                group_name = '-'.join([sub_category, csc, str(salindex), stream])
                if category == "cmd":
                    await self._join_group("cmd_acks", "all", "all", "all")
                    cmd_id = random.getrandbits(128)
                    if 'cmd_id' in data_csc[stream]:
                        cmd_id = data_csc[stream]['cmd_id']
                    self.pending_commands.add(cmd_id)
                    print('New Command', self.pending_commands)
                if category == "ack":
                    print('New Ack', self.pending_commands, message)
                    sub_category = "cmd"  # Use sub group from cmds
                    msg_type = "subscription_ack"
                    group_name = 'cmd_acks-all-all-all'
                await self.channel_layer.group_send(
                    group_name,
                    {
                        'type': msg_type,
                        'category': category,
                        'csc': csc,
                        'salindex': salindex,
                        'data': {stream: data_csc[stream]},
                        'subscription': group_name
                    }
                )
                streams_data[stream] = data_csc[stream]
            await self.channel_layer.group_send(
                '-'.join([category, csc, str(salindex), 'all']),
                {
                    'type': 'subscription_data',
                    'category': category,
                    'csc': csc,
                    'salindex': salindex,
                    'data': {csc: streams_data},
                    'subscription': '-'.join([category, csc, str(salindex), 'all'])
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

        # If subscribing to an event, send the initial_state
        if category == 'event':
            await self.channel_layer.group_send(
                'initial_state-all-all-all',
                {
                    'type': 'subscription_all_data',
                    'category': 'initial_state',
                    'data': [{
                        "csc": csc,
                        "salindex": int(salindex) if salindex != 'all' else salindex,
                        "data": {
                            "event_name": stream
                        }
                    }]
                }
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
        subscription = message['subscription']

        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'category': category,
            'data': [{
                'csc': csc,
                'salindex': salindex,
                'data': data
            }],
            'subscription': subscription
        }))

    async def subscription_ack(self, message):
        """
        Send a message to all the instances of a consumer that have joined the group.

        It is used to send ack messages associated to subscriptions to all the groups of a particular category.
        Only sends messages to those groups with a corresponding pending cmd.

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json
        """
        data = message['data']
        category = message['category']
        salindex = message['salindex']
        csc = message['csc']
        for stream in data:
            print('stream', data[stream])
            cmd_id = data[stream]['cmd_id']
            if cmd_id in self.pending_commands:
                self.pending_commands.discard(cmd_id)
                await self.send(text_data=json.dumps({
                    'category': category,
                    'data': [{
                        'csc': csc,
                        'salindex': salindex,
                        'data': data,
                    }],
                    'subscription': 'cmd_acks-all-all-all'
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
        # subscription = '{}-all-all-all'.format(category)

        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'category': category,
            'data': data,
            'subscription': '{}-all-all-all'.format(category)
        }))
