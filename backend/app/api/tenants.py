import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.db.database import get_connection
from backend.app.utils.logger import get_logger

logger = get_logger("api.tenants")
router = APIRouter()


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    plan_type: str = Field(default="starter")


@router.post("/tenants")
def create_tenant(body: TenantCreate):
    try:
        api_key = f"cl_{secrets.token_hex(24)}"

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tenants (name, api_key, plan_type)
            VALUES (?, ?, ?)
        """, (body.name, api_key, body.plan_type))

        conn.commit()
        tenant_id = cursor.lastrowid
        conn.close()

        logger.info(f"Tenant created: {body.name} (id={tenant_id})")
        return {
            "id": tenant_id,
            "name": body.name,
            "api_key": api_key,
            "plan_type": body.plan_type,
            "message": "Save this API key — it cannot be retrieved later"
        }
    except Exception as e:
        logger.error(f"Tenant creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tenants")
def list_tenants():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, plan_type, created_at FROM tenants")
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "plan_type": row["plan_type"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Tenant list failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
