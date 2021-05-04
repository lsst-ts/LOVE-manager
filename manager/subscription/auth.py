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
