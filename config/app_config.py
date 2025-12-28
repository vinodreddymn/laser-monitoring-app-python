# config/app_config.py
"""
Application Configuration
-------------------------
- Defaults
- Runtime helpers
- Persistent plain-text password via security.json

Designed for offline / kiosk / industrial systems
"""

import json
import os
import logging

log = logging.getLogger(__name__)

# ==================================================
# Paths
# ==================================================

CONFIG_DIR = os.path.dirname(__file__)
SECURITY_FILE = os.path.join(CONFIG_DIR, "security.json")


# ==================================================
# Application Information
# ==================================================

APP_NAME = "Pneumatic Laser QC System"
VERSION = "2.3.7"
AUTHOR = "Development Team"

WINDOW_TITLE = f"{APP_NAME} v{VERSION}"


# ==================================================
# Security (PLAIN PASSWORD – PERSISTENT)
# ==================================================

DEFAULT_SETTINGS_PASSWORD = "admin123"

_SETTINGS_PASSWORD = None  # loaded at runtime


def _load_security_config() -> None:
    """
    Load password from security.json.
    Creates file with default password if missing.
    """
    global _SETTINGS_PASSWORD

    if not os.path.exists(SECURITY_FILE):
        _SETTINGS_PASSWORD = DEFAULT_SETTINGS_PASSWORD
        _save_security_config()
        return

    try:
        with open(SECURITY_FILE, "r") as f:
            data = json.load(f)
            _SETTINGS_PASSWORD = data.get(
                "settings_password",
                DEFAULT_SETTINGS_PASSWORD
            )
    except Exception:
        log.exception("Failed to load security.json, using default password")
        _SETTINGS_PASSWORD = DEFAULT_SETTINGS_PASSWORD


def _save_security_config() -> None:
    """
    Persist password to security.json.
    """
    try:
        with open(SECURITY_FILE, "w") as f:
            json.dump(
                {"settings_password": _SETTINGS_PASSWORD},
                f,
                indent=4
            )
    except Exception:
        log.exception("Failed to save security.json")


def verify_settings_password(password: str) -> bool:
    """
    Verify settings password (plain text).
    """
    if _SETTINGS_PASSWORD is None:
        _load_security_config()

    return password == _SETTINGS_PASSWORD


def update_settings_password(new_password: str) -> None:
    """
    Update and persist settings password.
    """
    global _SETTINGS_PASSWORD

    _SETTINGS_PASSWORD = new_password
    _save_security_config()


# Load password on module import
_load_security_config()


# ==================================================
# Logging Configuration
# ==================================================

LOG_LEVEL = "INFO"

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ==================================================
# UI Configuration
# ==================================================

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1000

PRIMARY_COLOR = "#1d4ed8"
SUCCESS_COLOR = "#10b981"
ERROR_COLOR = "#ef4444"
WARNING_COLOR = "#f59e0b"


# ==================================================
# Serial Communication Defaults
# ==================================================

DEFAULT_BAUD_LASER = 9600
DEFAULT_BAUD_PLC = 9600
DEFAULT_BAUD_GSM = 115200

SERIAL_TIMEOUT = 1.0
SERIAL_WRITE_TIMEOUT = 1.0


# ==================================================
# Timeouts & Intervals
# ==================================================

GSM_HEARTBEAT_INTERVAL = 5.0
GSM_RECONNECT_DELAY = 3.0
PRINTER_CHECK_INTERVAL = 5.0

PLC_POLL_INTERVAL = 1000          # ms
SMS_POLL_INTERVAL = 20            # seconds
PURGE_INTERVAL = 3600             # seconds


# ==================================================
# Limits & Capacities
# ==================================================

MAX_SMS_QUEUE_SIZE = 200
MAX_CYCLE_HISTORY = 100


# ==================================================
# File & Directory Paths
# ==================================================

FONTS_DIR = "fonts"
ASSETS_DIR = "assets"
LOGS_DIR = "logs"
PRINTS_DIR = "prints"
QR_IMAGES_DIR = "qr_images"


# ==================================================
# Database Configuration
# ==================================================

DB_HOST = "localhost"
DB_USER = "svr_user"
DB_PASSWORD = "india123"
DB_NAME = "laser_monitoring"


# ==================================================
# Default System Settings
# ==================================================

DEFAULT_QR_PREFIX = "G510"
DEFAULT_QR_START_COUNTER = 100000
DEFAULT_MODEL_TYPE = "LHD"


# ==================================================
# Data Retention
# ==================================================

DEFAULT_SMS_RETENTION_HOURS = 6
DEFAULT_QR_RETENTION_HOURS = 6


# ==================================================
# Peripheral Defaults
# ==================================================

DEFAULT_GSM_PORT = "COM1"
DEFAULT_PLC_PORT = "COM6"
DEFAULT_PRINTER_NAME = "PDFCreator"


# ==================================================
# Feature Flags
# ==================================================

ENABLE_SMS = True
ENABLE_PRINTER = True
ENABLE_GSM = True


# ==================================================
# Printer Settings
# ==================================================

EXCLUDED_PRINTERS = [
    "fax",
    "pdf",
    "xps",
    "microsoft",
    "onenote",
]
