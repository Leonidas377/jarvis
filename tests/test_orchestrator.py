# ==========================================================================
# Tests: AI Orchestrator & Multi-Step Execution
# ==========================================================================

import pytest
from server.database import init_db
from server.ai.orchestrator import orchestrator, OrchestrationState

@pytest.mark.asyncio
async def test_orchestrator_conversational_message():
    await init_db()
    user = {"id": "default-tony-stark", "username": "tony_stark"}

    result = await orchestrator.process_message(
        user=user,
        content="Status report on core telemetry"
    )

    assert result["state"] == OrchestrationState.COMPLETED
    assert result["approval_required"] is False
    assert len(result["response"]) > 10

@pytest.mark.asyncio
async def test_orchestrator_safe_tool_execution():
    await init_db()
    user = {"id": "default-tony-stark", "username": "tony_stark"}

    result = await orchestrator.process_message(
        user=user,
        content="create task: inspect drone telemetry"
    )

    assert result["state"] == OrchestrationState.COMPLETED
    assert result["approval_required"] is False
    assert result["tool_executed"] is not None
    assert result["tool_executed"]["tool"] == "create_task"

@pytest.mark.asyncio
async def test_orchestrator_approval_gated_execution():
    await init_db()
    user = {"id": "default-tony-stark", "username": "tony_stark"}

    # Asking to remember something triggers save_memory (Risk R2)
    result = await orchestrator.process_message(
        user=user,
        content="remember that flight ceiling is 45000 feet"
    )

    assert result["approval_required"] is True
    assert result["approval_request"] is not None
    assert result["approval_request"]["tool_name"] == "save_memory"
    assert "requires explicit authorization" in result["response"].lower()
