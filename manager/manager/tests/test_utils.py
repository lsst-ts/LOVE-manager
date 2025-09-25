import pytest

from manager.utils import arrange_nightlydigest_urls_for_obsday


@pytest.fixture
def mock_nightlydigest_base_url(monkeypatch):
    """Fixture to mock the NIGHTLYDIGEST_BASE_URL environment variable."""
    monkeypatch.setenv("NIGHTLYDIGEST_BASE_URL", "https://example.com/nightlydigest")


def test_arrange_nightlydigest_urls_for_obsday(mock_nightlydigest_base_url):
    obsday = 20231010
    expected_urls = {
        "simonyi": (
            "https://example.com/nightlydigest"
            "/?startDayobs=20231010&endDayobs=20231010&telescope=Simonyi"
        ),
        "auxtel": (
            "https://example.com/nightlydigest"
            "/?startDayobs=20231010&endDayobs=20231010&telescope=AuxTel"
        ),
    }

    result = arrange_nightlydigest_urls_for_obsday(obsday)
    assert result == expected_urls


def test_arrange_nightlydigest_urls_for_obsday_invalid_obsday():
    invalid_obsdays = [2025091, 202509100, "2025091", None]

    for obsday in invalid_obsdays:
        with pytest.raises(
            ValueError, match="obsday must be an integer in YYYYMMDD format"
        ):
            arrange_nightlydigest_urls_for_obsday(obsday)
