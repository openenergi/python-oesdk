import datetime
import math
import logging

import pandas as pd


def to_pd_timestamp_utc(in_datetime):
    # pandas timestamp
    is_pd_ts = isinstance(in_datetime, pd._libs.tslibs.timestamps.Timestamp)
    has_pd_ts_tz = is_pd_ts and in_datetime.tz is not None
    if is_pd_ts and has_pd_ts_tz:
        return in_datetime.tz_convert('UTC')
    if is_pd_ts and not has_pd_ts_tz:
        return in_datetime.tz_localize('UTC')
    # string type
    if isinstance(in_datetime, str):
        return pd.Timestamp(in_datetime, tz='UTC')
    # datetime type
    is_datetime = isinstance(in_datetime, datetime.datetime)
    has_datetime_tz = in_datetime.tzname() is not None
    if is_datetime and has_datetime_tz:
        return pd.Timestamp(in_datetime).tz_convert('UTC')
    if is_datetime and not has_datetime_tz:
        return pd.Timestamp(in_datetime, tz='UTC')


def to_iso_ts_zulu(in_datetime):
    '''
    Check Go (Golang) argument on
    ISO 8601 being more relaxed than RFC 3339
    https://github.com/golang/go/issues/31113

    Open Energi backend API is implemented in Go (Golang)
    '''
    return to_pd_timestamp_utc(in_datetime).isoformat().replace("+00:00", "Z")


def get_datetime_slices(start, end):
    '''
    Returns 1-hour *STRING* (ISO 8601) pairs between start_utc and end_utc.
    Each date has the Zulu format (last letter being "Z"):
    yyyy-MM-ddTHH:mm:ssZ

    The input could be of any kind, e.g.:
    - day string '2019-11-15'
    - datetime (partial) string '2019-11-15 23:37'
    - datetime object
    - pandas timestamp
    '''
    start = to_pd_timestamp_utc(start)
    end = to_pd_timestamp_utc(end)
    # 1-hour slices between start and end
    date_range = list(pd.date_range(
        start=start,
        end=end,
        freq='H',
        tz='UTC'
    ).map(lambda ts: to_iso_ts_zulu(ts)))
    end_zulu = to_iso_ts_zulu(end)
    if date_range[-1] != end_zulu:
        logging.info("The last element is {}, so appending to the list of timestamps the end {}".format(
            date_range[-1], end_zulu))
        date_range.append(end_zulu)
    # chop ranges in start/end for each 1-hour interval
    chops = [[date_range[idx], date_range[idx + 1]]
             for idx, elem in enumerate(date_range[:-1])]
    return chops


def utc_to_settlement_period(timestamp):
    """
    Converts UTC datetime to NG settlement window

    Args:
        timestamp (optional datetime, str): timestamp in UTC, defaults to utcnow

    Returns:
        Tuple of (settle,date)
    """
    if timestamp is None:
        timestamp = datetime.datetime.utcnow()
    # Get timestamp in correct format
    tUtc = pd.Timestamp(timestamp, tz='UTC')
    # Convert timezone to BST
    tLocal = tUtc.tz_convert('Europe/London')
    # Work out when last midnight local time was
    tLocalMidnight = pd.Timestamp(tLocal.date(), tz='Europe/London')
    # Calculate difference in half-hours
    settle = math.floor((tLocal - tLocalMidnight).total_seconds() / 1800) + 1

    return (settle, tLocal.date())
