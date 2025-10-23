from unittest.mock import patch

import pytest
import requests
from django.test import TestCase
from django.test.utils import override_settings

from manager.utils import (
    arrange_nightlydigest_urls_for_obsday,
    get_last_valid_night_report,
)


class UtilsTestCase(TestCase):
    def setUp(self):
        self.requests_get_patcher = patch("requests.get")
        self.mock_requests_get = self.requests_get_patcher.start()

    def tearDown(self):
        self.requests_get_patcher.stop()

    @override_settings(NIGHTLYDIGEST_BASE_URL="https://example.com/nightlydigest")
    def test_arrange_nightlydigest_urls_for_obsday(self):
        obsday = 20250930
        expected_urls = {
            "simonyi": (
                "https://example.com/nightlydigest"
                "/?startDayobs=20250930&endDayobs=20250930&telescope=Simonyi"
            ),
            "auxtel": (
                "https://example.com/nightlydigest"
                "/?startDayobs=20250930&endDayobs=20250930&telescope=AuxTel"
            ),
        }

        result = arrange_nightlydigest_urls_for_obsday(obsday)
        assert result == expected_urls

    def test_arrange_nightlydigest_urls_for_obsday_invalid_obsday(self):
        invalid_obsdays = [2025091, 202509100, "2025091", None]

        for obsday in invalid_obsdays:
            with pytest.raises(ValueError) as e:
                arrange_nightlydigest_urls_for_obsday(obsday)
            assert (
                str(e.value)
                == f"Invalid obsday format: {obsday}. Expected format is 'YYYYMMDD'."
            )

    def test_get_last_valid_night_report(self):
        response_get = requests.Response()
        response_get.status_code = 200
        self.mock_requests_get.return_value = response_get

        # Return None if there are no reports
        response_get.json = lambda: []
        assert get_last_valid_night_report() is None

        reports = [
            {"id": 3, "date_added": "2025-09-30T12:00:00Z"},
            {"id": 2, "date_added": "2025-09-29T12:00:00Z"},
            {"id": 1, "date_added": "2025-09-28T12:00:00Z"},
        ]
        response_get.json = lambda: reports
        assert get_last_valid_night_report() is reports[0]

        # mock_get.stop()

    def test_get_last_valid_night_report_fails(self):
        response_get = requests.Response()
        response_get.status_code = 500
        self.mock_requests_get.return_value = response_get

        # Raises an exception if query to get
        # the last night report fails
        with self.assertRaises(Exception):
            get_last_valid_night_report()
