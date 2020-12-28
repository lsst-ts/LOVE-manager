"""Test users' authentication through the API."""
import datetime
import io
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework import status
from api.models import ConfigFile, Token
from django.conf import settings
from manager import utils
from django.core.files.base import ContentFile

#python manage.py test api.tests.tests_configfile.ConfigFileApiTestCase

class ConfigFileApiTestCase(TestCase):
    """Test suite for config files handling."""

    @staticmethod
    def get_config_file_sample(name, content):
        f = ContentFile(content.encode("ascii"), name=name)
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
        self.filename = 'test.json'
        self.content = 'this is the content of the file'
        self.configfile = ConfigFile.objects.create(user=self.user, 
            config_file=ConfigFileApiTestCase.get_config_file_sample("random_filename", self.content),
            file_name=self.filename)
        self.url = reverse("config")
        self.token = Token.objects.create(user=self.user)

    def test_get_config_file(self):
        """Test that an authenticated user can get a config file."""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(reverse("configfile-detail", args=[self.configfile.id]), format="json")
        import pdb; pdb.set_trace()
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "id": self.configfile.id,
            "username": self.user.username, 
            "filename": self.filename, 
        }
        self.assertEqual(response.data["id"], expected_data["id"])
        self.assertEqual(response.data["username"], expected_data["username"])
        self.assertEqual(response.data["filename"], expected_data["filename"])

    def test_get_config_file_content(self):
        """Test that an authenticated user can get a config file content."""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(reverse("configfile-content", args=[self.configfile.id]), format="json")
        import pdb; pdb.set_trace()
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "id": self.configfile.id,
            "content": self.content, 
            "filename": self.filename, 
        }
        self.assertEqual(response.data["id"], expected_data["id"])
        self.assertEqual(response.data["content"], expected_data["content"])
        self.assertEqual(response.data["filename"], expected_data["filename"])

    def test_unauthenticated_cannot_get_config_file(self):
        """Test that an unauthenticated user cannot get the config file."""
        # Act:
        response = self.client.get(self.url, format="json")

        # Assert:
        self.assertEqual(response.status_code, 401)
        self.assertNotEqual(response.data, self.expected_data)
