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
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def test_get_config(self):
        """Test that a user can get the config file."""
        # Arrange:

        # Act:
        url = reverse("config")
        response = self.client.get(url, format="json")

        # Assert:
        expected_data = {
            "alarm_sounds": {"critical": "true", "serious": "true", "warning": "false"}
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)
