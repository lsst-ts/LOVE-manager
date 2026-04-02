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

import os
import sys

from django.apps import AppConfig
from django.conf import settings

from subscription.tasks import HeatbeatManagerCommander


class SubscriptionConfig(AppConfig):
    """General Subscription config class."""

    name = "subscription"
    """The name of the app."""

    def ready(self):
        """Start background heartbeat tasks when the app is ready.
        Spawns daemon threads for the commander heartbeat query
        and the heartbeat dispatch loop.

        The heartbeat tasks are only started in server processes, not
        in management commands.  This is determined by inspecting
        ``sys.argv`` and environment variables to detect the context in
        which the app is running. Additionally, the heartbeat tasks are
        only started if ``settings.HEARTBEAT_QUERY_COMMANDER`` is ``True``.
        """
        if self._is_server_process() and settings.HEARTBEAT_QUERY_COMMANDER:
            HeatbeatManagerCommander.start_heartbeat_tasks()

    # ------------------------------------------------------------------
    @staticmethod
    def _is_server_process():
        """Return ``True`` only when running inside a real server process.

        * Returns ``False`` for management commands like ``migrate``,
          ``loaddata``, ``makemigrations``, etc.
        * For Django's ``runserver`` with auto-reload, returns ``True``
          only in the reloader's *child* process (``RUN_MAIN=true``).
        * For ASGI servers launched via ``python -m uvicorn …`` or
          ``daphne …``, returns ``True``.
        """
        # Detect Django management commands by inspecting sys.argv.
        # manage.py <command> …  →  sys.argv = ['manage.py', '<command>', …]
        _server_commands = {"runserver", "runserver_plus"}
        if len(sys.argv) >= 2 and sys.argv[0].endswith("manage.py"):
            command = sys.argv[1]
            if command not in _server_commands:
                # A non-server management command (migrate, loaddata, …)
                return False
            # Django runserver: only proceed in the reloader child.
            return os.environ.get("RUN_MAIN") == "true"

        # Not launched via manage.py → assume an ASGI server (uvicorn,
        # daphne, etc.) where we always want the tasks.
        return True
