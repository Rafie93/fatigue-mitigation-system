"""Camera discovery and source building (v1.2 — multi camera / multiple types)."""
import sys
from dataclasses import dataclass

import cv2


@dataclass
class CameraDevice:
    index: int
    name: str
    kind: str = "camera"  # integrated | usb | camera

    @property
    def label(self) -> str:
        return self.name


def _backend():
    """Pick a sensible per-platform OpenCV backend for local devices."""
    if sys.platform == "darwin":
        return cv2.CAP_AVFOUNDATION
    if sys.platform.startswith("win"):
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY


def discover_cameras(max_index: int = 6) -> list[CameraDevice]:
    """Probe indices 0..max_index-1 and return the ones that open and deliver a
    frame. Names are synthesised (OpenCV cannot read device names portably)."""
    devices: list[CameraDevice] = []
    for index in range(max_index):
        cap = cv2.VideoCapture(index, _backend())
        opened = cap.isOpened()
        ok = False
        if opened:
            ok, _ = cap.read()
        cap.release()
        if opened and ok:
            kind = "integrated" if index == 0 else "usb"
            name = "Integrated Camera" if index == 0 else f"USB Camera {index}"
            devices.append(CameraDevice(index=index, name=name, kind=kind))
    if not devices:
        # Always expose a default so the UI is never empty.
        devices.append(CameraDevice(index=0, name="Default Camera", kind="integrated"))
    return devices


def build_capture(camera_cfg: dict) -> cv2.VideoCapture:
    """Create a cv2.VideoCapture from the `camera` config section.

    Supports integrated/usb/virtual (by index) and rtsp/http (by URL)."""
    ctype = (camera_cfg.get("camera_type") or "integrated").lower()
    url = (camera_cfg.get("camera_url") or "").strip()
    index = int(camera_cfg.get("camera_index", 0) or 0)

    if ctype in ("rtsp", "http") and url:
        # FFMPEG backend handles RTSP and HTTP/MJPEG streams.
        return cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    return cv2.VideoCapture(index, _backend())


def describe_source(camera_cfg: dict) -> str:
    """Human-readable label for the configured source (for status display)."""
    ctype = (camera_cfg.get("camera_type") or "integrated").lower()
    if ctype in ("rtsp", "http"):
        return f"{ctype.upper()}: {camera_cfg.get('camera_url', '')}".strip()
    return f"Camera #{int(camera_cfg.get('camera_index', 0) or 0)}"
