# ======================================================
# backend/gsm_modem.py
# GSM Modem Controller – SIM7670 / A7670
# CP2102 USB–RS232 (WINDOWS SAFE)
# ======================================================

import time
import logging
import serial
import serial.tools.list_ports

from threading import Thread, Lock
from PySide6.QtCore import QObject, Signal

from config.app_config import (
    GSM_HEARTBEAT_INTERVAL,
    GSM_RECONNECT_DELAY,
    DEFAULT_GSM_PORT,
    DEFAULT_BAUD_GSM,
)

log = logging.getLogger(__name__)

# ======================================================
# UI SIGNALS
# ======================================================
class ModemSignals(QObject):
    modem_connected = Signal(bool)
    signal_strength = Signal(int)


modem_signals = ModemSignals()

# ======================================================
# GSM MODEM
# ======================================================
class GSMModem:
    def __init__(self):
        self.port = DEFAULT_GSM_PORT
        self.baud = DEFAULT_BAUD_GSM

        self.ser: serial.Serial | None = None
        self.lock = Lock()

        self.running = False
        self.stopping = False
        self.worker: Thread | None = None

        self.is_connected = False
        modem_signals.modem_connected.emit(False)

    # --------------------------------------------------
    def emit_current_status(self):
        modem_signals.modem_connected.emit(self.is_connected)
        modem_signals.signal_strength.emit(-1)

    # --------------------------------------------------
    def start(self):
        if self.running:
            return

        log.info("📡 Starting GSM modem worker (CP2102 / Windows-safe)")
        self.running = True
        self.stopping = False

        self.worker = Thread(
            target=self._worker_loop,
            daemon=True,
            name="GSMWorker",
        )
        self.worker.start()

    def stop(self):
        log.info("🛑 Stopping GSM modem worker")
        self.stopping = True
        self.running = False

        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=5)

        self._disconnect()

    # --------------------------------------------------
    # SERIAL
    # --------------------------------------------------
    def _wait_for_port(self):
        while self.running and not self.stopping:
            ports = [p.device for p in serial.tools.list_ports.comports()]
            if self.port in ports:
                return
            log.info("⌛ Waiting for GSM modem USB (%s)...", self.port)
            time.sleep(1)

    def _connect(self):
        log.info("🔌 Connecting GSM modem on %s", self.port)

        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            timeout=1,
            write_timeout=1,
        )

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def _disconnect(self):
        if not self.ser:
            return

        self.is_connected = False
        modem_signals.modem_connected.emit(False)

        try:
            self.ser.close()
        except Exception:
            pass

        self.ser = None
        log.warning("🔌 GSM modem disconnected & released")

    # --------------------------------------------------
    # IO
    # --------------------------------------------------
    def _send(self, cmd: str):
        if self.stopping:
            raise RuntimeError("SHUTTING_DOWN")

        if not self.ser or not self.ser.is_open:
            raise serial.SerialException("SERIAL_NOT_OPEN")

        self.ser.write((cmd + "\r\n").encode())
        self.ser.flush()

    # --------------------------------------------------
    # MODEM OPS
    # --------------------------------------------------
    def _toggle_dtr(self):
        try:
            log.info("🔁 Toggling DTR to wake modem")
            self.ser.dtr = False
            time.sleep(0.4)
            self.ser.dtr = True
            time.sleep(0.4)
        except Exception as e:
            log.warning("DTR toggle failed: %s", e)

    def _wake_modem(self) -> bool:
        for _ in range(6):
            try:
                self._send("AT")
                return True
            except Exception:
                time.sleep(0.5)
        return False

    def _init_modem(self):
        cmds = [
            "ATE0",
            "AT+CMGF=1",
            'AT+CSCS="GSM"',
            "AT+CSMP=17,167,0,0",
        ]

        for cmd in cmds:
            self._send(cmd)
            time.sleep(0.3)

    # --------------------------------------------------
    # WORKER
    # --------------------------------------------------
    def _worker_loop(self):
        while self.running and not self.stopping:
            try:
                self._wait_for_port()
                if self.stopping:
                    break

                self._connect()
                self._toggle_dtr()
                time.sleep(2)

                if not self._wake_modem():
                    raise RuntimeError("MODEM_NOT_RESPONDING")

                self._init_modem()

                self.is_connected = True
                modem_signals.modem_connected.emit(True)
                log.info("✅ GSM modem connected")

                last_heartbeat = time.time()

                while self.running and not self.stopping:
                    if time.time() - last_heartbeat >= GSM_HEARTBEAT_INTERVAL:
                        self._send("AT")  # write-only heartbeat
                        last_heartbeat = time.time()
                    time.sleep(0.3)

            except Exception as e:
                if self.stopping:
                    log.info("🧹 GSM worker stopped cleanly")
                else:
                    log.error("❌ GSM error: %s", e)

            self._disconnect()
            time.sleep(GSM_RECONNECT_DELAY)

    # --------------------------------------------------
    # SMS
    # --------------------------------------------------
    def send_sms(self, phone: str, message: str):
        if not self.is_connected or not self.ser:
            return False, "MODEM_DISCONNECTED"

        try:
            with self.lock:
                self._send("AT+CMGF=1")
                time.sleep(0.3)

                self._send(f'AT+CMGS="{phone}"')
                time.sleep(0.6)

                self.ser.write((message + "\x1A").encode())
                self.ser.flush()

            start = time.time()

            while time.time() - start < 25:
                try:
                    line = self.ser.readline().decode(errors="ignore").strip()
                except Exception:
                    break

                if "ERROR" in line:
                    return False, "SMS_FAILED"

                if "+CMGS" in line:
                    return True, None

                time.sleep(0.05)

            return True, "SENT_NO_CONFIRM"

        except Exception as e:
            log.error("❌ SMS send failed: %s", e)
            return False, str(e)


# ======================================================
# GLOBAL
# ======================================================
gsm = GSMModem()


def send_gsm_message(phone: str, message: str):
    ok, err = gsm.send_sms(phone, message)
    return {"success": ok, "error": err}
