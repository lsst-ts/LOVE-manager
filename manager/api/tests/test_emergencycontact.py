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


"""Test users' authentication through the API."""
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import EmergencyContact, Token
from django.core.files.base import ContentFile

# python manage.py test api.tests.tests_emergencycontact.EmergencyContactApiTestCase


class EmergencyContactApiTestCase(TestCase):
    """Test suite for config files handling."""

    @staticmethod
    def get_config_file_sample(name, content):
        f = ContentFile(json.dumps(content).encode("ascii"), name=name)
        return f

    def setUp(self):
        """Define the test suite setup."""
        # Arrange:

        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.token = Token.objects.create(user=self.user)
        self.ec1 = EmergencyContact.objects.create(
            subsystem="ATDome",
            name="Name Lastname",
            contact_info="+568984861",
            email="name@email.com",
        )
        self.ec2 = EmergencyContact.objects.create(
            subsystem="ATMCS",
            name="Name2 Lastname2",
            contact_info="no info",
            email="name2@email.com",
        )

    def test_list_emergency_contacts(self):
        """Test that an authenticated user can get a config file."""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(reverse("emergencycontact-list"), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["subsystem"], self.ec1.subsystem)
        self.assertEqual(response.data[0]["name"], self.ec1.name)
        self.assertEqual(response.data[0]["contact_info"], self.ec1.contact_info)
        self.assertEqual(response.data[0]["email"], self.ec1.email)
        self.assertEqual(response.data[1]["subsystem"], self.ec2.subsystem)
        self.assertEqual(response.data[1]["name"], self.ec2.name)
        self.assertEqual(response.data[1]["contact_info"], self.ec2.contact_info)
        self.assertEqual(response.data[1]["email"], self.ec2.email)
