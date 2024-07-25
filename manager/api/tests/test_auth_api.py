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


"""Test users' authentication through the API."""
import datetime
import json
from unittest.mock import patch

import ldap
from api.models import ConfigFile, Token
from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from manager import utils

LDAP_USERNAME = "ldap_user"
LDAP_USERNAME_NON_COMMANDS = "ldap_user_non_commands"
LDAP_USERNAME_EXISTENT = "ldap_user_existent"
LDAP_SEARCH_RESPONSE = [
    [
        None,
        {"memberUid": [bytes(LDAP_USERNAME, encoding="utf-8"), b"user2", b"user3"]},
    ],
]


class MockLDAPUser:
    _username = LDAP_USERNAME

    def authenticate(self, password):
        aux_user = User.objects.filter(username=self._username).first()
        if aux_user is None:
            ldap_user = User.objects.create_user(
                username=self._username,
                password=password,
                email=f"{self._username}@user.cl",
                first_name="First",
                last_name="Last",
            )
            return ldap_user
        return aux_user


class MockLDAPUserCommands(MockLDAPUser):
    _username = LDAP_USERNAME


class MockLDAPUserNonCommands(MockLDAPUser):
    _username = LDAP_USERNAME_NON_COMMANDS


class MockLDAPUserExistent(MockLDAPUser):
    _username = LDAP_USERNAME_EXISTENT


