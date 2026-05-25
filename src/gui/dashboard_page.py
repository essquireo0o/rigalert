from typing import Dict, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ..core.miner import MinerData
from .theme import STATUS_COLORS, BITCOIN_ORANGE, BG_CARD, TEXT_MUTED, BORDER_COLOR

_CHAIN_COLORS = {
    "running":      "#3fb950",
    "normal":       "#3fb950",
    "active":       "#3fb950",
    "mining":       "#3fb950",
    "stopped":      "#d29922",
    "idle":         "#d29922",
    "auto-tuning":  "#58a6ff",
    "disabled":     "#8b949e",
    "failure":      "#f85149",
    "dead":         "#f85149",
    "error":        "#f85149",
}


def _chain_color(state: str) -> str:
    return _CHAIN_COLORS.get(state.lower(), "#8b949e")


class MinerCard(QFrame):
    def __init__(self, miner: MinerData, parent=None):
        super().__init__(parent)
        self.setObjectName("minerCard")
        self.setFixedWidth(320)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self._miner = miner
        self._build(miner)

    def _build(self, m: MinerData):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # ── Header ────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(6)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{STATUS_COLORS.get(m.status, '#8b949e')};font-size:10px;background:transparent;")
        header.addWidget(dot)

        name = QLabel(m.display_name)
        name.setObjectName("cardName")
        name.setStyleSheet("font-size:13px;font-weight:700;color:#e6edf3;background:transparent;")
        header.addWidget(name, 1)

        bc = STATUS_COLORS.get(m.status, "#8b949e")
        if m.status == "online":
            bs = "background:#238636;color:#aff5b4;"
        elif m.status == "warning":
            bs = "background:#9e6a03;color:#fae17d;"
        elif m.status == "offline":
            bs = "background:#da3633;color:#ffdcd7;"
        else:
            bs = "background:#30363d;color:#8b949e;"
        badge = QLabel(m.status.upper())
        badge.setStyleSheet(f"{bs}font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;")
        header.addWidget(badge)
        layout.addLayout(header)

        # IP + port (clickable — opens miner web UI in browser)
        ip_lbl = QLabel(f'<a href="http://{m.ip}" style="color:#8b949e;text-decoration:none;">'
                        f'{m.ip}:{m.port}</a>')
        ip_lbl.setOpenExternalLinks(True)
        ip_lbl.setStyleSheet("font-size:11px;font-family:Consolas,monospace;background:transparent;")
        ip_lbl.setToolTip(f"Click to open http://{m.ip} in browser")
        layout.addWidget(ip_lbl)

        # Model name
        if m.model:
            mdl = QLabel(m.model)
            mdl.setStyleSheet(f"color:{BITCOIN_ORANGE};font-size:11px;font-weight:600;background:transparent;")
            mdl.setWordWrap(True)
            layout.addWidget(mdl)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#21262d;background:#21262d;max-height:1px;")
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
        hr_unit.setStyleSheet("font-size:11px;color:#8b949e;padding-bottom:4px;background:transparent;")
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
        bar_color = "#3fb950" if pct >= 95 else "#d29922" if pct >= 80 else "#f85149"
        hr_bar.setStyleSheet(
            f"QProgressBar{{background:#21262d;border:none;border-radius:3px;height:5px;}}"
            f"QProgressBar::chunk{{background:{bar_color};border-radius:3px;}}"
        )
        layout.addWidget(hr_bar)

        # ── Metrics grid ──────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setContentsMargins(0, 4, 0, 0)

        def add_metric(row, col, key, val, val_color="#e6edf3"):
            k = QLabel(key)
            k.setStyleSheet("color:#8b949e;font-size:10px;background:transparent;")
            v = QLabel(val)
            v.setStyleSheet(f"color:{val_color};font-size:11px;font-weight:500;background:transparent;")
            grid.addWidget(k, row, col * 2)
            grid.addWidget(v, row, col * 2 + 1)

        temp = m.display_temp()
        temp_color = (STATUS_COLORS.get(m.temp_level(75, 85), "#e6edf3")
                      if temp != "N/A" else "#8b949e")

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
                   "#f85149" if m.hw_error_rate >= 1.0 else "#e6edf3")
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
            sep2.setStyleSheet("color:#21262d;background:#21262d;max-height:1px;margin-top:2px;")
            layout.addWidget(sep2)

            chain_row = QHBoxLayout()
            chain_row.setSpacing(4)
            ch_lbl = QLabel("CHAINS:")
            ch_lbl.setStyleSheet("color:#8b949e;font-size:10px;background:transparent;")
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
                fl.setStyleSheet("color:#f85149;font-size:10px;background:transparent;margin-left:4px;")
                layout.addWidget(fl)

        # ── Alert messages ────────────────────────────────────────
        non_chain_alerts = [a for a in m.alerts if not a.startswith("Ch")]
        for alert in non_chain_alerts[:2]:
            al = QLabel(f"⚠ {alert}")
            al.setWordWrap(True)
            al.setStyleSheet("color:#d29922;font-size:10px;background:transparent;")
            layout.addWidget(al)

        # ── Details button ────────────────────────────────────────
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("color:#21262d;background:#21262d;max-height:1px;margin-top:2px;")
        layout.addWidget(sep3)

        btn_details = QPushButton("Details")
        btn_details.setFixedHeight(24)
        btn_details.setStyleSheet(
            "QPushButton{background:#21262d;color:#8b949e;border:1px solid #30363d;"
            "border-radius:4px;font-size:11px;padding:0 10px;}"
            "QPushButton:hover{background:#30363d;color:#e6edf3;}"
        )
        btn_details.clicked.connect(self._open_details)
        layout.addWidget(btn_details)

        self._update_border(m.status)

    def _open_details(self):
        from .dialogs import MinerDetailsDialog
        dlg = MinerDetailsDialog(self._miner, self)
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


class DashboardPage(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._cards: Dict[str, MinerCard] = {}
        self._setup_ui()

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

        btn_scan = QPushButton("⟳  Scan Now")
        btn_scan.setFixedHeight(32)
        btn_scan.clicked.connect(self._scan_now)
        title_row.addWidget(btn_scan)

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

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(12)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._grid_container)
        layout.addWidget(scroll, 1)

    def update_miner(self, miner: MinerData):
        if miner.ip in self._cards:
            self._cards[miner.ip].refresh(miner)
        else:
            card = MinerCard(miner)
            self._cards[miner.ip] = card
            self._relayout()
        self._update_summary()

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
        cols = max(1, self._grid_container.width() // 336)
        for i, card in enumerate(self._cards.values()):
            self._grid.addWidget(card, i // cols, i % cols)

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

    def _scan_now(self):
        scanner = self._main.get_scanner()
        scanner.stop()
        scanner.wait(500)
        scanner.start()

    def _add_miner(self):
        from .dialogs import AddMinerDialog
        dlg = AddMinerDialog(self._main, self)
        if dlg.exec():
            ip, port, name, min_ths, notes = dlg.result_data()
            self._main.add_miner_to_watch(ip, port, name, min_ths, notes)
