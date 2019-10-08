"""Test the UI Framework API."""
from collections import OrderedDict
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import serializers, status
from rest_framework.test import APIClient
from api.models import Token
from ui_framework.models import Workspace, View, WorkspaceView


class WorkspaceCrudTestCase(TestCase):
    """Test the workspace CRUD API."""

    def setUp(self):
        """Testcase setup."""
        # Arrange
        self.client = APIClient()
        self.login_url = reverse('login')
        self.username = 'test'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.username,
            password='password',
            email='test@user.cl',
            first_name='First',
            last_name='Last',
        )
        self.setup_ts = timezone.now()
        self.setup_ts_str = serializers.DateTimeField().to_representation(self.setup_ts)
        with freeze_time(self.setup_ts):
            self.workspaces = [
                Workspace.objects.create(name='My Workspace 1'),
                Workspace.objects.create(name='My Workspace 2'),
                Workspace.objects.create(name='My Workspace 3'),
            ]

    def client_login(self):
        """Perform a login for the APIClient."""
        data = {'username': self.username, 'password': self.password}
        self.client.post(self.login_url, data, format='json')
        self.token = Token.objects.get(user__username=self.username)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_list_workspaces(self):
        """Test that the list of workspaces can be retrieved through the API."""
        # Arrange
        self.client_login()

        # Act
        response = self.client.get(reverse('workspace-list'))

        # Assert
        expected_workspaces = [
            {
                'id': workspace.id,
                'name': workspace.name,
                'creation_timestamp': self.setup_ts_str,
                'update_timestamp': self.setup_ts_str,
                'views': [],
            } for workspace in Workspace.objects.all()
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_workspaces = [dict(w) for w in response.data]
        self.assertEqual(retrieved_workspaces, expected_workspaces)
