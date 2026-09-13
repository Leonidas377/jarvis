# ==========================================================================
# Tests: Authentication & Security Tokens
# ==========================================================================

import pytest
from server.auth.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing_and_verification():
    raw_secret = "StarkTower#2026!Quantum"
    hashed = hash_password(raw_secret)
    
    assert hashed != raw_secret
    assert ":" in hashed
    assert verify_password(raw_secret, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False

def test_jwt_token_generation_and_decoding():
    user_payload = {"sub": "user-uuid-12345", "username": "tony_stark"}
    token = create_access_token(user_payload)
    
    assert isinstance(token, str)
    assert len(token) > 20
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-uuid-12345"
    assert decoded["username"] == "tony_stark"
    assert "exp" in decoded

def test_invalid_jwt_token():
    assert decode_access_token("corrupted.jwt.token.string") is None
    assert decode_access_token("") is None
