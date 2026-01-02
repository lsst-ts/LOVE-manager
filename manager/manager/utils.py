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


import json
import os
import re
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tempfile import TemporaryFile
from urllib.parse import quote

import astropy.time
import requests
from astropy.time import Time
from astropy.units import hour
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage
from pytz import timezone
from rest_framework.response import Response

# Constants
JSON_RESPONSE_LOCAL_STORAGE_NOT_ALLOWED = {"error": "Local storage not allowed."}
JSON_RESPONSE_ERROR_NOT_VALID_JSON = {"error": "Not a valid JSON response."}

ERROR_OBS_TICKETS = f"Error getting issues from {os.environ.get('JIRA_API_HOSTNAME')}"

OBS_ISSUE_TYPE_ID = "10065"
OBS_TIME_LOST_FIELD = "customfield_10106"
OBS_SYSTEMS_FIELD = "customfield_10476"
OBS_TICKETS_FIELDS = f"summary,created,creator,system,{OBS_TIME_LOST_FIELD},{OBS_SYSTEMS_FIELD}"

DATETIME_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

JIRA_PROJECTS_WITH_TIME_LOSS = ["OBS"]

CSC_SUMMARY_STATE_MAP = {
    0: "UNKNOWN",
    1: "DISABLED",
    2: "ENABLED",
    3: "FAULT",
    4: "OFFLINE",
    5: "STANDBY",
}

MTMOUNT_DEPLOYABLE_MOTION_STATE_MAP = {
    0: "RETRACTED",
    1: "DEPLOYED",
    2: "RETRACTING",
    3: "DEPLOYING",
    4: "LOST",
}

MTMOUNT_POWER_STATE_MAP = {
    0: "OFF",
    1: "ON",
    2: "FAULT",
    3: "TURNING_ON",
    4: "TURNING_OFF",
    15: "UNKNOWN",
}

MTMOUNT_MT_MOUNT_ELEVATION_LOCKING_PIN_MOTION_STATE_MAP = {
    0: "LOCKED",
    1: "TEST",
    2: "UNLOCKED",
    3: "MOVING",
    4: "MISMATCH",
}

ATPNEUMATICS_MIRROR_COVER_STATE_MAP = {
    1: "DISABLED",
    2: "ENABLED",
    3: "FAULT",
    4: "OFFLINE",
    5: "STANDBY",
    6: "CLOSED",
    7: "OPENED",
    8: "IN MOTION",
    9: "INVALID",
    0: "UNKNOWN",
}

NIGHT_REPORT_CSCS = [
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

EFD_INSTACES = {
    "summit-lsp.lsst.codes": "summit_efd",
    "base-lsp.lsst.codes": "base_efd",
    "tucson-teststand.lsst.codes": "tucson_teststand_efd",
}


class RemoteStorage(Storage):
    PREFIX_THUMBNAIL = "thumbnails/"
    PREFIX_CONFIG = "configs/"

    ALLOWED_FILE_TYPES = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "application/json",
        "binary/octet-stream",
    ]

    def __init__(self, location=None):
        self.location = (
            f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/lfa"
        )

    def _validate_LFA_url(self, name):
        """Validate the name of the file is a valid LFA url."""
        allowed_file_types = [t.split("/")[1] for t in RemoteStorage.ALLOWED_FILE_TYPES]
        lfa_url_pattern = rf"https?:\/\/?.*\/.*({'|'.join(allowed_file_types)})$"
        if not re.match(lfa_url_pattern, name):
            raise ValueError(f"Invalid remote url: {name}")

    def _open(self, name, mode="rb"):
        """Return the remote file object."""

        # Validate name is a remote url
        self._validate_LFA_url(name)

        # Make request to remote server
        response = requests.get(name)
        if response.status_code != 200:
            raise FileNotFoundError(f"Error requesting file at: {name}.")

        # Create temporary file to store the response
        tf = TemporaryFile()

        # If request is for thumbnail (image file)
        if (
            response.headers.get("content-type") in RemoteStorage.ALLOWED_FILE_TYPES[:3]
        ) or response.headers.get("content-type") == RemoteStorage.ALLOWED_FILE_TYPES[4]:
            byte_encoded_response = response.content
            tf.write(byte_encoded_response)
            # Before sending the file,
            # we need to reset the file pointer to the beginning
            tf.seek(0)
            return tf

        # If request is for config files (json file)
        if (
            response.headers.get("content-type") == RemoteStorage.ALLOWED_FILE_TYPES[3]
            or response.headers.get("content-type") == RemoteStorage.ALLOWED_FILE_TYPES[4]
        ):
            json_response = response.json()
            byte_encoded_response = json.dumps(json_response).encode("ascii")
            tf.write(byte_encoded_response)
            # Before sending the file,
            # we need to reset the file pointer to the beginning
            tf.seek(0)
            return tf

        # Raise error if file type is not supported
        raise ValueError(f"File type not supported: {response.headers.get('content-type')}")

    def _save(self, name, content):
        """Upload the file to the remote server.

        Notes
        -----
        This methods connects to the
        LOVE-commander lfa endpoint to upload the file.
        """
        if name.startswith(RemoteStorage.PREFIX_THUMBNAIL):
            url = f"{self.location}/upload-love-thumbnail"
        elif name.startswith(RemoteStorage.PREFIX_CONFIG):
            url = f"{self.location}/upload-love-config-file"

        # Before sending the file,
        # we need to reset the file pointer to the beginning
        content.seek(0)
        upload_file_response = requests.post(url, files={"uploaded_file": content})
        if upload_file_response.status_code != 200:
            raise ValueError("Error uploading file to the LFA.")
        return upload_file_response.json()["url"]

    def delete(self, name):
        pass

    def exists(self, name):
        return False

    def url(self, name):
        """Return the URL of the remote file."""
        if "http" in name:
            return name
        return f"{settings.MEDIA_URL}{name}"


def upload_to_lfa(request, *args, **kwargs):
    """Connects to LFA API to upload a new file

    Params
    ------
    request: Request
        The Request object
    args: list
        List of additional arguments. Currently unused
    kwargs: dict
        Dictionary with request arguments. Currently unused

    Returns
    -------
    Response
        The response and status code
        of the request to the LOVE-commander LFA API
    """

    option = kwargs.get("option", None)
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/lfa/{option}"

    if len(request.FILES.getlist("file[]")) == 0:
        return Response({"ack": "No files to upload"}, status=400)

    if option == "upload-file":
        uploaded_files_urls = []
        files_to_upload = request.FILES.getlist("file[]")
        for file in files_to_upload:
            upload_file_response = requests.post(url, files={"uploaded_file": file})
            if upload_file_response.status_code == 200:
                uploaded_files_urls.append(upload_file_response.json().get("url"))

        if len(uploaded_files_urls) != len(files_to_upload):
            return Response({"ack": "Error when uploading files"}, status=400)

        return Response(
            {"ack": "All files uploaded correctly", "urls": uploaded_files_urls},
            status=200,
        )

    return Response({"ack": "Option not found"}, status=400)


