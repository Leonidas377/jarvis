# ==========================================================================
# JARVIS Secret Management: AES-256-GCM Encryption at Rest
# Protects User-Provided LLM API Keys with hardware-speed AEAD encryption
# ==========================================================================

import os
import base64
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from server.config import settings

_SECRETS_KEY_FILE = Path(__file__).resolve().parent.parent / ".secrets.key"
_CACHED_KEK: bytes = b""

def get_key_encryption_key() -> bytes:
    """
    Retrieves or derives the 256-bit Key Encryption Key (KEK).
    Preference order:
    1. Explicit environment variable JARVIS_LLM_ENCRYPTION_KEY (base64 or hex).
    2. Persisted local key file (server/.secrets.key) stored outside database.
    3. Derived deterministically from server JWT_SECRET via SHA-256 fallback.
    """
    global _CACHED_KEK
    if _CACHED_KEK and len(_CACHED_KEK) == 32:
        return _CACHED_KEK

    env_key = os.getenv("JARVIS_LLM_ENCRYPTION_KEY", "").strip()
    if env_key:
        try:
            # Check if base64 or hex
            if len(env_key) == 64:
                _CACHED_KEK = bytes.fromhex(env_key)
            else:
                _CACHED_KEK = base64.b64decode(env_key)
            if len(_CACHED_KEK) == 32:
                return _CACHED_KEK
        except Exception:
            pass

    # Check local key file
    if _SECRETS_KEY_FILE.exists():
        try:
            with open(_SECRETS_KEY_FILE, "rb") as f:
                key_bytes = f.read().strip()
                if len(key_bytes) == 32:
                    _CACHED_KEK = key_bytes
                    return _CACHED_KEK
        except Exception:
            pass

    # Generate new random 256-bit key and persist to key file
    try:
        new_key = AESGCM.generate_key(bit_length=256)
        with open(_SECRETS_KEY_FILE, "wb") as f:
            f.write(new_key)
        _CACHED_KEK = new_key
        return _CACHED_KEK
    except Exception:
        # Fallback to derivation from JWT_SECRET
        derived = hashlib.sha256(settings.JWT_SECRET.encode("utf-8") + b"::JARVIS_KEK_SALT").digest()
        _CACHED_KEK = derived
        return _CACHED_KEK

def encrypt_secret(plaintext: str) -> str:
    """
    Encrypts sensitive plaintext using AES-256-GCM.
    Returns base64-encoded string: nonce (12 bytes) + ciphertext + auth tag (16 bytes).
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty secret.")

    kek = get_key_encryption_key()
    aesgcm = AESGCM(kek)
    nonce = os.urandom(12)  # 96-bit random nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("ascii")

def decrypt_secret(encrypted_b64: str) -> str:
    """
    Decrypts AES-256-GCM encrypted base64 payload.
    Decrypts only in backend memory at execution time.
    """
    if not encrypted_b64:
        raise ValueError("Cannot decrypt empty payload.")

    raw = base64.b64decode(encrypted_b64)
    if len(raw) < 28:  # 12-byte nonce + 16-byte minimum tag
        raise ValueError("Corrupted or truncated ciphertext.")

    nonce = raw[:12]
    ciphertext = raw[12:]
    kek = get_key_encryption_key()
    aesgcm = AESGCM(kek)
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode("utf-8")

def compute_fingerprint(secret: str) -> str:
    """
    Returns a safe masked indicator (e.g. ••••••••6D7N).
    Never reveals the secret.
    """
    if not secret:
        return "Not configured"
    clean = secret.strip()
    if len(clean) <= 4:
        return "••••"
    last_four = clean[-4:]
    return f"••••••••{last_four}"

def hash_secret_for_matching(secret: str) -> str:
    """
    Returns a cryptographic hash of the secret to safely verify identity.
    """
    clean = secret.strip().encode("utf-8")
    return hashlib.sha256(clean + b"::JARVIS_HASH_SALT").hexdigest()
