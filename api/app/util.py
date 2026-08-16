from datetime import datetime, timezone


def utc_now_str():
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")


def date_from_timestamp(value):
    return value[:10]
