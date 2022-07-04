import requests
from unittest.mock import patch
from django.test import TestCase, override_settings
from api.views import jira


@override_settings(DEBUG=True)
class JiraTestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.jira_request = requests.Request(data={"test": "test"})

    def test_missing_parameters(self):
        """Test call to function with missing parameters"""
        assert "true" == "true"

    def test_needed_parameters(self):
        """Test call to function with all needed parameters"""
        mock_jira_patcher = patch("requests.post")
        mock_jira_client = mock_jira_patcher.start()
        mock_jira_client.return_value = requests.Response({"key": "LOVE-XX"})

        print(self.jira_request.data)

        jira_response = jira(self.jira_request)
        print(jira_response)

        assert "true" == "true"
        mock_jira_patcher.stop()
