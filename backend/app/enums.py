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


def get_availability_code(day: Day, period: TimePeriod) -> str:
    return f"{day.value}{period.value}"