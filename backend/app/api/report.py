from fastapi import APIRouter
from backend.app.utils.logger import get_logger

logger = get_logger("api.report")
router = APIRouter()


@router.get("/report/health")
def report_health():
    return {"status": "report service healthy"}