def get_jira_title(request_data):
    """Generate title for a jira ticket

    Parameters:
    -----------
    request_data: dict
        Request data

    Returns:
    --------
    title: str
        Jira ticket title
    """
    request_type = request_data.get("request_type")
    jira_title = request_data.get("jira_issue_title")

    if jira_title is not None and jira_title != "":
        return jira_title

    return "LOVE generated: " + request_type


def get_jira_description(request_data):
    """Generate description for a jira ticket

    Parameters:
    -----------
    request_data: dict
        Request data

    Notes:
    ------
    The expected structure of the request_data dictionary is as follows:

    If request_type is "exposure":
        {
            "request_type": "<exposure|narrative>",
            "obs_id": "<observation id>",
            "instrument": "<instrument>",
            "exposure_flag": "<exposure flag>",
        }

    If request_type is "narrative":
        {
            "request_type": "<exposure|narrative>",
            "date_begin": "<begin date>",
            "date_end": "<end date>",
        }

    The format of date_begin and date_end is: "YYYY-MM-DDTHH:MM:SS.ssssss".

    Also both shall contain:
        {
            "lfa_files_urls": "<list of urls of
            the files uploaded to the LFA>",
            "message_text": "<message text>",
            "user_id": "<user id>",
            "user_agent": "<user agent>",
        }

    Returns:
    --------
    description: str
        Jira ticket description

    Raises:
    -------
    Exception
        If there is an error reading the request data
    """
    # Shared params
    request_type = request_data["request_type"]
    try:
        lfa_files_urls = request_data["lfa_files_urls"]
        message_log = request_data["message_text"]
        user_id = request_data["user_id"]
        user_agent = request_data["user_agent"]
    except Exception as e:
        raise Exception("Error reading params") from e

    # Exposure log params
    if request_type == "exposure":
        try:
            obs_id = request_data["obs_id"]
            instrument = request_data["instrument"]
            exposure_flag = request_data["exposure_flag"]
        except Exception as e:
            raise Exception("Error reading params") from e
        description = (
            "*Created by* "
            + user_id
            + " *from* "
            + user_agent
            + "\n"
            + "*Observation ids:* "
            + str(obs_id)
            + "\n"
            + "*Instrument:* "
            + instrument
            + "\n"
            + "*Exposure flag:* "
            + exposure_flag
            + "\n"
            + "*Files:* "
            + "\n"
            + str(lfa_files_urls)
            + "\n\n"
            + message_log
        )
    # Narrative log params
    if request_type == "narrative":
        try:
            begin_date = request_data["date_begin"]
            end_date = request_data["date_end"]
        except Exception as e:
            raise Exception("Error reading params") from e

        description = (
            "*Created by* "
            + user_id
            + " *from* "
            + user_agent
            + "\n"
            + "*Time of incident:* "
            + "".join(begin_date.split(".")[:-1])
            + " *-* "
            + "".join(end_date.split(".")[:-1])
            + "\n"
            + "*Files:* "
            + "\n"
            + str(lfa_files_urls)
            + "\n\n"
            + message_log
        )

    return description if description is not None else ""


def jira_ticket(request_data):
    """Connect to the Rubin Observatory JIRA Cloud REST API to
    create a ticket on the OBS project.

    For details on the fields available for the JIRA Cloud REST API see:
    - https://rubinobs.atlassian.net/rest/api/latest/field

    For details on the OBS project see:
    - https://rubinobs.atlassian.net/rest/api/latest/project/OBS

    For more information on the REST API endpoints refer to:
    - https://developer.atlassian.com/cloud/jira/platform/rest/v3
    - https://developer.atlassian.com/cloud/jira/platform/\
        basic-auth-for-rest-apis/

    Params
    ------
    request_data: dict
        Request data

    Returns
    -------
    Response
        The response and status code of the request to the JIRA API

        For successful requests, the response will contain the following keys:
        - ack: A message indicating the request was successful
        - url: The url of the created ticket

        For failed requests, the response will contain the following keys:
        - ack: A message indicating the request failed
        - error: The errors from the JIRA API
    """
    if "request_type" not in request_data:
        return Response({"ack": "Error reading request type"}, status=400)

    obs_system_selection = request_data.get("jira_obs_selection")

    try:
        jira_payload = {
            "fields": {
                "issuetype": {"id": OBS_ISSUE_TYPE_ID},
                # If the JIRA_PROJECT_ID environment variable is not set,
                # the project id is set to the OBS project by default: 10063.
                # Set it in case the OBS project id has changed for any reason
                # and update the default value above and in the following line.
                "project": {"id": os.environ.get("JIRA_PROJECT_ID", "10063")},
                "summary": get_jira_title(request_data),
                "description": get_jira_description(request_data),
                # customfield_15602 which represents the URGENT flag
                # is not yet migrated to the new JIRA cloud OBS project.
                # The following block is commented until the migration is done.
                # TODO: DM-43066
                # "customfield_15602": (
                #     "on" if int(request_data.get("level", 0)) >= 100
                #     else "off"
                # ),
                OBS_TIME_LOST_FIELD: float(request_data.get("time_lost", 0)),
            },
        }

        if obs_system_selection:
            jira_payload["fields"][OBS_SYSTEMS_FIELD] = json.loads(obs_system_selection)
    except Exception as e:
        return Response(
            {
                "ack": "Error creating jira payload",
                "error": str(e),
            },
            status=400,
        )

    headers = {
        "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
        "content-type": "application/json",
    }
    url = f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/issue/"
    response = requests.post(url, json=jira_payload, headers=headers)
    response_data = response.json()
    if response.status_code == 201:
        return Response(
            {
                "ack": "Jira ticket created",
                "url": f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/{response_data['key']}",
            },
            status=200,
        )

    return Response(
        {
            "ack": "Jira ticket could not be created",
            "error": (str(response_data["errors"]) if "errors" in response_data else str(response_data)),
        },
        status=400,
    )


def update_time_lost(jira_id: int, add_time_lost: float = 0.0) -> Response:
    """Connect to the Rubin Observatory JIRA Cloud REST API to
    update time_lost field in a given jira ticket

    Params
    ------
    jira_id: int
        Jira ID
    add_time_lost: float
        time value given from comment

    Returns
    -------
    Response
        The response and status code of the request to the JIRA API
        200 if the time_lost field was successfully updated
        400 if the time_lost field was not updated
    """
    headers = {
        "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
        "content-type": "application/json",
    }
    url = f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/issue/{jira_id}/"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        jira_ticket_fields = response.json().get("fields", {})
        time_lost_value = jira_ticket_fields.get(OBS_TIME_LOST_FIELD, 0.0)
        existent_time_lost = float(time_lost_value) if time_lost_value else 0.0
        jira_payload = {
            "fields": {
                OBS_TIME_LOST_FIELD: existent_time_lost + add_time_lost,
            },
        }
        response = requests.put(url, json=jira_payload, headers=headers)
        if response.status_code == 204:
            return Response(
                {
                    "ack": "Jira time_lost field updated",
                    "url": f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/{jira_id}",
                },
                status=200,
            )
    return Response(
        {
            "ack": "Jira time_lost field could not be updated",
        },
        status=400,
    )


