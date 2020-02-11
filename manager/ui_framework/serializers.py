"""Defines the serializer used by the REST API exposed by this app."""
from rest_framework import serializers
from ui_framework.models import Workspace, View, WorkspaceView
from django.conf import settings

class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    def to_representation(self, value):
        return settings.MEDIA_URL + str(value)

    def to_internal_value(self, data):
        from django.core.files.base import ContentFile
        import base64
        import six
        import uuid

        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension
        
class ViewSerializer(serializers.ModelSerializer):
    """Serializer for the View model."""
    thumbnail = Base64ImageField(
        required=False, max_length=None, use_url=False, allow_empty_file=True, allow_null=True,
    )

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = View
        fields = ('id', 'name', 'thumbnail', 'data')


class ViewSummarySerializer(serializers.ModelSerializer):
    """Serializer for the View model including only id and name."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = View
        fields = ('id', 'name', 'thumbnail')


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for the Workspace model."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = Workspace
        fields = '__all__'


class WorkspaceFullSerializer(serializers.ModelSerializer):
    """Serializer for the Workspace model, including the views fully subserialized."""

    views = ViewSerializer(many=True, read_only=True)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = Workspace
        fields = '__all__'


class WorkspaceWithViewNameSerializer(serializers.ModelSerializer):
    """Serializer for the Workspace model, including names of views in the view field."""

    views = ViewSummarySerializer(many=True, read_only=True)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = Workspace
        fields = '__all__'


class WorkspaceViewSerializer(serializers.ModelSerializer):
    """Serializer for the WorkspaceView model."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = WorkspaceView
        fields = '__all__'
