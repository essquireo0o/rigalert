import sys
import os

# Ensure src/ is importable when run directly or as frozen EXE
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
import pathlib

from src.gui.main_window import MainWindow


def main():
    # High-DPI support
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("RigAlert")
    app.setApplicationDisplayName("RigAlert™ by ING Mining")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ING Mining")

    ico = pathlib.Path(__file__).parent / "rigalert.ico"
    if ico.exists():
        app.setWindowIcon(QIcon(str(ico)))

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
