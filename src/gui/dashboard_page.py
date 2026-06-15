import os
import subprocess
import threading
from typing import Dict, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ..core.miner import MinerData
from .theme import STATUS_COLORS, BITCOIN_ORANGE, BG_CARD, TEXT_MUTED, BORDER_COLOR


def _launch_chrome(url: str, main_win=None):
    """Open url in Chrome; if main_win is available also trigger VNish auto-unlock."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            subprocess.Popen([path, url])
            break
    else:
        subprocess.Popen(["start", "chrome", url], shell=True)
    if main_win and hasattr(main_win, "get_config"):
        try:
            from ..gui.miners_page import _auto_unlock_vnish
            pwd = main_win.get_config().miner_web_password or "admin"
            threading.Thread(target=_auto_unlock_vnish, args=(pwd,), daemon=True).start()
        except Exception:
            pass

_CHAIN_COLORS = {
    "running":      "#2fbf71",
    "normal":       "#2fbf71",
    "active":       "#2fbf71",
    "mining":       "#2fbf71",
    "stopped":      "#f2b84b",
    "idle":         "#f2b84b",
    "auto-tuning":  "#58a6ff",
    "disabled":     "#9aa8bd",
    "failure":      "#ff6b6b",
    "dead":         "#ff6b6b",
    "error":        "#ff6b6b",
}


def _chain_color(state: str) -> str:
    return _CHAIN_COLORS.get(state.lower(), "#9aa8bd")


class MinerCard(QFrame):
    def __init__(self, miner: MinerData, parent=None, main_win=None):
        super().__init__(parent)
        self.setObjectName("minerCard")
        self.setMinimumWidth(270)
        self.setMinimumHeight(206)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setToolTip("Double-click to view full details")
        self._miner = miner
        self._main_win = main_win
        self._build(miner)

    def mouseDoubleClickEvent(self, event):
        self._open_details()

    def _build(self, m: MinerData):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # ── Header ────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(6)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{STATUS_COLORS.get(m.status, '#9aa8bd')};font-size:10px;background:transparent;")
        header.addWidget(dot)

        name = QLabel(m.display_name)
        name.setObjectName("cardName")
        name.setStyleSheet("font-size:13px;font-weight:700;color:#eef4ff;background:transparent;")
        header.addWidget(name, 1)

        if m.status == "online":
            bs = "background:#174f35;color:#8ff0b2;"
        elif m.status == "warning":
            bs = "background:#664b1f;color:#ffe2a3;"
        elif m.status == "offline":
            bs = "background:#6e2b2b;color:#ffd2d2;"
        else:
            bs = "background:#263144;color:#9aa8bd;"
        badge = QLabel(m.status.upper())
        badge.setStyleSheet(f"{bs}font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;")
        header.addWidget(badge)
        layout.addLayout(header)

        # IP + port — click opens Chrome
        ip_lbl = QLabel(f'<a href="http://{m.ip}" style="color:#58a6ff;text-decoration:underline;">'
                        f'{m.ip}:{m.port}</a>')
        ip_lbl.setStyleSheet("font-size:11px;font-family:Consolas,monospace;background:transparent;")
        ip_lbl.setToolTip(f"Open http://{m.ip} in Chrome")
        ip_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        ip_lbl.linkActivated.connect(lambda url: _launch_chrome(url, self._main_win))
        layout.addWidget(ip_lbl)

        # Model name + firmware badge
        if m.model or m.firmware:
            model_row = QHBoxLayout()
            model_row.setSpacing(6)
            if m.model:
                mdl = QLabel(m.model)
                mdl.setStyleSheet(f"color:{BITCOIN_ORANGE};font-size:11px;font-weight:600;background:transparent;")
                mdl.setWordWrap(False)
                model_row.addWidget(mdl)
            if m.firmware:
                fw_lower = m.firmware.lower()
                if "vnish" in fw_lower:
                    fw_label, fw_color = "VNish", "#58a6ff"
                elif "braiins" in fw_lower or "bosminer" in fw_lower or "bos+" in fw_lower:
                    fw_label, fw_color = "Braiins OS", "#2fbf71"
                elif fw_lower:
                    fw_label, fw_color = "Stock", "#9aa8bd"
                else:
                    fw_label, fw_color = None, None
                if fw_label:
                    fw_btn = QPushButton(fw_label)
                    fw_btn.setFlat(True)
                    fw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    fw_btn.setStyleSheet(
                        f"QPushButton{{color:{fw_color};font-size:9px;font-weight:700;"
                        f"border:1px solid {fw_color};border-radius:4px;"
                        f"padding:1px 5px;background:transparent;}}"
                        f"QPushButton:hover{{background:rgba(88,166,255,0.15);}}"
                    )
                    fw_btn.setToolTip(f"Open http://{m.ip} in Chrome")
                    _ip = m.ip
                    _mw = self._main_win
                    fw_btn.clicked.connect(lambda _=False, ip=_ip, mw=_mw:
                                           _launch_chrome(f"http://{ip}", mw))
                    model_row.addWidget(fw_btn)
            model_row.addStretch()
            layout.addLayout(model_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#202938;background:#202938;max-height:1px;")
        layout.addWidget(sep)

        # ── Hashrate ──────────────────────────────────────────────
        hr_row = QHBoxLayout()
        hs_str = m.display_hashrate()
        parts = hs_str.split(" ", 1)
        hs_num = parts[0]
        hs_unit = parts[1] if len(parts) > 1 else ""
        hr_val = QLabel(hs_num)
        hr_val.setStyleSheet(f"font-size:22px;font-weight:700;color:{BITCOIN_ORANGE};background:transparent;")
        hr_row.addWidget(hr_val)
        hr_unit = QLabel(hs_unit)
        hr_unit.setStyleSheet("font-size:11px;color:#9aa8bd;padding-bottom:4px;background:transparent;")
        hr_row.addWidget(hr_unit)
        hr_row.addStretch()

        # Miner state badge (if VNISH)
        if m.miner_state:
            state_col = _chain_color(m.miner_state)
            state_lbl = QLabel(m.miner_state.upper())
            state_lbl.setStyleSheet(
                f"color:{state_col};font-size:9px;font-weight:700;"
                f"border:1px solid {state_col};border-radius:4px;padding:1px 5px;background:transparent;"
            )
            hr_row.addWidget(state_lbl)

        layout.addLayout(hr_row)

        # Hashrate progress bar
        pct = int(m.hashrate_pct())
        hr_bar = QProgressBar()
        hr_bar.setValue(pct)
        hr_bar.setMaximumHeight(5)
        hr_bar.setTextVisible(False)
        bar_color = "#2fbf71" if pct >= 95 else "#f2b84b" if pct >= 80 else "#ff6b6b"
        hr_bar.setStyleSheet(
            f"QProgressBar{{background:#202938;border:none;border-radius:3px;height:5px;}}"
            f"QProgressBar::chunk{{background:{bar_color};border-radius:3px;}}"
        )
        layout.addWidget(hr_bar)

        # ── Metrics grid ──────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setContentsMargins(0, 4, 0, 0)

        def add_metric(row, col, key, val, val_color="#eef4ff"):
            k = QLabel(key)
            k.setStyleSheet("color:#9aa8bd;font-size:10px;background:transparent;")
            v = QLabel(val)
            v.setStyleSheet(f"color:{val_color};font-size:11px;font-weight:500;background:transparent;")
            grid.addWidget(k, row, col * 2)
            grid.addWidget(v, row, col * 2 + 1)

        temp = m.display_temp()
        temp_color = (STATUS_COLORS.get(m.temp_level(75, 85), "#eef4ff")
                      if temp != "N/A" else "#9aa8bd")

        # Fan display: show individual fans if available
        if m.fan_speeds and len(m.fan_speeds) > 1:
            fan_str = "  ".join(f"{rpm:,}" for rpm in m.fan_speeds[:4])
            fan_str += " RPM"
        else:
            fan_str = m.display_fan()

        add_metric(0, 0, "TEMP", temp, temp_color)
        add_metric(0, 1, "FAN", fan_str)
        add_metric(1, 0, "ACCEPT", f"{m.accepted:,}")
        add_metric(1, 1, "HW ERR", f"{m.hw_error_rate:.2f}%",
                   "#ff6b6b" if m.hw_error_rate >= 1.0 else "#eef4ff")
        add_metric(2, 0, "UPTIME", m.display_uptime())
        pool_short = m.pool_url.replace("stratum+tcp://", "").split("/")[0][:20]
        add_metric(2, 1, "POOL", pool_short or "—")

        if m.total_acn > 0:
            add_metric(3, 0, "ASICS", str(m.total_acn))
        if m.fan_pwm > 0:
            add_metric(3, 1, "FAN PWM", f"{m.fan_pwm}%")

        layout.addLayout(grid)

        # ── Chain status ──────────────────────────────────────────
        if m.chain_states:
            sep2 = QFrame()
            sep2.setFrameShape(QFrame.Shape.HLine)
            sep2.setStyleSheet("color:#202938;background:#202938;max-height:1px;margin-top:2px;")
            layout.addWidget(sep2)

            chain_row = QHBoxLayout()
            chain_row.setSpacing(4)
            ch_lbl = QLabel("CHAINS:")
            ch_lbl.setStyleSheet("color:#9aa8bd;font-size:10px;background:transparent;")
            chain_row.addWidget(ch_lbl)

            for i, state in enumerate(m.chain_states):
                col = _chain_color(state)
                acn = m.chain_acns[i] if i < len(m.chain_acns) else 0
                chip = m.chain_temps_chip[i] if i < len(m.chain_temps_chip) else 0
                tip_parts = [f"Ch{i+1}: {state}"]
                if acn > 0:
                    tip_parts.append(f"{acn} ASICs")
                if chip > 0:
                    tip_parts.append(f"{chip:.0f}°C")
                ch_dot = QLabel(f"● Ch{i+1}")
                ch_dot.setStyleSheet(f"color:{col};font-size:10px;font-weight:600;background:transparent;")
                ch_dot.setToolTip("  ·  ".join(tip_parts))
                chain_row.addWidget(ch_dot)

            chain_row.addStretch()
            layout.addLayout(chain_row)

            # Show chain faults
            for fault in m.chain_faults_summary():
                fl = QLabel(f"⚠ {fault}")
                fl.setWordWrap(True)
                fl.setStyleSheet("color:#ff6b6b;font-size:10px;background:transparent;margin-left:4px;")
                layout.addWidget(fl)

        # ── Alert messages ────────────────────────────────────────
        non_chain_alerts = [a for a in m.alerts if not a.startswith("Ch")]
        for alert in non_chain_alerts[:2]:
            al = QLabel(f"⚠ {alert}")
            al.setWordWrap(True)
            al.setStyleSheet("color:#f2b84b;font-size:10px;background:transparent;")
            layout.addWidget(al)

        self._update_border(m.status)

    def _open_details(self):
        from .dialogs import MinerDetailsDialog
        dlg = MinerDetailsDialog(self._miner, self, main_win=self._main_win)
        dlg.exec()

    def _update_border(self, status: str):
        self.setProperty("status", status)
        self.style().unpolish(self)
        self.style().polish(self)

    def refresh(self, m: MinerData):
        self._miner = m
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        self._build(m)


_STAT_CHIP_QSS = (
    "QFrame#statChip{background:#111722;border:1px solid #2d3a50;border-radius:8px;padding:4px 12px;}"
)

_BTC_PER_TH_PER_DAY = 9.5e-8  # rough network estimate; updated manually as difficulty changes


def _make_stat_chip(parent=None) -> "tuple[QFrame, QLabel, QLabel]":
    chip = QFrame(parent)
    chip.setObjectName("statChip")
    chip.setStyleSheet(_STAT_CHIP_QSS)
    chip.setMinimumWidth(110)
    vl = QVBoxLayout(chip)
    vl.setContentsMargins(0, 4, 0, 4)
    vl.setSpacing(2)
    key_lbl = QLabel()
    key_lbl.setStyleSheet("color:#9aa8bd;font-size:10px;font-weight:600;background:transparent;")
    key_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    val_lbl = QLabel()
    val_lbl.setStyleSheet("color:#eef4ff;font-size:16px;font-weight:700;background:transparent;")
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    vl.addWidget(key_lbl)
    vl.addWidget(val_lbl)
    return chip, key_lbl, val_lbl


class DashboardPage(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._cards: Dict[str, MinerCard] = {}
        self._btc_price: float = 0.0
        self._setup_ui()

    def set_btc_price(self, price: float):
        self._btc_price = price
        self._update_stats()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("sectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        self._auto_refresh = QCheckBox("Auto")
        self._auto_refresh.setToolTip("Automatically refresh known miners on the configured interval")
        self._auto_refresh.setChecked(getattr(self._main.get_config(), "auto_refresh_enabled", True))
        self._auto_refresh.toggled.connect(self._toggle_auto_refresh)
        title_row.addWidget(self._auto_refresh)

        btn_scan = QPushButton("⟳  Quick Scan")
        btn_scan.setFixedHeight(32)
        btn_scan.clicked.connect(self._scan_now)
        title_row.addWidget(btn_scan)

        btn_full_scan = QPushButton("Full Scan")
        btn_full_scan.setFixedHeight(32)
        btn_full_scan.setToolTip("Scan the configured network range for newly discovered miners")
        btn_full_scan.clicked.connect(self._full_scan_now)
        title_row.addWidget(btn_full_scan)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(32)
        btn_cancel.clicked.connect(self._cancel_scan)
        title_row.addWidget(btn_cancel)

        btn_add = QPushButton("+ Add Miner")
        btn_add.setObjectName("btnPrimary")
        btn_add.setFixedHeight(32)
        btn_add.clicked.connect(self._add_miner)
        title_row.addWidget(btn_add)
        layout.addLayout(title_row)

        # Subtitle / summary
        self._summary_lbl = QLabel("No miners found yet. Add miners or wait for scan.")
        self._summary_lbl.setObjectName("sectionSub")
        layout.addWidget(self._summary_lbl)

        # Fleet stats bar
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        chip_hs, _, self._stat_hs = _make_stat_chip()
        chip_hs.layout().itemAt(0).widget().setText("HASHRATE")
        self._stat_hs.setText("— TH/s")
        self._stat_hs.setStyleSheet(f"color:{BITCOIN_ORANGE};font-size:16px;font-weight:700;background:transparent;")

        chip_pw, _, self._stat_pw = _make_stat_chip()
        chip_pw.layout().itemAt(0).widget().setText("POWER")
        self._stat_pw.setText("— W")
        self._stat_pw.setStyleSheet("color:#68b8ff;font-size:16px;font-weight:700;background:transparent;")

        chip_ef, _, self._stat_ef = _make_stat_chip()
        chip_ef.layout().itemAt(0).widget().setText("EFFICIENCY")
        self._stat_ef.setText("— W/TH")
        self._stat_ef.setStyleSheet("color:#bda8ff;font-size:16px;font-weight:700;background:transparent;")

        chip_rev, _, self._stat_rev = _make_stat_chip()
        chip_rev.layout().itemAt(0).widget().setText("EST. DAILY REV")
        self._stat_rev.setText("—")
        self._stat_rev.setStyleSheet(f"color:#2fbf71;font-size:16px;font-weight:700;background:transparent;")

        chip_on, _, self._stat_on = _make_stat_chip()
        chip_on.layout().itemAt(0).widget().setText("ONLINE")
        self._stat_on.setText("0")
        self._stat_on.setStyleSheet("color:#2fbf71;font-size:16px;font-weight:700;background:transparent;")

        chip_warn, _, self._stat_warn = _make_stat_chip()
        chip_warn.layout().itemAt(0).widget().setText("WARNINGS")
        self._stat_warn.setText("0")
        self._stat_warn.setStyleSheet("color:#f2b84b;font-size:16px;font-weight:700;background:transparent;")

        chip_off, _, self._stat_off = _make_stat_chip()
        chip_off.layout().itemAt(0).widget().setText("OFFLINE")
        self._stat_off.setText("0")
        self._stat_off.setStyleSheet("color:#ff6b6b;font-size:16px;font-weight:700;background:transparent;")

        for chip in [chip_hs, chip_pw, chip_ef, chip_rev, chip_on, chip_warn, chip_off]:
            stats_row.addWidget(chip)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(14)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._grid_container)
        layout.addWidget(scroll, 1)

    def update_miner(self, miner: MinerData):
        if miner.ip in self._cards:
            self._cards[miner.ip].refresh(miner)
        else:
            card = MinerCard(miner, main_win=self._main)
            self._cards[miner.ip] = card
            self._relayout()
        self._update_summary()
        self._update_stats()

    def remove_miner(self, ip: str):
        if ip in self._cards:
            card = self._cards.pop(ip)
            card.deleteLater()
            self._relayout()

    def refresh(self):
        miners = self._main.get_miners()
        for ip, miner in miners.items():
            self.update_miner(miner)

    def _relayout(self):
        while self._grid.count():
            self._grid.takeAt(0)
        # Clear old column stretches
        for c in range(self._grid.columnCount()):
            self._grid.setColumnStretch(c, 0)
        cols = max(1, self._grid_container.width() // 300)
        for i, card in enumerate(self._cards.values()):
            self._grid.addWidget(card, i // cols, i % cols)
        # Cards expand to fill each column equally
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(50, self._relayout)

    def _update_summary(self):
        miners = list(self._main.get_miners().values())
        total = len(miners)
        if total == 0:
            self._summary_lbl.setText("No miners found yet. Add miners or wait for scan.")
            return
        online = sum(1 for m in miners if m.status == "online")
        warning = sum(1 for m in miners if m.status == "warning")
        offline = sum(1 for m in miners if m.status == "offline")
        total_ths = sum(m.best_hashrate() for m in miners if m.status != "offline")
        self._summary_lbl.setText(
            f"{total} miners  ·  {online} online  ·  {warning} warnings  ·  "
            f"{offline} offline  ·  {total_ths:.1f} TH/s total"
        )

    def _update_stats(self):
        miners = list(self._main.get_miners().values())
        active = [m for m in miners if m.status != "offline"]
        total_ths = sum(m.best_hashrate() for m in active)
        total_watts = sum(m.power_watts for m in active if m.power_watts > 0)

        if total_ths >= 1000:
            self._stat_hs.setText(f"{total_ths/1000:.2f} PH/s")
        elif total_ths > 0:
            self._stat_hs.setText(f"{total_ths:.1f} TH/s")
        else:
            self._stat_hs.setText("— TH/s")

        if total_watts >= 1_000_000:
            self._stat_pw.setText(f"{total_watts/1_000_000:.2f} MW")
        elif total_watts >= 1000:
            self._stat_pw.setText(f"{total_watts/1000:.2f} kW")
        elif total_watts > 0:
            self._stat_pw.setText(f"{total_watts:,.0f} W")
        else:
            self._stat_pw.setText("— W")

        if total_ths > 0 and total_watts > 0:
            self._stat_ef.setText(f"{total_watts/total_ths:.1f} W/TH")
        else:
            self._stat_ef.setText("— W/TH")

        if self._btc_price > 0 and total_ths > 0:
            daily_btc = total_ths * _BTC_PER_TH_PER_DAY
            daily_usd = daily_btc * self._btc_price
            self._stat_rev.setText(f"${daily_usd:,.2f}")
        else:
            self._stat_rev.setText("—")

        online = sum(1 for m in miners if m.status == "online")
        warning = sum(1 for m in miners if m.status == "warning")
        offline = sum(1 for m in miners if m.status == "offline")
        self._stat_on.setText(str(online))
        self._stat_warn.setText(str(warning))
        self._stat_off.setText(str(offline))

    def _scan_now(self):
        scanner = self._main.get_scanner()
        scanner.request_scan(full_network=False)
        self._main._status_msg.setText("Quick scan queued...")

    def _full_scan_now(self):
        self._main.get_scanner().request_scan(full_network=True)
        self._main._status_msg.setText("Full network scan queued...")

    def _cancel_scan(self):
        self._main.get_scanner().cancel_scan()

    def _toggle_auto_refresh(self, checked: bool):
        cfg = self._main.get_config()
        cfg.auto_refresh_enabled = checked
        cfg.save()
        self._main.reload_config()
        self._main._status_msg.setText("Auto-refresh enabled" if checked else "Auto-refresh paused")

    def _add_miner(self):
        from .dialogs import AddMinerDialog
        dlg = AddMinerDialog(self._main, self)
        if dlg.exec():
            ip, port, name, min_ths, notes, group_id = dlg.result_data()
            self._main.add_miner_to_watch(ip, port, name, min_ths, notes, group_id)
