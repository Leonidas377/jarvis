# ==========================================================================
# Tests: Human Approval Lifecycle
# ==========================================================================

import pytest
from server.database import init_db
from server.permissions.approval_service import (
    create_approval_request,
    get_pending_approvals,
    decide_approval,
    verify_approval_unexpired
)

@pytest.mark.asyncio
async def test_approval_lifecycle_flow():
    await init_db()
    user_id = "default-tony-stark"

    # 1. Create approval request
    req = await create_approval_request(
        user_id=user_id,
        conversation_id="conv-test-1",
        tool_name="save_memory",
        summary="Authorize saving preference: Coffee is black",
        parameters={"category": "Preferences", "key": "Coffee", "value": "black"},
        risk_level="R2_MEDIUM",
        ttl_seconds=300
    )

    assert req["id"] is not None
    assert req["status"] == "pending"
    approval_id = req["id"]

    # 2. Query pending
    pending = await get_pending_approvals(user_id)
    assert any(p["id"] == approval_id for p in pending)

    # 3. Verify not approved yet
    assert await verify_approval_unexpired(approval_id, user_id) is False

    # 4. Decide approve
    decided = await decide_approval(approval_id, user_id, action="approve")
    assert decided is True

    # 5. Verify now approved and unexpired
    assert await verify_approval_unexpired(approval_id, user_id) is True
