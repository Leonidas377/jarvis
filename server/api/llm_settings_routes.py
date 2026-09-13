# ==========================================================================
# JARVIS User LLM Provider Settings API Routes
# Handles Bring-Your-Own-Key (BYOK) lifecycle, AES-256-GCM encryption,
# connection diagnostics, and strict credential isolation
# ==========================================================================

import uuid
import time
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from server.auth.dependencies import get_optional_user
from server.auth.crypto import encrypt_secret, decrypt_secret, compute_fingerprint
from server.database import get_db_connection
from server.ai.providers.openai_compatible import OpenAICompatibleProvider
from server.ai.providers.gemini_provider import GeminiProvider
from server.ai.provider_factory import invalidate_user_llm_cache
from server.audit.logger import audit_logger

router = APIRouter(prefix="/api/settings/llm", tags=["User LLM Configuration (BYOK)"])

# --------------------------------------------------------------------------
# Request & Response Schemas
# --------------------------------------------------------------------------
class LLMConfigIn(BaseModel):
    provider: str = Field(default="openai-compatible", description="Provider protocol type")
    display_name: str = Field(default="NVIDIA NIM", description="Human-readable provider label")
    base_url: Optional[str] = Field(default="https://integrate.api.nvidia.com/v1", description="API Base URL")
    model: str = Field(default="meta/llama-3.2-11b-vision-instruct", description="Model identifier")
    api_key: str = Field(..., min_length=4, max_length=512, description="Provider secret API key")
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.5)
    max_output_tokens: Optional[int] = Field(default=1024, ge=16, le=4096)

class LLMConfigOut(BaseModel):
    id: str
    user_id: str
    provider: str
    display_name: str
    base_url: Optional[str] = None
    model: str
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    key_fingerprint: str
    status: str
    is_enabled: bool
    temperature: float
    max_output_tokens: int
    last_tested_at: Optional[str] = None
    last_error_code: Optional[str] = None
    created_at: str
    updated_at: str

class LLMTestIn(BaseModel):
    provider: str = "openai-compatible"
    display_name: Optional[str] = "Provider Diagnostic"
    base_url: Optional[str] = "https://integrate.api.nvidia.com/v1"
    model: str = "meta/llama-3.2-11b-vision-instruct"
    api_key: Optional[str] = None  # If omitted, test saved key
    organization_id: Optional[str] = None
    project_id: Optional[str] = None

class LLMTestOut(BaseModel):
    status: str
    message: str
    provider: str
    model: str
    latency_ms: Optional[int] = None

class LLMStatusUpdateIn(BaseModel):
    is_enabled: bool

# --------------------------------------------------------------------------
# Route Handlers
# --------------------------------------------------------------------------

