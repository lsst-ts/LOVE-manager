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
from api.models import Token, ZephyrScaleCredential
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@override_settings(DEBUG=True)
class PlanningToolTestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()

        user_with_jira_tokens = {
            "username": "user-with-permissions",
            "password": "password",
            "email": "test@user.cl",
            "first_name": "user-with-permissions",
            "last_name": "",
        }
        self.user_with_jira_tokens = User.objects.create_user(**user_with_jira_tokens)
        self.token_user_with_jira_tokens = Token.objects.create(
            user=self.user_with_jira_tokens
        )
        self.zephyr_scale_credential_user_with_jira_tokens = (
            ZephyrScaleCredential.objects.create(
                user=self.user_with_jira_tokens,
                jira_username="user-normal",
                jira_api_token="jira-api-token",
                zephyr_api_token="zephyr-api-token",
            )
        )

        user_without_jira_tokens = {
            "username": "user-without-permissions",
            "password": "password",
            "email": "test@user.cl",
            "first_name": "user-without-permissions",
            "last_name": "",
        }
        self.user_without_jira_tokens = User.objects.create_user(
            **user_without_jira_tokens
        )
        self.token_user_without_jira_tokens = Token.objects.create(
            user=self.user_without_jira_tokens
        )

        self.response_test_cycles = [
            {
                "id": "12345678",
                "key": "CYCLE-1",
                "name": "Test cycle #1",
            },
            {
                "id": "12345679",
                "key": "CYCLE-2",
                "name": "Test cycle #2",
            },
            {
                "id": "12345670",
                "key": "CYCLE-3",
                "name": "Test cycle #3",
            },
        ]

        self.response_test_cycle = {
            "id": "12345678",
            "key": "CYCLE-1",
            "name": "Test cycle CYCLE-1",
            "description": "Test cycle description",
            "project": "BLOCK",
            "status": "Done",
            "folder": "/Folder",
            "owner": "User",
            "customFields": {
                "Night Support": "Tiago Ribeiro",
                "Night Planner": "Bruno Quint",
                "Night Summary": "Test cycle summary",
                "TMA walk around done": True,
                "TMA walk around - performed by": "User",
                "TMA walk around - comments": "Test cycle comments",
                "TMA ready for use?": True,
                "End of Night - TMA El Position": "El Position",
                "End of Night - TMA Az Position": "Az Position",
                "End of Night - OSS Power Status": "Power Status",
                "End of Night - Power Supply Status": "Power Supply Status",
            },
        }

        self.response_test_cases = [
            {
                "id": "12345678",
                "key": "CASE-1",
                "name": "Test case #1",
                "environment": "Test environment",
                "status": "Done",
                "executed_by": "User",
            },
            {
                "id": "12345679",
                "key": "CASE-2",
                "name": "Test case #2",
                "environment": "Test environment",
                "status": "Done",
                "executed_by": "User",
            },
            {
                "id": "12345670",
                "key": "CASE-3",
                "name": "Test case #3",
                "environment": "Test environment",
                "status": "Done",
                "executed_by": "User",
            },
        ]

        self.response_test_case_last_execution = {
            "test_case": "BLOCK-T17",
            "version": "1.0",
            "title": "AuxTel Daytime Checkouts",
            "status": "PASSED",
            "environment": "2. Late Afternoon",
            "release_version": "None",
            "executed_by": "Bruno Quint",
            "executed_time": 15,
            "iteration": "None",
            "assignee": "Bruno Quint",
            "estimated_time": 1200,
            "objective": "Complete AuxTel Daytime Checkouts",
            "precondition": "AuxTel is in a good state",
            "comment": "All tests passed successfully",
            "steps": [
                {
                    "title": "Enable LATISS",
                    "status": "NOT EXECUTED",
                    "test_data": "None",
                    "expected_result": (
                        "Script completes without error. "
                        "All ATSpectrograph components are enabled."
                    ),
                    "sal_script": "auxtel/enable_latiss.py",
                    "script_configuration": "",
                    "is_external": True,
                    "actual_result": "None",
                },
                {
                    "title": "Run LATISS checkouts",
                    "status": "NOT EXECUTED",
                    "test_data": "None",
                    "expected_result": "Script completes without error.",
                    "sal_script": "auxtel/daytime_checkout/latiss_checkout.py",
                    "script_configuration": "",
                    "is_external": False,
                    "actual_result": "None",
                },
                {
                    "title": "Enable ATCS.",
                    "status": "NOT EXECUTED",
                    "test_data": "None",
                    "expected_result": (
                        "Script completes without error. "
                        "All AuxTel components are in enabled mode."
                    ),
                    "sal_script": "auxtel/enable_atcs.py",
                    "script_configuration": "",
                    "is_external": False,
                    "actual_result": "None",
                },
                {
                    "title": "ATPneumatics Checkout",
                    "status": "NOT EXECUTED",
                    "test_data": "None",
                    "expected_result": "Script completes without error.",
                    "sal_script": "auxtel/daytime_checkout/atpneumatics_checkout.py",
                    "script_configuration": "",
                    "is_external": False,
                    "actual_result": "None",
                },
            ],
        }

    def test_query_test_cycles(self):
        """Test Planning Tool query test cycles."""
        # Arrange:
        mock_planning_tool_patcher = patch("requests.post")
        mock_planning_tool_client = mock_planning_tool_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: self.response_test_cycles
        mock_planning_tool_client.return_value = response

        # Act:
        # User without Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_without_jira_tokens.key
        )
        url = reverse("Planning-tool-test-cycles")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Zephyr Scale credentials not found")

        # User with Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_with_jira_tokens.key
        )
        url = reverse("Planning-tool-test-cycles")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        for obj in response.data:
            self.assertIn("id", obj)
            self.assertIn("key", obj)
            self.assertIn("name", obj)

        # Stop patches
        mock_planning_tool_patcher.stop()

    def test_query_test_cycle(self):
        """Test Planning Tool query test cycle."""
        # Arrange:
        mock_planning_tool_patcher = patch("requests.post")
        mock_planning_tool_client = mock_planning_tool_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: self.response_test_cycle
        mock_planning_tool_client.return_value = response

        # Act:
        # User without Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_without_jira_tokens.key
        )
        url = reverse("Planning-tool-test-cycle", kwargs={"pk_cycle": "12345678"})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Zephyr Scale credentials not found")

        # User with Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_with_jira_tokens.key
        )
        url = reverse("Planning-tool-test-cycle", kwargs={"pk_cycle": "12345678"})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.data)
        self.assertIn("key", response.data)
        self.assertIn("name", response.data)
        self.assertIn("description", response.data)
        self.assertIn("project", response.data)
        self.assertIn("status", response.data)
        self.assertIn("folder", response.data)
        self.assertIn("owner", response.data)
        self.assertIn("customFields", response.data)

        # Stop patches
        mock_planning_tool_patcher.stop()

    def test_query_test_cases(self):
        """Test Planning Tool query test cases."""
        # Arrange:
        mock_planning_tool_patcher = patch("requests.post")
        mock_planning_tool_client = mock_planning_tool_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: self.response_test_cases
        mock_planning_tool_client.return_value = response

        # Act:
        # User without Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_without_jira_tokens.key
        )
        url = reverse(
            "Planning-tool-test-cycle-test-cases", kwargs={"pk_cycle": "12345678"}
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Zephyr Scale credentials not found")

        # User with Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_with_jira_tokens.key
        )
        url = reverse(
            "Planning-tool-test-cycle-test-cases", kwargs={"pk_cycle": "12345678"}
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        for obj in response.data:
            self.assertIn("id", obj)
            self.assertIn("key", obj)
            self.assertIn("name", obj)
            self.assertIn("environment", obj)
            self.assertIn("status", obj)
            self.assertIn("executed_by", obj)

        # Stop patches
        mock_planning_tool_patcher.stop()

    def test_query_test_last_execution(self):
        """Test Planning Tool query test last execution."""
        # Arrange:
        mock_planning_tool_patcher = patch("requests.post")
        mock_planning_tool_client = mock_planning_tool_patcher.start()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: self.response_test_case_last_execution
        mock_planning_tool_client.return_value = response

        # Act:
        # User without Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_without_jira_tokens.key
        )
        url = reverse(
            "Planning-tool-test-cycle-test-case-last-execution",
            kwargs={"pk_cycle": "12345678", "pk_case": "12345678"},
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Zephyr Scale credentials not found")

        # User with Jira tokens
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_with_jira_tokens.key
        )
        url = reverse(
            "Planning-tool-test-cycle-test-case-last-execution",
            kwargs={"pk_cycle": "12345678", "pk_case": "12345678"},
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("test_case", response.data)
        self.assertIn("version", response.data)
        self.assertIn("title", response.data)
        self.assertIn("status", response.data)
        self.assertIn("environment", response.data)
        self.assertIn("release_version", response.data)
        self.assertIn("executed_by", response.data)
        self.assertIn("executed_time", response.data)
        self.assertIn("iteration", response.data)
        self.assertIn("assignee", response.data)
        self.assertIn("estimated_time", response.data)
        self.assertIn("objective", response.data)
        self.assertIn("precondition", response.data)
        self.assertIn("comment", response.data)
        self.assertIn("steps", response.data)
        for obj in response.data["steps"]:
            self.assertIn("title", obj)
            self.assertIn("status", obj)
            self.assertIn("test_data", obj)
            self.assertIn("expected_result", obj)
            self.assertIn("sal_script", obj)
            self.assertIn("script_configuration", obj)
            self.assertIn("is_external", obj)
            self.assertIn("actual_result", obj)

        # Stop patches
        mock_planning_tool_patcher.stop()
