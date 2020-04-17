"""Defines the serializer used by the REST API exposed by this app ('api')."""
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from django.contrib.auth.models import User
from manager.utils import tai_utc_offset


class UserSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = User
        """The model class to serialize"""

        fields = ("username", "email")
        """The fields of the model class to serialize"""


class UserPermissionsSerializer(serializers.Serializer):
    """Custom Serializer for user permissions."""

    execute_commands = serializers.SerializerMethodField("can_execute_commands")

    def can_execute_commands(self, user) -> bool:
        """Define wether or not the given user has permissions to execute commands.

        Params
        ------
        user: User
            The User object

        Returns
        -------
        Bool
            True if the user can execute commands, False if not.
        """
        return user.has_perm("api.command.execute_command")


class TokenSerializer(serializers.Serializer):
    """Custom Serializer for responses to validate and get token requests."""

    user = UserSerializer()

    token = serializers.SerializerMethodField("get_token")

    permissions = serializers.SerializerMethodField("get_permissions")

    tai_to_utc = serializers.SerializerMethodField("get_tai_to_utc")

    @swagger_serializer_method(serializer_or_field=UserPermissionsSerializer)
    def get_permissions(self, token):
        """Return user permissions serialized as a dictionary with permission names as keys and bools as values.

        Params
        ------
        token: Token
            The Token object

        Returns
        -------
        Bool
            True if the user can execute commands, False if not.
        """
        return UserPermissionsSerializer(token.user).data

    def get_token(self, token):
        """Return the token key.

        Params
        ------
        token: Token
            The Token object

        Returns
        -------
        String
            The token key
        """
        return token.key

    def get_tai_to_utc(self, token) -> float:
        """Return the difference in seconds between TAI and UTC Timestamps.

        Params
        ------
        token: Token
            The Token object

        Returns
        -------
        Int
            The number of seconds of difference between TAI and UTC times
        """
        return tai_utc_offset()
