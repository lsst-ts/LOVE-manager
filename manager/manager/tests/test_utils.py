import random
from unittest.mock import patch

import pytest
import requests
from django.test import TestCase
from django.test.utils import override_settings

from manager.utils import (
    arrange_nightlydigest_urls_for_obsday,
    get_last_valid_night_report,
    get_nightreport_cscs_status_from_efd,
    get_nightreport_observatory_status_from_efd,
)

observatory_status_efd_response = {
    "MTMount-0-azimuth": {
        "actualPosition": [
            {"ts": "2025-10-24 19:22:12.914495+00:00", "value": -32.0348721139252}
        ]
    },
    "MTMount-0-elevation": {
        "actualPosition": [
            {"ts": "2025-10-24 19:22:12.886953+00:00", "value": 89.940244604426}
        ]
    },
    "MTMount-0-logevent_mirrorCoversMotionState": {
        "state": [{"ts": "2025-10-24 08:42:57.537999+00:00", "value": 1}]
    },
    "MTMount-0-logevent_oilSupplySystemState": {
        "powerState": [{"ts": "2025-10-21 17:38:43.939533+00:00", "value": 1}]
    },
    "MTMount-0-logevent_mainAxesPowerSupplySystemState": {
        "powerState": [{"ts": "2025-10-24 18:42:20.613430+00:00", "value": 1}]
    },
    "MTMount-0-logevent_elevationLockingPinMotionState": {
        "state": [{"ts": "2025-10-24 18:53:15.919564+00:00", "value": 2}]
    },
    "MTDome-0-azimuth": {
        "positionActual": [
            {"ts": "2025-10-24 19:22:04.829711+00:00", "value": 327.9999084472656}
        ]
    },
    "MTRotator-0-rotation": {
        "actualPosition": [
            {"ts": "2025-10-24 19:22:13.100240+00:00", "value": -0.0016296546160410818}
        ]
    },
    "ATMCS-0-mount_AzEl_Encoders": {
        "azimuthCalculatedAngle0": [
            {"ts": "2025-10-24 19:22:03.259886+00:00", "value": 15.1014567}
        ],
        "elevationCalculatedAngle0": [
            {"ts": "2025-10-24 19:22:03.259886+00:00", "value": 69.9999993}
        ],
    },
    "ATDome-0-position": {
        "azimuthPosition": [{"ts": "2025-10-24 19:22:04.123028+00:00", "value": 104.66}]
    },
    "ATPneumatics-0-logevent_m1CoverState": {
        "state": [{"ts": "2025-10-24 15:45:44.900717+00:00", "value": 6}]
    },
}

cscs_status_efd_response = {
    "MTMount-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 08:42:28.722677+00:00", "value": 1}]
    },
    "MTM1M3-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 18:07:29.756257+00:00", "value": 2}]
    },
    "MTAOS-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 19:15:04.343931+00:00", "value": 2}]
    },
    "MTM2-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-15 12:11:40.536744+00:00", "value": 2}]
    },
    "MTDome-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 18:49:35.972748+00:00", "value": 2}]
    },
    "MTDomeTrajectory-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 19:13:55.004857+00:00", "value": 2}]
    },
    "MTHexapod-1-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 19:14:21.026974+00:00", "value": 2}]
    },
    "MTHexapod-2-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 19:14:08.988283+00:00", "value": 2}]
    },
    "MTRotator-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 19:13:39.644249+00:00", "value": 2}]
    },
    "MTPtg-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-23 07:40:04.094982+00:00", "value": 2}]
    },
    "MTM1M3TS-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 18:13:49.147085+00:00", "value": 2}]
    },
    "MTCamera-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-23 21:00:34.303127+00:00", "value": 2}]
    },
    "ATMCS-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:47.928323+00:00", "value": 2}]
    },
    "ATPtg-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:31.353509+00:00", "value": 2}]
    },
    "ATDome-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:31.917250+00:00", "value": 2}]
    },
    "ATDomeTrajectory-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:31.336460+00:00", "value": 2}]
    },
    "ATAOS-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:31.322111+00:00", "value": 2}]
    },
    "ATPneumatics-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:45.007918+00:00", "value": 2}]
    },
    "ATHexapod-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:31.544154+00:00", "value": 2}]
    },
    "ATCamera-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:06.566642+00:00", "value": 2}]
    },
    "ATOODS-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:03.484459+00:00", "value": 2}]
    },
    "ATHeaderService-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:03.639109+00:00", "value": 2}]
    },
    "ATSpectrograph-0-logevent_summaryState": {
        "summaryState": [{"ts": "2025-10-24 15:41:19.389653+00:00", "value": 2}]
    },
}


