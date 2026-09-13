# ==========================================================================
# Comprehensive Test Suite: User-Provided LLM API Key (BYOK) Integration
# Verifies AES-256-GCM encryption, secret isolation, SSRF defenses,
# diagnostic error normalization, API lifecycles, and agent orchestration
# ==========================================================================

import pytest
import uuid
import httpx
from fastapi.testclient import TestClient

from server.main import app
from server.database import init_db, get_db_connection
from server.auth.crypto import encrypt_secret, decrypt_secret, compute_fingerprint
from server.auth.security import create_access_token
from server.ai.providers.openai_compatible import OpenAICompatibleProvider
from server.ai.provider_factory import get_user_llm_client, invalidate_user_llm_cache
from server.ai.orchestrator import orchestrator, OrchestrationState

client = TestClient(app)

# --------------------------------------------------------------------------
# 1. Cryptography & Secret Storage Tests
# --------------------------------------------------------------------------

def test_aes_256_gcm_encryption_roundtrip():
    secret_key = "nvapi-TestSecretKey1234567890ABCDEF"
    encrypted = encrypt_secret(secret_key)

    # Must not contain the plaintext key
    assert secret_key not in encrypted
    assert len(encrypted) > len(secret_key)

    # Decrypt only in memory
    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret_key

def test_aes_256_gcm_corrupted_payload_rejected():
    with pytest.raises(Exception):
        decrypt_secret("invalid-truncated-base64")

def test_compute_fingerprint_never_exposes_raw_key():
    key = "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"
    fp = compute_fingerprint(key)
    assert fp.endswith("6D7N")
    assert "MkNr" not in fp
    assert "nvapi" not in fp
    assert "•" in fp

# --------------------------------------------------------------------------
# 2. SSRF Protection on Provider Base URL
# --------------------------------------------------------------------------

def test_ssrf_blocked_cloud_metadata_base_url():
    with pytest.raises(ValueError) as exc:
        OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://169.254.169.254/v1"
        )
    assert "security policy" in str(exc.value).lower() or "private or restricted" in str(exc.value).lower()

def test_ssrf_blocked_private_network_base_url():
    with pytest.raises(ValueError) as exc:
        OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://192.168.1.50:8000/v1"
        )
    assert "security policy" in str(exc.value).lower() or "private or restricted" in str(exc.value).lower()

def test_ssrf_blocked_invalid_scheme():
    with pytest.raises(ValueError) as exc:
        OpenAICompatibleProvider(
            api_key="test-key",
            base_url="file:///etc/secrets/api"
        )
    assert "invalid url scheme" in str(exc.value).lower()

# --------------------------------------------------------------------------
# 3. API Endpoints: Save, Retrieve, Test, Status, and Delete Lifecycle
# --------------------------------------------------------------------------

