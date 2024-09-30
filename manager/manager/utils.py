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
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tempfile import TemporaryFile
from urllib.parse import quote

import requests
from api.models import ControlLocation
from astropy.time import Time
from astropy.units import hour
from django.conf import settings
from django.core.files.storage import Storage
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

# Constants
JSON_RESPONSE_LOCAL_STORAGE_NOT_ALLOWED = {"error": "Local storage not allowed."}
JSON_RESPONSE_ERROR_NOT_VALID_JSON = {"error": "Not a valid JSON response."}
TIME_LOST_FIELD = "customfield_10106"
PRIMARY_SOFTWARE_COMPONENTS_IDS = "customfield_10107"
PRIMARY_HARDWARE_COMPONENTS_IDS = "customfield_10196"


class LocationPermission(BasePermission):
    """Permission class to check if the user is in the location whitelist."""

    message = {"ack": "Your location is not allowed to command the observatory."}

    def has_permission(self, request, view):
        """Return True if the request comes from a location
        configured as command location."""
        selected_location = ControlLocation.objects.filter(selected=True).first()
        location = (
            selected_location if selected_location else ControlLocation.objects.first()
        )
        client_ip = get_client_ip(request)
        return client_ip in location.ip_whitelist


class UserBasedPermission(BasePermission):
    """Permission class to check if the user has commanding permissions."""

    message = {"ack": "Your user is not allowed to command the observatory."}

    def has_permission(self, request, view):
        """Return True if the user has command permissions."""
        return request.user.has_perm("api.command.execute_command")


