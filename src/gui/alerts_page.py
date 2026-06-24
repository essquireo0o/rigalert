from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QRadioButton, QScrollArea, QSpinBox, QVBoxLayout,
    QWidget, QLineEdit, QFrame,
)
from PyQt6.QtGui import QColor

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
        scroll.setStyleSheet("QScrollArea{border:none;background:#0a0d12;}")
        root.addWidget(scroll)

        content = QWidget()
        content.setObjectName("alertsContent")
        content.setStyleSheet("QWidget#alertsContent{background:#0a0d12;}")
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
        sub.setStyleSheet(f"color:#9aa8bd;font-size:12px;background:transparent;")
        outer.addWidget(sub)

        # ── Active Alerts ──────────────────────────────────────────────────
        active_box = QGroupBox("Active Alerts")
        active_box.setStyleSheet(
            "QGroupBox{border:2px solid #ff6b6b;border-radius:8px;"
            "margin-top:14px;padding:14px;background:#111722;}"
            "QGroupBox::title{color:#ff6b6b;font-size:11px;font-weight:700;"
            "subcontrol-origin:margin;"
            "left:10px;padding:0 6px;background:#0a0d12;}"
        )
        av = QVBoxLayout(active_box)
        av.setSpacing(8)

        self._active_list = QListWidget()
        self._active_list.setFixedHeight(120)
        self._active_list.setStyleSheet(
            "QListWidget{background:#0d121a;border:1px solid #2d3a50;border-radius:6px;}"
            "QListWidget::item{padding:5px 8px;border-bottom:1px solid #202938;color:#ff6b6b;}"
        )
        av.addWidget(self._active_list)

        btn_row_active = QHBoxLayout()
        self._btn_snooze = QPushButton("Snooze Selected (1hr)")
        self._btn_snooze.setFixedHeight(28)
        self._btn_snooze.setEnabled(False)
        self._btn_snooze.clicked.connect(self._snooze_selected)
        self._btn_dismiss = QPushButton("Dismiss Selected")
        self._btn_dismiss.setFixedHeight(28)
        self._btn_dismiss.setEnabled(False)
        self._btn_dismiss.clicked.connect(self._dismiss_selected)
        btn_dismiss_all = QPushButton("Dismiss All")
        btn_dismiss_all.setFixedHeight(28)
        btn_dismiss_all.clicked.connect(self._dismiss_all)
        btn_row_active.addWidget(self._btn_snooze)
        btn_row_active.addWidget(self._btn_dismiss)
        btn_row_active.addWidget(btn_dismiss_all)
        btn_row_active.addStretch()
        av.addLayout(btn_row_active)

        self._active_list.currentItemChanged.connect(self._on_active_item_changed)
        outer.addWidget(active_box)

        # ── Email Schedule ─────────────────────────────────────────────────
        sched_box = QGroupBox("Email Schedule  (one summary email per interval)")
        sched_box.setStyleSheet(
            f"QGroupBox{{border:2px solid {BITCOIN_ORANGE};border-radius:8px;"
            f"margin-top:14px;padding:14px;background:#111722;}}"
            f"QGroupBox::title{{color:{BITCOIN_ORANGE};font-size:11px;font-weight:700;"
            f"subcontrol-origin:margin;"
            f"left:10px;padding:0 6px;background:#0a0d12;}}"
        )
        sf = QVBoxLayout(sched_box)
        sf.setSpacing(10)

        self._rb_hourly = QRadioButton("Hourly  —  one email at the top of each hour (e.g. 9:00, 10:00, 11:00)")
        self._rb_12h    = QRadioButton("Every 12 Hours  —  one email at midnight and noon")
        self._rb_daily  = QRadioButton("Daily  —  one email per day at the time you choose below")

        self._sched_grp = QButtonGroup(self)
        for rb in [self._rb_hourly, self._rb_12h, self._rb_daily]:
            self._sched_grp.addButton(rb)
            rb.setStyleSheet("color:#eef4ff;font-size:13px;spacing:8px;")
            sf.addWidget(rb)

        hour_row = QHBoxLayout()
        hour_row.setContentsMargins(26, 0, 0, 0)
        lbl = QLabel("Daily send time (0–23 hour, US Eastern Time):")
        lbl.setStyleSheet("color:#9aa8bd;font-size:12px;background:transparent;")
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
        self._chk_email.setStyleSheet("color:#eef4ff;")
        self._chk_popup.setStyleSheet("color:#eef4ff;")
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

        daily_row = QHBoxLayout()
        self._btn_send_daily = QPushButton("Send 24 Hour Report Now")
        self._btn_send_daily.setObjectName("btnPrimary")
        self._btn_send_daily.setFixedWidth(210)
        self._btn_send_daily.setFixedHeight(32)
        self._btn_send_daily.clicked.connect(self._send_daily_now)
        self._daily_result = QLabel("")
        self._daily_result.setStyleSheet("font-size:12px;background:transparent;")
        daily_row.addWidget(self._btn_send_daily)
        daily_row.addWidget(self._daily_result, 1)
        df.addLayout(daily_row)

        outer.addWidget(delivery_box)

        # ── Crypto Price Alerts ────────────────────────────────────────────
        price_box = QGroupBox("Crypto Price Alerts  (polls CoinGecko every 5 min — no API key needed)")
        pf = QVBoxLayout(price_box)
        pf.setSpacing(10)

        self._chk_price = QCheckBox("Enable crypto price alerts")
        self._chk_price.setStyleSheet("color:#eef4ff;font-weight:600;")
        pf.addWidget(self._chk_price)

        # BTC thresholds
        btc_box = QGroupBox("Bitcoin (BTC)")
        btc_box.setStyleSheet(
            "QGroupBox{border:1px solid #202938;border-radius:6px;margin-top:8px;"
            "padding:8px;background:#0d121a;}"
            "QGroupBox::title{subcontrol-origin:margin;left:6px;padding:0 4px;"
            "background:#0d121a;color:#9aa8bd;font-size:11px;}"
        )
        bf = QFormLayout(btc_box)
        bf.setSpacing(8)
        bf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._btc_above = QDoubleSpinBox()
        self._btc_above.setRange(0, 10_000_000)
        self._btc_above.setDecimals(0)
        self._btc_above.setPrefix("$")
        self._btc_above.setFixedWidth(140)
        self._btc_above.setSpecialValueText("Disabled")
        bf.addRow("Alert when BTC above:", self._btc_above)

        self._btc_below = QDoubleSpinBox()
        self._btc_below.setRange(0, 10_000_000)
        self._btc_below.setDecimals(0)
        self._btc_below.setPrefix("$")
        self._btc_below.setFixedWidth(140)
        self._btc_below.setSpecialValueText("Disabled")
        bf.addRow("Alert when BTC below:", self._btc_below)

        self._btc_pct = QDoubleSpinBox()
        self._btc_pct.setRange(0, 100)
        self._btc_pct.setDecimals(1)
        self._btc_pct.setSuffix("% in 24h")
        self._btc_pct.setFixedWidth(140)
        self._btc_pct.setSpecialValueText("Disabled")
        bf.addRow("Alert on ±% move:", self._btc_pct)

        pf.addWidget(btc_box)

        # Altcoin row (simple: coin id + above/below)
        alt_box = QGroupBox("Altcoins (one per line: coin_id,above_usd,below_usd  e.g. ethereum,4000,2000)")
        alt_box.setStyleSheet(
            "QGroupBox{border:1px solid #202938;border-radius:6px;margin-top:8px;"
            "padding:8px;background:#0d121a;}"
            "QGroupBox::title{subcontrol-origin:margin;left:6px;padding:0 4px;"
            "background:#0d121a;color:#9aa8bd;font-size:10px;}"
        )
        af = QVBoxLayout(alt_box)
        self._altcoin_text = QLineEdit()
        self._altcoin_text.setPlaceholderText(
            "e.g.  ethereum,4000,2000   or   solana,200,100"
        )
        af.addWidget(self._altcoin_text)
        coin_hint = QLabel(
            "Use CoinGecko coin IDs: bitcoin, ethereum, solana, cardano, etc.  "
            "Leave blank to disable altcoin alerts."
        )
        coin_hint.setStyleSheet("color:#9aa8bd;font-size:11px;background:transparent;")
        coin_hint.setWordWrap(True)
        af.addWidget(coin_hint)
        pf.addWidget(alt_box)

        # Test price check button
        test_price_row = QHBoxLayout()
        btn_price_test = QPushButton("Check Prices Now")
        btn_price_test.setFixedWidth(160)
        btn_price_test.clicked.connect(self._check_prices_now)
        self._price_result = QLabel("")
        self._price_result.setStyleSheet("font-size:12px;background:transparent;")
        test_price_row.addWidget(btn_price_test)
        test_price_row.addWidget(self._price_result, 1)
        pf.addLayout(test_price_row)

        outer.addWidget(price_box)

        # ── Auto-Reboot ────────────────────────────────────────────────────
        reboot_box = QGroupBox("Auto-Reboot  (VNish / CGMiner firmware)")
        reboot_box.setStyleSheet(
            "QGroupBox{border:2px solid #f85149;border-radius:8px;"
            "margin-top:14px;padding:14px;background:#111722;}"
            "QGroupBox::title{color:#f85149;font-size:11px;font-weight:700;"
            "subcontrol-origin:margin;left:10px;padding:0 6px;background:#0a0d12;}"
        )
        rf2 = QVBoxLayout(reboot_box)
        rf2.setSpacing(10)

        self._chk_reboot = QCheckBox("Automatically reboot miner when a critical error is detected")
        self._chk_reboot.setStyleSheet("color:#eef4ff;font-weight:600;")
        rf2.addWidget(self._chk_reboot)

        trigger_lbl = QLabel(
            "Triggers a reboot when any of these occur:\n"
            "  • Temperature reaches or exceeds the Critical Temp threshold above\n"
            "  • Hashrate drops to zero while the miner is online (stopped mining)\n"
            "  • A hashboard enters a fault / dead state (chain fault)\n\n"
            "Uses the Miner Web Password set in Settings.  Miner reboots itself — "
            "no power relay needed."
        )
        trigger_lbl.setWordWrap(True)
        trigger_lbl.setStyleSheet("color:#9aa8bd;font-size:12px;background:transparent;")
        rf2.addWidget(trigger_lbl)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background:#2d3a50;max-height:1px;border:none;margin:4px 0;")
        div.setFixedHeight(1)
        rf2.addWidget(div)

        self._chk_board_overheat = QCheckBox("Auto-handle overheating boards")
        self._chk_board_overheat.setStyleSheet("color:#eef4ff;font-weight:600;")
        rf2.addWidget(self._chk_board_overheat)

        overheat_desc = QLabel(
            "30 minutes or less: disable the overheating board and reboot\n"
            "Over 30 minutes: reboot the miner to keep it hashing"
        )
        overheat_desc.setWordWrap(True)
        overheat_desc.setStyleSheet("color:#9aa8bd;font-size:12px;background:transparent;")
        rf2.addWidget(overheat_desc)

        restart_interval_row = QHBoxLayout()
        restart_interval_row.setContentsMargins(26, 4, 0, 0)
        ri_lbl = QLabel("Threshold:")
        ri_lbl.setStyleSheet("color:#9aa8bd;font-size:12px;background:transparent;")
        self._restart_overheat_mins = QSpinBox()
        self._restart_overheat_mins.setRange(5, 240)
        self._restart_overheat_mins.setValue(30)
        self._restart_overheat_mins.setSuffix(" min")
        self._restart_overheat_mins.setFixedWidth(90)
        restart_interval_row.addWidget(ri_lbl)
        restart_interval_row.addWidget(self._restart_overheat_mins)
        restart_interval_row.addStretch()
        rf2.addLayout(restart_interval_row)

        cooldown_row = QHBoxLayout()
        cooldown_lbl = QLabel("Minimum time between reboots per miner:")
        cooldown_lbl.setStyleSheet("color:#9aa8bd;font-size:12px;background:transparent;")
        self._reboot_cooldown = QSpinBox()
        self._reboot_cooldown.setRange(1, 120)
        self._reboot_cooldown.setSuffix(" min")
        self._reboot_cooldown.setFixedWidth(90)
        self._reboot_cooldown.setToolTip("Prevents reboot loops — miner won't be rebooted again within this window")
        cooldown_row.addWidget(cooldown_lbl)
        cooldown_row.addWidget(self._reboot_cooldown)
        cooldown_row.addStretch()
        rf2.addLayout(cooldown_row)

        outer.addWidget(reboot_box)

        # ── Save ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Alert Settings")
        btn_save.setObjectName("btnPrimary")
        btn_save.setFixedWidth(200)
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        self._saved_lbl = QLabel("")
        self._saved_lbl.setStyleSheet("color:#2fbf71;font-size:12px;background:transparent;")
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

        # Auto-reboot
        self._chk_reboot.setChecked(getattr(cfg, "auto_reboot_enabled", False))
        self._reboot_cooldown.setValue(getattr(cfg, "auto_reboot_cooldown_minutes", 10))
        self._chk_board_overheat.setChecked(getattr(cfg, "auto_board_overheat_enabled", False))
        self._restart_overheat_mins.setValue(getattr(cfg, "auto_reboot_overheat_minutes", 30))

        # Price alerts
        self._chk_price.setChecked(cfg.price_alerts_enabled)
        self._btc_above.setValue(cfg.btc_alert_above or 0)
        self._btc_below.setValue(cfg.btc_alert_below or 0)
        self._btc_pct.setValue(cfg.btc_alert_pct_move or 0)
        alt_lines = []
        for alt in (cfg.altcoin_alerts or []):
            parts = [alt.get("id", ""), str(alt.get("above", 0)), str(alt.get("below", 0))]
            alt_lines.append(",".join(parts))
        self._altcoin_text.setText("  ".join(alt_lines))

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

        # Auto-reboot
        cfg.auto_reboot_enabled           = self._chk_reboot.isChecked()
        cfg.auto_reboot_cooldown_minutes  = self._reboot_cooldown.value()
        cfg.auto_board_overheat_enabled   = self._chk_board_overheat.isChecked()
        cfg.auto_reboot_overheat_minutes  = self._restart_overheat_mins.value()

        # Price alerts
        cfg.price_alerts_enabled = self._chk_price.isChecked()
        cfg.btc_alert_above      = self._btc_above.value()
        cfg.btc_alert_below      = self._btc_below.value()
        cfg.btc_alert_pct_move   = self._btc_pct.value()

        alts = []
        for token in self._altcoin_text.text().replace(";", " ").split():
            parts = [p.strip() for p in token.split(",")]
            if parts and parts[0]:
                try:
                    alts.append({
                        "id":       parts[0],
                        "symbol":   parts[0].upper(),
                        "above":    float(parts[1]) if len(parts) > 1 else 0,
                        "below":    float(parts[2]) if len(parts) > 2 else 0,
                        "pct_move": float(parts[3]) if len(parts) > 3 else 0,
                    })
                except ValueError:
                    pass
        cfg.altcoin_alerts = alts

        cfg.save()
        self._main.reload_config()
        self._saved_lbl.setText("✓ Saved")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self._saved_lbl.setText(""))

    def _check_prices_now(self):
        self._price_result.setText("Fetching...")
        self._price_result.setStyleSheet("color:#9aa8bd;font-size:12px;background:transparent;")
        from ..alerts.price_monitor import _fetch_prices
        import threading

        def run():
            data = _fetch_prices(["bitcoin"])
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._show_price_result(data))

        threading.Thread(target=run, daemon=True).start()

    def _show_price_result(self, data: dict):
        btc = data.get("bitcoin", {})
        price = btc.get("usd", 0)
        change = btc.get("usd_24h_change", 0) or 0
        if price:
            direction = "▲" if change >= 0 else "▼"
            self._price_result.setText(f"BTC: ${price:,.0f}  {direction}{abs(change):.1f}% 24h")
            color = "#2fbf71" if change >= 0 else "#ff6b6b"
            self._price_result.setStyleSheet(f"color:{color};font-size:12px;background:transparent;")
        else:
            self._price_result.setText("Could not fetch price — check internet connection")
            self._price_result.setStyleSheet("color:#ff6b6b;font-size:12px;background:transparent;")

    def refresh_active_alerts(self, miners):
        """Called by MainWindow on each miner update to refresh the active alerts panel."""
        self._active_list.clear()
        cfg = self._main.get_config()
        for m in miners:
            issues = []
            if m.status == "offline":
                issues.append(("OFFLINE", f"offline"))
            elif m.status == "warning":
                temp = m.temp_chip_max or m.temp_outlet
                if temp >= cfg.high_temp_c > 0:
                    issues.append(("CRIT TEMP", f"{temp:.0f}°C"))
                elif temp >= cfg.warn_temp_c > 0:
                    issues.append(("HIGH TEMP", f"{temp:.0f}°C"))
                if m.best_hashrate() < cfg.default_min_ths > 0:
                    issues.append(("LOW HASH", f"{m.best_hashrate():.1f} TH/s"))
                if m.hw_error_rate >= cfg.max_hw_error_rate > 0:
                    issues.append(("HW ERR", f"{m.hw_error_rate:.2f}%"))
            for kind, detail in issues:
                item = QListWidgetItem(f"  {m.display_name} ({m.ip})  —  {kind}: {detail}")
                item.setData(Qt.ItemDataRole.UserRole, m.ip)
                item.setForeground(QColor("#ff6b6b" if kind in ("OFFLINE", "CRIT TEMP") else "#f2b84b"))
                self._active_list.addItem(item)
        if self._active_list.count() == 0:
            ok = QListWidgetItem("  No active alerts — fleet is healthy")
            ok.setForeground(QColor("#2fbf71"))
            self._active_list.addItem(ok)

    def _on_active_item_changed(self, current, _prev):
        has = current is not None and current.data(Qt.ItemDataRole.UserRole) is not None
        self._btn_snooze.setEnabled(has)
        self._btn_dismiss.setEnabled(has)

    def _snooze_selected(self):
        cur = self._active_list.currentItem()
        if not cur:
            return
        ip = cur.data(Qt.ItemDataRole.UserRole)
        if ip:
            self._main.snooze_miner(ip, 60)
            self._active_list.takeItem(self._active_list.row(cur))

    def _dismiss_selected(self):
        cur = self._active_list.currentItem()
        if not cur:
            return
        ip = cur.data(Qt.ItemDataRole.UserRole)
        if ip:
            self._main.dismiss_miner_alerts(ip)
            self._active_list.takeItem(self._active_list.row(cur))

    def _dismiss_all(self):
        for row in range(self._active_list.count()):
            item = self._active_list.item(row)
            if item:
                ip = item.data(Qt.ItemDataRole.UserRole)
                if ip:
                    self._main.dismiss_miner_alerts(ip)
        self._active_list.clear()
        ok = QListWidgetItem("  No active alerts — fleet is healthy")
        ok.setForeground(QColor("#2fbf71"))
        self._active_list.addItem(ok)

    def _send_daily_now(self):
        from PyQt6.QtCore import QTimer
        cfg = self._main.get_config()

        if not cfg.enable_email_alerts:
            self._daily_result.setText("✗ Email alerts disabled — tick the checkbox above and save")
            self._daily_result.setStyleSheet("color:#ff6b6b;font-size:12px;background:transparent;")
            return
        if not cfg.gmail_user or not cfg.gmail_app_password:
            self._daily_result.setText("✗ Gmail credentials missing — go to Settings tab")
            self._daily_result.setStyleSheet("color:#ff6b6b;font-size:12px;background:transparent;")
            return
        if not cfg.alert_to_email:
            self._daily_result.setText("✗ No destination email — go to Settings tab")
            self._daily_result.setStyleSheet("color:#ff6b6b;font-size:12px;background:transparent;")
            return

        self._daily_result.setText("Sending...")
        self._daily_result.setStyleSheet("color:#f2b84b;font-size:12px;background:transparent;")

        from ..alerts.email_builder import build_summary_email
        from ..alerts.gmail_oauth import send_email

        miners = list(self._main.get_miners().values())
        subject, html = build_summary_email(miners, "Daily", farm_name=cfg.farm_name)
        ok, err = send_email(cfg.gmail_user, cfg.gmail_app_password, cfg.alert_to_email, subject, html)

        if ok:
            self._daily_result.setText(f"✓ Daily report sent to {cfg.alert_to_email}")
            self._daily_result.setStyleSheet("color:#2fbf71;font-size:12px;background:transparent;")
            QTimer.singleShot(10000, lambda: self._daily_result.setText(""))
        else:
            self._daily_result.setText(f"✗ {err}")
            self._daily_result.setStyleSheet("color:#ff6b6b;font-size:12px;background:transparent;")

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
        self._test_result.setStyleSheet("color:#f2b84b;font-size:12px;background:transparent;")

        from ..alerts.gmail_oauth import send_email
        from ..alerts.email_builder import build_summary_email
        miners = list(self._main.get_miners().values())
        subject, html = build_summary_email(miners, "Test", farm_name=cfg.farm_name)
        subject = subject.replace("Test Report", "Test Email")
        ok, err = send_email(cfg.gmail_user, cfg.gmail_app_password,
                             cfg.alert_to_email, subject, html)
        if ok:
            self._test_result.setText("✓ Test email sent — check your inbox")
            self._test_result.setStyleSheet("color:#2fbf71;font-size:12px;background:transparent;")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(5000, lambda: self._test_result.setText(""))
        else:
            self._test_result.setText(f"✗ {err}")
            self._test_result.setStyleSheet("color:#ff6b6b;font-size:12px;background:transparent;")
