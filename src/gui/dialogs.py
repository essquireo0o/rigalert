import threading
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialogButtonBox, QDialog, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPlainTextEdit, QProgressBar, QPushButton, QRadioButton, QScrollArea, QSpinBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from ..core.miner import MinerData
from ..core.scanner import MinerScanner


# ── Miner Details Dialog ───────────────────────────────────────────────────

class MinerDetailsDialog(QDialog):
    _CHAIN_COLORS = {
        "running": "#3fb950", "normal": "#3fb950", "active": "#3fb950", "mining": "#3fb950",
        "stopped": "#d29922", "idle": "#d29922",
        "auto-tuning": "#58a6ff", "disabled": "#8b949e",
        "failure": "#f85149", "dead": "#f85149", "error": "#f85149",
    }

    def __init__(self, miner: MinerData, parent=None, main_win=None):
        super().__init__(parent)
        self._m = miner
        self._main_win = main_win
        self._chain_status_lbl: Optional[QLabel] = None
        self.setWindowTitle(f"Miner Details — {miner.ip}")
        self.setMinimumWidth(760)
        self.setMinimumHeight(560)
        self._build()

    def _section(self, title: str) -> QGroupBox:
        gb = QGroupBox(title)
        gb.setStyleSheet(
            "QGroupBox{border:1px solid #30363d;border-radius:6px;margin-top:10px;"
            "padding:10px;background:#161b22;color:#e6edf3;font-weight:700;}"
            "QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;"
            "background:#161b22;color:#c8a94b;}"
        )
        return gb

    def _row(self, form: QFormLayout, label: str, value: str, val_color: str = "#e6edf3"):
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        val = QLabel(value or "—")
        val.setStyleSheet(f"color:{val_color};font-size:12px;background:transparent;font-family:Consolas,monospace;")
        val.setWordWrap(True)
        form.addRow(lbl, val)

    def _build(self):
        m = self._m

        outer = QVBoxLayout(self)
        outer.setSpacing(8)
        outer.setContentsMargins(12, 12, 12, 12)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#0d1117;}")
        content = QWidget()
        content.setStyleSheet("background:#0d1117;")
        vbox = QVBoxLayout(content)
        vbox.setSpacing(8)
        vbox.setContentsMargins(4, 4, 4, 4)

        # ── Hardware Info ──────────────────────────────────────────
        hw = self._section("Hardware")
        hf = QFormLayout(hw)
        hf.setSpacing(6)
        hf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._row(hf, "Model:", m.model or "Unknown")
        self._row(hf, "Firmware:", m.firmware)
        self._row(hf, "IP Address:", f"{m.ip}:{m.port}")
        self._row(hf, "Status:", m.status.upper(),
                  "#3fb950" if m.status == "online" else "#f85149" if m.status == "offline" else "#d29922")
        if m.miner_state:
            state_col = self._CHAIN_COLORS.get(m.miner_state.lower(), "#8b949e")
            self._row(hf, "Miner State:", m.miner_state, state_col)
        if m.total_acn > 0:
            self._row(hf, "Total ASICs:", str(m.total_acn))
        self._row(hf, "Uptime:", m.display_uptime())
        vbox.addWidget(hw)

        # ── Chain Status ───────────────────────────────────────────
        if m.chain_states:
            ch_box = self._section(f"Chain Status  ({len(m.chain_states)} chains)")
            ch_vbox = QVBoxLayout(ch_box)
            ch_vbox.setSpacing(6)

            # Data table (9 columns — no Action column so it fits without scrolling)
            tbl = QTableWidget(len(m.chain_states), 9)
            tbl.setHorizontalHeaderLabels(
                ["Chain", "State", "Fault", "Rate (TH/s)", "Ideal (TH/s)",
                 "Chip °C", "PCB °C", "Freq (MHz)", "ASICs"]
            )
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setAlternatingRowColors(True)
            tbl.setStyleSheet(
                "QTableWidget{background:#0d1117;color:#e6edf3;gridline-color:#21262d;"
                "border:none;font-size:12px;font-family:Consolas,monospace;}"
                "QTableWidget::item{padding:4px 6px;}"
                "QHeaderView::section{background:#161b22;color:#8b949e;border:none;"
                "border-bottom:1px solid #30363d;padding:4px 6px;font-size:11px;}"
                "QTableWidget::item:alternate{background:#0d1117;}"
                "QTableWidget::item:!alternate{background:#161b22;}"
            )
            tbl.horizontalHeader().setStretchLastSection(True)

            def _ti(text: str, color: str = "#e6edf3") -> QTableWidgetItem:
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                return item

            for i, state in enumerate(m.chain_states):
                col = self._CHAIN_COLORS.get(state.lower(), "#8b949e")
                rate  = m.chain_rates[i]       if i < len(m.chain_rates)       else 0.0
                ideal = m.chain_ideal_rates[i] if i < len(m.chain_ideal_rates) else 0.0
                chip  = m.chain_temps_chip[i]  if i < len(m.chain_temps_chip)  else 0.0
                pcb   = m.chain_temps_pcb[i]   if i < len(m.chain_temps_pcb)   else 0.0
                freq  = m.chain_freqs[i]        if i < len(m.chain_freqs)       else 0.0
                acn   = m.chain_acns[i]         if i < len(m.chain_acns)        else 0
                fault = m.chain_faults[i]       if i < len(m.chain_faults)      else ""

                tbl.setItem(i, 0, _ti(f"  Chain {i+1}"))
                tbl.setItem(i, 1, _ti(f"  {state}", col))
                tbl.setItem(i, 2, _ti(f"  {fault}", "#f85149" if fault else "#8b949e"))
                tbl.setItem(i, 3, _ti(f"  {rate:.4f}"  if rate  > 0 else "  0"))
                tbl.setItem(i, 4, _ti(f"  {ideal:.4f}" if ideal > 0 else "  0"))
                tbl.setItem(i, 5, _ti(f"  {chip:.1f}"  if chip  > 0 else "  —"))
                tbl.setItem(i, 6, _ti(f"  {pcb:.1f}"   if pcb   > 0 else "  —"))
                tbl.setItem(i, 7, _ti(f"  {freq:.0f}"  if freq  > 0 else "  —"))
                tbl.setItem(i, 8, _ti(f"  {acn}"       if acn   > 0 else "  —"))
                tbl.setRowHeight(i, 32)

            tbl.resizeColumnsToContents()
            tbl.setMinimumHeight(len(m.chain_states) * 34 + 36)
            ch_vbox.addWidget(tbl)

            # ── Board control buttons (always visible below the table) ──────
            # Board control note + open-in-browser button
            note = QLabel(
                "VNISH board enable/disable requires the web UI.  "
                "Click below to open it in Chrome with auto-unlock:"
            )
            note.setStyleSheet("color:#8b949e;font-size:11px;background:transparent;")
            note.setWordWrap(True)
            ch_vbox.addWidget(note)

            ctrl_row = QHBoxLayout()
            ctrl_row.setSpacing(8)

            btn_open = QPushButton("Open Board Settings in Chrome")
            btn_open.setFixedHeight(34)
            btn_open.setStyleSheet(
                "QPushButton{background:#1a2a3a;color:#58a6ff;border:1px solid #1f6feb;"
                "border-radius:4px;padding:4px 16px;font-size:12px;font-weight:600;}"
                "QPushButton:hover{background:#1f4068;}"
            )

            def _open_chrome():
                import os, subprocess
                web_user, web_pwd = "root", "admin"
                if self._main_win and hasattr(self._main_win, "get_config"):
                    cfg = self._main_win.get_config()
                    web_user = cfg.miner_web_user or "root"
                    web_pwd  = cfg.miner_web_password or "admin"
                url = f"http://{m.ip}"
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                ]
                launched = False
                for path in chrome_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path, url])
                        launched = True
                        break
                if not launched:
                    subprocess.Popen(["start", "chrome", url], shell=True)
                # Trigger auto-unlock
                from ..gui.miners_page import _auto_unlock_vnish
                threading.Thread(
                    target=_auto_unlock_vnish, args=(web_pwd,), daemon=True
                ).start()

            btn_open.clicked.connect(_open_chrome)
            ctrl_row.addWidget(btn_open)
            ctrl_row.addStretch()
            ch_vbox.addLayout(ctrl_row)
            vbox.addWidget(ch_box)

        # ── Temperature ────────────────────────────────────────────
        temp_box = self._section("Temperature")
        tf = QFormLayout(temp_box)
        tf.setSpacing(6)
        tf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._row(tf, "Chip Max:", m.display_temp())
        if m.temp_inlet > 0:
            self._row(tf, "Inlet:", f"{m.temp_inlet:.1f}°C")
        if m.temp_outlet > 0:
            self._row(tf, "Outlet:", f"{m.temp_outlet:.1f}°C")
        if m.chain_temps_chip:
            chip_vals = [f"Ch{i+1}: {t:.1f}°C" if t > 0 else f"Ch{i+1}: —"
                         for i, t in enumerate(m.chain_temps_chip)]
            self._row(tf, "Per-Chain Chip:", "   ".join(chip_vals))
        if m.chain_temps_pcb:
            pcb_vals = [f"Ch{i+1}: {t:.1f}°C" if t > 0 else f"Ch{i+1}: —"
                        for i, t in enumerate(m.chain_temps_pcb)]
            self._row(tf, "Per-Chain PCB:", "   ".join(pcb_vals))
        vbox.addWidget(temp_box)

        # ── Fans ───────────────────────────────────────────────────
        fan_box = self._section("Fans")
        ff = QFormLayout(fan_box)
        ff.setSpacing(6)
        ff.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        if m.fan_speeds:
            for i, rpm in enumerate(m.fan_speeds):
                self._row(ff, f"Fan {i+1}:", f"{rpm:,} RPM" if rpm > 0 else "—")
        elif not m.fan_speeds:
            self._row(ff, "Fan Speeds:", "No data")
        if m.fan_pwm > 0:
            self._row(ff, "Fan PWM:", f"{m.fan_pwm}%")
        if m.fan_pcts:
            self._row(ff, "Fan %:", "  ".join(f"{p}%" for p in m.fan_pcts))
        vbox.addWidget(fan_box)

        # ── Hashrate ───────────────────────────────────────────────
        hr_box = self._section("Hashrate")
        hrf = QFormLayout(hr_box)
        hrf.setSpacing(6)
        hrf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._row(hrf, "5s:", m.display_hashrate() if m.hashrate_5s > 0 else "0 TH/s")
        if m.hashrate_1m > 0:
            self._row(hrf, "1m:", f"{m.hashrate_1m:.4f} TH/s")
        if m.hashrate_5m > 0:
            self._row(hrf, "5m:", f"{m.hashrate_5m:.4f} TH/s")
        if m.hashrate_15m > 0:
            self._row(hrf, "15m:", f"{m.hashrate_15m:.4f} TH/s")
        if m.hashrate_ideal > 0:
            self._row(hrf, "Expected:", f"{m.hashrate_ideal:.1f} TH/s")
        if m.chain_rates:
            chain_rate_strs = [f"Ch{i+1}: {r:.4f}" if r > 0 else f"Ch{i+1}: 0"
                               for i, r in enumerate(m.chain_rates)]
            self._row(hrf, "Per-Chain (TH/s):", "   ".join(chain_rate_strs))
        if m.chain_freqs and any(f > 0 for f in m.chain_freqs):
            freq_strs = [f"Ch{i+1}: {f:.0f}MHz" if f > 0 else f"Ch{i+1}: —"
                         for i, f in enumerate(m.chain_freqs)]
            self._row(hrf, "Frequency:", "   ".join(freq_strs))
        vbox.addWidget(hr_box)

        # ── Pool Info ──────────────────────────────────────────────
        pool_box = self._section("Pool Configuration")
        pf = QFormLayout(pool_box)
        pf.setSpacing(6)
        pf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        if m.all_pools:
            for i, pool in enumerate(m.all_pools):
                label = f"Pool {pool.get('priority', i)+1}:"
                url = pool.get("url", "")
                user = pool.get("user", "")
                status = pool.get("status", "")
                accepted = pool.get("accepted", 0)
                diff = pool.get("diff", "")
                parts = [url]
                if user:
                    parts.append(f"user: {user}")
                if status:
                    scol = "#3fb950" if "alive" in status.lower() else "#f85149"
                    self._row(pf, label, f"{url}  |  {user}", "#e6edf3")
                    self._row(pf, "   Status:", status, scol)
                    if diff:
                        self._row(pf, "   Difficulty:", diff)
                    self._row(pf, "   Accepted:", f"{accepted:,}")
                else:
                    self._row(pf, label, "  ".join(parts))
        else:
            self._row(pf, "Primary Pool:", m.pool_url)
            self._row(pf, "User:", m.pool_user)
            self._row(pf, "Status:", m.pool_status)
        vbox.addWidget(pool_box)

        # ── Share Statistics ───────────────────────────────────────
        stats_box = self._section("Share Statistics")
        sf = QFormLayout(stats_box)
        sf.setSpacing(6)
        sf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._row(sf, "Accepted:", f"{m.accepted:,}")
        self._row(sf, "Rejected:", f"{m.rejected:,}")
        self._row(sf, "HW Errors:", f"{m.hw_errors:,}")
        hw_col = "#f85149" if m.hw_error_rate >= 1.0 else "#d29922" if m.hw_error_rate >= 0.1 else "#e6edf3"
        self._row(sf, "HW Error Rate:", f"{m.hw_error_rate:.4f}%", hw_col)
        if m.chain_acns and any(a > 0 for a in m.chain_acns):
            acn_strs = [f"Ch{i+1}: {a}" for i, a in enumerate(m.chain_acns)]
            self._row(sf, "ASICs per Chain:", "   ".join(acn_strs))
        vbox.addWidget(stats_box)

        vbox.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        outer.addLayout(btn_row)


