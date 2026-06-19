"""Centralised path resolution that works both frozen (PyInstaller) and unfrozen."""
import os
import sys


def _base_dir() -> str:
    """Directory that contains app.py / main.py (or the PyInstaller bundle root)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*relative: str) -> str:
    """Resolve a path to a bundled (read-only) resource such as a model file."""
    return os.path.join(_base_dir(), *relative)


def _writable_root() -> str:
    """A writable directory for config/pending/logs.

    When unfrozen we keep everything inside the project folder. When frozen we
    fall back to a per-user application-support directory because the bundle is
    read-only.
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            root = os.path.join(
                os.path.expanduser("~"), "Library", "Application Support", "FatigueDesktop"
            )
        elif sys.platform.startswith("win"):
            root = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "FatigueDesktop")
        else:
            root = os.path.join(os.path.expanduser("~"), ".fatigue_desktop")
    else:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(root, exist_ok=True)
    return root


def writable_path(*relative: str) -> str:
    """Resolve (and create parent dirs for) a writable path."""
    path = os.path.join(_writable_root(), *relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def storage_dir(name: str) -> str:
    """Resolve (and create) a sub-directory under storage/ (v1.2 layout)."""
    path = os.path.join(_writable_root(), "storage", name)
    os.makedirs(path, exist_ok=True)
    return path


CONFIG_PATH = writable_path("config", "config.json")
PENDING_DIR = writable_path("pending", ".keep").rsplit(os.sep, 1)[0]
LOGS_DIR = writable_path("logs", ".keep").rsplit(os.sep, 1)[0]
SCREENSHOTS_DIR = storage_dir("screenshots")
VIDEOS_DIR = storage_dir("videos")
CACHE_DIR = storage_dir("cache")
