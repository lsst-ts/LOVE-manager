"""Defines the views exposed by the REST API exposed by this app."""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from ui_framework.models import Workspace, View, WorkspaceView
from ui_framework.serializers import (
    WorkspaceSerializer,
    ViewSerializer,
    WorkspaceViewSerializer,
    WorkspaceWithViewNameSerializer,
)


class WorkspaceViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the Workspace model."""

    queryset = Workspace.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = WorkspaceSerializer
    """Serializer used to serialize Workspace objects"""

    @swagger_auto_schema(
        method='get',
        responses={200: openapi.Response('Responsee', WorkspaceWithViewNameSerializer)})
    @action(detail=False)
    def with_view_name(self, request):
        """Serialize Workspaces including the view's names in the views response.

        Params
        ------
        request: Request
            The Requets object

        Returns
        -------
        Response
            The response containing the serialized Workspaces,
            but returning a list of dicts with each view's id and name
        """
        workspaces = Workspace.objects.all()
        serializer = WorkspaceWithViewNameSerializer(workspaces, many=True)
        return Response(serializer.data)


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
