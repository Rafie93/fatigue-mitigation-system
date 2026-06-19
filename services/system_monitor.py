"""Polls CPU / memory usage for the status bar."""
import os

from PySide6.QtCore import QObject, QTimer, Signal

try:
    import psutil
    _PROC = psutil.Process(os.getpid())
    _PROC.cpu_percent(None)  # prime the first reading
except Exception:  # pragma: no cover - psutil is a hard dep but stay safe
    psutil = None
    _PROC = None


class SystemMonitor(QObject):
    updated = Signal(float, float)  # cpu_percent, memory_mb

    def __init__(self, interval_ms: int = 2000):
        super().__init__()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(interval_ms)

    def _poll(self) -> None:
        if _PROC is None:
            self.updated.emit(0.0, 0.0)
            return
        cpu = _PROC.cpu_percent(None)
        mem_mb = _PROC.memory_info().rss / (1024 * 1024)
        self.updated.emit(cpu, mem_mb)
