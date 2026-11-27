from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required

from ..auth import ACCOUNT, get_staff_identity
from ..custom_attributes import parse_custom_attribute
from ..database import db, SavedAttribute


# Custom Details (and other settings) saved to a Staff Account
saved_bp = Blueprint("saved", __name__, url_prefix="/staff")

MAX_SAVED_ATTRIBUTES = 50


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
