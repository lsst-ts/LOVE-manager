import json
import os
import re
import requests
from api.models import ControlLocation
from astropy.time import Time
from astropy.units import hour
from django.conf import settings
from django.core.files.storage import Storage
from rest_framework.permissions import BasePermission
from tempfile import TemporaryFile


# Constants
JSON_RESPONSE_LOCAL_STORAGE_NOT_ALLOWED = {"error": "Local storage not allowed."}
JSON_RESPONSE_ERROR_NOT_VALID_JSON = {"error": "Not a valid JSON response."}


class LocationPermission(BasePermission):
    """Permission class to check if the user is in the location whitelist."""

    message = {"ack": "Your location is not allowed to command the observatory."}

    def has_permission(self, request, view):
        """Return True if the request comes from a location configured as command location."""
        selected_location = ControlLocation.objects.filter(selected=True).first()
        location = (
            selected_location if selected_location else ControlLocation.objects.first()
        )
        client_ip = get_client_ip(request)
        return client_ip in location.ip_whitelist


class UserBasedPermission(BasePermission):
    """Permission class to check if the user has commanding permissions."""

    message = {"ack": "Your don't have commanding permissions."}

    def has_permission(self, request, view):
        """Return True if the user has command permissions."""
        return request.user.has_perm("api.command.execute_command")


class CommandPermission(BasePermission):
    """Permission class to check if the user has commanding permissions."""

    def __new__(cls) -> BasePermission:
        """Return the correct permission class based on the configured permission type."""
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

    ALLOWED_FILE_TYPES = ["image/png", "image/jpeg", "image/jpg", "application/json"]

    def __init__(self, location=None):
        self.location = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/lfa"

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
        response = requests.get(name)
        if response.status_code != 200:
            raise FileNotFoundError(f"Error requesting file at: {name}.")

        tf = TemporaryFile()
        # If request is for thumbnail (image file)
        if response.headers.get("content-type") in RemoteStorage.ALLOWED_FILE_TYPES[:3]:
            byte_encoded_response = response.content
            tf.write(byte_encoded_response)
            # Before sending the file, we need to reset the file pointer to the beginning
            tf.seek(0)
            return tf

        # If request is for config files (json file)
        if response.headers.get("content-type") == RemoteStorage.ALLOWED_FILE_TYPES[3]:
            json_response = response.json()
            byte_encoded_response = json.dumps(json_response).encode("ascii")
            tf.write(byte_encoded_response)
            # Before sending the file, we need to reset the file pointer to the beginning
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
        This methods connects to the LOVE-commander lfa endpoint to upload the file.
        """
        if name.startswith(RemoteStorage.PREFIX_THUMBNAIL):
            url = f"{self.location}/upload-love-thumbnail"
        elif name.startswith(RemoteStorage.PREFIX_CONFIG):
            url = f"{self.location}/upload-love-config-file"

        # Before sending the file, we need to reset the file pointer to the beginning
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
        - sidereal_summit: current time as a sidereal_time w/respect to the summit location (hourangles)
        - sidereal_greenwich: current time as a sidereal_time w/respect to Greenwich location (hourangles)
        - tai_to_utc: The number of seconds of difference between TAI and UTC times (seconds)
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
            "utc": "<current time in UTC scale as a unix timestamp (seconds), in float format>",
            "tai": "<current time in UTC scale as a unix timestamp (seconds), in float format>",
            "mjd": "<current time as a modified julian date, in float format>",
            "sidereal_summit": "<current time as a sidereal_time w/respect
                to the summit location (hourangles), in float format>",
            "sidereal_greenwich": "<current time as a sidereal_time w/respect
                to Greenwich location (hourangles), in float format>",
            "tai_to_utc": "<The number of seconds of difference between TAI and UTC times (seconds), in float format>",
        }

    Parameters
    ----------
    time_data : dict
        dictionary containing the time data in different formats, indexed by format

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
