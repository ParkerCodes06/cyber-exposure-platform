import platform
import socket
import requests
import psutil

BACKEND_URL = "http://127.0.0.1:8000/ingest"


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


def build_payload():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system() + " " + platform.release(),
        "ip_address": get_local_ip(),
        "open_ports": collect_ports()
    }


def send(payload):
    try:
        response = requests.post(BACKEND_URL, json=payload)
        print("Response:", response.json())
    except Exception as e:
        print("Error sending data:", e)


if __name__ == "__main__":
    print("[*] Collecting system information...")
    data = build_payload()
    print(f"[*] Hostname: {data['hostname']}")
    print(f"[*] OS: {data['os']}")
    print(f"[*] IP: {data['ip_address']}")
    print(f"[*] Open ports: {len(data['open_ports'])} found")
    print(f"[*] Sending to {BACKEND_URL}...")
    send(data)
