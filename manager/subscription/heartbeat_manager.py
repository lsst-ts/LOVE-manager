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


"""Backward-compatible façade over :mod:`subscription.tasks`.

All heartbeat logic (commander query and dispatch) now runs in
background daemon threads started at Django startup.  This module
preserves the public API that existing code and tests rely on
(``set_heartbeat_timestamp``, ``reset``, ``stop``).
"""

from subscription import tasks


class HeartbeatManager:
    """Manages the heartbeats of LOVE software components.

    Both the LOVE-Commander heartbeat query and the periodic
    heartbeat dispatch run as background daemon threads started
    by :meth:`SubscriptionConfig.ready` (see
    :mod:`subscription.tasks`).  This class provides a
    backward-compatible interface for setting timestamps and
    for test lifecycle helpers (``reset`` / ``stop``).
    """

    class __HeartbeatManager:
        @classmethod
        def set_heartbeat_timestamp(cls, source, timestamp):
            """Set a given timestamp as the heartbeat for a given source.

            Parameters
            ----------
            source : `str`
                Name of the component, e.g. ``"Commander"``.
            timestamp : `float`
                Unix timestamp of the heartbeat.
            """
            tasks.set_heartbeat_timestamp(source, timestamp)

        @classmethod
        async def reset(cls):
            """Clear all stored heartbeat data.

            The background threads keep running — they will pick up
            the empty state on their next iteration.
            """
            tasks.clear_heartbeat_data()

        @classmethod
        async def stop(cls):
            """No-op kept for backward compatibility.

            The background threads are daemon threads and will be
            terminated automatically when the main process exits.
            """
            pass

    instance = None

    def __init__(self):
        if not HeartbeatManager.instance:
            HeartbeatManager.instance = HeartbeatManager.__HeartbeatManager()

    def __getattr__(self, name):
        return getattr(self.instance, name)
