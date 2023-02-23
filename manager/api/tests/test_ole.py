import requests
from unittest.mock import patch
from api.models import Token
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@override_settings(DEBUG=True)
class OLETestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()

        user_normal_obj = {
            "username": "user-normal",
            "password": "password",
            "email": "test@user.cl",
            "first_name": "user-normal",
            "last_name": "",
        }
        self.user_normal = User.objects.create_user(
            username=user_normal_obj["username"],
            password=user_normal_obj["password"],
            email=user_normal_obj["email"],
            first_name=user_normal_obj["first_name"],
            last_name=user_normal_obj["last_name"],
        )
        self.token_user_normal = Token.objects.create(user=self.user_normal)

        payload_shared = {
            "message_text": "Lorem ipsum",
            "user_id": "love@localhost",
            "user_agent": "LOVE",
            "tags": "tag1, tag2",
        }

        payload_exposure = {
            "obs_id": "AT_O_20220208_000140",
            "instrument": "LATISS",
            "exposure_flag": "none",
        }

        payload_narrative = {
            "systems": "MainTel",
            "subsystems": "Camera",
            "cscs": "M1M3",
            "date_begin": "202200703-19:58:13",
            "date_end": "20220704-19:25:13",
            "time_lost": 10,
            "level": 0,
        }

        self.payload_full_exposure = {
            **payload_shared,
            **payload_exposure,
            "request_type": "exposure",
        }

        self.payload_full_narrative = {
            **payload_shared,
            **payload_narrative,
            "request_type": "narrative",
        }

    def test_exposurelog_list(self):
        """Test exposurelog list."""
        # Arrange:
        mock_ole_patcher = patch("requests.get")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: []
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("ExposureLogs-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_simple_exposurelog_create(self):
        """Test exposurelog create."""
        # Arrange:
        mock_ole_patcher = patch("requests.post")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: {}
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("ExposureLogs-list")
        response = self.client.post(url, self.payload_full_exposure)
        self.assertEqual(response.status_code, 201)

    def test_exposurelog_update(self):
        """Test exposurelog update."""
        # Arrange:
        mock_ole_patcher = patch("requests.patch")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: {}
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("ExposureLogs-detail", args=[1])
        response = self.client.put(url, self.payload_full_exposure)
        self.assertEqual(response.status_code, 200)

    def test_narrativelog_list(self):
        """Test narrativelog list."""
        # Arrange:
        mock_ole_patcher = patch("requests.get")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: []
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NarrativeLogs-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_simple_narrativelog_create(self):
        """Test narrativelog create."""
        # Arrange:
        mock_ole_patcher = patch("requests.post")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: {}
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NarrativeLogs-list")
        response = self.client.post(url, self.payload_full_narrative)
        self.assertEqual(response.status_code, 201)

    def test_narrativelog_update(self):
        """Test narrativelog update."""
        # Arrange:
        mock_ole_patcher = patch("requests.patch")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: {}
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NarrativeLogs-detail", args=[1])
        response = self.client.put(url, self.payload_full_narrative)
        self.assertEqual(response.status_code, 200)
