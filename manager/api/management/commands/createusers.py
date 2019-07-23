"""Management utility to create operator on duty user."""
import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group, User
from django.core.management.base import BaseCommand

PASSWORD_FIELD = 'password'
username = 'operator_on_duty'
operators_group_name = 'operators'

user_username = 'user'
cmd_user_username = 'cmd_user'
admin_username = 'admin'
cmd_groupname = 'cmd'


class Command(BaseCommand):
    """The Django command to create the initial users with their permissions."""

    help = 'Creates the initial users'
    requires_migrations_checks = True
    stealth_options = ('stdin',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(
            self.UserModel.USERNAME_FIELD)

    def add_arguments(self, parser):
        """Add arguments for the command.

        Params
        ------
        parser: object
            parser for the arguments
        """
        parser.add_argument(
            '--adminpass',
            help='Specifies the password for the admin user.'
        )
        parser.add_argument(
            '--userpass',
            help='Specifies the password for the regular user, "user".'
        )
        parser.add_argument(
            '--cmduserpass',
            help='Specifies password for the user with cmd permissions, "cmd_user".'
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

        # Create admin
        self._create_admin(admin_password)

        # Create user
        self._create_user(user_username, user_password)

        # Create cmd_user
        cmd_user = self._create_user(cmd_user_username, cmd_password)

        # Create cmd_group
        cmd_group = self._create_cmd_group()

        # Add cmd_user to cmd_group
        cmd_group.user_set.add(cmd_user)

    def _create_admin(self, password):
        """Create the admin user, if it does not exist. Return it anyway.

        Params
        ------
        password: string
            The password for the user

        Returns
        -------
        user: User
            The User object
        """
        while password is None or password.strip() == '':
            print('Creating admin user...')
            password = getpass.getpass()
            if password.strip() == '':
                self.stderr.write("Error: Blank passwords aren't allowed.")
                password = None
                continue

        user = User.objects.filter(username=admin_username).first()
        if not user:
            user = User.objects.create_superuser(
                username=admin_username,
                email='{}@fake.com'.format(admin_username),
                password=password
            )
        else:
            self.stderr.write("Error: The {} user is already created".format(admin_username))
        return user

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
            self.stderr.write("Error: The {} user is already created".format(username))
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