async def seed_test_user(user_id: str, username: str):
    async with await get_db_connection() as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (id, username, email, hashed_password, display_name, status, created_at)
            VALUES (?, ?, ?, 'test_hash', ?, 'active', datetime('now'))
        """, (user_id, username, f"{username}@test.com", username))
        await db.commit()

@pytest.mark.asyncio
async def test_llm_config_api_lifecycle_and_zero_key_exposure():
    await init_db()
    test_user_id = f"user-{uuid.uuid4().hex[:8]}"
    username = f"user_{test_user_id}"
    await seed_test_user(test_user_id, username)
    token = create_access_token({"sub": test_user_id, "username": username})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initially GET returns None
    get_res = client.get("/api/settings/llm", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json() is None

    # 2. POST Save configuration with API key
    raw_api_key = "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"
    save_payload = {
        "provider": "openai-compatible",
        "display_name": "NVIDIA NIM Cloud",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.2-11b-vision-instruct",
        "api_key": raw_api_key,
        "temperature": 0.7,
        "max_output_tokens": 1024
    }

    save_res = client.post("/api/settings/llm", json=save_payload, headers=headers)
    assert save_res.status_code == 200
    save_data = save_res.json()

    # Verify safe fields returned
    assert save_data["provider"] == "openai-compatible"
    assert save_data["display_name"] == "NVIDIA NIM Cloud"
    assert save_data["model"] == "meta/llama-3.2-11b-vision-instruct"
    assert save_data["is_enabled"] is True
    assert save_data["key_fingerprint"].endswith("6D7N")

    # CRITICAL SECURITY CHECK: Raw API key and encrypted cipher must NEVER be in response
    assert "api_key" not in save_data
    assert "encrypted_api_key" not in save_data
    assert raw_api_key not in str(save_res.text)

    # 3. Verify Database Storage is Encrypted (No Plaintext)
    async with await get_db_connection() as db:
        cur = await db.execute("SELECT encrypted_api_key, key_fingerprint FROM user_llm_configs WHERE user_id = ?", (test_user_id,))
        db_row = await cur.fetchone()
        assert db_row is not None
        assert raw_api_key not in db_row["encrypted_api_key"]
        # Decrypt verifies roundtrip
        assert decrypt_secret(db_row["encrypted_api_key"]) == raw_api_key

    # 4. Subsequent GET returns safe metadata without raw key
    get_res2 = client.get("/api/settings/llm", headers=headers)
    assert get_res2.status_code == 200
    get_data = get_res2.json()
    assert get_data["key_fingerprint"].endswith("6D7N")
    assert raw_api_key not in str(get_res2.text)

    # 5. PATCH /api/settings/llm/status toggles enable/disable
    patch_res = client.patch("/api/settings/llm/status", json={"is_enabled": False}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["is_enabled"] is False

    # 6. DELETE /api/settings/llm clears configuration
    del_res = client.delete("/api/settings/llm", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"

    # Verify deleted from DB
    get_res3 = client.get("/api/settings/llm", headers=headers)
    assert get_res3.status_code == 200
    assert get_res3.json() is None

# --------------------------------------------------------------------------
# 4. User Isolation Test (User A cannot access User B's key)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_data_isolation():
    await init_db()
    user_a_id = f"user-a-{uuid.uuid4().hex[:6]}"
    user_b_id = f"user-b-{uuid.uuid4().hex[:6]}"
    await seed_test_user(user_a_id, "usera")
    await seed_test_user(user_b_id, "userb")
    token_a = create_access_token({"sub": user_a_id, "username": "usera"})
    token_b = create_access_token({"sub": user_b_id, "username": "userb"})

    # User A saves config
    client.post("/api/settings/llm", json={
        "provider": "openai-compatible",
        "display_name": "User A Provider",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.2-11b-vision-instruct",
        "api_key": "nvapi-SecretUserA-AAAA"
    }, headers={"Authorization": f"Bearer {token_a}"})

    # User B requests config -> Must be empty (cannot see User A's config)
    res_b = client.get("/api/settings/llm", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.json() is None

    # User B cannot resolve User A's client
    client_b = await get_user_llm_client(user_b_id)
    assert client_b is None

    # User A resolves their own client
    client_a = await get_user_llm_client(user_a_id)
    assert client_a is not None
    assert client_a.display_name == "User A Provider"

# --------------------------------------------------------------------------
# 5. Connection Test Diagnostic & Redaction Test
# --------------------------------------------------------------------------

def test_connection_test_diagnostics_normalizes_error():
    # Test with deliberate invalid key
    res = client.post("/api/settings/llm/test", json={
        "provider": "openai-compatible",
        "display_name": "Test Check",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.2-11b-vision-instruct",
        "api_key": "nvapi-definitely-invalid-key-00000000"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["INVALID_KEY", "MODEL_NOT_FOUND", "CONFIGURATION_ERROR", "TIMEOUT"]
    assert "nvapi-definitely-invalid-key" not in data["message"]
