# ==========================================================================
# JARVIS Centralized Policy & Risk Evaluation Engine
# ==========================================================================

from typing import Optional, Dict, Any
from pydantic import BaseModel
from server.models.schemas import RiskLevel
from server.permissions.scopes import Scope
from server.permissions.approval_service import verify_approval_unexpired

class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool = False
    risk_level: str
    reason: str
    approval_id: Optional[str] = None

class PolicyEngine:
    """Evaluates multi-tier security permissions and risk levels before tool execution."""

    @staticmethod
    async def evaluate(
        user: dict,
        tool: Any,
        parameters: Dict[str, Any],
        supplied_approval_id: Optional[str] = None
    ) -> PolicyDecision:
        user_id = user["id"]
        risk_level = getattr(tool, "risk_level", RiskLevel.R0_SAFE.value)
        required_scope = getattr(tool, "required_scope", None)
        requires_confirmation = getattr(tool, "requires_confirmation", False)

        # 1. Global Guardrail: Trading orders strictly disabled in this phase
        if required_scope == Scope.BROKER_TRADE.value or "trade" in tool.name.lower():
            return PolicyDecision(
                allowed=False,
                risk_level=RiskLevel.R4_CRITICAL.value,
                reason="Live trading execution is disabled in this implementation phase."
            )

        # 2. Risk R0: Safe read operations auto-execute immediately
        if risk_level == RiskLevel.R0_SAFE.value and not requires_confirmation:
            return PolicyDecision(
                allowed=True,
                requires_approval=False,
                risk_level=risk_level,
                reason="Auto-authorized: Safe read-only operation."
            )

        # 3. Check if user already provided an unexpired valid approval ID
        if supplied_approval_id:
            is_valid = await verify_approval_unexpired(supplied_approval_id, user_id)
            if is_valid:
                return PolicyDecision(
                    allowed=True,
                    requires_approval=False,
                    risk_level=risk_level,
                    reason="Authorized by confirmed user approval.",
                    approval_id=supplied_approval_id
                )
            else:
                return PolicyDecision(
                    allowed=False,
                    requires_approval=False,
                    risk_level=risk_level,
                    reason="Provided approval ID is invalid, rejected, or expired."
                )

        # 4. If confirmation required and no approval provided yet, trigger approval gate
        if requires_confirmation or risk_level in [RiskLevel.R2_MEDIUM.value, RiskLevel.R3_HIGH.value, RiskLevel.R4_CRITICAL.value]:
            return PolicyDecision(
                allowed=False,
                requires_approval=True,
                risk_level=risk_level,
                reason=f"Action requires explicit user confirmation (Risk: {risk_level})."
            )

        # 5. Default allow for low-risk non-sensitive tools (like create_task)
        return PolicyDecision(
            allowed=True,
            requires_approval=False,
            risk_level=risk_level,
            reason="Authorized: Low-risk task operation."
        )

policy_engine = PolicyEngine()
