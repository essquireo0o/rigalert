"""Bitcoin and altcoin price monitor — polls CoinGecko, emits alerts on threshold crosses."""
import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

_COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids={ids}&vs_currencies=usd&include_24hr_change=true"
)

# Poll every 5 minutes — well within CoinGecko free tier (15 calls/min)
_POLL_INTERVAL_MS = 300_000


def _fetch_prices(coin_ids: list[str]) -> dict:
    """Returns {coin_id: {usd: float, usd_24h_change: float}} or {}."""
    if not coin_ids:
        return {}
    ids_param = ",".join(coin_ids)
    url = _COINGECKO_URL.format(ids=ids_param)
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "RigAlert/2.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except (URLError, OSError) as e:
        logger.debug(f"CoinGecko request failed: {e}")
        return {}
    except Exception as e:
        logger.debug(f"CoinGecko parse error: {e}")
        return {}


class PriceMonitor(QThread):
    """Background thread that polls CoinGecko and emits signals for price updates and alerts."""

    price_updated  = pyqtSignal(str, float, float)  # coin_id, usd_price, 24h_change_pct
    alert_triggered = pyqtSignal(str, str)           # coin_id, alert_message

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._running = False
        # Track last-known alert states to avoid repeated alerts on the same condition
        # Key: (coin_id, "above"/"below"/"pct"), Value: bool (alert active)
        self._alert_state: dict = {}

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            self._poll()
            for _ in range(_POLL_INTERVAL_MS // 100):
                if not self._running:
                    break
                self.msleep(100)

    def poll_now(self):
        """Force an immediate poll (called from UI)."""
        self._poll()

    def _poll(self):
        cfg = self.config

        # Always fetch BTC for the live price chip in the header
        always_fetch = ["bitcoin"]
        alert_ids = self._get_coin_ids(cfg) if cfg.price_alerts_enabled else []
        coin_ids = list(dict.fromkeys(always_fetch + alert_ids))  # deduplicate, preserve order

        prices = _fetch_prices(coin_ids)
        if not prices:
            return

        for coin_id in coin_ids:
            data = prices.get(coin_id, {})
            price = float(data.get("usd", 0) or 0)
            change_24h = float(data.get("usd_24h_change", 0) or 0)

            if price <= 0:
                continue

            self.price_updated.emit(coin_id, price, change_24h)

            if cfg.price_alerts_enabled and coin_id in alert_ids:
                self._check_thresholds(cfg, coin_id, price, change_24h)

    def _get_coin_ids(self, cfg) -> list[str]:
        ids = []
        if cfg.btc_alert_enabled:
            ids.append("bitcoin")
        for alt in (cfg.altcoin_alerts or []):
            cid = alt.get("id", "").strip()
            if cid and (alt.get("above", 0) or alt.get("below", 0) or alt.get("pct_move", 0)):
                ids.append(cid)
        return ids

    def _check_thresholds(self, cfg, coin_id: str, price: float, change_24h: float):
        if coin_id == "bitcoin":
            above = float(cfg.btc_alert_above or 0)
            below = float(cfg.btc_alert_below or 0)
            pct   = float(cfg.btc_alert_pct_move or 0)
            label = "BTC"
        else:
            alt = next((a for a in (cfg.altcoin_alerts or []) if a.get("id") == coin_id), {})
            above = float(alt.get("above", 0) or 0)
            below = float(alt.get("below", 0) or 0)
            pct   = float(alt.get("pct_move", 0) or 0)
            label = alt.get("symbol", coin_id).upper()

        self._check_above(coin_id, label, price, above)
        self._check_below(coin_id, label, price, below)
        self._check_pct(coin_id, label, change_24h, pct)

    def _check_above(self, coin_id, label, price, threshold):
        if threshold <= 0:
            return
        key = (coin_id, "above")
        triggered = price >= threshold
        was_triggered = self._alert_state.get(key, False)
        if triggered and not was_triggered:
            msg = f"{label} price alert: ${price:,.0f} is above threshold ${threshold:,.0f}"
            self.alert_triggered.emit(coin_id, msg)
            logger.info(msg)
        self._alert_state[key] = triggered

    def _check_below(self, coin_id, label, price, threshold):
        if threshold <= 0:
            return
        key = (coin_id, "below")
        triggered = price <= threshold
        was_triggered = self._alert_state.get(key, False)
        if triggered and not was_triggered:
            msg = f"{label} price alert: ${price:,.0f} is below threshold ${threshold:,.0f}"
            self.alert_triggered.emit(coin_id, msg)
            logger.info(msg)
        self._alert_state[key] = triggered

    def _check_pct(self, coin_id, label, change_24h, threshold_pct):
        if threshold_pct <= 0:
            return
        key = (coin_id, "pct")
        triggered = abs(change_24h) >= threshold_pct
        was_triggered = self._alert_state.get(key, False)
        if triggered and not was_triggered:
            direction = "up" if change_24h > 0 else "down"
            msg = f"{label} moved {change_24h:+.1f}% in 24h (threshold: ±{threshold_pct:.1f}%)"
            self.alert_triggered.emit(coin_id, msg)
            logger.info(msg)
        self._alert_state[key] = triggered
