# ======================================================
# main.py — FINAL PRODUCTION VERSION v2.4.1
# Pneumatic Laser QC System
# ======================================================

"""
Main entry point for the Pneumatic Laser QC System.

Responsibilities:
- Application bootstrap
- Qt-safe signal bridge
- Backend service startup/shutdown
- GUI lifecycle
"""

import sys
import os
import signal
import logging
from pathlib import Path

# ------------------------------------------------------
# Qt logging suppression (noise control)
# ------------------------------------------------------
os.environ["QT_LOGGING_RULES"] = (
    "qt.qpa.fonts=false\n"
    "qt.qpa.fonts.warning=false\n"
    "qt.qss.debug=false\n"
)

# ------------------------------------------------------
# Qt imports
# ------------------------------------------------------
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QObject, Signal, QTimer, QLoggingCategory

# ------------------------------------------------------
# App config
# ------------------------------------------------------
from config.app_config import *

# ======================================================
# LOGGING (MUST BE FIRST)
# ======================================================
from backend.logger import setup_logging
setup_logging()
log = logging.getLogger(__name__)

# ======================================================
# GLOBAL UI SIGNAL BUS (Qt-thread owned)
# ======================================================
class Signals(QObject):
    laser_value = Signal(float)
    laser_status = Signal(str)
    cycle_detected = Signal(dict)
    plc_status = Signal(dict)
    sms_sent = Signal(dict)

signals = Signals()

# ======================================================
# Qt-SAFE CYCLE BRIDGE (CRITICAL)
# ======================================================
class CycleBridge(QObject):
    """
    Sole purpose:
    Receive cycles from detector thread
    and re-emit them inside Qt event loop.
    """
    cycle_ready = Signal(dict)

cycle_bridge = CycleBridge()

# ======================================================
# PATHS
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "fonts"

# ======================================================
# ASSET LOADING
# ======================================================
def load_fonts():
    if not FONTS_DIR.exists():
        log.warning("Fonts directory missing: %s", FONTS_DIR)
        return

    loaded = 0
    for font in FONTS_DIR.iterdir():
        if font.suffix.lower() in (".ttf", ".otf"):
            if QFontDatabase.addApplicationFont(str(font)) != -1:
                loaded += 1
                log.info("Font loaded: %s", font.name)

    log.info("Total fonts loaded: %d", loaded)


def apply_dummy_stylesheet(app: QApplication):
    qss = BASE_DIR / "styles.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
        log.info("Dummy stylesheet applied")

# ======================================================
# BACKEND IMPORTS
# ======================================================
from backend.detector import init_detector, push_laser_value, update_threshold
from backend.cycle_service import handle_detected_cycle
from backend.combined_serial_reader import combined_reader, init_combined_reader
from backend.startup_checks import run_startup_checks
from backend.sms_sender import start_sms_sender, stop_sms_sender
from backend.gsm_modem import gsm
from backend.settings_dao import get_settings
from backend.purge_service import run_purge

from gui.main_window import MainWindow
from config.app_config import APP_READ_PORT, GSM_APP_PORT

# ======================================================
# PLC STATUS CALLBACK
# ======================================================
def on_plc_status_update(status: dict):
    signals.plc_status.emit(status)

# ======================================================
# MAIN
# ======================================================
def main():
    log.info("=" * 70)
    log.info("🚀 Starting Pneumatic Laser QC System")
    log.info("=" * 70)

    # --------------------------------------------------
    # Qt Application
    # --------------------------------------------------
    app = QApplication(sys.argv)

    QLoggingCategory.setFilterRules(
        "qt.qpa.fonts=false\n"
        "qt.qpa.fonts.warning=false\n"
    )

    app.setApplicationName(APP_NAME)
    app.setOrganizationName(AUTHOR)

    # --------------------------------------------------
    # Assets
    # --------------------------------------------------
    load_fonts()
    apply_dummy_stylesheet(app)

    # --------------------------------------------------
    # Settings
    # --------------------------------------------------
    settings = get_settings() or {}
    threshold = float(settings.get("laser_threshold", 1.0))
    log.info("Settings loaded")

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    window = MainWindow(signals)
    window.showMaximized()

    # --------------------------------------------------
    # Startup checks
    # --------------------------------------------------
    try:
        run_startup_checks()
    except Exception:
        log.exception("Startup checks failed")

    # --------------------------------------------------
    # Purge service
    # --------------------------------------------------
    run_purge()
    purge_timer = QTimer()
    purge_timer.timeout.connect(run_purge)
    purge_timer.start(PURGE_INTERVAL * 1000)

    # ==================================================
    # 🔑 DETECTOR → QT SAFE WIRING (THIS FIXES EVERYTHING)
    # ==================================================

    # 1️⃣ CycleBridge emits inside Qt thread
    cycle_bridge.cycle_ready.connect(
        lambda c: handle_detected_cycle(c, signals)
    )

    # 2️⃣ Detector callback (pure Python thread)
    def detector_callback(cycle: dict):
        cycle_bridge.cycle_ready.emit(dict(cycle))

    init_detector(detector_callback)
    update_threshold(threshold)

    log.info("Detector initialized (touch-point mode)")

    # --------------------------------------------------
    # Serial / PLC
    # --------------------------------------------------
    init_combined_reader()

    combined_reader.laser_value.connect(push_laser_value)
    combined_reader.laser_value.connect(signals.laser_value.emit)
    combined_reader.plc_status.connect(on_plc_status_update)
    combined_reader.status_changed.connect(signals.laser_status.emit)

    log.info("Serial reader initialized")

    # --------------------------------------------------
    # GSM + SMS
    # --------------------------------------------------
    gsm.start()
    start_sms_sender()

    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------
    def shutdown():
        log.info("Shutdown initiated")

        purge_timer.stop()
        combined_reader.stop()
        stop_sms_sender()
        gsm.stop()

        log.info("Shutdown complete")

    app.aboutToQuit.connect(shutdown)

    if os.name != "nt":
        signal.signal(signal.SIGINT, lambda *_: app.quit())

    # --------------------------------------------------
    # RUN
    # --------------------------------------------------
    log.info("✅ SYSTEM FULLY OPERATIONAL")
    sys.exit(app.exec())


# ======================================================
if __name__ == "__main__":
    main()
