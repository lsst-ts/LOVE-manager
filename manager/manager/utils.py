import json
import os
import requests
import urllib
from astropy.time import Time
from astropy.units import hour
from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from tempfile import TemporaryFile
from api.models import ConfigFile 


class RemoteStorage(Storage):
    PREFIX_THUMBNAIL = "thumbnails/"
    PREFIX_CONFIG = "configs/"

    def __init__(self, location=None):
        self.location = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/lfa"

    def _open(self, name, mode="rb"):
        """Return the remote file object."""
        response = requests.get(name)
        try:
            json_response = response.json()
        except Exception:
            json_response = {"error": "File is not a valid json format"}

        byte_encoded_response = json.dumps(json_response).encode('utf-8')
        tf = TemporaryFile()
        tf.write(byte_encoded_response)
        tf.seek(0)
        return File(tf)

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

        upload_file_response = requests.post(url, files={"uploaded_file": content})
        stored_url = None
        if upload_file_response.status_code == 200:
            stored_url = upload_file_response.json()["url"]
        return stored_url

    def delete(self, name):
        pass

    def exists(self, name):
        return False

    def url(self, name):
        """Return the URL of the remote file."""
        return name


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
