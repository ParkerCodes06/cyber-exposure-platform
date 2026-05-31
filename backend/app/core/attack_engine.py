from backend.app.utils.logger import get_logger

logger = get_logger("attack_engine")


def build_attack_path(os_value, open_ports, vulnerabilities):
    path = []

    os_value = (os_value or "").lower()

    # STEP 1: Entry point detection
    if 3389 in open_ports:
        path.append({
            "stage": "Initial Access",
            "technique": "RDP Exposure",
            "description": "Attacker can brute-force or exploit RDP service"
        })

    if 22 in open_ports:
        path.append({
            "stage": "Initial Access",
            "technique": "SSH Exposure",
            "description": "SSH service exposed to network"
        })

    # STEP 2: Exploitation phase
    for v in vulnerabilities:
        if "apache" in v["software"].lower():
            path.append({
                "stage": "Execution",
                "technique": "Remote Code Execution",
                "description": f"Exploit {v['cve_id']} leads to code execution"
            })

        if "openssl" in v["software"].lower():
            path.append({
                "stage": "Man-in-the-Middle",
                "technique": "TLS Interception",
                "description": "Allows traffic interception and credential theft"
            })

    # STEP 3: Privilege escalation (OS-based assumption)
    if "windows" in os_value:
        path.append({
            "stage": "Privilege Escalation",
            "technique": "Windows Local Privilege Escalation",
            "description": "Attacker may escalate privileges after initial access"
        })

    # STEP 4: Lateral movement (heuristic)
    if 445 in open_ports:
        path.append({
            "stage": "Lateral Movement",
            "technique": "SMB Propagation",
            "description": "Possible spread across internal network via SMB"
        })

    logger.info(f"Attack path built: {len(path)} stages for {os_value}")
    return path
