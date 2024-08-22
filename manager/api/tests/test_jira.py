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

import requests
from django.test import TestCase, override_settings

from manager.utils import (
    TIME_LOST_FIELD,
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
        # Arrange
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
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: {TIME_LOST_FIELD: 13.6}
        mock_jira_get.return_value = response

        put_patcher = patch("requests.put")
        mock_jira_put = put_patcher.start()
        response.status_code = 204
        mock_jira_put.return_value = response

        # call update time lost
        jira_response = update_time_lost(1, 3.4)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira time_lost field updated"

        jira_response = update_time_lost(93827, 1.23)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira time_lost field updated"

        response.status_code = 400
        mock_jira_put.return_value = response

        jira_response = update_time_lost(12, 97.01)
        assert jira_response.status_code == 400

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
        mock_time_lost_client.return_value = response

        jira_response = jira_comment(self.jira_request_narrative_full_jira_comment.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"

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
