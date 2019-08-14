"""Test users' authentication thorugh the API."""
from django.test import TestCase
from django.contrib.auth.models import User, Group
from api.management.commands.createusers import (
    Command,
    admin_username,
    user_username,
    cmd_user_username,
    cmd_groupname,
)

cmd_permission_codename = 'api.command.execute_command'


class CreateusersTestCase(TestCase):
    """Test suite for the createusers command."""

    def test_command_creates_users(self):
        """Test that the command creates the users and their permissions accordingly."""
        # Arrange:
        old_users_num = User.objects.count()
        old_groups_num = Group.objects.count()
        command = Command()
        # Act:
        options = {
            'adminpass': 'admin_pass',
            'userpass': 'user_pass',
            'cmduserpass': 'cmd_pass',
        }
        command.handle(*[], **options)
        # Assert:
        self.assertEqual(User.objects.count(), old_users_num + 4, 'There are no new users')
        self.assertEqual(Group.objects.count(), old_groups_num + 1, 'There is no new group')
        admin = User.objects.filter(username=admin_username).first()
        user = User.objects.filter(username=user_username).first()
        cmd_user = User.objects.filter(username=cmd_user_username).first()
        cmd_group = Group.objects.filter(name=cmd_groupname).first()
        self.assertTrue(admin, 'The {} user was not created'.format(admin_username))
        self.assertTrue(user, 'The {} user was not created'.format(user_username))
        self.assertTrue(cmd_user, 'The {} user was not created'.format(cmd_user_username))
        self.assertTrue(cmd_group, 'The {} group was not created'.format(cmd_groupname))
        self.assertTrue(
            admin.has_perm(cmd_permission_codename),
            '{} user should have cmd_execute permissions'.format(admin_username)
        )
        self.assertFalse(
            user.has_perm(cmd_permission_codename),
            '{} user should not have cmd_execute permissions'.format(user_username)
        )
        self.assertTrue(
            cmd_user.has_perm(cmd_permission_codename),
            '{} user should have cmd_execute permissions'.format(cmd_user_username)
        )

    def test_command_sets_permissions_even_if_users_already_existed(self):
        """Test that the command does not fail if the users already existed."""
        # Arrange:
        old_groups_num = Group.objects.count()
        command = Command()
        User.objects.create_user(
            username=admin_username,
            email='{}@fake.com'.format(admin_username),
            password='dummy-pass'
        )
        User.objects.create_user(
            username=user_username,
            email='{}@fake.com'.format(user_username),
            password='dummy-pass'
        )
        User.objects.create_user(
            username=cmd_user_username,
            email='{}@fake.com'.format(cmd_user_username),
            password='dummy-pass'
        )
        # Act:
        options = {
            'adminpass': 'admin_pass',
            'userpass': 'user_pass',
            'cmduserpass': 'cmd_pass',
        }
        command.handle(*[], **options)
        # Assert:
        self.assertEqual(Group.objects.count(), old_groups_num + 1, 'There is no new group')
        admin = User.objects.filter(username=admin_username).first()
        user = User.objects.filter(username=user_username).first()
        cmd_user = User.objects.filter(username=cmd_user_username).first()
        cmd_group = Group.objects.filter(name=cmd_groupname).first()
        self.assertTrue(cmd_group, 'The {} group was not created'.format(cmd_groupname))
        self.assertTrue(
            admin.has_perm(cmd_permission_codename),
            '{} user should have cmd_execute permissions'.format(admin_username)
        )
        self.assertFalse(
            user.has_perm(cmd_permission_codename),
            '{} user should not have cmd_execute permissions'.format(user_username)
        )
        self.assertTrue(
            cmd_user.has_perm(cmd_permission_codename),
            '{} user should have cmd_execute permissions'.format(cmd_user_username)
        )
