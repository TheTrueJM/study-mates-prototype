from enum import Enum


class Day(Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class TimePeriod(Enum):
    M = "M"
    A = "A"
    E = "E"


VALID_CODES = {day.value + time.value for day in Day for time in TimePeriod}


def get_availability_code(day: Day, period: TimePeriod) -> str:
    return f"{day.value}{period.value}"


def parse_availability(availability_raw) -> list[str]:
    if isinstance(availability_raw, list):
        codes = {code.strip().upper() for code in availability_raw if isinstance(code, str) and code.strip()}
    elif isinstance(availability_raw, str) and availability_raw.strip():
        codes = {code.strip().upper() for code in availability_raw.split(",") if code.strip()}
    else:
        return list()

    return list(codes & VALID_CODES)
