from fastapi import Header, HTTPException
from backend.app.core.auth import decode_token
from backend.app.utils.logger import get_logger

logger = get_logger("deps")


def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization format")

        token = parts[1]
        payload = decode_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "tenant_id": payload.get("tenant_id"),
            "role": payload.get("role", "viewer")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")
