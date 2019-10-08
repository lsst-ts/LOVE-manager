"""Test the models."""
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from ui_framework.models import Workspace, View, WorkspaceView


class WorkspaceModelTestCase(TestCase):
    """Test the workspace model."""

    def setUp(self):
        """Testcase setup."""
        # Arrange
        self.workspace_name = 'My Workspace'
        self.old_workspaces_num = Workspace.objects.count()
        self.creation_timestamp = timezone.now()
        with freeze_time(self.creation_timestamp):
            self.workspace = Workspace.objects.create(name=self.workspace_name)

    def test_create_workspace(self):
        """Test that a workspace can be created in the database."""
        # Assert
        self.new_workspaces_num = Workspace.objects.count()
        self.assertEqual(
            self.old_workspaces_num + 1, self.new_workspaces_num,
            'There is not a new object in the database'
        )
        self.assertEqual(
            self.workspace.name, self.workspace_name,
            'The name is not as expected'
        )
        self.assertEqual(
            self.workspace.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.workspace.update_timestamp, self.creation_timestamp,
            'The update_timestamp is not as expected'
        )

    def test_retrieve_workspace(self):
        """Test that a workspace can be retrieved from the database."""
        # Arrange:
        self.old_workspaces_num = Workspace.objects.count()

        # Act
        self.workspace = Workspace.objects.get(pk=self.workspace.pk)

        # Assert
        self.new_workspaces_num = Workspace.objects.count()
        self.assertEqual(
            self.old_workspaces_num, self.new_workspaces_num,
            'The number of objects in the DB should not change'
        )
        self.assertEqual(
            self.workspace.name, self.workspace_name,
            'The name is not as expected'
        )
        self.assertEqual(
            self.workspace.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.workspace.update_timestamp, self.creation_timestamp,
            'The update_timestamp is not as expected'
        )

    def test_update_workspace(self):
        """Test that a workspace can be updated in the database."""
        # Arrange:
        self.old_workspaces_num = Workspace.objects.count()

        # Act
        self.update_timestamp = timezone.now()
        with freeze_time(self.update_timestamp):
            self.workspace.name = 'This other name'
            self.workspace.save()

        # Assert
        self.workspace = Workspace.objects.get(pk=self.workspace.pk)
        self.new_workspaces_num = Workspace.objects.count()
        self.assertEqual(
            self.old_workspaces_num, self.new_workspaces_num,
            'The number of objects in the DB should not change'
        )
        self.assertEqual(
            self.workspace.name, 'This other name',
            'The name is not as expected'
        )
        self.assertEqual(
            self.workspace.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.workspace.update_timestamp, self.update_timestamp,
            'The update_timestamp is not as expected'
        )
        self.assertNotEqual(
            self.workspace.creation_timestamp, self.workspace.update_timestamp,
            'The update_timestamp should be updated after updating the object'
        )

    def test_delete_workspace(self):
        """Test that a workspace can be deleted from the database."""
        # Arrange:
        self.old_workspaces_num = Workspace.objects.count()

        # Act
        self.workspace = Workspace.objects.get(pk=self.workspace.pk)
        self.workspace_pk = self.workspace.pk
        self.workspace.delete()

        # Assert
        self.new_workspaces_num = Workspace.objects.count()
        self.assertEqual(
            self.old_workspaces_num - 1, self.new_workspaces_num,
            'The number of objects in the DB have decreased by 1'
        )
        with self.assertRaises(Exception):
            Workspace.objects.get(pk=self.workspace_pk)


