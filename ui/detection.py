"""Detection window: live camera preview + status overlay panel."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)


class _Metric(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        t = QLabel(title)
        t.setObjectName("Subtitle")
        self.value = QLabel("-")
        self.value.setObjectName("StatusValue")
        layout.addWidget(t)
        layout.addWidget(self.value)

    def set(self, text: str, color: str = "#e6e6e6") -> None:
        self.value.setText(text)
        self.value.setStyleSheet(f"color: {color};")


class DetectionView(QWidget):
    stop_camera = Signal()

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # --- video preview ---
        self.video = QLabel("Camera starting...")
        self.video.setAlignment(Qt.AlignCenter)
        self.video.setMinimumSize(640, 480)
        self.video.setStyleSheet(
            "background-color:#000; border:1px solid #263041; border-radius:12px;"
        )
        root.addWidget(self.video, stretch=3)

        # --- side panel ---
        panel = QVBoxLayout()
        panel.setSpacing(12)
        header_row = QHBoxLayout()
        title = QLabel("Detection")
        title.setObjectName("SectionTitle")
        self.rec_indicator = QLabel("")
        self.rec_indicator.setStyleSheet("color:#ef4444; font-weight:700;")
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.rec_indicator)
        panel.addLayout(header_row)

        self.m_eye = _Metric("Eye Status")
        self.m_mouth = _Metric("Mouth Status")
        self.m_closed = _Metric("Eye Closed Duration")
        self.m_yawn = _Metric("Yawn Counter")
        self.m_status = _Metric("Detection Status")
        self.m_backend = _Metric("Backend Status")
        for m in (self.m_eye, self.m_mouth, self.m_closed, self.m_yawn,
                  self.m_status, self.m_backend):
            panel.addWidget(m)

        panel.addStretch()

        btn_stop = QPushButton("⏹  Stop Camera")
        btn_stop.setObjectName("Danger")
        btn_stop.setMinimumHeight(46)
        btn_stop.clicked.connect(self.stop_camera)
        panel.addWidget(btn_stop)

        self.info = QLabel("Auto screenshot & recording on events")
        self.info.setObjectName("Subtitle")
        self.info.setWordWrap(True)
        panel.addWidget(self.info)

        wrapper = QWidget()
        wrapper.setLayout(panel)
        wrapper.setFixedWidth(280)
        root.addWidget(wrapper, stretch=1)

    # ----------------------------------------------------- slots
    def update_frame(self, image: QImage) -> None:
        pix = QPixmap.fromImage(image).scaled(
            self.video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video.setPixmap(pix)

    def update_stats(self, stats: dict) -> None:
        eye = stats["eye_label"]
        self.m_eye.set(
            f"{eye} ({stats['eye_confidence']:.0%})",
            "#ef4444" if eye == "Closed" else "#22c55e",
        )
        mouth = stats["mouth_label"]
        self.m_mouth.set(
            f"{mouth} ({stats['mouth_confidence']:.0%})",
            "#ef4444" if mouth == "Yawn" else "#22c55e",
        )
        dur = stats["eye_closed_duration"]
        self.m_closed.set(f"{dur:.1f}s", "#ef4444" if dur >= 5 else "#e6e6e6")
        self.m_yawn.set(f"{stats['yawn_counter']} / {stats['yawn_limit']}")
        status = stats["status_text"]
        self.m_status.set(status, "#ef4444" if "BAHAYA" in status else
                          "#f59e0b" if "PERINGATAN" in status else "#22c55e")
        self.rec_indicator.setText("● REC" if stats.get("recording") else "")

    def flash_saved(self, text: str) -> None:
        self.info.setText(text)

    def set_backend_status(self, connected: bool) -> None:
        self.m_backend.set("Connected" if connected else "Offline",
                           "#22c55e" if connected else "#f59e0b")

    def reset(self) -> None:
        self.video.setPixmap(QPixmap())
        self.video.setText("Camera starting...")
