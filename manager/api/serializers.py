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


"""Defines the serializer used by the REST API exposed by this app ('api')."""
import json
from typing import Union

from api.models import (
    ConfigFile,
    ControlLocation,
    EmergencyContact,
    ImageTag,
    ScriptConfiguration,
)
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from manager import utils
from manager.utils import CommandPermission


class UserSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = User
        """The model class to serialize"""

        fields = ("username", "email", "first_name", "last_name")
        """The fields of the model class to serialize"""


class UserPermissionsSerializer(serializers.Serializer):
    """Custom Serializer for user permissions."""

    execute_commands = serializers.SerializerMethodField("can_execute_commands")

    def can_execute_commands(self, user) -> bool:
        """Define wether or not the given user
        has permissions to execute commands.

        Params
        ------
        user: User
            The User object

        Returns
        -------
        Bool
            True if the user can execute commands, False if not.
        """
        request = self.context.get("request")
        return CommandPermission().has_permission(request, None)


class TimeDataSerializer(serializers.Serializer):
    """Custom Serializer to describe the time data fields for the Apidocs."""

    utc = serializers.FloatField()

    tai = serializers.FloatField()

    mjd = serializers.FloatField()

    sidereal_summit = serializers.FloatField()

    sidereal_greenwich = serializers.FloatField()

    tai_to_utc = serializers.FloatField()


class ConfigSerializer(serializers.Serializer):
    """Custom Serializer to describe the config file field for the Apidocs."""

    config_file = serializers.JSONField()


class TokenSerializer(serializers.Serializer):
    """Custom Serializer for responses to validate and get token requests."""

    user = UserSerializer()

    token = serializers.SerializerMethodField("get_token")

    permissions = serializers.SerializerMethodField("get_permissions")

    time_data = serializers.SerializerMethodField("get_time_data")

    config = serializers.SerializerMethodField("get_config")

    @swagger_serializer_method(serializer_or_field=UserPermissionsSerializer)
    def get_permissions(self, token):
        """Return user permissions serialized as a dictionary
        with permission names as keys and bools as values.

        Params
        ------
        token: Token
            The Token object

        Returns
        -------
        Bool
            True if the user can execute commands, False if not.
        """
        request = self.context.get("request")
        return UserPermissionsSerializer(token.user, context={"request": request}).data

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
            - sidereal_summit: current time as a sidereal_time
            w/respect to the summit location (hourangles)
            - sidereal_summit: current time as a sidereal_time
            w/respect to Greenwich location (hourangles)
            - tai_to_utc: The number of seconds of difference
            between TAI and UTC times (seconds)
        """
        return utils.get_times()

    @swagger_serializer_method(serializer_or_field=serializers.JSONField())
    def get_config(self, token) -> Union[dict, None]:
        # TODO: We are not using static typing yet. We will keep the
        # return type as 'Union[dict, None]' until we do. Then it
        # should be replaced by 'dict | None'.
        # See: DM-43424.
        """Return the config file.
        If the 'no_config' flag is present in the url of the original request,
        then the file is not read and the return value is None

        Params
        ------
        token: Token
            The Token object

        Returns
        -------
        Dict
            Dictionary containing the following keys:
            - alarms_sounds: dictionary containing flags
            of sound ON/OF for each severity level. Eg:
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
            selected_configuration = ConfigFile.objects.filter(
                selected_by_users=token.user
            ).first()
            if selected_configuration is not None:
                serializer = ConfigFileContentSerializer(selected_configuration)
            else:
                first_configuration = ConfigFile.objects.first()
                serializer = ConfigFileContentSerializer(first_configuration)

            return serializer.data


class ConfigFileSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    filename = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return str(obj.user)

    def get_filename(self, obj):
        return str(obj.file_name)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = ConfigFile
        """The model class to serialize"""

        fields = (
            "id",
            "username",
            "filename",
            "creation_timestamp",
            "update_timestamp",
        )
        """The fields of the model class to serialize"""


class ConfigFileContentSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    content = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()

    def get_content(self, obj):
        return json.loads(obj.config_file.read().decode("ascii"))

    def get_filename(self, obj):
        return str(obj.file_name)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = ConfigFile
        """The model class to serialize"""

        fields = ("id", "filename", "content", "update_timestamp")
        """The fields of the model class to serialize"""


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = EmergencyContact
        """The model class to serialize"""

        fields = "__all__"
        """The fields of the model class to serialize"""


class ImageTagSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = ImageTag
        """The model class to serialize"""

        fields = "__all__"
        """The fields of the model class to serialize"""


class ControlLocationSerializer(serializers.ModelSerializer):
    """Serializer to list ControlLocation Requests."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = ControlLocation
        """The model class to serialize"""

        fields = "__all__"
        """The fields of the model class to serialize"""


class ScriptConfigurationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    script_path = serializers.CharField(max_length=100)
    config_name = serializers.CharField(max_length=50)
    config_schema = serializers.CharField()
    script_type = serializers.ChoiceField(ScriptConfiguration.ScriptTypes)
    creation_timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ScriptConfiguration

    def create(self, validated_data):
        """Function that allows to handle the request of the method POST.
        Also, returns the instance of the seriliazer with the data
        that comes as payload.
        """
        return ScriptConfiguration.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Function that allows the method PATCH to be properly executed,
        returns the new instance of the object.
        """
        instance.config_schema = validated_data.get(
            "config_schema", instance.config_schema
        )
        instance.save()
        return instance
