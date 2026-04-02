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


"""Django apps configuration for the subscription app."""

from django.apps import AppConfig


class SubscriptionConfig(AppConfig):
    """General Subscription config class."""

    name = "subscription"
    """The name of the app."""

    def ready(self):
        """Start background heartbeat tasks when the app is ready.

        Spawns daemon threads for the commander heartbeat query
        and the heartbeat dispatch loop.  The threads themselves
        check ``settings.HEARTBEAT_QUERY_COMMANDER`` on every
        iteration, so the setting can be toggled at runtime
        (e.g. via ``@override_settings`` in tests).
        """
        from subscription.tasks import start_heartbeat_tasks

        start_heartbeat_tasks()
