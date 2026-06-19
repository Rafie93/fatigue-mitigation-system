"""Fast, headless CI smoke test (no camera, no display, no model download).

Verifies the app's services/UI import and wire up correctly so the packaging
pipeline can fail early before the (slow) PyInstaller step."""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np

# Avoid touching real camera hardware on the runner.
import services.camera_discovery as cd
from services.camera_discovery import CameraDevice
cd.discover_cameras = lambda max_index=6: [CameraDevice(0, "Test Camera", "integrated")]

from PySide6.QtWidgets import QApplication

from services.config_service import ConfigService, DEFAULT_CONFIG
from services.paths import ensure_storage, CONFIG_PATH
from services.recorder_service import ScreenshotSaver, VideoRecorder
from services.theme_manager import stylesheet_for

app = QApplication(sys.argv)

ensure_storage()
assert os.path.isdir(os.path.join(ROOT, "storage", "screenshots"))
print("[ci] storage tree ok")

config = ConfigService()
assert os.path.exists(CONFIG_PATH), "config not created"
for section in DEFAULT_CONFIG:
    assert section in config.data, f"missing config section {section}"
print("[ci] config ok")

assert "0f1419" in stylesheet_for("dark")
assert "f3f4f6" in stylesheet_for("light")
print("[ci] themes ok")

shot = ScreenshotSaver(overlay=True)
ev = {"event_type": "yawn_alert", "status_text": "WARN", "meta": {"conf_eye": 0.9, "conf_mouth": 0.2}}
spath = shot.save((np.random.rand(120, 160, 3) * 255).astype("uint8"), ev,
                  {"eye_confidence": 0.9, "mouth_confidence": 0.2}, "Test")
assert spath and os.path.exists(spath)
os.remove(spath)
print("[ci] screenshot ok")

rec = VideoRecorder(buffer_seconds=1, duration=2)
rec.set_fps(8)
for _ in range(20):
    rec.push((np.random.rand(120, 160, 3) * 255).astype("uint8"))
rec.trigger("micro_sleep")
for _ in range(20):
    rec.push((np.random.rand(120, 160, 3) * 255).astype("uint8"))
saved = rec.last_saved
rec.stop()
assert saved and os.path.exists(saved)
os.remove(saved)
print("[ci] recorder ok")

# UI imports (construct the heavy widgets without a real model).
from ui.home import HomeView
from ui.settings import SettingsView
from ui.detection import DetectionView
SettingsView(config)
HomeView()
DetectionView()
print("[ci] ui ok")

print("CI SMOKE PASSED")
