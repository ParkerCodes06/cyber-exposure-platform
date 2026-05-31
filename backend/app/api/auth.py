from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel, Field
from backend.app.core.auth import (
    hash_password, verify_password, validate_password,
    create_access_token, create_refresh_token, decode_token,
    check_rate_limit, record_login_attempt, clear_login_attempts,
    log_auth_event
)
from backend.app.core.deps import get_current_user
from backend.app.db.database import get_connection
from backend.app.utils.logger import get_logger

logger = get_logger("api.auth")
router = APIRouter()

COOKIE_SAMESITE = "lax"
COOKIE_SECURE = True
ACCESS_MAX_AGE = 15 * 60
REFRESH_MAX_AGE = 7 * 24 * 60 * 60


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="viewer")


class LoginRequest(BaseModel):
    email: str
    password: str


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        "access_token", access_token,
        httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
        max_age=ACCESS_MAX_AGE, path="/"
    )
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
        max_age=REFRESH_MAX_AGE, path="/auth/refresh"
    )


@router.post("/auth/register")
def register(body: RegisterRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    try:
        validate_password(body.password)
    except HTTPException:
        raise

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (body.email,))
        if cursor.fetchone():
            conn.close()
            log_auth_event("REGISTER", body.email, ip, ua, False, "duplicate email")
            raise HTTPException(status_code=409, detail="Email already registered")

        password_hash = hash_password(body.password)

        cursor.execute("""
            INSERT INTO users (email, password_hash, role, tenant_id)
            VALUES (?, ?, ?, ?)
        """, (body.email, password_hash, body.role, body.tenant_id))

        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        log_auth_event("REGISTER", body.email, ip, ua, True, f"role={body.role} tenant={body.tenant_id}")
        return {
            "message": "User created",
            "user_id": user_id,
            "email": body.email,
            "role": body.role,
            "tenant_id": body.tenant_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/auth/login")
def login(body: LoginRequest, response: Response, request: Request):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    check_rate_limit(ip)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (body.email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not verify_password(body.password, user["password_hash"]):
            record_login_attempt(ip)
            log_auth_event("LOGIN", body.email, ip, ua, False, "invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        clear_login_attempts(ip)

        token_data = {
            "user_id": user["id"],
            "email": user["email"],
            "tenant_id": user["tenant_id"],
            "role": user["role"]
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        _set_auth_cookies(response, access_token, refresh_token)

        log_auth_event("LOGIN", body.email, ip, ua, True)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "tenant_id": user["tenant_id"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/auth/refresh")
def refresh(request: Request, response: Response):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        log_auth_event("REFRESH", ip=ip, ua=ua, success=False, detail="invalid token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (payload["user_id"],))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    token_data = {
        "user_id": user["id"],
        "email": user["email"],
        "tenant_id": user["tenant_id"],
        "role": user["role"]
    }

    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    _set_auth_cookies(response, new_access, new_refresh)

    log_auth_event("REFRESH", user["email"], ip, ua, True)
    return {"message": "Tokens refreshed"}


@router.post("/auth/logout")
def logout(response: Response, request: Request):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    log_auth_event("LOGOUT", ip=ip, ua=ua, success=True)

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/auth/refresh")
    return {"message": "Logged out"}


@router.get("/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "tenant_id": user["tenant_id"],
        "role": user["role"]
    }
