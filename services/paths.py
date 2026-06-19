"""Centralised path resolution that works both frozen (PyInstaller) and unfrozen.

Frozen (Windows --onedir) uses a *portable* layout: config/, models/, assets/
and storage/ all live next to the executable, matching the distribution folder
described in the Windows Packaging PRD. Per the PRD, storage/ holds logs/,
pending/, screenshots/, videos/ and cache/."""
import os
import sys


def _app_dir() -> str:
    """Root of the application files.

    - frozen: the folder that contains the .exe (the --onedir distribution root)
    - source: the FatigueDesktop project folder
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*relative: str) -> str:
    """Resolve a path to a read-only resource (model, asset) next to the app.

    Falls back to the PyInstaller temp bundle (_MEIPASS) when a resource was
    embedded rather than shipped alongside the executable."""
    candidate = os.path.join(_app_dir(), *relative)
    if os.path.exists(candidate):
        return candidate
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled = os.path.join(meipass, *relative)
        if os.path.exists(bundled):
            return bundled
    return candidate


def _writable_root() -> str:
    """Writable root for config/storage. Portable: next to the executable."""
    root = _app_dir()
    try:
        os.makedirs(root, exist_ok=True)
    except OSError:
        pass
    return root


def writable_path(*relative: str) -> str:
    """Resolve (and create parent dirs for) a writable path."""
    path = os.path.join(_writable_root(), *relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def storage_dir(name: str) -> str:
    """Resolve (and create) a sub-directory under storage/."""
    path = os.path.join(_writable_root(), "storage", name)
    os.makedirs(path, exist_ok=True)
    return path


def ensure_storage() -> None:
    """Create the full storage/ tree on first run (PRD startup flow)."""
    for name in ("logs", "pending", "screenshots", "videos", "cache"):
        storage_dir(name)


CONFIG_PATH = writable_path("config", "config.json")
LOGS_DIR = storage_dir("logs")
PENDING_DIR = storage_dir("pending")
SCREENSHOTS_DIR = storage_dir("screenshots")
VIDEOS_DIR = storage_dir("videos")
CACHE_DIR = storage_dir("cache")
