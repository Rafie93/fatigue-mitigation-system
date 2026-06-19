"""Application-wide Qt stylesheets (dark + light themes — v1.2 Theme Manager)."""

APP_NAME = "Fatigue - mitigation system"
APP_VERSION = "1.2"

DARK_STYLESHEET = """
* { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; }

QWidget { background-color: #0f1419; color: #e6e6e6; font-size: 14px; }

QLabel#Title { font-size: 26px; font-weight: 700; color: #ffffff; }
QLabel#Subtitle { font-size: 14px; color: #8b9bb4; }
QLabel#SectionTitle { font-size: 16px; font-weight: 600; color: #ffffff; }
QLabel#StatusValue { font-size: 15px; font-weight: 600; }

QFrame#Card {
    background-color: #1a212b;
    border: 1px solid #263041;
    border-radius: 12px;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #1d4ed8; }
QPushButton:pressed { background-color: #1e40af; }
QPushButton:disabled { background-color: #374151; color: #9ca3af; }

QPushButton#Secondary { background-color: #334155; }
QPushButton#Secondary:hover { background-color: #3f4d63; }
QPushButton#Danger { background-color: #dc2626; }
QPushButton#Danger:hover { background-color: #b91c1c; }

QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #0b0f14;
    border: 1px solid #2b3647;
    border-radius: 6px;
    padding: 8px;
    color: #e6e6e6;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #2563eb; }

QComboBox {
    background-color: #0b0f14; border: 1px solid #2b3647; border-radius: 6px;
    padding: 8px; color: #e6e6e6;
}
QComboBox:focus { border: 1px solid #2563eb; }
QComboBox QAbstractItemView {
    background-color: #11161d; color: #e6e6e6; selection-background-color: #2563eb;
}
QRadioButton, QCheckBox { color: #e6e6e6; }

QTabWidget::pane { border: 1px solid #263041; border-radius: 8px; }
QTabBar::tab {
    background: #1a212b; color: #8b9bb4; padding: 10px 18px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}
QTabBar::tab:selected { background: #2563eb; color: #ffffff; }

QTableWidget {
    background-color: #11161d; gridline-color: #263041;
    border: 1px solid #263041; border-radius: 8px;
}
QHeaderView::section {
    background-color: #1a212b; color: #8b9bb4; padding: 8px; border: none;
}

QStatusBar { background-color: #0b0f14; color: #8b9bb4; }
QProgressBar {
    background-color: #1a212b; border: none; border-radius: 6px;
    text-align: center; color: #ffffff; height: 14px;
}
QProgressBar::chunk { background-color: #2563eb; border-radius: 6px; }
"""

LIGHT_STYLESHEET = """
* { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; }

QWidget { background-color: #f3f4f6; color: #1f2937; font-size: 14px; }

QLabel#Title { font-size: 26px; font-weight: 700; color: #111827; }
QLabel#Subtitle { font-size: 14px; color: #6b7280; }
QLabel#SectionTitle { font-size: 16px; font-weight: 600; color: #111827; }
QLabel#StatusValue { font-size: 15px; font-weight: 600; }

QFrame#Card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}

QPushButton {
    background-color: #2563eb; color: #ffffff; border: none;
    border-radius: 8px; padding: 10px 18px; font-size: 14px; font-weight: 600;
}
QPushButton:hover { background-color: #1d4ed8; }
QPushButton:pressed { background-color: #1e40af; }
QPushButton:disabled { background-color: #d1d5db; color: #9ca3af; }

QPushButton#Secondary { background-color: #e5e7eb; color: #1f2937; }
QPushButton#Secondary:hover { background-color: #d1d5db; }
QPushButton#Danger { background-color: #dc2626; }
QPushButton#Danger:hover { background-color: #b91c1c; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 6px;
    padding: 8px; color: #1f2937;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}
QComboBox QAbstractItemView {
    background-color: #ffffff; color: #1f2937; selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QRadioButton, QCheckBox { color: #1f2937; }

QTabWidget::pane { border: 1px solid #e5e7eb; border-radius: 8px; }
QTabBar::tab {
    background: #e5e7eb; color: #6b7280; padding: 10px 18px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}
QTabBar::tab:selected { background: #2563eb; color: #ffffff; }

QTableWidget {
    background-color: #ffffff; gridline-color: #e5e7eb;
    border: 1px solid #e5e7eb; border-radius: 8px;
}
QHeaderView::section {
    background-color: #f3f4f6; color: #6b7280; padding: 8px; border: none;
}

QStatusBar { background-color: #e5e7eb; color: #6b7280; }
QProgressBar {
    background-color: #e5e7eb; border: none; border-radius: 6px;
    text-align: center; color: #111827; height: 14px;
}
QProgressBar::chunk { background-color: #2563eb; border-radius: 6px; }
"""

# Backwards-compatible default (used by app.py before a theme is applied).
STYLESHEET = DARK_STYLESHEET
