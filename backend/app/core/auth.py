import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Header, HTTPException
from backend.app.db.database import get_connection
from backend.app.utils.logger import get_logger

logger = get_logger("auth")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cyberlens-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_TENANT = "default"


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
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
