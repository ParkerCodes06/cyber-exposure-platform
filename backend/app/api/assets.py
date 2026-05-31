import json
from fastapi import APIRouter, HTTPException, Header
from backend.app.db.database import get_connection
from backend.app.models.asset_model import AssetIngest
from backend.app.utils.logger import get_logger

logger = get_logger("api.assets")
router = APIRouter()

API_KEY = "secret-key-change-me"


def verify_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/ingest")
def ingest_asset(asset: AssetIngest):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO assets (hostname, os, ip_address, open_ports)
            VALUES (?, ?, ?, ?)
        """, (
            asset.hostname,
            asset.os,
            asset.ip_address,
            json.dumps(asset.open_ports)
        ))

        conn.commit()
        conn.close()

        logger.info(f"Asset ingested: {asset.hostname}")
        return {
            "message": "Asset stored in database",
            "hostname": asset.hostname
        }
    except Exception as e:
        logger.error(f"Asset ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/assets")
def get_assets():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        rows = cursor.fetchall()

        conn.close()

        return [
            {
                "id": row["id"],
                "hostname": row["hostname"],
                "os": row["os"],
                "ip_address": row["ip_address"],
                "open_ports": json.loads(row["open_ports"] or "[]"),
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Asset retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
