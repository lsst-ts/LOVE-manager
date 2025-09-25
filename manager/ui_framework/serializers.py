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


"""Defines the serializer used by the REST API exposed by this app."""
import base64
import imghdr

import six
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Max
from rest_framework import serializers
from ui_framework.models import View, Workspace, WorkspaceView


class Base64ImageField(serializers.ImageField):
    """A Django REST framework field for handling image-uploads
    through raw post data. It uses base64 for encoding
    and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    @staticmethod
    def _get_view_id_from_data(data):
        """Return a view_id integer for building the thumbnail file_namet
        by checking whether the id comes in the request data or if a new one
        has to be created"""
        # id field should come in req data if view exists
        if "id" in data:
            return data["id"]

        # safe to assume that max(id)+1 can be overwritten
        view_id_max = View.objects.aggregate(Max("id"))
        if view_id_max["id__max"] is None:
            return 1

        return view_id_max["id__max"] + 1

    def to_representation(self, value):
        """Return a string representation of the image based on a given value.
        If value is None, then None is returned.

        Parameters
        ----------
        value : object
            The given value for the string representation

        Returns
        -------
        string
            The string representation
        """
        string_value = str(value)
        if value is not None and value != "":
            if string_value.startswith("http"):
                return str(value)
            return f"{settings.MEDIA_URL}{string_value}"
        return None

    def to_internal_value(self, data):
        """Transform a serialized image to the internal Base64ImageField object

        Parameters
        ----------
        data : dict
            The serialized image

        Returns
        -------
        object
            the object value
        """
        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if "data:" in data and ";base64," in data:
                # Break out the header from the base64 content
                header, data = data.split(";base64,")
            else:
                return None

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail("invalid_image")

            # Generate file name:
            view_id = self._get_view_id_from_data(self.parent.context["request"].data)
            file_name = f"view_{view_id}"

            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (
                file_name,
                file_extension,
            )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        """Return the file extension of an image,
        given its filename and decoded_file.

        Parameters
        ----------
        file_name : string
            The name of the image file
        decoded_file : bytes
            The decoded image

        Returns
        -------
        string
            the image extension, e.g. "jpg"
        """
        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension
        return extension


class ViewSerializer(serializers.ModelSerializer):
    """Serializer for the View model."""

    thumbnail = Base64ImageField(
        required=False,
        max_length=None,
        use_url=True,
        allow_empty_file=True,
        allow_null=True,
    )
    """Serializer for the thumbnail field."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = View
        fields = ("id", "name", "thumbnail", "screen", "data")


class ViewSummarySerializer(serializers.ModelSerializer):
    """Serializer for the View model including only id and name."""

    thumbnail = Base64ImageField(
        required=False,
        max_length=None,
        use_url=True,
        allow_empty_file=True,
        allow_null=True,
    )

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = View
        fields = ("id", "name", "thumbnail", "screen")


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for the Workspace model."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = Workspace
        fields = "__all__"


class WorkspaceFullSerializer(serializers.ModelSerializer):
    """Serializer for the Workspace model,
    including the views fully subserialized."""

    views = ViewSerializer(many=True, read_only=True)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = Workspace
        fields = "__all__"


class WorkspaceWithViewNameSerializer(serializers.ModelSerializer):
    """Serializer for the Workspace model,
    including names of views in the view field."""

    views = ViewSummarySerializer(many=True, read_only=True)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = Workspace
        fields = "__all__"


class WorkspaceViewSerializer(serializers.ModelSerializer):
    """Serializer for the WorkspaceView model."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = WorkspaceView
        fields = "__all__"
