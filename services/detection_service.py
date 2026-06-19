"""AI detection engine. Wraps the MobileNetV2 eye/mouth models and the
per-frame fatigue logic ported from version 1.0."""
import time
from dataclasses import dataclass, field

import cv2
import numpy as np

from services.paths import resource_path

EYE_LABELS = ["Closed", "Open"]
MOUTH_LABELS = ["No_yawn", "Yawn"]


@dataclass
class DetectionState:
    """Mutable state carried across frames during a detection session."""

    closed_frame_count: int = 0
    eye_closed_start: float | None = None
    eye_open_start: float | None = None
    eye_closed_duration: float = 0.0

    yawn_counter: int = 0
    yawn_cooldown: bool = False
    yawn_frame_count: int = 0
    last_yawn_time: float = field(default_factory=time.time)

    active_alerts: set = field(default_factory=set)

    last_eye_label: str = "-"
    last_mouth_label: str = "-"
    last_eye_conf: float = 0.0
    last_mouth_conf: float = 0.0


@dataclass
class FrameResult:
    """Everything the GUI/worker needs after processing one frame."""

    frame: np.ndarray
    status_text: str
    eye_label: str
    mouth_label: str
    eye_confidence: float
    mouth_confidence: float
    eye_closed_duration: float
    yawn_counter: int
    events: list = field(default_factory=list)  # list of event dicts to dispatch