def jira_comment(request_data):
    """Connect to the Rubin Observatory JIRA Cloud REST API to
    make a comment on a previously created ticket.

    Also update the time_lost field if the jira project
    supports it and the time_lost parameter is present in the request_data.

    For more information on the REST API endpoints refer to:
    - https://developer.atlassian.com/cloud/jira/platform/rest/v3
    - https://developer.atlassian.com/cloud/jira/platform/\
        basic-auth-for-rest-apis/

    Params
    ------
    request_data: dict
        Request data

    Returns
    -------
    Response
        The response and status code of the request to the JIRA API

    Raises
    ------
    Exception
        If there is an error reading the request data
    """
    if "jira_issue_id" not in request_data:
        return Response({"ack": "Error reading the JIRA issue ID"}, status=400)

    jira_id = request_data.get("jira_issue_id")
    jira_project = jira_id.split("-")[0]

    try:
        jira_payload = {
            "body": get_jira_description(request_data),
        }
    except Exception as e:
        return Response({"ack": f"Error creating jira payload: {e}"}, status=400)

    if "time_lost" in request_data and jira_project in JIRA_PROJECTS_WITH_TIME_LOSS:
        timelost_response = update_time_lost(
            jira_id=jira_id, add_time_lost=float(request_data.get("time_lost", 0.0))
        )
        if timelost_response.status_code != 200:
            return timelost_response

    headers = {
        "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
        "content-type": "application/json",
    }
    url = f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/issue/{jira_id}/comment"
    response = requests.post(url, json=jira_payload, headers=headers)

    if response.status_code == 201:
        return Response(
            {
                "ack": "Jira comment created",
                "url": f"https://{os.environ.get('JIRA_API_HOSTNAME')}/browse/{jira_id}",
            },
            status=200,
        )
    return Response(
        {
            "ack": "Jira comment could not be created",
        },
        status=400,
    )


def handle_jira_payload(request, lfa_urls=[]):
    """Handle the JIRA payload and send it to the JIRA API

    Parameters
    ----------
    request : Request
        The request object
    lfa_urls : list
        List of urls of the files uploaded to the LFA
        Which will be attached to the Jira ticket

    Returns
    -------
    Response
        The response and status code of the request to the JIRA API
    """
    payload_data = request.data.copy()
    payload_data["user_agent"] = "LOVE"
    payload_data["user_id"] = f"{request.user}@{request.get_host()}"
    payload_data["lfa_files_urls"] = lfa_urls

    if request.data.get("jira_new") == "true":
        return jira_ticket(payload_data)
    return jira_comment(payload_data)


def get_jira_obs_report(request_data):
    """Connect to the Rubin Observatory JIRA Cloud REST API to
    query all issues of the OBS project for a certain obs day.

    For more information on the REST API endpoints refer to:
    - https://developer.atlassian.com/cloud/jira/platform/rest/v3
    - https://developer.atlassian.com/cloud/jira/platform/\
        basic-auth-for-rest-apis/

    Parameters
    ----------
    request_data : `dict`
        The request data

    Notes
    -----
    The JIRA REST API query is based on the user timezone so
    we need to account for the timezone difference between the user and the
    server. The user timezone is obtained from the JIRA API.

    Returns
    -------
    List
        List of dictionaries containing the following keys:
        - key: The issue key
        - summary: The issue summary
        - time_lost: The time lost in the issue
        - reporter: The issue reporter
        - created: The issue creation date
    """
    intitial_day_obs_tai = get_obsday_to_tai(request_data.get("day_obs"))
    final_day_obs_tai = intitial_day_obs_tai + timedelta(days=1)

    headers = {
        "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
        "content-type": "application/json",
    }

    # Get user timezone
    url = f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/myself"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_timezone = timezone(response.json()["timeZone"])
    else:
        raise Exception(f"Error getting user timezone from {os.environ.get('JIRA_API_HOSTNAME')}")

    start_date_user_datetime = intitial_day_obs_tai.replace(tzinfo=timezone("UTC")).astimezone(user_timezone)
    end_date_user_datetime = final_day_obs_tai.replace(tzinfo=timezone("UTC")).astimezone(user_timezone)

    initial_day_obs_string = start_date_user_datetime.strftime("%Y-%m-%d")
    final_day_obs_string = end_date_user_datetime.strftime("%Y-%m-%d")
    start_date_user_time_string = start_date_user_datetime.time().strftime("%H:%M")
    end_date_user_time_string = end_date_user_datetime.time().strftime("%H:%M")

    # JQL query to find issues created on a specific date
    jql_query = (
        f"project = 'OBS' "
        f"AND created >= '{initial_day_obs_string} {start_date_user_time_string}' "
        f"AND created <= '{final_day_obs_string} {end_date_user_time_string}'"
    )

    url = (
        f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest"
        f"/search/jql?jql={quote(jql_query)}&fields={OBS_TICKETS_FIELDS}"
    )
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        issues = response.json()["issues"]
        try:
            return [
                {
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "time_lost": (
                        issue["fields"][OBS_TIME_LOST_FIELD]
                        if issue["fields"][OBS_TIME_LOST_FIELD] is not None
                        else 0.0
                    ),
                    "reporter": issue["fields"]["creator"]["displayName"],
                    "created": issue["fields"]["created"].split(".")[0],
                    "systems": parse_obs_issue_systems(issue),
                }
                for issue in issues
            ]
        except KeyError as e:
            traceback.print_exc()
            raise Exception(f"{ERROR_OBS_TICKETS}. Parsing JIRA response failed: missing field {e}")
    raise Exception(ERROR_OBS_TICKETS)


def get_client_ip(request):
    """Return the client IP address.

    Parameters
    ----------
    request : HttpRequest
        The request object

    Returns
    -------
    String
        The client IP address
    """
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        return x_real_ip
    return request.META.get("REMOTE_ADDR")


def get_obsday_from_tai(tai):
    """Return the observing day from a TAI timestamp.

    If the date is after 12:00 UTC, the day is the same day.
    If the date is before 12:00 UTC, the day is the previous day.

    Parameters
    ----------
    tai : `datetime.datetime`
        TAI timestamp

    Returns
    -------
    String
        The observing day in the format "YYYYMMDD"
    """
    observing_day = tai.strftime("%Y%m%d")
    if tai.hour < 12:
        observing_day = (tai - timedelta(days=1)).strftime("%Y%m%d")
    return observing_day


def get_obsday_to_tai(obsday):
    """Return the TAI timestamp from an observing day.

    The TAI timestamp is set to 12:00 UTC of the observing day.

    Parameters
    ----------
    obsday : `int`
        The observing day in the format "YYYYMMDD" as an integer

    Returns
    -------
    `datetime.datetime`
        The TAI timestamp
    """
    obsday_iso = get_obsday_iso(obsday)
    return Time(f"{obsday_iso}T12:00:00", scale="tai").datetime


def get_obsday_iso(obsday):
    """Return the observing day in ISO format.

    Parameters
    ----------
    obsday : `int`
        The observing day in the format "YYYYMMDD" as an integer

    Returns
    -------
    String
        The observing day in ISO format
    """
    return f"{str(obsday)[:4]}-{str(obsday)[4:6]}-{str(obsday)[6:8]}"


