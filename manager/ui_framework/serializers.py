"""Defines the serializer used by the REST API exposed by this app."""
from rest_framework import serializers
from ui_framework.models import Workspace, View, WorkspaceView


class ViewSerializer(serializers.ModelSerializer):
    """Serializer for the View model."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = View
        fields = '__all__'


class ViewSummarySerializer(serializers.ModelSerializer):
    """Serializer for the View model including only id and name."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""

        model = View
        fields = ('id', 'name')


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for the Workspace model."""

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
