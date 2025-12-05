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


import os
from unittest.mock import call, patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse
from manager.utils import UserBasedPermission
from rest_framework.test import APIClient

from api.models import Token

# python manage.py test api.tests.test_commander.CommanderTestCase
# python manage.py test api.tests.test_commander.SalinfoTestCase
# python manage.py test api.tests.test_commander.EFDTestCase
# python manage.py test api.tests.test_commander.TCSTestCase


@override_settings(DEBUG=True)
class CommanderTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_view"),
            Permission.objects.get(codename="add_view"),
            Permission.objects.get(codename="delete_view"),
            Permission.objects.get(codename="change_view"),
        )
        os.environ["COMMANDER_HOSTNAME"] = "foo"
        os.environ["COMMANDER_PORT"] = "bar"

    @patch("requests.post")
    @patch.dict(os.environ, {"SERVER_URL": "localhost"})
    def test_authorized_commander_data(self, mock_requests):
        """Test authorized user commander data is sent to love-commander"""
        # Arrange:
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))

        # Act:
        url = reverse("commander")
        data = {
            "csc": "Test",
            "salindex": 1,
            "cmd": "cmd_setScalars",
            "params": {"a": 1, "b": 2},
        }
        data_with_identity = data.copy()
        data_with_identity["identity"] = f"{self.user.username}@localhost"

        with self.assertRaises(ValueError):
            self.client.post(url, data, format="json")
        expected_url = "http://foo:bar/cmd"
        self.assertEqual(mock_requests.call_args, call(expected_url, json=data_with_identity))

    @patch("requests.post")
    def test_unauthorized_commander(self, mock_requests):
        """Test an unauthorized user can't send commands"""
        # Act:
        url = reverse("commander")
        data = {
            "csc": "Test",
            "salindex": 1,
            "cmd": "cmd_setScalars",
            "params": {"a": 1, "b": 2},
        }

        response = self.client.post(url, data, format="json")
        result = response.json()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(result, UserBasedPermission.message)


@override_settings(DEBUG=True)
class SalinfoTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_view"),
            Permission.objects.get(codename="add_view"),
            Permission.objects.get(codename="delete_view"),
            Permission.objects.get(codename="change_view"),
        )

        os.environ["COMMANDER_HOSTNAME"] = "foo"
        os.environ["COMMANDER_PORT"] = "bar"

    @patch("requests.get")
    def test_salinfo_metadata(self, mock_requests):
        """Test authorized user can get salinfo metadata"""
        # Act:
        url = reverse("salinfo-metadata")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = "http://foo:bar/salinfo/metadata"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch("requests.get")
    def test_salinfo_topic_names(self, mock_requests):
        """Test authorized user can get salinfo topic_names"""
        # Act:
        url = reverse("salinfo-topic-names")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = "http://foo:bar/salinfo/topic-names"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch("requests.get")
    def test_salinfo_topic_names_with_param(self, mock_requests):
        """Test authorized user can get salinfo topic_names with query param"""
        # Act:
        url = reverse("salinfo-topic-names") + "?categories=telemetry"

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = "http://foo:bar/salinfo/topic-names?categories=telemetry"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch("requests.get")
    def test_salinfo_topic_data(self, mock_requests):
        """Test authorized user can get salinfo topic_data"""
        # Act:
        url = reverse("salinfo-topic-data")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = "http://foo:bar/salinfo/topic-data"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch("requests.get")
    def test_salinfo_topic_data_with_param(self, mock_requests):
        """Test authorized user can get salinfo topic_data with query param"""
        # Act:
        url = reverse("salinfo-topic-data") + "?categories=telemetry"

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = "http://foo:bar/salinfo/topic-data?categories=telemetry"
        self.assertEqual(mock_requests.call_args, call(expected_url))


