import json
from pathlib import Path
from functools import lru_cache
from backend.app.utils.logger import get_logger

logger = get_logger("cve_engine")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CVE_FILE = BASE_DIR / "data" / "cves.json"


@lru_cache(maxsize=128)
def load_cves():
    logger.info("Loading CVE database")
    with open(CVE_FILE, "r") as f:
        return json.load(f)


def check_vulnerabilities(os_value: str, open_ports=None):
    cves = load_cves()
    results = []

    os_value = (os_value or "").lower()

    for cve in cves:
        software = cve["software"].lower()

        if software in os_value:
            results.append({
                "cve_id": cve["cve_id"],
                "software": cve["software"],
                "description": cve["description"],
                "severity": cve["severity"]
            })

    logger.info(f"Found {len(results)} vulnerabilities for OS: {os_value}")
    return results
