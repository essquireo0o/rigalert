import csv
import os
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from .theme import STATUS_COLORS

LEVEL_COLORS = {
    "INFO":  "#2fbf71",
    "WARN":  "#f2b84b",
    "ERROR": "#ff6b6b",
    "DEBUG": "#9aa8bd",
}


class LogsPage(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._setup_ui()
        self._load_from_db()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("Event Logs")
        title.setObjectName("sectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter logs...")
        self._search.setFixedWidth(200)
        self._search.textChanged.connect(self._filter)
        title_row.addWidget(self._search)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedHeight(30)
        btn_refresh.clicked.connect(self._load_from_db)
        title_row.addWidget(btn_refresh)

        btn_export = QPushButton("Export CSV")
        btn_export.setFixedHeight(30)
        btn_export.clicked.connect(self._export_csv)
        title_row.addWidget(btn_export)

        btn_clear = QPushButton("Clear Logs")
        btn_clear.setObjectName("btnDanger")
        btn_clear.setFixedHeight(30)
        btn_clear.clicked.connect(self._clear_logs)
        title_row.addWidget(btn_clear)

        layout.addLayout(title_row)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Time", "IP", "Level", "Message"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 140)
        self._table.setColumnWidth(1, 120)
        self._table.setColumnWidth(2, 70)
        self._table.verticalHeader().setDefaultSectionSize(32)

        layout.addWidget(self._table, 1)

        self._footer = QLabel("")
        self._footer.setObjectName("sectionSub")
        layout.addWidget(self._footer)

    def add_event(self, ip: str, level: str, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._insert_row(ts, ip, level, message)
        self._update_footer()

    def _insert_row(self, ts: str, ip: str, level: str, message: str):
        row = 0
        self._table.insertRow(row)
        self._table.setRowHeight(row, 32)

        color = LEVEL_COLORS.get(level.upper(), "#eef4ff")

        def item(text, c="#eef4ff"):
            it = QTableWidgetItem(text)
            it.setForeground(QColor(c))
            it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            return it

        self._table.setItem(row, 0, item(ts, "#9aa8bd"))
        self._table.setItem(row, 1, item(ip, "#9aa8bd"))
        self._table.setItem(row, 2, item(level.upper(), color))
        self._table.setItem(row, 3, item(message, color if level.upper() != "INFO" else "#eef4ff"))

        # Keep max 1000 rows
        while self._table.rowCount() > 1000:
            self._table.removeRow(self._table.rowCount() - 1)

    def _load_from_db(self):
        self._table.setRowCount(0)
        events = self._main.get_db().get_events(limit=500)
        for ev in events:
            self._insert_row(
                str(ev.get("ts", ""))[:19],
                str(ev.get("ip", "")),
                str(ev.get("level", "INFO")),
                str(ev.get("message", "")),
            )
        self._update_footer()

    def _filter(self, text: str):
        text = text.lower()
        for row in range(self._table.rowCount()):
            visible = False
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item and text in item.text().lower():
                    visible = True
                    break
            self._table.setRowHidden(row, not visible and bool(text))

    def _clear_logs(self):
        reply = QMessageBox.question(
            self, "Clear Logs", "Clear all event logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._main.get_db().clear_events()
            self._table.setRowCount(0)
            self._update_footer()

    def _export_csv(self):
        default_name = f"rigalert_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = os.path.join(os.path.expanduser("~"), "Desktop", default_name)
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs as CSV", default_path, "CSV Files (*.csv)"
        )
        if not path:
            return
        headers = ["Time", "IP", "Level", "Message"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in range(self._table.rowCount()):
                    if self._table.isRowHidden(row):
                        continue
                    writer.writerow([
                        self._table.item(row, col).text() if self._table.item(row, col) else ""
                        for col in range(self._table.columnCount())
                    ])
            QMessageBox.information(self, "Export Complete", f"Logs exported to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def _update_footer(self):
        self._footer.setText(f"{self._table.rowCount()} events shown")
