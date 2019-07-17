"""Defines the TokenAuthMiddleware used for token authentication."""
import urllib.parse as urlparse
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from api.models import Token


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
        query_string = scope.get('query_string').decode()
        data = urlparse.parse_qs(query_string)
        token_key = None
        scope['user'] = AnonymousUser()
        scope['password'] = False

        if 'token' in data:
            token_key = data['token'][0]
            token = Token.objects.filter(key=token_key).first()
            if token is not None:
                scope['user'] = token.user

        if 'password' in data:
            password = data['password'][0]
            if password is not None:
                scope['password'] = password

        close_old_connections()
        return self.inner(scope)
