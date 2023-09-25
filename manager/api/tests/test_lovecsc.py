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
from django.test import TestCase, override_settings
from django.urls import reverse
from api.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission
from unittest.mock import patch, call
from manager.utils import UserBasedPermission


@override_settings(DEBUG=True)
class LOVECscTestCase(TestCase):
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
    def test_authorized_lovecsc_data(self, mock_requests):
        """Test authorized user observing log is sent to love-commander"""
        # Arrange:
        self.user.user_permissions.add(Permission.objects.get(name="Execute Commands"))

        # Act:
        url = reverse("lovecsc-observinglog")
        data = {
            "user": "user",
            "message": "a message",
        }

        with self.assertRaises(ValueError):
            self.client.post(url, data, format="json")

        expected_url = "http://foo:bar/lovecsc/observinglog"
        self.assertEqual(mock_requests.call_args, call(expected_url, json=data))

    @patch("requests.post")
    def test_unauthorized_lovecsc(self, mock_requests):
        """Test an unauthorized user can't send commands"""
        # Act:
        url = reverse("lovecsc-observinglog")
        data = {
            "user": "user",
            "message": "a message",
        }

        response = self.client.post(url, data, format="json")
        result = response.json()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(result, UserBasedPermission.message)
