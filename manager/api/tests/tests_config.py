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


class ConfigApiTestCase(TestCase):
    """Test suite for config files handling."""

    def setUp(self):
        """Define the test suite setup."""
        # Arrange:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="an user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.url = reverse("config")
        self.expected_data = {"setting1": {"setting11": 1, "setting12": 2}}
        self.token = Token.objects.create(user=self.user)
        # self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def test_get_config(self):
        """Test that an authenticated user can get the config file."""
        # Arrange
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        # Act:
        response = self.client.get(self.url, format="json")

        # Assert:
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.expected_data)

    def test_unauthenticated_cannot_get_config(self):
        """Test that an unauthenticated user cannot get the config file."""
        # Act:
        response = self.client.get(self.url, format="json")

        # Assert:
        self.assertEqual(response.status_code, 401)
        self.assertNotEqual(response.data, self.expected_data)
