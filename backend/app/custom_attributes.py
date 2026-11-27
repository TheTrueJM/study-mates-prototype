"""
Custom Details (attributes) which Staff create for their Tutorials: a question with Options that
Students choose One of (or Several of). Each can be Display Only, or used for Matching by grouping
Students with Similar answers together, or Mixing Different answers across Groups.
"""
import re, secrets


MAX_CUSTOM_ATTRIBUTES = 5 # Per Tutorial
MAX_LABEL_LENGTH = 40
MAX_HINT_LENGTH = 150
MAX_OPTION_LENGTH = 40
MIN_OPTIONS, MAX_OPTIONS = 2, 12

DISPLAY, SIMILAR, MIXED = "display", "similar", "mixed"
MATCHING_MODES = (DISPLAY, SIMILAR, MIXED)

ID_PREFIX = "custom_"
ID_PATTERN = re.compile(r"^custom_[a-z0-9]{1,24}$")

# Fields of a Definition that Students see
PUBLIC_FIELDS = ("id", "label", "hint", "options", "multiple", "matching")


def generate_custom_id():
    return f"{ID_PREFIX}{secrets.token_hex(4)}"

def is_custom(attribute) -> bool:
    return isinstance(attribute, str) and attribute.startswith(ID_PREFIX)

def is_shareable(definition) -> bool:
    """Matching Details can be hidden from a Student's Group, while Display-Only Details are always visible"""
    return definition["matching"] != DISPLAY

def public_definition(definition) -> dict:
    return {field: definition[field] for field in PUBLIC_FIELDS}


def _clean_text(value, name, max_length, required=True):
    if value is None and not required:
        return "", None
    if not isinstance(value, str):
        return None, f"Invalid {name}."

    value = " ".join(value.split())
    if required and not value:
        return None, f"Enter a {name}."
    if len(value) > max_length:
        return None, f"The {name} can be at most {max_length} characters."
    if not value.isprintable():
        return None, f"The {name} has characters which can't be used."
    return value, None


def parse_custom_attribute(raw, used_ids=()) -> tuple[dict | None, str | None]:
    """Validates a Custom Detail's Definition, returning a tuple of the cleaned Definition and an error message"""
    if not isinstance(raw, dict):
        return None, "Invalid custom detail."

    label, error = _clean_text(raw.get("label"), "name", MAX_LABEL_LENGTH)
    if error:
        return None, error

    hint, error = _clean_text(raw.get("hint"), "question", MAX_HINT_LENGTH, required=False)
    if error:
        return None, f"{label}: {error}"

    options_raw = raw.get("options")
    if not isinstance(options_raw, list):
        return None, f"{label}: Invalid options."

    options = []
    for option in options_raw:
        option, error = _clean_text(option, "option", MAX_OPTION_LENGTH, required=False)
        if error:
            return None, f"{label}: {error}"
        if not option:
            continue
        if option.lower() in (existing.lower() for existing in options):
            return None, f"{label}: Each option must be different."
        options.append(option)

    if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS:
        return None, f"{label}: Add between {MIN_OPTIONS} and {MAX_OPTIONS} options."

    multiple = raw.get("multiple", False)
    if not isinstance(multiple, bool):
        return None, f"{label}: Invalid choice type."

    matching = raw.get("matching", DISPLAY)
    if matching not in MATCHING_MODES:
        return None, f"{label}: Invalid matching type."

    # Keep the Detail's ID (so Students' Answers are kept when it is edited) unless it is invalid or repeated
    attribute_id = raw.get("id")
    if not isinstance(attribute_id, str) or not ID_PATTERN.match(attribute_id) or attribute_id in used_ids:
        attribute_id = generate_custom_id()
        while attribute_id in used_ids:
            attribute_id = generate_custom_id()

    # Which of the Staff Member's Saved Details it came from (if any)
    saved_id = raw.get("saved_id")
    if not isinstance(saved_id, int) or isinstance(saved_id, bool) or saved_id < 1:
        saved_id = None

    return {
        "id": attribute_id,
        "label": label,
        "hint": hint,
        "options": options,
        "multiple": multiple,
        "matching": matching,
        "saved_id": saved_id,
    }, None


def parse_custom_attributes(raw) -> tuple[list | None, str | None]:
    """Validates a Tutorial's Custom Details, returning a tuple of the cleaned Definitions and an error message"""
    if not isinstance(raw, list):
        return None, "Invalid custom details."
    if len(raw) > MAX_CUSTOM_ATTRIBUTES:
        return None, f"A Session can have at most {MAX_CUSTOM_ATTRIBUTES} custom details."

    definitions, used_ids, labels = [], set(), set()
    for item in raw:
        definition, error = parse_custom_attribute(item, used_ids)
        if error:
            return None, error
        if definition["label"].lower() in labels:
            return None, f"There is already a custom detail named {definition['label']}."

        used_ids.add(definition["id"])
        labels.add(definition["label"].lower())
        definitions.append(definition)

    return definitions, None


def validate_custom_value(definition, value) -> tuple:
    """Returns a tuple of a Student's cleaned answer (None or [] if cleared) and an error message"""
    options = definition["options"]
    invalid = f"Invalid choice for {definition['label']}."

    if definition["multiple"]:
        if value in (None, "", []):
            return [], None
        if not isinstance(value, list) or not all(isinstance(choice, str) for choice in value):
            return None, invalid
        if any(choice not in options for choice in value):
            return None, invalid
        return [option for option in options if option in value], None

    if value in (None, ""):
        return None, None
    if not isinstance(value, str) or value not in options:
        return None, invalid
    return value, None


def coerce_custom_value(definition, value):
    """Keeps as much of an existing answer as is still valid after its Detail was edited"""
    options = definition["options"]
    choices = value if isinstance(value, list) else [value] if isinstance(value, str) else []
    choices = [option for option in options if option in choices]

    if definition["multiple"]:
        return choices
    return choices[0] if choices else None


def custom_similarity(definition, a, b) -> float | None:
    """How similar two Students' answers are (0 to 1), or None if either hasn't answered"""
    if definition["multiple"]:
        a, b = set(a or []), set(b or [])
        if not a or not b:
            return None
        return len(a & b) / len(a | b)

    if a is None or b is None:
        return None
    return float(a == b)
