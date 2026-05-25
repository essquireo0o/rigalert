"""Firmware Tools page — detect, display, and safely manage miner firmware."""
import json
import os
import threading
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QScrollArea, QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

from ..core.firmware import (
    detect_type, firmware_badge_color, vnish_get_info, vnish_get_config,
    FIRMWARE_VNISH, FIRMWARE_BRAIINS, FIRMWARE_STOCK, FIRMWARE_UNKNOWN,
)
from ..core.miner import MinerData
from .theme import BITCOIN_ORANGE, BG_CARD, BORDER_COLOR, TEXT_MUTED


# ── Background worker for HTTP firmware info ──────────────────────────────────

class _FirmwareInfoWorker(QThread):
    result = pyqtSignal(str, dict)   # ip, info_dict

    def __init__(self, ip: str, user: str, password: str, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._user = user
        self._password = password

    def run(self):
        info = vnish_get_info(self._ip, self._user, self._password)
        self.result.emit(self._ip, info)


# ── Firmware Details Panel ────────────────────────────────────────────────────

class _FirmwareDetailPanel(QWidget):
    backup_requested = pyqtSignal(str)   # ip
    install_requested = pyqtSignal(str)  # ip
    restore_requested = pyqtSignal(str)  # ip

    def __init__(self, parent=None):
        super().__init__(parent)
        self._miner: Optional[MinerData] = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self._title = QLabel("Select a miner")
        self._title.setStyleSheet(f"font-size:16px;font-weight:700;color:#e6edf3;")
        layout.addWidget(self._title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        self._content = QWidget()
        self._content.setStyleSheet("background:transparent;")
        self._vbox = QVBoxLayout(self._content)
        self._vbox.setContentsMargins(0, 0, 0, 0)
        self._vbox.setSpacing(10)
        self._vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._content)
        layout.addWidget(scroll, 1)

        # ── Action buttons ────────────────────────────────────────────
        action_box = QGroupBox("Actions")
        action_box.setStyleSheet(
            "QGroupBox{border:1px solid #30363d;border-radius:6px;margin-top:8px;"
            "padding:10px;background:#161b22;}"
            "QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;"
            "background:#161b22;color:#8b949e;font-size:11px;text-transform:uppercase;}"
        )
        ab = QVBoxLayout(action_box)
        ab.setSpacing(6)

        self._btn_backup = QPushButton("⬇  Backup Config")
        self._btn_backup.setEnabled(False)
        self._btn_backup.setToolTip("Download miner configuration as JSON backup")
        self._btn_backup.clicked.connect(self._on_backup)
        ab.addWidget(self._btn_backup)

        # Dangerous actions
        danger_box = QGroupBox("Dangerous Actions — require confirmation")
        danger_box.setStyleSheet(
            "QGroupBox{border:2px solid #da3633;border-radius:6px;margin-top:8px;"
            "padding:10px;background:#161b22;}"
            "QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;"
            "background:#161b22;color:#f85149;font-size:11px;font-weight:700;}"
        )
        db_layout = QVBoxLayout(danger_box)
        db_layout.setSpacing(6)

        self._btn_install = QPushButton("⚠  Install New Firmware...")
        self._btn_install.setObjectName("btnDanger")
        self._btn_install.setEnabled(False)
        self._btn_install.setToolTip("Flash new firmware to this miner (requires confirmation)")
        self._btn_install.clicked.connect(self._on_install)
        db_layout.addWidget(self._btn_install)

        self._btn_restore = QPushButton("↩  Restore Stock Firmware...")
        self._btn_restore.setObjectName("btnDanger")
        self._btn_restore.setEnabled(False)
        self._btn_restore.setToolTip("Remove VNish/Braiins and restore original Antminer firmware")
        self._btn_restore.clicked.connect(self._on_restore)
        db_layout.addWidget(self._btn_restore)

        ab.addWidget(danger_box)
        layout.addWidget(action_box)

        self._log_lbl = QLabel("")
        self._log_lbl.setWordWrap(True)
        self._log_lbl.setStyleSheet("font-size:11px;color:#8b949e;background:transparent;")
        layout.addWidget(self._log_lbl)

    def _clear_content(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _section(self, title: str) -> tuple[QGroupBox, QFormLayout]:
        gb = QGroupBox(title)
        gb.setStyleSheet(
            "QGroupBox{border:1px solid #30363d;border-radius:6px;margin-top:8px;"
            "padding:10px;background:#161b22;}"
            "QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;"
            "background:#161b22;color:#c8a94b;font-size:11px;font-weight:700;}"
        )
        f = QFormLayout(gb)
        f.setSpacing(6)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        return gb, f

    def _row(self, form: QFormLayout, label: str, value: str, color: str = "#e6edf3"):
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        val = QLabel(value or "—")
        val.setStyleSheet(f"color:{color};font-size:12px;font-family:Consolas,monospace;background:transparent;")
        val.setWordWrap(True)
        form.addRow(lbl, val)

    def show_miner(self, miner: MinerData):
        self._miner = miner
        self._clear_content()

        fw_type = detect_type(miner.firmware, miner.model)
        fw_color = firmware_badge_color(fw_type)

        self._title.setText(miner.display_name)

        # Firmware info section
        fw_box, ff = self._section("Firmware")
        self._row(ff, "Type:", fw_type, fw_color)
        self._row(ff, "Version:", miner.firmware or "Unknown")
        self._row(ff, "Model:", miner.model or "Unknown", BITCOIN_ORANGE)
        self._row(ff, "IP:", f"{miner.ip}:{miner.port}")
        if miner.total_acn > 0:
            self._row(ff, "Total ASICs:", str(miner.total_acn))
        self._vbox.addWidget(fw_box)

        # Chain status for VNISH
        if miner.chain_states:
            ch_box, cf = self._section(f"Hashboard Status ({len(miner.chain_states)} boards)")
            for i, state in enumerate(miner.chain_states):
                state_colors = {
                    "running": "#3fb950", "normal": "#3fb950", "disabled": "#8b949e",
                    "failure": "#f85149", "dead": "#f85149", "stopped": "#d29922",
                }
                sc = state_colors.get(state.lower(), "#8b949e")
                acn = miner.chain_acns[i] if i < len(miner.chain_acns) else 0
                detail = state
                if acn > 0:
                    detail += f"  ({acn} ASICs)"
                if i < len(miner.chain_faults) and miner.chain_faults[i]:
                    detail += f"  ⚠ {miner.chain_faults[i]}"
                self._row(cf, f"Board {i+1}:", detail, sc)
            self._vbox.addWidget(ch_box)

        # Enable/disable action buttons based on firmware type
        can_backup  = fw_type in (FIRMWARE_VNISH,)
        can_install = fw_type in (FIRMWARE_VNISH, FIRMWARE_STOCK)
        can_restore = fw_type in (FIRMWARE_VNISH, FIRMWARE_BRAIINS)

        self._btn_backup.setEnabled(can_backup)
        self._btn_install.setEnabled(can_install)
        self._btn_restore.setEnabled(can_restore)

        if not can_backup:
            self._btn_backup.setToolTip("Config backup not yet supported for this firmware type")
        if fw_type == FIRMWARE_UNKNOWN:
            self._log_lbl.setText("Unknown firmware — connect miner to detect firmware type.")
        else:
            self._log_lbl.setText("")

    def update_http_info(self, info: dict):
        """Called when VNish HTTP info arrives. Refresh the firmware version display."""
        if not self._miner or not info:
            return
        if info.get("fw_version"):
            self._miner.firmware = info["fw_version"]
        if info.get("model") and not self._miner.model:
            self._miner.model = info["model"]
        self.show_miner(self._miner)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_backup(self):
        if not self._miner:
            return
        self.backup_requested.emit(self._miner.ip)

    def _on_install(self):
        if not self._miner:
            return
        self.install_requested.emit(self._miner.ip)

    def _on_restore(self):
        if not self._miner:
            return
        self.restore_requested.emit(self._miner.ip)


# ── Firmware Page ─────────────────────────────────────────────────────────────

class FirmwarePage(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._workers: dict = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Firmware Tools")
        title.setObjectName("sectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        btn_refresh = QPushButton("⟳  Refresh Info")
        btn_refresh.setFixedHeight(32)
        btn_refresh.clicked.connect(self._refresh_all)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)

        sub = QLabel(
            "Read-only firmware detection from CGMiner API. "
            "Firmware actions require explicit confirmation and are logged to the audit trail."
        )
        sub.setObjectName("sectionSub")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Splitter: left=miner list, right=detail panel
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle{background:#21262d;}")

        # Left: miner list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        lbl = QLabel("Miners")
        lbl.setStyleSheet("font-size:12px;font-weight:600;color:#8b949e;text-transform:uppercase;")
        left_layout.addWidget(lbl)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget{background:#0d1117;border:1px solid #30363d;border-radius:6px;}"
            "QListWidget::item{padding:8px 10px;border-bottom:1px solid #21262d;color:#e6edf3;}"
            "QListWidget::item:selected{background:#1c2128;color:#e6edf3;}"
            "QListWidget::item:hover{background:#161b22;}"
        )
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self._list)

        splitter.addWidget(left)

        # Right: detail panel
        self._detail = _FirmwareDetailPanel()
        self._detail.backup_requested.connect(self._do_backup)
        self._detail.install_requested.connect(self._show_install_wizard)
        self._detail.restore_requested.connect(self._show_restore_wizard)
        self._detail.setStyleSheet("background:#0d1117;")

        splitter.addWidget(self._detail)
        splitter.setSizes([280, 600])
        layout.addWidget(splitter, 1)

    def _make_list_item(self, miner: MinerData) -> QListWidgetItem:
        fw_type = detect_type(miner.firmware, miner.model)
        fw_color = firmware_badge_color(fw_type)
        name = miner.display_name
        status_dot = {"online": "●", "offline": "○", "warning": "◐"}.get(miner.status, "◌")
        text = f"{status_dot}  {name}\n   {fw_type}  ·  {miner.ip}"
        item = QListWidgetItem(text)
        item.setForeground(QColor("#e6edf3"))
        item.setData(Qt.ItemDataRole.UserRole, miner.ip)
        return item

    def refresh(self):
        """Rebuild the miner list from current scanner state."""
        miners = list(self._main.get_miners().values())
        current_ip = None
        cur = self._list.currentItem()
        if cur:
            current_ip = cur.data(Qt.ItemDataRole.UserRole)

        self._list.clear()
        for miner in sorted(miners, key=lambda m: m.display_name.lower()):
            self._list.addItem(self._make_list_item(miner))

        # Restore selection
        if current_ip:
            for i in range(self._list.count()):
                item = self._list.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == current_ip:
                    self._list.setCurrentItem(item)
                    break

    def update_miner(self, miner: MinerData):
        """Called when a miner is updated by the scanner."""
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == miner.ip:
                item.setText(self._make_list_item(miner).text())
                if self._list.currentItem() is item:
                    self._detail.show_miner(miner)
                return
        self._list.addItem(self._make_list_item(miner))

    def remove_miner(self, ip: str):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == ip:
                self._list.takeItem(i)
                break

    def _on_selection_changed(self, current: QListWidgetItem, _prev):
        if not current:
            return
        ip = current.data(Qt.ItemDataRole.UserRole)
        miner = self._main.get_scanner().get_miner(ip)
        if miner:
            self._detail.show_miner(miner)
            # For VNish, also fetch HTTP info in background
            fw_type = detect_type(miner.firmware, miner.model)
            if fw_type == "VNish":
                self._fetch_vnish_http(miner.ip)

    def _refresh_all(self):
        self.refresh()
        # Refresh HTTP info for currently selected VNish miner
        cur = self._list.currentItem()
        if cur:
            ip = cur.data(Qt.ItemDataRole.UserRole)
            miner = self._main.get_scanner().get_miner(ip)
            if miner and detect_type(miner.firmware, miner.model) == "VNish":
                self._fetch_vnish_http(ip)

    def _fetch_vnish_http(self, ip: str):
        cfg = self._main.get_config()
        user = cfg.miner_web_user or "admin"
        pwd  = cfg.miner_web_password or "admin"
        worker = _FirmwareInfoWorker(ip, user, pwd, self)
        worker.result.connect(self._on_vnish_info)
        worker.start()
        self._workers[ip] = worker

    def _on_vnish_info(self, ip: str, info: dict):
        cur = self._list.currentItem()
        if cur and cur.data(Qt.ItemDataRole.UserRole) == ip:
            self._detail.update_http_info(info)
        self._workers.pop(ip, None)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _do_backup(self, ip: str):
        miner = self._main.get_scanner().get_miner(ip)
        if not miner:
            return
        cfg = self._main.get_config()
        user = cfg.miner_web_user or "admin"
        pwd  = cfg.miner_web_password or "admin"

        def run():
            config_data = vnish_get_config(ip, user, pwd)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._save_backup(ip, config_data))

        threading.Thread(target=run, daemon=True).start()

    def _save_backup(self, ip: str, config_data):
        if not config_data:
            QMessageBox.warning(self, "Backup Failed",
                f"Could not download config from {ip}.\n\n"
                "Check that the miner IP, username, and password are correct in Settings.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rigalert_backup_{ip.replace('.','_')}_{ts}.json"
        save_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        try:
            with open(save_path, "w") as f:
                json.dump(config_data, f, indent=2)
            self._main.get_db().log_event(ip, "INFO", f"Config backup saved: {filename}")
            QMessageBox.information(self, "Backup Saved",
                f"Config backup saved to Desktop:\n{filename}")
        except Exception as e:
            QMessageBox.warning(self, "Backup Error", f"Could not save file: {e}")

    def _show_install_wizard(self, ip: str):
        miner = self._main.get_scanner().get_miner(ip)
        if not miner:
            return
        dlg = _InstallFirmwareDialog(ip, miner.display_name, self._main, self)
        dlg.exec()

    def _show_restore_wizard(self, ip: str):
        miner = self._main.get_scanner().get_miner(ip)
        if not miner:
            return
        dlg = _RestoreFirmwareDialog(ip, miner.display_name, self._main, self)
        dlg.exec()


# ── Install Firmware Dialog ───────────────────────────────────────────────────

class _InstallFirmwareDialog(QDialog):
    def __init__(self, ip: str, name: str, main_win, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._name = name
        self._main = main_win
        self.setWindowTitle(f"Install Firmware — {ip}")
        self.setMinimumWidth(500)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        warn = QLabel(
            "⚠  WARNING: Flashing firmware is irreversible.\n\n"
            "Before proceeding:\n"
            "  • Back up the current miner config\n"
            "  • Download the correct firmware file for your model\n"
            "  • Do NOT power off the miner during flashing\n\n"
            "This feature is currently in DRY-RUN mode — it will show\n"
            "what would happen without actually flashing."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet(
            "color:#d29922;font-size:13px;background:#21262d;"
            "border:1px solid #9e6a03;border-radius:6px;padding:14px;"
        )
        layout.addWidget(warn)

        info = QLabel(
            f"Target miner:  {self._name}  ({self._ip})\n"
            "Firmware install via web UI upload is coming soon.\n"
            "Currently showing dry-run mode only."
        )
        info.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFixedHeight(120)
        self._log.setStyleSheet(
            "QTextEdit{background:#0d1117;border:1px solid #30363d;border-radius:4px;"
            "color:#8b949e;font-family:Consolas,monospace;font-size:11px;}"
        )
        self._log.append(f"[DRY-RUN] Target: {self._ip}")
        self._log.append("[DRY-RUN] Would check miner model and firmware compatibility")
        self._log.append("[DRY-RUN] Would upload firmware file via HTTP POST")
        self._log.append("[DRY-RUN] No changes made — dry-run complete")
        layout.addWidget(self._log)

        self._main.get_db().log_event(
            self._ip, "INFO",
            f"Firmware install wizard opened (dry-run) for {self._name}"
        )

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# ── Restore Stock Firmware Dialog ─────────────────────────────────────────────

class _RestoreFirmwareDialog(QDialog):
    def __init__(self, ip: str, name: str, main_win, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._name = name
        self._main = main_win
        self.setWindowTitle(f"Restore Stock Firmware — {ip}")
        self.setMinimumWidth(500)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        warn = QLabel(
            "⚠  WARNING: Restoring stock firmware will remove VNish/Braiins OS.\n\n"
            "Before proceeding:\n"
            "  • Save your pool configuration\n"
            "  • Note your current firmware settings\n"
            "  • Miner will restart during the process\n\n"
            "This feature is currently in DRY-RUN mode — it will show\n"
            "what would happen without making any changes."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet(
            "color:#f85149;font-size:13px;background:#21262d;"
            "border:1px solid #da3633;border-radius:6px;padding:14px;"
        )
        layout.addWidget(warn)

        info = QLabel(
            f"Target miner:  {self._name}  ({self._ip})\n"
            "Stock firmware restore is coming soon.\n"
            "Currently showing dry-run mode only."
        )
        info.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFixedHeight(120)
        self._log.setStyleSheet(
            "QTextEdit{background:#0d1117;border:1px solid #30363d;border-radius:4px;"
            "color:#8b949e;font-family:Consolas,monospace;font-size:11px;}"
        )
        self._log.append(f"[DRY-RUN] Target: {self._ip}")
        self._log.append("[DRY-RUN] Would verify current firmware is VNish or Braiins OS")
        self._log.append("[DRY-RUN] Would trigger stock firmware restore endpoint")
        self._log.append("[DRY-RUN] No changes made — dry-run complete")
        layout.addWidget(self._log)

        self._main.get_db().log_event(
            self._ip, "INFO",
            f"Firmware restore wizard opened (dry-run) for {self._name}"
        )

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
