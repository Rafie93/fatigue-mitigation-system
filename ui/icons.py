"""Application icon. Prefers the shipped assets/icon.ico, falls back to a
programmatically drawn icon so the app still has an icon when run from source."""
import os

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from services.paths import resource_path


def _drawn_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#2563eb"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(QRect(2, 2, 60, 60), 14, 14)
    painter.setPen(QColor("#ffffff"))
    painter.setFont(QFont("Segoe UI", 26, QFont.Bold))
    painter.drawText(pix.rect(), Qt.AlignCenter, "F")
    painter.end()
    return QIcon(pix)


def app_icon() -> QIcon:
    for name in ("icon.ico", "logo.png"):
        path = resource_path("assets", name)
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon
    return _drawn_icon()
