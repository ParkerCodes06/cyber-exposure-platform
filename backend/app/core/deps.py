from fastapi import Header, HTTPException, Request
from backend.app.core.auth import decode_token
from backend.app.utils.logger import get_logger

logger = get_logger("deps")


def get_current_user(request: Request, authorization: str = Header(None)):
    token = None

    # Try HttpOnly cookie first
    token = request.cookies.get("access_token")

    # Fallback to Authorization header (for API clients / backward compat)
    if not token and authorization:
        try:
            parts = authorization.split(" ")
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
        except Exception:
            pass

    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role", "viewer")
    }
