"""Splash screen shown while the AI models load on a background thread."""
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget,
)

from ui.theme import APP_NAME, APP_VERSION


class ModelLoaderThread(QThread):
    """Loads the detection engine off the GUI thread."""

    progress = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self) -> None:
        try:
            self.engine.load(progress_cb=self.progress.emit)
            self.finished_ok.emit()
        except Exception as exc:  # pragma: no cover
            self.failed.emit(str(exc))


class SplashScreen(QWidget):
    """A centered card with logo text, progress bar and loading status."""

    done = Signal()

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setFixedSize(460, 320)
        self._build()

        self._loader = ModelLoaderThread(engine)
        self._loader.progress.connect(self.status.setText)
        self._loader.finished_ok.connect(self._on_done)
        self._loader.failed.connect(self._on_failed)

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("ISAN-FS")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel(APP_NAME)
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        self.status = QLabel("Loading AI Model...")
        self.status.setObjectName("Subtitle")
        self.status.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setTextVisible(False)

        version = QLabel(f"Version {APP_VERSION}")
        version.setObjectName("Subtitle")
        version.setAlignment(Qt.AlignCenter)
        version.setFont(QFont("Segoe UI", 9))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addStretch()
        layout.addWidget(version)
        outer.addWidget(card)

    def start(self) -> None:
        self._loader.start()

    def _on_done(self) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.done.emit()

    def _on_failed(self, message: str) -> None:
        self.progress.setRange(0, 1)
        self.status.setText(f"Gagal memuat model: {message}")
