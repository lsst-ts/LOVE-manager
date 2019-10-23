"""Defines the serializer used by the REST API exposed by this app ('api')."""
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = User
        """The model class to serialize"""

        fields = ('username', 'email')
        """The fields of the model class to serialize"""


class UserPermissionsSerializer(serializers.Serializer):

    execute_commands = serializers.SerializerMethodField('can_execute_commands')

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def can_execute_commands(self, obj):
        return serializers.BooleanField(obj.has_perm('api.command.execute_command'))


class TokenSerializer(serializers.Serializer):
    """Custom Serializer for responses to validate and get token requests."""

    user = UserSerializer()

    key = serializers.CharField()

    user_data = serializers.SerializerMethodField('get_user_data')

    token = serializers.SerializerMethodField('get_token')

    permissions = serializers.SerializerMethodField('get_permissions')

    @swagger_serializer_method(serializer_or_field=UserPermissionsSerializer)
    def get_permissions(self, obj):
        return UserPermissionsSerializer(obj)

    def get_token(self, obj):
        return serializers.CharField(obj.key)

    def get_user_data(self, obj):
        return UserSerializer(obj.user)
