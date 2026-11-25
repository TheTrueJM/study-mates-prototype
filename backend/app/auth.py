from flask_jwt_extended import create_access_token, decode_token
import uuid

from .database import db, Staff


# Staff may use the application as a Guest or with an Account.
# NOTE Both currently have the same access, but each Token records
# its type so account-only features can be added later.
GUEST = "guest"
ACCOUNT = "account"


def create_staff_token(staff: Staff | None = None) -> str:
    """Issues a staff access token for a signed in account, or for a new guest when no account is given"""
    if staff is None:
        return create_access_token(identity=str(uuid.uuid4()), additional_claims={"staff_type": GUEST})
    return create_access_token(identity=str(staff.id), additional_claims={"staff_type": ACCOUNT})


def get_staff_identity(claims: dict) -> dict | None:
    """
    Returns the staff identity of a decoded token's claims (None if invalid or the account no longer exists).
    The identity's "id" is used as the staff member's user ID throughout the tutorial sessions.
    """
    staff_type, subject = claims.get("staff_type"), claims.get("sub")
    if not isinstance(subject, str) or not subject:
        return None

    if staff_type == GUEST:
        return {"id": f"{GUEST}:{subject}", "type": GUEST, "username": None}

    if staff_type == ACCOUNT and subject.isdigit():
        if staff := db.session.get(Staff, int(subject)):
            return {"id": f"{ACCOUNT}:{staff.id}", "type": ACCOUNT, "username": staff.username}

    return None


def verify_staff_token(token) -> dict | None:
    """Validates an encoded access token (signature, expiry, and staff identity), returning the staff identity"""
    if not isinstance(token, str) or not token:
        return None

    try:
        claims = decode_token(token)
    except Exception: # Expired, Malformed, or signed with Another Key
        return None

    return get_staff_identity(claims)
