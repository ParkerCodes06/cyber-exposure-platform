import platform
import socket
import requests
import psutil
from datetime import datetime

BACKEND_URL = "https://cyber-exposure-platform.onrender.com/ingest"
AGENT_VERSION = "2.0.0"
DEFAULT_API_KEY = "default-tenant-key"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def collect_basic_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system() + " " + platform.release(),
        "ip_address": get_local_ip()
    }


def collect_ports():
    try:
        ports = []
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr:
                ports.append(conn.laddr.port)
        return list(set(ports))
    except PermissionError:
        print("[!] Permission denied for port scanning - running without port data")
        return []
    except Exception as e:
        print(f"[!] Port collection error: {e}")
        return []


def build_payload(api_key=None):
    return {
        "hostname": socket.gethostname(),
        "os": platform.system() + " " + platform.release(),
        "ip_address": get_local_ip(),
        "open_ports": collect_ports(),
        "agent_id": socket.gethostname(),
        "timestamp": datetime.utcnow().isoformat(),
        "version": AGENT_VERSION,
        "api_key": api_key or DEFAULT_API_KEY
    }


def send(payload, api_key=None):
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        response = requests.post(BACKEND_URL, json=payload, headers=headers)
        print("Response:", response.json())
    except Exception as e:
        print("Error sending data:", e)


if __name__ == "__main__":
    import sys

    api_key = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API_KEY

    print("[*] Collecting system information...")
    data = build_payload(api_key)
    print(f"[*] Hostname: {data['hostname']}")
    print(f"[*] Agent ID: {data['agent_id']}")
    print(f"[*] OS: {data['os']}")
    print(f"[*] IP: {data['ip_address']}")
    print(f"[*] Open ports: {len(data['open_ports'])} found")
    print(f"[*] Version: {data['version']}")
    print(f"[*] Sending to {BACKEND_URL}...")
    send(data, api_key)
