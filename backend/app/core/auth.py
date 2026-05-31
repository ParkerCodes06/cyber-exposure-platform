import os
import re
import secrets
import time
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Header, HTTPException, Request
from backend.app.db.database import get_connection
from backend.app.utils.logger import get_logger

logger = get_logger("auth")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cyberlens-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_TENANT = "default"


# ------------------------
# PASSWORD POLICY
# ------------------------
def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain an uppercase letter")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Password must contain a lowercase letter")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Password must contain a number")


# ------------------------
# PASSWORD HASHING
# ------------------------
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


# ------------------------
# JWT TOKEN CREATION
# ------------------------
def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode["type"] = "access"
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    to_encode["type"] = "refresh"
    to_encode["jti"] = secrets.token_hex(16)
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ------------------------
# TOKEN VALIDATION
# ------------------------
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ------------------------
# BRUTE-FORCE PROTECTION
# ------------------------
_login_attempts = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_BLOCK = 300


def check_rate_limit(ip: str):
    now = time.time()
    if ip in _login_attempts:
        attempts, blocked_until = _login_attempts[ip]
        if blocked_until and now < blocked_until:
            remaining = int(blocked_until - now)
            raise HTTPException(
                status_code=429,
                detail=f"Too many login attempts. Try again in {remaining}s"
            )
        if now - attempts[-1] > RATE_LIMIT_WINDOW:
            _login_attempts[ip] = ([], None)

    attempts, _ = _login_attempts.get(ip, ([], None))
    if len(attempts) >= RATE_LIMIT_MAX:
        _login_attempts[ip] = (attempts, now + RATE_LIMIT_BLOCK)
        logger.warning(f"Rate limit triggered for IP: {ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Blocked for {RATE_LIMIT_BLOCK}s"
        )


def record_login_attempt(ip: str):
    now = time.time()
    if ip in _login_attempts:
        attempts, _ = _login_attempts[ip]
        attempts.append(now)
        _login_attempts[ip] = (attempts, None)
    else:
        _login_attempts[ip] = ([now], None)


def clear_login_attempts(ip: str):
    _login_attempts.pop(ip, None)


# ------------------------
# AUDIT LOGGING
# ------------------------
def log_auth_event(event_type: str, email: str = None, ip: str = None,
                   user_agent: str = None, success: bool = True, detail: str = None):
    status = "SUCCESS" if success else "FAILURE"
    msg = f"[AUTH] {status} {event_type}"
    if email:
        msg += f" email={email}"
    if ip:
        msg += f" ip={ip}"
    if detail:
        msg += f" {detail}"
    if user_agent:
        msg += f" ua={user_agent[:80]}"

    if success:
        logger.info(msg)
    else:
        logger.warning(msg)


# ------------------------
# API KEY AUTH (for agents)
# ------------------------
def get_tenant_from_key(api_key: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tenants WHERE api_key = ?", (api_key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "api_key": row["api_key"],
                "plan_type": row["plan_type"]
            }
        return None
    except Exception as e:
        logger.error(f"Tenant lookup failed: {e}")
        return None


async def get_tenant(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    tenant = get_tenant_from_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return tenant


async def get_tenant_optional(x_api_key: str = Header(None)):
    if not x_api_key:
        tenant = get_tenant_from_key("default-tenant-key")
        return tenant if tenant else {"name": DEFAULT_TENANT, "plan_type": "starter"}

    tenant = get_tenant_from_key(x_api_key)
    return tenant if tenant else {"name": DEFAULT_TENANT, "plan_type": "starter"}
