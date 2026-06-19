"""Camera capture + detection worker thread.

Owns the cv2.VideoCapture so that the GUI thread never touches the camera
directly. Emits annotated frames (as QImage), live stats and triggered events.
v1.2: builds the source from config (multi camera / RTSP / HTTP), and drives
automatic event video recording + screenshots."""
import time

import cv2

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from services.camera_discovery import build_capture, describe_source
from services.detection_service import DetectionEngine, DetectionState
from services.recorder_service import ScreenshotSaver, VideoRecorder


class CameraWorker(QThread):
    frame_ready = Signal(QImage)
    stats_ready = Signal(dict)
    event_triggered = Signal(dict, object)  # event dict, raw frame
    fps_ready = Signal(float)
    error = Signal(str)
    screenshot_saved = Signal(str)
    recording_saved = Signal(str)

    def __init__(self, engine: DetectionEngine, config_service):
        super().__init__()
        self.engine = engine
        self.config = config_service
        self._running = False

    def run(self) -> None:
        cfg = self.config.data
        cap = build_capture(cfg["camera"])
        if not cap.isOpened():
            self.error.emit("Tidak dapat membuka kamera / sumber video.")
            return

        camera_label = describe_source(cfg["camera"])
        recorder = VideoRecorder(
            buffer_seconds=int(cfg["recording"]["buffer_seconds"]),
            duration=int(cfg["recording"]["duration"]),
        )
        screenshot = ScreenshotSaver(overlay=bool(cfg["screenshot"]["overlay"]))

        self._running = True
        state = DetectionState()
        frames = 0
        fps_t0 = time.time()
        current_fps = 0.0

        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    self.error.emit("Gagal membaca frame dari sumber video.")
                    break

                cfg = self.config.data
                result = self.engine.process(frame, state, cfg)

                # --- automatic recording (circular buffer) ---
                rec_enabled = bool(cfg["recording"]["enabled"])
                if rec_enabled:
                    recorder.push(result.frame)

                # --- per-event side effects ---
                for event in result.events:
                    self.event_triggered.emit(event, result.frame)
                    if cfg["screenshot"]["enabled"]:
                        path = screenshot.save(
                            result.frame, event,
                            {
                                "eye_confidence": result.eye_confidence,
                                "mouth_confidence": result.mouth_confidence,
                            },
                            camera_label,
                        )
                        if path:
                            self.screenshot_saved.emit(path)
                    if rec_enabled:
                        recorder.trigger(event["event_type"])

                if recorder.last_saved:
                    self.recording_saved.emit(recorder.last_saved)
                    recorder.last_saved = None

                self.frame_ready.emit(self._to_qimage(result.frame))
                self.stats_ready.emit({
                    "eye_label": result.eye_label,
                    "mouth_label": result.mouth_label,
                    "eye_confidence": result.eye_confidence,
                    "mouth_confidence": result.mouth_confidence,
                    "eye_closed_duration": result.eye_closed_duration,
                    "yawn_counter": result.yawn_counter,
                    "yawn_limit": int(cfg["yawn"]["limit"]),
                    "status_text": result.status_text,
                    "recording": recorder.is_recording,
                })

                frames += 1
                now = time.time()
                if now - fps_t0 >= 1.0:
                    current_fps = frames / (now - fps_t0)
                    recorder.set_fps(current_fps)
                    self.fps_ready.emit(current_fps)
                    frames = 0
                    fps_t0 = now
        finally:
            recorder.stop()
            cap.release()

    @staticmethod
    def _to_qimage(frame_bgr) -> QImage:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()

    def stop(self) -> None:
        self._running = False
        self.wait(3000)
