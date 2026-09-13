# ==========================================================================
# JARVIS LLM Provider Factory & Client Lifecycle Manager
# Resolves user-configured LLM with AES-256-GCM in-memory decryption
# ==========================================================================

from typing import Dict, Any, Optional
from server.database import get_db_connection
from server.auth.crypto import decrypt_secret
from server.ai.providers.base import LLMClient
from server.ai.providers.openai_compatible import OpenAICompatibleProvider
from server.ai.providers.gemini_provider import GeminiProvider

# In-memory per-user client cache: {user_id: (client, config_fingerprint)}
_CLIENT_CACHE: Dict[str, tuple[LLMClient, str]] = {}

async def get_user_llm_client(user_id: str) -> Optional[LLMClient]:
    """
    Retrieves and instantiates the active LLM client for an authenticated user.
    Decrypts the secret key ONLY in backend memory at instantiation time.
    """
    async with await get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, provider, display_name, base_url, model, organization_id, project_id,
                   encrypted_api_key, key_fingerprint, status, is_enabled, temperature, max_output_tokens
            FROM user_llm_configs
            WHERE user_id = ?
        """, (user_id,))
        row = await cur.fetchone()

    if not row:
        return None

    if not bool(row["is_enabled"]):
        return None

    fingerprint = f"{row['provider']}:{row['model']}:{row['key_fingerprint']}:{row['temperature']}"

    # Check memory cache
    if user_id in _CLIENT_CACHE:
        cached_client, cached_fingerprint = _CLIENT_CACHE[user_id]
        if cached_fingerprint == fingerprint:
            return cached_client

    # Decrypt key in memory
    try:
        raw_key = decrypt_secret(row["encrypted_api_key"])
    except Exception as e:
        print(f"[JARVIS SECURITY] Failed to decrypt user API key for user {user_id}: {str(e)}")
        return None

    provider_type = row["provider"].lower()
    base_url = row["base_url"] or "https://api.openai.com/v1"
    model = row["model"]
    display_name = row["display_name"]
    temp = float(row["temperature"] or 0.7)
    max_tokens = int(row["max_output_tokens"] or 1024)

    client: LLMClient
    if provider_type in ["google", "gemini"]:
        client = GeminiProvider(
            api_key=raw_key,
            model=model,
            display_name=display_name,
            temperature=temp,
            max_output_tokens=max_tokens
        )
    else:
        # Default to OpenAI-compatible (works with NVIDIA NIM, OpenAI, Groq, DeepSeek, Together, etc.)
        client = OpenAICompatibleProvider(
            api_key=raw_key,
            base_url=base_url,
            model=model,
            display_name=display_name,
            organization_id=row["organization_id"],
            project_id=row["project_id"],
            temperature=temp,
            max_output_tokens=max_tokens
        )

    # Store in memory cache
    _CLIENT_CACHE[user_id] = (client, fingerprint)
    return client

def invalidate_user_llm_cache(user_id: str) -> None:
    """Invalidates the in-memory client cache when configuration is modified, disabled, or deleted."""
    if user_id in _CLIENT_CACHE:
        del _CLIENT_CACHE[user_id]
