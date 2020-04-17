from astropy.time import Time


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
            - sidereal_summit: current time as a sidereal_time w/respect to Greenwich location (hourangles)
            - tai_to_utc: The number of seconds of difference between TAI and UTC times (seconds)
    """
    t = Time.now()
    t_utc = t.datetime.timestamp()
    t_tai = t.tai.datetime.timestamp()
    sidereal_summit = t.sidereal_time("apparent", longitude=-70.749417, model=None)
    sidereal_greenwich = t.sidereal_time("apparent", longitude="greenwich", model=None)
    return {
        "utc": t_utc,
        "tai": t_tai,
        "mjd": t.mjd,
        "sidereal_summit": sidereal_summit.value,
        "sidereal_greenwich": sidereal_greenwich.value,
        "tai_to_utc": t_utc - t_tai,
    }
