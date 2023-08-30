# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile and Vera C. Rubin Observatory Telescope
# and Site Systems.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or at your option any later version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""Management utility to create operator on duty user."""
import getpass
from argparse import RawTextHelpFormatter
from django.contrib.auth.models import Permission, Group, User
from django.core.management.base import BaseCommand

user_username = "user"
test_username = "test"
cmd_user_username = "cmd_user"
admin_username = "admin"
authlist_username = "authlist_user"
cmd_groupname = "cmd"
ui_framework_groupname = "ui_framework"
authlist_groupname = "authlist"


class Command(BaseCommand):
    """Django command to create the initial users with their permissions.

    It creates 5 users with the following characteristics and permissions:

    - "admin": has all the permissions, it is a Django superuser
    - "user": basic user with no permissions)
    - "cmd_user": basic user with commands execution permissions
    - "authlist_user": basic user with authlist administration permissions
    - "test": basic user with commands execution permissions

    It also creates 2 Groups:
    "cmd_group", which defines the commands execution permissions.
    "authlist_group", which defines the permission to access and resolve AuthList requests

    "cmd_user" and "test" users belong to "cmd_group".
    "authlist_user" belong to "authlist_group"

    The command receives arguments to set the passwords of the users,
    run `python manage.py createusers --help` for help.
    """

    help = """Django command to create the initial users with their permissions.\n

    It creates 5 users with the following characteristics and permissions:

    - "admin": has all the permissions, it is a Django superuser
    - "user": basic user with no permissions)
    - "cmd_user": basic user with commands execution permissions
    - "authlist_user": basic user with authlist administration permissions
    - "test": basic user with commands execution permissions

    It also creates 2 Group:
    "cmd_group", which defines the commands execution permissions.
    "ui_framework_group", which defines the permissions to add, edit and delete views.
    "authlist_group", which defines the permission to access and resolve AuthList requests

    "cmd_user" and "test" users belong to "cmd_group".
    "cmd_user", "test" and "authlist_user" users belong to "ui_framework_group".
    "authlist_user" belong to "authlist_group"."""

    requires_migrations_checks = True
    stealth_options = ("stdin",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_parser(self, *args, **kwargs):
        """Create the arguments parser.

        It is ovewritten here just in order to set the formatter_class so that is allows break lines
        in the Command help.

        Params
        ------
        args: list
            List of arguments
        kwargs: dict
            Dictionary with addittional keyword arguments (indexed by keys in the dict)
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
            help='Specifies password for the users with cmd permissions ("cmd_user" and "test").',
        )
        parser.add_argument(
            "--authlistuserpass",
            help='Specifies password for the users with authlist permissions ("authlist_user").',
        )

    def handle(self, *args, **options):
        """Execute the command, which creates the users.

        Params
        ------
        args: list
            List of arguments
        kwargs: dict
            Dictionary with addittional keyword arguments (indexed by keys in the dict)
        """
        admin_password = options["adminpass"]
        user_password = options["userpass"]
        cmd_password = options["cmduserpass"]
        authlist_password = options["authlistuserpass"]

        # Create users
        admin = self._create_user(admin_username, admin_password)
        self._create_user(user_username, user_password)
        cmd_user = self._create_user(cmd_user_username, cmd_password)
        test_user = self._create_user(test_username, cmd_password)
        authlist_user = self._create_user(authlist_username, authlist_password)

        # Make admin superuser and staff
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()

        # Create cmd_group
        cmd_group = self._create_cmd_group()

        # Add cmd_user and test users to cmd_group
        cmd_group.user_set.add(cmd_user)
        cmd_group.user_set.add(test_user)

        # Create ui_framework group
        ui_framework_group = self._create_ui_framework_group()

        # Add cmd_user, test and authlist_user users to ui_framework_group
        ui_framework_group.user_set.add(cmd_user)
        ui_framework_group.user_set.add(test_user)
        ui_framework_group.user_set.add(authlist_user)

        # Create authlist_group
        authlist_group = self._create_authlist_group()

        # Add authlist_user to authlist_group
        authlist_group.user_set.add(authlist_user)

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
        """Create and return the group of users with permissions to execute commands.

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
        """Create and return the group of users with permissions to save, edit and delete views.

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

    def _create_authlist_group(self):
        """Create and return the group of users with permissions to administrate authlist.

        Returns
        -------
        group: Group
            The Group object
        """
        group, created = Group.objects.get_or_create(name=authlist_groupname)
        permissions = Permission.objects.filter(codename="authlist.administrator")
        for permission in permissions:
            group.permissions.add(permission)
        return group
