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


import json
from unittest.mock import patch

import requests
import rest_framework.response
from api.models import Token
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from manager.utils import DATETIME_ISO_FORMAT, ERROR_OBS_TICKETS, get_tai_from_utc

OBS_SYSTEMS_HIERARCHY = """
{
  "name": "AuxTel",
  "children": [
    {
      "name": "OCS",
      "children": [
        {
          "name": "ATScheduler CSC"
        }
      ]
    }
  ]
}
"""


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
            "components_json": OBS_SYSTEMS_HIERARCHY,
            "date_begin": "2024-01-01T00:00:00.000000",
            "date_end": "2024-01-01T00:10:00.000000",
            "time_lost": 1,
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

        mock_ole_patcher.stop()

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

        mock_ole_patcher.stop()

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

        mock_ole_patcher.stop()

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

        mock_jira_ticket_patcher.stop()
        mock_jira_comment_patcher.stop()
        mock_ole_patcher.stop()

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

        mock_jira_ticket_patcher.stop()
        mock_jira_comment_patcher.stop()
        mock_ole_patcher.stop()

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

        mock_ole_patcher.stop()

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

        # Assert:
        self.assertEqual(response.status_code, 201)

        # Check the date_begin and date_end arguments
        # are transformed to TAI scale.
        mock_ole_client_json_arg = mock_ole_client.call_args.kwargs["json"].dict()
        date_begin_arg = mock_ole_client_json_arg["date_begin"]
        date_end_arg = mock_ole_client_json_arg["date_end"]
        payload_date_begin_formatted = get_tai_from_utc(
            self.payload_full_narrative["date_begin"]
        ).strftime("%Y-%m-%dT%H:%M:%S.%f")
        payload_date_end_formatted = get_tai_from_utc(
            self.payload_full_narrative["date_end"]
        ).strftime("%Y-%m-%dT%H:%M:%S.%f")
        assert date_begin_arg == payload_date_begin_formatted
        assert date_end_arg == payload_date_end_formatted

        mock_ole_patcher.stop()

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

        # Assert
        self.assertEqual(response.status_code, 200)

        # Check the date_begin and date_end arguments
        # are transformed to TAI scale.
        mock_ole_client_json_arg = mock_ole_client.call_args.kwargs["json"].dict()
        date_begin_arg = mock_ole_client_json_arg["date_begin"]
        date_end_arg = mock_ole_client_json_arg["date_end"]
        payload_date_begin_formatted = get_tai_from_utc(
            self.payload_full_narrative["date_begin"]
        ).strftime(DATETIME_ISO_FORMAT)
        payload_date_end_formatted = get_tai_from_utc(
            self.payload_full_narrative["date_end"]
        ).strftime(DATETIME_ISO_FORMAT)
        assert date_begin_arg == payload_date_begin_formatted
        assert date_end_arg == payload_date_end_formatted

        mock_ole_patcher.stop()

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

        mock_jira_ticket_patcher.stop()
        mock_jira_comment_patcher.stop()
        mock_ole_patcher.stop()

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

        mock_jira_ticket_patcher.stop()
        mock_jira_comment_patcher.stop()
        mock_ole_patcher.stop()

    def test_narrativelog_create_with_not_valid_obs_systems_hierarchy(self):
        """Test narrativelog create with not valid OBS systems hierarchy."""
        # Arrange:
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NarrativeLogs-list")
        with self.assertRaises(json.decoder.JSONDecodeError):
            self.client.post(
                url, {**self.payload_full_narrative, "components_json": "invalid"}
            )


