from fastapi import Header, HTTPException
from backend.app.db.database import get_connection
from backend.app.utils.logger import get_logger

logger = get_logger("auth")

DEFAULT_TENANT = "default"


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
        tenant = get_tenant_from_key("default-tenant-key")
        if tenant:
            return tenant
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

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
