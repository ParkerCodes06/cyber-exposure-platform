from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.app.core.deps import get_current_user
from backend.app.core.alert_engine import get_alerts, acknowledge_alert
from backend.app.utils.logger import get_logger

logger = get_logger("api.alerts")
router = APIRouter()


@router.get("/alerts")
def list_alerts(user: dict = Depends(get_current_user)):
    try:
        tenant_id = user["tenant_id"]
        alerts = get_alerts(tenant_id)
        return alerts
    except Exception as e:
        logger.error(f"Alert list failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class AlertAck(BaseModel):
    alert_id: int


@router.post("/alerts/acknowledge")
def ack_alert(body: AlertAck, user: dict = Depends(get_current_user)):
    try:
        tenant_id = user["tenant_id"]
        success = acknowledge_alert(body.alert_id, tenant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert acknowledged"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert ack failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
