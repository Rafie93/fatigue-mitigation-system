"""Automatic event video recording (circular buffer) and screenshot capture.

Both classes are driven from the camera worker thread (where the frames live),
so they must stay lightweight. Files are organised by date under storage/."""
import os
from collections import deque
from datetime import datetime

import cv2

from services.paths import SCREENSHOTS_DIR, VIDEOS_DIR

DEFAULT_FPS = 15.0


def _dated_dir(root: str) -> str:
    path = os.path.join(root, datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(path, exist_ok=True)
    return path


class VideoRecorder:
    """Keeps the last `buffer_seconds` of frames; on an event it writes those
    pre-event frames plus the following frames until `duration` is reached."""

    def __init__(self, buffer_seconds: int = 10, duration: int = 30):
        self.buffer_seconds = max(1, int(buffer_seconds))
        self.duration = max(self.buffer_seconds + 1, int(duration))
        self._buffer: deque = deque()
        self._fps = DEFAULT_FPS
        self._writer: cv2.VideoWriter | None = None
        self._frames_remaining = 0
        self._current_path: str | None = None
        self.last_saved: str | None = None

    @property
    def is_recording(self) -> bool:
        return self._writer is not None

    def set_fps(self, fps: float) -> None:
        if fps and fps > 1:
            self._fps = float(fps)
            self._buffer = deque(self._buffer, maxlen=int(self._fps * self.buffer_seconds))

    def push(self, frame) -> None:
        """Call once per processed frame."""
        if self._buffer.maxlen is None:
            self._buffer = deque(maxlen=int(self._fps * self.buffer_seconds))
        self._buffer.append(frame.copy())
        if self._writer is not None:
            self._writer.write(frame)
            self._frames_remaining -= 1
            if self._frames_remaining <= 0:
                self._finalise()

    def trigger(self, event_type: str) -> str | None:
        """Start a recording (ignored if one is already running). Returns path."""
        if self._writer is not None or not self._buffer:
            return None
        h, w = self._buffer[0].shape[:2]
        ts = datetime.now().strftime("%H%M%S")
        path = os.path.join(_dated_dir(VIDEOS_DIR), f"{event_type}_{ts}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(path, fourcc, self._fps, (w, h))
        if not writer.isOpened():
            return None
        # Flush the pre-event buffer first.
        for buffered in list(self._buffer):
            writer.write(buffered)
        self._writer = writer
        self._current_path = path
        after_seconds = self.duration - self.buffer_seconds
        self._frames_remaining = int(self._fps * after_seconds)
        return path

    def _finalise(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self.last_saved = self._current_path
        self._writer = None
        self._current_path = None
        self._frames_remaining = 0

    def stop(self) -> None:
        self._finalise()
        self._buffer.clear()


class ScreenshotSaver:
    """Saves a PNG snapshot with an information overlay when an event fires."""

    def __init__(self, overlay: bool = True):
        self.overlay = overlay
        self.last_saved: str | None = None

    def save(self, frame, event: dict, stats: dict, camera_label: str) -> str | None:
        try:
            img = frame.copy()
            if self.overlay:
                self._draw_overlay(img, event, stats, camera_label)
            ts = datetime.now().strftime("%H%M%S")
            path = os.path.join(
                _dated_dir(SCREENSHOTS_DIR), f"{event['event_type']}_{ts}.png"
            )
            if cv2.imwrite(path, img):
                self.last_saved = path
                return path
        except Exception:
            return None
        return None

    @staticmethod
    def _draw_overlay(img, event: dict, stats: dict, camera_label: str) -> None:
        meta = event.get("meta", {})
        lines = [
            f"Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Event  : {event['event_type'].replace('_', ' ').title()}",
            f"Status : {event.get('status_text', '')}",
            f"Camera : {camera_label}",
            f"Conf   : eye {meta.get('conf_eye', 0):.2f} / mouth {meta.get('conf_mouth', 0):.2f}",
        ]
        h = img.shape[0]
        box_h = 18 * len(lines) + 16
        cv2.rectangle(img, (0, h - box_h), (img.shape[1], h), (0, 0, 0), -1)
        y = h - box_h + 22
        for line in lines:
            cv2.putText(img, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (255, 255, 255), 1, cv2.LINE_AA)
            y += 18
