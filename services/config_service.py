"""Configuration manager: reads/writes config/config.json and mirrors values to env."""
import copy
import json
import os

from PySide6.QtCore import QObject, Signal

from services.paths import CONFIG_PATH

DEFAULT_CONFIG = {
    "backend": {
        "api_url": "",
        "device_token": "",
        "source_device": "raspberrypi-01",
        "pending_file": "pending/pending.jsonl",
    },
    "desktop": {
        "username": "admin",
        "password": "",
    },
    "detection": {
        "eye_closed_threshold": 15,
        "eye_closed_secs_1": 15,
        "eye_closed_secs_2": 30,
        "eye_open_reset_secs": 0.4,
        "min_confidence": 0.8,
    },
    "yawn": {
        "limit": 3,
        "time_window": 60,
        "frame_threshold": 5,
    },
    "event": {
        "backend_url": "",
        "backend_token": "",
    },
    # ---- v1.2 future features ----
    "camera": {
        "camera_type": "integrated",  # integrated | usb | virtual | rtsp | http
        "camera_index": 0,
        "camera_url": "",
        "auto_refresh": True,
    },
    "recording": {
        "enabled": True,
        "duration": 30,        # total seconds (buffer + after-event)
        "buffer_seconds": 10,  # seconds kept before the event
    },
    "screenshot": {
        "enabled": True,
        "overlay": True,
    },
    "theme": {
        "mode": "system",  # light | dark | system
    },
    "tray": {
        "enabled": True,
        "start_minimized": False,
    },
}

# config (section, key) -> environment variable name used by the detection code.
ENV_MAP = {
    ("backend", "api_url"): "Fatigue_API_URL",
    ("backend", "device_token"): "Fatigue_DEVICE_TOKEN",
    ("backend", "source_device"): "Fatigue_SOURCE_DEVICE",
    ("backend", "pending_file"): "Fatigue_PENDING_FILE",
    ("desktop", "username"): "Fatigue_DESKTOP_USERNAME",
    ("desktop", "password"): "Fatigue_DESKTOP_PASSWORD",
    ("detection", "eye_closed_threshold"): "EYE_CLOSED_THRESHOLD",
    ("detection", "eye_closed_secs_1"): "EYE_CLOSED_SECS_1",
    ("detection", "eye_closed_secs_2"): "EYE_CLOSED_SECS_2",
    ("detection", "eye_open_reset_secs"): "EYE_OPEN_RESET_SECS",
    ("detection", "min_confidence"): "MIN_CONFIDENCE",
    ("yawn", "limit"): "YAWN_LIMIT",
    ("yawn", "time_window"): "TIME_WINDOW",
    ("yawn", "frame_threshold"): "YAWN_FRAME_THRESHOLD",
    ("event", "backend_url"): "BACKEND_EVENT_URL",
    ("event", "backend_token"): "BACKEND_DEVICE_TOKEN",
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Return base updated with override, keeping defaults for missing keys."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class ConfigService(QObject):
    """Single source of truth for application configuration."""

    changed = Signal(dict)

    def __init__(self, path: str = CONFIG_PATH):
        super().__init__()
        self.path = path
        self._data = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    # ------------------------------------------------------------------ load
    def load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                self._data = _deep_merge(DEFAULT_CONFIG, stored)
            except (json.JSONDecodeError, OSError):
                self._data = copy.deepcopy(DEFAULT_CONFIG)
        else:
            self._data = copy.deepcopy(DEFAULT_CONFIG)
            self.save()
        self.apply_to_env()
        return self._data

    # ------------------------------------------------------------------ save
    def save(self, data: dict | None = None) -> None:
        if data is not None:
            self._data = _deep_merge(DEFAULT_CONFIG, data)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
        self.apply_to_env()
        self.changed.emit(self._data)

    def restore_defaults(self) -> dict:
        self._data = copy.deepcopy(DEFAULT_CONFIG)
        self.save()
        return self._data

    # --------------------------------------------------------------- access
    @property
    def data(self) -> dict:
        return copy.deepcopy(self._data)

    def section(self, name: str) -> dict:
        return copy.deepcopy(self._data.get(name, {}))

    def get(self, section: str, key: str, default=None):
        return self._data.get(section, {}).get(key, default)

    # ----------------------------------------------------------------- env
    def apply_to_env(self) -> None:
        """Mirror config values into os.environ for os.getenv() compatibility."""
        for (section, key), env_name in ENV_MAP.items():
            value = self._data.get(section, {}).get(key)
            if value is not None:
                os.environ[env_name] = str(value)
