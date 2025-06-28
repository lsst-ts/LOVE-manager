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


"""Management utility to create operator on duty user."""
import getpass
from argparse import RawTextHelpFormatter

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

# Default users names
user_username = "user"
cmd_user_username = "cmd_user"
admin_username = "admin"

# Remote control users names
remote_base_username = "base_control_room"
remote_tucson_username = "tucson_control_room"
remote_slac_username = "slac_control_room"

# Default groups names
cmd_groupname = "cmd"
ui_framework_groupname = "ui_framework"


class Command(BaseCommand):
    """Django command to create the initial users with their permissions.

    It creates 3 users with the following characteristics and permissions:

    - "admin": has all the permissions, it is a Django superuser.
    - "user": basic user with no commands execution permissions
    but with permissions to add, edit and delete views.
    - "cmd_user": basic user with commands execution permissions
    and with permissions to add, edit and delete views.

    It also creates 3 users for remote monitoring support
    with no commands execution permissions
    but with permissions to add, edit and delete views:

    - "base_control_room": user for the Base control room.
    - "tucson_control_room": user for the Tucson control room.
    - "slac_control_room": user for the SLAC control room.

    It also creates 2 groups:

    - "cmd_group": defines the commands execution permissions.
    - "ui_framework_group": defines the permissions to add,
    edit and delete views.

    "cmd_user" user belongs to "cmd_group".
    "cmd_user", "user", "base_control_room",
    "tucson_control_room" and "slac_control_room"
    users belong to "ui_framework_group".

    The command receives arguments to set the passwords of the users,
    run `python manage.py createusers --help` for help.
    """

    help = """Django command to create the initial users with their permissions.\n

    It creates 3 users with the following characteristics and permissions:

    - "admin": has all the permissions, it is a Django superuser.
    - "user": basic user with no commands execution permissions,
    but with permissions to add, edit and delete views.
    - "cmd_user": basic user with commands execution permissions
    and with permissions to add, edit and delete views.

    It also creates 3 users for remote monitoring support
    with no commands execution permissions
    but with permissions to add, edit and delete views:

    - "base_control_room": user for the Base control room.
    - "tucson_control_room": user for the Tucson control room.
    - "slac_control_room": user for the SLAC control room.

    It also creates 2 groups:

    - "cmd_group": defines the commands execution permissions.
    - "ui_framework_group": defines the permissions to add,
    edit and delete views.

    "cmd_user" user belongs to "cmd_group".
    "cmd_user", "user", "base_control_room",
    "tucson_control_room" and "slac_control_room"
    users belong to "ui_framework_group"."""

    requires_migrations_checks = True
    stealth_options = ("stdin",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_parser(self, *args, **kwargs):
        """Create the arguments parser.

        It is ovewritten here just in order to set the formatter_class
        so that is allows break lines in the Command help.

        Params
        ------
        args: list
            List of arguments
        kwargs: dict
            Dictionary with additional
            keyword arguments (indexed by keys in the dict)
        """
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        """Add arguments for the command.

        Params
        ------
        parser: object
            parser for the arguments
        """
        parser.add_argument(
            "--adminpass", help='Specifies the password for the "admin" user.'
        )
        parser.add_argument(
            "--userpass", help='Specifies the password for the regular users ("user").'
        )
        parser.add_argument(
            "--cmduserpass",
            help='Specifies password for the users with cmd permissions ("cmd_user").',
        )
        parser.add_argument(
            "--remotebaseuserpass",
            help='Specifies password for the user for remote monitoring at Base ("base_control_room").',
        )
        parser.add_argument(
            "--remotetucsonuserpass",
            help='Specifies password for the user for remote monitoring at Tucson ("tucson_control_room").',
        )
        parser.add_argument(
            "--remoteslacuserpass",
            help='Specifies password for the user for remote monitoring at SLAC ("slac_control_room").',
        )

    def handle(self, *args, **options):
        """Execute the command, which creates the users.

        Params
        ------
        args: list
            List of arguments
        kwargs: dict
            Dictionary with additional
            keyword arguments (indexed by keys in the dict)
        """
        admin_password = options.get("adminpass")
        user_password = options.get("userpass")
        cmd_password = options.get("cmduserpass")
        remote_base_password = options.get("remotebaseuserpass")
        remote_tucson_password = options.get("remotetucsonuserpass")
        remote_slac_password = options.get("remoteslacuserpass")

        # Create groups
        ui_framework_group = self._create_ui_framework_group()
        cmd_group = self._create_cmd_group()

        # Create admin user
        if admin_password is not None:
            admin = self._create_user(admin_username, admin_password)

            # Make admin superuser and staff
            admin.is_superuser = True
            admin.is_staff = True
            admin.save()

        # Create user user
        if user_password is not None:
            user_user = self._create_user(user_username, user_password)
            ui_framework_group.user_set.add(user_user)

        # Create cmd_user user
        if cmd_password is not None:
            cmd_user = self._create_user(cmd_user_username, cmd_password)
            ui_framework_group.user_set.add(cmd_user)
            cmd_group.user_set.add(cmd_user)

        # Create remote users
        if remote_base_password is not None:
            remote_base_user = self._create_user(
                remote_base_username, remote_base_password
            )
            ui_framework_group.user_set.add(remote_base_user)

        if remote_tucson_password is not None:
            remote_tucson_user = self._create_user(
                remote_tucson_username, remote_tucson_password
            )
            ui_framework_group.user_set.add(remote_tucson_user)

        if remote_slac_password is not None:
            remote_slac_user = self._create_user(
                remote_slac_username, remote_slac_password
            )
            ui_framework_group.user_set.add(remote_slac_user)

    def _create_user(self, username, password):
        """Create a given user, if it does not exist. Return it anyway.

        Params
        ------
        username: string
            The name for the user
        password: string
            The password for the user

        Returns
        -------
        user: User
            The User object
        """
        while password is None or password.strip() == "":
            print("Creating {}...".format(username))
            password = getpass.getpass()
            if password.strip() == "":
                self.stderr.write("Error: Blank passwords aren't allowed.")
                password = None

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_user(
                username=username,
                email="{}@fake.com".format(username),
                password=password,
            )
        else:
            self.stderr.write(
                "Warning: The {} user is already created".format(username)
            )
        return user

    def _create_cmd_group(self):
        """Create and return the group of users
        with permissions to execute commands.

        Returns
        -------
        grouop: Group
            The Group object
        """
        group, created = Group.objects.get_or_create(name=cmd_groupname)
        permissions = Permission.objects.filter(codename="command.execute_command")
        for permission in permissions:
            group.permissions.add(permission)
        return group

    def _create_ui_framework_group(self):
        """Create and return the group of users
        with permissions to save, edit and delete views.

        Returns
        -------
        grouop: Group
            The Group object
        """
        group, created = Group.objects.get_or_create(name=ui_framework_groupname)
        permissions = Permission.objects.filter(
            content_type__app_label__contains="ui_framework"
        )
        for permission in permissions:
            group.permissions.add(permission)
        return group
