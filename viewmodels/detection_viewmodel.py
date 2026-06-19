"""ViewModel coordinating the camera worker, detection engine and event service."""
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

from services.camera_service import CameraWorker


class DetectionViewModel(QObject):
    frame_ready = Signal(QImage)
    stats_ready = Signal(dict)
    fps_ready = Signal(float)
    running_changed = Signal(bool)
    error = Signal(str)
    screenshot_saved = Signal(str)
    recording_saved = Signal(str)

    def __init__(self, engine, config_service, event_service):
        super().__init__()
        self.engine = engine
        self.config = config_service
        self.events = event_service
        self._worker: CameraWorker | None = None

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def start(self) -> None:
        """Start detection using the camera source from configuration."""
        if self.is_running:
            return
        self._worker = CameraWorker(self.engine, self.config)
        self._worker.frame_ready.connect(self.frame_ready)
        self._worker.stats_ready.connect(self.stats_ready)
        self._worker.fps_ready.connect(self.fps_ready)
        self._worker.event_triggered.connect(self._on_event)
        self._worker.error.connect(self._on_error)
        self._worker.screenshot_saved.connect(self.screenshot_saved)
        self._worker.recording_saved.connect(self.recording_saved)
        self._worker.finished.connect(lambda: self.running_changed.emit(False))
        self._worker.start()
        self.running_changed.emit(True)

    def _on_event(self, event: dict, frame) -> None:
        self.events.dispatch(event, frame)

    def _on_error(self, message: str) -> None:
        self.error.emit(message)
        self.stop()

    def stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
        self.running_changed.emit(False)
