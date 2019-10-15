"""Utilities for testing purposes."""
import json
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import serializers
from rest_framework.test import APIClient
from ui_framework.models import Workspace, View, WorkspaceView


def get_dict(obj):
    """Return a dictionary with the fields of a given object."""
    if type(obj) == Workspace:
        return {
            'id': obj.id,
            'name': obj.name,
            'creation_timestamp': obj.creation_timestamp,
            'update_timestamp': obj.update_timestamp,
        }
    if type(obj) == View:
        return {
            'id': obj.id,
            'name': obj.name,
            'data': json.dumps(obj.data),
            'creation_timestamp': obj.creation_timestamp,
            'update_timestamp': obj.update_timestamp,
        }
    if type(obj) == WorkspaceView:
        return {
            'id': obj.id,
            'view_name': obj.view_name,
            'view': obj.view.pk,
            'workspace': obj.workspace.pk,
            'creation_timestamp': obj.creation_timestamp,
            'update_timestamp': obj.update_timestamp,
        }


class BaseTestCase(TestCase):
    """Base TestCase used to define a common setUp."""

    def setUp(self):
        """Set the base testcase.

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
            self.workspace_views_data = []
            # Create views, store them in self.views and add auto-generated fields to self.views_data
            for i in range(0, len(self.views_data)):
                view = View.objects.create(**self.views_data[i])
                self.views_data[i]['id'] = view.id
                self.views_data[i]['creation_timestamp'] = self.setup_ts_str
                self.views_data[i]['update_timestamp'] = self.setup_ts_str
                self.views.append(view)

            # Create views, store them in self.views and add auto-generated fields to self.views_data
            for i in range(0, len(self.workspaces_data)):
                workspace = Workspace.objects.create(**self.workspaces_data[i])
                self.workspaces_data[i]['id'] = workspace.id
                self.workspaces_data[i]['creation_timestamp'] = self.setup_ts_str
                self.workspaces_data[i]['update_timestamp'] = self.setup_ts_str
                self.workspaces_data[i]['views'] = [self.views[i].pk, self.views[i + 1].pk]
                self.workspaces.append(workspace)

                # Add view[i]
                self.workspaces[i].views.add(self.views[i], through_defaults={'view_name': 'v{}'.format(i)})
                aux = WorkspaceView.objects.get(workspace=self.workspaces[i], view=self.views[i])
                self.workspace_views_data.append({
                    'id': aux.id,
                    'creation_timestamp': self.setup_ts_str,
                    'update_timestamp': self.setup_ts_str,
                    'view_name': 'v{}'.format(i),
                    'sort_value': 0,
                    'view': self.views[i].pk,
                    'workspace': self.workspaces[i].pk,
                })
                # Add view[i + 1]
                self.workspaces[i].views.add(self.views[i + 1], through_defaults={'view_name': 'v{}'.format(i)})
                aux = WorkspaceView.objects.get(workspace=self.workspaces[i], view=self.views[i + 1])
                self.workspace_views_data.append({
                    'id': aux.id,
                    'creation_timestamp': self.setup_ts_str,
                    'update_timestamp': self.setup_ts_str,
                    'view_name': 'v{}'.format(i),
                    'sort_value': 0,
                    'view': self.views[i + 1].pk,
                    'workspace': self.workspaces[i].pk,
                })

        # Client to test the API
        self.client = APIClient()

        # Models to test:
        self.cases = [
            {
                'class': Workspace,
                'key': 'workspace',
                'old_count': Workspace.objects.count(),
                'new_data': {
                    'name': 'My new Workspace',
                },
                'current_data': self.workspaces_data,
                'selected_id': self.workspaces_data[0]['id'],
            },
            {
                'class': View,
                'key': 'view',
                'old_count': View.objects.count(),
                'new_data': {
                    'name': 'My new View',
                    'data': json.dumps({"dummy_key": "Dummy_value"}),
                },
                'current_data': self.views_data,
                'selected_id': self.views_data[0]['id'],
            },
            {
                'class': WorkspaceView,
                'key': 'workspaceview',
                'old_count': WorkspaceView.objects.count(),
                'new_data': {
                    'view_name': 'New view_name',
                    # 'sort_value': 1,
                    'view': self.views_data[3]['id'],
                    'workspace': self.workspaces_data[0]['id'],
                },
                'current_data': self.workspace_views_data,
                'selected_id': self.workspace_views_data[0]['id'],
            },
        ]
