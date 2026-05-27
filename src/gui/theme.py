DARK_QSS = """
/* ── Globals ──────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: #eef4ff;
}

QMainWindow, QDialog, QWidget#centralWidget {
    background-color: #0a0d12;
}

QWidget {
    background-color: transparent;
}

/* ── Sidebar ──────────────────────────────────────────────── */
QWidget#sidebar {
    background-color: #070a0f;
    border-right: 1px solid #263144;
    min-width: 72px;
    max-width: 72px;
}

QPushButton#navBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 8px;
    color: #9aa8bd;
    font-size: 20px;
    margin: 2px 10px;
    min-width: 50px;
    min-height: 46px;
}
QPushButton#navBtn:hover {
    background-color: #131a24;
    color: #eef4ff;
}
QPushButton#navBtn[active="true"] {
    background-color: #172033;
    color: #f2b84b;
    border-left: 3px solid #f2b84b;
    border-radius: 0px 8px 8px 0px;
    margin-left: 0px;
    padding-left: 11px;
}

/* ── Top Status Bar ───────────────────────────────────────── */
QWidget#topHeader {
    background-color: #0d121a;
    border-bottom: 1px solid #263144;
}
QWidget#headerBrand {
    background-color: transparent;
}
QLabel#headerTitle {
    color: #f2b84b;
    font-size: 16px;
    font-weight: 800;
}
QLabel#headerSubtitle {
    color: #9aa8bd;
    font-size: 11px;
    font-weight: 500;
}
QWidget#headerMetrics {
    background-color: transparent;
}
QLabel[metricChip="true"] {
    background-color: #111722;
    border: 1px solid #2d3a50;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 700;
    min-width: 76px;
}
QLabel#statOnline      { color: #2fbf71; border-color: #237a51; background-color: #0d1a14; }
QLabel#statOffline     { color: #ff6b6b; border-color: #97413f; background-color: #1d1011; }
QLabel#statWarning     { color: #f2b84b; border-color: #8f6b2f; background-color: #1c170d; }
QLabel#statHash        { color: #f2b84b; border-color: #8f6b2f; }
QLabel#statPower       { color: #68b8ff; border-color: #2f5f8f; }
QLabel#statEfficiency  { color: #bda8ff; border-color: #6655a3; }
QLabel#statBtc         { color: #ffb36b; border-color: #9a6030; }
QLabel#statTime        { color: #9aa8bd; }

/* ── Content Pages ────────────────────────────────────────── */
QWidget#page {
    background-color: #0a0d12;
    padding: 16px;
}

/* ── Cards ────────────────────────────────────────────────── */
QFrame#minerCard {
    background-color: #111722;
    border: 1px solid #2d3a50;
    border-radius: 8px;
    padding: 0;
}
QFrame#minerCard:hover {
    border-color: #5f7088;
}
QFrame#minerCard[status="online"]  { border-left: 3px solid #2fbf71; }
QFrame#minerCard[status="warning"] { border-left: 3px solid #f2b84b; }
QFrame#minerCard[status="offline"] { border-left: 3px solid #ff6b6b; }
QFrame#minerCard[status="error"]   { border-left: 3px solid #ff6b6b; }
QFrame#minerCard[status="unknown"] { border-left: 3px solid #4a5568; }

QWidget#batchBar {
    background-color: #101620;
    border: 1px solid #2d3a50;
    border-radius: 8px;
}

QLabel#cardName {
    font-size: 14px;
    font-weight: 700;
    color: #eef4ff;
}
QLabel#cardIP {
    font-size: 11px;
    color: #9aa8bd;
    font-family: "Consolas", monospace;
}
QLabel#cardHashrate {
    font-size: 18px;
    font-weight: 700;
    color: #f2b84b;
}
QLabel#cardUnit {
    font-size: 11px;
    color: #9aa8bd;
    padding-bottom: 2px;
}
QLabel#cardStatusBadge {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
}
QLabel#badgeOnline  { background-color: #174f35; color: #8ff0b2; }
QLabel#badgeWarning { background-color: #664b1f; color: #ffe2a3; }
QLabel#badgeOffline { background-color: #6e2b2b; color: #ffd2d2; }
QLabel#badgeUnknown { background-color: #263144; color: #9aa8bd; }

QLabel#cardMetaKey { color: #9aa8bd; font-size: 11px; }
QLabel#cardMetaVal { color: #eef4ff; font-size: 12px; font-weight: 500; }

/* ── Tables ───────────────────────────────────────────────── */
QTableWidget {
    background-color: #0d121a;
    border: 1px solid #2d3a50;
    border-radius: 8px;
    gridline-color: #202938;
    selection-background-color: #1c2635;
    alternate-background-color: #111722;
}
QTableWidget::item {
    padding: 7px 10px;
    border: none;
    color: #eef4ff;
}
QTableWidget::item:selected {
    background-color: #1c2635;
    color: #eef4ff;
}
QHeaderView::section {
    background-color: #151c27;
    color: #9aa8bd;
    font-size: 11px;
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #2d3a50;
    border-right: 1px solid #202938;
}
QHeaderView::section:last {
    border-right: none;
}
QScrollBar:vertical {
    background: #0a0d12;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #354258;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #6c7a91; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #0a0d12;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #354258;
    border-radius: 4px;
}

/* ── Buttons ──────────────────────────────────────────────── */
QPushButton {
    background-color: #1a2330;
    border: 1px solid #303d52;
    border-radius: 6px;
    padding: 7px 14px;
    color: #eef4ff;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #243044;
    border-color: #65748c;
}
QPushButton:pressed {
    background-color: #121923;
}
QPushButton:disabled {
    color: #586174;
    border-color: #202938;
    background-color: #121923;
}

QPushButton#btnPrimary {
    background-color: #b9862c;
    border-color: #f2b84b;
    color: #ffffff;
    font-weight: 700;
}
QPushButton#btnPrimary:hover {
    background-color: #d99d32;
    border-color: #ffca62;
    color: #ffffff;
}
QPushButton#btnPrimary:pressed {
    background-color: #94691f;
    border-color: #d99d32;
    color: #ffffff;
}
QPushButton#btnPrimary:disabled {
    background-color: #141c27;
    border-color: #394557;
    color: #687386;
}

QPushButton#btnDanger {
    background-color: #b93a3a;
    border-color: #d34c4c;
    color: #fff;
}
QPushButton#btnDanger:hover {
    background-color: #9f2f2f;
}

QPushButton#btnSubtle {
    background-color: #141c27;
    color: #9aa8bd;
    border-color: #2d3a50;
}
QPushButton#btnSubtle:hover {
    background-color: #1a2330;
    color: #eef4ff;
    border-color: #65748c;
}

QPushButton#btnSuccess {
    background-color: #247a4a;
    border-color: #2fbf71;
    color: #fff;
}
QPushButton#btnSuccess:hover {
    background-color: #1f6840;
}

/* ── Inputs ───────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTimeEdit {
    background-color: #0d121a;
    border: 1px solid #303d52;
    border-radius: 6px;
    padding: 6px 10px;
    color: #eef4ff;
    selection-background-color: #b9862c;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTimeEdit:focus {
    border-color: #f2b84b;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #111722;
    border: 1px solid #303d52;
    selection-background-color: #1c2635;
    color: #eef4ff;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #1a2330;
    border: none;
    width: 18px;
}

QPlainTextEdit, QTextEdit, QListWidget {
    background-color: #0d121a;
    border: 1px solid #2d3a50;
    border-radius: 8px;
    color: #eef4ff;
    selection-background-color: #1c2635;
}
QListWidget::item {
    padding: 7px 10px;
    border-bottom: 1px solid #202938;
}
QListWidget::item:selected {
    background-color: #1c2635;
    color: #eef4ff;
}
QListWidget::item:hover {
    background-color: #141c27;
}

/* ── Labels ───────────────────────────────────────────────── */
QLabel { background: transparent; }
QLabel#sectionTitle {
    font-size: 19px;
    font-weight: 700;
    color: #eef4ff;
    padding-bottom: 4px;
}
QLabel#sectionSub {
    font-size: 12px;
    color: #9aa8bd;
}

/* ── GroupBox ─────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #2d3a50;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    background-color: #111722;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #9aa8bd;
    font-size: 11px;
    font-weight: 600;
    background-color: #0a0d12;
}

/* ── CheckBox ─────────────────────────────────────────────── */
QCheckBox {
    color: #eef4ff;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #303d52;
    border-radius: 4px;
    background-color: #0d121a;
}
QCheckBox::indicator:checked {
    background-color: #f2b84b;
    border-color: #f2b84b;
}
QCheckBox::indicator:hover {
    border-color: #65748c;
}

/* ── RadioButton ──────────────────────────────────────────── */
QRadioButton {
    color: #eef4ff;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #303d52;
    border-radius: 8px;
    background-color: #0d121a;
}
QRadioButton::indicator:checked {
    background-color: #f2b84b;
    border-color: #f2b84b;
}

/* ── Separator ────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #202938;
}

/* ── Tooltips ─────────────────────────────────────────────── */
QToolTip {
    background-color: #111722;
    border: 1px solid #303d52;
    color: #eef4ff;
    padding: 4px 8px;
    border-radius: 4px;
}

/* ── Progress Bar ─────────────────────────────────────────── */
QProgressBar {
    background-color: #202938;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #f2b84b;
    border-radius: 4px;
}
QProgressBar[status="warning"]::chunk { background-color: #f2b84b; }
QProgressBar[status="critical"]::chunk { background-color: #ff6b6b; }
QProgressBar[status="good"]::chunk { background-color: #2fbf71; }

/* ── Tab Widget ───────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #2d3a50;
    border-radius: 8px;
    background-color: #111722;
}
QTabBar::tab {
    background-color: #0d121a;
    color: #9aa8bd;
    padding: 8px 16px;
    border: 1px solid #2d3a50;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #111722;
    color: #eef4ff;
    border-bottom: 2px solid #f2b84b;
}
QTabBar::tab:hover:!selected {
    background-color: #141c27;
    color: #eef4ff;
}

/* ── Splitter ─────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #202938;
    width: 1px;
    height: 1px;
}

QMenu {
    background-color: #111722;
    border: 1px solid #303d52;
    color: #eef4ff;
}
QMenu::item {
    padding: 7px 22px;
}
QMenu::item:selected {
    background-color: #1c2635;
}

/* ── Message/Status ───────────────────────────────────────── */
QStatusBar {
    background-color: #070a0f;
    color: #9aa8bd;
    font-size: 11px;
    border-top: 1px solid #263144;
}
"""


STATUS_COLORS = {
    "online":  "#2fbf71",
    "warning": "#f2b84b",
    "offline": "#ff6b6b",
    "error":   "#ff6b6b",
    "unknown": "#9aa8bd",
}

BITCOIN_ORANGE = "#f2b84b"
BG_DARK = "#0a0d12"
BG_CARD = "#111722"
BG_SURFACE = "#172033"
BORDER_COLOR = "#2d3a50"
TEXT_PRIMARY = "#eef4ff"
TEXT_MUTED = "#9aa8bd"