class AuthApiTestCase(TestCase):
    """Test suite for users' authentication."""

    @staticmethod
    def get_config_file_sample(name, content):
        f = ContentFile(json.dumps(content).encode("ascii"), name=name)
        return f

    def setUp(self):
        """Define the test suite setup."""
        # Arrange:
        self.client = APIClient()
        self.username = "test"
        self.username2 = "test2"
        self.password = "password"
        self.user = User.objects.create_user(
            username=self.username,
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.user2 = User.objects.create_user(
            username=self.username2,
            password="password",
            email="test2@user.cl",
            first_name="First2",
            last_name="Last2",
        )
        self.user_ldap = User.objects.create_user(
            username=LDAP_USERNAME_EXISTENT,
            password="password",
            email="user_ldap@user.cl",
            first_name="First LDAP",
            last_name="Last LDAP",
        )
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))
        self.user2.user_permissions.add(Permission.objects.get(name="Execute Commands"))

        # Create cmd Group and add existent LDAP user
        cmd_group = Group.objects.create(name="cmd")
        cmd_group.permissions.add(Permission.objects.get(name="Execute Commands"))
        cmd_group.user_set.add(self.user_ldap)

        # Create ui_framework Group and add existent LDAP user
        ui_framework_group = Group.objects.create(name="ui_framework")
        permissions = Permission.objects.filter(
            content_type__app_label__contains="ui_framework"
        )
        for permission in permissions:
            ui_framework_group.permissions.add(permission)
        ui_framework_group.user_set.add(self.user_ldap)

        self.login_url = reverse("login")
        self.validate_token_url = reverse("validate-token")
        self.validate_token_no_config_url = reverse(
            "validate-token", kwargs={"flags": "no_config"}
        )
        self.logout_url = reverse("logout")
        self.swap_url = reverse("swap-user")
        self.swap_no_config_url = reverse("swap-user", kwargs={"flags": "no_config"})
        self.expected_permissions = {
            "execute_commands": True,
        }
        self.expected_config = {"setting1": {"setting11": 1, "setting12": 2}}

        self.filename = "test.json"
        self.content = {"key1": "this is the content of the file"}
        self.configfile = ConfigFile.objects.create(
            user=self.user,
            config_file=AuthApiTestCase.get_config_file_sample(
                "random_filename", self.content
            ),
            file_name=self.filename,
        )

    def test_user_login(self):
        """Test that a user can request a token using name and password."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        tokens_num_0 = Token.objects.filter(user__username=self.username).count()

        # Act:
        response = self.client.post(self.login_url, data, format="json")

        # Assert:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(
            tokens_num_0 + 1, tokens_num, "The user should have a new token"
        )
        tokens_in_db = [
            t.key for t in Token.objects.filter(user__username=self.username)
        ]
        retrieved_token = response.data["token"]
        self.assertTrue(
            retrieved_token in tokens_in_db, "The token should be in the DB"
        )
        self.assertEqual(
            response.data["permissions"],
            self.expected_permissions,
            "The permissions are not as expected",
        )

        self.assertEqual(
            response.data["user"],
            {
                "username": self.user.username,
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            },
            "The user is not as expected",
        )
        self.assertTrue(
            utils.assert_time_data(response.data["time_data"]),
            "Time data is not as expected",
        )
        self.assertEqual(
            response.data["config"]["filename"],
            self.filename,
            "The config was not requested",
        )

    @patch("api.views.AUTH_LDAP_1_SERVER_URI", return_value="ldap://test/")
    @patch("django_auth_ldap.backend._LDAPUser", return_value=MockLDAPUserCommands())
    @patch("ldap.initialize", return_value=ldap.ldapobject.LDAPObject("ldap://test/"))
    @patch("ldap.ldapobject.LDAPObject.search_s", return_value=LDAP_SEARCH_RESPONSE)
    def test_ldap_nonexistent_cmd_user_login(
        self, mockLDAPObject, mockLDAPInitialize, mockLDAPUser, mockLDAPServerUri
    ):
        # Arrange:
        data = {"username": LDAP_USERNAME, "password": "password"}
        total_users_before = User.objects.count()

        # Act:
        with self.settings(
            AUTHENTICATION_BACKENDS=[
                "api.views.IPABackend1",
                "django.contrib.auth.backends.ModelBackend",
            ]
        ):
            response = self.client.post(self.login_url, data, format="json")
            user = User.objects.filter(username=LDAP_USERNAME).first()
            user_group_cmd = user.groups.filter(name="cmd").first()
            user_group_ui_framework = user.groups.filter(name="ui_framework").first()

        total_users_after = User.objects.count()

        # Assert:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_users_before + 1, total_users_after)
        self.assertEqual(user_group_cmd.name, "cmd")
        self.assertEqual(user_group_ui_framework.name, "ui_framework")

    @patch("api.views.AUTH_LDAP_1_SERVER_URI", return_value="ldap://test/")
    @patch("django_auth_ldap.backend._LDAPUser", return_value=MockLDAPUserExistent())
    @patch("ldap.initialize", return_value=ldap.ldapobject.LDAPObject("ldap://test/"))
    @patch("ldap.ldapobject.LDAPObject.search_s", return_value=LDAP_SEARCH_RESPONSE)
    def test_ldap_existent_cmd_user_login(
        self, mockLDAPObject, mockLDAPInitialize, mockLDAPUser, mockLDAPServerUri
    ):
        # Arrange:
        data = {"username": LDAP_USERNAME_EXISTENT, "password": "password"}
        total_users_before = User.objects.count()

        # Act:
        with self.settings(
            AUTHENTICATION_BACKENDS=[
                "api.views.IPABackend1",
                "django.contrib.auth.backends.ModelBackend",
            ]
        ):
            response = self.client.post(self.login_url, data, format="json")
            user = User.objects.filter(username=LDAP_USERNAME_EXISTENT).first()
            user_group_cmd = user.groups.filter(name="cmd").first()
            user_group_ui_framework = user.groups.filter(name="ui_framework").first()

        total_users_after = User.objects.count()

        # Assert:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_users_before, total_users_after)
        self.assertEqual(user_group_cmd.name, "cmd")
        self.assertEqual(user_group_ui_framework.name, "ui_framework")

    @patch("api.views.AUTH_LDAP_1_SERVER_URI", return_value="ldap://test/")
    @patch("django_auth_ldap.backend._LDAPUser", return_value=MockLDAPUserNonCommands())
    @patch("ldap.initialize", return_value=ldap.ldapobject.LDAPObject("ldap://test/"))
    @patch(
        "ldap.ldapobject.LDAPObject.search_s",
        return_value=LDAP_SEARCH_RESPONSE,
    )
    def test_ldap_nonexistent_non_cmd_user_login(
        self, mockLDAPObject, mockLDAPInitialize, mockLDAPUserNonCmd, mockLDAPServerUri
    ):
        # Arrange:
        data = {"username": LDAP_USERNAME_NON_COMMANDS, "password": "password"}
        total_users_before = User.objects.count()

        # Act:
        with self.settings(
            AUTHENTICATION_BACKENDS=[
                "api.views.IPABackend1",
                "django.contrib.auth.backends.ModelBackend",
            ]
        ):
            response = self.client.post(self.login_url, data, format="json")
            user = User.objects.filter(username=LDAP_USERNAME_NON_COMMANDS).first()

        total_users_after = User.objects.count()

        # Assert:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_users_before + 1, total_users_after)
        self.assertEqual(user.groups.count(), 0)

    def test_user_login_failed(self):
        """Test that a user cannot request a token
        if the credentials are invalid."""
        # Arrange:
        data = {"username": self.username, "password": "wrong-password"}
        tokens_num_0 = Token.objects.filter(user__username=self.username).count()

        # Act:
        response = self.client.post(self.login_url, data, format="json")

        # Assert:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tokens_num_1 = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num_0, tokens_num_1, "The user should have no token")

    def test_user_login_twice(self):
        """Test that a user can request a token
        twice receiving different tokens each time."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        tokens_num_0 = Token.objects.filter(user__username=self.username).count()

        # Act 1:
        response = self.client.post(self.login_url, data, format="json")

        # Assert 1:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens_num_1 = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(
            tokens_num_0 + 1, tokens_num_1, "The user should have a new token"
        )
        retrieved_token_1 = response.data["token"]
        tokens_in_db = [
            t.key for t in Token.objects.filter(user__username=self.username)
        ]
        self.assertTrue(
            retrieved_token_1 in tokens_in_db, "The token should be in the DB"
        )

        # Act 2:
        response = self.client.post(self.login_url, data, format="json")

        # Assert after request 2:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens_num_2 = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(
            tokens_num_1 + 1, tokens_num_2, "The user should have another new token"
        )
        retrieved_token_2 = response.data["token"]
        tokens_in_db = [
            t.key for t in Token.objects.filter(user__username=self.username)
        ]
        self.assertTrue(
            retrieved_token_1 in tokens_in_db, "The token should be in the DB"
        )
        self.assertNotEqual(
            retrieved_token_1, retrieved_token_2, "The tokens should be different"
        )

    def test_user_validate_token(self):
        """Test that a user can validate a token."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        self.client.post(self.login_url, data, format="json")
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        # Act:
        response = self.client.get(self.validate_token_url, data, format="json")

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["token"], token.key, "The response is not as expected"
        )
        self.assertEqual(
            response.data["permissions"],
            self.expected_permissions,
            "The permissions are not as expected",
        )
        self.assertEqual(
            response.data["user"],
            {
                "username": self.user.username,
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            },
            "The user is not as expected",
        )
        self.assertTrue(
            utils.assert_time_data(response.data["time_data"]),
            "Time data is not as expected",
        )
        self.assertEqual(
            response.data["config"]["filename"],
            self.filename,
            "The config was not requested",
        )

    def test_user_validate_token_no_config(self):
        """Test that a user can validate a token
        and not receive the config passing the no_config query param."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        self.client.post(self.login_url, data, format="json")
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        # Act:
        print("self.validate_token_no_config_url: ", self.validate_token_no_config_url)
        response = self.client.get(
            self.validate_token_no_config_url, data, format="json"
        )

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["token"], token.key, "The response is not as expected"
        )
        self.assertEqual(
            response.data["permissions"],
            self.expected_permissions,
            "The permissions are not as expected",
        )
        self.assertEqual(
            response.data["user"],
            {
                "username": self.user.username,
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            },
            "The user is not as expected",
        )
        self.assertTrue(
            utils.assert_time_data(response.data["time_data"]),
            "Time data is not as expected",
        )
        self.assertEqual(response.data["config"], None, "The config was requested")

    def test_user_validate_token_fail(self):
        """Test that a user fails to validate an invalid token."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        self.client.post(self.login_url, data, format="json")
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key + "fake")

        # Act:
        response = self.client.get(self.validate_token_url, data, format="json")

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_fails_to_validate_deleted_token(self):
        """Test that a user fails to validate an deleted token."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        self.client.post(self.login_url, data, format="json")
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        token.delete()

        # Act:
        response = self.client.get(self.validate_token_url, format="json")

        # Assert:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_fails_to_validate_expired_token(self):
        """Test that a user fails to validate an expired token."""
        # Arrange:
        initial_time = datetime.datetime.now()
        with freeze_time(initial_time) as frozen_datetime:
            data = {"username": self.username, "password": self.password}
            self.client.post(self.login_url, data, format="json")
            token = Token.objects.filter(user__username=self.username).first()
            token_num_0 = Token.objects.filter(user__username=self.username).count()
            self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

            # Act:
            max_timedelta = datetime.timedelta(
                days=settings.TOKEN_EXPIRED_AFTER_DAYS, seconds=1
            )
            frozen_datetime.tick(delta=max_timedelta)
            response = self.client.get(self.validate_token_url, format="json")

            # Assert:
            token_num_1 = Token.objects.filter(user__username=self.username).count()
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(token_num_0 - 1, token_num_1)

    def test_user_logout(self):
        """Test that a user can logout and delete the token."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        self.client.post(self.login_url, data, format="json")
        token = Token.objects.filter(user__username=self.username).first()
        old_tokens_count = Token.objects.filter(user__username=self.username).count()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        # Act:
        response = self.client.delete(self.logout_url, format="json")

        # Assert:
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            response.data,
            {"detail": "Logout successful, Token succesfully deleted"},
            "The response is not as expected",
        )
        new_tokens_count = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(
            old_tokens_count - 1, new_tokens_count, "The token was not deleted"
        )

    def test_user_swap(self):
        """Test that a logged user can be swapped"""
        # Arrange login:
        data = {"username": self.username, "password": self.password}
        user_1_tokens_num_0 = Token.objects.filter(user__username=self.username).count()
        user_2_tokens_num_0 = Token.objects.filter(
            user__username=self.username2
        ).count()
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Act:
        data = {"username": self.username2, "password": self.password}
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        self.client.post(self.swap_url, data, format="json")
        user_1_tokens_num_1 = Token.objects.filter(user__username=self.username).count()
        user_2_tokens_num_1 = Token.objects.filter(
            user__username=self.username2
        ).count()
        # Assert:
        self.assertEqual(
            user_1_tokens_num_1,
            user_1_tokens_num_0,
            "User 1 has the same number of tokens as before logging in",
        )
        self.assertEqual(
            user_2_tokens_num_1, user_2_tokens_num_0 + 1, "User 2 has one more token"
        )
        # Act 2:
        token = Token.objects.filter(user__username=self.username2).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.get(self.validate_token_url)
        # Assert 2:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["config"]["filename"],
            self.filename,
            "The config was not requested",
        )

    def test_user_swap_no_config(self):
        """Test that a logged user can be swapped and not request config"""
        # Arrange login:
        data = {"username": self.username, "password": self.password}
        user_1_tokens_num_0 = Token.objects.filter(user__username=self.username).count()
        user_2_tokens_num_0 = Token.objects.filter(
            user__username=self.username2
        ).count()
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Act:
        data = {"username": self.username2, "password": self.password}
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.post(self.swap_no_config_url, data, format="json")
        user_1_tokens_num_1 = Token.objects.filter(user__username=self.username).count()
        user_2_tokens_num_1 = Token.objects.filter(
            user__username=self.username2
        ).count()
        # Assert:
        self.assertEqual(
            user_1_tokens_num_1,
            user_1_tokens_num_0,
            "User 1 has the same number of tokens as before logging in",
        )
        self.assertEqual(
            user_2_tokens_num_1, user_2_tokens_num_0 + 1, "User 2 has one more token"
        )
        self.assertEqual(response.data["config"], None, "The config was requested")
        # Act 2:
        token = Token.objects.filter(user__username=self.username2).first()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.get(self.validate_token_no_config_url)
        # Assert 2:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["config"], None, "The config was requested")

    def test_user_swap_forbidden(self):
        """Test that a user that's not logged in cannot swap users"""
        # Arrange logout:
        self.client.delete(self.logout_url, format="json")
        self.client.logout()
        data = {"username": self.username, "password": self.password}
        # Act:
        response = self.client.post(self.swap_url, data, format="json")
        # Assert:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_swap_wrong_credentials(self):
        """Test that a user that's not logged in cannot swap users"""
        # Arrange login:
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Act swap with wrong credentials:
        data = {"username": self.username, "password": "wrong_password"}
        response = self.client.post(self.swap_url, data, format="json")
        # Assert:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
