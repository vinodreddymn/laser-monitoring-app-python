# config/app_config.py
"""
Application Configuration
-------------------------
- Loads from config.json
- Runtime helpers
- Persistent plain-text password via config.json

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
CONFIG_FILE = os.path.join(CONFIG_DIR, "..", "config.json")
SECURITY_FILE = os.path.join(CONFIG_DIR, "security.json")  # Keep separate for security


# ==================================================
# Load Config
# ==================================================

def _load_config():
    if not os.path.exists(CONFIG_FILE):
        log.error(f"Config file not found: {CONFIG_FILE}")
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Failed to load config.json: {e}")
        return {}

config = _load_config()

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
# Database Configuration
# ==================================================

DB_HOST = config.get("database", {}).get("host", "localhost")
DB_USER = config.get("database", {}).get("user", "svr_user")
DB_PASSWORD = config.get("database", {}).get("password", "india123")
DB_NAME = config.get("database", {}).get("name", "pneumatic_qc")


# ==================================================
# Serial Ports
# ==================================================

SIMULATOR_WRITE_PORT = config.get("serial_ports", {}).get("simulator_write_port", "COM5")
APP_READ_PORT = config.get("serial_ports", {}).get("app_read_port", "COM6")
GSM_SIMULATOR_PORT = config.get("serial_ports", {}).get("gsm_simulator_port", "COM2")
GSM_APP_PORT = config.get("serial_ports", {}).get("gsm_app_port", "COM1")
LASER_BAUD = config.get("serial_ports", {}).get("laser_baud", 9600)
PLC_BAUD = config.get("serial_ports", {}).get("plc_baud", 9600)
GSM_BAUD = config.get("serial_ports", {}).get("gsm_baud", 115200)


# ==================================================
# Peripherals
# ==================================================

DEFAULT_GSM_PORT = config.get("peripherals", {}).get("gsm_port", "COM1")
DEFAULT_PLC_PORT = config.get("peripherals", {}).get("plc_port", "COM6")
DEFAULT_PRINTER_NAME = config.get("peripherals", {}).get("printer_name", "PDFCreator")


# ==================================================
# Logging Configuration
# ==================================================

LOG_LEVEL = config.get("app_settings", {}).get("log_level", "INFO")

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ==================================================
# UI Configuration
# ==================================================

WINDOW_WIDTH = config.get("app_settings", {}).get("window_width", 1920)
WINDOW_HEIGHT = config.get("app_settings", {}).get("window_height", 1000)

PRIMARY_COLOR = config.get("app_settings", {}).get("primary_color", "#1d4ed8")
SUCCESS_COLOR = config.get("app_settings", {}).get("success_color", "#10b981")
ERROR_COLOR = config.get("app_settings", {}).get("error_color", "#ef4444")
WARNING_COLOR = config.get("app_settings", {}).get("warning_color", "#f59e0b")


# ==================================================
# Serial Communication Defaults
# ==================================================

DEFAULT_BAUD_LASER = LASER_BAUD
DEFAULT_BAUD_PLC = PLC_BAUD
DEFAULT_BAUD_GSM = GSM_BAUD

SERIAL_TIMEOUT = config.get("app_settings", {}).get("serial_timeout", 1.0)
SERIAL_WRITE_TIMEOUT = config.get("app_settings", {}).get("serial_write_timeout", 1.0)


# ==================================================
# Timeouts & Intervals
# ==================================================

GSM_HEARTBEAT_INTERVAL = config.get("app_settings", {}).get("gsm_heartbeat_interval", 5.0)
GSM_RECONNECT_DELAY = config.get("app_settings", {}).get("gsm_reconnect_delay", 3.0)
PRINTER_CHECK_INTERVAL = config.get("app_settings", {}).get("printer_check_interval", 5.0)

PLC_POLL_INTERVAL = config.get("app_settings", {}).get("plc_poll_interval", 1000)
SMS_POLL_INTERVAL = config.get("app_settings", {}).get("sms_poll_interval", 20)
PURGE_INTERVAL = config.get("app_settings", {}).get("purge_interval", 3600)


# ==================================================
# Limits & Capacities
# ==================================================

MAX_SMS_QUEUE_SIZE = config.get("app_settings", {}).get("max_sms_queue_size", 200)
MAX_CYCLE_HISTORY = config.get("app_settings", {}).get("max_cycle_history", 100)


# ==================================================
# File & Directory Paths
# ==================================================

FONTS_DIR = "fonts"
ASSETS_DIR = "assets"
LOGS_DIR = "logs"
PRINTS_DIR = "prints"
QR_IMAGES_DIR = "qr_images"


# ==================================================
# Default System Settings
# ==================================================

DEFAULT_QR_PREFIX = config.get("app_settings", {}).get("default_qr_prefix", "G510")
DEFAULT_QR_START_COUNTER = config.get("app_settings", {}).get("default_qr_start_counter", 100000)
DEFAULT_MODEL_TYPE = config.get("app_settings", {}).get("default_model_type", "LHD")


# ==================================================
# Data Retention
# ==================================================

DEFAULT_SMS_RETENTION_HOURS = config.get("app_settings", {}).get("default_sms_retention_hours", 6)
DEFAULT_QR_RETENTION_HOURS = config.get("app_settings", {}).get("default_qr_retention_hours", 6)


# ==================================================
# Feature Flags
# ==================================================

ENABLE_SMS = config.get("app_settings", {}).get("enable_sms", True)
ENABLE_PRINTER = config.get("app_settings", {}).get("enable_printer", True)
ENABLE_GSM = config.get("app_settings", {}).get("enable_gsm", True)


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

# ======================================================
# TEST / SIMULATION MODE
# ======================================================
ENABLE_SIMULATOR = config.get("app_settings", {}).get("enable_simulator", True)
SIMULATOR_PORT = config.get("app_settings", {}).get("simulator_port", "COM5")
