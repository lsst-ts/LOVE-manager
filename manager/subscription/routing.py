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


"""Define the rules for routing of channels messages (websockets) in the subscirption application."""
from django.conf.urls import url
from subscription.auth import TokenAuthMiddleware
from .consumers import SubscriptionConsumer
from django.conf import settings


URL_PREFIX = settings.FORCE_SCRIPT_NAME[1:] + "/" if settings.FORCE_SCRIPT_NAME else ""

websocket_urlpatterns = [
    url(
        rf"^{URL_PREFIX}manager(.*?)/ws/subscription/?$",
        TokenAuthMiddleware(SubscriptionConsumer.as_asgi()),
    ),
]
"""List of url patterns that match a URL to a Consumer (in this case only 1)."""
