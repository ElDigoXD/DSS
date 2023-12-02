from datetime import datetime


def try_strptime(date_string: str, format: str) -> datetime | None:
    try:
        return datetime.strptime(date_string, format)
    except:
        return None


def try_int(x: str) -> int | None:
    try:
        return int(x)
    except:
        return None


def float_round(num: float) -> float:
    return float("{:.2f}".format(num))