class CommandPermission(BasePermission):
    """Permission class to check if the user has commanding permissions."""

    def __new__(cls) -> BasePermission:
        """Return the correct permission class based on
        the configured permission type."""
        configured_command_permission = settings.COMMANDING_PERMISSION_TYPE
        if configured_command_permission == "user":
            return UserBasedPermission()
        elif configured_command_permission == "location":
            return LocationPermission()
        else:
            raise ValueError(
                f"Invalid permission type: {configured_command_permission}"
            )


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
            f"http://{os.environ.get('COMMANDER_HOSTNAME')}"
            f":{os.environ.get('COMMANDER_PORT')}/lfa"
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
        ) or response.headers.get("content-type") == RemoteStorage.ALLOWED_FILE_TYPES[
            4
        ]:
            byte_encoded_response = response.content
            tf.write(byte_encoded_response)
            # Before sending the file,
            # we need to reset the file pointer to the beginning
            tf.seek(0)
            return tf

        # If request is for config files (json file)
        if (
            response.headers.get("content-type") == RemoteStorage.ALLOWED_FILE_TYPES[3]
            or response.headers.get("content-type")
            == RemoteStorage.ALLOWED_FILE_TYPES[4]
        ):
            json_response = response.json()
            byte_encoded_response = json.dumps(json_response).encode("ascii")
            tf.write(byte_encoded_response)
            # Before sending the file,
            # we need to reset the file pointer to the beginning
            tf.seek(0)
            return tf

        # Raise error if file type is not supported
        raise ValueError(
            f"File type not supported: {response.headers.get('content-type')}"
        )

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
        List of addittional arguments. Currently unused
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

    tags_data = request_data.get("tags").split(",") if request_data.get("tags") else []

    components_ids = (
        request_data.get("components_ids").split(",")
        if request_data.get("components_ids")
        else []
    )
    primary_software_components_ids = (
        request_data.get("primary_software_components_ids").split(",")
        if request_data.get("primary_software_components_ids")
        else None
    )
    primary_hardware_components_ids = (
        request_data.get("primary_hardware_components_ids").split(",")
        if request_data.get("primary_hardware_components_ids")
        else None
    )

    try:
        jira_payload = {
            "fields": {
                "issuetype": {"id": "10065"},
                # If the JIRA_PROJECT_ID environment variable is not set,
                # the project id is set to the OBS project by default: 10063.
                # Set it in case the OBS project id has changed for any reason
                # and update the default value above and in the following line.
                "project": {"id": os.environ.get("JIRA_PROJECT_ID", "10063")},
                "labels": [
                    "LOVE",
                    *tags_data,
                ],
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
                TIME_LOST_FIELD: float(request_data.get("time_lost", 0)),
                # Default values of the following fields are set to -1
                PRIMARY_SOFTWARE_COMPONENTS_IDS: {
                    "id": (
                        str(primary_software_components_ids[0])
                        if primary_software_components_ids
                        else "-1"
                    )
                },
                PRIMARY_HARDWARE_COMPONENTS_IDS: {
                    "id": (
                        str(primary_hardware_components_ids[0])
                        if primary_hardware_components_ids
                        else "-1"
                    )
                },
            },
            "update": {
                "components": [{"set": [{"id": str(id)} for id in components_ids]}]
            },
        }
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
            "error": response_data,
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
        time_lost_value = jira_ticket_fields.get(TIME_LOST_FIELD, 0.0)
        existent_time_lost = float(time_lost_value) if time_lost_value else 0.0
        jira_payload = {
            "fields": {
                TIME_LOST_FIELD: existent_time_lost + add_time_lost,
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

    try:
        jira_payload = {
            "body": get_jira_description(request_data),
        }
    except Exception as e:
        return Response({"ack": f"Error creating jira payload: {e}"}, status=400)

    if "time_lost" in request_data:
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
    """Query all issues of the OBS project for a certain day.
    Then get the total observation time loss from the time_lost param
    """

    initial_day_obs_string = get_obsday_iso(request_data.get("day_obs"))
    final_day_obs_string = get_obsday_iso(request_data.get("day_obs") + 1)

    # JQL query to find issues created on a specific date
    jql_query = (
        f"project = 'OBS' "
        f"AND created >= '{initial_day_obs_string} 12:00' "
        f"AND created <= '{final_day_obs_string} 12:00'"
    )

    headers = {
        "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
        "content-type": "application/json",
    }

    url = f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/search?jql={quote(jql_query)}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        issues = response.json()["issues"]
        return [
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "time_lost": (
                    issue["fields"][TIME_LOST_FIELD]
                    if issue["fields"][TIME_LOST_FIELD] is not None
                    else 0.0
                ),
                "reporter": issue["fields"]["creator"]["displayName"],
                "created": issue["fields"]["created"].split(".")[0],
            }
            for issue in issues
        ]
    raise Exception(f"Error getting issues from {os.environ.get('JIRA_API_HOSTNAME')}")


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
    - telescope: The telescope used during the observing night.
    Either "AuxTel" or "Simonyi"
    - day_obs: The observing day in the format "YYYYMMDD"
    - telescope: The telescope used during the observing night.
    Either "AuxTel" or "Simonyi"
    - summary: The summary of the observing night
    - telescope_status: The final telescope status at the end of the night
    - confluence_url: The URL of the confluence page with the full report
    - obs_issues: The list of OBS issues during the night
    - observers_crew: The list of observers that participated during the night

    Returns
    -------
    str
        The night report email in HTML format or plain text format
    """

    expected_keys = [
        "telescope",
        "day_obs",
        "summary",
        "telescope_status",
        "confluence_url",
        "obs_issues",
        "observers_crew",
    ]
    missing_keys = [key for key in expected_keys if key not in report]
    if missing_keys:
        raise ValueError(f"Missing keys in report: {', '.join(missing_keys)}")

    url_jira_obs_tickets = (
        "https://rubinobs.atlassian.net/jira/software/c/projects/OBS/boards/232"
    )
    day_added = get_obsday_iso(report["day_obs"])

    # TODO: Swap this hardcoded url by a dynamic one.
    # The service is meant to be run in the summit,
    # so this will work for the moment.
    # See: DM-43637
    url_rolex = f"https://summit-lsp.lsst.codes/rolex?log_date={day_added}"

    SUMMARY_TITLE = "Summary:"
    FINAL_TELESCOPE_STATUS_TITLE = "Final telescope status:"
    ADDITIONAL_RESOURCES_TITLE = "Additional resources:"
    SIGNED_MSG = "Submitted by:"
    LINK_MSG_OBS = "OBS fault reports from last 24 hours:"
    LINK_MSG_CONFLUENCE = f"Link to {report['telescope']} Log Confluence Page:"
    LINK_MSG_ROLEX = "Link to detailed night log entries (requires Summit VPN):"
    DETAILED_ISSUE_REPORT_TITLE = "Detailed issue report:"

    if plain:
        plain_content = f"""{SUMMARY_TITLE}
{report["summary"]}

{FINAL_TELESCOPE_STATUS_TITLE}
{report["telescope_status"]}

{ADDITIONAL_RESOURCES_TITLE}
- {LINK_MSG_OBS} {url_jira_obs_tickets}
- {LINK_MSG_CONFLUENCE} {report["confluence_url"]}
- {LINK_MSG_ROLEX} {url_rolex}
{f'''
{DETAILED_ISSUE_REPORT_TITLE}
{parse_obs_issues_array_to_plain_text(report["obs_issues"])}
''' if len(report["obs_issues"]) > 0 else ""}

{SIGNED_MSG}
{", ".join(report["observers_crew"])}"""
        return plain_content

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
            {SUMMARY_TITLE}
            <br>
            {report["summary"].replace(new_line_character, '<br>')}
        </p>
        <p>
            {FINAL_TELESCOPE_STATUS_TITLE}
            <br>
            {report["telescope_status"].replace(new_line_character, '<br>')}
        </p>
        <p>
            {ADDITIONAL_RESOURCES_TITLE}
            <br>
            <ul>
                <li>
                    {LINK_MSG_OBS}
                    <a href="{url_jira_obs_tickets}">{url_jira_obs_tickets}</a>
                </li>
                <li>
                    {LINK_MSG_CONFLUENCE}
                    <a href="{report["confluence_url"]}">{report["confluence_url"]}</a>
                </li>
                <li>
                    {LINK_MSG_ROLEX}
                    <a href="{url_rolex}">{url_rolex}</a>
                </li>
            </ul>
        </p>
        {f'''<p>
            {DETAILED_ISSUE_REPORT_TITLE}
            <br>
            {parse_obs_issues_array_to_html_table(report["obs_issues"])}
        </p>''' if len(report["obs_issues"]) > 0 else ""}
        <p>
            {SIGNED_MSG}
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
            <td>{issue.get('key', '-')}</td>
            <td>{issue.get('summary', '-')}</td>
            <td>{issue.get('reporter', '-')}</td>
            <td>{issue.get('created', '-')}</td>
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
