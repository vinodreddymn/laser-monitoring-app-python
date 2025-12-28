# ======================================================
# backend/gsm_modem.py
# GSM Modem Controller – A7670C SAFE
# ======================================================

import serial
import time
import logging
import json
from threading import Thread, Lock
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from config.app_config import (
    GSM_HEARTBEAT_INTERVAL,
    GSM_RECONNECT_DELAY,
    DEFAULT_BAUD_GSM,
    SERIAL_TIMEOUT,
)

log = logging.getLogger(__name__)

# ======================================================
# CONFIG
# ======================================================
CONFIG_FILE = Path(__file__).parent / "peripherals_config.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"gsm_port": "COM1"}

config = load_config()

GSM_PORT = config["gsm_port"]
GSM_BAUD = DEFAULT_BAUD_GSM


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
        self.port = GSM_PORT
        self.baud = GSM_BAUD

        self.ser = None
        self.lock = Lock()
        self.running = False
        self.worker = None

        self.is_connected = False
        modem_signals.modem_connected.emit(False)

    # --------------------------------------------------
    # BACKWARD-COMPATIBILITY
    # --------------------------------------------------
    def emit_current_status(self):
        modem_signals.modem_connected.emit(self.is_connected)
        modem_signals.signal_strength.emit(-1)

    # --------------------------------------------------
    def start(self):
        if self.running:
            return

        log.info("📡 Starting GSM modem (A7670C)")
        self.running = True

        self.worker = Thread(
            target=self._worker_loop,
            daemon=True,
            name="GSMWorker",
        )
        self.worker.start()

    # --------------------------------------------------
    def stop(self):
        self.running = False
        self._disconnect()

    # --------------------------------------------------
    def _connect(self):
        log.info("Connecting GSM modem on %s", self.port)
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            timeout=1,
            write_timeout=1,
        )
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    # --------------------------------------------------
    def _disconnect(self):
        self.is_connected = False
        modem_signals.modem_connected.emit(False)

        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

        self.ser = None
        log.warning("🔌 GSM modem disconnected")

    # --------------------------------------------------
    def _send(self, cmd: str):
        self.ser.write((cmd + "\r\n").encode())

    # --------------------------------------------------
    def _wait_ok(self, timeout=SERIAL_TIMEOUT) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line == "OK":
                    return True
            time.sleep(0.05)
        return False

    # --------------------------------------------------
    def _init_modem(self):
        """
        A7670C-safe initialization
        """
        cmds = [
            "ATE0",
            "AT+CMGF=1",
            'AT+CSCS="GSM"',
            "AT+CSMP=17,167,0,0",
        ]

        for cmd in cmds:
            self._send(cmd)
            self._wait_ok()
            time.sleep(0.2)

    # --------------------------------------------------
    def _check_alive(self) -> bool:
        self._send("AT")
        return self._wait_ok()

    # --------------------------------------------------
    def _worker_loop(self):
        while self.running:
            try:
                self._connect()

                if not self._check_alive():
                    raise RuntimeError("MODEM_NOT_RESPONDING")

                self._init_modem()
                self.is_connected = True
                modem_signals.modem_connected.emit(True)

                log.info("✅ GSM modem connected")

                last_heartbeat = time.time()

                while self.running and self.ser and self.ser.is_open:
                    if time.time() - last_heartbeat > GSM_HEARTBEAT_INTERVAL:
                        if not self._check_alive():
                            raise RuntimeError("HEARTBEAT_FAILED")
                        last_heartbeat = time.time()

                    time.sleep(0.2)

            except Exception as e:
                log.error("GSM error: %s", e)

            self._disconnect()
            time.sleep(GSM_RECONNECT_DELAY)

    # --------------------------------------------------
    # 🔥 SMS SEND – A7670C SAFE
    # --------------------------------------------------
    def send_sms(self, phone: str, message: str):
        if not self.is_connected or not self.ser:
            return False, "MODEM_DISCONNECTED"

        try:
            with self.lock:
                self.ser.reset_input_buffer()

                self._send("AT+CMGF=1")
                time.sleep(0.2)

                self._send(f'AT+CMGS="{phone}"')
                time.sleep(0.5)

                self.ser.write((message + "\x1A").encode())

            start = time.time()
            saw_error = False

            while time.time() - start < 25:  # A7670C needs more time
                if self.ser.in_waiting:
                    line = self.ser.readline().decode(errors="ignore").strip()
                    log.debug("SMS RESP: %s", line)

                    if "ERROR" in line:
                        return False, "SMS_FAILED"

                    if "+CMGS" in line or line == "OK":
                        return True, None

                time.sleep(0.05)

            # 🔥 A7670C BEHAVIOUR:
            # No ERROR = SMS WAS SENT
            log.warning(
                "SMS confirmation not received (A7670C), assuming sent"
            )
            return True, "SENT_NO_CONFIRM"

        except Exception as e:
            return False, str(e)


# ======================================================
# GLOBAL INSTANCE
# ======================================================
gsm = GSMModem()


def send_gsm_message(phone: str, message: str):
    ok, err = gsm.send_sms(phone, message)
    return {"success": ok, "error": err}
