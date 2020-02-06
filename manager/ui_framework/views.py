"""Defines the views exposed by the REST API exposed by this app."""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ui_framework.models import Workspace, View, WorkspaceView
from ui_framework.serializers import (
    WorkspaceSerializer,
    ViewSerializer,
    WorkspaceViewSerializer,
    WorkspaceFullSerializer,
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
        responses={200: openapi.Response('Responsee', WorkspaceFullSerializer)})
    @action(detail=True)
    def full(self, request, pk=None):
        """Serialize a Workspace including the view's fully subserialized.

        Params
        ------
        request: Request
            The Requets object
        pk: int
            The corresponding Workspace pk

        Returns
        -------
        Response
            The response containing the serialized Workspaces, with the views fully subserialized
        """
        try:
            workspace = Workspace.objects.get(pk=pk)
        except Workspace.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = WorkspaceFullSerializer(workspace)
        return Response(serializer.data)

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

    queryset = View.objects.order_by('-update_timestamp').all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = ViewSerializer
    """Serializer used to serialize View objects"""

    @swagger_auto_schema(
        method='get',
        responses={200: openapi.Response('Responsee', ViewSerializer)})
    @action(detail=False)
    def search(self, request):
        """Serialize Views containing the query string.

        Params
        ------
        request: Request
            The Requets object

        Returns
        -------
        Response
            The response containing the serialized Views.
        """

        views = View.objects.order_by('-update_timestamp').all()
        query = self.request.query_params.get('query', None)
        if query is not None:
            views = views.filter(name__icontains=query)

        serializer = ViewSerializer(views, many=True)
        return Response(serializer.data)


class WorkspaceViewViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the WorkspaceView model."""

    queryset = WorkspaceView.objects.all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = WorkspaceViewSerializer
    """Serializer used to serialize View objects"""