@override_settings(DEBUG=True)
class EFDTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_view"),
            Permission.objects.get(codename="add_view"),
            Permission.objects.get(codename="delete_view"),
            Permission.objects.get(codename="change_view"),
        )

        os.environ["COMMANDER_HOSTNAME"] = "foo"
        os.environ["COMMANDER_PORT"] = "bar"

    @patch("requests.post")
    def test_timeseries_query(self, mock_requests):
        """Test authorized user can query and get a timeseries"""
        # Act:
        cscs = {
            "ATDome": {
                "0": {"topic1": ["field1"]},
            },
            "ATMCS": {
                "1": {"topic2": ["field2", "field3"]},
            },
        }
        data = {
            "start_date": "2020-03-16T12:00:00",
            "time_window": 15,
            "cscs": cscs,
            "resample": "1min",
        }
        url = reverse("EFD-timeseries")

        with self.assertRaises(ValueError):
            self.client.post(url, data, format="json")
        expected_url = "http://foo:bar/efd/timeseries"
        self.assertEqual(mock_requests.call_args, call(expected_url, json=data))


@override_settings(DEBUG=True)
class TCSTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_view"),
            Permission.objects.get(codename="add_view"),
            Permission.objects.get(codename="delete_view"),
            Permission.objects.get(codename="change_view"),
        )

        os.environ["COMMANDER_HOSTNAME"] = "foo"
        os.environ["COMMANDER_PORT"] = "bar"

    @patch("requests.post")
    def test_command_query_atcs(self, mock_requests):
        """Test authorized user can send a ATCS command"""
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))
        # Act:
        data = {
            "command_name": "atcs_command",
            "params": {
                "param1": "value1",
                "param2": 2,
                "param3": True,
            },  # noqa: E231
        }
        url = reverse("TCS-aux")

        with self.assertRaises(ValueError):
            self.client.post(url, data, format="json")
        expected_url = "http://foo:bar/tcs/aux"
        self.assertEqual(mock_requests.call_args, call(expected_url, json=data))

    @patch("requests.post")
    def test_command_query_atcs_unauthorized(self, mock_requests):
        """Test unauthorized user cannot send a ATCS command"""
        self.user.user_permissions.remove(Permission.objects.get(name="Execute Commands"))
        # Act:
        data = {
            "command_name": "atcs_command",
            "params": {
                "param1": "value1",
                "param2": 2,
                "param3": True,
            },  # noqa: E231
        }
        url = reverse("TCS-aux")
        response = self.client.post(url, data, format="json")
        result = response.json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(result, UserBasedPermission.message)

    @patch("requests.get")
    def test_docstrings_query_atcs(self, mock_requests):
        """Test authorized user can send a ATCS command"""
        # Act:
        url = reverse("TCS-aux-docstrings")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = "http://foo:bar/tcs/aux/docstrings"
        self.assertEqual(mock_requests.call_args, call(expected_url))

    @patch("requests.post")
    def test_command_query_mtcs(self, mock_requests):
        """Test authorized user can send a MTCS command"""
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))
        # Act:
        data = {
            "command_name": "mtcs_command",
            "params": {
                "param1": "value1",
                "param2": 2,
                "param3": True,
            },  # noqa: E231
        }
        url = reverse("TCS-main")

        with self.assertRaises(ValueError):
            self.client.post(url, data, format="json")
        expected_url = "http://foo:bar/tcs/main"
        self.assertEqual(mock_requests.call_args, call(expected_url, json=data))

    @patch("requests.post")
    def test_command_query_mtcs_unauthorized(self, mock_requests):
        """Test unauthorized user cannot send a MTCS command"""
        self.user.user_permissions.remove(Permission.objects.get(name="Execute Commands"))
        # Act:
        data = {
            "command_name": "mtcs_command",
            "params": {
                "param1": "value1",
                "param2": 2,
                "param3": True,
            },  # noqa: E231
        }
        url = reverse("TCS-main")
        response = self.client.post(url, data, format="json")
        result = response.json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(result, UserBasedPermission.message)

    @patch("requests.get")
    def test_docstrings_query_mtcs(self, mock_requests):
        """Test authorized user can send a MTCS command"""
        # Act:
        url = reverse("TCS-main-docstrings")

        with self.assertRaises(ValueError):
            self.client.get(url)
        expected_url = "http://foo:bar/tcs/main/docstrings"
        self.assertEqual(mock_requests.call_args, call(expected_url))
