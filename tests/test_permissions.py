# ==========================================================================
# Tests: Policy Engine & Risk Evaluation
# ==========================================================================

import pytest
from server.models.schemas import RiskLevel
from server.permissions.scopes import Scope
from server.permissions.policy_engine import policy_engine
from server.tools.base import BaseTool
from pydantic import BaseModel

class DummySafeTool(BaseTool):
    name = "safe_reader"
    description = "Reads public stats"
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.CONVERSATION_READ.value
    requires_confirmation = False
    input_schema = BaseModel

    async def execute(self, params, context):
        return {"data": "read_ok"}

class DummySensitiveTool(BaseTool):
    name = "modify_memory"
    description = "Saves facts"
    risk_level = RiskLevel.R2_MEDIUM.value
    required_scope = Scope.MEMORY_WRITE.value
    requires_confirmation = True
    input_schema = BaseModel

    async def execute(self, params, context):
        return {"status": "saved"}

class DummyTradeTool(BaseTool):
    name = "execute_live_trade"
    description = "Attempts live broker trade"
    risk_level = RiskLevel.R4_CRITICAL.value
    required_scope = Scope.BROKER_TRADE.value
    requires_confirmation = True
    input_schema = BaseModel

    async def execute(self, params, context):
        return {"traded": False}

@pytest.mark.asyncio
async def test_policy_engine_safe_tool():
    user = {"id": "test-user-1"}
    decision = await policy_engine.evaluate(user, DummySafeTool(), {})
    assert decision.allowed is True
    assert decision.requires_approval is False
    assert decision.risk_level == RiskLevel.R0_SAFE.value

@pytest.mark.asyncio
async def test_policy_engine_sensitive_tool_requires_approval():
    user = {"id": "test-user-1"}
    decision = await policy_engine.evaluate(user, DummySensitiveTool(), {})
    assert decision.allowed is False
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.R2_MEDIUM.value

@pytest.mark.asyncio
async def test_policy_engine_strictly_blocks_live_trading():
    user = {"id": "test-user-1"}
    decision = await policy_engine.evaluate(user, DummyTradeTool(), {})
    assert decision.allowed is False
    assert decision.requires_approval is False
    assert "Live trading execution is disabled" in decision.reason
