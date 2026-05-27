"""Firmware type detection and VNish HTTP API helpers."""
import base64
import json
import logging
from urllib.error import HTTPError, URLError
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


def _http_request(
    ip: str,
    path: str,
    user: str = "",
    password: str = "",
    method: str = "GET",
    payload=None,
    token: str = "",
    timeout: float = 6.0,
) -> dict | bool | str | None:
    url = f"http://{ip}{path}"
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif user or password:
        creds = base64.b64encode(f"{user}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {creds}"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace").strip()
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
    except HTTPError as e:
        logger.debug(f"HTTP {method} {url}: {e.code} {e.reason}")
        return None
    except (URLError, OSError) as e:
        logger.debug(f"HTTP {method} {url}: {e}")
        return None
    except Exception as e:
        logger.debug(f"HTTP {method} {url} error: {e}")
        return None


def _http_get(ip: str, path: str, user: str, password: str, timeout: float = 6.0) -> dict | None:
    data = _http_request(ip, path, user, password, timeout=timeout)
    return data if isinstance(data, dict) else None


def braiins_login(ip: str, user: str, password: str, timeout: float = 6.0) -> str:
    """Return a Braiins OS REST API bearer token, or an empty string."""
    data = _http_request(
        ip,
        "/api/v1/auth/login",
        method="POST",
        payload={"username": user, "password": password},
        timeout=timeout,
    )
    if isinstance(data, dict):
        for key in ("token", "access_token", "jwt", "bearer"):
            token = data.get(key)
            if token:
                return str(token)
    if isinstance(data, str) and data:
        return data
    return ""


def braiins_request(ip: str, path: str, user: str, password: str, method: str = "GET",
                    payload=None, timeout: float = 6.0):
    """Call the Braiins OS REST API using token auth, falling back to basic auth."""
    token = braiins_login(ip, user, password, timeout=timeout)
    if token:
        return _http_request(ip, path, method=method, payload=payload, token=token, timeout=timeout)
    return _http_request(ip, path, user, password, method=method, payload=payload, timeout=timeout)


def braiins_set_locate(ip: str, enabled: bool, user: str, password: str) -> tuple[bool, str]:
    result = braiins_request(ip, "/api/v1/actions/locate", user, password, method="PUT", payload=enabled)
    if result is not None:
        return True, "Locate LED enabled" if enabled else "Locate LED disabled"
    return False, "Braiins locate API request failed"


def braiins_set_password(ip: str, new_password: str, user: str, password: str) -> tuple[bool, str]:
    result = braiins_request(
        ip,
        "/api/v1/auth/password",
        user,
        password,
        method="PUT",
        payload={"password": new_password},
    )
    if result is not None:
        return True, "Braiins OS password changed"
    return False, "Braiins password API request failed"


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
