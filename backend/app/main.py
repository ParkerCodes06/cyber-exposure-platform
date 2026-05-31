from fastapi import FastAPI
from backend.app.db.database import init_db
from backend.app.api import assets, scan, report
from backend.app.utils.logger import get_logger

logger = get_logger("main")

app = FastAPI(
    title="Cyber Exposure Platform",
    version="0.2"
)

app.include_router(assets.router)
app.include_router(scan.router)
app.include_router(report.router)


@app.on_event("startup")
def startup():
    init_db()
    logger.info("Application started")


@app.get("/")
def root():
    return {
        "message": "Cyber Exposure Platform Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
