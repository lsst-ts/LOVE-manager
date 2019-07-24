"""Management utility to create operator on duty user."""
import getpass
from argparse import RawTextHelpFormatter
from django.contrib.auth.models import Permission, Group, User
from django.core.management.base import BaseCommand

user_username = 'user'
cmd_user_username = 'cmd_user'
admin_username = 'admin'
cmd_groupname = 'cmd'
test_username = 'test'


class Command(BaseCommand):
    """Django command to create the initial users with their permissions.

    It creates 4 users with the following characteristics and permissions:

    - "admin": has all the permissions, it is a Django superuser
    - "user": basic user with no permissions)
    - "cmd_user": basic user with commands execution permissions
    - "test": basic user with commands execution permissions

    It also creates 1 Group: "cmd_group", which defines the commands execution permissions.
    "cmd_user" and "test" users belong to "cmd_group".

    The command receives arguments to set the passwords of the users,
    run `python manage.py createusers --help` for help.
    """

    help = """Django command to create the initial users with their permissions.\n

    It creates 4 users with the following characteristics and permissions:

    - "admin": has all the permissions, it is a Django superuser
    - "user": basic user with no permissions)
    - "cmd_user": basic user with commands execution permissions
    - "test": basic user with commands execution permissions

    It also creates 1 Group: "cmd_group", which defines the commands execution permissions.
    "cmd_user" and "test" users belong to "cmd_group"."""

    requires_migrations_checks = True
    stealth_options = ('stdin',)

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
            '--adminpass',
            help='Specifies the password for the "admin" user.'
        )
        parser.add_argument(
            '--userpass',
            help='Specifies the password for the regular users ("user").'
        )
        parser.add_argument(
            '--cmduserpass',
            help='Specifies password for the users with cmd permissions ("cmd_user" and "test").'
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
        admin_password = options['adminpass']
        user_password = options['userpass']
        cmd_password = options['cmduserpass']
        cmd_password = options['cmduserpass']

        # Create users
        admin = self._create_user(admin_username, admin_password)
        self._create_user(user_username, user_password)
        cmd_user = self._create_user(cmd_user_username, cmd_password)
        test_user = self._create_user(test_username, cmd_password)

        # Make admin superuser and staff
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()

        # Create cmd_group
        cmd_group = self._create_cmd_group()

        # Add cmd_user to cmd_group
        cmd_group.user_set.add(cmd_user)
        cmd_group.user_set.add(test_user)

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
        while password is None or password.strip() == '':
            print('Creating {}...'.format(username))
            password = getpass.getpass()
            if password.strip() == '':
                self.stderr.write("Error: Blank passwords aren't allowed.")
                password = None
                continue

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_user(
                username=username,
                email='{}@fake.com'.format(username),
                password=password
            )
        else:
            self.stderr.write("Warning: The {} user is already created".format(username))
        return user

    def _create_cmd_group(self):
        """Create and return the group of users with permissions to execute commands.

        Returns
        -------
        grouop: Group
            The Group object
        """
        group, created = Group.objects.get_or_create(name=cmd_groupname)
        permissions = Permission.objects.filter(codename='command.execute_command')
        for permission in permissions:
            group.permissions.add(permission)
        return group
