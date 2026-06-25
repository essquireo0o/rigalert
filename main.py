import sys
import os

# Ensure src/ is importable when run directly or as frozen EXE
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
import pathlib


def _enforce_single_instance():
    """
    Create a named Windows mutex. If it already exists another instance is
    running — bring that window to the foreground and return False so the
    caller can exit immediately.
    """
    import ctypes
    MUTEX_NAME = "Global\\RigAlertByINGMining_SingleInstance"
    ERROR_ALREADY_EXISTS = 183

    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        # Find the existing window by scanning all top-level windows
        found = ctypes.c_int(0)

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        def _cb(hwnd, _lparam):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if "RigAlert" in buf.value:
                found.value = hwnd
                return False  # stop enumeration
            return True

        ctypes.windll.user32.EnumWindows(_cb, 0)
        hwnd = found.value
        if hwnd:
            # Restore minimised window and bring to front
            ctypes.windll.user32.ShowWindow(hwnd, 9)   # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        return False  # caller should exit
    return True  # we are the only instance; keep the mutex alive


def main():
    if not _enforce_single_instance():
        sys.exit(0)

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

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    start_minimized = "--minimized" in sys.argv

    from src.gui.main_window import MainWindow
    from src.core.config import AppConfig
    from src.core.licensing import validate_license

    cfg = AppConfig.load()
    license_ok, license_msg = validate_license(cfg)
    if not license_ok:
        QMessageBox.critical(
            None, "RigAlert — License Required",
            f"{license_msg}\n\nContact support@ingmining.com to obtain a license.",
        )
        sys.exit(1)

    window = MainWindow(start_minimized=start_minimized)
    if not start_minimized:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
