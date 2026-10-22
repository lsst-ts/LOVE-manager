# This file is part of LOVE-manager.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import random
from unittest.mock import patch
from urllib.parse import unquote

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from redirect.utils import ChronografSites, FATable


def get_random_force_actuator():
    """Get a random force actuator

    Returns
    -------
    ForceActuatorData
        The random force actuator record

    """
    return random.choice(FATable)


class M1M3ForceActuatorsRedirectTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_m1m3_force_actuators_tests_redirect_success(self):
        # Arrange
        site = ChronografSites.SUMMIT
        params = {
            "id": get_random_force_actuator().actuator_id,
            "lower": "2022-01-01T00:00:00",
            "upper": "2022-01-02T00:00:00",
        }
        url = reverse("dashboards-m1m3-force-actuator-tests", args=[site])

        # Act
        response = self.client.get(url, params)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("https://", response.url)
        self.assertIn(site, response.url)
        self.assertIn("refresh=Paused", response.url)
        self.assertIn("tempVars[x_index]", unquote(response.url))
        self.assertIn("tempVars[y_index]", unquote(response.url))
        self.assertIn("tempVars[z_index]", unquote(response.url))
        self.assertIn("tempVars[s_index]", unquote(response.url))
        self.assertIn("lower=2022-01-01T00:00:00Z", unquote(response.url))
        self.assertIn("upper=2022-01-02T00:00:00Z", unquote(response.url))

    def test_m1m3_force_actuators_tests_redirect_missing_parameters(self):
        # Arrange
        site = ChronografSites.SUMMIT
        params = {
            "id": get_random_force_actuator().actuator_id,
            "lower": "2022-01-01T00:00:00",
            # Missing "upper" parameter
        }
        url = reverse("dashboards-m1m3-force-actuator-tests", args=[site])

        # Act
        response = self.client.get(url, params)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Error: lower and upper parameters are required")

    def test_m1m3_force_actuators_tests_redirect_exception(self):
        # Arrange
        site = ChronografSites.SUMMIT
        params = {
            "id": get_random_force_actuator().actuator_id,
            "lower": "2022-01-01T00:00:00",
            "upper": "2022-01-02T00:00:00",
        }
        url = reverse("dashboards-m1m3-force-actuator-tests", args=[site])

        # Mock the exception
        with patch("redirect.views.urlunparse") as mock_urlunparse:
            mock_urlunparse.side_effect = Exception("Mocked exception")

            # Act
            response = self.client.get(url, params)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Error: Mocked exception")