class ViewModelTestCase(TestCase):
    """Test the view model."""

    def setUp(self):
        """Testcase setup."""
        # Arrange
        self.view_name = 'My View'
        self.old_views_num = View.objects.count()
        self.creation_timestamp = timezone.now()
        with freeze_time(self.creation_timestamp):
            self.view = View.objects.create(name=self.view_name)

    def test_create_view(self):
        """Test that a view can be created in the database."""
        # Assert
        self.new_views_num = View.objects.count()
        self.assertEqual(
            self.old_views_num + 1, self.new_views_num,
            'There is not a new object in the database'
        )
        self.assertEqual(
            self.view.name, self.view_name,
            'The name is not as expected'
        )
        self.assertEqual(
            self.view.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.view.update_timestamp, self.creation_timestamp,
            'The update_timestamp is not as expected'
        )

    def test_retrieve_view(self):
        """Test that a view can be retrieved from the database."""
        # Arrange:
        self.old_views_num = View.objects.count()

        # Act
        self.view = View.objects.get(pk=self.view.pk)

        # Assert
        self.new_views_num = View.objects.count()
        self.assertEqual(
            self.old_views_num, self.new_views_num,
            'The number of objects in the DB should not change'
        )
        self.assertEqual(
            self.view.name, self.view_name,
            'The name is not as expected'
        )
        self.assertEqual(
            self.view.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.view.update_timestamp, self.creation_timestamp,
            'The update_timestamp is not as expected'
        )

    def test_update_view(self):
        """Test that a view can be updated in the database."""
        # Arrange:
        self.old_views_num = View.objects.count()

        # Act
        self.update_timestamp = timezone.now()
        with freeze_time(self.update_timestamp):
            self.view.name = 'This other name'
            self.view.save()

        # Assert
        self.view = View.objects.get(pk=self.view.pk)
        self.new_views_num = View.objects.count()
        self.assertEqual(
            self.old_views_num, self.new_views_num,
            'The number of objects in the DB should not change'
        )
        self.assertEqual(
            self.view.name, 'This other name',
            'The name is not as expected'
        )
        self.assertEqual(
            self.view.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.view.update_timestamp, self.update_timestamp,
            'The update_timestamp is not as expected'
        )
        self.assertNotEqual(
            self.view.creation_timestamp, self.view.update_timestamp,
            'The update_timestamp should be updated after updating the object'
        )

    def test_delete_view(self):
        """Test that a view can be deleted from the database."""
        # Arrange:
        self.old_views_num = View.objects.count()

        # Act
        self.view = View.objects.get(pk=self.view.pk)
        self.view_pk = self.view.pk
        self.view.delete()

        # Assert
        self.new_views_num = View.objects.count()
        self.assertEqual(
            self.old_views_num - 1, self.new_views_num,
            'The number of objects in the DB have decreased by 1'
        )
        with self.assertRaises(Exception):
            Workspace.objects.get(pk=self.view_pk)


