import json
import os
from dataclasses import dataclass, asdict

from .app_paths import get_app_dir

_CFG_PATH = os.path.join(get_app_dir(), "rigalert_config.json")


@dataclass
class AppConfig:
    # Identity
    farm_name: str = ""

    # Miner web UI credentials (used when opening miner in browser)
    miner_web_user: str = "root"
    miner_web_password: str = "admin"

    # Network scan
    start_ip: str = "192.168.1.1"
    end_ip: str = "192.168.1.254"
    miner_port: int = 4028
    scan_interval_seconds: int = 60
    connection_timeout: float = 8.0
    max_scan_workers: int = 20
    quick_scan_timeout: float = 0.8
    full_scan_interval_minutes: int = 30
    dead_host_backoff_seconds: int = 300
    slow_response_seconds: float = 2.5
    auto_refresh_enabled: bool = True
    debug_scan_enabled: bool = False

    # Thresholds
    default_min_ths: float = 80.0
    offline_after_seconds: int = 180
    high_temp_c: float = 85.0
    warn_temp_c: float = 75.0
    min_fan_rpm: int = 2000
    max_hw_error_rate: float = 1.0

    # Alert schedule
    alert_interval: str = "daily"   # hourly | 12hour | daily
    alert_send_hour: int = 5        # for daily: hour of day in US Eastern Time (0-23)
    enable_email_alerts: bool = False
    enable_popup_alerts: bool = True

    # Alert types
    alert_offline_enabled: bool = True
    alert_low_hash_enabled: bool = True
    alert_temp_enabled: bool = True
    alert_fan_enabled: bool = False
    alert_hw_err_enabled: bool = True

    # Gmail (App Password — no OAuth needed)
    alert_to_email: str = ""
    gmail_user: str = ""
    gmail_app_password: str = ""

    # Saved miners (list of dicts: ip, port, name, min_ths)
    saved_miners: list = None

    # Telegram
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Auto-reboot
    auto_reboot_enabled: bool = False
    auto_reboot_cooldown_minutes: int = 10   # minimum minutes between reboots per miner

    # Economics
    electricity_cost_kwh: float = 0.07   # USD per kWh

    # Crypto price alerts
    price_alerts_enabled: bool = False
    btc_alert_enabled: bool = True
    btc_alert_above: float = 0.0      # USD, 0 = disabled
    btc_alert_below: float = 0.0      # USD, 0 = disabled
    btc_alert_pct_move: float = 0.0   # 24h %, 0 = disabled
    altcoin_alerts: list = None        # [{id, symbol, above, below, pct_move}]

    def __post_init__(self):
        if self.saved_miners is None:
            self.saved_miners = []
        if self.altcoin_alerts is None:
            self.altcoin_alerts = []

    def save(self, path: str = _CFG_PATH):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str = _CFG_PATH) -> "AppConfig":
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                obj = cls()
                for k, v in data.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
                return obj
            except Exception:
                pass
        return cls()
