# ==========================================================================
# JARVIS Auth Dependencies for FastAPI
# ==========================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from server.auth.security import decode_access_token
from server.database import get_db_connection

security_bearer = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> dict:
    """Extracts and verifies the current authenticated user from Bearer JWT."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload["sub"]
    async with await get_db_connection() as db:
        cursor = await db.execute("SELECT id, username, email, display_name, status FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identity no longer exists.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return dict(row)

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> dict:
    """Returns authenticated user if token present; otherwise defaults to demo guest user."""
    if credentials:
        try:
            return await get_current_user(credentials)
        except HTTPException:
            pass

    # Default fallback for demo / standalone operation
    return {
        "id": "default-tony-stark",
        "username": "tony_stark",
        "email": "tony@starkindustries.com",
        "display_name": "Tony Stark",
        "status": "active"
    }
