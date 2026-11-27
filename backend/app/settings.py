"""Validation of Tutorial Settings (shared by Tutorials and the Presets saved to Staff Accounts)"""
import math

from .enums import DEFAULT_AVAILABLE_ATTRIBUTES, SELECTABLE_ATTRIBUTES, parse_available_attributes
from .custom_attributes import parse_custom_attributes


MIN_GROUP_SIZE, MAX_GROUP_SIZE = 2, 10
MIN_DISCUSSION_MINUTES, MAX_DISCUSSION_MINUTES = 1, 60
DEFAULT_DISCUSSION_MINUTES = 5


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_discussion_time(minutes):
    """Returns a tuple of the discussion time in seconds and an error message"""
    try:
        minutes = float(minutes)
    except (TypeError, ValueError):
        return None, "Invalid discussion time."

    if math.isnan(minutes) or not MIN_DISCUSSION_MINUTES <= minutes <= MAX_DISCUSSION_MINUTES:
        return None, f"Discussion time must be between {MIN_DISCUSSION_MINUTES} and {MAX_DISCUSSION_MINUTES} minutes."
    return math.ceil(minutes * 60), None


def validate_settings(data, current=None):
    """
    Validates tutorial settings, returning a tuple of the cleaned settings and an error message.
    Settings omitted from an update keep their current value; on creation they use their defaults.
    """
    group_size = data.get("group_size", current["group_size"] if current else None)
    if not is_int(group_size) or not MIN_GROUP_SIZE <= group_size <= MAX_GROUP_SIZE:
        return None, f"Group size must be between {MIN_GROUP_SIZE} and {MAX_GROUP_SIZE} students."

    max_groups = data.get("max_groups", current["max_groups"] if current else None)
    if max_groups is not None and (not is_int(max_groups) or max_groups < 2):
        return None, "Maximum groups must be at least 2."

    if "discussion_time" in data or "time" in data:
        discussion_time, error = validate_discussion_time(data.get("discussion_time", data.get("time")))
        if error:
            return None, error
    elif current:
        discussion_time = current["discussion_time"]
    else:
        discussion_time = DEFAULT_DISCUSSION_MINUTES * 60

    if "available_attributes" in data and data["available_attributes"] is not None:
        available_attributes = parse_available_attributes(data["available_attributes"])
        if available_attributes is None:
            return None, "Invalid student details selection."
    elif current:
        available_attributes = [a for a in current["available_attributes"] if a in SELECTABLE_ATTRIBUTES]
    else:
        available_attributes = list(DEFAULT_AVAILABLE_ATTRIBUTES)

    if "custom_attributes" in data and data["custom_attributes"] is not None:
        custom_attributes, error = parse_custom_attributes(data["custom_attributes"])
        if error:
            return None, error
    elif current:
        custom_attributes = current["custom_attributes"]
    else:
        custom_attributes = list()

    shortlisting = data.get("shortlisting", current["shortlisting"] if current else False)
    if not isinstance(shortlisting, bool):
        return None, "Invalid shortlist setting."

    # Custom Details are always enabled, after the Selected Built-In Details
    available_attributes += [definition["id"] for definition in custom_attributes]

    return {
        "group_size": group_size,
        "max_groups": max_groups,
        "discussion_time": discussion_time,
        "available_attributes": available_attributes,
        "custom_attributes": custom_attributes,
        "shortlisting": shortlisting,
    }, None
