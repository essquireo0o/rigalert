import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStackedWidget, QStatusBar, QSystemTrayIcon, QVBoxLayout, QWidget,
    QMenu, QApplication,
)

from ..core.config import AppConfig
from ..core.database import Database
from ..core.miner import MinerData
from ..core.scanner import MinerScanner
from ..alerts.scheduler import AlertScheduler
from ..alerts.price_monitor import PriceMonitor
from .theme import DARK_QSS, STATUS_COLORS, BITCOIN_ORANGE


class NavButton(QPushButton):
    def __init__(self, icon_text: str, tooltip: str, parent=None):
        super().__init__(icon_text, parent)
        self.setObjectName("navBtn")
        self.setToolTip(tooltip)
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class StatusChip(QLabel):
    def __init__(self, obj_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(obj_name)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = AppConfig.load()
        self.db = Database()

        self._miners: Dict[str, MinerData] = {}

        self._setup_ui()
        self._setup_scanner()
        self._setup_alert_scheduler()
        self._setup_price_monitor()
        self._setup_tray()
        self._setup_refresh_timer()

        self._update_title()
        self.resize(1300, 820)
        self._nav_click(0)

    # ── UI Setup ───────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setStyleSheet(DARK_QSS)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self._sidebar = self._make_sidebar()
        root.addWidget(self._sidebar)

        # Right column
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self._status_bar_widget = self._make_status_bar()
        right.addWidget(self._status_bar_widget)

        self._stack = QStackedWidget()
        self._stack.setObjectName("page")
        right.addWidget(self._stack, 1)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root.addWidget(right_widget, 1)

        # Pages (lazy import to avoid circular deps)
        self._init_pages()

        # App status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_msg = QLabel("Ready")
        sb.addWidget(self._status_msg)
        self._last_scan_label = QLabel("")
        sb.addPermanentWidget(self._last_scan_label)

    def _make_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo — use generated PNG if available, fall back to text
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("padding:10px 0;background:transparent;")
        base = getattr(sys, "_MEIPASS", os.path.join(os.path.dirname(__file__), "..", "..", ""))
        logo_path = os.path.join(base, "rigalert_preview.png")
        pix = QPixmap(logo_path)
        if not pix.isNull():
            logo.setPixmap(pix.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("⛏")
            logo.setStyleSheet(f"font-size:26px;color:{BITCOIN_ORANGE};padding:12px 0;")
        layout.addWidget(logo)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background:#21262d;margin:4px 8px;")
        layout.addWidget(sep)

        self._nav_btns = []
        nav_items = [
            ("⊞", "Dashboard"),
            ("◉", "Miners"),
            ("⚑", "Alerts"),
            ("⚒", "Firmware"),
            ("⚙", "Settings"),
            ("≡", "Logs"),
        ]
        for txt, tip in nav_items:
            btn = NavButton(txt, tip)
            btn.clicked.connect(lambda checked, i=len(self._nav_btns): self._nav_click(i))
            layout.addWidget(btn)
            self._nav_btns.append(btn)

        layout.addStretch()

        # Version label
        ver = QLabel("v2.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("font-size:10px;color:#484f58;padding:4px;")
        layout.addWidget(ver)

        return sidebar

    def _make_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(48)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        self._title_label = QLabel("RigAlert™ by ING Mining")
        self._title_label.setStyleSheet(f"font-size:15px;font-weight:700;color:{BITCOIN_ORANGE};margin-right:16px;background:transparent;")
        layout.addWidget(self._title_label)

        layout.addStretch()

        self._chip_hash = StatusChip("statHash")
        self._chip_hash.setText("0.0 TH/s")
        self._chip_online = StatusChip("statOnline")
        self._chip_online.setText("0 Online")
        self._chip_offline = StatusChip("statOffline")
        self._chip_offline.setText("0 Offline")
        self._chip_warn = StatusChip("statWarning")
        self._chip_warn.setText("0 Warnings")

        for chip in [self._chip_hash, self._chip_online, self._chip_offline, self._chip_warn]:
            chip.setObjectName(chip.objectName())
            layout.addWidget(chip)

        return bar

    def _init_pages(self):
        from .dashboard_page import DashboardPage
        from .miners_page import MinersPage
        from .alerts_page import AlertsPage
        from .firmware_page import FirmwarePage
        from .settings_page import SettingsPage
        from .logs_page import LogsPage

        self._dashboard_page = DashboardPage(self)
        self._miners_page = MinersPage(self)
        self._alerts_page = AlertsPage(self)
        self._firmware_page = FirmwarePage(self)
        self._settings_page = SettingsPage(self)
        self._logs_page = LogsPage(self)

        for page in [self._dashboard_page, self._miners_page, self._alerts_page,
                     self._firmware_page, self._settings_page, self._logs_page]:
            self._stack.addWidget(page)

    # ── Navigation ─────────────────────────────────────────────────────────

    def _nav_click(self, index: int):
        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == index)
        self._stack.setCurrentIndex(index)

    # ── Scanner Setup ──────────────────────────────────────────────────────

    def _setup_scanner(self):
        self._scanner = MinerScanner(self.config, self.db, self)
        saved = self.db.get_miners()
        self._scanner.set_known_miners(saved)
        self._scanner.miner_updated.connect(self._on_miner_updated)
        self._scanner.miner_offline.connect(self._on_miner_offline)
        self._scanner.scan_started.connect(self._on_scan_started)
        self._scanner.scan_finished.connect(self._on_scan_finished)
        self._scanner.log_event.connect(self._on_log_event)
        self._scanner.start()

    def _setup_alert_scheduler(self):
        self._scheduler = AlertScheduler(self.config, self._scanner.all_miners, self)
        self._scheduler.alert_sent.connect(lambda msg: self._status_msg.setText(msg))
        self._scheduler.alert_failed.connect(lambda msg: self._status_msg.setText(f"⚠ {msg}"))
        self._scheduler.popup_requested.connect(self._show_popup)
        self._scheduler.start()

    def _setup_price_monitor(self):
        self._price_monitor = PriceMonitor(self.config, self)
        self._price_monitor.alert_triggered.connect(self._on_price_alert)
        self._price_monitor.start()

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("RigAlert™ by ING Mining — Miner Monitor")
        tray_menu = QMenu()
        tray_menu.setStyleSheet(DARK_QSS)
        tray_menu.addAction("Open RigAlert™ by ING Mining", self.show_normal)
        tray_menu.addSeparator()
        tray_menu.addAction("Quit", QApplication.quit)
        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._tray_activated)
        self._tray.show()

    def _setup_refresh_timer(self):
        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._refresh_ui)
        self._ui_timer.start(5000)

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    # ── Slots ──────────────────────────────────────────────────────────────

    @pyqtSlot(object)
    def _on_miner_updated(self, miner: MinerData):
        self._miners[miner.ip] = miner
        self._dashboard_page.update_miner(miner)
        self._miners_page.update_miner(miner)
        self._firmware_page.update_miner(miner)
        self._update_chips()

    @pyqtSlot(str)
    def _on_miner_offline(self, ip: str):
        if ip in self._miners:
            self._miners[ip].status = "offline"
        self._update_chips()

    @pyqtSlot()
    def _on_scan_started(self):
        self._status_msg.setText("Scanning network...")

    @pyqtSlot(int)
    def _on_scan_finished(self, count: int):
        self._status_msg.setText(f"Scan complete — {count} miners found")
        self._last_scan_label.setText(f"Last scan: {datetime.now().strftime('%H:%M:%S')}")

    @pyqtSlot(str, str, str)
    def _on_log_event(self, ip: str, level: str, message: str):
        self._logs_page.add_event(ip, level, message)

    def _refresh_ui(self):
        self._update_chips()

    def _update_chips(self):
        miners = list(self._miners.values())
        total_ths = sum(m.best_hashrate() for m in miners if m.status != "offline")
        online = sum(1 for m in miners if m.status == "online")
        warning = sum(1 for m in miners if m.status == "warning")
        offline = sum(1 for m in miners if m.status == "offline")

        if total_ths >= 1000:
            self._chip_hash.setText(f"{total_ths/1000:.2f} PH/s")
        else:
            self._chip_hash.setText(f"{total_ths:.1f} TH/s")
        self._chip_online.setText(f"{online} Online")
        self._chip_offline.setText(f"{offline} Offline")
        self._chip_warn.setText(f"{warning} Warnings")

    @pyqtSlot(str)
    def _show_popup(self, text: str):
        if self._tray.isVisible():
            self._tray.showMessage("RigAlert™ by ING Mining Alert", text,
                                   QSystemTrayIcon.MessageIcon.Warning, 8000)

    # ── Public API used by pages ───────────────────────────────────────────

    def get_config(self) -> AppConfig:
        return self.config

    def get_db(self) -> Database:
        return self.db

    def get_scanner(self) -> MinerScanner:
        return self._scanner

    def get_scheduler(self) -> AlertScheduler:
        return self._scheduler

    def get_miners(self) -> Dict[str, MinerData]:
        return self._miners

    def _update_title(self):
        farm = self.config.farm_name
        if farm:
            self.setWindowTitle(f"RigAlert™ by ING Mining — {farm}")
            self._title_label.setText(f"RigAlert™ by ING Mining  —  {farm}")
        else:
            self.setWindowTitle("RigAlert™ by ING Mining — Bitcoin Miner Monitor")
            self._title_label.setText("RigAlert™ by ING Mining")

    def reload_config(self):
        self.config = AppConfig.load()
        self._scanner.config = self.config
        self._scheduler.config = self.config
        self._price_monitor.config = self.config
        self._update_title()

    def add_miner_to_watch(self, ip: str, port: int, name: str, min_ths: float):
        self.db.upsert_miner(ip, port, name, min_ths)
        self._scanner.add_miner(ip, port, name, min_ths)
        self.config.saved_miners = self.db.get_miners()
        self.config.save()

    def remove_miner_from_watch(self, ip: str):
        self.db.delete_miner(ip)
        self._scanner.remove_miner(ip)
        self._miners.pop(ip, None)
        self._dashboard_page.remove_miner(ip)
        self._miners_page.remove_miner(ip)
        self._firmware_page.remove_miner(ip)

    @pyqtSlot(str, str)
    def _on_price_alert(self, coin_id: str, message: str):
        self.db.log_event("price", "WARN", message)
        self._logs_page.add_event("price", "WARN", message)
        self._show_popup(f"Price Alert\n{message}")
        self._status_msg.setText(f"Price alert: {message}")

    def closeEvent(self, event):
        self.hide()
        event.ignore()
