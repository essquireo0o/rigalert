import sys
import os


def get_app_dir() -> str:
    """Folder containing the running EXE (frozen) or the project root (source).
    Config and database live here so the whole app folder is self-contained
    and can be copied to another machine with credentials intact."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
