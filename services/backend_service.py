"""Talks to the Laravel/REST backend using only the standard library (urllib)."""
import json
from urllib import error, request

REQUEST_TIMEOUT_SECONDS = 5


class BackendService:
    """Stateless HTTP client. Configuration is passed in per call so it always
    reflects the latest saved config."""

    def __init__(self, config_service):
        self.config = config_service

    # ------------------------------------------------------------- helpers
    def _url(self) -> str:
        # event.backend_url takes precedence, fall back to backend.api_url
        url = (self.config.get("event", "backend_url", "") or "").strip()
        if not url:
            url = (self.config.get("backend", "api_url", "") or "").strip()
        return url

    def _token(self) -> str:
        token = (self.config.get("event", "backend_token", "") or "").strip()
        if not token:
            token = (self.config.get("backend", "device_token", "") or "").strip()
        return token

    def is_ready(self) -> bool:
        return bool(self._url()) and bool(self._token())

    # ------------------------------------------------------------- network
    def send(self, payload: dict) -> bool:
        """POST a single event payload. Returns True on 2xx."""
        if not self.is_ready():
            return False
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self._url(),
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Device-Token": self._token(),
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                return 200 <= resp.status < 300
        except (error.URLError, error.HTTPError, TimeoutError, OSError):
            return False

    def check_connection(self) -> bool:
        """Best-effort reachability check for the configured endpoint."""
        url = self._url()
        if not url:
            return False
        try:
            req = request.Request(url, method="HEAD")
            with request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                return resp.status < 500
        except error.HTTPError:
            # Server answered (4xx) -> it is reachable.
            return True
        except (error.URLError, TimeoutError, OSError):
            return False
