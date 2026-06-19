"""Configuration manager UI mapping to config.json sections (v1.2)."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
    QLineEdit, QPushButton, QRadioButton, QScrollArea, QSpinBox, QTabWidget,
    QVBoxLayout, QWidget,
)

from services.camera_discovery import discover_cameras


class RadioGroup(QWidget):
    """Horizontal group of mutually-exclusive options bound to a value."""

    def __init__(self, options: list[tuple[str, str]]):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._group = QButtonGroup(self)
        self._buttons: list[tuple[QRadioButton, str]] = []
        for label, value in options:
            btn = QRadioButton(label)
            self._group.addButton(btn)
            layout.addWidget(btn)
            self._buttons.append((btn, value))
        layout.addStretch()

    def value(self) -> str:
        for btn, value in self._buttons:
            if btn.isChecked():
                return value
        return self._buttons[0][1] if self._buttons else ""

    def set_value(self, value) -> None:
        for btn, val in self._buttons:
            if str(val) == str(value):
                btn.setChecked(True)
                return
        if self._buttons:
            self._buttons[0][0].setChecked(True)


class SettingsView(QWidget):
    saved = Signal()
    cancelled = Signal()

    def __init__(self, config_service):
        super().__init__()
        self.config = config_service
        self._fields: dict[tuple[str, str], QWidget] = {}
        self._build()
        self.load_from_config()
        self.refresh_cameras()

    # ----------------------------------------------------- field builders
    def _line(self, section, key, password=False):
        w = QLineEdit()
        if password:
            w.setEchoMode(QLineEdit.Password)
        self._fields[(section, key)] = w
        return w

    def _int(self, section, key, minimum=0, maximum=100000):
        w = QSpinBox()
        w.setRange(minimum, maximum)
        self._fields[(section, key)] = w
        return w

    def _float(self, section, key, minimum=0.0, maximum=1000.0, step=0.1):
        w = QDoubleSpinBox()
        w.setRange(minimum, maximum)
        w.setSingleStep(step)
        w.setDecimals(2)
        self._fields[(section, key)] = w
        return w

    def _combo(self, section, key, options: list[tuple[str, str]]):
        w = QComboBox()
        for label, value in options:
            w.addItem(label, value)
        self._fields[(section, key)] = w
        return w

    def _check(self, section, key, text=""):
        w = QCheckBox(text)
        self._fields[(section, key)] = w
        return w

    def _radio(self, section, key, options: list[tuple[str, str]]):
        w = RadioGroup(options)
        self._fields[(section, key)] = w
        return w

    # ----------------------------------------------------- build UI
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        tabs = QTabWidget()

        # --- Camera (v1.2) ---
        camera = QFormLayout()
        camera.addRow("Camera Source", self._combo("camera", "camera_type", [
            ("Integrated Camera", "integrated"),
            ("USB Camera", "usb"),
            ("Virtual Camera", "virtual"),
            ("RTSP Camera", "rtsp"),
            ("HTTP Stream", "http"),
        ]))
        self.camera_device = QComboBox()
        self._fields[("camera", "camera_index")] = self.camera_device
        device_row = QHBoxLayout()
        device_row.addWidget(self.camera_device, stretch=1)
        btn_refresh = QPushButton("Refresh Camera")
        btn_refresh.setObjectName("Secondary")
        btn_refresh.clicked.connect(self.refresh_cameras)
        device_row.addWidget(btn_refresh)
        device_wrap = QWidget()
        device_wrap.setLayout(device_row)
        camera.addRow("Camera", device_wrap)
        camera.addRow("RTSP / HTTP URL", self._line("camera", "camera_url"))
        camera.addRow("Auto Refresh Devices", self._check("camera", "auto_refresh"))
        tabs.addTab(self._wrap(camera), "Camera")

        # --- Backend ---
        backend = QFormLayout()
        backend.addRow("Backend API URL", self._line("backend", "api_url"))
        backend.addRow("Device Token", self._line("backend", "device_token"))
        backend.addRow("Device Name", self._line("backend", "source_device"))
        backend.addRow("Pending Event File", self._line("backend", "pending_file"))
        tabs.addTab(self._wrap(backend), "Backend")

        # --- Desktop Authentication ---
        desktop = QFormLayout()
        desktop.addRow("Username", self._line("desktop", "username"))
        desktop.addRow("Password", self._line("desktop", "password", password=True))
        tabs.addTab(self._wrap(desktop), "Authentication")

        # --- Eye Detection ---
        eye = QFormLayout()
        eye.addRow("Eye Closed Threshold", self._int("detection", "eye_closed_threshold"))
        eye.addRow("Micro Sleep Threshold (s)", self._int("detection", "eye_closed_secs_1"))
        eye.addRow("Critical Sleep Threshold (s)", self._int("detection", "eye_closed_secs_2"))
        eye.addRow("Eye Open Reset Delay (s)",
                   self._float("detection", "eye_open_reset_secs", 0.0, 10.0, 0.1))
        eye.addRow("Minimum Confidence",
                   self._float("detection", "min_confidence", 0.0, 1.0, 0.05))
        tabs.addTab(self._wrap(eye), "Eye Detection")

        # --- Yawn Detection ---
        yawn = QFormLayout()
        yawn.addRow("Maximum Yawn Count", self._int("yawn", "limit"))
        yawn.addRow("Observation Window (s)", self._int("yawn", "time_window"))
        yawn.addRow("Consecutive Yawn Frames", self._int("yawn", "frame_threshold"))
        tabs.addTab(self._wrap(yawn), "Yawn Detection")

        # --- Recording & Screenshot (v1.2) ---
        rec = QFormLayout()
        rec.addRow("Enable Recording", self._check("recording", "enabled"))
        rec.addRow("Recording Duration (s)", self._int("recording", "duration", 5, 600))
        rec.addRow("Pre-event Buffer (s)", self._int("recording", "buffer_seconds", 1, 120))
        rec.addRow("Enable Screenshot", self._check("screenshot", "enabled"))
        rec.addRow("Screenshot Overlay", self._check("screenshot", "overlay"))
        tabs.addTab(self._wrap(rec), "Recording")

        # --- Event Notification ---
        event = QFormLayout()
        event.addRow("Backend Event URL", self._line("event", "backend_url"))
        event.addRow("Backend Event Token", self._line("event", "backend_token"))
        tabs.addTab(self._wrap(event), "Event Notification")

        # --- Appearance & System (v1.2) ---
        system = QFormLayout()
        system.addRow("Theme", self._radio("theme", "mode", [
            ("Light", "light"), ("Dark", "dark"), ("Follow System", "system"),
        ]))
        system.addRow("Enable System Tray", self._check("tray", "enabled"))
        system.addRow("Start Minimized", self._check("tray", "start_minimized"))
        tabs.addTab(self._wrap(system), "Appearance")

        root.addWidget(tabs)

        # --- buttons ---
        row = QHBoxLayout()
        row.addStretch()
        btn_restore = QPushButton("Restore Default")
        btn_restore.setObjectName("Secondary")
        btn_restore.clicked.connect(self._on_restore)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("Secondary")
        btn_cancel.clicked.connect(self._on_cancel)
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self._on_save)
        for b in (btn_restore, btn_cancel, btn_save):
            b.setMinimumHeight(40)
            row.addWidget(b)
        root.addLayout(row)

    @staticmethod
    def _wrap(form: QFormLayout) -> QWidget:
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(14)
        inner = QWidget()
        inner.setLayout(form)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setFrameShape(QScrollArea.NoFrame)
        return scroll

    # ----------------------------------------------------- camera discovery
    def refresh_cameras(self) -> None:
        current = self.config.get("camera", "camera_index", 0)
        self.camera_device.blockSignals(True)
        self.camera_device.clear()
        for dev in discover_cameras():
            self.camera_device.addItem(dev.label, dev.index)
        # restore selection
        idx = self.camera_device.findData(current)
        if idx >= 0:
            self.camera_device.setCurrentIndex(idx)
        self.camera_device.blockSignals(False)

    # ----------------------------------------------------- data binding
    def load_from_config(self) -> None:
        data = self.config.data
        for (section, key), widget in self._fields.items():
            value = data.get(section, {}).get(key)
            if value is None:
                continue
            if isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                pos = widget.findData(value)
                widget.setCurrentIndex(pos if pos >= 0 else 0)
            elif isinstance(widget, RadioGroup):
                widget.set_value(value)
            else:  # QLineEdit
                widget.setText(str(value))

    def _collect(self) -> dict:
        data = self.config.data
        for (section, key), widget in self._fields.items():
            if isinstance(widget, QSpinBox):
                data.setdefault(section, {})[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                data.setdefault(section, {})[key] = round(widget.value(), 4)
            elif isinstance(widget, QCheckBox):
                data.setdefault(section, {})[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                data.setdefault(section, {})[key] = widget.currentData()
            elif isinstance(widget, RadioGroup):
                data.setdefault(section, {})[key] = widget.value()
            else:  # QLineEdit
                data.setdefault(section, {})[key] = widget.text().strip()
        return data

    # ----------------------------------------------------- actions
    def _on_save(self) -> None:
        self.config.save(self._collect())
        self.saved.emit()

    def _on_cancel(self) -> None:
        self.load_from_config()
        self.cancelled.emit()

    def _on_restore(self) -> None:
        self.config.restore_defaults()
        self.load_from_config()
        self.refresh_cameras()
