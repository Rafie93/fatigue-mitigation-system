"""Main application window: hosts the stacked pages, status bar and wiring.

v1.2 adds: multi-camera selection, theme manager, system tray (keep running in
background), and desktop notifications for alerts."""
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel, QMainWindow, QMenu, QMessageBox, QStackedWidget, QStatusBar,
    QSystemTrayIcon, QWidget,
)

from services.camera_discovery import discover_cameras
from services.system_monitor import SystemMonitor
from services.theme_manager import apply_theme
from ui.about import AboutView
from ui.detection import DetectionView
from ui.event_history import EventHistoryView
from ui.home import HomeView
from ui.icons import app_icon
from ui.settings import SettingsView
from ui.theme import APP_NAME


class BackendPinger(QThread):
    """Periodically checks backend reachability without blocking the GUI."""

    result = Signal(bool)

    def __init__(self, backend_service):
        super().__init__()
        self.backend = backend_service
        self._running = True

    def run(self) -> None:
        while self._running:
            self.result.emit(self.backend.check_connection())
            for _ in range(100):  # ~10s, responsive shutdown
                if not self._running:
                    return
                self.msleep(100)

    def stop(self) -> None:
        self._running = False
        self.wait(1500)


class MainWindow(QMainWindow):
    PAGE_HOME = 0
    PAGE_DETECTION = 1
    PAGE_SETTINGS = 2
    PAGE_HISTORY = 3
    PAGE_ABOUT = 4

    def __init__(self, app, engine, config_service, backend_service, event_service,
                 detection_vm):
        super().__init__()
        self.app = app
        self.engine = engine
        self.config = config_service
        self.backend = backend_service
        self.events = event_service
        self.vm = detection_vm

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(1080, 720)

        self._backend_connected = False
        self._force_quit = False
        self._build_pages()
        self._build_status_bar()
        self._build_tray()
        self._wire()
        self._populate_cameras()
        self._refresh_home()

        # Background backend polling.
        self._pinger = BackendPinger(self.backend)
        self._pinger.result.connect(self._on_backend_status)
        self._pinger.start()

        self._monitor = SystemMonitor()
        self._monitor.updated.connect(self._on_system_stats)

    # --------------------------------------------------------- pages
    def _build_pages(self) -> None:
        self.stack = QStackedWidget()
        self.home = HomeView()
        self.detection = DetectionView()
        self.settings = SettingsView(self.config)
        self.history = EventHistoryView(self.events)
        self.about = AboutView()
        for w in (self.home, self.detection, self.settings, self.history, self.about):
            self.stack.addWidget(w)
        self.setCentralWidget(self.stack)

    def _build_status_bar(self) -> None:
        bar = QStatusBar()
        self.setStatusBar(bar)
        self.sb_camera = QLabel("Camera: Offline")
        self.sb_backend = QLabel("Backend: --")
        self.sb_fps = QLabel("FPS: 0")
        self.sb_cpu = QLabel("CPU: 0%")
        self.sb_ram = QLabel("RAM: 0 MB")
        for lbl in (self.sb_camera, self.sb_backend, self.sb_fps, self.sb_cpu, self.sb_ram):
            bar.addWidget(lbl)
            bar.addWidget(self._sep())

    @staticmethod
    def _sep() -> QLabel:
        return QLabel("   ")

    # --------------------------------------------------------- system tray
    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip(APP_NAME)
        menu = QMenu()

        self._act_open = QAction("Open Dashboard", self)
        self._act_open.triggered.connect(self._show_window)
        self._act_start = QAction("Start Camera", self)
        self._act_start.triggered.connect(self._start_detection)
        self._act_stop = QAction("Stop Camera", self)
        self._act_stop.triggered.connect(self._stop_detection)
        self._act_settings = QAction("Settings", self)
        self._act_settings.triggered.connect(lambda: self._show_page(self.PAGE_SETTINGS))
        self._act_history = QAction("Event History", self)
        self._act_history.triggered.connect(lambda: self._show_page(self.PAGE_HISTORY))
        self._act_about = QAction("About", self)
        self._act_about.triggered.connect(lambda: self._show_page(self.PAGE_ABOUT))
        self._act_exit = QAction("Exit", self)
        self._act_exit.triggered.connect(self._real_quit)

        for act in (self._act_open, self._act_start, self._act_stop):
            menu.addAction(act)
        menu.addSeparator()
        for act in (self._act_settings, self._act_history, self._act_about):
            menu.addAction(act)
        menu.addSeparator()
        menu.addAction(self._act_exit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        if self.config.get("tray", "enabled", True):
            self.tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:  # left click
            self._show_window()

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _show_page(self, index: int) -> None:
        self._go(index)
        self._show_window()

    # --------------------------------------------------------- wiring
    def _wire(self) -> None:
        # Home navigation
        self.home.start_camera.connect(self._start_detection)
        self.home.open_configuration.connect(lambda: self._go(self.PAGE_SETTINGS))
        self.home.open_history.connect(self._open_history)
        self.home.open_about.connect(lambda: self._go(self.PAGE_ABOUT))
        self.home.exit_app.connect(self._real_quit)
        self.home.refresh_cameras.connect(self._populate_cameras)
        self.home.camera_selected.connect(self._on_camera_selected)

        # Detection
        self.detection.stop_camera.connect(self._stop_detection)
        self.vm.frame_ready.connect(self.detection.update_frame)
        self.vm.stats_ready.connect(self.detection.update_stats)
        self.vm.fps_ready.connect(self._on_fps)
        self.vm.running_changed.connect(self._on_running_changed)
        self.vm.error.connect(self._on_detection_error)
        self.vm.screenshot_saved.connect(self._on_screenshot_saved)
        self.vm.recording_saved.connect(self._on_recording_saved)

        # Settings / history / about navigation
        self.settings.saved.connect(self._on_settings_saved)
        self.settings.cancelled.connect(lambda: self._go(self.PAGE_HOME))
        self.history.back.connect(lambda: self._go(self.PAGE_HOME))
        self.about.back.connect(lambda: self._go(self.PAGE_HOME))

        # Events -> dashboard + notifications
        self.events.pending_count_changed.connect(self.home.set_pending)
        self.events.event_recorded.connect(self._notify_event)

    # --------------------------------------------------------- navigation
    def _go(self, index: int) -> None:
        self.stack.setCurrentIndex(index)

    def _open_history(self) -> None:
        self.history.refresh()
        self._go(self.PAGE_HISTORY)

    def _populate_cameras(self) -> None:
        devices = discover_cameras()
        current = int(self.config.get("camera", "camera_index", 0))
        self.home.set_cameras(devices, current)

    def _on_camera_selected(self, index: int) -> None:
        if self.vm.is_running:
            return  # idle-only switching
        data = self.config.data
        data["camera"]["camera_index"] = int(index)
        # selecting a device implies a local (integrated/usb) source
        if data["camera"]["camera_type"] in ("rtsp", "http"):
            data["camera"]["camera_type"] = "usb"
        self.config.save(data)
        self.settings.load_from_config()

    def _refresh_home(self) -> None:
        self.home.set_model_status(self.engine.loaded)
        self.home.set_camera_status(self.vm.is_running)
        self.home.set_device(self.config.get("backend", "source_device", "USB Camera"))
        self.home.set_pending(self.events.pending_count())
        self.home.set_backend_status(self._backend_connected)
        self.home.set_camera_enabled(not self.vm.is_running)

    # --------------------------------------------------------- detection
    def _start_detection(self) -> None:
        if not self.engine.loaded:
            QMessageBox.warning(self, APP_NAME, "AI model belum siap.")
            return
        if self.vm.is_running:
            self._show_page(self.PAGE_DETECTION)
            return
        self.detection.reset()
        self.detection.set_backend_status(self._backend_connected)
        self._go(self.PAGE_DETECTION)
        self.vm.start()

    def _stop_detection(self) -> None:
        self.vm.stop()
        self._go(self.PAGE_HOME)
        self._refresh_home()

    def _on_running_changed(self, running: bool) -> None:
        self.home.set_camera_status(running)
        self.home.set_camera_enabled(not running)
        self._act_start.setEnabled(not running)
        self._act_stop.setEnabled(running)
        self.sb_camera.setText(f"Camera: {'Running' if running else 'Offline'}")
        if not running:
            self.sb_fps.setText("FPS: 0")

    def _on_detection_error(self, message: str) -> None:
        QMessageBox.critical(self, APP_NAME, message)
        self._go(self.PAGE_HOME)
        self._refresh_home()

    def _on_fps(self, fps: float) -> None:
        self.sb_fps.setText(f"FPS: {fps:.0f}")

    def _on_screenshot_saved(self, path: str) -> None:
        self.detection.flash_saved(f"Screenshot saved: {path.split('/')[-1]}")

    def _on_recording_saved(self, path: str) -> None:
        self.detection.flash_saved(f"Recording saved: {path.split('/')[-1]}")

    # --------------------------------------------------------- notifications
    def _notify_event(self, row: dict) -> None:
        if not self.config.get("tray", "enabled", True) or not self.tray.isVisible():
            return
        self.tray.showMessage(
            APP_NAME, f"{row['event']} detected",
            QSystemTrayIcon.Warning, 4000,
        )

    # --------------------------------------------------------- status
    def _on_backend_status(self, connected: bool) -> None:
        self._backend_connected = connected
        self.home.set_backend_status(connected)
        self.detection.set_backend_status(connected)
        self.sb_backend.setText(f"Backend: {'Connected' if connected else 'Offline'}")

    def _on_system_stats(self, cpu: float, mem_mb: float) -> None:
        self.sb_cpu.setText(f"CPU: {cpu:.0f}%")
        self.sb_ram.setText(f"RAM: {mem_mb:.0f} MB")

    def _on_settings_saved(self) -> None:
        # Apply theme + tray changes live (no restart).
        apply_theme(self.app, self.config.get("theme", "mode", "system"))
        self.tray.setVisible(bool(self.config.get("tray", "enabled", True)))
        self._populate_cameras()
        QMessageBox.information(self, APP_NAME, "Configuration saved.")
        self._go(self.PAGE_HOME)
        self._refresh_home()

    # --------------------------------------------------------- lifecycle
    def closeEvent(self, event) -> None:
        # System tray behaviour: hide instead of quit (keep monitoring).
        if (not self._force_quit and self.config.get("tray", "enabled", True)
                and self.tray.isVisible()):
            event.ignore()
            self.hide()
            self.tray.showMessage(
                APP_NAME, "Masih berjalan di background. Klik kanan tray → Exit untuk keluar.",
                QSystemTrayIcon.Information, 3000,
            )
            return
        self._shutdown()
        super().closeEvent(event)

    def _real_quit(self) -> None:
        self._force_quit = True
        self._shutdown()
        self.tray.hide()
        self.app.quit()

    def _shutdown(self) -> None:
        self.vm.stop()
        self._pinger.stop()
        self.events.stop()