@override_settings(DEBUG=True)
class NightReportTestCase(TestCase):
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

        self.payload = {
            "summary": "summary",
            "weather": "weather summary",
            "maintel_summary": "maintel summary",
            "auxtel_summary": "auxtel summary",
            "confluence_url": "https://localhost/confluence",
            "observers_crew": ["User1", "User2"],
        }

        self.response_report = {
            "id": "e75b07b6-a422-4cd7-99fc-95b0046645b0",
            "site_id": "base",
            "day_obs": 20250930,
            "summary": "string",
            "weather": "string",
            "maintel_summary": "string",
            "auxtel_summary": "string",
            "confluence_url": "string",
            "user_id": "string",
            "user_agent": "string",
            "date_added": "2024-03-20T15:12:46.508840",
            "date_sent": None,
            "is_valid": True,
            "date_invalidated": None,
            "parent_id": None,
            "observers_crew": [],
        }

        self.send_report_payload = {
            "observatory_status": {
                "simonyiAzimuth": "0.00°",
                "simonyiElevation": "0.00°",
                "simonyiDomeAzimuth": "0.00°",
                "simonyiRotator": "0.00°",
                "simonyiMirrorCoversState": "UNKNOWN",
                "simonyiOilSupplySystemState": "UNKNOWN",
                "simonyiPowerSupplySystemState": "UNKNOWN",
                "simonyiLockingPinsSystemState": "UNKNOWN",
                "auxtelAzimuth": "0.00°",
                "auxtelElevation": "0.00°",
                "auxtelDomeAzimuth": "0.00°",
                "auxtelMirrorCoversState": "UNKNOWN",
            },
            "cscs_status": {
                "CSC:0": "UNKNOWN",
                "CSC:1": "UNKNOWN",
                "CSC:2": "UNKNOWN",
                "CSC:3": "UNKNOWN",
            },
        }

    def test_nightreport_list(self):
        """Test nightreport list."""
        # Arrange:
        mock_ole_patcher = patch("requests.get")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: [self.response_report]
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NightReportLogs-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        mock_ole_patcher.stop()

    def test_simple_nightreport_create(self):
        """Test nightreport create."""
        # Arrange:
        mock_ole_patcher = patch("requests.post")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: self.response_report
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NightReportLogs-list")
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, 201)

        mock_ole_patcher.stop()

    def test_nightreport_update(self):
        """Test nightreport update."""
        # Arrange:
        mock_ole_patcher = patch("requests.patch")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: self.response_report
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NightReportLogs-detail", args=[1])
        response = self.client.put(url, self.payload)
        self.assertEqual(response.status_code, 200)

        mock_ole_patcher.stop()

    def test_nightreport_delete(self):
        """Test nightreport delete."""
        # Arrange:
        mock_ole_patcher = patch("requests.delete")
        mock_ole_client = mock_ole_patcher.start()
        response = requests.Response()
        response.status_code = 204
        response.json = lambda: "ok"
        mock_ole_client.return_value = response

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("NightReportLogs-detail", args=[1])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

        mock_ole_patcher.stop()

    def test_nightreport_send(self):
        """Test nightreport send."""
        # Arrange:
        response_get = requests.Response()
        response_get.status_code = 200
        response_get.json = lambda: self.response_report

        response_patch = requests.Response()
        response_patch.status_code = 200
        response_patch.json = lambda: self.response_report

        mock_ole_patcher_get = patch("requests.get")
        mock_ole_client_get = mock_ole_patcher_get.start()
        mock_ole_client_get.return_value = response_get

        mock_ole_patcher_patch = patch("requests.patch")
        mock_ole_client_patch = mock_ole_patcher_patch.start()
        mock_ole_client_patch.return_value = response_patch

        mock_get_jira_obs_report = patch("api.views.get_jira_obs_report")
        mock_get_jira_obs_report_client = mock_get_jira_obs_report.start()
        mock_get_jira_obs_report_client.return_value = []

        mock_send_smtp_email = patch("api.views.send_smtp_email")
        mock_send_smtp_email_client = mock_send_smtp_email.start()
        mock_send_smtp_email_client.return_value = True

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("OLE-nightreport-send-report", args=[self.response_report["id"]])
        response = self.client.post(url, data=self.send_report_payload, format="json")
        self.assertEqual(response.status_code, 200)

        mock_ole_patcher_get.stop()
        mock_ole_patcher_patch.stop()
        mock_get_jira_obs_report.stop()
        mock_send_smtp_email.stop()

    def test_nightreport_send_fail(self):
        """Test nightreport send fail."""
        # Arrange:
        response_get = requests.Response()
        response_get.status_code = 200
        mock_ole_patcher_get = patch("requests.get")
        mock_ole_client_get = mock_ole_patcher_get.start()
        mock_ole_client_get.return_value = response_get

        mock_get_jira_obs_report = patch("api.views.get_jira_obs_report")
        mock_get_jira_obs_report_client = mock_get_jira_obs_report.start()

        mock_arrange_nightreport_email = patch("api.views.arrange_nightreport_email")
        mock_arrange_nightreport_email_client = mock_arrange_nightreport_email.start()

        mock_send_smtp_email = patch("api.views.send_smtp_email")
        mock_send_smtp_email_client = mock_send_smtp_email.start()

        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        url = reverse("OLE-nightreport-send-report", args=[self.response_report["id"]])

        # Act:
        # Night report already sent
        response_get.json = lambda: {
            **self.response_report,
            "date_sent": "2024-03-20T15:12:46.508840",
        }
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Night report already sent"})

        # Obs ticket report raise error
        response_get.json = lambda: {
            **self.response_report,
        }
        mock_get_jira_obs_report_client.side_effect = Exception(ERROR_OBS_TICKETS)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data, {"error": ERROR_OBS_TICKETS})

        # Arrange night report email raise error
        mock_get_jira_obs_report_client.side_effect = None
        mock_arrange_nightreport_email_client.side_effect = Exception(
            "Error arranging night report email"
        )
        response = self.client.post(url, data=self.send_report_payload, format="json")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data, {"error": "Error arranging night report email"})

        # SMTP email send fail
        mock_arrange_nightreport_email_client.side_effect = None
        mock_send_smtp_email_client.return_value = False
        response = self.client.post(url, data=self.send_report_payload, format="json")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data, {"error": "Error sending email"})

        mock_ole_patcher_get.stop()
        mock_get_jira_obs_report.stop()
        mock_arrange_nightreport_email.stop()
        mock_send_smtp_email.stop()
