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


"""Define the rules for routing
of channels messages (websockets) in the subscription application."""

from django.urls import re_path

from .consumers import SubscriptionConsumer

websocket_urlpatterns = [
    re_path(
        r"^manager(.*?)/ws/subscription/?$",
        SubscriptionConsumer.as_asgi(),
    ),
]
"""List of url patterns that match
a URL to a Consumer (in this case only 1)."""
