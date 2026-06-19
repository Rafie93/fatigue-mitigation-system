"""Application entry point.

Flow: QApplication -> Splash (loads config + AI model on a worker thread) ->
Home Dashboard. The camera is NOT opened until the user presses Start Camera.
"""
import os
import sys

# Quieter TensorFlow logs before it is imported anywhere.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

# Make the package importable when run as a plain script (python app.py).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from services.backend_service import BackendService
from services.config_service import ConfigService
from services.detection_service import DetectionEngine
from services.event_service import EventService
from services.logging_setup import setup_logging
from services.paths import ensure_storage
from services.theme_manager import apply_theme
from ui.icons import app_icon
from ui.main_window import MainWindow
from ui.splash import SplashScreen
from viewmodels.detection_viewmodel import DetectionViewModel


def main() -> int:
    app = QApplication(sys.argv)
    app.setWindowIcon(app_icon())

    # --- startup: create storage folders + logging, then load config ---
    ensure_storage()
    logger = setup_logging()
    logger.info("Starting Fatigue Mitigation System")

    # --- services (config loaded immediately; model loaded on splash) ---
    config = ConfigService()
    apply_theme(app, config.get("theme", "mode", "system"))
    engine = DetectionEngine()
    backend = BackendService(config)
    events = EventService(config, backend)
    detection_vm = DetectionViewModel(engine, config, events)

    # With the system tray enabled, closing the window only hides it.
    if config.get("tray", "enabled", True):
        app.setQuitOnLastWindowClosed(False)

    splash = SplashScreen(engine)
    splash.show()
    splash.start()

    window_holder = {}

    def on_loaded():
        window = MainWindow(app, engine, config, backend, events, detection_vm)
        window_holder["window"] = window
        if config.get("tray", "enabled", True) and config.get("tray", "start_minimized", False):
            pass  # stay hidden in tray
        else:
            window.show()
        splash.close()

    splash.done.connect(on_loaded)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
