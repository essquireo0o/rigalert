from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSpinBox, QDoubleSpinBox, QVBoxLayout, QWidget, QMessageBox,
)

from .theme import BITCOIN_ORANGE


class SettingsPage(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#0d1117;}")
        root.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background:#0d1117;")
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # ── Farm Identity ──────────────────────────────────────────
        farm_box = QGroupBox("Farm Identity")
        ff = QFormLayout(farm_box)
        ff.setSpacing(10)
        self._farm_name = QLineEdit()
        self._farm_name.setPlaceholderText("e.g. Farm 1, Warehouse A, Texas Site...")
        self._farm_name.setFixedWidth(280)
        ff.addRow("Farm Name:", self._farm_name)

        self._web_user = QLineEdit()
        self._web_user.setPlaceholderText("root")
        self._web_user.setFixedWidth(160)
        ff.addRow("Miner Web Username:", self._web_user)

        self._web_password = QLineEdit()
        self._web_password.setPlaceholderText("root")
        self._web_password.setFixedWidth(160)
        ff.addRow("Miner Web Password:", self._web_password)

        layout.addWidget(farm_box)

        # ── Network Scan ───────────────────────────────────────────
        net_box = QGroupBox("Network Scan")
        nf = QFormLayout(net_box)
        nf.setSpacing(10)

        self._start_ip = QLineEdit()
        self._start_ip.setPlaceholderText("192.168.1.1")
        self._start_ip.setFixedWidth(160)
        nf.addRow("Start IP:", self._start_ip)

        self._end_ip = QLineEdit()
        self._end_ip.setPlaceholderText("192.168.1.254")
        self._end_ip.setFixedWidth(160)
        nf.addRow("End IP:", self._end_ip)

        self._miner_port = QSpinBox()
        self._miner_port.setRange(1, 65535)
        self._miner_port.setFixedWidth(100)
        nf.addRow("Miner API Port:", self._miner_port)

        self._scan_interval = QSpinBox()
        self._scan_interval.setRange(10, 3600)
        self._scan_interval.setSuffix(" sec")
        self._scan_interval.setFixedWidth(100)
        nf.addRow("Scan Interval:", self._scan_interval)

        self._conn_timeout = QDoubleSpinBox()
        self._conn_timeout.setRange(1, 30)
        self._conn_timeout.setDecimals(1)
        self._conn_timeout.setSuffix(" sec")
        self._conn_timeout.setFixedWidth(100)
        nf.addRow("Connection Timeout:", self._conn_timeout)

        layout.addWidget(net_box)

        # ── Gmail App Password ─────────────────────────────────────
        gmail_box = QGroupBox("Gmail — App Password Setup")
        gmail_box.setStyleSheet(
            f"QGroupBox{{border:2px solid {BITCOIN_ORANGE};border-radius:8px;"
            f"margin-top:14px;padding:14px;background:#161b22;}}"
            f"QGroupBox::title{{color:{BITCOIN_ORANGE};font-size:11px;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:1px;subcontrol-origin:margin;"
            f"left:10px;padding:0 6px;background:#0d1117;}}"
        )
        gf = QVBoxLayout(gmail_box)
        gf.setSpacing(10)

        instructions = QLabel(
            "How to get a Gmail App Password (free, takes 1 minute):\n"
            "  1. Go to myaccount.google.com → Security → 2-Step Verification  (must be ON)\n"
            "  2. Search \"App passwords\" at the top of that page\n"
            "  3. Type a name (e.g. RigAlert™ by ING Mining) → click Create\n"
            "  4. Copy the 16-character password shown and paste it below"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color:#8b949e;font-size:12px;line-height:1.6;background:transparent;")
        gf.addWidget(instructions)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._gmail_user = QLineEdit()
        self._gmail_user.setPlaceholderText("your@gmail.com")
        self._gmail_user.setFixedWidth(280)
        form.addRow("Gmail Address:", self._gmail_user)

        self._app_password = QLineEdit()
        self._app_password.setPlaceholderText("xxxx xxxx xxxx xxxx")
        self._app_password.setFixedWidth(280)
        self._app_password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("App Password:", self._app_password)

        self._alert_to = QLineEdit()
        self._alert_to.setPlaceholderText("email1@gmail.com, email2@outlook.com  (comma-separated)")
        self._alert_to.setFixedWidth(280)
        form.addRow("Send Alerts To:", self._alert_to)

        gf.addLayout(form)

        # Test button
        test_row = QHBoxLayout()
        btn_test = QPushButton("Test Connection")
        btn_test.setFixedWidth(150)
        btn_test.clicked.connect(self._test_email)
        self._test_lbl = QLabel("")
        self._test_lbl.setStyleSheet("font-size:12px;background:transparent;")
        test_row.addWidget(btn_test)
        test_row.addWidget(self._test_lbl, 1)
        gf.addLayout(test_row)

        layout.addWidget(gmail_box)

        # ── Telegram Notifications ─────────────────────────────────
        tg_box = QGroupBox("Telegram Notifications  (real-time alerts)")
        tf = QVBoxLayout(tg_box)
        tf.setSpacing(10)

        tg_instructions = QLabel(
            "How to set up Telegram:\n"
            "  1. Message @BotFather on Telegram → /newbot → get your bot token\n"
            "  2. Start a chat with your new bot, then open:\n"
            "     https://api.telegram.org/bot<TOKEN>/getUpdates\n"
            "  3. Copy the 'id' number from 'chat' — that's your Chat ID"
        )
        tg_instructions.setWordWrap(True)
        tg_instructions.setStyleSheet("color:#8b949e;font-size:12px;line-height:1.6;background:transparent;")
        tf.addWidget(tg_instructions)

        tg_form = QFormLayout()
        tg_form.setSpacing(10)
        tg_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._tg_enabled = QCheckBox("Enable Telegram alerts")
        self._tg_enabled.setStyleSheet("color:#e6edf3;")
        tg_form.addRow("", self._tg_enabled)

        self._tg_token = QLineEdit()
        self._tg_token.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrSTUVwxyz")
        self._tg_token.setFixedWidth(320)
        tg_form.addRow("Bot Token:", self._tg_token)

        self._tg_chat_id = QLineEdit()
        self._tg_chat_id.setPlaceholderText("e.g. -100123456789")
        self._tg_chat_id.setFixedWidth(200)
        tg_form.addRow("Chat ID:", self._tg_chat_id)

        tf.addLayout(tg_form)

        tg_test_row = QHBoxLayout()
        btn_tg_test = QPushButton("Send Test Message")
        btn_tg_test.setFixedWidth(160)
        btn_tg_test.clicked.connect(self._test_telegram)
        self._tg_test_lbl = QLabel("")
        self._tg_test_lbl.setStyleSheet("font-size:12px;background:transparent;")
        tg_test_row.addWidget(btn_tg_test)
        tg_test_row.addWidget(self._tg_test_lbl, 1)
        tf.addLayout(tg_test_row)

        layout.addWidget(tg_box)

        # ── Economics ──────────────────────────────────────────────
        econ_box = QGroupBox("Economics — Profitability Calculator")
        ef = QFormLayout(econ_box)
        ef.setSpacing(10)
        ef.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._elec_cost = QDoubleSpinBox()
        self._elec_cost.setRange(0, 10)
        self._elec_cost.setDecimals(4)
        self._elec_cost.setPrefix("$")
        self._elec_cost.setSuffix(" / kWh")
        self._elec_cost.setFixedWidth(160)
        ef.addRow("Electricity Cost:", self._elec_cost)

        self._profit_lbl = QLabel("— Save settings and wait for miner data to estimate profit")
        self._profit_lbl.setStyleSheet("color:#3fb950;font-size:12px;background:transparent;")
        self._profit_lbl.setWordWrap(True)
        ef.addRow("Est. Daily Profit:", self._profit_lbl)

        layout.addWidget(econ_box)

        # ── Save ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("btnPrimary")
        btn_save.setFixedWidth(160)
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self._save)
        self._saved_lbl = QLabel("")
        self._saved_lbl.setStyleSheet("color:#3fb950;font-size:12px;background:transparent;")
        btn_row.addWidget(btn_save)
        btn_row.addWidget(self._saved_lbl)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

    def _load(self):
        cfg = self._main.get_config()
        self._farm_name.setText(cfg.farm_name)
        self._web_user.setText(cfg.miner_web_user)
        self._web_password.setText(cfg.miner_web_password)
        self._start_ip.setText(cfg.start_ip)
        self._end_ip.setText(cfg.end_ip)
        self._miner_port.setValue(cfg.miner_port)
        self._scan_interval.setValue(cfg.scan_interval_seconds)
        self._conn_timeout.setValue(cfg.connection_timeout)
        self._gmail_user.setText(cfg.gmail_user)
        self._app_password.setText(cfg.gmail_app_password)
        self._alert_to.setText(cfg.alert_to_email)
        self._elec_cost.setValue(cfg.electricity_cost_kwh)
        self._tg_enabled.setChecked(cfg.telegram_enabled)
        self._tg_token.setText(cfg.telegram_bot_token)
        self._tg_chat_id.setText(cfg.telegram_chat_id)

    def _save(self):
        cfg = self._main.get_config()
        cfg.farm_name = self._farm_name.text().strip()
        cfg.miner_web_user = self._web_user.text().strip() or "root"
        cfg.miner_web_password = self._web_password.text().strip() or "root"
        cfg.start_ip = self._start_ip.text().strip()
        cfg.end_ip = self._end_ip.text().strip()
        cfg.miner_port = self._miner_port.value()
        cfg.scan_interval_seconds = self._scan_interval.value()
        cfg.connection_timeout = self._conn_timeout.value()
        cfg.gmail_user = self._gmail_user.text().strip()
        cfg.gmail_app_password = self._app_password.text().strip()
        cfg.alert_to_email = self._alert_to.text().strip()
        cfg.electricity_cost_kwh = self._elec_cost.value()
        cfg.telegram_enabled = self._tg_enabled.isChecked()
        cfg.telegram_bot_token = self._tg_token.text().strip()
        cfg.telegram_chat_id = self._tg_chat_id.text().strip()
        cfg.save()
        self._main.reload_config()
        self._refresh_profit()
        self._saved_lbl.setText("✓ Saved")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self._saved_lbl.setText(""))

    def _test_email(self):
        user = self._gmail_user.text().strip()
        pwd = self._app_password.text().strip()
        to = self._alert_to.text().strip()

        if not user or not pwd:
            self._test_lbl.setText("Enter Gmail address and App Password first")
            self._test_lbl.setStyleSheet("color:#d29922;font-size:12px;background:transparent;")
            return

        self._test_lbl.setText("Testing...")
        self._test_lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")

        from ..alerts.gmail_oauth import test_connection, send_email
        ok, msg = test_connection(user, pwd)
        if ok:
            # Send a real test email if destination is set
            if to:
                from ..alerts.email_builder import build_summary_email
                cfg = self._main.get_config()
                miners = list(self._main.get_miners().values())
                subject, html = build_summary_email(miners, "Test", farm_name=cfg.farm_name)
                subject = subject.replace("Test Report", "Test Email")
                sent, send_err = send_email(user, pwd, to, subject, html)
                if sent:
                    self._test_lbl.setText(f"✓ Connected — test email sent to {to}")
                else:
                    self._test_lbl.setText(f"✗ {send_err}")
                    self._test_lbl.setStyleSheet("color:#f85149;font-size:12px;background:transparent;")
                    return
            else:
                self._test_lbl.setText("✓ Connected successfully")
            self._test_lbl.setStyleSheet("color:#3fb950;font-size:12px;background:transparent;")
        else:
            self._test_lbl.setText(f"✗ {msg}")
            self._test_lbl.setStyleSheet("color:#f85149;font-size:12px;background:transparent;")

    def _refresh_profit(self):
        """Update profitability estimate using current miner data and BTC price from dashboard."""
        from .dashboard_page import _BTC_PER_TH_PER_DAY
        cfg = self._main.get_config()
        miners = list(self._main.get_miners().values())
        active = [m for m in miners if m.status != "offline"]
        total_ths = sum(m.best_hashrate() for m in active)
        total_watts = sum(m.power_watts for m in active if m.power_watts > 0)
        btc_price = self._main._dashboard_page._btc_price
        cost_kwh = cfg.electricity_cost_kwh

        if total_ths <= 0:
            self._profit_lbl.setText("— No miner data yet")
            return

        daily_btc = total_ths * _BTC_PER_TH_PER_DAY
        daily_revenue = daily_btc * btc_price if btc_price > 0 else 0
        daily_kwh = total_watts / 1000 * 24
        daily_elec_cost = daily_kwh * cost_kwh
        daily_profit = daily_revenue - daily_elec_cost

        parts = []
        if btc_price > 0:
            parts.append(f"Revenue: ${daily_revenue:,.2f}/day")
        parts.append(f"Power cost: ${daily_elec_cost:,.2f}/day  ({daily_kwh:.1f} kWh @ ${cost_kwh:.4f}/kWh)")
        if btc_price > 0:
            color = "#3fb950" if daily_profit >= 0 else "#f85149"
            profit_str = f"${daily_profit:+,.2f}/day"
            self._profit_lbl.setText("  ·  ".join(parts) + f"  →  {profit_str}")
            self._profit_lbl.setStyleSheet(f"color:{color};font-size:12px;background:transparent;")
        else:
            self._profit_lbl.setText("  ·  ".join(parts) + "  (BTC price not yet loaded)")
            self._profit_lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")

    def update_profit_estimate(self):
        """Called externally (e.g., on BTC price update) to refresh the profit display."""
        self._refresh_profit()

    def _test_telegram(self):
        token = self._tg_token.text().strip()
        chat_id = self._tg_chat_id.text().strip()
        if not token or not chat_id:
            self._tg_test_lbl.setText("Enter bot token and chat ID first")
            self._tg_test_lbl.setStyleSheet("color:#d29922;font-size:12px;background:transparent;")
            return
        self._tg_test_lbl.setText("Sending...")
        self._tg_test_lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        import threading
        from ..alerts.telegram_notify import test_telegram
        def run():
            ok, msg = test_telegram(token, chat_id)
            from PyQt6.QtCore import QTimer
            color = "#3fb950" if ok else "#f85149"
            QTimer.singleShot(0, lambda: (
                self._tg_test_lbl.setText(f"{'✓' if ok else '✗'} {msg}"),
                self._tg_test_lbl.setStyleSheet(f"color:{color};font-size:12px;background:transparent;"),
            ))
        threading.Thread(target=run, daemon=True).start()
