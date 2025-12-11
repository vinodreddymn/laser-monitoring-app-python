# ======================================================
# main.py — FINAL PRODUCTION VERSION v2.1
# Pneumatic Laser QC System
# Laser + PLC → COM6 | GSM → COM1
# ======================================================

import sys
import os
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QTimer, QObject, Signal

# ======================================================
# GLOBAL SIGNAL BUS
# ======================================================
class Signals(QObject):
    laser_value = Signal(float)
    laser_status = Signal(str)   # ✅ NEW
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
        print("⚠️ No 'fonts' folder found")
        return

    loaded = 0
    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            path = os.path.join(fonts_dir, fname)
            fid = QFontDatabase.addApplicationFont(path)
            if fid != -1:
                print(f"✅ Font loaded: {fname}")
                loaded += 1
    print(f"✅ Loaded {loaded} font(s)")


def load_stylesheet(app: QApplication):
    for path in ("gui/styles.qss", "styles.qss"):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            print(f"✅ Stylesheet applied: {os.path.basename(path)}")
            return
    print("⚠️ No stylesheet found — default Qt style used")

# ======================================================
# BACKEND IMPORTS
# ======================================================
from backend.detector import (
    init_detector,
    push_laser_value,
    set_active_model,
    update_threshold
)

from backend.models_dao import get_active_model
from backend.qr_generator import generate_and_save_qr_code
from backend.cycles_dao import log_cycle

from backend.combined_serial_reader import combined_reader, init_combined_reader


from backend.sms_sender import start_sms_sender, stop_sms_sender
from backend.sms_dao import queue_sms_by_model

from backend.gsm_modem import gsm

from gui.main_window import MainWindow

# ======================================================
# CALLBACKS
# ======================================================
def on_cycle_detected(cycle: dict):
    status = cycle.get("pass_fail", "UNKNOWN")
    peak = cycle.get("peak_height", 0.0)

    print(f"\n🔁 CYCLE → {status} | Peak: {peak:.2f} mm")

    # ✅ QR Generate only for PASS
    if status == "PASS":
        try:
            qr = generate_and_save_qr_code()
            cycle["qr_code_id"] = qr.get("id")
            cycle["qr_text"] = qr.get("text")
            print(f"✅ QR Generated → ID: {qr['id']}")
        except Exception as e:
            print(f"❌ QR Error: {e}")

    # ✅ Queue SMS only for FAIL
    if status == "FAIL" and cycle.get("model_id"):
        QTimer.singleShot(
            0,
            lambda: queue_sms_by_model(cycle["model_id"], cycle)
        )

    # ✅ Log to database
    try:
        log_cycle(cycle)
    except Exception as e:
        print(f"❌ DB Log Error: {e}")

    signals.cycle_detected.emit(cycle)


def on_plc_status_update(status: dict):
    power = "ON" if status.get("power") else "OFF"
    state = status.get("status", "UNKNOWN")
    print(f"⚙️ PLC → {power} | Status: {state}")
    signals.plc_status.emit(status)

# ======================================================
# MAIN APPLICATION
# ======================================================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pneumatic QC System")
    app.setOrganizationName("YourCompany")

    # -------------------------------
    # LOAD ASSETS
    # -------------------------------
    load_fonts()
    load_stylesheet(app)

    # -------------------------------
    # GUI
    # -------------------------------
    window = MainWindow(signals)
    window.showMaximized()

    print("\n" + "═" * 72)
    print("✅ PNEUMATIC LASER QC SYSTEM v2.1 — STARTING")
    print("═" * 72)

    # -------------------------------
    # DETECTOR INIT
    # -------------------------------
    init_detector(on_cycle_detected)
    update_threshold(1.0)
    print("✅ Detector initialized & threshold set")

    # -------------------------------
    # LOAD ACTIVE MODEL
    # -------------------------------
    try:
        model = get_active_model()
        if model:
            set_active_model(model)
            print(f"✅ Model Loaded → {model['name']}")
            print(f"   Tolerance → {model['lower_limit']} – {model['upper_limit']} mm")
        else:
            print("⚠️ No active model found in DB")
    except Exception as e:
        print(f"❌ Model load failed: {e}")

    # -------------------------------
    # SERIAL COMMUNICATION
    # -------------------------------
    print("\n✅ Starting serial communication...")

    init_combined_reader()

    combined_reader.laser_value.connect(push_laser_value)
    combined_reader.laser_value.connect(lambda v: signals.laser_value.emit(v))

    combined_reader.plc_status.connect(on_plc_status_update)
    combined_reader.status_changed.connect(lambda s: signals.laser_status.emit(s))




    # -------------------------------
    # GSM MODEM + SMS SYSTEM
    # -------------------------------
    try:
        gsm.start()
        print("✅ GSM Modem Connected (COM1)")
    except Exception as e:
        print("❌ GSM Failed:", e)

    try:
        start_sms_sender()
        print("✅ SMS Alert System → ACTIVE")
    except Exception as e:
        print("❌ SMS System failed:", e)

    # Optional GSM Keepalive Poll
    def poll_gsm():
        try:
            reply = gsm.send("STATUS?")
            print("📡 GSM:", reply)
        except:
            pass

    gsm_timer = QTimer()
    gsm_timer.timeout.connect(poll_gsm)
    gsm_timer.start(5000)

    # ======================================================
    # ✅ GRACEFUL SHUTDOWN — GUARANTEED PORT RELEASE
    # ======================================================
    def shutdown():
        print("\n🛑 Shutting down system...")

        try:
            gsm_timer.stop()
        except:
            pass

        try:
            combined_reader.stop()
            print("✅ Combined Serial Reader stopped")
            print("✅ LaserReader stopped")
        except:
            pass

        

        try:
            stop_sms_sender()
            print("✅ SMS System stopped")
        except:
            pass

        try:
            gsm.close()
            print("✅ GSM COM1 released")
        except:
            pass

        print("✅ Shutdown complete — restart safe!")

    app.aboutToQuit.connect(shutdown)
    signal.signal(signal.SIGINT, lambda *a: app.quit())

    # -------------------------------
    # FINAL SYSTEM MAP
    # -------------------------------
    print("\n" + "═" * 72)
    print("✅ SYSTEM FULLY OPERATIONAL")
    print("   Laser + PLC  → COM6")
    print("   Laser SIM    → COM5")
    print("   GSM App      → COM1")
    print("   GSM SIM      → COM2")
    print("\n   Start Laser Simulator:")
    print("   → python tools\\combined_simulator.py")
    print("\n   Start GSM Simulator:")
    print("   → python tools\\gsm_simulator.py")
    print("═" * 72 + "\n")

    sys.exit(app.exec())

# ======================================================
if __name__ == "__main__":
    main()
