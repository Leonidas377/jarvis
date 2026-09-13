# ==========================================================================
# JARVIS Authentication & Cryptographic Security
# ==========================================================================

import os
import hashlib
import hmac
import time
import jwt
from typing import Optional, Dict, Any
from server.config import settings

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique 16-byte salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt:hash string."""
    try:
        salt_hex, key_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False

def create_access_token(user_id_or_data: Any, username: Optional[str] = None, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """Generates an encoded JWT access token with an expiration timestamp."""
    now = int(time.time())
    expires = now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    if isinstance(user_id_or_data, dict):
        payload = dict(user_id_or_data)
        if "iat" not in payload: payload["iat"] = now
        if "exp" not in payload: payload["exp"] = expires
    else:
        payload = {
            "sub": str(user_id_or_data),
            "username": username or "user",
            "iat": now,
            "exp": expires
        }

    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT access token, returning the payload or None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None
