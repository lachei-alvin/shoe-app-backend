from passlib.context import CryptContext
from datetime import timedelta
from typing import Optional
# Omitted imports from jose (JWT library)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MOCK JWT configuration (Retained for structure, but logic is gone)
SECRET_KEY = "MOCK_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Retained for type hinting compatibility if needed

# --- Password Hashing Functions (Required for Mock User Creation) ---


def get_password_hash(password: str) -> str:
    """Hashes a plain text password."""
    return pwd_context.hash(password)


# Removed: verify_password, create_access_token, decode_access_token
