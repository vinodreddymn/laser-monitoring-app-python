# config/app_config.py
"""
Application configuration constants.
All hardcoded values should be moved here for easy maintenance.
"""

# Application Info
APP_NAME = "Pneumatic Laser QC System"
VERSION = "2.3.7"
AUTHOR = "Development Team"

# Security
SETTINGS_PASSWORD = "admin123"  # Password for accessing settings

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# UI
WINDOW_TITLE = f"{APP_NAME} v{VERSION}"
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1000

# Serial Communication
DEFAULT_BAUD_LASER = 9600
DEFAULT_BAUD_PLC = 9600
DEFAULT_BAUD_GSM = 115200
SERIAL_TIMEOUT = 1.0
SERIAL_WRITE_TIMEOUT = 1.0

# Timeouts and Intervals
GSM_HEARTBEAT_INTERVAL = 5.0
GSM_RECONNECT_DELAY = 3.0
PRINTER_CHECK_INTERVAL = 5.0
PLC_POLL_INTERVAL = 1000  # ms
SMS_POLL_INTERVAL = 20  # seconds
PURGE_INTERVAL = 3600  # seconds (1 hour)

# Limits
MAX_SMS_QUEUE_SIZE = 200
MAX_CYCLE_HISTORY = 100

# File Paths (relative to project root)
FONTS_DIR = "fonts"
ASSETS_DIR = "assets"
LOGS_DIR = "logs"
PRINTS_DIR = "prints"
QR_IMAGES_DIR = "qr_images"

# Database
DB_HOST = "localhost"
DB_USER = "svr_user"
DB_PASSWORD = "india123"
DB_NAME = "laser_monitoring"

# Default Settings
DEFAULT_QR_PREFIX = "G510"
DEFAULT_QR_START_COUNTER = 100000
DEFAULT_MODEL_TYPE = "LHD"

# Purge Settings
DEFAULT_SMS_RETENTION_HOURS = 6
DEFAULT_QR_RETENTION_HOURS = 6

# Peripheral Defaults
DEFAULT_GSM_PORT = "COM1"
DEFAULT_PLC_PORT = "COM6"
DEFAULT_PRINTER_NAME = "PDFCreator"

# UI Colors and Styles
PRIMARY_COLOR = "#1d4ed8"
SUCCESS_COLOR = "#10b981"
ERROR_COLOR = "#ef4444"
WARNING_COLOR = "#f59e0b"

# Feature Flags
ENABLE_SMS = True
ENABLE_PRINTER = True
ENABLE_GSM = True

# Printer Settings
EXCLUDED_PRINTERS = ["fax", "pdf", "xps", "microsoft", "onenote"]