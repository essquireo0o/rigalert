import logging
from datetime import datetime
from typing import Callable, List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from .email_builder import build_summary_email
from .gmail_oauth import send_email
from ..core.config import AppConfig
from ..core.miner import MinerData

logger = logging.getLogger(__name__)


class AlertScheduler(QThread):
    alert_sent = pyqtSignal(str)       # message
    alert_failed = pyqtSignal(str)     # error message
    popup_requested = pyqtSignal(str)  # summary text for popup

    def __init__(self, config: AppConfig, miner_getter: Callable[[], List[MinerData]], parent=None):
        super().__init__(parent)
        self.config = config
        self.get_miners = miner_getter
        self._running = False
        self._last_sent_hour: Optional[int] = None
        self._last_sent_half: Optional[int] = None  # for 12-hour

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            self._check_and_send()
            # Check every 30 seconds
            for _ in range(300):
                if not self._running:
                    break
                self.msleep(100)

    def _check_and_send(self):
        cfg = self.config
        now = datetime.now()
        h = now.hour
        m = now.minute

        should_send = False
        interval_label = ""

        if cfg.alert_interval == "hourly":
            # Send at the top of each hour (minute 0)
            if m == 0 and self._last_sent_hour != h:
                should_send = True
                interval_label = "Hourly"
                self._last_sent_hour = h

        elif cfg.alert_interval == "12hour":
            # Send at 00:00 and 12:00
            half = 0 if h < 12 else 1
            if h in (0, 12) and m == 0 and self._last_sent_half != (now.day, half):
                should_send = True
                interval_label = "12-Hour"
                self._last_sent_half = (now.day, half)

        elif cfg.alert_interval == "daily":
            # Send once per day at configured hour
            if h == cfg.alert_send_hour and m == 0 and self._last_sent_hour != now.day:
                should_send = True
                interval_label = "Daily"
                self._last_sent_hour = now.day

        if should_send:
            self._send_alert(interval_label)

    def _send_alert(self, interval_label: str):
        miners = self.get_miners()
        if not miners:
            return

        cfg = self.config
        subject, html = build_summary_email(miners, interval_label, farm_name=cfg.farm_name)

        if cfg.enable_popup_alerts:
            problems = [m for m in miners if m.status in ("offline", "warning") or m.alerts]
            total = len(miners)
            online = sum(1 for m in miners if m.status == "online")
            popup_text = f"{interval_label} Report\n{online}/{total} miners online"
            if problems:
                popup_text += f"\n{len(problems)} issues detected"
            self.popup_requested.emit(popup_text)

        if cfg.enable_email_alerts and cfg.alert_to_email and cfg.gmail_user and cfg.gmail_app_password:
            success, err = send_email(
                gmail_user=cfg.gmail_user,
                app_password=cfg.gmail_app_password,
                to=cfg.alert_to_email,
                subject=subject,
                html_body=html,
            )
            if success:
                self.alert_sent.emit(f"Alert email sent: {subject}")
            else:
                self.alert_failed.emit(f"Email failed: {err}")

        if cfg.telegram_enabled and cfg.telegram_bot_token and cfg.telegram_chat_id:
            from .telegram_notify import send_telegram
            problems = [m for m in miners if m.status in ("offline", "warning") or m.alerts]
            online = sum(1 for m in miners if m.status == "online")
            total = len(miners)
            lines = [f"<b>RigAlert™ {interval_label} Report</b>",
                     f"{online}/{total} miners online"]
            if problems:
                lines.append(f"⚠ {len(problems)} issue(s):")
                for m in problems[:5]:
                    status_emoji = "🔴" if m.status == "offline" else "🟡"
                    lines.append(f"  {status_emoji} {m.display_name} ({m.ip}) — {m.status}")
                if len(problems) > 5:
                    lines.append(f"  … and {len(problems) - 5} more")
            tg_ok, tg_err = send_telegram(cfg.telegram_bot_token, cfg.telegram_chat_id,
                                          "\n".join(lines))
            if not tg_ok:
                self.alert_failed.emit(f"Telegram failed: {tg_err}")

    def send_now(self, interval_label: str = "Manual"):
        self._send_alert(interval_label)
