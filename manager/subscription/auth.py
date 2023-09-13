# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed for Inria Chile.
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


"""Defines the TokenAuthMiddleware used for token authentication."""
import urllib.parse as urlparse
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.db import database_sync_to_async
from api.models import Token


@database_sync_to_async
def get_user(token):
    """Get the user associated to a given token.

    Parameters
    ----------
    token: `string`
        The token used for authentication.

    Returns
    -------
    `User`
        The User associated to the token, or AnonymousUser if the token was not found.
    """
    if not token:
        return AnonymousUser()

    token_obj = Token.objects.filter(key=token).first()
    if token_obj:
        return token_obj.user
    else:
        return AnonymousUser()


class TokenAuthMiddleware:
    """Custom middleware to use a token for user authentication on websockets connections."""

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        """Verify if the user is authenticated.

        Parameters
        ----------
        scope: `dict`
            dictionary defining parameters for the authentication
        """
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    """Class that builds the instance of the TokenAuthMiddleware."""

    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        """Verify if the user is authenticated.

        Parameters
        ----------
        scope: `dict`
            dictionary defining parameters for the authentication
        """
        close_old_connections()
        query_string = self.scope.get("query_string").decode()
        data = urlparse.parse_qs(query_string)
        self.scope["user"] = await get_user(
            data["token"][0] if "token" in data else None
        )
        self.scope["password"] = data["password"][0] if "password" in data else None
        return await self.inner(self.scope, receive, send)
