"""Contains the Django Channels Consumers that handle the reception/sending of channels messages."""
import json
import random
import asyncio
import datetime
from astropy.time import Time
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from manager import utils
from subscription.heartbeat_manager import HeartbeatManager


class SubscriptionConsumer(AsyncJsonWebsocketConsumer):
    """Consumer that handles incoming websocket messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_connection = asyncio.Future()
        self.heartbeat_manager = HeartbeatManager()
        self.heartbeat_manager.initialize()

    async def connect(self):
        """Handle connection, rejects connection if no authenticated user."""
        self.stream_group_names = []
        # Reject connection if no authenticated user:
        if self.scope["user"].is_anonymous:
            if (
                self.scope["password"]
                and self.scope["password"] == settings.PROCESS_CONNECTION_PASS
            ):
                await self.accept()
                self.first_connection.set_result(True)
            else:
                await self.close()
        else:
            await self.accept()
            self.first_connection.set_result(True)
            url_token = self.scope["query_string"][6:].decode()
            personal_group_name = "token-{}".format(url_token)
            await self.channel_layer.group_add(personal_group_name, self.channel_name)

    async def disconnect(self, close_code):
        """Handle disconnection."""
        await asyncio.gather(
            *[self._leave_group(*stream) for stream in self.stream_group_names]
        )

    async def receive_json(self, message):
        """Handle a received message.

        Calls handle_subscription_message() if the message is intended to join or leave a group.
        Otherwise handle_data_message() is called

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json
        """
        manager_rcv = (
            Time.now().tai.datetime.timestamp() if settings.TRACE_TIMESTAMPS else None
        )
        if "option" in message:
            await self.handle_subscription_message(message)
        elif "action" in message:
            await self.handle_action_message(message)
        elif "heartbeat" in message:
            await self.handle_heartbeat_message(message)
        else:
            await self.handle_data_message(message, manager_rcv)

    async def handle_subscription_message(self, message):
        """Handle a subscription/unsubscription message.

        Makes the consumer join or leave a group based on the data from the message

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json. The expected format of the message is as follows:

            .. code-block:: json

                {
                    "option": "subscribe/unsubscribe",
                    "category": "event/telemetry",
                    "csc": "ScriptQueue",
                    "salindex": 1,
                    "stream": "stream1",
                }

        """
        option = message["option"]
        category = message["category"]

        if option == "subscribe":
            # Subscribe and send confirmation
            csc = message["csc"]
            salindex = message["salindex"]
            stream = message["stream"]
            await self._join_group(category, csc, str(salindex), stream)
            await self.send_json(
                {
                    "data": "Successfully subscribed to %s-%s-%s-%s"
                    % (category, csc, salindex, stream)
                }
            )

        elif option == "unsubscribe":
            # Unsubscribe and send confirmation
            csc = message["csc"]
            salindex = message["salindex"]
            stream = message["stream"]
            await self._leave_group(category, csc, str(salindex), stream)
            await self.send_json(
                {
                    "data": "Successfully unsubscribed to %s-%s-%s-%s"
                    % (category, csc, salindex, stream)
                }
            )

    async def handle_action_message(self, message):
        """Handle an action message.

        Receives an action message and reacts according to each different action.

        Currently supported actions: 
        - get_time_data: sends a message with the time_data and passes though a request_time received with the message.

            - Expected input message:
            .. code-block:: json

                {
                    "action": "get_time_data",
                    "request_time": "<timestamp with the request time, e.g. 123243423.123>"
                }

            - Message sent (output):
            .. code-block:: json

                {
                    "time_data": {
                        "utc": "<current time in UTC scale as a unix timestamp (seconds)>",
                        "tai": "<current time in UTC scale as a unix timestamp (seconds)>",
                        "mjd": "<current time as a modified julian date>",
                        "sidereal_summit": "<current time as a sidereal_time w/respect to the summit location (hourangles)>",
                        "sidereal_summit": "<current time as a sidereal_time w/respect to Greenwich location (hourangles)>",
                        "tai_to_utc": "<The number of seconds of difference between TAI and UTC times (seconds)>",
                    },
                    "request_time": "<timestamp with the request time, e.g. 123243423.123>"
                }

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json. The expected format of the message is as follows:

            .. code-block:: json

                {
                    "action": "<string defining the action>"
                }

        """
        if message["action"] == "get_time_data":
            request_time = message["request_time"]
            time_data = utils.get_times()
            await self.send_json(
                {"time_data": time_data, "request_time": request_time,}
            )

    async def handle_heartbeat_message(self, message):
        """Handle a heartbeat message.

        Receives a heartbeat message and sets it in the heartbeat manager.

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json. The expected format of the message is as follows:

            .. code-block:: json

                {
                    "heartbeat": "<component name>",
                    "timestamp": "<timestamp of the last heartbeat> (optional)"
                }
        """
        timestamp = (
            message["timestamp"]
            if "timestamp" in message
            else datetime.datetime.now().timestamp()
        )
        self.heartbeat_manager.set_heartbeat_timestamp(message["heartbeat"], timestamp)

    async def handle_data_message(self, message, manager_rcv):
        """Handle a data message.

        Sends the message to the corresponding groups based on the data of the message.

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json.
            The expected format of the message for a telemetry or an event is as follows:

            .. code-block:: json

                {
                    "category": "event/telemetry",
                    "data": [{
                        "csc": "ScriptQueue",
                        "salindex": 1,
                        "data": {
                            "stream1": {
                                "<key11>": "<value11>",
                                "<key12>": "<value12>",
                            },
                            "stream2": {
                                "<key21>": "<value21>",
                                "<key22>": "<value22>",
                            },
                        }
                    }]
                }
        """
        data = message["data"]
        category = message["category"]
        user = self.scope["user"]
        producer_snd = message["producer_snd"] if "producer_snd" in message else None

        # Store pairs of group, message to send:
        to_send = []
        tracing = {}

        # Iterate over all stream groups
        for csc_message in data:
            csc = csc_message["csc"]
            salindex = csc_message["salindex"]
            data_csc = csc_message["data"]
            csc_message["data"] = data_csc
            streams = data_csc.keys()
            streams_data = {}

            # Individual groups for each stream
            for stream in streams:
                sub_category = category
                msg_type = "subscription_data"
                group_name = "-".join([sub_category, csc, str(salindex), stream])
                msg = {
                    "type": msg_type,
                    "category": category,
                    "csc": csc,
                    "salindex": salindex,
                    "data": {stream: data_csc[stream]},
                    "subscription": group_name,
                }

                to_send.append({"group": group_name, "message": msg})
                streams_data[stream] = data_csc[stream]

            # Higher level groups for all streams of a category-csc-salindex
            group_name = "-".join([category, csc, str(salindex), "all"])
            msg = {
                "type": "subscription_data",
                "category": category,
                "csc": csc,
                "salindex": salindex,
                "data": {csc: streams_data},
                "subscription": group_name,
            }
            to_send.append({"group": group_name, "message": msg})

        # Top level for "all" subscriptions of the same category
        group_name = "{}-all-all-all".format(category)
        msg = {"type": "subscription_all_data", "category": category, "data": data}
        to_send.append({"group": group_name, "message": msg})

        if settings.TRACE_TIMESTAMPS:
            tracing = {
                "producer_snd": producer_snd,
                "manager_rcv_from_producer": manager_rcv,
                "manager_snd_to_group": Time.now().tai.datetime.timestamp(),
            }
            for group_msg in to_send:
                group_msg["message"]["tracing"] = tracing

        # print("to_send: ", to_send, flush=True)

        # Send all group-message pairs concurrently:
        await asyncio.gather(
            *[self.channel_layer.group_send(**group_msg) for group_msg in to_send]
        )

    async def _join_group(self, category, csc, salindex, stream):
        """Join a group in order to receive messages from it.

        Parameters
        ----------
        category: `string`
            category of the message, it can be either: 'event' or 'telemetry'
        csc : `string`
            CSC associated to the message. E.g. 'ScriptQueue'
        salindex : `string`
            SAL index of the instance of the CSC associated to the message. E.g. '1'
        stream : `string`
            Stream to subscribe to. E.g. 'stream_1'
        """
        key = "-".join([category, csc, salindex, stream])
        if [category, csc, salindex, stream] not in self.stream_group_names:
            self.stream_group_names.append([category, csc, salindex, stream])
        await self.channel_layer.group_add(key, self.channel_name)

        # If subscribing to an event, send the initial_state
        if category == "event":
            await self.channel_layer.group_send(
                "initial_state-all-all-all",
                {
                    "type": "subscription_all_data",
                    "category": "initial_state",
                    "data": [
                        {
                            "csc": csc,
                            "salindex": int(salindex)
                            if salindex != "all"
                            else salindex,
                            "data": {"event_name": stream},
                        }
                    ],
                },
            )

    async def _leave_group(self, category, csc, salindex, stream):

        """Leave a group in order to receive messages from it.

        Parameters
        ----------
        category: `string`
            category of the message, it can be either: 'event' or 'telemetry'
        csc : `string`
            CSC associated to the message. E.g. 'ScriptQueue'
        salindex : `string`
            SAL index of the instance of the CSC associated to the message. E.g. '1'
        stream : `string`
            Stream to subscribe to. E.g. 'stream_1'
        """
        key = "-".join([category, csc, salindex, stream])
        if [category, csc, salindex, stream] in self.stream_group_names:
            self.stream_group_names.remove([category, csc, salindex, stream])
        await self.channel_layer.group_discard(key, self.channel_name)

    async def subscription_data(self, message):
        """
        Send a message to all the instances of a consumer that have joined the group.

        It is used to send messages associated to subscriptions to all the groups of a particular category

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json
        """
        if settings.TRACE_TIMESTAMPS:
            manager_rcv_from_group = Time.now().tai.datetime.timestamp()
            tracing = message["tracing"] if "tracing" in message else {}

        data = message["data"]
        category = message["category"]
        salindex = message["salindex"]
        csc = message["csc"]
        subscription = message["subscription"]
        msg = {
            "category": category,
            "data": [{"csc": csc, "salindex": salindex, "data": data}],
            "subscription": subscription,
        }

        if settings.TRACE_TIMESTAMPS:
            tracing["manager_rcv_from_group"] = manager_rcv_from_group
            tracing["manager_snd_to_client"] = Time.now().tai.datetime.timestamp()
            msg["tracing"] = tracing

        # Send data to WebSocket
        await self.send(text_data=json.dumps(msg))

    async def subscription_all_data(self, message):
        """
        Send a message to all the instances of a consumer that have joined the group.

        It is used to send messages associated to subscriptions to all the groups of a particular category

        Parameters
        ----------
        message: `dict`
            dictionary containing the message parsed as json
        """
        if settings.TRACE_TIMESTAMPS:
            manager_rcv_from_group = Time.now().tai.datetime.timestamp()
            tracing = message["tracing"] if "tracing" in message else {}

        data = message["data"]
        category = message["category"]
        msg = {
            "category": category,
            "data": data,
            "subscription": "{}-all-all-all".format(category),
        }

        if settings.TRACE_TIMESTAMPS:
            tracing["manager_rcv_from_group"] = manager_rcv_from_group
            tracing["manager_snd_to_client"] = Time.now().tai.datetime.timestamp()
            msg["tracing"] = tracing

        # Send data to WebSocket
        await self.send(text_data=json.dumps(msg))

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
        await self.send(text_data=message["data"])

    async def logout(self, message):
        """Closes the connection.

        Parameters
        ----------
        message: `string`
            message received, it is part of the API (as this function is called by a message reception)
            but it is not used
        """
        await self.close()
