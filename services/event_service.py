"""Builds, dispatches, records and retries fatigue events.

Network sends happen on a background thread so the detection loop never blocks.
Pending events (failed sends) are persisted to a JSONL file and retried."""
import base64
import json
import os
import threading
import time
from collections import deque
from datetime import datetime

import cv2

from PySide6.QtCore import QObject, Signal

from services.paths import writable_path

EVENT_COOLDOWN_SECONDS = 30
PENDING_FLUSH_INTERVAL_SECONDS = 15
SEVERITY_LABEL = {"danger": "Danger", "warning": "Warning", "info": "Info"}


class EventService(QObject):
    """Owns the event history, pending queue and dispatch thread."""

    # emits a history row dict: {time, event, severity, status, backend}
    event_recorded = Signal(dict)
    pending_count_changed = Signal(int)

    def __init__(self, config_service, backend_service):
        super().__init__()
        self.config = config_service
        self.backend = backend_service
        self.history: deque = deque(maxlen=500)
        self._last_sent_at = {"micro_sleep": 0.0, "yawn_alert": 0.0, "fatigue_alert": 0.0}
        self._lock = threading.Lock()
        self._stop = False
        self._flusher = threading.Thread(target=self._flush_loop, daemon=True)
        self._flusher.start()

    # ------------------------------------------------------------- paths
    def _pending_file(self) -> str:
        configured = (self.config.get("backend", "pending_file", "") or "").strip()
        if configured:
            if os.path.isabs(configured):
                return configured
            return writable_path(*configured.split("/"))
        return writable_path("pending", "pending.jsonl")

    # ------------------------------------------------------------- build
    def _build_payload(self, event: dict, image_b64: str | None) -> dict:
        meta = event.get("meta", {})
        payload = {
            "event_type": event["event_type"],
            "severity": event["severity"],
            "status_text": event["status_text"],
            "eye_label": meta.get("eye_label"),
            "mouth_label": meta.get("mouth_label"),
            "eye_confidence": round(float(meta.get("conf_eye", 0.0)), 4),
            "mouth_confidence": round(float(meta.get("conf_mouth", 0.0)), 4),
            "closed_frame_count": int(meta.get("closed_frame_count", 0)),
            "yawn_count": int(meta.get("yawn_count", 0)),
            "source_device": self.config.get("backend", "source_device", "").strip(),
            "detected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "metadata": {
                "time_window_seconds": meta.get("time_window"),
                "eye_closed_threshold": meta.get("eye_closed_threshold"),
                "yawn_limit": meta.get("yawn_limit"),
            },
        }
        if image_b64 is not None:
            payload["image_base64"] = image_b64
        return payload

    @staticmethod
    def _encode_frame(frame) -> str | None:
        try:
            if frame is None:
                return None
            small = cv2.resize(frame, (640, 360))
            ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 60])
            return base64.b64encode(buf.tobytes()).decode("utf-8") if ok else None
        except Exception:
            return None

    # ------------------------------------------------------------ dispatch
    def dispatch(self, event: dict, frame=None) -> None:
        """Entry point from the detection worker. Applies cooldown then sends
        asynchronously."""
        etype = event["event_type"]
        now = time.time()
        if now - self._last_sent_at.get(etype, 0.0) < EVENT_COOLDOWN_SECONDS:
            return
        self._last_sent_at[etype] = now
        image_b64 = self._encode_frame(frame)
        threading.Thread(
            target=self._send_worker, args=(event, image_b64), daemon=True
        ).start()

    def _send_worker(self, event: dict, image_b64: str | None) -> None:
        payload = self._build_payload(event, image_b64)
        sent = self.backend.send(payload) if self.backend.is_ready() else False
        if not sent:
            # Persist without the (large) image for retry.
            persisted = {k: v for k, v in payload.items() if k != "image_base64"}
            self._store_pending(persisted)
        self._record_history(event, sent)

    # ------------------------------------------------------------- history
    def _record_history(self, event: dict, sent: bool) -> None:
        row = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "event": event["event_type"].replace("_", " ").title(),
            "severity": SEVERITY_LABEL.get(event["severity"], event["severity"].title()),
            "status": "Sent" if sent else "Pending",
            "backend": "OK" if sent else "Offline",
        }
        self.history.appendleft(row)
        self.event_recorded.emit(row)

    # ------------------------------------------------------------- pending
    def _store_pending(self, payload: dict) -> None:
        with self._lock:
            with open(self._pending_file(), "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload) + "\n")
        self.pending_count_changed.emit(self.pending_count())

    def pending_count(self) -> int:
        path = self._pending_file()
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        except OSError:
            return 0

    def _flush_loop(self) -> None:
        while not self._stop:
            time.sleep(PENDING_FLUSH_INTERVAL_SECONDS)
            try:
                self.flush_pending()
            except Exception:
                pass

    def flush_pending(self) -> None:
        if not self.backend.is_ready():
            return
        path = self._pending_file()
        if not os.path.exists(path):
            return
        with self._lock:
            with open(path, "r", encoding="utf-8") as fh:
                rows = [line.strip() for line in fh if line.strip()]
            if not rows:
                os.remove(path)
                self.pending_count_changed.emit(0)
                return
            remaining = []
            for row in rows:
                try:
                    payload = json.loads(row)
                except json.JSONDecodeError:
                    continue
                if not self.backend.send(payload):
                    remaining.append(row)
            if remaining:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(remaining) + "\n")
            else:
                os.remove(path)
        self.pending_count_changed.emit(self.pending_count())

    def stop(self) -> None:
        self._stop = True
