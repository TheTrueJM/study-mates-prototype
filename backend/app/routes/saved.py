from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required

from ..auth import ACCOUNT, get_staff_identity
from ..custom_attributes import parse_custom_attribute
from ..database import db, SavedAttribute, TutorialPreset
from ..enums import SELECTABLE_ATTRIBUTES
from ..settings import validate_settings


# Custom Details (and other settings) saved to a Staff Account
saved_bp = Blueprint("saved", __name__, url_prefix="/staff")

MAX_SAVED_ATTRIBUTES = 50
MAX_PRESETS = 30
MAX_PRESET_NAME_LENGTH = 50


def account_required(f):
    """Requires a signed in Staff Account (not a Guest), passing the account's ID"""
    @wraps(f)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_staff_identity(get_jwt())
        if not identity:
            return jsonify({"message": "Your sign in is no longer valid"}), 401
        if identity["type"] != ACCOUNT:
            return jsonify({"message": "Sign in with a Staff Account to save to your Account"}), 403

        return f(int(identity["id"].split(":", 1)[1]), *args, **kwargs)
    return wrapper


def _saved_definition(data):
    """Returns a tuple of a Custom Detail's definition to save and an error response"""
    definition, error = parse_custom_attribute(data)
    if error:
        return None, (jsonify({"message": error}), 400)

    return {field: definition[field] for field in ("label", "hint", "options", "multiple", "matching")}, None


@saved_bp.route("/attributes", methods=["GET"])
@account_required
def list_attributes(staff_id):
    attributes = SavedAttribute.query.filter_by(staff_id=staff_id).all()
    attributes.sort(key=lambda attribute: attribute.definition["label"].lower())
    return jsonify({"attributes": [attribute.to_dict() for attribute in attributes]}), 200


@saved_bp.route("/attributes", methods=["POST"])
@account_required
def create_attribute(staff_id):
    definition, error = _saved_definition(request.get_json(silent=True))
    if error:
        return error

    if SavedAttribute.query.filter_by(staff_id=staff_id).count() >= MAX_SAVED_ATTRIBUTES:
        return jsonify({"message": f"You can save at most {MAX_SAVED_ATTRIBUTES} custom details"}), 400

    attribute = SavedAttribute(staff_id=staff_id, definition=definition)
    db.session.add(attribute)
    db.session.commit()
    return jsonify({"attribute": attribute.to_dict(), "message": "Custom detail saved"}), 201


@saved_bp.route("/attributes/<int:attribute_id>", methods=["PUT"])
@account_required
def update_attribute(staff_id, attribute_id):
    attribute = SavedAttribute.query.filter_by(id=attribute_id, staff_id=staff_id).first()
    if not attribute:
        return jsonify({"message": "This custom detail no longer exists"}), 404

    definition, error = _saved_definition(request.get_json(silent=True))
    if error:
        return error

    attribute.definition = definition
    db.session.commit()
    return jsonify({"attribute": attribute.to_dict(), "message": "Custom detail updated"}), 200


@saved_bp.route("/attributes/<int:attribute_id>", methods=["DELETE"])
@account_required
def delete_attribute(staff_id, attribute_id):
    attribute = SavedAttribute.query.filter_by(id=attribute_id, staff_id=staff_id).first()
    if not attribute:
        return jsonify({"message": "This custom detail no longer exists"}), 404

    db.session.delete(attribute)
    db.session.commit()
    return jsonify({"message": "Custom detail deleted"}), 200


# ===== Tutorial Setting Presets ===== #

def _preset_settings(data):
    """Returns a tuple of a Preset's Settings to save (in the form a Tutorial is created with) and an error response"""
    if not isinstance(data, dict):
        return None, (jsonify({"message": "Invalid settings"}), 400)

    settings, error = validate_settings(data)
    if error:
        return None, (jsonify({"message": error}), 400)

    return {
        "group_size": settings["group_size"],
        "max_groups": settings["max_groups"],
        "discussion_time": settings["discussion_time"] / 60, # Minutes
        "available_attributes": [a for a in settings["available_attributes"] if a in SELECTABLE_ATTRIBUTES],
        "custom_attributes": settings["custom_attributes"],
    }, None


def _preset_name(data, staff_id, preset_id=None):
    """Returns a tuple of a Preset's cleaned Name and an error response (names are unique per Account)"""
    name = data.get("name") if isinstance(data, dict) else None
    name = " ".join(name.split()) if isinstance(name, str) else ""

    if not name:
        return None, (jsonify({"message": "Enter a name for the preset"}), 400)
    if len(name) > MAX_PRESET_NAME_LENGTH or not name.isprintable():
        return None, (jsonify({"message": f"The name can be at most {MAX_PRESET_NAME_LENGTH} characters"}), 400)

    for preset in TutorialPreset.query.filter_by(staff_id=staff_id):
        if preset.id != preset_id and preset.name.lower() == name.lower():
            return None, (jsonify({"message": "You already have a preset with this name", "preset_id": preset.id}), 409)
    return name, None


@saved_bp.route("/presets", methods=["GET"])
@account_required
def list_presets(staff_id):
    presets = TutorialPreset.query.filter_by(staff_id=staff_id).all()
    presets.sort(key=lambda preset: preset.name.lower())
    return jsonify({"presets": [preset.to_dict() for preset in presets]}), 200


@saved_bp.route("/presets", methods=["POST"])
@account_required
def create_preset(staff_id):
    data = request.get_json(silent=True)
    name, error = _preset_name(data, staff_id)
    if error:
        return error

    settings, error = _preset_settings(data.get("settings"))
    if error:
        return error

    if TutorialPreset.query.filter_by(staff_id=staff_id).count() >= MAX_PRESETS:
        return jsonify({"message": f"You can save at most {MAX_PRESETS} presets"}), 400

    preset = TutorialPreset(staff_id=staff_id, name=name, settings=settings)
    db.session.add(preset)
    db.session.commit()
    return jsonify({"preset": preset.to_dict(), "message": "Preset saved"}), 201


@saved_bp.route("/presets/<int:preset_id>", methods=["PUT"])
@account_required
def update_preset(staff_id, preset_id):
    """Overrides a Preset's Settings (and Name, if given)"""
    preset = TutorialPreset.query.filter_by(id=preset_id, staff_id=staff_id).first()
    if not preset:
        return jsonify({"message": "This preset no longer exists"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid preset"}), 400

    if "name" in data:
        name, error = _preset_name(data, staff_id, preset_id)
        if error:
            return error
        preset.name = name

    if "settings" in data:
        settings, error = _preset_settings(data["settings"])
        if error:
            return error
        preset.settings = settings

    db.session.commit()
    return jsonify({"preset": preset.to_dict(), "message": "Preset updated"}), 200


@saved_bp.route("/presets/<int:preset_id>", methods=["DELETE"])
@account_required
def delete_preset(staff_id, preset_id):
    preset = TutorialPreset.query.filter_by(id=preset_id, staff_id=staff_id).first()
    if not preset:
        return jsonify({"message": "This preset no longer exists"}), 404

    db.session.delete(preset)
    db.session.commit()
    return jsonify({"message": "Preset deleted"}), 200
