from flask_bcrypt import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, decode_token
from gevent.lock import BoundedSemaphore
from gevent.threadpool import ThreadPool
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import time, uuid

from .database import db, Staff


# Staff may use the application as a Guest or with an Account.
# NOTE Both currently have the same access, but each Token records
# its type so account-only features can be added later.
GUEST = "guest"
ACCOUNT = "account"

MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH = 3, 50
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72 # Limit of bcrypt

MAX_LOGIN_ATTEMPTS = 10 # Failed attempts per Address and Username
MAX_REGISTER_ATTEMPTS = 20 # Attempts per Address
ATTEMPT_WINDOW = 5 * 60 # Seconds
MAX_PENDING_PASSWORDS = 20

auth_attempts = dict() # { (action, address, ...): [time, ...] }

# Password Functions are Slow by design, so are run on other threads to not hold up every running Tutorial
password_pool = ThreadPool(2)
pending_passwords = BoundedSemaphore(MAX_PENDING_PASSWORDS)

# Checked when a Username doesn't exist, so that it takes the same time as when it does
DUMMY_PASSWORD_HASH = generate_password_hash(str(uuid.uuid4()))


def is_possible_login(username: str, password: str) -> bool:
    """Whether a username and password are in a form which could belong to a staff account"""
    try:
        username.encode()
        return len(username) <= MAX_USERNAME_LENGTH and len(password.encode()) <= MAX_PASSWORD_BYTES
    except UnicodeEncodeError:
        return False


def verify_staff_login(username: str, password: str) -> Staff | None:
    """Returns the staff account which the username and password belong to (None if either are incorrect)"""
    staff: Staff | None = Staff.query.filter_by(username=username).first()
    staff_id, password_hash = (staff.id, staff.password_hash) if staff else (None, DUMMY_PASSWORD_HASH)

    matches = _run_password_function(check_password_hash, password_hash, password)
    return db.session.get(Staff, staff_id) if matches and staff_id is not None else None


def validate_staff_account(username: str, password: str) -> str | None:
    """Returns an error message if a new staff account can't use the username or password"""
    if not MIN_USERNAME_LENGTH <= len(username) <= MAX_USERNAME_LENGTH:
        return f"Your username must be between {MIN_USERNAME_LENGTH} and {MAX_USERNAME_LENGTH} Characters"
    if not username.isprintable():
        return "Your Username has Characters which can't be used"
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Your Password must be at least {MIN_PASSWORD_LENGTH} Characters"
    if "\x00" in password or not is_possible_login(username, password):
        return "Your Password is Too Long or has Characters which can't be used"

    return None


def register_staff(username: str, password: str) -> Staff | None:
    """Creates a staff account (None if the username is already taken, regardless of its letter case)"""
    if Staff.query.filter(func.lower(Staff.username) == username.lower()).first():
        return None

    password_hash = _run_password_function(generate_password_hash, password).decode()
    staff = Staff(username=username, password_hash=password_hash)
    db.session.add(staff)
    try:
        db.session.commit()
    except IntegrityError: # Taken while the Password was being Hashed
        db.session.rollback()
        return None

    return staff


def _run_password_function(function, *args):
    # Return the Database Connection before waiting, as the server is held up if they're all in use
    db.session.close()

    with pending_passwords:
        return password_pool.apply(function, args)


def record_attempt(*key, limit: int) -> bool:
    """Records an attempt of an action, returning False if there have been (or are currently) too many"""
    if pending_passwords.locked():
        return False

    current_time = time.monotonic()
    for other_key, attempts in list(auth_attempts.items()):
        if current_time - attempts[-1] > ATTEMPT_WINDOW:
            del auth_attempts[other_key]

    attempts = [attempt for attempt in auth_attempts.get(key, []) if current_time - attempt <= ATTEMPT_WINDOW]
    if len(attempts) >= limit:
        return False

    auth_attempts[key] = attempts + [current_time]
    return True


def clear_attempts(*key):
    auth_attempts.pop(key, None)


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
