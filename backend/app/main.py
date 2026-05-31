from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.db.database import init_db, get_connection
from backend.app.core.auth import hash_password
from backend.app.api import assets, scan, report, dashboard, fleet, tenants, alerts, auth
from backend.app.utils.logger import get_logger
import os

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
app.include_router(auth.router)


def seed_admin():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@cyberlens.com",))
        if not cursor.fetchone():
            pwd_hash = hash_password("Admin123!")
            cursor.execute(
                "INSERT INTO users (email, password_hash, role, tenant_id) VALUES (?, ?, ?, ?)",
                ("admin@cyberlens.com", pwd_hash, "admin", "default")
            )
            conn.commit()
            logger.info("Admin user seeded: admin@cyberlens.com")
        conn.close()
    except Exception as e:
        logger.error(f"Admin seed failed: {e}")


@app.on_event("startup")
def startup():
    init_db()
    seed_admin()
    logger.info("Application started")


FRONTEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
logger.info(f"Frontend dir: {FRONTEND_DIR} (exists: {os.path.isdir(FRONTEND_DIR)})")

ASSETS_DIR = os.path.join(FRONTEND_DIR, "assets")
if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="static")


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


if os.path.isdir(FRONTEND_DIR):

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return {"error": "not found"}
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
