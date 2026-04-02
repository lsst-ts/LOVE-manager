# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or at
# your option any later version.
#
# This program is distributed in the hope that it will be useful,but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""Background tasks for the subscription app.

Contains the heartbeat dispatch and commander heartbeat query logic
that run as daemon threads, fully independent of WebSocket consumers.
Both loops check ``settings.HEARTBEAT_QUERY_COMMANDER`` on every
iteration so that ``@override_settings`` in tests takes effect
dynamically.
"""

import datetime
import json
import os
import threading
import time

import requests
from asgiref.sync import async_to_sync

# ---------------------------------------------------------------------------
# Shared heartbeat data (thread-safe)
# ---------------------------------------------------------------------------

_heartbeat_data = {}
_lock = threading.Lock()


def set_heartbeat_timestamp(source, timestamp):
    """Set a given timestamp as the heartbeat for a given source.

    Thread-safe — can be called from any thread.

    Parameters
    ----------
    source : `str`
        Name of the component, e.g. ``"Commander"``, ``"Manager"``.
    timestamp : `float`
        Unix timestamp of the heartbeat.
    """
    with _lock:
        _heartbeat_data[source] = timestamp


def get_heartbeat_data():
    """Return a snapshot of the current heartbeat data.

    Returns
    -------
    `dict`
        Copy of the ``{source: timestamp}`` dictionary.
    """
    with _lock:
        return dict(_heartbeat_data)


def clear_heartbeat_data():
    """Clear all stored heartbeat timestamps."""
    with _lock:
        _heartbeat_data.clear()


# ---------------------------------------------------------------------------
# Background loops
# ---------------------------------------------------------------------------


def _query_commander_loop():
    """Poll the LOVE-Commander ``/heartbeat`` endpoint every 3 seconds.

    Runs in a daemon thread.  Skips the HTTP request when
    ``settings.HEARTBEAT_QUERY_COMMANDER`` is ``False``.
    """
    from django.conf import settings

    heartbeat_url = (
        "http://"
        + os.environ.get("COMMANDER_HOSTNAME", "localhost")
        + ":"
        + os.environ.get("COMMANDER_PORT", "8000")
        + "/heartbeat"
    )

    while True:
        try:
            if settings.HEARTBEAT_QUERY_COMMANDER:
                resp = requests.get(heartbeat_url, timeout=5)
                timestamp = resp.json()["timestamp"]
                set_heartbeat_timestamp("Commander", timestamp)
        except Exception as e:
            print(e, flush=True)
        time.sleep(3)


def _dispatch_heartbeats_loop():
    """Dispatch aggregated heartbeats to the Channels layer every 3 seconds.

    Runs in a daemon thread.  Uses ``asgiref.async_to_sync`` to call
    ``channel_layer.group_send`` from synchronous code.  Skips
    dispatching when ``settings.HEARTBEAT_QUERY_COMMANDER`` is ``False``.
    """
    from channels.layers import get_channel_layer
    from django.conf import settings

    channel_layer = get_channel_layer()

    while True:
        try:
            if settings.HEARTBEAT_QUERY_COMMANDER:
                set_heartbeat_timestamp("Manager", datetime.datetime.now().timestamp())
                data = json.dumps(
                    {
                        "category": "heartbeat",
                        "data": [
                            {
                                "csc": source,
                                "salindex": 0,
                                "data": {"timestamp": ts},
                            }
                            for source, ts in get_heartbeat_data().items()
                        ],
                        "subscription": "heartbeat",
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    "heartbeat-manager-0-stream",
                    {"type": "send_heartbeat", "data": data},
                )
        except Exception as e:
            print(e, flush=True)
        time.sleep(3)


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------

_dispatch_thread = None
_commander_thread = None
_started = False


def start_heartbeat_tasks():
    """Start both background daemon threads (idempotent).

    Safe to call multiple times — only the first call actually
    spawns threads.  Both threads are daemon threads and will
    be terminated automatically when the main process exits.
    """
    global _dispatch_thread, _commander_thread, _started
    if _started:
        return
    _started = True

    _commander_thread = threading.Thread(
        target=_query_commander_loop,
        daemon=True,
        name="commander-heartbeat-query",
    )
    _dispatch_thread = threading.Thread(
        target=_dispatch_heartbeats_loop,
        daemon=True,
        name="heartbeat-dispatch",
    )
    _commander_thread.start()
    _dispatch_thread.start()
