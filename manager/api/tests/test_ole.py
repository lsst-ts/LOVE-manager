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


from unittest.mock import patch

import requests
import rest_framework.response
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
            "request_type": "exposure",
            "obs_id": "AT_O_20220208_000140",
            "instrument": "LATISS",
            "exposure_flag": "none",
        }

        payload_narrative = {
            "request_type": "narrative",
            "components": "MainTel",
            "primary_software_components": "None",
            "primary_hardware_components": "None",
            "date_begin": "202200703-19:58:13",
            "date_end": "20220704-19:25:13",
            "time_lost": 10,
            "level": 0,
        }

        payload_jira_new = {
            "jira": "true",
            "jira_new": "true",
            "jira_issue_title": "Issue title",
        }

        payload_jira_comment = {
            "jira": "true",
            "jira_new": "false",
            "jira_issue_id": "LOVE-1234",
        }

        self.payload_full_exposure = {
            **payload_shared,
            **payload_exposure,
        }

        self.payload_full_narrative = {
            **payload_shared,
            **payload_narrative,
        }

        self.payload_full_exposure_with_jira_new = {
            **self.payload_full_exposure,
            **payload_jira_new,
        }

        self.payload_full_exposure_with_jira_comment = {
            **self.payload_full_exposure,
            **payload_jira_comment,
        }

        self.payload_full_narrative_with_jira_new = {
            **self.payload_full_narrative,
            **payload_jira_new,
        }

        self.payload_full_narrative_with_jira_comment = {
            **self.payload_full_narrative,
            **payload_jira_comment,
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

    def test_exposurelog_create_with_jira(self):
        """Test exposurelog create with jira."""
        # Arrange:
        mock_jira_ticket_patcher = patch("manager.utils.jira_ticket")
        mock_jira_ticket_client = mock_jira_ticket_patcher.start()
        response_jira_new = rest_framework.response.Response()
        response_jira_new.status_code = 200
        response_jira_new.data = {
            "ack": "Jira ticket created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_ticket_client.return_value = response_jira_new

        mock_jira_comment_patcher = patch("manager.utils.jira_comment")
        mock_jira_comment_client = mock_jira_comment_patcher.start()
        response_jira_comment = rest_framework.response.Response()
        response_jira_comment.status_code = 200
        response_jira_comment.data = {
            "ack": "Jira comment created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_comment_client.return_value = response_jira_comment

        mock_ole_patcher = patch("requests.post")
        mock_ole_client = mock_ole_patcher.start()
        response_ole = requests.Response()
        response_ole.status_code = 201
        response_ole.json = lambda: {}
        mock_ole_client.return_value = response_ole

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        # New jira ticket
        url = reverse("ExposureLogs-list")
        response = self.client.post(url, self.payload_full_exposure_with_jira_new)
        self.assertEqual(response.status_code, 201)

        # Existent jira ticket
        url = reverse("ExposureLogs-list")
        response = self.client.post(url, self.payload_full_exposure_with_jira_comment)
        self.assertEqual(response.status_code, 201)

    def test_exposurelog_update_with_jira(self):
        """Test exposurelog update with jira."""
        # Arrange:
        mock_jira_ticket_patcher = patch("manager.utils.jira_ticket")
        mock_jira_ticket_client = mock_jira_ticket_patcher.start()
        response_jira_new = rest_framework.response.Response()
        response_jira_new.status_code = 200
        response_jira_new.data = {
            "ack": "Jira ticket created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_ticket_client.return_value = response_jira_new

        mock_jira_comment_patcher = patch("manager.utils.jira_comment")
        mock_jira_comment_client = mock_jira_comment_patcher.start()
        response_jira_comment = rest_framework.response.Response()
        response_jira_comment.status_code = 200
        response_jira_comment.data = {
            "ack": "Jira comment created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_comment_client.return_value = response_jira_comment

        mock_ole_patcher = patch("requests.patch")
        mock_ole_client = mock_ole_patcher.start()
        response_ole = requests.Response()
        response_ole.status_code = 200
        response_ole.json = lambda: {}
        mock_ole_client.return_value = response_ole

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        # New jira ticket
        url = reverse("ExposureLogs-detail", args=[1])
        response = self.client.put(url, self.payload_full_exposure_with_jira_new)
        self.assertEqual(response.status_code, 200)

        # Existent jira ticket
        url = reverse("ExposureLogs-detail", args=[1])
        response = self.client.put(url, self.payload_full_exposure_with_jira_comment)
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

    def test_narrative_log_create_with_jira(self):
        """Test narrativelog create with jira."""
        # Arrange:
        mock_jira_ticket_patcher = patch("manager.utils.jira_ticket")
        mock_jira_ticket_client = mock_jira_ticket_patcher.start()
        response_jira_new = rest_framework.response.Response()
        response_jira_new.status_code = 200
        response_jira_new.data = {
            "ack": "Jira ticket created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_ticket_client.return_value = response_jira_new

        mock_jira_comment_patcher = patch("manager.utils.jira_comment")
        mock_jira_comment_client = mock_jira_comment_patcher.start()
        response_jira_comment = rest_framework.response.Response()
        response_jira_comment.status_code = 200
        response_jira_comment.data = {
            "ack": "Jira comment created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_comment_client.return_value = response_jira_comment

        mock_ole_patcher = patch("requests.post")
        mock_ole_client = mock_ole_patcher.start()
        response_ole = requests.Response()
        response_ole.status_code = 201
        response_ole.json = lambda: {}
        mock_ole_client.return_value = response_ole

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        # New jira ticket
        url = reverse("NarrativeLogs-list")
        response = self.client.post(url, self.payload_full_narrative_with_jira_new)
        self.assertEqual(response.status_code, 201)

        # Existent jira ticket
        url = reverse("NarrativeLogs-list")
        response = self.client.post(url, self.payload_full_narrative_with_jira_comment)
        self.assertEqual(response.status_code, 201)

    def test_narrative_log_update_with_jira(self):
        """Test narrativelog update with jira."""
        # Arrange:
        mock_jira_ticket_patcher = patch("manager.utils.jira_ticket")
        mock_jira_ticket_client = mock_jira_ticket_patcher.start()
        response_jira_new = rest_framework.response.Response()
        response_jira_new.status_code = 200
        response_jira_new.data = {
            "ack": "Jira ticket created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_ticket_client.return_value = response_jira_new

        mock_jira_comment_patcher = patch("manager.utils.jira_comment")
        mock_jira_comment_client = mock_jira_comment_patcher.start()
        response_jira_comment = rest_framework.response.Response()
        response_jira_comment.status_code = 200
        response_jira_comment.data = {
            "ack": "Jira comment created",
            "url": "https://jira.lsstcorp.org/browse/LOVE-1234",
        }
        mock_jira_comment_client.return_value = response_jira_comment

        mock_ole_patcher = patch("requests.patch")
        mock_ole_client = mock_ole_patcher.start()
        response_ole = requests.Response()
        response_ole.status_code = 200
        response_ole.json = lambda: {}
        mock_ole_client.return_value = response_ole

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        # New jira ticket
        url = reverse("NarrativeLogs-detail", args=[1])
        response = self.client.put(url, self.payload_full_narrative_with_jira_new)
        self.assertEqual(response.status_code, 200)

        # Existent jira ticket
        url = reverse("NarrativeLogs-detail", args=[1])
        response = self.client.put(url, self.payload_full_narrative_with_jira_comment)
        self.assertEqual(response.status_code, 200)
