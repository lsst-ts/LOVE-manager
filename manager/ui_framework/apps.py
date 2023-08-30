# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile and Vera C. Rubin Observatory Telescope
# and Site Systems.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or at your option any later version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""Django apps configuration for the ui_framework app."""
from django.apps import AppConfig


class UiFrameworkConfig(AppConfig):
    """General App config class. Currently defines the name of the app."""

    name = "ui_framework"
    """The name of the app."""

    def ready(self):
        """Import signals module when app is ready"""
        import ui_framework.signals  # noqa F401
