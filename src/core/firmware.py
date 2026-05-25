"""Firmware type detection and VNish HTTP API helpers."""
import base64
import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

FIRMWARE_VNISH = "VNish"
FIRMWARE_BRAIINS = "Braiins OS"
FIRMWARE_STOCK = "Stock"
FIRMWARE_UNKNOWN = "Unknown"


def detect_type(firmware_str: str, model_str: str = "") -> str:
    fw = firmware_str.lower()
    mdl = model_str.lower()
    if "vnish" in fw:
        return FIRMWARE_VNISH
    if "braiins" in fw or "bosminer" in fw or "bos+" in fw:
        return FIRMWARE_BRAIINS
    if fw or "bmminer" in fw or "cgminer" in fw or "antminer" in mdl:
        return FIRMWARE_STOCK
    return FIRMWARE_UNKNOWN


def firmware_badge_color(fw_type: str) -> str:
    return {
        FIRMWARE_VNISH:   "#58a6ff",
        FIRMWARE_BRAIINS: "#3fb950",
        FIRMWARE_STOCK:   "#d29922",
        FIRMWARE_UNKNOWN: "#8b949e",
    }.get(fw_type, "#8b949e")


def _http_get(ip: str, path: str, user: str, password: str, timeout: float = 6.0) -> dict | None:
    url = f"http://{ip}{path}"
    creds = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = Request(url, headers={"Authorization": f"Basic {creds}", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except (URLError, OSError) as e:
        logger.debug(f"HTTP GET {url}: {e}")
        return None
    except Exception as e:
        logger.debug(f"HTTP GET {url} parse error: {e}")
        return None


def vnish_get_info(ip: str, user: str = "admin", password: str = "admin") -> dict:
    """Fetch VNish /api/v1/info. Returns dict with keys: fw_version, model, uptime, etc."""
    data = _http_get(ip, "/api/v1/info", user, password)
    if not data:
        return {}
    return {
        "fw_version": data.get("fw_version") or data.get("version", ""),
        "model":      data.get("miner_type") or data.get("model", ""),
        "uptime":     data.get("uptime", 0),
        "api_ver":    data.get("api_version", ""),
    }


def vnish_get_config(ip: str, user: str = "admin", password: str = "admin") -> dict | None:
    """Fetch full miner config from VNish (backup data)."""
    return _http_get(ip, "/api/v1/bitmain/get_bitmain_config", user, password)


def vnish_get_network(ip: str, user: str = "admin", password: str = "admin") -> dict:
    """Fetch VNish network settings."""
    data = _http_get(ip, "/api/v1/bitmain/network-info", user, password)
    return data or {}


def audit_entry(action: str, ip: str, detail: str) -> dict:
    """Build an audit log entry dict."""
    from datetime import datetime
    return {
        "ts":     datetime.now().isoformat(),
        "action": action,
        "ip":     ip,
        "detail": detail,
    }