@router.get("", response_model=Optional[LLMConfigOut])
async def get_user_llm_config(user: dict = Depends(get_optional_user)):
    """
    Returns safe configuration metadata for the authenticated user.
    CRITICAL: The raw API key and encrypted cipher payload are NEVER returned.
    """
    user_id = user["id"]
    async with await get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, user_id, provider, display_name, base_url, model, organization_id, project_id,
                   key_fingerprint, status, is_enabled, temperature, max_output_tokens,
                   last_tested_at, last_error_code, created_at, updated_at
            FROM user_llm_configs
            WHERE user_id = ?
        """, (user_id,))
        row = await cur.fetchone()

    if not row:
        return None

    return LLMConfigOut(
        id=row["id"],
        user_id=row["user_id"],
        provider=row["provider"],
        display_name=row["display_name"],
        base_url=row["base_url"],
        model=row["model"],
        organization_id=row["organization_id"],
        project_id=row["project_id"],
        key_fingerprint=row["key_fingerprint"],
        status=row["status"],
        is_enabled=bool(row["is_enabled"]),
        temperature=float(row["temperature"]),
        max_output_tokens=int(row["max_output_tokens"]),
        last_tested_at=row["last_tested_at"],
        last_error_code=row["last_error_code"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

@router.post("", response_model=LLMConfigOut)
async def save_user_llm_config(payload: LLMConfigIn, user: dict = Depends(get_optional_user)):
    """
    Saves or replaces the user's LLM configuration.
    Validates base_url against SSRF, encrypts API key using AES-256-GCM, and updates database.
    """
    user_id = user["id"]
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # Validate provider and base_url
    provider_type = payload.provider.lower().strip()
    base_url = (payload.base_url or "").strip().rstrip("/")
    if provider_type in ["openai-compatible", "openai", "custom"]:
        if not base_url:
            base_url = "https://api.openai.com/v1"

    # Encrypt raw API key with AES-256-GCM
    try:
        encrypted_key = encrypt_secret(payload.api_key)
        fingerprint = compute_fingerprint(payload.api_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security encryption failure: {str(e)}"
        )

    # Validate connectivity with temporary instance
    test_status = "untested"
    test_err_code = None
    try:
        if provider_type in ["google", "gemini"]:
            test_client = GeminiProvider(
                api_key=payload.api_key,
                model=payload.model,
                display_name=payload.display_name
            )
        else:
            test_client = OpenAICompatibleProvider(
                api_key=payload.api_key,
                base_url=base_url,
                model=payload.model,
                display_name=payload.display_name,
                organization_id=payload.organization_id,
                project_id=payload.project_id
            )
        test_result = await test_client.test_connection()
        test_status = "connected" if test_result.status == "CONNECTED" else "invalid"
        test_err_code = test_result.status if test_result.status != "CONNECTED" else None
    except Exception as e:
        test_status = "invalid"
        test_err_code = "VALIDATION_FAILED"

    # Save to SQLite WAL
    config_id = str(uuid.uuid4())
    async with await get_db_connection() as db:
        await db.execute("""
            INSERT INTO user_llm_configs (
                id, user_id, provider, display_name, base_url, model,
                organization_id, project_id, encrypted_api_key, key_fingerprint,
                status, is_enabled, temperature, max_output_tokens,
                last_tested_at, last_error_code, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                provider = excluded.provider,
                display_name = excluded.display_name,
                base_url = excluded.base_url,
                model = excluded.model,
                organization_id = excluded.organization_id,
                project_id = excluded.project_id,
                encrypted_api_key = excluded.encrypted_api_key,
                key_fingerprint = excluded.key_fingerprint,
                status = excluded.status,
                is_enabled = 1,
                temperature = excluded.temperature,
                max_output_tokens = excluded.max_output_tokens,
                last_tested_at = excluded.last_tested_at,
                last_error_code = excluded.last_error_code,
                updated_at = excluded.updated_at;
        """, (
            config_id, user_id, provider_type, payload.display_name, base_url, payload.model,
            payload.organization_id, payload.project_id, encrypted_key, fingerprint,
            test_status, payload.temperature or 0.7, payload.max_output_tokens or 1024,
            now_str, test_err_code, now_str, now_str
        ))
        await db.commit()

    # Invalidate cached in-memory client
    invalidate_user_llm_cache(user_id)

    await audit_logger.log_event(
        event_type="LLM_CONFIG_SAVED",
        action="llm.configure",
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        details={"provider": provider_type, "model": payload.model, "status": test_status}
    )

    return LLMConfigOut(
        id=config_id,
        user_id=user_id,
        provider=provider_type,
        display_name=payload.display_name,
        base_url=base_url,
        model=payload.model,
        organization_id=payload.organization_id,
        project_id=payload.project_id,
        key_fingerprint=fingerprint,
        status=test_status,
        is_enabled=True,
        temperature=payload.temperature or 0.7,
        max_output_tokens=payload.max_output_tokens or 1024,
        last_tested_at=now_str,
        last_error_code=test_err_code,
        created_at=now_str,
        updated_at=now_str
    )

@router.post("/test", response_model=LLMTestOut)
async def test_llm_connection(payload: LLMTestIn, user: dict = Depends(get_optional_user)):
    """
    Tests an LLM connection without persisting anything.
    If api_key is omitted, retrieves and decrypts the user's currently saved key.
    """
    user_id = user["id"]
    api_key = payload.api_key

    # If no key in test payload, use stored key
    if not api_key:
        async with await get_db_connection() as db:
            cur = await db.execute("SELECT encrypted_api_key FROM user_llm_configs WHERE user_id = ?", (user_id,))
            row = await cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No API key provided and no configuration saved yet."
                )
            try:
                api_key = decrypt_secret(row["encrypted_api_key"])
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to decrypt saved key."
                )

    provider_type = payload.provider.lower().strip()
    base_url = (payload.base_url or "").strip().rstrip("/")
    if provider_type in ["openai-compatible", "openai", "custom"] and not base_url:
        base_url = "https://api.openai.com/v1"

    try:
        if provider_type in ["google", "gemini"]:
            client = GeminiProvider(
                api_key=api_key,
                model=payload.model,
                display_name=payload.display_name or "Google Gemini"
            )
        else:
            client = OpenAICompatibleProvider(
                api_key=api_key,
                base_url=base_url,
                model=payload.model,
                display_name=payload.display_name or "OpenAI-Compatible",
                organization_id=payload.organization_id,
                project_id=payload.project_id
            )

        result = await client.test_connection()
        return LLMTestOut(
            status=result.status,
            message=result.message,
            provider=result.provider,
            model=result.model,
            latency_ms=result.latency_ms
        )

    except ValueError as ve:
        return LLMTestOut(
            status="CONFIGURATION_ERROR",
            message=str(ve),
            provider=payload.display_name or provider_type,
            model=payload.model
        )
    except Exception as e:
        return LLMTestOut(
            status="PROVIDER_UNREACHABLE",
            message=f"Connection diagnostic failed: {str(e)[:100]}",
            provider=payload.display_name or provider_type,
            model=payload.model
        )

@router.patch("/status", response_model=LLMConfigOut)
async def update_llm_status(payload: LLMStatusUpdateIn, user: dict = Depends(get_optional_user)):
    """Enables or disables the user's configured LLM."""
    user_id = user["id"]
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with await get_db_connection() as db:
        await db.execute("""
            UPDATE user_llm_configs
            SET is_enabled = ?, updated_at = ?
            WHERE user_id = ?
        """, (1 if payload.is_enabled else 0, now_str, user_id))
        await db.commit()

        cur = await db.execute("""
            SELECT id, user_id, provider, display_name, base_url, model, organization_id, project_id,
                   key_fingerprint, status, is_enabled, temperature, max_output_tokens,
                   last_tested_at, last_error_code, created_at, updated_at
            FROM user_llm_configs
            WHERE user_id = ?
        """, (user_id,))
        row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No LLM configuration found.")

    invalidate_user_llm_cache(user_id)

    await audit_logger.log_event(
        event_type="LLM_STATUS_UPDATED",
        action="llm.status",
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        details={"is_enabled": payload.is_enabled}
    )

    return LLMConfigOut(
        id=row["id"],
        user_id=row["user_id"],
        provider=row["provider"],
        display_name=row["display_name"],
        base_url=row["base_url"],
        model=row["model"],
        organization_id=row["organization_id"],
        project_id=row["project_id"],
        key_fingerprint=row["key_fingerprint"],
        status=row["status"],
        is_enabled=bool(row["is_enabled"]),
        temperature=float(row["temperature"]),
        max_output_tokens=int(row["max_output_tokens"]),
        last_tested_at=row["last_tested_at"],
        last_error_code=row["last_error_code"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

@router.delete("")
async def delete_user_llm_config(user: dict = Depends(get_optional_user)):
    """
    Permanently removes the user's LLM configuration and key ciphertext.
    Clears all cached in-memory clients.
    """
    user_id = user["id"]
    async with await get_db_connection() as db:
        await db.execute("DELETE FROM user_llm_configs WHERE user_id = ?", (user_id,))
        await db.commit()

    invalidate_user_llm_cache(user_id)

    await audit_logger.log_event(
        event_type="LLM_CONFIG_DELETED",
        action="llm.delete",
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        details={"status": "deleted"}
    )

    return {"status": "DELETED", "message": "LLM configuration and encrypted keys permanently deleted."}
