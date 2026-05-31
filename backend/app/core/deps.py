from fastapi import Header, Request
from backend.app.core.auth import decode_token
from backend.app.utils.logger import get_logger

logger = get_logger("deps")

DEFAULT_USER = {
    "user_id": 0,
    "email": "guest",
    "tenant_id": "default",
    "role": "viewer"
}


def get_current_user(request: Request, authorization: str = Header(None)):
    token = None

    # Try HttpOnly cookie first
    token = request.cookies.get("access_token")

    # Fallback to Authorization header
    if not token and authorization:
        try:
            parts = authorization.split(" ")
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
        except Exception:
            pass

    if not token:
        return DEFAULT_USER

    payload = decode_token(token)
    if not payload:
        return DEFAULT_USER

    if payload.get("type") and payload["type"] != "access":
        return DEFAULT_USER

    return {
        "user_id": payload.get("user_id", 0),
        "email": payload.get("email", "guest"),
        "tenant_id": payload.get("tenant_id", "default"),
        "role": payload.get("role", "viewer")
    }
