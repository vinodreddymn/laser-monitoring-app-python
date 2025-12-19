# ======================================================
# backend/logger.py
# Centralized Logging Configuration (Production)
# ======================================================

import logging
import logging.handlers
import os
import sys

# ------------------------------------------------------
# LOG DIRECTORY
# ------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")


def setup_logging():
    """
    Global logging setup:
    - Console logging (INFO)
    - Rotating application log (INFO+)
    - Rotating error log (ERROR+)
    - Captures unhandled exceptions
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # -------------------------------
    # CONSOLE
    # -------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # -------------------------------
    # APP LOG (ROTATING)
    # -------------------------------
    app_file_handler = logging.handlers.RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,             # ~30 MB max
        encoding="utf-8",
    )
    app_file_handler.setLevel(logging.INFO)
    app_file_handler.setFormatter(formatter)

    # -------------------------------
    # ERROR LOG (ROTATING)
    # -------------------------------
    error_file_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=2 * 1024 * 1024,   # 2 MB
        backupCount=5,             # ~12 MB max
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    # -------------------------------
    # RESET HANDLERS
    # -------------------------------
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)

    # -------------------------------
    # GLOBAL EXCEPTION HOOK
    # -------------------------------
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.critical(
            "UNHANDLED EXCEPTION",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception

    root_logger.info("Logging system initialized")
    root_logger.info("Log directory: %s", LOG_DIR)
