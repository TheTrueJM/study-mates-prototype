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
    N = "N"


VALID_CODES = [
    "MONM", "MONA", "MONN",
    "TUEM", "TUEA", "TUEN",
    "WEDM", "WEDA", "WEDN",
    "THUM", "THUA", "THUN",
    "FRIM", "FRIA", "FRIN",
    "SATM", "SATA", "SATN",
    "SUNM", "SUNA", "SUNN"
]

MAX_AVAILABILITY = 21


def get_availability_code(day: Day, period: TimePeriod) -> str:
    return f"{day.value}{period.value}"


def parse_availability(availability_raw) -> list[str]:
    if isinstance(availability_raw, list):
        codes = [code.strip().upper() for code in availability_raw if code and code.strip()]
    elif availability_raw and isinstance(availability_raw, str):
        normalized = availability_raw.replace(",", " ")
        codes = [code.strip().upper() for code in normalized.split() if code.strip()]
    else:
        return []

    valid_codes = [code for code in codes if code in VALID_CODES]
    unique_codes = list(dict.fromkeys(valid_codes))

    return unique_codes[:MAX_AVAILABILITY]
