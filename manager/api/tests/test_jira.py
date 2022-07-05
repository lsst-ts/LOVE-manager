import requests
import random
from unittest.mock import patch
from django.test import TestCase, override_settings
from api.views import jira


@override_settings(DEBUG=True)
class JiraTestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        shared_params = [
            "level",
            "lfa_files_urls",
            "message_text",
            "user_id",
            "user_agent",
        ]
        exposure_params = ["obs_id", "instrument", "exposure_flag"]
        narrative_params = [
            "subsystem",
            "csc",
            "salindex",
            "topic",
            "parameter",
            "begin_date",
            "end_date",
            "time_lost",
        ]

        request_shared = {
            "level": 10,
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
            "subsystem": "MainTel",
            "csc": "M1M3",
            "salindex": "1",
            "topic": "accelerometerData",
            "parameter": "accelerometer",
            "begin_date": "202200703-19:58:13",
            "end_date": "20220704-19:25:13",
            "time_lost": 10,
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

    def test_missing_parameters(self):
        """Test call to function with missing parameters"""

        # exposure
        jira_response = jira(self.jira_request_exposure_without_request_type)
        assert jira_response.data["ack"] == "Error into request type data"

        jira_response = jira(self.jira_request_exposure_without_shared_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

        jira_response = jira(self.jira_request_exposure_without_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

        # narrative
        jira_response = jira(self.jira_request_narrative_without_request_type)
        assert jira_response.data["ack"] == "Error into request type data"

        jira_response = jira(self.jira_request_narrative_without_shared_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

        jira_response = jira(self.jira_request_narrative_without_param)
        assert jira_response.data["ack"] == "Error creating jira payload"

    def test_needed_parameters(self):
        """Test call to function with all needed parameters"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        response = requests.Response()
        response.status_code = 200
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