class AddMinerDialog(QDialog):
    def __init__(self, main_win, parent=None, existing: Optional[dict] = None):
        super().__init__(parent)
        self._main = main_win
        self._existing = existing
        self._result = None
        self.setWindowTitle("Add Miner" if not existing else "Edit Miner")
        self.setFixedWidth(400)
        self._build()
        if existing:
            self._load(existing)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self._ip = QLineEdit()
        self._ip.setPlaceholderText("192.168.1.100")
        form.addRow("IP Address:", self._ip)

        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(4028)
        form.addRow("API Port:", self._port)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Optional display name")
        form.addRow("Name:", self._name)

        self._min_ths = QDoubleSpinBox()
        self._min_ths.setRange(0, 99999)
        self._min_ths.setDecimals(1)
        self._min_ths.setSuffix(" TH/s")
        cfg = self._main.get_config()
        self._min_ths.setValue(cfg.default_min_ths)
        form.addRow("Min Hashrate:", self._min_ths)

        self._notes = QPlainTextEdit()
        self._notes.setPlaceholderText("Optional notes (location, serial number, etc.)")
        self._notes.setFixedHeight(64)
        form.addRow("Notes:", self._notes)

        self._group = QComboBox()
        self._group.addItem("— No group —", None)
        for g in self._main.get_db().get_groups():
            self._group.addItem(g["name"], g["id"])
        form.addRow("Group:", self._group)

        layout.addLayout(form)

        # Test connection
        test_row = QHBoxLayout()
        btn_test = QPushButton("Test Connection")
        btn_test.clicked.connect(self._test_connection)
        self._test_lbl = QLabel("")
        self._test_lbl.setStyleSheet("font-size:12px;background:transparent;")
        test_row.addWidget(btn_test)
        test_row.addWidget(self._test_lbl, 1)
        layout.addLayout(test_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, d: dict):
        self._ip.setText(d.get("ip", ""))
        self._port.setValue(d.get("port", 4028))
        self._name.setText(d.get("name", ""))
        self._min_ths.setValue(d.get("min_ths", self._main.get_config().default_min_ths))
        self._notes.setPlainText(d.get("notes", ""))
        gid = d.get("group_id")
        if gid is not None:
            idx = self._group.findData(gid)
            if idx >= 0:
                self._group.setCurrentIndex(idx)

    def _test_connection(self):
        ip = self._ip.text().strip()
        port = self._port.value()
        if not ip:
            self._test_lbl.setText("Enter an IP first")
            self._test_lbl.setStyleSheet("color:#d29922;font-size:12px;background:transparent;")
            return

        self._test_lbl.setText("Connecting...")
        self._test_lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")

        from ..core.cgminer_api import CGMinerAPI
        cfg = self._main.get_config()

        def probe():
            api = CGMinerAPI(ip, port, cfg.connection_timeout)
            raw = api.fetch_all()
            return bool(raw)

        def done(ok):
            if ok:
                self._test_lbl.setText("Connected!")
                self._test_lbl.setStyleSheet("color:#3fb950;font-size:12px;background:transparent;")
            else:
                self._test_lbl.setText("No response")
                self._test_lbl.setStyleSheet("color:#f85149;font-size:12px;background:transparent;")

        def run():
            ok = probe()
            # Use Qt-safe callback
            from PyQt6.QtCore import QMetaObject, Q_ARG
            done(ok)

        threading.Thread(target=run, daemon=True).start()

    def result_data(self) -> Tuple[str, int, str, float, str, object]:
        return (
            self._ip.text().strip(),
            self._port.value(),
            self._name.text().strip(),
            self._min_ths.value(),
            self._notes.toPlainText().strip(),
            self._group.currentData(),
        )


