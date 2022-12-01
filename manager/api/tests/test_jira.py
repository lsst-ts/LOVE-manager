import requests
import random
from unittest.mock import patch
from django.test import TestCase, override_settings
from api.views import jira, jira_comment


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
            "tags",
        ]
        exposure_params = ["obs_id", "instrument", "exposure_flag"]
        narrative_params = [
            "system",
            "subsystems",
            "cscs",
            "date_begin",
            "date_end",
            "time_lost",
            "level",
        ]

        request_shared = {
            "lfa_files_urls": ["test", "test"],
            "message_text": "Lorem ipsum",
            "user_id": "love@localhost",
            "user_agent": "LOVE",
            "tags": "tag1, tag2",
        }

        request_exposure = {
            "obs_id": "AT_O_20220208_000140",
            "instrument": "LATISS",
            "exposure_flag": "none",
        }

        request_narrative = {
            "system": "MainTel",
            "subsystems": "Camera",
            "cscs": "M1M3",
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
            "issue_id": "TEST-XX",
        }

        request_full_narrative_jira_comment = {
            **request_shared,
            **request_narrative,
            "request_type": "narrative",
            "issue_id": "TEST-XX",
        }

        # exposure
        data_exposure_without_request_type = {**request_full_exposure}
        del data_exposure_without_request_type["request_type"]
        self.jira_request_exposure_without_request_type = requests.Request(
            data=data_exposure_without_request_type
        )

        data_exposure_without_shared_param = {**request_full_exposure}
        del data_exposure_without_shared_param[random.choice(shared_params)]
        self.jira_request_exposure_without_shared_param = requests.Request(
            data=data_exposure_without_shared_param
        )

        data_exposure_without_param = {**request_full_exposure}
        del data_exposure_without_param[random.choice(exposure_params)]
        self.jira_request_exposure_without_param = requests.Request(
            data=data_exposure_without_param
        )

        # narrative
        data_narrative_without_request_type = {**request_full_narrative}
        del data_narrative_without_request_type["request_type"]
        self.jira_request_narrative_without_request_type = requests.Request(
            data=data_narrative_without_request_type
        )

        data_narrative_without_shared_param = {**request_full_narrative}
        del data_narrative_without_shared_param[random.choice(shared_params)]
        self.jira_request_narrative_without_shared_param = requests.Request(
            data=data_narrative_without_shared_param
        )

        data_narrative_without_param = {**request_full_narrative}
        del data_narrative_without_param[random.choice(narrative_params)]
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
        jira_response = jira(self.jira_request_exposure_without_request_type)
        assert jira_response.data["ack"] == "Error reading request type"

        jira_response = jira(self.jira_request_exposure_without_shared_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

        jira_response = jira(self.jira_request_exposure_without_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

        # narrative
        jira_response = jira(self.jira_request_narrative_without_request_type)
        assert jira_response.data["ack"] == "Error reading request type"

        jira_response = jira(self.jira_request_narrative_without_shared_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

        jira_response = jira(self.jira_request_narrative_without_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

    def test_needed_parameters(self):
        """Test call to function with all needed parameters"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 201
        response.json = lambda: {"key": "LOVE-XX"}
        mock_jira_client.return_value = response

        jira_response = jira(self.jira_request_exposure_full)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira ticket created"
        assert jira_response.data["url"] == "https://jira.lsstcorp.org/browse/LOVE-XX"

        jira_response = jira(self.jira_request_narrative_full)
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

        jira_response = jira_comment(self.jira_request_exposure_full_jira_comment)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"

        jira_response = jira_comment(self.jira_request_narrative_full_jira_comment)
        assert jira_response.status_code == 200
        assert jira_response.data["ack"] == "Jira comment created"
