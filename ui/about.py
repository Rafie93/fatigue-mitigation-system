"""About page with version + environment info."""
import cv2
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from ui.theme import APP_NAME, APP_VERSION


def _tf_version() -> str:
    try:
        import tensorflow as tf
        return tf.__version__
    except Exception:
        return "unavailable"


class AboutView(QWidget):
    back = Signal()

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(20)

        title = QLabel("About")
        title.setObjectName("Title")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        info = QVBoxLayout(card)
        info.setContentsMargins(28, 24, 28, 24)
        info.setSpacing(10)

        rows = [
            ("Application", APP_NAME),
            ("Version", APP_VERSION),
            ("TensorFlow", _tf_version()),
            ("OpenCV", cv2.__version__),
            ("AI Model", "MobileNetV2 (eye + mouth)"),
            ("Analysts", "Ichsan"),
            ("Developer", "Rafi'e"),
            ("Institution", "ULM"),
        ]
        for label, value in rows:
            line = QHBoxLayout()
            k = QLabel(label)
            k.setObjectName("Subtitle")
            k.setFixedWidth(160)
            v = QLabel(value)
            v.setObjectName("StatusValue")
            line.addWidget(k)
            line.addWidget(v)
            line.addStretch()
            info.addLayout(line)

        root.addWidget(card)
        root.addStretch()

        btn_back = QPushButton("Back")
        btn_back.setObjectName("Secondary")
        btn_back.setMinimumHeight(40)
        btn_back.clicked.connect(self.back)
        root.addWidget(btn_back, alignment=Qt.AlignLeft)