class _ScanWorker(QThread):
    found = pyqtSignal(object)
    finished = pyqtSignal()
    progress = pyqtSignal(object)

    def __init__(self, scanner: MinerScanner, start_ip: str, end_ip: str,
                 port: int, timeout: float, parent=None):
        super().__init__(parent)
        self._scanner = scanner
        self._start_ip = start_ip
        self._end_ip = end_ip
        self._port = port
        self._timeout = timeout
        self._results: List[MinerData] = []
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        results = self._scanner.scan_network_once(
            self._start_ip, self._end_ip, self._port, self._timeout, max_workers=100,
            progress_callback=self.progress.emit,
            cancel_callback=lambda: self._cancelled,
        )
        for m in results:
            self.found.emit(m)
        self.finished.emit()

    def get_results(self) -> List[MinerData]:
        return self._results


class ScanNetworkDialog(QDialog):
    def __init__(self, main_win, config, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._config = config
        self._found: List[MinerData] = []
        self._worker: Optional[_ScanWorker] = None
        self.setWindowTitle("Scan Network for Miners")
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self._start = QLineEdit(self._config.start_ip)
        self._end = QLineEdit(self._config.end_ip)
        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(self._config.miner_port)

        form.addRow("Start IP:", self._start)
        form.addRow("End IP:", self._end)
        form.addRow("Port:", self._port)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self._btn_scan = QPushButton("Start Scan")
        self._btn_scan.setObjectName("btnPrimary")
        self._btn_scan.clicked.connect(self._start_scan)
        btn_row.addWidget(self._btn_scan)

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setFixedWidth(90)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(self._cancel_scan)
        btn_row.addWidget(self._btn_cancel)

        self._scan_lbl = QLabel("")
        self._scan_lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        btn_row.addWidget(self._scan_lbl, 1)
        layout.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setMaximumHeight(6)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        layout.addWidget(QLabel("Discovered Miners:"))

        self._list = QListWidget()
        self._list.setStyleSheet("background:#161b22;border:1px solid #30363d;border-radius:6px;")
        layout.addWidget(self._list, 1)

        self._select_all = QPushButton("Select All")
        self._select_all.clicked.connect(self._toggle_all)
        layout.addWidget(self._select_all)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Add Selected")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _start_scan(self):
        self._found.clear()
        self._list.clear()
        self._progress.setVisible(True)
        self._btn_scan.setEnabled(False)
        self._btn_cancel.setEnabled(True)
        self._scan_lbl.setText("Scanning...")

        self._worker = _ScanWorker(
            self._main.get_scanner(),
            self._start.text().strip(),
            self._end.text().strip(),
            self._port.value(),
            self._config.connection_timeout,
            self,
        )
        self._worker.found.connect(self._on_found)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _cancel_scan(self):
        if self._worker:
            self._worker.cancel()
            self._scan_lbl.setText("Cancelling scan...")
        self._btn_cancel.setEnabled(False)

    def _on_progress(self, progress: dict):
        completed = int(progress.get("completed") or 0)
        total = int(progress.get("total") or 0)
        found = int(progress.get("found") or 0)
        elapsed = float(progress.get("elapsed") or 0)
        ip = progress.get("ip") or ""
        phase = progress.get("phase", "scan")
        if total > 0:
            self._progress.setRange(0, total)
            self._progress.setValue(min(completed, total))
        self._scan_lbl.setText(f"{phase.title()} {completed}/{total}  ·  {found} found  ·  {elapsed:.1f}s  ·  {ip}")

    def _on_found(self, miner: MinerData):
        self._found.append(miner)
        item = QListWidgetItem(f"  {miner.ip}:{miner.port}  —  {miner.display_hashrate()}")
        item.setCheckState(Qt.CheckState.Checked)
        item.setData(Qt.ItemDataRole.UserRole, miner.ip)
        self._list.addItem(item)
        self._scan_lbl.setText(f"Found {len(self._found)} miners...")

    def _on_done(self):
        self._progress.setVisible(False)
        self._btn_scan.setEnabled(True)
        self._btn_cancel.setEnabled(False)
        self._scan_lbl.setText(f"Scan complete — {len(self._found)} miners found")

    def _toggle_all(self):
        all_checked = all(
            self._list.item(i).checkState() == Qt.CheckState.Checked
            for i in range(self._list.count())
        )
        state = Qt.CheckState.Unchecked if all_checked else Qt.CheckState.Checked
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(state)

    def selected_miners(self) -> List[MinerData]:
        selected_ips = set()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_ips.add(item.data(Qt.ItemDataRole.UserRole))
        return [m for m in self._found if m.ip in selected_ips]


# ── Change Pool Dialog ─────────────────────────────────────────────────────

class ChangePoolDialog(QDialog):
    """Let the user set up to 3 pools and push them to one or all miners."""

    def __init__(self, main_win, target_ip: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._target_ip = target_ip   # None = apply to all miners
        self.setWindowTitle("Change Pool Configuration")
        self.setMinimumWidth(640)
        self.setMinimumHeight(500)
        self._build()
        self._prefill()

    # ── Build UI ───────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setSpacing(0)
        outer.setContentsMargins(0, 0, 0, 0)

        # Scroll area wraps everything except the bottom button row
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#0d1117;}")
        outer.addWidget(scroll, 1)

        content = QWidget()
        content.setStyleSheet("background:#0d1117;")
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Scope selector
        scope_box = QGroupBox("Apply To")
        scope_box.setStyleSheet(
            "QGroupBox{border:1px solid #30363d;border-radius:6px;margin-top:10px;"
            "padding:10px;background:#161b22;}"
            "QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;"
            "background:#161b22;color:#c8a94b;font-weight:700;}"
        )
        sr = QHBoxLayout(scope_box)
        self._rb_one = QRadioButton(
            f"This miner only  ({self._target_ip})" if self._target_ip else "This miner only"
        )
        self._rb_all = QRadioButton("ALL miners currently monitored")
        self._rb_one.setStyleSheet("color:#e6edf3;")
        self._rb_all.setStyleSheet("color:#e6edf3;")

        if self._target_ip:
            self._rb_one.setChecked(True)
        else:
            self._rb_all.setChecked(True)
            self._rb_one.setEnabled(False)

        sr.addWidget(self._rb_one)
        sr.addWidget(self._rb_all)
        sr.addStretch()
        layout.addWidget(scope_box)

        # Pool rows
        pools_box = QGroupBox("Pool Configuration")
        pools_box.setStyleSheet(
            "QGroupBox{border:1px solid #30363d;border-radius:6px;margin-top:10px;"
            "padding:12px;background:#161b22;}"
            "QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;"
            "background:#161b22;color:#c8a94b;font-weight:700;}"
        )
        pf = QVBoxLayout(pools_box)
        pf.setSpacing(14)

        self._pool_rows = []
        labels = ["Pool 1  (primary)", "Pool 2  (backup, optional)", "Pool 3  (backup, optional)"]
        for i, lbl in enumerate(labels):
            grp = QGroupBox(lbl)
            grp.setStyleSheet(
                "QGroupBox{border:1px solid #21262d;border-radius:4px;margin-top:8px;"
                "padding:8px;background:#0d1117;}"
                "QGroupBox::title{subcontrol-origin:margin;left:6px;padding:0 4px;"
                "background:#0d1117;color:#8b949e;font-size:11px;}"
            )
            gf = QFormLayout(grp)
            gf.setSpacing(6)
            gf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

            url_edit = QLineEdit()
            url_edit.setPlaceholderText("stratum+tcp://pool.example.com:3333")
            url_edit.setMinimumWidth(340)
            gf.addRow("URL:", url_edit)

            worker_edit = QLineEdit()
            worker_edit.setPlaceholderText("wallet.worker1")
            gf.addRow("Worker:", worker_edit)

            pwd_edit = QLineEdit()
            pwd_edit.setPlaceholderText("x")
            pwd_edit.setText("x")
            gf.addRow("Password:", pwd_edit)

            pf.addWidget(grp)
            self._pool_rows.append((url_edit, worker_edit, pwd_edit))

        layout.addWidget(pools_box)

        # Result log
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFixedHeight(90)
        self._log.setStyleSheet(
            "QTextEdit{background:#0d1117;border:1px solid #30363d;border-radius:4px;"
            "color:#8b949e;font-family:Consolas,monospace;font-size:11px;}"
        )
        self._log.setPlaceholderText("Results will appear here after applying...")
        layout.addWidget(self._log)

        # Buttons — outside scroll area so always visible
        btn_widget = QWidget()
        btn_widget.setStyleSheet("background:#0d1117;border-top:1px solid #21262d;")
        btn_row = QHBoxLayout(btn_widget)
        btn_row.setContentsMargins(20, 10, 20, 10)
        self._btn_apply = QPushButton("Apply Pool Changes")
        self._btn_apply.setObjectName("btnPrimary")
        self._btn_apply.setFixedHeight(36)
        self._btn_apply.setFixedWidth(200)
        self._btn_apply.clicked.connect(self._apply)

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(36)
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(self._btn_apply)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        outer.addWidget(btn_widget)

    # ── Pre-fill with current pool data for the target miner ──────────────

    def _prefill(self):
        if not self._target_ip:
            return
        miner = self._main.get_scanner().get_miner(self._target_ip)
        if not miner:
            return
        # Fill pool 1 from the miner's current known pool
        if miner.pool_url:
            self._pool_rows[0][0].setText(miner.pool_url)
        if miner.pool_user:
            self._pool_rows[0][1].setText(miner.pool_user)
        # Fill all three from all_pools if available
        for i, pool in enumerate(miner.all_pools[:3]):
            self._pool_rows[i][0].setText(pool.get("url", ""))
            self._pool_rows[i][1].setText(pool.get("user", ""))
            pwd = pool.get("diff", "")   # some firmware stores pass here
            self._pool_rows[i][2].setText(pwd or "x")

    # ── Collect pool entries from form ─────────────────────────────────────

    def _get_pools(self) -> List[dict]:
        pools = []
        for url_e, worker_e, pwd_e in self._pool_rows:
            url = url_e.text().strip()
            if url:
                pools.append({
                    "url": url,
                    "user": worker_e.text().strip(),
                    "password": pwd_e.text().strip() or "x",
                })
        return pools

    # ── Apply ──────────────────────────────────────────────────────────────

    def _apply(self):
        pools = self._get_pools()
        if not pools:
            self._log.setHtml('<span style="color:#f85149">Enter at least one pool URL.</span>')
            return

        cfg = self._main.get_config()
        if self._rb_all.isChecked():
            targets = list(self._main.get_miners().values())
        elif self._target_ip:
            m = self._main.get_scanner().get_miner(self._target_ip)
            targets = [m] if m else []
        else:
            targets = []

        if not targets:
            self._log.setHtml('<span style="color:#f85149">No miners to apply to.</span>')
            return

        self._btn_apply.setEnabled(False)
        self._log.clear()
        self._log.append(f"Applying to {len(targets)} miner(s)...\n")

        def run():
            from ..core.cgminer_api import CGMinerAPI
            results = []
            for miner in targets:
                api = CGMinerAPI(miner.ip, miner.port, cfg.connection_timeout)
                ok, msg = api.change_pools(pools)
                results.append((miner.ip, ok, msg))

            # Update UI from main thread
            from PyQt6.QtCore import QMetaObject, Q_ARG
            lines = []
            for ip, ok, msg in results:
                color = "#3fb950" if ok else "#f85149"
                icon  = "✓" if ok else "✗"
                lines.append(f'<span style="color:{color}">{icon} {ip}: {msg}</span>')
            html = "<br>".join(lines)

            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._finish(html))

        threading.Thread(target=run, daemon=True).start()

    def _finish(self, html: str):
        self._log.setHtml(html)
        self._btn_apply.setEnabled(True)
