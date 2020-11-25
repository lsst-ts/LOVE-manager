from django.test import TestCase, override_settings
from django.urls import reverse
from api.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission
import yaml
from unittest.mock import patch, call


@override_settings(DEBUG=True)
class LOVECscTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
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
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_view"),
            Permission.objects.get(codename="add_view"),
            Permission.objects.get(codename="delete_view"),
            Permission.objects.get(codename="change_view"),
        )

    @patch(
        "os.environ.get",
        side_effect=lambda arg: "fakehost"
        if arg == "COMMANDER_HOSTNAME"
        else "fakeport",
    )
    @patch("requests.post")
    def test_authorized_lovecsc_data(self, mock_requests, mock_environ):
        """Test authorized user commander data is sent to love-commander"""
        # Arrange:
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))

        # Act:
        url = reverse("love-csc")
        data = {
            "user": "an user",
            "message": "a message",
        }

        with self.assertRaises(ValueError):
            response = self.client.post(url, data, format="json")
        fakehostname = "fakehost"
        fakeport = "fakeport"
        expected_url = f"http://fakehost:fakeport/lovecsc"
        self.assertEqual(mock_requests.call_args, call(expected_url, json=data))

    @patch(
        "os.environ.get",
        side_effect=lambda arg: "fakehost"
        if arg == "COMMANDER_HOSTNAME"
        else "fakeport",
    )
    @patch("requests.post")
    def test_unauthorized_lovecsc(self, mock_requests, mock_environ):
        """Test an unauthorized user can't send commands"""
        # Act:
        url = reverse("love-csc")
        data = {
            "user": "an user",
            "message": "a message",
        }

        response = self.client.post(url, data, format="json")
        result = response.json()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            result, {"ack": "User does not have permissions to send observing logs."}
        )
