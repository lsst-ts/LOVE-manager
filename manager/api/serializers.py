"""Defines the serializer used by the REST API exposed by this app ('api')."""
import json
from django.conf import settings
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from django.contrib.auth.models import User
from manager import utils


def read_config_file():
    url = settings.CONFIG_URL
    with open(url) as f:
        content = f.read()
    try:
        data = json.loads(content)
    except ValueError:
        return None
    return data


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


class TimeDataSerializer(serializers.Serializer):
    """Custom Serializer for responses to validate and get token requests."""

    utc = serializers.FloatField()

    tai = serializers.FloatField()

    mjd = serializers.FloatField()

    sidereal_summit = serializers.FloatField()

    sidereal_greenwich = serializers.FloatField()

    tai_to_utc = serializers.FloatField()


class TokenSerializer(serializers.Serializer):
    """Custom Serializer for responses to validate and get token requests."""

    user = UserSerializer()

    token = serializers.SerializerMethodField("get_token")

    permissions = serializers.SerializerMethodField("get_permissions")

    time_data = serializers.SerializerMethodField("get_time_data")

    config = serializers.SerializerMethodField("get_config")

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

    @swagger_serializer_method(serializer_or_field=TimeDataSerializer)
    def get_time_data(self, token) -> dict:
        """Return relevant time measures.

        Params
        ------
        token: Token
            The Token object

        Returns
        -------
        Dict
            Dictionary containing the following keys:
            - utc: current time in UTC scale as a unix timestamp (seconds)
            - tai: current time in UTC scale as a unix timestamp (seconds)
            - mjd: current time as a modified julian date
            - sidereal_summit: current time as a sidereal_time w/respect to the summit location (hourangles)
            - sidereal_summit: current time as a sidereal_time w/respect to Greenwich location (hourangles)
            - tai_to_utc: The number of seconds of difference between TAI and UTC times (seconds)
        """
        return utils.get_times()

    @swagger_serializer_method(serializer_or_field=serializers.JSONField())
    def get_config(self, token) -> dict:
        """Return the config file.
        If the query_param 'no_config' is present in the url of the original request, then the file is not read and the return value is None

        Params
        ------
        token: Token
            The Token object

        Returns
        -------
        Dict
            Dictionary containing the following keys:
            - alarms_sounds: dictionary containing flags of sound ON/OF for each severity level. Eg:
            alarms_sounds: {
                critical: 1,
                serious: 1,
                warning: 0
            }
        """
        no_config = self.context.get("no_config")
        if no_config:
            return None
        else:
            return read_config_file()
