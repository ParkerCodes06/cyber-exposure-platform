from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.db.database import init_db
from backend.app.api import assets, scan, report, dashboard, fleet, tenants, alerts
from backend.app.utils.logger import get_logger

logger = get_logger("main")

app = FastAPI(
    title="Cyber Exposure Platform",
    version="0.2"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router)
app.include_router(scan.router)
app.include_router(report.router)
app.include_router(dashboard.router)
app.include_router(fleet.router)
app.include_router(tenants.router)
app.include_router(alerts.router)


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
