from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from backend.app.core.auth import hash_password, verify_password, create_access_token
from backend.app.core.deps import get_current_user
from backend.app.db.database import get_connection
from backend.app.utils.logger import get_logger

logger = get_logger("api.auth")
router = APIRouter()


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="viewer")


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/register")
def register(body: RegisterRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (body.email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Email already registered")

        password_hash = hash_password(body.password)

        cursor.execute("""
            INSERT INTO users (email, password_hash, role, tenant_id)
            VALUES (?, ?, ?, ?)
        """, (body.email, password_hash, body.role, body.tenant_id))

        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        logger.info(f"User registered: {body.email} (role={body.role}, tenant={body.tenant_id})")
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
def login(body: LoginRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (body.email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({
            "user_id": user["id"],
            "email": user["email"],
            "tenant_id": user["tenant_id"],
            "role": user["role"]
        })

        logger.info(f"User logged in: {body.email}")
        return {
            "access_token": token,
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


@router.get("/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "tenant_id": user["tenant_id"],
        "role": user["role"]
    }
