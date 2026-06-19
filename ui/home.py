"""Home dashboard: status overview + navigation buttons."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)


class StatusCard(QFrame):
    def __init__(self, title: str, value: str = "-"):
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        self._title = QLabel(title)
        self._title.setObjectName("Subtitle")
        self._value = QLabel(value)
        self._value.setObjectName("StatusValue")
        layout.addWidget(self._title)
        layout.addWidget(self._value)

    def set_value(self, text: str, color: str = "#e6e6e6") -> None:
        self._value.setText(text)
        self._value.setStyleSheet(f"color: {color};")


class HomeView(QWidget):
    start_camera = Signal()
    open_configuration = Signal()
    open_history = Signal()
    open_about = Signal()
    exit_app = Signal()
    refresh_cameras = Signal()
    camera_selected = Signal(int)  # camera index

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(22)

        header = QVBoxLayout()
        title = QLabel("ISAN-FS")
        title.setObjectName("Title")
        subtitle = QLabel("Fatigue - mitigation system")
        subtitle.setObjectName("Subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        # --- active camera selector (v1.2 multi camera) ---
        cam_card = QFrame()
        cam_card.setObjectName("Card")
        cam_layout = QHBoxLayout(cam_card)
        cam_layout.setContentsMargins(18, 12, 18, 12)
        cam_label = QLabel("Active Camera")
        cam_label.setObjectName("Subtitle")
        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumWidth(220)
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        btn_refresh = QPushButton("Refresh Camera")
        btn_refresh.setObjectName("Secondary")
        btn_refresh.clicked.connect(self.refresh_cameras)
        cam_layout.addWidget(cam_label)
        cam_layout.addWidget(self.camera_combo, stretch=1)
        cam_layout.addWidget(btn_refresh)
        root.addWidget(cam_card)

        # --- status cards grid ---
        grid = QGridLayout()
        grid.setSpacing(14)
        self.card_camera = StatusCard("Camera", "Offline")
        self.card_backend = StatusCard("Backend", "Checking...")
        self.card_model = StatusCard("AI Model", "Loaded")
        self.card_device = StatusCard("Device", "-")
        self.card_pending = StatusCard("Pending Events", "0")
        grid.addWidget(self.card_camera, 0, 0)
        grid.addWidget(self.card_backend, 0, 1)
        grid.addWidget(self.card_model, 0, 2)
        grid.addWidget(self.card_device, 1, 0)
        grid.addWidget(self.card_pending, 1, 1)
        root.addLayout(grid)

        root.addStretch()

        # --- action buttons ---
        btn_start = QPushButton("▶  Start Camera")
        btn_start.setMinimumHeight(48)
        btn_start.clicked.connect(self.start_camera)

        row = QHBoxLayout()
        btn_config = QPushButton("Configuration")
        btn_config.setObjectName("Secondary")
        btn_config.clicked.connect(self.open_configuration)
        btn_history = QPushButton("Event History")
        btn_history.setObjectName("Secondary")
        btn_history.clicked.connect(self.open_history)
        btn_about = QPushButton("About")
        btn_about.setObjectName("Secondary")
        btn_about.clicked.connect(self.open_about)
        btn_exit = QPushButton("Exit")
        btn_exit.setObjectName("Danger")
        btn_exit.clicked.connect(self.exit_app)
        for b in (btn_config, btn_history, btn_about, btn_exit):
            b.setMinimumHeight(44)
            row.addWidget(b)

        root.addWidget(btn_start)
        root.addLayout(row)

    # ------------------------------------------------- camera selector
    def set_cameras(self, devices: list, current_index: int) -> None:
        """Populate the camera dropdown from discovered devices."""
        self.camera_combo.blockSignals(True)
        self.camera_combo.clear()
        for dev in devices:
            self.camera_combo.addItem(dev.label, dev.index)
        pos = self.camera_combo.findData(current_index)
        self.camera_combo.setCurrentIndex(pos if pos >= 0 else 0)
        self.camera_combo.blockSignals(False)

    def set_camera_enabled(self, enabled: bool) -> None:
        """Disable switching while a session is running (idle-only change)."""
        self.camera_combo.setEnabled(enabled)

    def _on_camera_changed(self, _pos: int) -> None:
        index = self.camera_combo.currentData()
        if index is not None:
            self.camera_selected.emit(int(index))

    # ------------------------------------------------- updates from VM
    def set_camera_status(self, online: bool) -> None:
        if online:
            self.card_camera.set_value("● Running", "#22c55e")
        else:
            self.card_camera.set_value("○ Offline", "#9ca3af")

    def set_backend_status(self, connected: bool) -> None:
        if connected:
            self.card_backend.set_value("● Connected", "#22c55e")
        else:
            self.card_backend.set_value("○ Disconnected", "#f59e0b")

    def set_model_status(self, loaded: bool) -> None:
        if loaded:
            self.card_model.set_value("✓ Loaded", "#22c55e")
        else:
            self.card_model.set_value("… Loading", "#f59e0b")

    def set_device(self, name: str) -> None:
        self.card_device.set_value(name or "-")

    def set_pending(self, count: int) -> None:
        self.card_pending.set_value(str(count), "#f59e0b" if count else "#e6e6e6")
