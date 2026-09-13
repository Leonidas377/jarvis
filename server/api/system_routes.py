# ==========================================================================
# JARVIS System Status & Tool Catalog API Routes
# ==========================================================================

import time
from typing import Dict, Any, List
from fastapi import APIRouter
from server.tools.registry import default_registry
from server.ai.provider import get_ai_provider

router = APIRouter(prefix="/api", tags=["System & Telemetry"])

_START_TIME = time.time()

@router.get("/system/status")
async def system_status() -> Dict[str, Any]:
    uptime_seconds = int(time.time() - _START_TIME)
    provider = get_ai_provider()
    tools = default_registry.list_tools()

    return {
        "status": "ONLINE",
        "system_name": "J.A.R.V.I.S. Android Operating Core",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "ai_engine": getattr(provider, "model", "cognitive-local"),
        "database": "SQLite 3 (WAL mode enabled)",
        "registered_tools_count": len(tools),
        "policy_mode": "STRICT_CONFIRMATION_ENFORCED",
        "live_trading_enabled": False,
        "safety_guardrails": "ACTIVE"
    }

@router.get("/tools")
async def list_tools() -> List[Dict[str, Any]]:
    return default_registry.list_tools()
