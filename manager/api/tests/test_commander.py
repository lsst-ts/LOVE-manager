from django.test import TestCase, override_settings
from django.urls import reverse
from api.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission
import yaml
from unittest.mock import patch, call

#python manage.py test api.tests.test_commander.CommanderTestCase
#python manage.py test api.tests.test_commander.SalinfoTestCase
#python manage.py test api.tests.test_commander.EFDTestCase

@override_settings(DEBUG=True)
class CommanderTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
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
    def test_authorized_commander_data(self, mock_requests, mock_environ):
        """Test authorized user commander data is sent to love-commander"""
        # Arrange:
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))

        # Act:
        url = reverse("commander")
        data = {
            "csc": "Test",
            "salindex": 1,
            "cmd": "cmd_setScalars",
            "params": {"a": 1, "b": 2},
        }

        with self.assertRaises(ValueError):
            self.client.post(url, data, format="json")
        expected_url = f"http://fakehost:fakeport/cmd"
        self.assertEqual(mock_requests.call_args, call(expected_url, json=data))

    @patch(
        "os.environ.get",
        side_effect=lambda arg: "fakehost"
        if arg == "COMMANDER_HOSTNAME"
        else "fakeport",
    )
    @patch("requests.post")
    def test_unauthorized_commander(self, mock_requests, mock_environ):
        """Test an unauthorized user can't send commands"""
        # Act:
        url = reverse("commander")
        data = {
            "csc": "Test",
            "salindex": 1,
            "cmd": "cmd_setScalars",
            "params": {"a": 1, "b": 2},
        }

        response = self.client.post(url, data, format="json")
        result = response.json()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            result, {"ack": "User does not have permissions to execute commands."}
        )


@override_settings(DEBUG=True)
class SalinfoTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
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
    @patch("requests.get")
    def test_salinfo_metadata(self, mock_requests, mock_environ):
        """Test authorized user can get salinfo metadata"""
        # Act:
        url = reverse("salinfo-metadata")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = f"http://fakehost:fakeport/salinfo/metadata"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch(
        "os.environ.get",
        side_effect=lambda arg: "fakehost"
        if arg == "COMMANDER_HOSTNAME"
        else "fakeport",
    )
    @patch("requests.get")
    def test_salinfo_topic_names(self, mock_requests, mock_environ):
        """Test authorized user can get salinfo topic_names"""
        # Act:
        url = reverse("salinfo-topic-names")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = f"http://fakehost:fakeport/salinfo/topic-names"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch(
        "os.environ.get",
        side_effect=lambda arg: "fakehost"
        if arg == "COMMANDER_HOSTNAME"
        else "fakeport",
    )
    @patch("requests.get")
    def test_salinfo_topic_names_with_param(self, mock_requests, mock_environ):
        """Test authorized user can get salinfo topic_names with query param"""
        # Act:
        url = reverse("salinfo-topic-names") + "?categories=telemetry"

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = (
            f"http://fakehost:fakeport/salinfo/topic-names?categories=telemetry"
        )
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch(
        "os.environ.get",
        side_effect=lambda arg: "fakehost"
        if arg == "COMMANDER_HOSTNAME"
        else "fakeport",
    )
    @patch("requests.get")
    def test_salinfo_topic_data(self, mock_requests, mock_environ):
        """Test authorized user can get salinfo topic_data"""
        # Act:
        url = reverse("salinfo-topic-data")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = f"http://fakehost:fakeport/salinfo/topic-data"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch(
        "os.environ.get",
        side_effect=lambda arg: "fakehost"
        if arg == "COMMANDER_HOSTNAME"
        else "fakeport",
    )
    @patch("requests.get")
    def test_salinfo_topic_data_with_param(self, mock_requests, mock_environ):
        """Test authorized user can get salinfo topic_data with query param"""
        # Act:
        url = reverse("salinfo-topic-data") + "?categories=telemetry"

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = (
            f"http://fakehost:fakeport/salinfo/topic-data?categories=telemetry"
        )
        self.assertEqual(mock_requests.call_args, call(expected_url))


@override_settings(DEBUG=True)
class EFDTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
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
    @patch("requests.get")
    def test_timeseries_query(self, mock_requests, mock_environ):
        """Test authorized user can query and get a timeseries"""
        # Act:
        kwargs = {}
        url = reverse("EFD-timeseries")

        with self.assertRaises(ValueError):
            self.client.get(url, **kwargs)
        expected_url = f"http://fakehost:fakeport/EFD/timeseries/"
        self.assertEqual(mock_requests.call_args, call(expected_url, kwargs=kwargs))
