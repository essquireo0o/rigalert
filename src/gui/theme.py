DARK_QSS = """
/* ── Globals ──────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: #e6edf3;
}

QMainWindow, QDialog, QWidget#centralWidget {
    background-color: #0d1117;
}

QWidget {
    background-color: transparent;
}

/* ── Sidebar ──────────────────────────────────────────────── */
QWidget#sidebar {
    background-color: #010409;
    border-right: 1px solid #21262d;
    min-width: 64px;
    max-width: 64px;
}

QPushButton#navBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 12px 8px;
    color: #8b949e;
    font-size: 20px;
    margin: 2px 8px;
    min-width: 48px;
    min-height: 48px;
}
QPushButton#navBtn:hover {
    background-color: #161b22;
    color: #e6edf3;
}
QPushButton#navBtn[active="true"] {
    background-color: #1c2128;
    color: #c8a94b;
    border-left: 2px solid #c8a94b;
    border-radius: 0px 8px 8px 0px;
    margin-left: 0px;
    padding-left: 10px;
}

/* ── Top Status Bar ───────────────────────────────────────── */
QWidget#statusBar {
    background-color: #010409;
    border-bottom: 1px solid #21262d;
    min-height: 48px;
    max-height: 48px;
    padding: 0 16px;
}

QLabel#statLabel {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}
QLabel#statOnline  { color: #3fb950; border-color: #238636; }
QLabel#statOffline { color: #f85149; border-color: #da3633; }
QLabel#statWarning { color: #d29922; border-color: #9e6a03; }
QLabel#statHash    { color: #c8a94b; border-color: #7a6820; }
QLabel#statTime    { color: #8b949e; }

/* ── Content Pages ────────────────────────────────────────── */
QWidget#page {
    background-color: #0d1117;
    padding: 16px;
}

/* ── Cards ────────────────────────────────────────────────── */
QFrame#minerCard {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 0;
}
QFrame#minerCard:hover {
    border-color: #8b949e;
}
QFrame#minerCard[status="online"]  { border-left: 3px solid #3fb950; }
QFrame#minerCard[status="warning"] { border-left: 3px solid #d29922; }
QFrame#minerCard[status="offline"] { border-left: 3px solid #f85149; }
QFrame#minerCard[status="error"]   { border-left: 3px solid #f85149; }
QFrame#minerCard[status="unknown"] { border-left: 3px solid #30363d; }

QLabel#cardName {
    font-size: 14px;
    font-weight: 700;
    color: #e6edf3;
}
QLabel#cardIP {
    font-size: 11px;
    color: #8b949e;
    font-family: "Consolas", monospace;
}
QLabel#cardHashrate {
    font-size: 18px;
    font-weight: 700;
    color: #c8a94b;
}
QLabel#cardUnit {
    font-size: 11px;
    color: #8b949e;
    padding-bottom: 2px;
}
QLabel#cardStatusBadge {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
}
QLabel#badgeOnline  { background-color: #238636; color: #aff5b4; }
QLabel#badgeWarning { background-color: #9e6a03; color: #fae17d; }
QLabel#badgeOffline { background-color: #da3633; color: #ffdcd7; }
QLabel#badgeUnknown { background-color: #30363d; color: #8b949e; }

QLabel#cardMetaKey { color: #8b949e; font-size: 11px; }
QLabel#cardMetaVal { color: #e6edf3; font-size: 12px; font-weight: 500; }

/* ── Tables ───────────────────────────────────────────────── */
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    gridline-color: #21262d;
    selection-background-color: #1c2128;
    alternate-background-color: #0d1117;
}
QTableWidget::item {
    padding: 6px 10px;
    border: none;
    color: #e6edf3;
}
QTableWidget::item:selected {
    background-color: #1c2128;
    color: #e6edf3;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #30363d;
    border-right: 1px solid #21262d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QHeaderView::section:last {
    border-right: none;
}
QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #8b949e; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #0d1117;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
}

/* ── Buttons ──────────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
    color: #e6edf3;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QPushButton:pressed {
    background-color: #161b22;
}
QPushButton:disabled {
    color: #484f58;
    border-color: #21262d;
}

QPushButton#btnPrimary {
    background-color: #c8a94b;
    border-color: #c8a94b;
    color: #000;
    font-weight: 700;
}
QPushButton#btnPrimary:hover {
    background-color: #b8963a;
    border-color: #b8963a;
}

QPushButton#btnDanger {
    background-color: #da3633;
    border-color: #da3633;
    color: #fff;
}
QPushButton#btnDanger:hover {
    background-color: #b91c1c;
}

QPushButton#btnSuccess {
    background-color: #238636;
    border-color: #238636;
    color: #fff;
}
QPushButton#btnSuccess:hover {
    background-color: #1a7f37;
}

/* ── Inputs ───────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTimeEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e6edf3;
    selection-background-color: #c8a94b;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTimeEdit:focus {
    border-color: #c8a94b;
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
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1c2128;
    color: #e6edf3;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #21262d;
    border: none;
    width: 18px;
}

/* ── Labels ───────────────────────────────────────────────── */
QLabel { background: transparent; }
QLabel#sectionTitle {
    font-size: 18px;
    font-weight: 700;
    color: #e6edf3;
    padding-bottom: 4px;
}
QLabel#sectionSub {
    font-size: 12px;
    color: #8b949e;
}

/* ── GroupBox ─────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    background-color: #161b22;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    background-color: #0d1117;
}

/* ── CheckBox ─────────────────────────────────────────────── */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #30363d;
    border-radius: 4px;
    background-color: #0d1117;
}
QCheckBox::indicator:checked {
    background-color: #c8a94b;
    border-color: #c8a94b;
}
QCheckBox::indicator:hover {
    border-color: #8b949e;
}

/* ── RadioButton ──────────────────────────────────────────── */
QRadioButton {
    color: #e6edf3;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #30363d;
    border-radius: 8px;
    background-color: #0d1117;
}
QRadioButton::indicator:checked {
    background-color: #c8a94b;
    border-color: #c8a94b;
}

/* ── Separator ────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #21262d;
}

/* ── Tooltips ─────────────────────────────────────────────── */
QToolTip {
    background-color: #161b22;
    border: 1px solid #30363d;
    color: #e6edf3;
    padding: 4px 8px;
    border-radius: 4px;
}

/* ── Progress Bar ─────────────────────────────────────────── */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #c8a94b;
    border-radius: 4px;
}
QProgressBar[status="warning"]::chunk { background-color: #d29922; }
QProgressBar[status="critical"]::chunk { background-color: #f85149; }
QProgressBar[status="good"]::chunk { background-color: #3fb950; }

/* ── Tab Widget ───────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 8px;
    background-color: #161b22;
}
QTabBar::tab {
    background-color: #0d1117;
    color: #8b949e;
    padding: 8px 16px;
    border: 1px solid #30363d;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #161b22;
    color: #e6edf3;
    border-bottom: 2px solid #c8a94b;
}
QTabBar::tab:hover:!selected {
    background-color: #161b22;
    color: #e6edf3;
}

/* ── Splitter ─────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #21262d;
    width: 1px;
    height: 1px;
}

/* ── Message/Status ───────────────────────────────────────── */
QStatusBar {
    background-color: #010409;
    color: #8b949e;
    font-size: 11px;
    border-top: 1px solid #21262d;
}
"""


STATUS_COLORS = {
    "online":  "#3fb950",
    "warning": "#d29922",
    "offline": "#f85149",
    "error":   "#f85149",
    "unknown": "#8b949e",
}

BITCOIN_ORANGE = "#c8a94b"
BG_DARK = "#0d1117"
BG_CARD = "#161b22"
BG_SURFACE = "#1c2128"
BORDER_COLOR = "#30363d"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED = "#8b949e"