class WorkspaceViewModelTestCase(TestCase):
    """Test the workspace_view model."""

    def setUp(self):
        """Testcase setup."""
        # Arrange
        self.workspace_name = 'My Workspace'
        self.view_name = 'My View'
        self.workspace_view_name = 'My WorkspaceView'
        self.old_workspace_views_num = WorkspaceView.objects.count()
        self.creation_timestamp = timezone.now()
        with freeze_time(self.creation_timestamp):
            self.workspace = Workspace.objects.create(name=self.workspace_name)
            self.view = View.objects.create(name=self.view_name)
            self.workspace_view = WorkspaceView.objects.create(
                view_name=self.workspace_view_name,
                workspace=self.workspace,
                view=self.view
            )

    def test_create_workspace_view(self):
        """Test that a workspace_view can be created in the database."""
        # Assert
        self.new_workspace_views_num = WorkspaceView.objects.count()
        self.assertEqual(
            self.old_workspace_views_num + 1, self.new_workspace_views_num,
            'There is not a new object in the database'
        )
        self.assertEqual(
            self.workspace_view.view_name, self.workspace_view_name,
            'The name is not as expected'
        )
        self.assertEqual(
            self.workspace_view.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.workspace_view.update_timestamp, self.creation_timestamp,
            'The update_timestamp is not as expected'
        )

    def test_retrieve_workspace_view(self):
        """Test that a workspace_view can be retrieved from the database."""
        # Arrange:
        self.old_workspace_views_num = WorkspaceView.objects.count()

        # Act
        self.workspace_view = WorkspaceView.objects.get(pk=self.workspace_view.pk)

        # Assert
        self.new_workspace_views_num = WorkspaceView.objects.count()
        self.assertEqual(
            self.old_workspace_views_num, self.new_workspace_views_num,
            'The number of objects in the DB should not change'
        )
        self.assertEqual(
            self.workspace_view.view_name, self.workspace_view_name,
            'The name is not as expected'
        )
        self.assertEqual(
            self.workspace_view.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.workspace_view.update_timestamp, self.creation_timestamp,
            'The update_timestamp is not as expected'
        )

    def test_update_workspace_view(self):
        """Test that a workspace_view can be updated in the database."""
        # Arrange:
        self.old_workspace_views_num = WorkspaceView.objects.count()
        self.new_sort_value = self.workspace_view.sort_value + 1
        # Act
        self.update_timestamp = timezone.now()
        with freeze_time(self.update_timestamp):
            self.workspace_view.view_name = 'This other name'
            self.workspace_view.sort_value = self.new_sort_value
            self.workspace_view.save()

        # Assert
        self.workspace_view = WorkspaceView.objects.get(pk=self.workspace_view.pk)
        self.new_workspace_views_num = WorkspaceView.objects.count()
        self.assertEqual(
            self.old_workspace_views_num, self.new_workspace_views_num,
            'The number of objects in the DB should not change'
        )
        self.assertEqual(
            self.workspace_view.view_name, 'This other name',
            'The name was not updated'
        )
        self.assertEqual(
            self.workspace_view.sort_value, self.new_sort_value,
            'The sort value was not updated'
        )
        self.assertEqual(
            self.workspace_view.creation_timestamp, self.creation_timestamp,
            'The creation_timestamp is not as expected'
        )
        self.assertEqual(
            self.workspace_view.update_timestamp, self.update_timestamp,
            'The update_timestamp is not as expected'
        )
        self.assertNotEqual(
            self.workspace_view.creation_timestamp, self.workspace_view.update_timestamp,
            'The update_timestamp should be updated after updating the object'
        )

    def test_delete_workspace_view(self):
        """Test that a workspace_view can be deleted from the database."""
        # Arrange:
        self.old_workspace_views_num = WorkspaceView.objects.count()

        # Act
        self.workspace_view = WorkspaceView.objects.get(pk=self.workspace_view.pk)
        self.workspace_view_pk = self.workspace_view.pk
        self.workspace_view.delete()

        # Assert
        self.new_workspace_views_num = WorkspaceView.objects.count()
        self.assertEqual(
            self.old_workspace_views_num - 1, self.new_workspace_views_num,
            'The number of objects in the DB have decreased by 1'
        )
        with self.assertRaises(Exception):
            Workspace.objects.get(pk=self.workspace_view_pk)


class WorkspaceAndViewsRelationsTestCase(TestCase):
    """Test the relationships vetween Workspace, View and WorkspaceView models."""

    def setUp(self):
        """Testcase setup."""
        # Arrange
        self.setup_timestamp = timezone.now()
        with freeze_time(self.setup_timestamp):
            self.workspaces = [
                Workspace.objects.create(name='My Workspace 1'),
                Workspace.objects.create(name='My Workspace 2'),
                Workspace.objects.create(name='My Workspace 3'),
            ]
            self.views = [
                View.objects.create(name='My View 1'),
                View.objects.create(name='My View 2'),
                View.objects.create(name='My View 3'),
            ]

    def test_add_and_get_views_to_workspace(self):
        """Test that Views can be added/retrieved to/from a Workspace in the DB."""
        # Act
        # - Add
        sorted_views = [self.views[0], self.views[2], self.views[1]]
        for view in sorted_views:
            self.workspaces[0].views.add(view)
        # - Get
        workspace = Workspace.objects.get(pk=self.workspaces[0].pk)
        retrieved_views = list(workspace.views.all())
        retrieved_sorted_views = list(workspace.get_sorted_views())
        # Assert
        self.assertEqual(set(retrieved_views), set(self.views), 'The views were not assigned to the workspace')
        self.assertEqual(retrieved_sorted_views, sorted_views, 'The views were not sorted properly workspace')

    def test_get_workspaces_from_a_view(self):
        """Test that a View can retrieve its Workspaces from the DB."""
        # Arrange
        view = self.views[0]
        workspaces = [
            self.workspaces[2],
            self.workspaces[0],
        ]
        for workspace in workspaces:
            workspace.views.add(view)
        # Act
        retrieved_workspaces = set(view.workspaces.all())
        # Assert
        self.assertEqual(retrieved_workspaces, set(workspaces), 'The workspaces from the view are not as expected')
