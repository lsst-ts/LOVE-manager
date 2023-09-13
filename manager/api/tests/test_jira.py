# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed for Inria Chile.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or at your option any later version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


import random
import requests

from api.views import jira_ticket, jira_comment
from django.test import TestCase, override_settings
from unittest.mock import patch
from manager.utils import (
    OLE_JIRA_OBS_COMPONENTS_FIELDS,
    OLE_JIRA_OBS_PRIMARY_SOFTWARE_COMPONENT_FIELDS,
    OLE_JIRA_OBS_PRIMARY_HARDWARE_COMPONENT_FIELDS,
)


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
            "components": ",".join(list(OLE_JIRA_OBS_COMPONENTS_FIELDS.keys())[:2]),
            "primary_software_components": list(
                OLE_JIRA_OBS_PRIMARY_SOFTWARE_COMPONENT_FIELDS.keys()
            )[0],
            "primary_hardware_components": list(
                OLE_JIRA_OBS_PRIMARY_HARDWARE_COMPONENT_FIELDS.keys()
            )[0],
            "date_begin": "202200703-19:58:13",
            "date_end": "20220704-19:25:13",
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

        request_full_exposure_jira_comment = {
            **request_shared,
            **request_exposure,
            "request_type": "exposure",
            "jira_issue_id": "TEST-XX",
        }

        request_full_narrative_jira_comment = {
            **request_shared,
            **request_narrative,
            "request_type": "narrative",
            "jira_issue_id": "TEST-XX",
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

        self.jira_request_exposure_full = requests.Request(data=request_full_exposure)
        self.jira_request_narrative_full = requests.Request(data=request_full_narrative)

        self.jira_request_exposure_full_jira_comment = requests.Request(
            data=request_full_exposure_jira_comment
        )
        self.jira_request_narrative_full_jira_comment = requests.Request(
            data=request_full_narrative_jira_comment
        )

    def test_missing_parameters(self):
        """Test call to function with missing parameters"""

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

    def test_needed_parameters(self):
        """Test call to function with all needed parameters"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: {"key": "LOVE-XX"}
        mock_jira_client.return_value = response

        jira_response = jira_ticket(self.jira_request_exposure_full.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira ticket created"
        assert jira_response.data["url"] == "https://jira.lsstcorp.org/browse/LOVE-XX"

        jira_response = jira_ticket(self.jira_request_narrative_full.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira ticket created"
        assert jira_response.data["url"] == "https://jira.lsstcorp.org/browse/LOVE-XX"

        mock_jira_patcher.stop()

    def test_add_comment(self):
        """Test call to function with all needed parameters"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        mock_jira_client.return_value = response

        jira_response = jira_comment(self.jira_request_exposure_full_jira_comment.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"

        jira_response = jira_comment(self.jira_request_narrative_full_jira_comment.data)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"
