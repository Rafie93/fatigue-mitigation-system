"""Theme manager (v1.2). Applies light/dark/system themes at runtime."""
from PySide6.QtCore import Qt

from ui.theme import DARK_STYLESHEET, LIGHT_STYLESHEET


def resolve_mode(mode: str) -> str:
    """Resolve 'system' to either 'light' or 'dark' using the OS color scheme."""
    mode = (mode or "system").lower()
    if mode in ("light", "dark"):
        return mode
    try:
        from PySide6.QtWidgets import QApplication
        scheme = QApplication.styleHints().colorScheme()
        return "dark" if scheme == Qt.ColorScheme.Dark else "light"
    except Exception:
        return "dark"


def stylesheet_for(mode: str) -> str:
    return DARK_STYLESHEET if resolve_mode(mode) == "dark" else LIGHT_STYLESHEET


def apply_theme(app, mode: str) -> None:
    """Apply the theme to the whole application (no restart required)."""
    app.setStyleSheet(stylesheet_for(mode))
