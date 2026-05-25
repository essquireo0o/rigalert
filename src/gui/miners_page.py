import ctypes
import ctypes.wintypes
import time
from datetime import datetime
from typing import Dict

from PyQt6.QtCore import Qt, QSortFilterProxyModel, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core.miner import MinerData
from .theme import STATUS_COLORS, BITCOIN_ORANGE


def _auto_unlock_vnish(password: str):
    """Wait for Chrome to load, find the gold VNISH Unlock button by color, click it, type password."""
    time.sleep(2.8)
    try:
        from PIL import ImageGrab

        # Get the foreground window (Chrome that just opened)
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        wl, wt, wr, wb = rect.left, rect.top, rect.right, rect.bottom
        win_w = wr - wl
        win_h = wb - wt

        # Search top-right 35% of window for the gold Unlock button
        sx, sy = wl + win_w * 6 // 10, wt
        ex, ey = wr, wt + win_h // 4
        shot = ImageGrab.grab(bbox=(sx, sy, ex, ey))
        data = list(shot.getdata())
        sw = ex - sx

        gxs, gys = [], []
        for i in range(0, len(data), 3):
            px = data[i]
            r, g, b = px[0], px[1], px[2]
            # Gold/amber VNISH button: high red, mid-high green, very low blue
            if r > 185 and 130 <= g <= 215 and b < 65:
                gxs.append(sx + (i % sw))
                gys.append(sy + (i // sw))

        if len(gxs) >= 12:
            cx = sum(gxs) // len(gxs)
            cy = sum(gys) // len(gys)
        else:
            # Fallback: approximate button position (84% across, 13% down)
            cx = wl + int(win_w * 0.84)
            cy = wt + int(win_h * 0.13)

        # Bring Chrome to front and click the Unlock button
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        ctypes.windll.user32.SetCursorPos(cx, cy)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP

        time.sleep(0.8)  # Wait for password modal to appear

        # Type the password
        for ch in password:
            vk = ctypes.windll.user32.VkKeyScanA(ord(ch)) & 0xFF
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.04)
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
            time.sleep(0.02)

        # Press Enter
        ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)

    except Exception:
        pass


class StatusItem(QTableWidgetItem):
    def __init__(self, status: str):
        super().__init__(f"  {status.upper()}")
        color = STATUS_COLORS.get(status, "#8b949e")
        self.setForeground(QColor(color))
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)


class ColorItem(QTableWidgetItem):
    def __init__(self, text: str, color: str = "#e6edf3"):
        super().__init__(text)
        self.setForeground(QColor(color))
        self.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)


class _LinkItem(QTableWidgetItem):
    """IP cell styled as a clickable blue link."""
    def __init__(self, ip: str):
        super().__init__(ip)
        self.setForeground(QColor("#58a6ff"))
        self.setToolTip(f"Click to open http://{ip} in browser")
        font = self.font()
        font.setUnderline(True)
        self.setFont(font)
        self.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)


COLS = ["Status", "Name", "IP", "Model", "Hashrate", "Temp", "Fan", "Accepted",
        "Rejected", "HW Err%", "Pool", "Uptime", "Last Seen"]


