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


"""Defines custom authentication classes."""
from datetime import timedelta

import rest_framework.authentication
from api.models import Token
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed


class TokenAuthentication(rest_framework.authentication.TokenAuthentication):
    """Custom authentication class. Created in order
    to use our custom Token model."""

    model = Token
    """django.model: defines the Token model associated to this class"""


class ExpiringTokenAuthentication(rest_framework.authentication.TokenAuthentication):
    """Custom authentication class.

    Created in order to:
    1. Use our custom Token model; and
    2. Remove tokens if they are expired
    """

    model = Token
    """django.model: defines the Token model associated to this class"""

    def authenticate_credentials(self, key):
        """Check if a provided token is valid or not.

        If it is valid, the user and token are returned,
        if not, an AuthenticationFailed exception is raised.

        Params
        ------
        key: string
            the token key to validate_token

        Returns
        -------
        User, Token
            The corresponding user and token objects
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
    def token_expire_handler(cls, token):
        """Check if a given token is expired or not,
        if it is the Token is deleted.

        Params
        ------
        token: Token object
            The token object to check expiration

        Returns
        -------
        boolean, Token:
            True if it is expired, False if not; and the Token object
        """
        is_expired = cls.is_token_expired(token)
        if is_expired:
            token.delete()
        return is_expired, token

    @classmethod
    def is_token_expired(cls, token):
        """Check if a given token is expired or not.

        Params
        ------
        token: Token
            The token object to check expiration

        Returns
        -------
        boolean
            True if it is expired, False if not
        """
        return cls.expires_in(token) < timedelta(seconds=0)

    @classmethod
    def expires_in(cls, token):
        """Return the remaining time of a given token.

        Params
        ------
        token: Token
            The token object to check remianing time

        Returns
        -------
        int
            The number of remaining seconds for the token
        """
        time_elapsed = timezone.now() - token.created
        left_time = timedelta(days=settings.TOKEN_EXPIRED_AFTER_DAYS) - time_elapsed
        return left_time
