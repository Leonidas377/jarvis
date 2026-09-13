# ==========================================================================
# JARVIS Authentication API Routes
# ==========================================================================

import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, status
from server.models.schemas import UserRegister, UserLogin, UserOut, Token
from server.auth.security import hash_password, verify_password, create_access_token
from server.auth.dependencies import get_current_user, get_optional_user
from server.database import get_db_connection
from server.audit.logger import audit_logger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    user_id = str(uuid.uuid4())
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    hashed = hash_password(user_in.password)

    async with get_db_connection() as db:
        # Check existing username or email
        cur = await db.execute("SELECT id FROM users WHERE username = ? OR email = ?", (user_in.username, user_in.email))
        if await cur.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered.")

        await db.execute("""
            INSERT INTO users (id, username, email, hashed_password, display_name, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?)
        """, (user_id, user_in.username, user_in.email, hashed, user_in.display_name or "Administrator", now_str))
        await db.commit()

    token = create_access_token({"sub": user_id, "username": user_in.username})
    user_out = UserOut(
        id=user_id,
        username=user_in.username,
        email=user_in.email,
        display_name=user_in.display_name or "Administrator",
        created_at=now_str,
        status="active"
    )

    await audit_logger.log_event(
        event_type="USER_REGISTERED",
        action="auth.register",
        user_id=user_id,
        details={"username": user_in.username}
    )

    return Token(access_token=token, token_type="bearer", user=user_out)

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, username, email, hashed_password, display_name, status, created_at
            FROM users WHERE username = ? OR email = ?
        """, (credentials.username, credentials.username))
        row = await cur.fetchone()

        if not row or not verify_password(credentials.password, row["hashed_password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

    token = create_access_token({"sub": row["id"], "username": row["username"]})
    user_out = UserOut(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        display_name=row["display_name"],
        created_at=row["created_at"],
        status=row["status"]
    )

    await audit_logger.log_event(
        event_type="USER_LOGGED_IN",
        action="auth.login",
        user_id=row["id"],
        details={"username": row["username"]}
    )

    return Token(access_token=token, token_type="bearer", user=user_out)

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_optional_user)):
    return UserOut(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        display_name=current_user.get("display_name", "Tony Stark"),
        created_at=current_user.get("created_at", "2026-09-01 00:00:00"),
        status=current_user.get("status", "active")
    )
