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


import math
import os
import random
from unittest.mock import patch
from urllib.parse import quote

import pytest
import requests
import rest_framework
from django.test import TestCase, override_settings

from manager.utils import (
    TIME_LOST_FIELD,
    get_jira_obs_report,
    handle_jira_payload,
    jira_comment,
    jira_ticket,
    update_time_lost,
)

OLE_JIRA_OBS_COMPONENTS_FIELDS = [
    "AuxTel",
    "Calibrations",
    "Environmental Monitoring Systems",
    "Facilities",
    "IT Infrastricture",
    "MainTel",
    "Observer Remark",
    "Other",
    "Unknown",
]

OLE_JIRA_OBS_PRIMARY_SOFTWARE_COMPONENT_FIELDS = [
    "None",
    "CSC level",
    "Component Level (EUI)",
    "Visualization",
    "Analysis",
    "Other",
    "Camera Control Software",
]

OLE_JIRA_OBS_PRIMARY_HARDWARE_COMPONENT_FIELDS = [
    "None",
    "Mount",
    "Rotator",
    "Hexapod",
    "M2",
    "Science Cameras",
    "M1M3",
    "Dome",
    "Utilities",
    "Calibration",
    "Other",
]


@override_settings(DEBUG=True)
class JiraTestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
        shared_params = [
            "lfa_files_urls",
            "message_text",
            "user_id",
            "user_agent",
        ]
        exposure_params_required = [
            "obs_id",
            "instrument",
            "exposure_flag",
        ]
        narrative_params_required = [
            "date_begin",
            "date_end",
        ]

        request_shared = {
            "lfa_files_urls": ["test", "test"],
            "message_text": "Lorem ipsum",
            "user_id": "love@localhost",
            "user_agent": "LOVE",
        }

        request_exposure = {
            "obs_id": "AT_O_20220208_000140",
            "instrument": "LATISS",
            "exposure_flag": "none",
        }

        request_narrative = {
            "components": ",".join(
                list(
                    OLE_JIRA_OBS_COMPONENTS_FIELDS[
                        : math.ceil(
                            random.random() * (len(OLE_JIRA_OBS_COMPONENTS_FIELDS) - 1)
                        )
                    ]
                )
            ),
            "components_ids": ",".join(
                [str(n) for n in range(1, math.ceil(random.random() * 100))]
            ),
            "primary_software_components": ",".join(
                OLE_JIRA_OBS_PRIMARY_SOFTWARE_COMPONENT_FIELDS[
                    math.ceil(
                        random.random()
                        * (len(OLE_JIRA_OBS_PRIMARY_SOFTWARE_COMPONENT_FIELDS) - 1)
                    )
                ]
            ),
            "primary_software_components_ids": ",".join(
                [str(math.ceil(random.random() * 100))]
            ),
            "primary_hardware_components": ",".join(
                OLE_JIRA_OBS_PRIMARY_HARDWARE_COMPONENT_FIELDS[
                    math.ceil(
                        random.random()
                        * (len(OLE_JIRA_OBS_PRIMARY_HARDWARE_COMPONENT_FIELDS) - 1)
                    )
                ]
            ),
            "primary_hardware_components_ids": ",".join(
                [str(math.ceil(random.random() * 100))]
            ),
            "date_begin": "2022-07-03T19:58:13.00000",
            "date_end": "2022-07-04T19:25:13.00000",
            "time_lost": 10,
            "level": 0,
        }

        request_full_exposure = {
            **request_shared,
            **request_exposure,
            "request_type": "exposure",
        }

        request_full_narrative = {
            **request_shared,
            **request_narrative,
            "request_type": "narrative",
        }

        request_full_exposure_jira_new = {
            **request_full_exposure,
            "jira": "true",
            "jira_new": "true",
            "jira_issue_title": "Issue title",
        }

        request_full_narrative_jira_new = {
            **request_full_narrative,
            "jira": "true",
            "jira_new": "true",
            "jira_issue_title": "Issue title",
        }

        request_full_exposure_jira_comment = {
            **request_full_exposure,
            "jira": "true",
            "jira_new": "false",
            "jira_issue_id": "LOVE-XX",
        }

        request_full_narrative_jira_comment = {
            **request_full_narrative,
            "jira": "true",
            "jira_new": "false",
            "jira_issue_id": "LOVE-XX",
        }

        # exposure without request type
        data_exposure_without_request_type = {**request_full_exposure}
        del data_exposure_without_request_type["request_type"]
        self.jira_request_exposure_without_request_type = requests.Request(
            data=data_exposure_without_request_type
        )

        # exposure without shared param
        data_exposure_without_shared_param = {**request_full_exposure}
        del data_exposure_without_shared_param[random.choice(shared_params)]
        self.jira_request_exposure_without_shared_param = requests.Request(
            data=data_exposure_without_shared_param
        )

        # exposure without param
        data_exposure_without_param = {**request_full_exposure}
        del data_exposure_without_param[random.choice(exposure_params_required)]
        self.jira_request_exposure_without_param = requests.Request(
            data=data_exposure_without_param
        )

        # narrative without request type
        data_narrative_without_request_type = {**request_full_narrative}
        del data_narrative_without_request_type["request_type"]
        self.jira_request_narrative_without_request_type = requests.Request(
            data=data_narrative_without_request_type
        )

        # narrative without shared param
        data_narrative_without_shared_param = {**request_full_narrative}
        del data_narrative_without_shared_param[random.choice(shared_params)]
        self.jira_request_narrative_without_shared_param = requests.Request(
            data=data_narrative_without_shared_param
        )

        # narrative without param
        data_narrative_without_param = {**request_full_narrative}
        del data_narrative_without_param[random.choice(narrative_params_required)]
        self.jira_request_narrative_without_param = requests.Request(
            data=data_narrative_without_param
        )

        # all parameters requests
        self.jira_request_exposure_full = requests.Request(data=request_full_exposure)
        self.jira_request_narrative_full = requests.Request(data=request_full_narrative)

        # all parameters requests with jira new
        self.jira_request_exposure_full_jira_new = requests.Request(
            data=request_full_exposure_jira_new
        )
        self.jira_request_exposure_full_jira_new.user = "user"
        self.jira_request_exposure_full_jira_new.get_host = lambda: "localhost"

        self.jira_request_narrative_full_jira_new = requests.Request(
            data=request_full_narrative_jira_new
        )
        self.jira_request_narrative_full_jira_new.user = "user"
        self.jira_request_narrative_full_jira_new.get_host = lambda: "localhost"

        # all parameters requests with jira comment
        self.jira_request_exposure_full_jira_comment = requests.Request(
            data=request_full_exposure_jira_comment
        )
        self.jira_request_exposure_full_jira_comment.user = "user"
        self.jira_request_exposure_full_jira_comment.get_host = lambda: "localhost"

        self.jira_request_narrative_full_jira_comment = requests.Request(
            data=request_full_narrative_jira_comment
        )
        self.jira_request_narrative_full_jira_comment.user = "user"
        self.jira_request_narrative_full_jira_comment.get_host = lambda: "localhost"

        # headers for jira requests
        self.headers = {
            "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
            "content-type": "application/json",
        }

    def test_missing_parameters(self):
        """Test call to jira_ticket function with missing parameters"""

        # exposure
        jira_response = jira_ticket(
            self.jira_request_exposure_without_request_type.data
        )
        assert "Error reading request type" in jira_response.data["ack"]

        jira_response = jira_ticket(
            self.jira_request_exposure_without_shared_param.data
        )
        assert "Error creating jira payload" in jira_response.data["ack"]

        jira_response = jira_ticket(self.jira_request_exposure_without_param.data)
        assert "Error creating jira payload" in jira_response.data["ack"]

        # narrative
        jira_response = jira_ticket(
            self.jira_request_narrative_without_request_type.data
        )
        assert "Error reading request type" in jira_response.data["ack"]

        jira_response = jira_ticket(
            self.jira_request_narrative_without_shared_param.data
        )
        assert "Error creating jira payload" in jira_response.data["ack"]

        jira_response = jira_ticket(self.jira_request_narrative_without_param.data)
        assert "Error creating jira payload" in jira_response.data["ack"]

    @patch.dict(os.environ, {"JIRA_API_HOSTNAME": "jira.lsstcorp.org"})
    def test_needed_parameters(self):
        """Test call to jira_ticket function with all needed parameters"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: {"key": "LOVE-XX"}
        mock_jira_client.return_value = response

        jira_response = jira_ticket(self.jira_request_exposure_full.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira ticket created"
        assert (
            jira_response.data["url"]
            == f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/LOVE-XX"
        )

        jira_response = jira_ticket(self.jira_request_narrative_full.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira ticket created"
        assert (
            jira_response.data["url"]
            == f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/LOVE-XX"
        )

        mock_jira_patcher.stop()

    def test_update_time_lost(self):
        """Test call to update_time_lost and verify field was updated"""
        mock_jira_patcher = patch("requests.get")
        mock_jira_get = mock_jira_patcher.start()
        response_get = requests.Response()
        response_get.status_code = 200
        response_get.json = lambda: {"fields": {TIME_LOST_FIELD: 13.6}}
        mock_jira_get.return_value = response_get

        put_patcher = patch("requests.put")
        mock_jira_put = put_patcher.start()
        response_put = requests.Response()
        response_put.status_code = 204
        mock_jira_put.return_value = response_put

        # call update time lost
        jira_response = update_time_lost(1, 3.4)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira time_lost field updated"

        jira_response = update_time_lost(93827, 1.23)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira time_lost field updated"

        # call update time lost with invalid time_lost
        with pytest.raises(TypeError):
            update_time_lost(93827, "5.25")

        # call update time lost with fail put response
        response_put.status_code = 400
        jira_response = update_time_lost(12, 97.01)
        assert jira_response.status_code == 400
        assert jira_response.data["ack"] == "Jira time_lost field could not be updated"

    def test_update_current_time_lost_none(self):
        """Test call to update_time_lost with None as current time_lost"""
        mock_jira_patcher = patch("requests.get")
        mock_jira_get = mock_jira_patcher.start()
        response_get = requests.Response()
        response_get.status_code = 200
        response_get.json = lambda: {"fields": {TIME_LOST_FIELD: None}}
        mock_jira_get.return_value = response_get

        put_patcher = patch("requests.put")
        mock_jira_put = put_patcher.start()
        response_put = requests.Response()
        response_put.status_code = 204
        mock_jira_put.return_value = response_put

        # call update time lost
        jira_response = update_time_lost(1, 3.4)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira time_lost field updated"

    def test_add_comment(self):
        """Test call to jira_comment function with all needed parameters"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        mock_jira_client.return_value = response

        jira_response = jira_comment(self.jira_request_exposure_full_jira_comment.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"

        mock_time_lost_patcher = patch("manager.utils.update_time_lost")
        mock_time_lost_client = mock_time_lost_patcher.start()
        time_lost_response = rest_framework.response.Response()
        time_lost_response.status_code = 200
        time_lost_response.data = {
            "ack": "Jira time_lost field updated",
        }
        mock_time_lost_client.return_value = time_lost_response

        jira_response = jira_comment(self.jira_request_narrative_full_jira_comment.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"

    def test_add_comment_fail(self):
        """Test jira_comment() return value when update_time_lost()
        fails during jira_comment()"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        mock_jira_client.return_value = response

        mock_time_lost_patcher = patch("manager.utils.update_time_lost")
        mock_time_lost_client = mock_time_lost_patcher.start()
        time_lost_response = rest_framework.response.Response()
        time_lost_response.status_code = 400
        time_lost_response.data = {
            "ack": "Jira time_lost field could not be updated",
        }
        mock_time_lost_client.return_value = time_lost_response

        resp = jira_comment(self.jira_request_narrative_full_jira_comment.data)
        assert resp.status_code == 400
        assert resp.data["ack"] == "Jira time_lost field could not be updated"

    @patch.dict(os.environ, {"JIRA_API_HOSTNAME": "jira.lsstcorp.org"})
    def test_handle_narrative_jira_payload(self):
        """Test call to function handle_jira_payload with all needed parameters
        for narrative request type
        """
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: {"key": "LOVE-XX"}
        mock_jira_client.return_value = response

        mock_time_lost_patcher = patch("manager.utils.update_time_lost")
        mock_time_lost_client = mock_time_lost_patcher.start()
        time_response = requests.Response()
        time_response.status_code = 200
        mock_time_lost_client.return_value = time_response

        jira_response = handle_jira_payload(self.jira_request_narrative_full_jira_new)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira ticket created"
        assert (
            jira_response.data["url"]
            == f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/LOVE-XX"
        )

        jira_response = handle_jira_payload(
            self.jira_request_narrative_full_jira_comment
        )
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"
        assert (
            jira_response.data["url"]
            == f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/LOVE-XX"
        )

        mock_jira_patcher.stop()

    def test_handle_exposure_jira_payload(self):
        """Test call to function handle_jira_payload with all needed parameters
        for exposure request type
        """
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: {"key": "LOVE-XX"}
        mock_jira_client.return_value = response

        jira_response = handle_jira_payload(self.jira_request_exposure_full_jira_new)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira ticket created"
        assert (
            jira_response.data["url"]
            == f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/LOVE-XX"
        )

        jira_response = handle_jira_payload(
            self.jira_request_exposure_full_jira_comment
        )
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"
        assert (
            jira_response.data["url"]
            == f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/LOVE-XX"
        )

        mock_jira_patcher.stop()

    def test_get_jira_obs_report(self):
        """Test call to get_jira_obs_report
        function with all needed parameters"""

        # Arrange
        mock_jira_patcher = patch("requests.get")
        mock_jira_client = mock_jira_patcher.start()

        url_call_1 = (
            f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/myself"
        )

        response_1 = requests.Response()
        response_1.status_code = 200
        response_1.json = lambda: {
            "timeZone": "America/Phoenix",
        }

        # American/Phoenix timezone is UTC-7
        day_obs = "20241127"
        jql_query = (
            "project = 'OBS' "
            "AND created >= '2024-11-27 05:00' "
            "AND created <= '2024-11-28 05:00'"
        )
        url_call_2 = (
            f"https://{os.environ.get('JIRA_API_HOSTNAME')}"
            f"/rest/api/latest/search?jql={quote(jql_query)}"
        )

        response_2 = requests.Response()
        response_2.status_code = 200
        response_2.json = lambda: {
            "issues": [
                {
                    "key": "LOVE-XX",
                    "fields": {
                        "summary": "Issue title",
                        TIME_LOST_FIELD: 13.6,
                        "creator": {"displayName": "user"},
                        "created": "2024-11-27T12:00:00.00000",
                    },
                }
            ]
        }

        mock_jira_client.side_effect = [response_1, response_2]

        # Act
        request_data = {
            "day_obs": day_obs,
        }
        jira_response = get_jira_obs_report(request_data)

        # Assert
        mock_jira_client.assert_any_call(url_call_1, headers=self.headers)
        mock_jira_client.assert_any_call(url_call_2, headers=self.headers)

        assert jira_response[0]["key"] == "LOVE-XX"
        assert jira_response[0]["summary"] == "Issue title"
        assert jira_response[0]["time_lost"] == 13.6
        assert jira_response[0]["reporter"] == "user"
        assert jira_response[0]["created"] == "2024-11-27T12:00:00"

        mock_jira_patcher.stop()

    def test_get_jira_obs_report_fail(self):
        """Test call to get_jira_obs_report function with fail response"""

        # Arrange
        request_data = {
            "day_obs": 20241127,
        }

        mock_jira_patcher = patch("requests.get")
        mock_jira_client = mock_jira_patcher.start()

        success_response_1 = requests.Response()
        success_response_1.status_code = 200
        success_response_1.json = lambda: {
            "timeZone": "America/Phoenix",
        }

        failed_response = requests.Response()
        failed_response.status_code = 400

        # Act
        # Incomplete request data
        incomplete_request_data = {}
        with self.assertRaises(ValueError):
            get_jira_obs_report(incomplete_request_data)

        # Fail response from Jira to get user data
        mock_jira_client.return_value = failed_response
        with pytest.raises(Exception) as e:
            get_jira_obs_report(request_data)
        assert (
            str(e.value)
            == f"Error getting user timezone from {os.environ.get('JIRA_API_HOSTNAME')}"
        )

        # Fail response from Jira to get issues
        mock_jira_client.side_effect = [success_response_1, failed_response]
        with pytest.raises(Exception) as e:
            get_jira_obs_report(request_data)
        assert (
            str(e.value)
            == f"Error getting issues from {os.environ.get('JIRA_API_HOSTNAME')}"
        )

        mock_jira_patcher.stop()

    def test_get_jira_obs_report_bad_date(self):
        """Test call to get_jira_obs_report function with bad date"""
        request_data = {
            "day_obs": 20240931,
        }
        with pytest.raises(ValueError):
            get_jira_obs_report(request_data)
