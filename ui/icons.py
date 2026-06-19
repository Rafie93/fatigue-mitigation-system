"""Programmatic application icon (avoids shipping a binary asset)."""
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap


def app_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#2563eb"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(QRect(2, 2, 60, 60), 14, 14)
    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 26, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignCenter, "F")
    painter.end()
    return QIcon(pix)
