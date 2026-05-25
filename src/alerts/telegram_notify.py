"""Telegram notification delivery for RigAlert™."""
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram(token: str, chat_id: str, text: str) -> tuple:
    """Send a Telegram message. Returns (success: bool, error: str)."""
    if not token or not chat_id:
        return False, "Telegram not configured (missing token or chat ID)"
    url = _API_BASE.format(token=token.strip())
    payload = json.dumps({
        "chat_id": chat_id.strip(),
        "text": text,
        "parse_mode": "HTML",
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("ok"):
                return True, ""
            return False, data.get("description", "Unknown error")
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)
        return False, str(e)


def test_telegram(token: str, chat_id: str) -> tuple:
    """Send a test message and return (success, message)."""
    ok, err = send_telegram(token, chat_id,
                            "✅ <b>RigAlert™ by ING Mining</b>\nTelegram notifications are working!")
    if ok:
        return True, "Test message sent — check your Telegram"
    return False, f"Failed: {err}"
