"""Miner Groups management page."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

_GROUP_COLORS = [
    ("#3fb950", "Green"),
    ("#58a6ff", "Blue"),
    ("#d29922", "Yellow"),
    ("#f85149", "Red"),
    ("#d2a8ff", "Purple"),
    ("#ffa657", "Orange"),
    ("#8b949e", "Gray"),
    ("#c8a94b", "Gold"),
]


class _GroupDialog(QDialog):
    def __init__(self, parent=None, existing: dict = None):
        super().__init__(parent)
        self._existing = existing
        self.setWindowTitle("Edit Group" if existing else "Create Group")
        self.setFixedWidth(360)
        self._selected_color = existing["color"] if existing else "#3fb950"
        self._build()
        if existing:
            self._name.setText(existing.get("name", ""))
            self._notes.setPlainText(existing.get("notes", ""))

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Site A, Row 1, Warehouse North")
        form.addRow("Group Name:", self._name)

        layout.addLayout(form)

        # Color picker
        color_lbl = QLabel("Group Color:")
        color_lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        layout.addWidget(color_lbl)

        color_row = QHBoxLayout()
        self._color_btns = []
        for hex_color, name in _GROUP_COLORS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setToolTip(name)
            btn.setStyleSheet(
                f"QPushButton{{background:{hex_color};border:2px solid #30363d;border-radius:6px;}}"
                f"QPushButton:hover{{border-color:#e6edf3;}}"
            )
            btn.clicked.connect(lambda checked, c=hex_color: self._pick_color(c))
            color_row.addWidget(btn)
            self._color_btns.append((btn, hex_color))
        color_row.addStretch()
        layout.addLayout(color_row)
        self._update_color_selection()

        notes_lbl = QLabel("Notes:")
        notes_lbl.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        layout.addWidget(notes_lbl)

        self._notes = QPlainTextEdit()
        self._notes.setPlaceholderText("Optional description for this group")
        self._notes.setFixedHeight(60)
        layout.addWidget(self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pick_color(self, color: str):
        self._selected_color = color
        self._update_color_selection()

    def _update_color_selection(self):
        for btn, hex_color in self._color_btns:
            border = "#e6edf3" if hex_color == self._selected_color else "#30363d"
            width = "3px" if hex_color == self._selected_color else "2px"
            btn.setStyleSheet(
                f"QPushButton{{background:{hex_color};border:{width} solid {border};border-radius:6px;}}"
                f"QPushButton:hover{{border-color:#e6edf3;}}"
            )

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Name Required", "Please enter a group name.")
            return
        self.accept()

    def result_data(self) -> dict:
        return {
            "name":  self._name.text().strip(),
            "color": self._selected_color,
            "notes": self._notes.toPlainText().strip(),
        }


class GroupsPage(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self._main = main_win
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Miner Groups")
        title.setObjectName("sectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        btn_new = QPushButton("+ New Group")
        btn_new.setObjectName("btnPrimary")
        btn_new.setFixedHeight(32)
        btn_new.clicked.connect(self._create_group)
        title_row.addWidget(btn_new)
        layout.addLayout(title_row)

        sub = QLabel(
            "Organize miners into groups for filtering and fleet management. "
            "Groups can represent sites, buildings, rows, racks, or any custom label."
        )
        sub.setObjectName("sectionSub")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Groups list + detail split
        split = QHBoxLayout()
        split.setSpacing(16)

        # Left: group list
        left = QVBoxLayout()
        lbl = QLabel("Groups")
        lbl.setStyleSheet("font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;")
        left.addWidget(lbl)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget{background:#0d1117;border:1px solid #30363d;border-radius:6px;}"
            "QListWidget::item{padding:10px 12px;border-bottom:1px solid #21262d;}"
            "QListWidget::item:selected{background:#1c2128;}"
            "QListWidget::item:hover{background:#161b22;}"
        )
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.currentItemChanged.connect(self._on_select)
        left.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._btn_edit = QPushButton("Edit")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._edit_group)
        self._btn_delete = QPushButton("Delete")
        self._btn_delete.setObjectName("btnDanger")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete_group)
        btn_row.addWidget(self._btn_edit)
        btn_row.addWidget(self._btn_delete)
        left.addLayout(btn_row)

        split.addLayout(left, 1)

        # Right: group detail + miners in group
        right = QVBoxLayout()
        self._detail_title = QLabel("Select a group")
        self._detail_title.setStyleSheet("font-size:14px;font-weight:700;color:#e6edf3;background:transparent;")
        right.addWidget(self._detail_title)

        self._detail_info = QLabel("")
        self._detail_info.setStyleSheet("color:#8b949e;font-size:12px;background:transparent;")
        self._detail_info.setWordWrap(True)
        right.addWidget(self._detail_info)

        members_lbl = QLabel("Miners in this group:")
        members_lbl.setStyleSheet("font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;margin-top:8px;")
        right.addWidget(members_lbl)

        self._members_list = QListWidget()
        self._members_list.setStyleSheet(
            "QListWidget{background:#0d1117;border:1px solid #30363d;border-radius:6px;}"
            "QListWidget::item{padding:6px 10px;border-bottom:1px solid #21262d;color:#e6edf3;}"
        )
        right.addWidget(self._members_list, 1)

        split.addLayout(right, 1)
        layout.addLayout(split, 1)

    def refresh(self):
        current_id = None
        cur = self._list.currentItem()
        if cur:
            current_id = cur.data(Qt.ItemDataRole.UserRole)

        self._list.clear()
        groups = self._main.get_db().get_groups()
        all_miners = self._main.get_db().get_miners()

        for g in groups:
            count = sum(1 for m in all_miners if m.get("group_id") == g["id"])
            item = QListWidgetItem()
            item.setText(f"  {g['name']}  ({count} miners)")
            item.setForeground(QColor(g.get("color", "#e6edf3")))
            item.setData(Qt.ItemDataRole.UserRole, g["id"])
            self._list.addItem(item)

        # Restore selection
        if current_id is not None:
            for i in range(self._list.count()):
                if self._list.item(i).data(Qt.ItemDataRole.UserRole) == current_id:
                    self._list.setCurrentRow(i)
                    break

        if not groups:
            self._detail_title.setText("No groups yet")
            self._detail_info.setText("Click '+ New Group' to create your first group.")
            self._members_list.clear()

        # Refresh the Miners page group filter if accessible
        if hasattr(self._main, '_miners_page'):
            self._main._miners_page.reload_groups()

    def _on_select(self, current: QListWidgetItem, _prev):
        has = current is not None
        self._btn_edit.setEnabled(has)
        self._btn_delete.setEnabled(has)
        if not has:
            return

        gid = current.data(Qt.ItemDataRole.UserRole)
        groups = self._main.get_db().get_groups()
        g = next((x for x in groups if x["id"] == gid), None)
        if not g:
            return

        self._detail_title.setText(g["name"])
        notes_text = f"\n{g['notes']}" if g.get("notes") else ""
        self._detail_info.setText(f"Color: {g['color']}{notes_text}")

        self._members_list.clear()
        for m in self._main.get_db().get_miners():
            if m.get("group_id") == gid:
                name = m.get("name") or m["ip"]
                lbl = QListWidgetItem(f"  {name}  ({m['ip']})")
                lbl.setForeground(QColor("#e6edf3"))
                self._members_list.addItem(lbl)

        if self._members_list.count() == 0:
            empty = QListWidgetItem("  No miners assigned to this group")
            empty.setForeground(QColor("#8b949e"))
            self._members_list.addItem(empty)

    def _create_group(self):
        dlg = _GroupDialog(self)
        if dlg.exec():
            data = dlg.result_data()
            try:
                self._main.get_db().create_group(data["name"], data["color"], data["notes"])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create group: {e}")
                return
            self.refresh()

    def _edit_group(self):
        cur = self._list.currentItem()
        if not cur:
            return
        gid = cur.data(Qt.ItemDataRole.UserRole)
        groups = self._main.get_db().get_groups()
        g = next((x for x in groups if x["id"] == gid), None)
        if not g:
            return

        dlg = _GroupDialog(self, existing=g)
        if dlg.exec():
            data = dlg.result_data()
            try:
                self._main.get_db().update_group(gid, data["name"], data["color"], data["notes"])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not update group: {e}")
                return
            self.refresh()

    def _delete_group(self):
        cur = self._list.currentItem()
        if not cur:
            return
        gid = cur.data(Qt.ItemDataRole.UserRole)
        name = cur.text().strip().split("  ")[0] if cur else "this group"
        reply = QMessageBox.question(
            self, "Delete Group",
            f"Delete group '{name}'?\n\nMiners in this group will not be deleted — "
            "they will just be unassigned.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._main.get_db().delete_group(gid)
            self.refresh()
