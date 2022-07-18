"""Defines the serializer used by the REST API exposed by this app ('api')."""
import json
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from django.contrib.auth.models import User
from manager import utils
from api.models import ConfigFile, EmergencyContact, ImageTag, CSCAuthorizationRequest
from typing import Union


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
    authlist_admin = serializers.SerializerMethodField("is_authlist_admin")

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

    def is_authlist_admin(self, user) -> bool:
        """Define wether or not the given user has permissions of authlist administration.

        Params
        ------
        user: User
            The User object

        Returns
        -------
        Bool
            True if the user can execute commands, False if not.
        """
        return user.has_perm("api.authlist.administrator")


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
    def get_config(self, token) -> Union[dict, None]:
        """Return the config file.
        If the 'no_config' flag is present in the url of the original request, then the file is not read
        and the return value is None
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


class CSCAuthorizationRequestSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    resolved_by = serializers.SlugRelatedField(read_only=True, slug_field="username")
    user = serializers.SlugRelatedField(read_only=True, slug_field="username")

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = CSCAuthorizationRequest
        """The model class to serialize"""

        fields = "__all__"
        """The fields of the model class to serialize"""


class CSCAuthorizationRequestAuthorizeSerializer(serializers.ModelSerializer):
    """Serializer to Authorize Authorization List Requests."""

    def validate_status(self, value):
        if not self.instance:
            raise serializers.ValidationError("No instance to update")
        elif self.instance.status != CSCAuthorizationRequest.RequestStatus.PENDING:
            raise serializers.ValidationError("Request already resolved")
        elif (
            self.instance.status == CSCAuthorizationRequest.RequestStatus.PENDING
            and value != CSCAuthorizationRequest.RequestStatus.AUTHORIZED
            and value != CSCAuthorizationRequest.RequestStatus.DENIED
        ):
            raise serializers.ValidationError(
                "Can only resolve status to Authorized or Denied"
            )
        return value

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = CSCAuthorizationRequest
        """The model class to serialize"""

        fields = ("status", "message", "duration")
        """The fields of the model class to serialize"""


class CSCAuthorizationRequestExecuteSerializer(serializers.ModelSerializer):
    """Serializer to Execute Authorization List Requests."""

    def validate_execution_status(self, value):
        if not self.instance:
            raise serializers.ValidationError("No instance to update")
        elif self.instance.status != CSCAuthorizationRequest.ExecutionStatus.PENDING:
            raise serializers.ValidationError("Request already executed")
        elif (
            self.instance.status == CSCAuthorizationRequest.ExecutionStatus.PENDING
            and value != CSCAuthorizationRequest.ExecutionStatus.SUCCESSFUL
            and value != CSCAuthorizationRequest.ExecutionStatus.FAIL
        ):
            raise serializers.ValidationError(
                "Can only resolve status to Successful or Fail"
            )
        return value

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = CSCAuthorizationRequest
        """The model class to serialize"""

        fields = ("execution_status", "execution_message")
        """The fields of the model class to serialize"""


class CSCAuthorizationRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer to create Authorization List Requests."""

    user = serializers.SlugRelatedField(read_only=True, slug_field="username")

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = CSCAuthorizationRequest
        """The model class to serialize"""

        fields = (
            "user",
            "cscs_to_change",
            "authorized_users",
            "unauthorized_cscs",
            "requested_by",
        )
        """The fields of the model class to serialize"""


# class ExposureLogSerializer(serializers.Serializer):
#     """Serializer to map the Model instance into JSON format."""
#     id = serializers.IntegerField(read_only=True)

#     def create(self, validated_data):
#         return {id: 1000}

#     def update(self, instance, validated_data):
#         return {id: 20000}
