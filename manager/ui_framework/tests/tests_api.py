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
            self.views = [
                View.objects.create(name='My View 1'),
                View.objects.create(name='My View 2'),
                View.objects.create(name='My View 3'),
                View.objects.create(name='My View 4'),
            ]
            self.workspaces = [
                Workspace.objects.create(name='My Workspace 1'),
                Workspace.objects.create(name='My Workspace 2'),
                Workspace.objects.create(name='My Workspace 3'),
            ]
            for i in range(0, len(self.workspaces)):
                self.workspaces[i].views.add(self.views[i])
                self.workspaces[i].views.add(self.views[i + 1])
        self.old_count = Workspace.objects.count()

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
        expected_data = [
            {
                'id': workspace.id,
                'name': workspace.name,
                'creation_timestamp': self.setup_ts_str,
                'update_timestamp': self.setup_ts_str,
                'views': [v.pk for v in workspace.views.all()],
            } for workspace in Workspace.objects.all()
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'The request failed')
        retrieved_data = [dict(w) for w in response.data]
        self.assertEqual(retrieved_data, expected_data, 'Retrieved data is not as expected')

    def test_create_workspaces(self):
        """Test that a workspace can be created through the API."""
        # Arrange
        self.client_login()
        given_data = {
            'name': 'My New Workspace',
            'views': [],
        }

        # Act
        response = self.client.post(reverse('workspace-list'), given_data)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, 'The request failed')
        self.new_count = Workspace.objects.count()
        self.assertEqual(self.old_count + 1, self.new_count, 'A new object should have been created in the DB')
        new_workspace = Workspace.objects.get(name=given_data['name'])
        new_workspace_views = [v.pk for v in new_workspace.views.all()]
        self.assertEqual(new_workspace_views, given_data['views'], 'Retrieved views are not as expected')

    def test_retrieve_workspaces(self):
        """Test that a workspace can be retrieved through the API."""
        # Arrange
        self.client_login()
        workspace = self.workspaces[0]
        # Act
        response = self.client.get(reverse('workspace-detail', kwargs={'pk': workspace.pk}))

        # Assert
        expected_data = {
            'id': workspace.id,
            'name': workspace.name,
            'creation_timestamp': self.setup_ts_str,
            'update_timestamp': self.setup_ts_str,
            'views': [v.pk for v in workspace.views.all()],
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'The request failed')
        retrieved_data = dict(response.data)
        self.assertEqual(retrieved_data, expected_data, 'Retrieved data is not as expected')

    def test_update_workspaces(self):
        """Test that a workspace can be updated through the API."""
        # Arrange
        self.client_login()
        workspace = self.workspaces[0]
        given_data = {
            'name': 'My New Workspace',
        }
        # Act
        self.update_ts = timezone.now()
        self.update_ts_str = serializers.DateTimeField().to_representation(self.update_ts)
        with freeze_time(self.update_ts):
            response = self.client.put(reverse('workspace-detail', kwargs={'pk': workspace.pk}), given_data)

        # Assert
        expected_data = {
            'id': workspace.id,
            'name': given_data['name'],
            'creation_timestamp': self.setup_ts_str,
            'update_timestamp': self.update_ts_str,
            'views': [v.pk for v in workspace.views.all()],
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'The request failed')
        retrieved_data = dict(response.data)
        self.assertEqual(retrieved_data, expected_data, 'Retrieved data is not as expected')

    def test_delete_workspaces(self):
        """Test that a workspace can be deleted through the API."""
        # Arrange
        self.client_login()
        workspace_pk = self.workspaces[0].pk
        # Act
        response = self.client.delete(reverse('workspace-detail', kwargs={'pk': workspace_pk}))

        # Assert
        self.new_count = Workspace.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, 'The request failed')
        self.assertEqual(self.old_count - 1, self.new_count, 'The number of objects in the DB have decreased by 1')
        with self.assertRaises(Exception):
            Workspace.objects.get(pk=workspace_pk)