def get_tai_to_utc() -> float:
    """Return the difference in seconds between TAI and UTC Timestamps.

    Returns
    -------
    Int
        The number of seconds of difference between TAI and UTC times
    """
    t = Time.now()
    dt = t.datetime.timestamp() - t.tai.datetime.timestamp()
    return dt


def get_tai_from_utc(utc):
    """Return the TAI timestamp from an UTC timestamp.

    Parameters
    ----------
    utc : `datetime.datetime`
        UTC timestamp

    Returns
    -------
    `datetime.datetime`
        The TAI timestamp
    """
    return Time(utc, scale="utc").tai.datetime


def get_times():
    """Return relevant time measures.

    Returns
    -------
    Dict
        Dictionary containing the following keys:
        - utc: current time in UTC scale as a unix timestamp (seconds)
        - tai: current time in UTC scale as a unix timestamp (seconds)
        - mjd: current time as a modified julian date
        - sidereal_summit: current time as a sidereal_time
        w/respect to the summit location (hourangles)
        - sidereal_greenwich: current time as a sidereal_time
        w/respect to Greenwich location (hourangles)
        - tai_to_utc: The number of seconds of difference
        between TAI and UTC times (seconds)
    """
    t = Time.now()
    t_utc = t.datetime.timestamp()
    t_tai = t.tai.datetime.timestamp()
    shifted_iso = (t.tai - 12 * hour).iso
    observing_day = shifted_iso[0:10].replace("-", "")
    sidereal_summit = t.sidereal_time("apparent", longitude=-70.749417, model=None)
    sidereal_greenwich = t.sidereal_time("apparent", longitude="greenwich", model=None)
    return {
        "utc": t_utc,
        "tai": t_tai,
        "mjd": t.mjd,
        "observing_day": observing_day,
        "sidereal_summit": sidereal_summit.value,
        "sidereal_greenwich": sidereal_greenwich.value,
        "tai_to_utc": t_utc - t_tai,
    }


def assert_time_data(time_data):
    """Asserts the structure of the time_data dictionary

    The expected structure is the following:

    .. code-block:: json

        {
            "utc": "<current time in UTC scale as a unix timestamp (seconds),
            in float format>",
            "tai": "<current time in UTC scale as a unix timestamp (seconds),
            in float format>",
            "mjd": "<current time as a modified julian date, in float format>",
            "sidereal_summit": "<current time as a sidereal_time w/respect
                to the summit location (hourangles), in float format>",
            "sidereal_greenwich": "<current time as a sidereal_time w/respect
                to Greenwich location (hourangles), in float format>",
            "tai_to_utc": "<The number of seconds of difference between
            TAI and UTC times (seconds), in float format>",
        }

    Parameters
    ----------
    time_data : dict
        dictionary containing the time data
        in different formats, indexed by format

    Returns
    -------
    bool
        True if the time data has the correct format, False if not
    """

    if not isinstance(time_data["utc"], float):
        return False
    if not isinstance(time_data["tai"], float):
        return False
    if not isinstance(time_data["mjd"], float):
        return False
    if not isinstance(time_data["sidereal_summit"], float):
        return False
    if not isinstance(time_data["sidereal_greenwich"], float):
        return False
    if not isinstance(time_data["tai_to_utc"], float):
        return False
    return True


def send_smtp_email(to, subject, html_content, plain_content):
    """Send an email using the SMTP protocol.

    Parameters
    ----------
    to : `str`
        The email address of the recipient
    subject : `str`
        The subject of the email
    html_content : `str`
        The content of the email in HTML format
    plain_content : `str`
        The content of the email in plain text format

    Notes
    -----
    The following environment variables are required to send the email:
    - SMTP_USER: The SMTP user name
    - SMTP_PASSWORD: The SMTP user password

    If the SMTP_USER has the @lsst.org sufix, then it is stripped.

    Raises
    ------
    ValueError
        If the SMTP_USER or SMTP_PASSWORD environment variables are not set

    Returns
    -------
    bool
        True if the email was sent successfully, False if not
    """
    smtp_user = os.environ.get("SMTP_USER")
    if not smtp_user:
        raise ValueError("SMTP_USER environment variable is not set")

    smtp_password = os.environ.get("SMTP_PASSWORD")
    if not smtp_password:
        raise ValueError("SMTP_PASSWORD environment variable is not set")

    if smtp_user.endswith("@lsst.org"):
        smtp_user = smtp_user.replace("@lsst.org", "")

    try:
        # Create message container - the correct MIME type
        # is multipart/alternative.
        msg = MIMEMultipart("alternative")
        part1 = MIMEText(plain_content, "plain")
        part2 = MIMEText(html_content, "html")

        # Attach parts into message container.
        # According to RFC 2046, the last part of
        # a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        msg["Subject"] = subject
        msg["From"] = f"{smtp_user}@lsst.org"
        msg["To"] = to

        s = smtplib.SMTP("exch-ls.lsst.org", "587")
        s.starttls()
        s.login(smtp_user, smtp_password)
        s.sendmail(msg["From"], msg["To"], msg.as_string())
        s.quit()
        return True
    except Exception:
        return False


