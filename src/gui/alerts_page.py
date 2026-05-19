from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QRadioButton,
    QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from .theme import BITCOIN_ORANGE


class AlertsPage(QWidget):
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

        outer = QVBoxLayout(content)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(16)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Alert Settings")
        title.setObjectName("sectionTitle")
        outer.addWidget(title)

        sub = QLabel(
            "Alerts are sent as a single SUMMARY email on your chosen schedule — "
            "not one email per event. All issues since the last email are bundled together."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:#8b949e;font-size:12px;background:transparent;")
        outer.addWidget(sub)

        # ── Email Schedule ─────────────────────────────────────────────────
        sched_box = QGroupBox("Email Schedule  (one summary email per interval)")
        sched_box.setStyleSheet(
            f"QGroupBox{{border:2px solid {BITCOIN_ORANGE};border-radius:8px;"
            f"margin-top:14px;padding:14px;background:#161b22;}}"
            f"QGroupBox::title{{color:{BITCOIN_ORANGE};font-size:11px;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:1px;subcontrol-origin:margin;"
            f"left:10px;padding:0 6px;background:#0d1117;}}"
        )
        sf = QVBoxLayout(sched_box)
        sf.setSpacing(10)

        self._rb_hourly = QRadioButton("Hourly  —  one email at the top of each hour (e.g. 9:00, 10:00, 11:00)")
        self._rb_12h    = QRadioButton("Every 12 Hours  —  one email at midnight and noon")
        self._rb_daily  = QRadioButton("Daily  —  one email per day at the time you choose below")

        self._sched_grp = QButtonGroup(self)
        for rb in [self._rb_hourly, self._rb_12h, self._rb_daily]:
            self._sched_grp.addButton(rb)
            rb.setStyleSheet("color:#e6edf3;font-size:13px;spacing:8px;")
            sf.addWidget(rb)

        hour_row = QHBoxLayout()
        hour_row.setContentsMargins(26, 0, 0, 0)
        lbl = QLabel("Daily send time (0–23 hour, local time):")
        lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        hour_row.addWidget(lbl)
        self._send_hour = QSpinBox()
        self._send_hour.setRange(0, 23)
        self._send_hour.setFixedWidth(70)
        self._send_hour.setSuffix(":00")
        hour_row.addWidget(self._send_hour)
        hour_row.addStretch()
        sf.addLayout(hour_row)

        self._rb_daily.toggled.connect(self._send_hour.setEnabled)
        outer.addWidget(sched_box)

        # ── Alert Rules ────────────────────────────────────────────────────
        rules_box = QGroupBox("Alert Rules  (what gets included in the summary)")
        rf = QVBoxLayout(rules_box)
        rf.setSpacing(8)

        self._chk_offline  = QCheckBox("Miner went offline")
        self._chk_low_hash = QCheckBox("Hashrate below minimum threshold")
        self._chk_temp     = QCheckBox("Temperature above warning/critical level")
        self._chk_fan      = QCheckBox("Fan speed below minimum RPM")
        self._chk_hw_err   = QCheckBox("Hardware error rate above threshold")

        for chk in [self._chk_offline, self._chk_low_hash, self._chk_temp,
                    self._chk_fan, self._chk_hw_err]:
            rf.addWidget(chk)

        outer.addWidget(rules_box)

        # ── Thresholds ─────────────────────────────────────────────────────
        thresh_box = QGroupBox("Thresholds")
        thf = QFormLayout(thresh_box)
        thf.setSpacing(10)
        thf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._min_ths = QDoubleSpinBox()
        self._min_ths.setRange(0, 999999)
        self._min_ths.setDecimals(1)
        self._min_ths.setSuffix(" TH/s")
        self._min_ths.setFixedWidth(140)
        thf.addRow("Min hashrate per miner:", self._min_ths)

        self._warn_temp = QDoubleSpinBox()
        self._warn_temp.setRange(0, 150)
        self._warn_temp.setDecimals(1)
        self._warn_temp.setSuffix(" °C")
        self._warn_temp.setFixedWidth(100)
        thf.addRow("Warning temperature:", self._warn_temp)

        self._crit_temp = QDoubleSpinBox()
        self._crit_temp.setRange(0, 150)
        self._crit_temp.setDecimals(1)
        self._crit_temp.setSuffix(" °C")
        self._crit_temp.setFixedWidth(100)
        thf.addRow("Critical temperature:", self._crit_temp)

        self._max_hw_err = QDoubleSpinBox()
        self._max_hw_err.setRange(0, 100)
        self._max_hw_err.setDecimals(2)
        self._max_hw_err.setSuffix(" %")
        self._max_hw_err.setFixedWidth(100)
        thf.addRow("Max HW error rate:", self._max_hw_err)

        self._min_fan_rpm = QSpinBox()
        self._min_fan_rpm.setRange(0, 20000)
        self._min_fan_rpm.setSuffix(" RPM")
        self._min_fan_rpm.setFixedWidth(110)
        thf.addRow("Min fan speed:", self._min_fan_rpm)

        outer.addWidget(thresh_box)

        # ── Delivery ───────────────────────────────────────────────────────
        delivery_box = QGroupBox("Delivery")
        df = QVBoxLayout(delivery_box)
        df.setSpacing(10)

        self._chk_email = QCheckBox("Send summary email via Gmail  (configure Gmail in Settings tab)")
        self._chk_popup = QCheckBox("Show Windows tray notification at each interval")
        self._chk_email.setStyleSheet("color:#e6edf3;")
        self._chk_popup.setStyleSheet("color:#e6edf3;")
        df.addWidget(self._chk_email)
        df.addWidget(self._chk_popup)

        test_row = QHBoxLayout()
        btn_test = QPushButton("Send Test Email Now")
        btn_test.setFixedWidth(180)
        btn_test.clicked.connect(self._send_test)
        self._test_result = QLabel("")
        self._test_result.setStyleSheet("font-size:12px;background:transparent;")
        test_row.addWidget(btn_test)
        test_row.addWidget(self._test_result, 1)
        df.addLayout(test_row)

        outer.addWidget(delivery_box)

        # ── Save ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Alert Settings")
        btn_save.setObjectName("btnPrimary")
        btn_save.setFixedWidth(200)
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        self._saved_lbl = QLabel("")
        self._saved_lbl.setStyleSheet("color:#3fb950;font-size:12px;background:transparent;")
        btn_row.addWidget(self._saved_lbl)
        btn_row.addStretch()
        outer.addLayout(btn_row)

        outer.addStretch()

    def _load(self):
        cfg = self._main.get_config()

        interval = cfg.alert_interval
        if interval == "hourly":
            self._rb_hourly.setChecked(True)
        elif interval == "12hour":
            self._rb_12h.setChecked(True)
        else:
            self._rb_daily.setChecked(True)

        self._send_hour.setValue(cfg.alert_send_hour)
        self._send_hour.setEnabled(interval == "daily")

        self._chk_offline.setChecked(cfg.alert_offline_enabled)
        self._chk_low_hash.setChecked(cfg.alert_low_hash_enabled)
        self._chk_temp.setChecked(cfg.alert_temp_enabled)
        self._chk_fan.setChecked(cfg.alert_fan_enabled)
        self._chk_hw_err.setChecked(cfg.alert_hw_err_enabled)

        self._min_ths.setValue(cfg.default_min_ths)
        self._warn_temp.setValue(cfg.warn_temp_c)
        self._crit_temp.setValue(cfg.high_temp_c)
        self._max_hw_err.setValue(cfg.max_hw_error_rate)
        self._min_fan_rpm.setValue(cfg.min_fan_rpm)

        self._chk_email.setChecked(cfg.enable_email_alerts)
        self._chk_popup.setChecked(cfg.enable_popup_alerts)

    def _save(self):
        cfg = self._main.get_config()

        if self._rb_hourly.isChecked():
            cfg.alert_interval = "hourly"
        elif self._rb_12h.isChecked():
            cfg.alert_interval = "12hour"
        else:
            cfg.alert_interval = "daily"

        cfg.alert_send_hour       = self._send_hour.value()
        cfg.alert_offline_enabled = self._chk_offline.isChecked()
        cfg.alert_low_hash_enabled= self._chk_low_hash.isChecked()
        cfg.alert_temp_enabled    = self._chk_temp.isChecked()
        cfg.alert_fan_enabled     = self._chk_fan.isChecked()
        cfg.alert_hw_err_enabled  = self._chk_hw_err.isChecked()
        cfg.default_min_ths       = self._min_ths.value()
        cfg.warn_temp_c           = self._warn_temp.value()
        cfg.high_temp_c           = self._crit_temp.value()
        cfg.max_hw_error_rate     = self._max_hw_err.value()
        cfg.min_fan_rpm           = self._min_fan_rpm.value()
        cfg.enable_email_alerts   = self._chk_email.isChecked()
        cfg.enable_popup_alerts   = self._chk_popup.isChecked()

        cfg.save()
        self._main.reload_config()
        self._saved_lbl.setText("✓ Saved")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self._saved_lbl.setText(""))

    def _send_test(self):
        cfg = self._main.get_config()
        if not cfg.gmail_user or not cfg.gmail_app_password:
            QMessageBox.warning(self, "Gmail Not Configured",
                                "Enter your Gmail address and App Password in Settings first.")
            return
        if not cfg.alert_to_email:
            QMessageBox.warning(self, "No Destination Email",
                                "Set a destination email address in Settings first.")
            return
        self._test_result.setText("Sending...")
        self._test_result.setStyleSheet("color:#d29922;font-size:12px;background:transparent;")

        from ..alerts.gmail_oauth import send_email
        from ..alerts.email_builder import build_summary_email
        miners = list(self._main.get_miners().values())
        subject, html = build_summary_email(miners, "Test", farm_name=cfg.farm_name)
        subject = subject.replace("Test Report", "Test Email")
        ok, err = send_email(cfg.gmail_user, cfg.gmail_app_password,
                             cfg.alert_to_email, subject, html)
        if ok:
            self._test_result.setText("✓ Test email sent — check your inbox")
            self._test_result.setStyleSheet("color:#3fb950;font-size:12px;background:transparent;")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(5000, lambda: self._test_result.setText(""))
        else:
            self._test_result.setText(f"✗ {err}")
            self._test_result.setStyleSheet("color:#f85149;font-size:12px;background:transparent;")
