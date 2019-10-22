"""Defines the views exposed by the REST API exposed by this app."""
from rest_framework import viewsets
from ui_framework.models import Workspace, View, WorkspaceView
from ui_framework.serializers import WorkspaceSerializer, ViewSerializer, WorkspaceViewSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the Workspace model."""

    queryset = Workspace.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = WorkspaceSerializer
    """Serializer used to serialize Workspace objects"""


class ViewViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the View model."""

    queryset = View.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = ViewSerializer
    """Serializer used to serialize View objects"""


class WorkspaceViewViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the WorkspaceView model."""

    queryset = WorkspaceView.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = WorkspaceViewSerializer
    """Serializer used to serialize View objects"""
