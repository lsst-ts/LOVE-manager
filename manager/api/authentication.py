import rest_framework.authentication
from rest_framework.exceptions import AuthenticationFailed
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from api.models import Token


class TokenAuthentication(rest_framework.authentication.TokenAuthentication):
    """ Custom authentication class. Created in order to use our custom Token model """

    model = Token
    """ Token model """


class ExpiringTokenAuthentication(rest_framework.authentication.TokenAuthentication):
    """ Custom authentication class. Created in order to:
    1. Use our custom Token model; and
    2. Remove tokens if they are expired
    """

    model = Token
    """ Token model """

    def authenticate_credentials(self, key):
        """ Checks if a provided token is valid or not.
        If it is valid, the user and token are returned, if not, an AuthenticationFailed exception is raised

        Args:
            key (string): the token key to validate_token

        Returns:
            (User, Token): The corresponding user and token objects
        """
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid Token")

        if not token.user.is_active:
            raise AuthenticationFailed("User is not active")

        is_expired, token = ExpiringTokenAuthentication.token_expire_handler(token)
        if is_expired:
            raise AuthenticationFailed("The Token is expired")

        return (token.user, token)

    @classmethod
    def token_expire_handler(self, token):
        """ Checks if a given token is expired or not, if it is the Token is deleted

        Args:
            token (Token): the token object to check expiration

        Returns:
            (boolean, Token): True if it is expired, False if not; and the Token object
        """
        is_expired = self.is_token_expired(token)
        if is_expired:
            token.delete()
            # token = Token.objects.create(user=token.user) # This line allows creation of a new token after expiration
        return is_expired, token

    @classmethod
    def is_token_expired(self, token):
        """ Checks if a given token is expired or not

        Args:
            token (Token): the token object to check expiration

        Returns:
            boolean: True if it is expired, False if not
        """
        return self.expires_in(token) < timedelta(seconds=0)

    @classmethod
    def expires_in(self, token):
        """ Returns the remaining time of a given token

        Args:
            token (Token): the token object to check remianing time

        Returns:
            (int): the number of remaining seconds for the token
        """
        time_elapsed = timezone.now() - token.created
        left_time = timedelta(days=settings.TOKEN_EXPIRED_AFTER_DAYS) - time_elapsed
        return left_time
