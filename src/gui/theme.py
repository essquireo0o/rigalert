# ── Enterprise color tokens ───────────────────────────────────────────────────
BG_BASE     = "#0d1117"
BG_SURFACE  = "#161b22"
BG_ELEVATED = "#1c2230"
BG_HOVER    = "#21273a"
BORDER      = "#21262d"
BORDER_STRONG = "#30363d"
TEXT_PRIMARY  = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED    = "#484f58"
BITCOIN_ORANGE = "#e3a030"
STATUS_GREEN   = "#3fb950"
STATUS_RED     = "#f85149"
STATUS_AMBER   = "#d29922"
STATUS_BLUE    = "#58a6ff"

# Legacy aliases used by other modules
BG_DARK    = BG_BASE
BG_CARD    = BG_SURFACE
BG_SURFACE = BG_SURFACE
BORDER_COLOR = BORDER_STRONG
TEXT_MUTED   = TEXT_SECONDARY

STATUS_COLORS = {
    "online":  STATUS_GREEN,
    "warning": STATUS_AMBER,
    "offline": STATUS_RED,
    "error":   STATUS_RED,
    "unknown": TEXT_MUTED,
}

DARK_QSS = """
/* ═══════════════════════════════════════════════════════════════
   RigAlert Enterprise Theme
   Palette: GitHub Dark · Spacing: 4 px grid · Font: Segoe UI
   ═══════════════════════════════════════════════════════════════ */

* {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: #e6edf3;
    outline: none;
}

QMainWindow, QDialog, QWidget#centralWidget {
    background-color: #0d1117;
}

QWidget { background-color: transparent; }


/* ── Sidebar ──────────────────────────────────────────────────── */
QWidget#sidebar {
    background-color: #010409;
    border-right: 1px solid #21262d;
    min-width: 188px;
    max-width: 188px;
}

QLabel#sidebarLogo {
    padding: 20px 0 12px 0;
    background: transparent;
}

QWidget#sidebarDivider {
    background: #21262d;
    max-height: 1px;
    margin: 0 16px;
}

QPushButton#navBtn {
    background-color: transparent;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 0px;
    padding: 10px 16px 10px 14px;
    color: #8b949e;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    min-height: 40px;
    margin: 0;
}
QPushButton#navBtn:hover {
    background-color: #161b22;
    color: #e6edf3;
    border-left-color: #30363d;
}
QPushButton#navBtn[active="true"] {
    background-color: #1c2230;
    color: #e3a030;
    font-weight: 600;
    border-left: 2px solid #e3a030;
}

QLabel#sidebarVersion {
    color: #30363d;
    font-size: 11px;
    padding: 12px 0;
    background: transparent;
}


/* ── Top Header ───────────────────────────────────────────────── */
QWidget#topHeader {
    background-color: #010409;
    border-bottom: 1px solid #21262d;
    min-height: 58px;
    max-height: 58px;
}

QLabel#headerTitle {
    color: #e3a030;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.2px;
    background: transparent;
}
QLabel#headerSubtitle {
    color: #484f58;
    font-size: 11px;
    font-weight: 400;
    background: transparent;
}

/* Metric chips */
QLabel[metricChip="true"] {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 5px 11px;
    font-size: 11px;
    font-weight: 600;
    min-width: 82px;
}
QLabel#statOnline     { color: #3fb950; border-color: #1a3d24; background-color: #0b1a10; }
QLabel#statOffline    { color: #f85149; border-color: #3d1515; background-color: #190909; }
QLabel#statWarning    { color: #d29922; border-color: #3d2e00; background-color: #1a1400; }
QLabel#statHash       { color: #e3a030; border-color: #3d2a00; background-color: #161b22; }
QLabel#statPower      { color: #58a6ff; border-color: #1a3358; background-color: #161b22; }
QLabel#statEfficiency { color: #8957e5; border-color: #2d1f5c; background-color: #161b22; }
QLabel#statBtc        { color: #c9d1d9; border-color: #21262d; background-color: #161b22; }
QLabel#statTime       { color: #8b949e; background-color: #161b22; }


/* ── Page ─────────────────────────────────────────────────────── */
QWidget#page {
    background-color: #0d1117;
}

QLabel#sectionTitle {
    font-size: 17px;
    font-weight: 700;
    color: #e6edf3;
    background: transparent;
}
QLabel#sectionSub {
    font-size: 12px;
    color: #8b949e;
    background: transparent;
}


/* ── Miner Cards ──────────────────────────────────────────────── */
QFrame#minerCard {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-left: 3px solid #21262d;
    border-radius: 8px;
}
QFrame#minerCard:hover {
    background-color: #1c2230;
    border-color: #30363d;
}
QFrame#minerCard[status="online"]  { border-left: 3px solid #3fb950; }
QFrame#minerCard[status="warning"] { border-left: 3px solid #d29922; }
QFrame#minerCard[status="offline"] { border-left: 3px solid #f85149; }
QFrame#minerCard[status="error"]   { border-left: 3px solid #f85149; }
QFrame#minerCard[status="unknown"] { border-left: 3px solid #30363d; }


/* ── Tables ───────────────────────────────────────────────────── */
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 6px;
    gridline-color: #21262d;
    selection-background-color: #1c2736;
    alternate-background-color: #161b22;
    color: #e6edf3;
}
QTableWidget::item {
    padding: 9px 12px;
    border: none;
    color: #c9d1d9;
}
QTableWidget::item:selected {
    background-color: #1c2736;
    color: #e6edf3;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid #21262d;
    border-right: 1px solid #21262d;
    text-transform: uppercase;
}
QHeaderView::section:last { border-right: none; }


/* ── Scrollbars ───────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 2px 0;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 3px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover { background: #484f58; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::corner { background: transparent; }


/* ── Buttons ──────────────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 16px;
    color: #c9d1d9;
    font-weight: 500;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
    color: #e6edf3;
}
QPushButton:pressed {
    background-color: #161b22;
    border-color: #484f58;
}
QPushButton:disabled {
    color: #484f58;
    border-color: #21262d;
    background-color: #161b22;
}

QPushButton#btnPrimary {
    background-color: #e3a030;
    border-color: #c88a24;
    color: #0d1117;
    font-weight: 700;
}
QPushButton#btnPrimary:hover {
    background-color: #f2b84b;
    border-color: #e3a030;
    color: #0d1117;
}
QPushButton#btnPrimary:pressed {
    background-color: #c88a24;
    border-color: #a36e18;
    color: #0d1117;
}
QPushButton#btnPrimary:disabled {
    background-color: #2a2010;
    border-color: #3a2e10;
    color: #5a4a1a;
}

QPushButton#btnDanger {
    background-color: #da3633;
    border-color: #f85149;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#btnDanger:hover { background-color: #b91c1c; }

QPushButton#btnSubtle {
    background-color: transparent;
    color: #8b949e;
    border-color: #30363d;
}
QPushButton#btnSubtle:hover {
    background-color: #21262d;
    color: #e6edf3;
    border-color: #484f58;
}

QPushButton#btnSuccess {
    background-color: #1a7f37;
    border-color: #3fb950;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#btnSuccess:hover { background-color: #116329; }


/* ── Inputs ───────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTimeEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #c9d1d9;
    selection-background-color: #e3a030;
    selection-color: #0d1117;
    min-height: 28px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTimeEdit:focus {
    border-color: #58a6ff;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: #484f58;
}

QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow { width: 10px; height: 10px; }
QComboBox QAbstractItemView {
    background-color: #1c2230;
    border: 1px solid #30363d;
    border-radius: 6px;
    selection-background-color: #1c2736;
    color: #c9d1d9;
    padding: 4px;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #21262d;
    border: none;
    width: 18px;
}

QPlainTextEdit, QTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #c9d1d9;
    selection-background-color: #1c2736;
}

QListWidget {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 6px;
    color: #c9d1d9;
    selection-background-color: #1c2736;
}
QListWidget::item {
    padding: 9px 12px;
    border-bottom: 1px solid #21262d;
}
QListWidget::item:selected { background-color: #1c2736; color: #e6edf3; }
QListWidget::item:hover { background-color: #161b22; }


/* ── Labels ───────────────────────────────────────────────────── */
QLabel { background: transparent; }


/* ── GroupBox ─────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #21262d;
    border-radius: 8px;
    margin-top: 18px;
    padding: 16px;
    background-color: #161b22;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #8b949e;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    background-color: #0d1117;
}


/* ── CheckBox ─────────────────────────────────────────────────── */
QCheckBox { color: #c9d1d9; spacing: 8px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #30363d;
    border-radius: 4px;
    background-color: #0d1117;
}
QCheckBox::indicator:checked { background-color: #e3a030; border-color: #e3a030; }
QCheckBox::indicator:hover { border-color: #8b949e; }


/* ── RadioButton ──────────────────────────────────────────────── */
QRadioButton { color: #c9d1d9; spacing: 8px; }
QRadioButton::indicator {
    width: 15px; height: 15px;
    border: 1px solid #30363d;
    border-radius: 8px;
    background-color: #0d1117;
}
QRadioButton::indicator:checked { background-color: #e3a030; border-color: #e3a030; }


/* ── Separators ───────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #21262d; background: #21262d; }


/* ── Tooltips ─────────────────────────────────────────────────── */
QToolTip {
    background-color: #1c2230;
    border: 1px solid #30363d;
    color: #c9d1d9;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 12px;
}


/* ── Progress Bars ────────────────────────────────────────────── */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 3px;
    height: 4px;
}
QProgressBar::chunk            { background-color: #e3a030; border-radius: 3px; }
QProgressBar[status="good"]::chunk     { background-color: #3fb950; }
QProgressBar[status="warning"]::chunk  { background-color: #d29922; }
QProgressBar[status="critical"]::chunk { background-color: #f85149; }


/* ── Tabs ─────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #21262d;
    border-radius: 6px;
    background-color: #161b22;
}
QTabBar::tab {
    background-color: transparent;
    color: #8b949e;
    padding: 9px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
    margin-right: 4px;
}
QTabBar::tab:selected {
    color: #e6edf3;
    border-bottom: 2px solid #e3a030;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    color: #c9d1d9;
    background-color: #161b22;
    border-radius: 6px 6px 0 0;
}


/* ── Menus ────────────────────────────────────────────────────── */
QMenu {
    background-color: #1c2230;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #c9d1d9;
    padding: 6px 0;
}
QMenu::item {
    padding: 8px 20px;
    border-radius: 4px;
    margin: 2px 6px;
}
QMenu::item:selected { background-color: #21262d; color: #e6edf3; }
QMenu::separator { height: 1px; background: #21262d; margin: 4px 0; }


/* ── Status Bar ───────────────────────────────────────────────── */
QStatusBar {
    background-color: #010409;
    color: #8b949e;
    font-size: 11px;
    border-top: 1px solid #21262d;
    padding: 0 4px;
}
QStatusBar::item { border: none; }


/* ── Splitter ─────────────────────────────────────────────────── */
QSplitter::handle { background-color: #21262d; width: 1px; height: 1px; }
"""
