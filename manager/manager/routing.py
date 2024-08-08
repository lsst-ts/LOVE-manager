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


"""Defines the rules for routing of
channels messages (websockets) in the whole project."""
import subscription.routing
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from subscription.auth import TokenAuthMiddleware

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        "websocket": TokenAuthMiddleware(
            URLRouter(subscription.routing.websocket_urlpatterns)
        ),
    }
)
