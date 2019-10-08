"""Defines the views exposed by the REST API exposed by this app."""
from rest_framework import viewsets
from ui_framework.models import Workspace, View, WorkspaceView
from ui_framework.serializers import WorkspaceSerializer, ViewSerializer, WorkspaceViewSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    """Define API endpoints for the Workspace model."""

    queryset = Workspace.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = WorkspaceSerializer
    """Serializer used to serialize Workspace objects"""


class ViewViewSet(viewsets.ModelViewSet):
    """Define API endpoints for the View model."""

    queryset = View.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = ViewSerializer
    """Serializer used to serialize View objects"""


class WorkspaceViewViewSet(viewsets.ModelViewSet):
    """Define API endpoints for the WorkspaceView model."""

    queryset = WorkspaceView.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = WorkspaceViewSerializer
    """Serializer used to serialize View objects"""