class DetectionEngine:
    """Loads the two MobileNet models and processes frames."""

    def __init__(self):
        self.model_eye = None
        self.model_mouth = None
        self.face_cascade = None
        self.loaded = False

    def load(self, progress_cb=None) -> None:
        """Load Keras models + Haar cascade. Heavy; call from a worker thread."""
        from tensorflow.keras.models import load_model  # local import: slow

        if progress_cb:
            progress_cb("Loading eye model...")
        self.model_eye = load_model(resource_path("models", "model_eye_mobilenet.h5"))

        if progress_cb:
            progress_cb("Loading mouth model...")
        self.model_mouth = load_model(resource_path("models", "model_mouth_mobilenet.h5"))

        if progress_cb:
            progress_cb("Loading face detector...")
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.loaded = True
        if progress_cb:
            progress_cb("AI model ready")

    # ----------------------------------------------------------- prediction
    def _predict(self, img, model, labels, threshold, safe_index):
        try:
            resized = cv2.resize(img, (160, 160)).astype("float32") / 255.0
            resized = np.expand_dims(resized, axis=0)
            pred = model.predict(resized, verbose=0)[0]
            idx = int(np.argmax(pred))
            conf = float(pred[idx])
            if conf < threshold:
                return labels[safe_index], conf
            return labels[idx], conf
        except Exception:
            return labels[safe_index], 0.0

    # ------------------------------------------------------------ per frame
    def process(self, frame, state: DetectionState, cfg: dict) -> FrameResult:
        """Process a single BGR frame, mutating `state`, returning a FrameResult."""
        det = cfg["detection"]
        yawn_cfg = cfg["yawn"]
        eye_secs_1 = float(det["eye_closed_secs_1"])
        eye_secs_2 = float(det["eye_closed_secs_2"])
        eye_open_reset = float(det["eye_open_reset_secs"])
        min_conf = float(det["min_confidence"])
        eye_closed_threshold = int(det["eye_closed_threshold"])
        yawn_limit = int(yawn_cfg["limit"])
        time_window = float(yawn_cfg["time_window"])
        yawn_frame_threshold = int(yawn_cfg["frame_threshold"])

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)

        current_time = time.time()
        if current_time - state.last_yawn_time > time_window:
            state.yawn_counter = 0
            state.last_yawn_time = current_time

        status_text = "Status: Siaga (Aman)"
        alert_color = (0, 255, 0)
        events: list = []

        eye_closed_duration = 0.0
        if len(faces) == 0:
            state.closed_frame_count = 0
            state.eye_closed_start = None
            state.eye_open_start = None
            state.yawn_frame_count = 0
            state.yawn_cooldown = False
            state.eye_closed_duration = 0.0

        label_eye, conf_eye = "-", 0.0
        label_mouth, conf_mouth = "-", 0.0

        for (x, y, w, h) in faces:
            eye_roi = frame[y:y + int(h * 0.5), x:x + w]
            mouth_roi = frame[
                y + int(h * 0.7): y + int(h * 0.9),
                x + int(w * 0.2): x + int(w * 0.8),
            ]

            label_eye, conf_eye = self._predict(
                eye_roi, self.model_eye, EYE_LABELS, min_conf, safe_index=1
            )
            label_mouth, conf_mouth = self._predict(
                mouth_roi, self.model_mouth, MOUTH_LABELS, min_conf, safe_index=0
            )

            # --- micro-sleep / eye timer ---
            if label_eye == "Closed":
                state.eye_open_start = None
                if state.eye_closed_start is None:
                    state.eye_closed_start = current_time
                state.closed_frame_count += 1
                eye_closed_duration = current_time - state.eye_closed_start
            else:
                if state.eye_open_start is None:
                    state.eye_open_start = current_time
                open_duration = current_time - state.eye_open_start
                if open_duration >= eye_open_reset:
                    state.eye_closed_start = None
                    state.closed_frame_count = 0
                    eye_closed_duration = 0.0
                    state.eye_open_start = None
                else:
                    eye_closed_duration = (
                        (current_time - state.eye_closed_start)
                        if state.eye_closed_start else 0.0
                    )

            # --- yawn smoothing ---
            if label_mouth == "Yawn":
                state.yawn_frame_count += 1
            else:
                state.yawn_frame_count = 0

            if state.yawn_frame_count >= yawn_frame_threshold:
                if not state.yawn_cooldown:
                    state.yawn_counter += 1
                    state.yawn_cooldown = True
            else:
                state.yawn_cooldown = False

            # --- visualisation ---
            e_color = (0, 0, 255) if label_eye == "Closed" else (0, 255, 0)
            m_color = (0, 0, 255) if label_mouth == "Yawn" else (255, 120, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + int(h * 0.5)), e_color, 2)
            cv2.putText(frame, f"EYE: {label_eye} ", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, e_color, 2)
            cv2.rectangle(frame, (x + int(w * 0.2), y + int(h * 0.7)),
                          (x + int(w * 0.8), y + int(h * 0.9)), m_color, 2)
            cv2.putText(frame, f"MOUTH: {label_mouth} ", (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, m_color, 2)

            # --- final status ---
            if eye_closed_duration >= eye_secs_2:
                status_text = f"!!! BAHAYA: TERTIDUR ({int(eye_closed_duration)}s) !!!"
                alert_color = (0, 0, 180)
            elif eye_closed_duration >= eye_secs_1:
                status_text = f"!!! BAHAYA: MICRO-SLEEP ({int(eye_closed_duration)}s) !!!"
                alert_color = (0, 0, 255)
            elif state.yawn_counter >= yawn_limit:
                status_text = f"PERINGATAN: LELAH ({state.yawn_counter}x Menguap)"
                alert_color = (0, 165, 255)

            # --- alert banner on the (to be sent) frame ---
            if eye_closed_duration >= eye_secs_1 or state.yawn_counter >= yawn_limit:
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 55), (0, 0, 0), -1)
                cv2.putText(frame, status_text, (10, 38),
                            cv2.FONT_HERSHEY_DUPLEX, 0.75, alert_color, 2)
            if eye_closed_duration >= eye_secs_2:
                cv2.rectangle(frame, (0, 0),
                              (frame.shape[1] - 1, frame.shape[0] - 1), (0, 0, 255), 10)

            # --- event decisions (deduped via active_alerts) ---
            meta = {
                "eye_label": label_eye, "conf_eye": conf_eye,
                "mouth_label": label_mouth, "conf_mouth": conf_mouth,
                "closed_frame_count": state.closed_frame_count,
                "yawn_count": state.yawn_counter,
                "eye_closed_threshold": eye_closed_threshold,
                "yawn_limit": yawn_limit, "time_window": time_window,
            }

            if eye_closed_duration >= eye_secs_2:
                state.active_alerts.discard("micro_sleep")
                if "fatigue_alert" not in state.active_alerts:
                    events.append(_mk_event("fatigue_alert", "danger", status_text, meta))
                    state.active_alerts.add("fatigue_alert")
            elif eye_closed_duration >= eye_secs_1:
                state.active_alerts.discard("fatigue_alert")
                if "micro_sleep" not in state.active_alerts:
                    events.append(_mk_event("micro_sleep", "danger", status_text, meta))
                    state.active_alerts.add("micro_sleep")
            else:
                state.active_alerts.discard("micro_sleep")
                state.active_alerts.discard("fatigue_alert")

            if state.yawn_counter >= yawn_limit:
                if "yawn_alert" not in state.active_alerts:
                    msg = f"PERINGATAN: LELAH ({state.yawn_counter}x Menguap)"
                    events.append(_mk_event("yawn_alert", "warning", msg, meta))
                    state.active_alerts.add("yawn_alert")
            else:
                state.active_alerts.discard("yawn_alert")

        # --- dashboard overlay ---
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 85), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, status_text, (20, 35),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, alert_color, 2)
        closed_info = (
            f"{int(eye_closed_duration)}s" if eye_closed_duration > 0
            else f"{state.closed_frame_count}f"
        )
        cv2.putText(frame,
                    f"Yawn: {state.yawn_counter}/{yawn_limit} | Mata tutup: {closed_info}",
                    (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if eye_closed_duration >= eye_secs_2:
            cv2.rectangle(frame, (0, 0),
                          (frame.shape[1] - 1, frame.shape[0] - 1), (0, 0, 255), 10)

        state.eye_closed_duration = eye_closed_duration
        state.last_eye_label, state.last_eye_conf = label_eye, conf_eye
        state.last_mouth_label, state.last_mouth_conf = label_mouth, conf_mouth

        return FrameResult(
            frame=frame,
            status_text=status_text,
            eye_label=label_eye,
            mouth_label=label_mouth,
            eye_confidence=conf_eye,
            mouth_confidence=conf_mouth,
            eye_closed_duration=eye_closed_duration,
            yawn_counter=state.yawn_counter,
            events=events,
        )


def _mk_event(event_type: str, severity: str, status_text: str, meta: dict) -> dict:
    """Lightweight event descriptor; the EventService enriches it before sending."""
    return {
        "event_type": event_type,
        "severity": severity,
        "status_text": status_text,
        "meta": meta,
    }
