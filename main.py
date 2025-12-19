# ======================================================
# main.py — FINAL PRODUCTION VERSION v2.3.7
# Pneumatic Laser QC System
# ======================================================

import sys
import os
import signal
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QTimer, QObject, Signal

# ======================================================
# LOGGING (MUST BE FIRST IMPORT)
# ======================================================
from backend.logger import setup_logging
setup_logging()

log = logging.getLogger(__name__)

# ======================================================
# GLOBAL SIGNAL BUS (UI)
# ======================================================
class Signals(QObject):
    laser_value = Signal(float)
    laser_status = Signal(str)
    cycle_detected = Signal(dict)
    plc_status = Signal(dict)
    sms_sent = Signal(dict)


signals = Signals()

# ======================================================
# ASSET LOADING
# ======================================================
def load_fonts():
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    if not os.path.isdir(fonts_dir):
        log.warning("Fonts directory not found")
        return

    count = 0
    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            if QFontDatabase.addApplicationFont(
                os.path.join(fonts_dir, fname)
            ) != -1:
                count += 1
                log.info("Font loaded: %s", fname)

    log.info("Total fonts loaded: %d", count)


def load_stylesheet(app: QApplication):
    for path in ("gui/styles.qss", "styles.qss"):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            log.info("Stylesheet applied: %s", path)
            return
    log.warning("No stylesheet found — default Qt style used")

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
    log.info(
        "PLC status → %s | %s",
        "CONNECTED" if status.get("connected") else "DISCONNECTED",
        status.get("status", "UNKNOWN"),
    )
    signals.plc_status.emit(status)

# ======================================================
# MAIN APPLICATION
# ======================================================
def main():
    log.info("=" * 60)
    log.info("Starting Pneumatic Laser QC System")
    log.info("=" * 60)

    # --------------------------------------------------
    # QT APPLICATION
    # --------------------------------------------------
    app = QApplication(sys.argv)
    app.setApplicationName("Pneumatic QC System")
    app.setOrganizationName("Ashtech Engineering Solutions")

    # --------------------------------------------------
    # LOAD UI ASSETS
    # --------------------------------------------------
    load_fonts()
    load_stylesheet(app)

    # --------------------------------------------------
    # LOAD SETTINGS
    # --------------------------------------------------
    settings = get_settings() or {}
    log.info("Settings loaded: %s", settings)

    # --------------------------------------------------
    # MAIN WINDOW
    # --------------------------------------------------
    try:
        window = MainWindow(signals)
        window.showMaximized()
    except Exception:
        log.exception("UI initialization failed")
        sys.exit(1)

    # --------------------------------------------------
    # STARTUP CHECKS
    # --------------------------------------------------
    try:
        results = run_startup_checks()
        log.info("Startup self-checks: %s", results)
    except Exception:
        log.exception("Startup self-checks failed")

    # --------------------------------------------------
    # PURGE SERVICE (STARTUP + PERIODIC)
    # --------------------------------------------------
    try:
        run_purge()
        log.info("Startup purge completed")
    except Exception:
        log.exception("Startup purge failed")

    def periodic_purge():
        try:
            run_purge()
        except Exception:
            log.exception("Periodic purge failed")

    purge_timer = QTimer()
    purge_timer.timeout.connect(periodic_purge)
    purge_timer.start(60 * 60 * 1000)  # 1 hour

    # --------------------------------------------------
    # DETECTOR INITIALIZATION
    # --------------------------------------------------
    threshold = float(settings.get("laser_threshold", 1.0))
    init_detector(lambda cycle: handle_detected_cycle(cycle, signals))
    update_threshold(threshold)
    log.info("Detector initialized (threshold=%s)", threshold)

    # --------------------------------------------------
    # SERIAL / PLC COMMUNICATION
    # --------------------------------------------------
    init_combined_reader()

    combined_reader.laser_value.connect(push_laser_value)
    combined_reader.laser_value.connect(signals.laser_value.emit)
    combined_reader.plc_status.connect(on_plc_status_update)
    combined_reader.status_changed.connect(signals.laser_status.emit)

    # --------------------------------------------------
    # GSM MODEM + SMS SYSTEM
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
    # SHUTDOWN HANDLER (CRASH-PROOF)
    # --------------------------------------------------
    def shutdown():
        log.info("Shutdown initiated")

        steps = [
            (purge_timer.stop, "Purge timer"),
            (combined_reader.stop, "Serial reader"),
            (stop_sms_sender, "SMS sender"),
        ]

        for action, label in steps:
            try:
                action()
                log.info("%s stopped", label)
            except Exception:
                log.exception("Failed stopping %s", label)

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
    # SYSTEM READY
    # --------------------------------------------------
    log.info("SYSTEM FULLY OPERATIONAL")
    log.info("Laser + PLC → %s", APP_READ_PORT)
    log.info("GSM App     → %s", GSM_APP_PORT)

    sys.exit(app.exec())


# ======================================================
if __name__ == "__main__":
    main()
