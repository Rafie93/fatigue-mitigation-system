"""Event history table."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

COLUMNS = ["Time", "Event", "Severity", "Status", "Backend"]
SEVERITY_COLOR = {"Danger": "#ef4444", "Warning": "#f59e0b", "Info": "#3b82f6"}


class EventHistoryView(QWidget):
    back = Signal()

    def __init__(self, event_service):
        super().__init__()
        self.events = event_service
        self._build()
        self.refresh()
        self.events.event_recorded.connect(lambda row: self._prepend(row))

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Event History")
        title.setObjectName("Title")
        header.addWidget(title)
        header.addStretch()
        btn_back = QPushButton("Back")
        btn_back.setObjectName("Secondary")
        btn_back.clicked.connect(self.back)
        header.addWidget(btn_back)
        root.addLayout(header)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        root.addWidget(self.table)

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for row in self.events.history:
            self._append(row)

    def _prepend(self, row: dict) -> None:
        self.table.insertRow(0)
        self._fill(0, row)

    def _append(self, row: dict) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        self._fill(r, row)

    def _fill(self, r: int, row: dict) -> None:
        values = [row["time"], row["event"], row["severity"], row["status"], row["backend"]]
        for c, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            if c == 2 and value in SEVERITY_COLOR:
                item.setForeground(QColor(SEVERITY_COLOR[value]))
            if c == 3:
                item.setForeground(QColor("#22c55e" if value == "Sent" else "#f59e0b"))
            self.table.setItem(r, c, item)
