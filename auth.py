import hashlib
import secrets
from database.connection import SessionLocal
from database.models import User

def hash_password(password, salt=None):
    """Creates a secure hash of the password."""
    if salt is None:
        salt = secrets.token_hex(16)
    # Using PBKDF2 with SHA256 (Standard Security)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + ':' + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Checks if the provided password matches the stored hash."""
    try:
        salt = stored_password.split(':')[0]
        return stored_password == hash_password(provided_password, salt)
    except:
        return False

def authenticate_user(username, password):
    """Returns the User object if credentials are valid, else None."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(user.hashed_password, password):
            return None
        return user
    finally:
        db.close()