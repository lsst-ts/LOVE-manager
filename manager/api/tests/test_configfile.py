"""Test users' authentication through the API."""
import json
import requests
import tempfile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import ConfigFile, Token
from django.conf import settings
from django.core.files.base import ContentFile
from unittest import mock


# python manage.py test api.tests.tests_configfile.ConfigFileApiTestCase


def setUp(self):
    settings.MEDIA_ROOT = tempfile.mkdtemp()


class ConfigFileApiTestCase(TestCase):
    """Test suite for config files handling."""

    @staticmethod
    def get_config_file_sample(name, content):
        f = ContentFile(json.dumps(content).encode("ascii"), name=name)
        return f

    def setUp(self):
        """Define the test suite setup."""
        # Arrange:

        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.token = Token.objects.create(user=self.user)
        self.url = reverse("config")

        self.local_config_file_content = {
            "key1": "this is the content of the local file"
        }
        self.local_config_file = ConfigFile.objects.create(
            user=self.user,
            config_file=ConfigFileApiTestCase.get_config_file_sample(
                "random_local_filename.json",
                self.local_config_file_content,
            ),
            file_name="random_local_filename.json",
        )

        self.remote_config_file_content = {
            "key1": "this is the content of the remote file"
        }
        self.remote_config_file = ConfigFile.objects.create(
            user=self.user,
            config_file=ConfigFileApiTestCase.get_config_file_sample(
                "http://foo.bar/LOVE/CONFIG/random_remote_filename.json",
                self.remote_config_file_content,
            ),
            file_name="random_remote_filename.json",
        )
        # Need to overwrite config file name to match the one in the remote server
        self.remote_config_file.config_file.name = (
            self.remote_config_file.config_file.name.replace("configs/", "")
        )
        self.remote_config_file.save()

    def test_get_config_files_list(self):
        """Test that an authenticated user can get a config file."""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(reverse("configfile-list"), format="json")
        self.assertEqual(response.status_code, 200)
        # Querying the configfile-list endpoints
        # retrieves the list of config files in descending timestamp order
        expected_data = [
            {
                "id": self.remote_config_file.id,
                "username": self.user.username,
                "filename": self.remote_config_file.file_name,
            },
            {
                "id": self.local_config_file.id,
                "username": self.user.username,
                "filename": self.local_config_file.file_name,
            },
        ]
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["filename"], expected_data[0]["filename"])
        self.assertEqual(response.data[1]["filename"], expected_data[1]["filename"])

    def test_get_config_file(self):
        """Test that an authenticated user can get a config file."""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(
            reverse("configfile-detail", args=[self.local_config_file.id]),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "id": self.local_config_file.id,
            "username": self.user.username,
            "filename": self.local_config_file.file_name,
        }
        self.assertEqual(response.data["id"], expected_data["id"])
        self.assertEqual(response.data["username"], expected_data["username"])
        self.assertEqual(response.data["filename"], expected_data["filename"])

    def test_get_config_file_content(self):
        """Test that an authenticated user can get a config file content."""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(
            reverse("configfile-content", args=[self.local_config_file.id]),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "id": self.local_config_file.id,
            "content": self.local_config_file_content,
            "filename": self.local_config_file.file_name,
        }
        self.assertEqual(response.data["id"], expected_data["id"])
        self.assertEqual(response.data["content"], expected_data["content"])
        self.assertEqual(response.data["filename"], expected_data["filename"])

    @override_settings(DEFAULT_FILE_STORAGE="manager.utils.RemoteStorage")
    def test_get_config_file_content_with_remote_storage(self):
        """Test that an authenticated user can get a config file content."""
        mock_requests_get = mock.patch("requests.get")
        mock_requests_get_client = mock_requests_get.start()
        response_requests_get = requests.Response()
        response_requests_get.status_code = 200
        response_requests_get.json = lambda: self.remote_config_file_content
        mock_requests_get_client.return_value = response_requests_get

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(
            reverse("configfile-content", args=[self.remote_config_file.id]),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "id": self.remote_config_file.id,
            "content": self.remote_config_file_content,
            "filename": self.remote_config_file.file_name,
        }
        self.assertEqual(response.data["id"], expected_data["id"])
        self.assertEqual(response.data["content"], expected_data["content"])
        self.assertEqual(response.data["filename"], expected_data["filename"])

        mock_requests_get.stop()

    def test_unauthenticated_cannot_get_config_file(self):
        """Test that an unauthenticated user cannot get the config file."""
        # Act:
        response = self.client.get(self.url, format="json")

        # Assert:
        self.assertEqual(response.status_code, 401)