class MinersPage(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._rows: Dict[str, int] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Miners")
        title.setObjectName("sectionTitle")
        title_row.addWidget(title)

        self._group_filter = QComboBox()
        self._group_filter.setFixedWidth(140)
        self._group_filter.addItem("All Groups", None)
        self._group_filter.currentIndexChanged.connect(self._apply_filter)
        title_row.addStretch()
        title_row.addWidget(QLabel("Group:"))
        title_row.addWidget(self._group_filter)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name or IP...")
        self._search.setFixedWidth(220)
        self._search.textChanged.connect(self._apply_filter)
        title_row.addWidget(self._search)

        btn_add = QPushButton("+ Add Miner")
        btn_add.setObjectName("btnPrimary")
        btn_add.setFixedHeight(32)
        btn_add.clicked.connect(self._add_miner)
        title_row.addWidget(btn_add)

        btn_scan = QPushButton("⟳ Scan Network")
        btn_scan.setFixedHeight(32)
        btn_scan.clicked.connect(self._scan_network)
        title_row.addWidget(btn_scan)

        btn_pool = QPushButton("⛏ Change Pool")
        btn_pool.setFixedHeight(32)
        btn_pool.clicked.connect(self._change_pool_all)
        title_row.addWidget(btn_pool)

        layout.addLayout(title_row)

        # Batch action bar (shown when multiple rows selected)
        batch_row = QHBoxLayout()
        self._batch_lbl = QLabel("Select rows for batch actions:")
        self._batch_lbl.setStyleSheet("color:#8b949e;font-size:11px;background:transparent;")
        batch_row.addWidget(self._batch_lbl)

        self._btn_batch_group = QPushButton("Assign Group")
        self._btn_batch_group.setFixedHeight(26)
        self._btn_batch_group.setEnabled(False)
        self._btn_batch_group.clicked.connect(self._batch_assign_group)
        batch_row.addWidget(self._btn_batch_group)

        self._btn_batch_export = QPushButton("Export CSV")
        self._btn_batch_export.setFixedHeight(26)
        self._btn_batch_export.setEnabled(False)
        self._btn_batch_export.clicked.connect(self._batch_export_csv)
        batch_row.addWidget(self._btn_batch_export)

        self._btn_batch_remove = QPushButton("Remove Selected")
        self._btn_batch_remove.setObjectName("btnDanger")
        self._btn_batch_remove.setFixedHeight(26)
        self._btn_batch_remove.setEnabled(False)
        self._btn_batch_remove.clicked.connect(self._batch_remove)
        batch_row.addWidget(self._btn_batch_remove)

        batch_row.addStretch()
        layout.addLayout(batch_row)

        # Table
        self._table = QTableWidget(0, len(COLS))
        self._table.setHorizontalHeaderLabels(COLS)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setStretchLastSection(True)
        self._table.setColumnWidth(0, 90)   # Status
        self._table.setColumnWidth(1, 120)  # Name
        self._table.setColumnWidth(2, 120)  # IP
        self._table.setColumnWidth(3, 200)  # Model
        self._table.setColumnWidth(4, 105)  # Hashrate
        self._table.setColumnWidth(5, 65)   # Temp
        self._table.setColumnWidth(6, 90)   # Fan
        self._table.setColumnWidth(7, 90)   # Accepted
        self._table.setColumnWidth(8, 75)   # Rejected
        self._table.setColumnWidth(9, 70)   # HW Err%
        self._table.setColumnWidth(10, 180) # Pool
        self._table.setColumnWidth(11, 70)  # Uptime
        self._table.setColumnWidth(12, 85)  # Last Seen
        self._table.setRowHeight(0, 36)
        self._table.verticalHeader().setDefaultSectionSize(36)

        layout.addWidget(self._table, 1)

        # Footer
        self._footer = QLabel("")
        self._footer.setObjectName("sectionSub")
        layout.addWidget(self._footer)

    def update_miner(self, miner: MinerData):
        if miner.ip in self._rows:
            row = self._rows[miner.ip]
        else:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._rows[miner.ip] = row

        self._table.setRowHeight(row, 36)
        self._fill_row(row, miner)
        self._update_footer()

    def _fill_row(self, row: int, m: MinerData):
        temp = m.display_temp()
        temp_color = (STATUS_COLORS.get(m.temp_level(75, 85), "#e6edf3")
                      if temp != "N/A" else "#8b949e")
        hw_color = "#f85149" if m.hw_error_rate >= 1.0 else "#d29922" if m.hw_error_rate >= 0.5 else "#e6edf3"
        last = m.last_seen.strftime("%H:%M:%S") if m.last_seen else "—"
        pool_short = m.pool_url.replace("stratum+tcp://", "").split("/")[0]
        model_short = m.model[:30] if m.model else "—"

        # Fetch notes from DB for tooltip
        miners_db = self._main.get_db().get_miners()
        miner_row = next((r for r in miners_db if r["ip"] == m.ip), {})
        notes = miner_row.get("notes", "") or ""

        items = [
            StatusItem(m.status),
            ColorItem(m.display_name),
            _LinkItem(m.ip),
            ColorItem(model_short, BITCOIN_ORANGE),
            ColorItem(m.display_hashrate(), BITCOIN_ORANGE),
            ColorItem(temp, temp_color),
            ColorItem(m.display_fan()),
            ColorItem(f"{m.accepted:,}"),
            ColorItem(f"{m.rejected:,}"),
            ColorItem(f"{m.hw_error_rate:.2f}%", hw_color),
            ColorItem(pool_short or "—", "#8b949e"),
            ColorItem(m.display_uptime()),
            ColorItem(last, "#8b949e"),
        ]
        for col, item in enumerate(items):
            item.setData(Qt.ItemDataRole.UserRole, m.ip)
            if notes:
                item.setToolTip(f"Notes: {notes}")
            self._table.setItem(row, col, item)

    def remove_miner(self, ip: str):
        if ip in self._rows:
            row = self._rows.pop(ip)
            self._table.removeRow(row)
            # Reindex
            self._rows = {}
            for r in range(self._table.rowCount()):
                item = self._table.item(r, 2)
                if item:
                    self._rows[item.text()] = r

    def _apply_filter(self):
        text = self._search.text().lower()
        group_id = self._group_filter.currentData()

        # Build a map of ip → group_id from DB
        miners_db = {m["ip"]: m.get("group_id") for m in self._main.get_db().get_miners()}

        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 1)
            ip_item   = self._table.item(row, 2)
            ip = ip_item.text() if ip_item else ""

            text_match = (not text or
                          (name_item and text in name_item.text().lower()) or
                          text in ip.lower())
            group_match = (group_id is None or miners_db.get(ip) == group_id)
            self._table.setRowHidden(row, not (text_match and group_match))

    def reload_groups(self):
        """Refresh the group filter combo from DB."""
        current = self._group_filter.currentData()
        self._group_filter.blockSignals(True)
        self._group_filter.clear()
        self._group_filter.addItem("All Groups", None)
        for g in self._main.get_db().get_groups():
            self._group_filter.addItem(g["name"], g["id"])
        # Restore selection
        idx = self._group_filter.findData(current)
        self._group_filter.setCurrentIndex(max(0, idx))
        self._group_filter.blockSignals(False)

    def _context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        ip_item = self._table.item(row, 2)
        if not ip_item:
            return
        ip = ip_item.text()

        menu = QMenu(self)
        menu.addAction("Details", lambda: self._open_details(ip))
        menu.addAction("Open in Browser", lambda: self._open_browser(ip))
        menu.addAction("Change Pool...", lambda: self._change_pool(ip))
        menu.addAction("Edit Miner", lambda: self._edit_miner(ip))
        menu.addSeparator()
        menu.addAction("Restart Miner (CGMiner)...", lambda: self._restart_miner(ip))
        menu.addSeparator()
        menu.addAction("Remove Miner", lambda: self._remove_miner(ip))
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_cell_clicked(self, row: int, col: int):
        if col == 2:  # IP column — open miner web UI
            ip_item = self._table.item(row, col)
            if ip_item:
                self._open_browser(ip_item.text())

    def _on_double_click(self, index):
        row = index.row()
        ip_item = self._table.item(row, 2)
        if ip_item:
            self._open_browser(ip_item.text())

    def _open_details(self, ip: str):
        miner = self._main.get_scanner().get_miner(ip)
        if miner:
            from .dialogs import MinerDetailsDialog
            dlg = MinerDetailsDialog(miner, self)
            dlg.exec()
        else:
            self._open_browser(ip)

    def _open_browser(self, ip: str):
        import webbrowser
        import threading
        cfg = self._main.get_config()
        user = cfg.miner_web_user or "root"
        pwd  = cfg.miner_web_password or "root"
        webbrowser.open(f"http://{user}:{pwd}@{ip}")
        threading.Thread(target=_auto_unlock_vnish,
                         args=(cfg.miner_web_password or "admin",),
                         daemon=True).start()

    def _add_miner(self):
        from .dialogs import AddMinerDialog
        dlg = AddMinerDialog(self._main, self)
        if dlg.exec():
            ip, port, name, min_ths, notes, group_id = dlg.result_data()
            self._main.add_miner_to_watch(ip, port, name, min_ths, notes, group_id)

    def _edit_miner(self, ip: str):
        from .dialogs import AddMinerDialog
        miners = self._main.get_db().get_miners()
        existing = next((m for m in miners if m["ip"] == ip), None)
        dlg = AddMinerDialog(self._main, self, existing=existing)
        if dlg.exec():
            new_ip, port, name, min_ths, notes, group_id = dlg.result_data()
            self._main.add_miner_to_watch(new_ip, port, name, min_ths, notes, group_id)

    def _restart_miner(self, ip: str):
        name_item = None
        for row in range(self._table.rowCount()):
            ip_item = self._table.item(row, 2)
            if ip_item and ip_item.text() == ip:
                name_item = self._table.item(row, 1)
                break
        name = name_item.text() if name_item else ip

        reply = QMessageBox.warning(
            self, "Restart Miner",
            f"Send RESTART command to {name} ({ip})?\n\n"
            f"This will stop and restart the CGMiner process on the miner.\n"
            f"The miner will go offline briefly then reconnect.\n\n"
            f"⚠ This does NOT change any settings, pools, or firmware.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        import threading
        def _do_restart():
            from ..core.cgminer_api import CGMinerAPI
            miner_data = self._main.get_miners().get(ip)
            port = miner_data.port if miner_data else 4028
            api = CGMinerAPI(ip, port, timeout=8.0)
            ok, msg = api.restart()
            level = "INFO" if ok else "WARN"
            log_msg = f"Restart {'sent' if ok else 'failed'} for {name} ({ip}): {msg}"
            self._main.db.log_event(ip, level, log_msg)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._main._logs_page.add_event(ip, level, log_msg))
            from PyQt6.QtCore import QTimer
            result_text = f"{'✓' if ok else '✗'} {name}: {msg}"
            QTimer.singleShot(0, lambda: self._main._status_msg.setText(result_text))

        threading.Thread(target=_do_restart, daemon=True).start()
        self._main._status_msg.setText(f"Sending restart to {name} ({ip})...")

    def _remove_miner(self, ip: str):
        reply = QMessageBox.question(
            self, "Remove Miner",
            f"Remove {ip} from monitoring?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._main.remove_miner_from_watch(ip)

    def _scan_network(self):
        from .dialogs import ScanNetworkDialog
        cfg = self._main.get_config()
        dlg = ScanNetworkDialog(self._main, cfg, self)
        if dlg.exec():
            for miner in dlg.selected_miners():
                self._main.add_miner_to_watch(miner.ip, miner.port, miner.name, cfg.default_min_ths)

    def _change_pool(self, ip: str):
        """Open pool manager pre-filled for a specific miner."""
        from .dialogs import ChangePoolDialog
        dlg = ChangePoolDialog(self._main, target_ip=ip, parent=self)
        dlg.exec()

    def _change_pool_all(self):
        """Open pool manager targeting all miners (toolbar button)."""
        from .dialogs import ChangePoolDialog
        dlg = ChangePoolDialog(self._main, target_ip=None, parent=self)
        dlg.exec()

    def _on_selection_changed(self):
        ips = self._get_selected_ips()
        has = len(ips) > 0
        n = len(ips)
        self._btn_batch_group.setEnabled(has)
        self._btn_batch_export.setEnabled(has)
        self._btn_batch_remove.setEnabled(has)
        self._batch_lbl.setText(
            f"{n} miner{'s' if n != 1 else ''} selected — batch actions:" if has
            else "Select rows (Shift/Ctrl+click) for batch actions:"
        )

    def _get_selected_ips(self) -> list:
        seen = set()
        ips = []
        for item in self._table.selectedItems():
            ip_item = self._table.item(item.row(), 2)
            if ip_item and ip_item.text() not in seen:
                seen.add(ip_item.text())
                ips.append(ip_item.text())
        return ips

    def _batch_assign_group(self):
        ips = self._get_selected_ips()
        if not ips:
            return
        groups = self._main.get_db().get_groups()
        if not groups:
            QMessageBox.information(self, "No Groups", "Create groups first in the Groups page.")
            return
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QComboBox as _CB
        dlg = QDialog(self)
        dlg.setWindowTitle("Assign Group")
        dlg.setFixedWidth(300)
        fl = QFormLayout(dlg)
        fl.setSpacing(12)
        fl.setContentsMargins(16, 16, 16, 16)
        combo = _CB()
        combo.addItem("(No group)", None)
        for g in groups:
            combo.addItem(g["name"], g["id"])
        fl.addRow("Group:", combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        fl.addRow(btns)
        if dlg.exec():
            gid = combo.currentData()
            db = self._main.get_db()
            for ip in ips:
                db.set_miner_group(ip, gid)
            if hasattr(self._main, "_groups_page"):
                self._main._groups_page.refresh()
            self.reload_groups()

    def _batch_export_csv(self):
        import csv, os
        from datetime import datetime
        ips = set(self._get_selected_ips())
        if not ips:
            return
        default = os.path.join(os.path.expanduser("~"), "Desktop",
                               f"miners_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        path, _ = QFileDialog.getSaveFileName(self, "Export Miners CSV", default, "CSV Files (*.csv)")
        if not path:
            return
        headers = COLS[:]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(headers)
                for row in range(self._table.rowCount()):
                    ip_item = self._table.item(row, 2)
                    if ip_item and ip_item.text() in ips:
                        w.writerow([
                            self._table.item(row, col).text() if self._table.item(row, col) else ""
                            for col in range(self._table.columnCount())
                        ])
            QMessageBox.information(self, "Export Complete", f"Exported to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def _batch_remove(self):
        ips = self._get_selected_ips()
        if not ips:
            return
        reply = QMessageBox.question(
            self, "Remove Miners",
            f"Remove {len(ips)} miner(s) from monitoring?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for ip in ips:
                self._main.remove_miner_from_watch(ip)

    def _update_footer(self):
        total = self._table.rowCount()
        miners = list(self._main.get_miners().values())
        online = sum(1 for m in miners if m.status == "online")
        offline = sum(1 for m in miners if m.status == "offline")
        self._footer.setText(f"{total} miners monitored  ·  {online} online  ·  {offline} offline")
