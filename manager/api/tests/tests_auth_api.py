"""Test users' authentication through the API."""
import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Token
from django.conf import settings
from manager import utils


class AuthApiTestCase(TestCase):
    """Test suite for users' authentication."""

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
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))
        self.user2.user_permissions.add(Permission.objects.get(name="Execute Commands"))
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
            {"username": self.user.username, "email": self.user.email},
            "The user is not as expected",
        )
        self.assertTrue(
            utils.assert_time_data(response.data["time_data"]),
            "Time data is not as expected",
        )
        self.assertEqual(
            response.data["config"],
            self.expected_config,
            "The config was not requested",
        )

    def test_user_login_failed(self):
        """Test that a user cannot request a token if the credentials are invalid."""
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
        """Test that a user can request a token twie receiving different tokens each time."""
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
        response = self.client.post(self.login_url, data, format="json")
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
            {"username": self.user.username, "email": self.user.email,},
            "The user is not as expected",
        )
        self.assertTrue(
            utils.assert_time_data(response.data["time_data"]),
            "Time data is not as expected",
        )
        self.assertEqual(
            response.data["config"],
            self.expected_config,
            "The config was not requested",
        )

    def test_user_validate_token_no_config(self):
        """Test that a user can validate a token and not receive the config passing the no_config query param."""
        # Arrange:
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.login_url, data, format="json")
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
            {"username": self.user.username, "email": self.user.email,},
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
        response = self.client.post(self.login_url, data, format="json")
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
        response = self.client.post(self.login_url, data, format="json")
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
            response = self.client.post(self.login_url, data, format="json")
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
        response = self.client.post(self.login_url, data, format="json")
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
        response = self.client.post(self.swap_url, data, format="json")
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
            response.data["config"], self.expected_config,
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
        response = self.client.delete(self.logout_url, format="json")
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