class UtilsTestCase(TestCase):
    def setUp(self):
        self.requests_get_patcher = patch("requests.get")
        self.mock_requests_get = self.requests_get_patcher.start()
        self.requests_post_patcher = patch("requests.post")
        self.mock_requests_post = self.requests_post_patcher.start()

    def tearDown(self):
        self.requests_get_patcher.stop()
        self.requests_post_patcher.stop()

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

    def test_get_nightreport_observatory_status_from_efd(self):
        response_post = requests.Response()
        response_post.status_code = 200
        response_post.json = lambda: observatory_status_efd_response
        self.mock_requests_post.return_value = response_post

        observatory_status = get_nightreport_observatory_status_from_efd()
        expected_payload_keys = [
            "simonyiAzimuth",
            "simonyiElevation",
            "simonyiDomeAzimuth",
            "simonyiRotator",
            "simonyiMirrorCoversState",
            "simonyiOilSupplySystemState",
            "simonyiPowerSupplySystemState",
            "simonyiLockingPinsSystemState",
            "auxtelAzimuth",
            "auxtelElevation",
            "auxtelDomeAzimuth",
            "auxtelMirrorCoversState",
        ]
        for key in expected_payload_keys:
            assert key in observatory_status

    def test_get_nightreport_observatory_status_from_efd_fails(self):
        response_post = requests.Response()
        response_post.status_code = 500
        self.mock_requests_post.return_value = response_post

        # Fails when EFD query fails
        with self.assertRaises(Exception):
            get_nightreport_observatory_status_from_efd()

        # Fails if response has missing keys
        random_key = random.choice(list(observatory_status_efd_response.keys()))
        observatory_status_clone = observatory_status_efd_response.copy()
        del observatory_status_clone[random_key]
        response_post.status_code = 200
        response_post.json = lambda: observatory_status_clone
        with self.assertRaises(Exception):
            get_nightreport_observatory_status_from_efd()

    def test_get_nightreport_cscs_status_from_efd(self):
        response_post = requests.Response()
        response_post.status_code = 200
        response_post.json = lambda: cscs_status_efd_response
        self.mock_requests_post.return_value = response_post

        cscs_status = get_nightreport_cscs_status_from_efd()
        expected_payload_keys = [
            "MTMount:0",
            "MTM1M3:0",
            "MTAOS:0",
            "MTM2:0",
            "MTDome:0",
            "MTDomeTrajectory:0",
            "MTHexapod:1",
            "MTHexapod:2",
            "MTRotator:0",
            "MTPtg:0",
            "MTM1M3TS:0",
            "MTCamera:0",
            "ATMCS:0",
            "ATPtg:0",
            "ATDome:0",
            "ATDomeTrajectory:0",
            "ATAOS:0",
            "ATPneumatics:0",
            "ATHexapod:0",
            "ATCamera:0",
            "ATOODS:0",
            "ATHeaderService:0",
            "ATSpectrograph:0",
        ]
        for key in expected_payload_keys:
            assert key in cscs_status

    def test_get_nightreport_cscs_status_from_efd_fails(self):
        response_post = requests.Response()
        response_post.status_code = 500
        self.mock_requests_post.return_value = response_post

        # Fails when EFD query fails
        with self.assertRaises(Exception):
            get_nightreport_cscs_status_from_efd()

        # Fails if response has missing keys
        random_key = random.choice(list(cscs_status_efd_response.keys()))
        cscs_status_clone = cscs_status_efd_response.copy()
        del cscs_status_clone[random_key]
        response_post.status_code = 200
        response_post.json = lambda: cscs_status_clone
        with self.assertRaises(Exception):
            get_nightreport_cscs_status_from_efd()