def arrange_nightreport_email(report, plain=False):
    """Arrange the night report email in HTML format
    or plain text format if specified.

    Parameters
    ----------
    report : `dict`
        The night report data

    Notes:
    ------
    The expected parameters of the report dictionary are the following:
    - day_obs: The observing day in the format "YYYYMMDD"
    - summary: The summary of the observing night
    - weather: The weather summary of the observing night
    - maintel_summary: The Simonyi telescope summary of the observing night
    - auxtel_summary: The AuxTel telescope summary of the observing night
    - confluence_url: The URL of the confluence page with the full report
    - obs_issues: The list of OBS issues during the night
    - observers_crew: The list of observers that participated during the night
    - observatory_status: The status of the observatory during the night
    - cscs_status: The status of the CSCs during the night

    Returns
    -------
    str
        The night report email in HTML format or plain text format
    """

    expected_keys = [
        "day_obs",
        "summary",
        "weather",
        "maintel_summary",
        "auxtel_summary",
        "confluence_url",
        "obs_issues",
        "observers_crew",
        "observatory_status",
        "cscs_status",
    ]
    missing_keys = [key for key in expected_keys if key not in report]
    if missing_keys:
        raise ValueError(f"Missing keys in report: {', '.join(missing_keys)}")

    url_jira_obs_tickets = "https://rubinobs.atlassian.net/jira/software/c/projects/OBS/boards/232"
    nightlydigest_urls = arrange_nightlydigest_urls_for_obsday(report["day_obs"])

    NIGHTLYDIGEST_TITLE = "Nightly Digest:"
    SUMMARY_TITLE = "Summary:"
    WEATHER_TITLE = "Weather summary:"
    MAINTEL_SUMMARY_TITLE = "Simonyi summary:"
    AUXTEL_SUMMARY_TITLE = "AuxTel summary:"
    ADDITIONAL_RESOURCES_TITLE = "Additional resources:"
    SIGNED_MSG = "Submitted by:"
    LINK_MSG_OBS = "OBS fault reports from last 24 hours:"
    LINK_MSG_CONFLUENCE = "Link to night plan page:"
    DETAILED_ISSUE_REPORT_TITLE = "Detailed issue report:"
    OBSERVATORY_STATUS_TITLE = "Observatory status:"
    CSCS_STATUS_TITLE = "CSCs status:"

    if plain:
        return f"""{NIGHTLYDIGEST_TITLE}
{nightlydigest_urls["simonyi"]}

{SUMMARY_TITLE}
{report["summary"]}

{WEATHER_TITLE}
{report["weather"]}

{MAINTEL_SUMMARY_TITLE}
{report["maintel_summary"]}

{AUXTEL_SUMMARY_TITLE}
{report["auxtel_summary"]}

{OBSERVATORY_STATUS_TITLE}
{parse_observatory_status_to_plain_text(report["observatory_status"])}

{CSCS_STATUS_TITLE}
{parse_cscs_status_to_plain_text(report["cscs_status"])}

{ADDITIONAL_RESOURCES_TITLE}
- {LINK_MSG_OBS} {url_jira_obs_tickets}
- {LINK_MSG_CONFLUENCE} {report["confluence_url"]}

{DETAILED_ISSUE_REPORT_TITLE}
{
            parse_obs_issues_array_to_plain_text(report["obs_issues"])
            if len(report["obs_issues"]) > 0
            else "No issues reported."
        }

{SIGNED_MSG}
{", ".join(report["observers_crew"])}"""

    new_line_character = "\n"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            table {{
                font-family: Arial, sans-serif;
                border-collapse: collapse;
                width: 100%;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }}
        </style>
    </head>
    <body>
        <p>
            <span style="font-weight: bold;">{NIGHTLYDIGEST_TITLE}</span>
            <br>
            <a href="{nightlydigest_urls["simonyi"]}">{nightlydigest_urls["simonyi"]}</a>
        </p>
        <p>
            <span style="font-weight: bold;">{SUMMARY_TITLE}</span>
            <br>
            {report["summary"].replace(new_line_character, "<br>")}
        </p>
        <p>
            <span style="font-weight: bold;">{WEATHER_TITLE}</span>
            <br>
            {report["weather"].replace(new_line_character, "<br>")}
        </p>
        <p>
            <span style="font-weight: bold;">{MAINTEL_SUMMARY_TITLE}</span>
            <br>
            {report["maintel_summary"].replace(new_line_character, "<br>")}
        </p>
        <p>
            <span style="font-weight: bold;">{AUXTEL_SUMMARY_TITLE}</span>
            <br>
            {report["auxtel_summary"].replace(new_line_character, "<br>")}
        </p>
        <br>
        {parse_observatory_status_to_html_table(report["observatory_status"])}
        <br>
        {parse_cscs_status_to_html_table(report["cscs_status"])}
        <br>
        <p>
            <span style="font-weight: bold;">{ADDITIONAL_RESOURCES_TITLE}</span>
        </p>
        <ul>
            <li>
                {LINK_MSG_OBS}
                <a href="{url_jira_obs_tickets}">{url_jira_obs_tickets}</a>
            </li>
            <li>
                {LINK_MSG_CONFLUENCE}
                <a href="{report["confluence_url"]}">{report["confluence_url"]}</a>
            </li>
        </ul>
        <p>
            <span style="font-weight: bold;">{DETAILED_ISSUE_REPORT_TITLE}</span>
            <br>
            {
        parse_obs_issues_array_to_html_table(report["obs_issues"])
        if len(report["obs_issues"]) > 0
        else "No issues reported."
    }
        </p>
        <p>
            <span style="font-weight: bold;">{SIGNED_MSG}</span>
            <br>
            {", ".join(report["observers_crew"])}
        </p>
    </body>
    </html>
    """

    return html_content


def parse_obs_issues_array_to_html_table(obs_issues):
    """Parse the OBS issues array to an HTML table.

    Parameters
    ----------
    obs_issues : `list`
        List of OBS issues

    Notes
    -----
    Each element of the obs_issues list must be dictionary
    with the following keys:
    - key: The key of the issue
    - summary: The summary of the issue
    - time_lost: The time lost in hours
    - reporter: The reporter of the issue
    - created: The creation date of the issue

    If a key is missing, it will be replaced by a dash "-".

    Returns
    -------
    str
        The OBS issues in HTML table format
    """

    html_table = """
    <table style="width:100%">
        <tr>
            <th>Key</th>
            <th>Summary</th>
            <th>Reporter</th>
            <th>Created</th>
        </tr>
    """

    for issue in obs_issues:
        html_table += f"""
        <tr>
            <td>{issue.get("key", "-")}</td>
            <td>{issue.get("summary", "-")}</td>
            <td>{issue.get("reporter", "-")}</td>
            <td>{issue.get("created", "-")}</td>
        </tr>
        """

    html_table += "</table>"
    return html_table


def parse_obs_issues_array_to_plain_text(obs_issues):
    """Parse the OBS issues array to plain text.

    Parameters
    ----------
    obs_issues : `list`
        List of OBS issues

    Notes
    -----
    Each element of the obs_issues list must be dictionary
    with the following keys:
    - key: The key of the issue
    - summary: The summary of the issue
    - time_lost: The time lost in hours
    - reporter: The reporter of the issue
    - created: The creation date of the issue

    If a key is missing, it will be replaced by a "None".

    Returns
    -------
    str
        The OBS issues in plain text format
    """

    plain_text = ""
    for issue in obs_issues:
        plain_text += f"{issue.get('key')} - {issue.get('summary')}: "
        plain_text += f"Created by {issue.get('reporter')}\n"

    return plain_text


def parse_obs_issue_systems(issue):
    """Parse the OBS issue systems selection to a list of strings
    containing the selected systems.

    Parameters
    ----------
    issue : `dict`
        The OBS issue got from the Jira API response.

    Returns
    -------
    list
        List of strings with the selected systems.
    """
    systemsPayload = issue["fields"][OBS_SYSTEMS_FIELD]["selection"][0]
    systems = [system["name"] for system in systemsPayload]
    return systems


def get_nightreport_observatory_status_from_efd(efd_instance="summit_efd"):
    """Get the observatory status from the EFD.

    Connect to the EFD LOVE-commander interface by querying
    the top_timeseries endpoint to get the current
    observatory status.

    Returns
    -------
    dict
        Dict with observatory status with the following
        keys:
        - simonyiAzimuth
        - simonyiElevation
        - simonyiDomeAzimuth
        - simonyiRotator
        - simonyiMirrorCoversState
        - simonyiOilSupplySystemState
        - simonyiPowerSupplySystemState
        - simonyiLockingPinsSystemState
        - auxtelAzimuth
        - auxtelElevation
        - auxtelDomeAzimuth
        - auxtelMirrorCoversState
    """
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}"
        "/efd/top_timeseries/"
    )

    cscs = {
        "MTMount": {
            0: {
                "azimuth": ["actualPosition"],
                "elevation": ["actualPosition"],
                "logevent_mirrorCoversMotionState": ["state"],
                "logevent_oilSupplySystemState": ["powerState"],
                "logevent_mainAxesPowerSupplySystemState": ["powerState"],
                "logevent_elevationLockingPinMotionState": ["state"],
            },
        },
        "MTDome": {
            0: {
                "azimuth": ["positionActual"],
            },
        },
        "MTRotator": {
            0: {
                "rotation": ["actualPosition"],
            },
        },
        "ATMCS": {
            0: {
                "mount_AzEl_Encoders": [
                    "azimuthCalculatedAngle0",
                    "elevationCalculatedAngle0",
                ],
            },
        },
        "ATDome": {
            0: {
                "position": ["azimuthPosition"],
            },
        },
        "ATPneumatics": {
            0: {
                "logevent_m1CoverState": ["state"],
            },
        },
    }

    def parse_measurement(measurement, unit=None):
        if measurement is None:
            return "NaN"
        rounded_value = f"{measurement:.2f}"
        return f"{rounded_value}{unit}" if unit else f"{rounded_value}"

    def get_efd_data_measurement(data, topic, field):
        try:
            return data[topic][field][0]["value"]
        except Exception:
            return None

    def get_efd_data_state(data, topic, field, state_map):
        try:
            state = data[topic][field][0]["value"]
        except Exception:
            state = 0
        return state_map.get(state, "UNKNOWN")

    curr_tai = astropy.time.Time.now().tai.datetime
    payload = {
        "cscs": cscs,
        "num": 1,
        "time_cut": curr_tai.isoformat(),
        "efd_instance": efd_instance,
    }
    response = requests.post(url, json=payload)

    if response.ok:
        data = response.json()
        observatory_status = {
            "simonyiAzimuth": parse_measurement(
                get_efd_data_measurement(
                    data,
                    "MTMount-0-azimuth",
                    "actualPosition",
                ),
                "°",
            ),
            "simonyiElevation": parse_measurement(
                get_efd_data_measurement(
                    data,
                    "MTMount-0-elevation",
                    "actualPosition",
                ),
                "°",
            ),
            "simonyiDomeAzimuth": parse_measurement(
                get_efd_data_measurement(
                    data,
                    "MTDome-0-azimuth",
                    "positionActual",
                ),
                "°",
            ),
            "simonyiRotator": parse_measurement(
                get_efd_data_measurement(
                    data,
                    "MTRotator-0-rotation",
                    "actualPosition",
                ),
                "°",
            ),
            "simonyiMirrorCoversState": get_efd_data_state(
                data,
                "MTMount-0-logevent_mirrorCoversMotionState",
                "state",
                MTMOUNT_DEPLOYABLE_MOTION_STATE_MAP,
            ),
            "simonyiOilSupplySystemState": get_efd_data_state(
                data,
                "MTMount-0-logevent_oilSupplySystemState",
                "powerState",
                MTMOUNT_POWER_STATE_MAP,
            ),
            "simonyiPowerSupplySystemState": get_efd_data_state(
                data,
                "MTMount-0-logevent_mainAxesPowerSupplySystemState",
                "powerState",
                MTMOUNT_POWER_STATE_MAP,
            ),
            "simonyiLockingPinsSystemState": get_efd_data_state(
                data,
                "MTMount-0-logevent_elevationLockingPinMotionState",
                "state",
                MTMOUNT_MT_MOUNT_ELEVATION_LOCKING_PIN_MOTION_STATE_MAP,
            ),
            "auxtelAzimuth": parse_measurement(
                get_efd_data_measurement(
                    data,
                    "ATMCS-0-mount_AzEl_Encoders",
                    "azimuthCalculatedAngle0",
                ),
                "°",
            ),
            "auxtelElevation": parse_measurement(
                get_efd_data_measurement(
                    data,
                    "ATMCS-0-mount_AzEl_Encoders",
                    "elevationCalculatedAngle0",
                ),
                "°",
            ),
            "auxtelDomeAzimuth": parse_measurement(
                get_efd_data_measurement(
                    data,
                    "ATDome-0-position",
                    "azimuthPosition",
                ),
                "°",
            ),
            "auxtelMirrorCoversState": get_efd_data_state(
                data,
                "ATPneumatics-0-logevent_m1CoverState",
                "state",
                ATPNEUMATICS_MIRROR_COVER_STATE_MAP,
            ),
        }
        return observatory_status
    raise Exception("Error getting observatory status from EFD.")


def get_nightreport_cscs_status_from_efd(efd_instance="summit_efd"):
    """Get the CSCS status from the EFD.

    Connect to the EFD LOVE-commander interface by querying
    the top_timeseries endpoint to get the current
    CSCs status.

    Returns
    -------
    dict
        Dict with CSCS status with the following keys:
        - MTMount:0
        - MTM1M3:0
        - MTAOS:0
        - MTM2:0
        - MTDome:0
        - MTDomeTrajectory:0
        - MTHexapod:1
        - MTHexapod:2
        - MTRotator:0
        - MTPtg:0
        - MTM1M3TS:0
        - MTCamera:0
        - ATMCS:0
        - ATPtg:0
        - ATDome:0
        - ATDomeTrajectory:0
        - ATAOS:0
        - ATPneumatics:0
        - ATHexapod:0
        - ATCamera:0
        - ATOODS:0
        - ATHeaderService:0
        - ATSpectrograph:0
    """
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}"
        "/efd/top_timeseries/"
    )

    cscs = {}
    for csc in NIGHT_REPORT_CSCS:
        name, index = csc.split(":")
        index = int(index)
        if name not in cscs:
            cscs[name] = {}
        cscs[name][index] = {"logevent_summaryState": ["summaryState"]}

    def parse_cscs_state(state):
        return CSC_SUMMARY_STATE_MAP.get(state, "UNKNOWN")

    def get_efd_data_summary_state(data, topic):
        try:
            return data[topic]["summaryState"][0]["value"]
        except Exception:
            return 0

    curr_tai = astropy.time.Time.now().tai.datetime
    payload = {
        "cscs": cscs,
        "num": 1,
        "time_cut": curr_tai.isoformat(),
        "efd_instance": efd_instance,
    }
    response = requests.post(url, json=payload)
    if response.ok:
        data = response.json()
        cscs_status = {}
        for csc in NIGHT_REPORT_CSCS:
            topic = csc.replace(":", "-") + "-logevent_summaryState"
            cscs_status[csc] = parse_cscs_state(get_efd_data_summary_state(data, topic))

        return cscs_status
    raise Exception("Error getting CSCS status from EFD.")


def parse_observatory_status_to_html_table(observatory_status):
    """Parse the observatory status to an HTML table.

    Parameters
    ----------
    observatory_status : `dict`
        Dict with observatory status with the following keys:
        - simonyiAzimuth
        - simonyiElevation
        - simonyiDomeAzimuth
        - simonyiRotator
        - simonyiMirrorCoversState
        - simonyiOilSupplySystemState
        - simonyiPowerSupplySystemState
        - simonyiLockingPinsSystemState
        - auxtelAzimuth
        - auxtelElevation
        - auxtelDomeAzimuth
        - auxtelMirrorCoversState

    Returns
    -------
    str
        The observatory status in HTML table format
    """
    html_table = f"""
    <table
        style="width:100%;border-collapse: collapse;border:1px solid #e5e7eb;table-layout: auto;"
        cellpadding="0" cellspacing="0">
        <tr style="background-color: #058B8C;color: #F5F5F5;">
            <td colspan="3" style="text-align: center;font-weight:bold;">Observatory Status</td>
        </tr>
        <tr style="background-color:#00BABC; color: #F5F5F5;">
            <td style="white-space:nowrap; width:1%;"></td>
            <td style="text-align: center;font-weight:bold;">Simonyi Telescope</td>
            <td style="text-align: center;font-weight:bold;">Auxiliary Telescope</td>
        </tr>
        <tr style="background-color:#ffffff;">
            <td style="white-space:nowrap;font-weight: bold;">Elevation</td>
            <td>{observatory_status["simonyiElevation"]}</td>
            <td>{observatory_status["auxtelElevation"]}</td>
        </tr>
        <tr style="background-color:#fafafa;">
            <td style="white-space:nowrap;font-weight: bold;">Azimuth</td>
            <td>{observatory_status["simonyiAzimuth"]}</td>
            <td>{observatory_status["auxtelAzimuth"]}</td>
        </tr>
        <tr style="background-color:#ffffff;">
            <td style="white-space:nowrap;font-weight: bold;">Dome Azimuth</td>
            <td>{observatory_status["simonyiDomeAzimuth"]}</td>
            <td>{observatory_status["auxtelDomeAzimuth"]}</td>
        </tr>
        <tr style="background-color:#fafafa;">
            <td style="white-space:nowrap;font-weight: bold;">Rotator</td>
            <td>{observatory_status["simonyiRotator"]}</td>
            <td>N/A</td>
        </tr>
        <tr style="background-color:#ffffff;">
            <td style="white-space:nowrap;font-weight: bold;">Mirror Covers State</td>
            <td>{observatory_status["simonyiMirrorCoversState"]}</td>
            <td>{observatory_status["auxtelMirrorCoversState"]}</td>
        </tr>
        <tr style="background-color:#fafafa;">
            <td style="white-space:nowrap;font-weight: bold;">Oil Supply System State</td>
            <td>{observatory_status["simonyiOilSupplySystemState"]}</td>
            <td>N/A</td>
        </tr>
        <tr style="background-color:#ffffff;">
            <td style="white-space:nowrap;font-weight: bold;">Power Supply System State</td>
            <td>{observatory_status["simonyiPowerSupplySystemState"]}</td>
            <td>N/A</td>
        </tr>
        <tr style="background-color:#fafafa;">
            <td style="white-space:nowrap;font-weight: bold;">Locking Pins System State</td>
            <td>{observatory_status["simonyiLockingPinsSystemState"]}</td
            <td>N/A</td>
        </tr>
    </table>
    """

    return html_table


def parse_observatory_status_to_plain_text(observatory_status):
    """Parse the observatory status to plain text.

    Parameters
    ----------
    observatory_status : `dict`
        Dict with observatory status with the following keys:
        - simonyiAzimuth
        - simonyiElevation
        - simonyiDomeAzimuth
        - simonyiRotator
        - simonyiMirrorCoversState
        - simonyiOilSupplySystemState
        - simonyiPowerSupplySystemState
        - simonyiLockingPinsSystemState
        - auxtelAzimuth
        - auxtelElevation
        - auxtelDomeAzimuth
        - auxtelMirrorCoversState

    Returns
    -------
    str
        The observatory status in plain text format
    """
    maintel_params_units = {
        "simonyiAzimuth": "°",
        "simonyiElevation": "°",
        "simonyiDomeAzimuth": "°",
        "simonyiRotator": "°",
    }
    auxtel_params_units = {
        "auxtelAzimuth": "°",
        "auxtelElevation": "°",
        "auxtelDomeAzimuth": "°",
    }

    plain_text = ""
    plain_text += "Simonyi Telescope: "
    plain_text += f"el = {observatory_status['simonyiElevation']}{maintel_params_units['simonyiElevation']}, "
    plain_text += f"az = {observatory_status['simonyiAzimuth']}{maintel_params_units['simonyiAzimuth']}, "
    plain_text += (
        f"dome az = {observatory_status['simonyiDomeAzimuth']}{maintel_params_units['simonyiDomeAzimuth']}, "
    )
    plain_text += f"rotator = {observatory_status['simonyiRotator']}{maintel_params_units['simonyiRotator']}."
    plain_text += "\n"
    plain_text += f"Mirror covers: {observatory_status['simonyiMirrorCoversState']}, "
    plain_text += f"Oil supply system: {observatory_status['simonyiOilSupplySystemState']}, "
    plain_text += f"Power supply system: {observatory_status['simonyiPowerSupplySystemState']}, "
    plain_text += f"Locking pins system: {observatory_status['simonyiLockingPinsSystemState']}.\n"
    plain_text += "AuxTel Telescope: "
    plain_text += f"el = {observatory_status['auxtelElevation']}{auxtel_params_units['auxtelElevation']}, "
    plain_text += f"az = {observatory_status['auxtelAzimuth']}{auxtel_params_units['auxtelAzimuth']}, "
    plain_text += (
        f"dome az = {observatory_status['auxtelDomeAzimuth']}{auxtel_params_units['auxtelDomeAzimuth']}."
    )
    plain_text += "\n"
    plain_text += f"Mirror covers: {observatory_status['auxtelMirrorCoversState']}.\n"

    return plain_text.strip()


def parse_cscs_status_to_html_table(cscs_status):
    """Parse the CSCS status to an HTML table.

    Parameters
    ----------
    cscs_status : `dict`
        Dict with CSCs status with the following keys:
        - MTMount:0
        - MTM1M3:0
        - MTAOS:0
        - MTM2:0
        - MTDome:0
        - MTDomeTrajectory:0
        - MTHexapod:1
        - MTHexapod:2
        - MTRotator:0
        - MTPtg:0
        - MTM1M3TS:0
        - MTCamera:0
        - ATMCS:0
        - ATPtg:0
        - ATDome:0
        - ATDomeTrajectory:0
        - ATAOS:0
        - ATPneumatics:0
        - ATHexapod:0
        - ATCamera:0
        - ATOODS:0
        - ATHeaderService:0
        - ATSpectrograph:0

    Returns
    -------
    str
        The CSCs status in HTML table format
    """

    def render_status_cell(status):
        color_map = {
            "ENABLED": "#d4edda",  # Green
            "STANDBY": "#fff3cd",  # Yellow
            "FAULT": "#f8d7da",  # Red
            "DISABLED": "#d6d8d9",  # Grey
            "UNKNOWN": "#d6d8d9",  # Grey
        }
        color = color_map.get(status, "#d6d8d9")
        return f"""
        <td style="text-align: center;">
            <div style="background-color: {color};border-radius: 4px;padding: 2px;">{status}</div>
        </td>
        """

    html_table = f"""
    <table
        style="width:100%;border-collapse: collapse;border:1px solid #e5e7eb;table-layout: auto;"
        cellpadding="0" cellspacing="0">
        <tr style="background-color: #058B8C;color: #F5F5F5;">
            <td colspan="8" style="text-align: center;font-weight: bold;">CSCs Summary States</td>
        </tr>
        <tr>
            <td style="font-weight: bold;">MTMount:0</td>
            {render_status_cell(cscs_status["MTMount:0"])}
            <td style="font-weight: bold;">MTM1M3:0</td>
            {render_status_cell(cscs_status["MTM1M3:0"])}
            <td style="font-weight: bold;">MTAOS:0</td>
            {render_status_cell(cscs_status["MTAOS:0"])}
            <td style="font-weight: bold;">MTM2:0</td>
            {render_status_cell(cscs_status["MTM2:0"])}
        </tr>
        <tr>
            <td style="font-weight: bold;">MTDome:0</td>
            {render_status_cell(cscs_status["MTDome:0"])}
            <td style="font-weight: bold;">MTDomeTrajectory:0</td>
            {render_status_cell(cscs_status["MTDomeTrajectory:0"])}
            <td style="font-weight: bold;">MTHexapod:1</td>
            {render_status_cell(cscs_status["MTHexapod:1"])}
            <td style="font-weight: bold;">MTHexapod:2</td>
            {render_status_cell(cscs_status["MTHexapod:2"])}
        </tr>
        <tr>
            <td style="font-weight: bold;">MTRotator:0</td>
            {render_status_cell(cscs_status["MTRotator:0"])}
            <td style="font-weight: bold;">MTPtg:0</td>
            {render_status_cell(cscs_status["MTPtg:0"])}
            <td style="font-weight: bold;">MTM1M3TS:0</td>
            {render_status_cell(cscs_status["MTM1M3TS:0"])}
            <td style="font-weight: bold;">MTCamera:0</td>
            {render_status_cell(cscs_status["MTCamera:0"])}
        </tr>
        <tr>
            <td style="font-weight: bold;">ATMCS:0</td>
            {render_status_cell(cscs_status["ATMCS:0"])}
            <td style="font-weight: bold;">ATPtg:0</td>
            {render_status_cell(cscs_status["ATPtg:0"])}
            <td style="font-weight: bold;">ATDome:0</td>
            {render_status_cell(cscs_status["ATDome:0"])}
            <td style="font-weight: bold;">ATDomeTrajectory:0</td>
            {render_status_cell(cscs_status["ATDomeTrajectory:0"])}
        </tr>
        <tr>
            <td style="font-weight: bold;">ATAOS:0</td>
            {render_status_cell(cscs_status["ATAOS:0"])}
            <td style="font-weight: bold;">ATPneumatics:0</td>
            {render_status_cell(cscs_status["ATPneumatics:0"])}
            <td style="font-weight: bold;">ATHexapod:0</td>
            {render_status_cell(cscs_status["ATHexapod:0"])}
            <td style="font-weight: bold;">ATCamera:0</td>
            {render_status_cell(cscs_status["ATCamera:0"])}
        </tr>
        <tr>
            <td style="font-weight: bold;">ATOODS:0</td>
            {render_status_cell(cscs_status["ATOODS:0"])}
            <td style="font-weight: bold;">ATHeaderService:0</td>
            {render_status_cell(cscs_status["ATHeaderService:0"])}
            <td style="font-weight: bold;">ATSpectrograph:0</td>
            {render_status_cell(cscs_status["ATSpectrograph:0"])}
            <td></td>
            <td></td>
        </tr>

    """

    return html_table


def parse_cscs_status_to_plain_text(cscs_status):
    """Parse the CSCS status to plain text.

    Parameters
    ----------
    cscs_status : `dict`
        Dict with CSCs status with the following keys:
        - MTMount:0
        - MTM1M3:0
        - MTAOS:0
        - MTM2:0
        - MTDome:0
        - MTDomeTrajectory:0
        - MTHexapod:1
        - MTHexapod:2
        - MTRotator:0
        - MTPtg:0
        - MTM1M3TS:0
        - MTCamera:0
        - ATMCS:0
        - ATPtg:0
        - ATDome:0
        - ATDomeTrajectory:0
        - ATAOS:0
        - ATPneumatics:0
        - ATHexapod:0
        - ATCamera:0
        - ATOODS:0
        - ATHeaderService:0
        - ATSpectrograph:0

    Returns
    -------
    str
        The CSCs status in plain text format
    """

    plain_text = ""
    for csc in NIGHT_REPORT_CSCS:
        plain_text += f"{csc}: {cscs_status[csc]}\n"

    return plain_text.strip()


def arrange_nightlydigest_urls_for_obsday(obsday):
    """Arrange the URL for the nightly digest page
    for a given observing day for both telescopes
    Simonyi and AuxTel.

    Parameters
    ----------
    obsday : `int`
        The observing day in the format "YYYYMMDD"

    Returns
    -------
    dict
        Dictionary with the following keys
        - simonyi: URL for the Simonyi telescope nightly digest page
        - auxtel: URL for the AuxTel telescope nightly digest page

    Raises
    ------
    ValueError
        If obsday is not in the format "YYYYMMDD"
    """

    if len(str(obsday)) != 8:
        raise ValueError(f"Invalid obsday format: {obsday}. Expected format is 'YYYYMMDD'.")

    try:
        datetime.strptime(str(obsday), "%Y%m%d")
    except ValueError:
        raise ValueError(f"Invalid obsday format: {obsday}. Expected format is 'YYYYMMDD'.")

    return {
        "simonyi": (
            f"{settings.NIGHTLYDIGEST_BASE_URL}/?startDayobs={obsday}&endDayobs={obsday}&telescope=Simonyi"
        ),
        "auxtel": (
            f"{settings.NIGHTLYDIGEST_BASE_URL}/?startDayobs={obsday}&endDayobs={obsday}&telescope=AuxTel"
        ),
    }


def get_last_valid_night_report(day_obs=None):
    """Get the night report for the current obs day
    from the Nightreport REST API.

    Parameters
    ----------
    day_obs : `int`
        The observing day in the format "YYYYMMDD"
        If None, the current obs day is used.

    Returns
    -------
    dict | None
        The current night report data or None if there is no report
        for the current obs day.

    Raises
    ------
    Exception
        If there is an error getting the current night report
    """
    if day_obs is None:
        day_obs = get_obsday_from_tai(Time.now().tai.datetime)

    day_obs_date = datetime.strptime(str(day_obs), "%Y%m%d")
    next_day = day_obs_date + timedelta(days=1)
    next_day_obs = int(next_day.strftime("%Y%m%d"))

    query_params = f"?min_day_obs={day_obs}&max_day_obs={next_day_obs}&order_by=-date_added"
    url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports{query_params}"
    response = requests.get(url)
    if response.ok:
        reports = response.json()
        if len(reports) == 0:
            return None
        return reports[0]
    raise Exception("Error getting the current night report from the Nightreport API.")


def get_efd_instance_from_request(request):
    """Get the EFD instance in base to the host
    in the request headers.

    Parameters
    ----------
    request : `django.http.HttpRequest`
        The HTTP request object.

    Returns
    -------
    str
        The EFD instance name. Default is "summit_efd".
    """
    host = request.get_host()
    return EFD_INSTACES.get(host, "summit_efd")


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = [".json"]
    if ext.lower() not in valid_extensions:
        raise ValidationError("Unsupported file extension.")


def validate_json_file(value):
    try:
        json.loads(value.read().decode("ascii"))
    except Exception:
        raise ValidationError("Malformatted JSON object.")
