# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or at
# your option any later version.
#
# This program is distributed in the hope that it will be useful,but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""Test users' authentication thorugh the API."""
from api.management.commands.createusers import (
    Command,
    admin_username,
    cmd_groupname,
    cmd_user_username,
    remote_base_username,
    remote_slac_username,
    remote_tucson_username,
    user_username,
)
from django.contrib.auth.models import Group, User
from django.test import TestCase

cmd_permission_codename = "api.command.execute_command"


class CreateusersTestCase(TestCase):
    """Test suite for the createusers command."""

    def test_command_creates_users(self):
        """Test that the command creates the users
        and their permissions accordingly."""
        # Arrange:
        old_users_num = User.objects.count()
        old_groups_num = Group.objects.count()
        command = Command()
        # Act:
        options = {
            "adminpass": "admin_pass",
            "userpass": "user_pass",
            "cmduserpass": "cmd_pass",
            "remotebaseuserpass": "remote_base_pass",
            "remotetucsonuserpass": "remote_tucson_pass",
            "remoteslacuserpass": "remote_slac_pass",
        }
        command.handle(*[], **options)
        # Assert:
        self.assertEqual(
            User.objects.count(), old_users_num + 6, "There are no new users"
        )
        self.assertEqual(
            Group.objects.count(), old_groups_num + 2, "There is no new group"
        )
        admin = User.objects.filter(username=admin_username).first()
        user = User.objects.filter(username=user_username).first()
        cmd_user = User.objects.filter(username=cmd_user_username).first()

        base_control_room = User.objects.filter(username=remote_base_username).first()
        tucson_control_room = User.objects.filter(
            username=remote_tucson_username
        ).first()
        slac_control_room = User.objects.filter(username=remote_slac_username).first()

        self.assertTrue(admin, "The {} user was not created".format(admin_username))
        self.assertTrue(user, "The {} user was not created".format(user_username))
        self.assertTrue(
            cmd_user, "The {} user was not created".format(cmd_user_username)
        )
        self.assertTrue(
            base_control_room,
            "The {} user was not created".format(remote_base_username),
        )
        self.assertTrue(
            tucson_control_room,
            "The {} user was not created".format(remote_tucson_username),
        )
        self.assertTrue(
            slac_control_room,
            "The {} user was not created".format(remote_slac_username),
        )
        self.assertTrue(
            admin.has_perm(cmd_permission_codename),
            "{} user should have cmd_execute permissions".format(admin_username),
        )
        self.assertFalse(
            user.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(user_username),
        )
        self.assertTrue(
            cmd_user.has_perm(cmd_permission_codename),
            "{} user should have cmd_execute permissions".format(cmd_user_username),
        )
        self.assertFalse(
            base_control_room.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(
                remote_base_username
            ),
        )
        self.assertFalse(
            tucson_control_room.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(
                remote_tucson_username
            ),
        )
        self.assertFalse(
            slac_control_room.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(
                remote_slac_username
            ),
        )

        cmd_group = Group.objects.filter(name=cmd_groupname).first()
        self.assertTrue(cmd_group, "The {} group was not created".format(cmd_groupname))

    def test_command_sets_permissions_even_if_users_already_existed(self):
        """Test that the command does not fail if the users already existed."""
        # Arrange:
        old_groups_num = Group.objects.count()
        command = Command()
        User.objects.create_user(
            username=admin_username,
            email="{}@fake.com".format(admin_username),
            password="dummy-pass",
        )
        User.objects.create_user(
            username=user_username,
            email="{}@fake.com".format(user_username),
            password="dummy-pass",
        )
        User.objects.create_user(
            username=cmd_user_username,
            email="{}@fake.com".format(cmd_user_username),
            password="dummy-pass",
        )
        User.objects.create_user(
            username=remote_base_username,
            email="{}@fake.com".format(remote_base_username),
            password="dummy-pass",
        )
        User.objects.create_user(
            username=remote_tucson_username,
            email="{}@fake.com".format(remote_tucson_username),
            password="dummy-pass",
        )
        User.objects.create_user(
            username=remote_slac_username,
            email="{}@fake.com".format(remote_slac_username),
            password="dummy-pass",
        )
        # Act:
        options = {
            "adminpass": "admin_pass",
            "userpass": "user_pass",
            "cmduserpass": "cmd_pass",
            "remotebaseuserpass": "remote_base_pass",
            "remotetucsonuserpass": "remote_tucson_pass",
            "remoteslacuserpass": "remote_slac_pass",
        }
        command.handle(*[], **options)
        # Assert:
        self.assertEqual(
            Group.objects.count(), old_groups_num + 2, "There is no new group"
        )
        admin = User.objects.filter(username=admin_username).first()
        user = User.objects.filter(username=user_username).first()
        cmd_user = User.objects.filter(username=cmd_user_username).first()
        base_control_room = User.objects.filter(username=remote_base_username).first()
        tucson_control_room = User.objects.filter(
            username=remote_tucson_username
        ).first()
        slac_control_room = User.objects.filter(username=remote_slac_username).first()

        self.assertTrue(
            admin.has_perm(cmd_permission_codename),
            "{} user should have cmd_execute permissions".format(admin_username),
        )
        self.assertFalse(
            user.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(user_username),
        )
        self.assertTrue(
            cmd_user.has_perm(cmd_permission_codename),
            "{} user should have cmd_execute permissions".format(cmd_user_username),
        )
        self.assertFalse(
            base_control_room.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(
                remote_base_username
            ),
        )
        self.assertFalse(
            tucson_control_room.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(
                remote_tucson_username
            ),
        )
        self.assertFalse(
            slac_control_room.has_perm(cmd_permission_codename),
            "{} user should not have cmd_execute permissions".format(
                remote_slac_username
            ),
        )

        cmd_group = Group.objects.filter(name=cmd_groupname).first()
        self.assertTrue(cmd_group, "The {} group was not created".format(cmd_groupname))
