import os
import requests
from astropy.time import Time
from astropy.units import hour
from django.conf import settings
from django.core.files.storage import Storage


class RemoteStorage(Storage):
    def __init__(self, location=None):
        if location is None:
            location = settings.MEDIA_ROOT
        self.location = location

    def _open(self, name, mode="rb"):
        return open(os.path.join(self.location, name), mode)

    def _save(self, name, content):
        # url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:
        # {os.environ.get('COMMANDER_PORT')}/lfa/upload-love-config-file"
        url = "http://google"
        upload_file_response = requests.post(url, files={"uploaded_file": content})
        if upload_file_response.status_code == 200:
            print("#####", flush=True)
            print(upload_file_response.json())
            print("#####", flush=True)
        else:
            print("#####", flush=True)
            print(upload_file_response.json())
            print("#####", flush=True)

        # path = os.path.join(self.location, name)
        # with open(path, 'wb') as f:
        #     content.seek(0)
        #     f.write(content.read())
        return name

    def delete(self, name):
        os.remove(os.path.join(self.location, name))

    def exists(self, name):
        return os.path.exists(os.path.join(self.location, name))

    def url(self, name):
        return settings.MEDIA_URL + name


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
