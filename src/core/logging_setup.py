import logging
import os
from logging.handlers import RotatingFileHandler


def _log_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "RigAlert", "logs")
    os.makedirs(path, exist_ok=True)
    return path


def setup_logging() -> str:
    """Configure app-wide logging once; safe for PyInstaller and repeated imports."""
    log_path = os.path.join(_log_dir(), "rigalert.log")
    root = logging.getLogger()
    if any(getattr(h, "_rigalert_handler", False) for h in root.handlers):
        return log_path

    root.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler._rigalert_handler = True
    root.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console._rigalert_handler = True
    root.addHandler(console)

    logging.getLogger(__name__).info("Logging initialized at %s", log_path)
    return log_path
