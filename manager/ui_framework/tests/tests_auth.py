"""Test the UI Framework API."""
import json
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import serializers, status
from ui_framework.models import Workspace, View, WorkspaceView
from ui_framework.tests.utils import get_dict


class UnauthorizedCrudTestCase(TestCase):
    """Test that unauthenticated users cannot use the CRUD API."""

    def setUp(self):
        """Testcase setup.

        We start with 3 workspaces and 4 views and we add view_i and view_i+1 to workspace_i
        """
        # Arrange
        # Populate the Database
        self.setup_ts = timezone.now()
        self.setup_ts_str = serializers.DateTimeField().to_representation(self.setup_ts)
        with freeze_time(self.setup_ts):
            # Data to be used to create views and workspaces
            self.views_data = [
                {
                    'name': 'My View 0',
                    'data': json.dumps({"data_name": "My View 0"}),
                },
                {
                    'name': 'My View 1',
                    'data': json.dumps({"data_name": "My View 1"}),
                },
                {
                    'name': 'My View 2',
                    'data': json.dumps({"data_name": "My View 2"}),
                },
                {
                    'name': 'My View 3',
                    'data': json.dumps({"data_name": "My View 3"}),
                }
            ]
            self.workspaces_data = [
                {'name': 'My Workspace 0'},
                {'name': 'My Workspace 1'},
                {'name': 'My Workspace 2'},
            ]
            self.views = []
            self.workspaces = []
            # Create views, store them in self.views and add auto-generated fields to self.views_data
            for i in range(0, len(self.views_data)):
                view = View.objects.create(**self.views_data[i])
                self.views_data[i]['id'] = view.id
                self.views_data[i]['creation_timestamp'] = view.creation_timestamp
                self.views_data[i]['update_timestamp'] = view.update_timestamp
                self.views.append(view)

            # Create views, store them in self.views and add auto-generated fields to self.views_data
            for i in range(0, len(self.workspaces_data)):
                workspace = Workspace.objects.create(**self.workspaces_data[i])
                self.workspaces_data[i]['id'] = workspace.id
                self.workspaces_data[i]['creation_timestamp'] = workspace.creation_timestamp
                self.workspaces_data[i]['update_timestamp'] = workspace.update_timestamp
                self.workspaces.append(workspace)

                # Add view_i and view_i+1 to workspace_i
                self.workspaces[i].views.add(self.views[i], through_defaults={'view_name': 'v{}'.format(i)})
                self.workspaces[i].views.add(self.views[i + 1], through_defaults={'view_name': 'v{}'.format(i)})

        self.cases = [
            {
                'class': Workspace,
                'url_key': 'workspace',
                'old_count': Workspace.objects.count(),
                'new_data': {
                    'name': 'My new Workspace',
                }
            },
            {
                'class': View,
                'url_key': 'view',
                'old_count': View.objects.count(),
                'new_data': {
                    'name': 'My new View',
                    'data': json.dumps({"dummy_key": "Dummy_value"}),
                }
            },
            {
                'class': WorkspaceView,
                'url_key': 'workspaceview',
                'old_count': WorkspaceView.objects.count(),
                'new_data': {
                    'view_name': 'My new View with custom name',
                    'sort_value': 1,
                    'view': 0,
                    'workspace': 0,
                }
            },
        ]

    def test_cannot_list_objects(self):
        """Test that unauthenticated users cannot retrieve the list of objects through the API."""
        for case in self.cases:
            # Act
            url = reverse('{}-list'.format(case['url_key']))
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Get list of {} did not return status 401'.format(case['class'])
            )

    def test_cannot_create_objects(self):
        """Test that unauthenticated users cannot create objects through the API."""
        for case in self.cases:
            # Act
            url = reverse('{}-list'.format(case['url_key']))
            response = self.client.post(url, case['new_data'])
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Posting a new {} did not return status 401'.format(case['class'])
            )
            self.assertEqual(
                case['class'].objects.count(), case['old_count'],
                'The number of {} should not have changed'.format(case['class'])
            )

    def test_cannot_retrieve_objects(self):
        """Test that unauthenticated users cannot retrieve objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Getting a {} did not return status 401'.format(case['class'])
            )

    def test_cannot_update_objects(self):
        """Test that unauthenticated users cannot update objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            old_data = get_dict(obj)
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.put(url, case['new_data'])
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Updating a {} did not return status 401'.format(case['class'])
            )
            new_data = get_dict(case['class'].objects.get(pk=obj.pk))
            self.assertEqual(
                new_data, old_data,
                'The object {} should not have been updated'.format(case['class'])
            )

    def test_cannot_dalete_objects(self):
        """Test that unauthenticated users cannot dalete objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.delete(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Deleting a {} did not return status 401'.format(case['class'])
            )
            self.assertEqual(
                case['class'].objects.count(), case['old_count'],
                'The number of {} should not have changed'.format(case['class'])
            )
