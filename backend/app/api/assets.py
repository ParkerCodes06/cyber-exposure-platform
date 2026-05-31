import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from backend.app.db.database import get_connection
from backend.app.models.asset_model import AssetIngest
from backend.app.core.cve_engine import check_vulnerabilities
from backend.app.core.risk_engine import calculate_risk
from backend.app.core.auth import get_tenant, get_tenant_optional
from backend.app.utils.logger import get_logger

logger = get_logger("api.assets")
router = APIRouter()


@router.post("/ingest")
def ingest_asset(asset: AssetIngest, tenant: dict = Depends(get_tenant_optional)):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        tenant_id = tenant["name"]
        agent_id = asset.agent_id or asset.hostname
        now = datetime.utcnow().isoformat()

        cursor.execute(
            "SELECT id FROM assets WHERE hostname = ? AND tenant_id = ?",
            (asset.hostname, tenant_id)
        )
        existing = cursor.fetchone()

        vulnerabilities = check_vulnerabilities(os_value=asset.os)
        risk_report = calculate_risk(vulnerabilities, asset.open_ports)

        if existing:
            cursor.execute("""
                UPDATE assets
                SET os = ?, ip_address = ?, open_ports = ?, agent_id = ?, last_seen = ?
                WHERE hostname = ? AND tenant_id = ?
            """, (
                asset.os,
                asset.ip_address,
                json.dumps(asset.open_ports),
                agent_id,
                now,
                asset.hostname,
                tenant_id
            ))
            logger.info(f"Asset updated: {asset.hostname} (tenant={tenant_id})")
        else:
            cursor.execute("""
                INSERT INTO assets (hostname, os, ip_address, open_ports, agent_id, last_seen,
                    tenant_id, risk_score, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'LOW')
            """, (
                asset.hostname,
                asset.os,
                asset.ip_address,
                json.dumps(asset.open_ports),
                agent_id,
                now,
                tenant_id
            ))
            logger.info(f"Asset ingested: {asset.hostname} (tenant={tenant_id})")

        cursor.execute("""
            INSERT INTO scan_history (hostname, agent_id, timestamp, risk_score,
                vulnerability_count, risk_level, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            asset.hostname,
            agent_id,
            now,
            risk_report["total_risk_score"],
            len(vulnerabilities),
            risk_report["risk_level"],
            tenant_id
        ))

        conn.commit()
        conn.close()

        return {
            "message": "Asset stored" if not existing else "Asset updated",
            "hostname": asset.hostname,
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "risk_level": risk_report["risk_level"],
            "risk_score": risk_report["total_risk_score"]
        }
    except Exception as e:
        logger.error(f"Asset ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/assets")
def get_assets(tenant: dict = Depends(get_tenant)):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        tenant_id = tenant["name"]

        cursor.execute("SELECT * FROM assets WHERE tenant_id = ?", (tenant_id,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "hostname": row["hostname"],
                "os": row["os"],
                "ip_address": row["ip_address"],
                "open_ports": json.loads(row["open_ports"] or "[]"),
                "agent_id": row["agent_id"],
                "last_seen": row["last_seen"],
                "risk_score": row["risk_score"],
                "risk_level": row["risk_level"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Asset retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
