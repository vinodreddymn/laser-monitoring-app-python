# ======================================================
# main.py — FINAL PRODUCTION VERSION v2.4.0
# Pneumatic Laser QC System
# ======================================================
"""
Main entry point for the Pneumatic Laser QC System.

Responsibilities:
- Application bootstrap
- Global signal bus
- Backend service startup/shutdown
- Dummy global styling only
"""

import sys
import os
import signal
import logging
from pathlib import Path

# ------------------------------------------------------
# Qt: suppress noisy QSS warnings (expected in dummy QSS)
# ------------------------------------------------------
os.environ["QT_LOGGING_RULES"] = "qt.qss.debug=false"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QObject, Signal, QTimer

# ------------------------------------------------------
# Application configuration
# ------------------------------------------------------
from config.app_config import *

# ======================================================
# LOGGING (MUST BE FIRST)
# ======================================================
from backend.logger import setup_logging
setup_logging()

log = logging.getLogger(__name__)

# ======================================================
# GLOBAL UI SIGNAL BUS
# ======================================================
class Signals(QObject):
    laser_value = Signal(float)
    laser_status = Signal(str)
    cycle_detected = Signal(dict)
    plc_status = Signal(dict)
    sms_sent = Signal(dict)


signals = Signals()

# ======================================================
# PATHS
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
STYLES_DIR = BASE_DIR / "styles"
FONTS_DIR = BASE_DIR / "fonts"

# ======================================================
# ASSET LOADING
# ======================================================
def load_fonts():
    if not FONTS_DIR.exists():
        log.warning("Fonts directory not found: %s", FONTS_DIR)
        return

    loaded = 0
    for font in FONTS_DIR.iterdir():
        if font.suffix.lower() in (".ttf", ".otf"):
            if QFontDatabase.addApplicationFont(str(font)) != -1:
                loaded += 1
                log.info("Font loaded: %s", font.name)

    log.info("Total fonts loaded: %d", loaded)


def apply_dummy_stylesheet(app: QApplication):
    """
    Applies ONLY a neutral base stylesheet.
    All real styling is widget-owned.
    """
    qss = BASE_DIR / "styles.qss"

    if not qss.exists():
        log.warning("Dummy stylesheet missing: %s", qss)
        return

    app.setStyleSheet(qss.read_text(encoding="utf-8"))
    log.info("Dummy global stylesheet applied: %s", qss.name)



# ======================================================
# BACKEND IMPORTS (AFTER LOGGING)
# ======================================================
from backend.detector import init_detector, push_laser_value, update_threshold
from backend.cycle_service import handle_detected_cycle
from backend.combined_serial_reader import combined_reader, init_combined_reader
from backend.startup_checks import run_startup_checks
from backend.sms_sender import start_sms_sender, stop_sms_sender
from backend.gsm_modem import gsm
from backend.settings_dao import get_settings
from backend.purge_service import run_purge

from config.serial_ports import APP_READ_PORT, GSM_APP_PORT
from gui.main_window import MainWindow

# ======================================================
# PLC STATUS CALLBACK
# ======================================================
def on_plc_status_update(status: dict):
    state = "CONNECTED" if status.get("connected") else "DISCONNECTED"
    log.info("PLC status → %s | %s", state, status.get("status", "UNKNOWN"))
    signals.plc_status.emit(status)

# ======================================================
# MAIN APPLICATION
# ======================================================
def main():
    log.info("=" * 64)
    log.info("Starting Pneumatic Laser QC System")
    log.info("=" * 64)

    # --------------------------------------------------
    # Qt Application
    # --------------------------------------------------
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(AUTHOR)

    # --------------------------------------------------
    # Global assets (fonts + dummy QSS)
    # --------------------------------------------------
    load_fonts()
    apply_dummy_stylesheet(app)

    # --------------------------------------------------
    # Load persisted settings
    # --------------------------------------------------
    settings = get_settings() or {}
    log.info("Settings loaded")

    # --------------------------------------------------
    # Main Window
    # --------------------------------------------------
    try:
        window = MainWindow(signals)
        window.showMaximized()
    except Exception:
        log.exception("UI initialization failed")
        sys.exit(1)

    # --------------------------------------------------
    # Startup self-checks
    # --------------------------------------------------
    try:
        results = run_startup_checks()
        log.info("Startup checks OK: %s", results)
    except Exception:
        log.exception("Startup checks failed")

    # --------------------------------------------------
    # Purge service (startup + periodic)
    # --------------------------------------------------
    try:
        run_purge()
        log.info("Startup purge completed")
    except Exception:
        log.exception("Startup purge failed")

    purge_timer = QTimer()
    purge_timer.timeout.connect(run_purge)
    purge_timer.start(PURGE_INTERVAL * 1000)

    # --------------------------------------------------
    # Detector initialization
    # --------------------------------------------------
    threshold = float(settings.get("laser_threshold", 1.0))
    init_detector(lambda cycle: handle_detected_cycle(cycle, signals))
    update_threshold(threshold)

    log.info("Detector initialized (threshold=%s)", threshold)

    # --------------------------------------------------
    # Serial / PLC communication
    # --------------------------------------------------
    init_combined_reader()

    combined_reader.laser_value.connect(push_laser_value)
    combined_reader.laser_value.connect(signals.laser_value.emit)
    combined_reader.plc_status.connect(on_plc_status_update)
    combined_reader.status_changed.connect(signals.laser_status.emit)

    log.info("Serial reader initialized")

    # --------------------------------------------------
    # GSM modem + SMS sender
    # --------------------------------------------------
    try:
        gsm.start()
        log.info("GSM modem started (%s)", GSM_APP_PORT)
    except Exception:
        log.exception("GSM modem start failed")

    try:
        start_sms_sender()
        log.info("SMS sender started")
    except Exception:
        log.exception("SMS sender start failed")

    # --------------------------------------------------
    # Graceful shutdown handler
    # --------------------------------------------------
    def shutdown():
        log.info("Shutdown initiated")

        steps = [
            (purge_timer.stop, "Purge timer"),
            (combined_reader.stop, "Serial reader"),
            (stop_sms_sender, "SMS sender"),
        ]

        for action, name in steps:
            try:
                action()
                log.info("%s stopped", name)
            except Exception:
                log.exception("Failed stopping %s", name)

        try:
            gsm.stop()
            log.info("GSM modem stopped")
        except Exception:
            log.exception("GSM modem shutdown failed")

        log.info("Shutdown complete")

    app.aboutToQuit.connect(shutdown)

    if os.name != "nt":
        signal.signal(signal.SIGINT, lambda *_: app.quit())

    # --------------------------------------------------
    # System ready
    # --------------------------------------------------
    log.info("SYSTEM FULLY OPERATIONAL")
    log.info("Laser / PLC → %s", APP_READ_PORT)
    log.info("GSM App     → %s", GSM_APP_PORT)

    sys.exit(app.exec())


# ======================================================
if __name__ == "__main__":
    main()
