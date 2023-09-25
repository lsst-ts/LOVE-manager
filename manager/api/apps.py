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


"""Django apps configuration for the api app."""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """General App config class. Currently defines the name of the app."""

    name = "api"
    """The name of the app (`string`)"""

    def ready(self):
        """Import the signals module when the application is ready."""
        import api.signals  # noqa: F401
