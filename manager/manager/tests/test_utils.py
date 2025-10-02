import pytest
from django.test import TestCase
from django.test.utils import override_settings

from manager.utils import arrange_nightlydigest_urls_for_obsday


class UtilsTestCase(TestCase):

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
