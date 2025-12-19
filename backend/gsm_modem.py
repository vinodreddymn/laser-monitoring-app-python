# ======================================================
# backend/gsm_modem.py
# Production-Grade GSM Modem Controller (COMPATIBLE)
# ======================================================

import serial
import time
import logging
from threading import Thread, Lock
from queue import Queue, Empty

from PySide6.QtCore import QObject, Signal

# ======================================================
# CONFIG
# ======================================================
GSM_APP_PORT = "COM1"
GSM_BAUD = 115200

AT_TIMEOUT = 2.0
HEARTBEAT_INTERVAL = 5.0
RECONNECT_DELAY = 3.0
MAX_QUEUE_SIZE = 200

log = logging.getLogger(__name__)

# ======================================================
# MODEM SIGNALS (UI)
# ======================================================
class ModemSignals(QObject):
    modem_connected = Signal(bool)


modem_signals = ModemSignals()

# ======================================================
# GSM MODEM
# ======================================================
class GSMModem:
    def __init__(self):
        self.port = GSM_APP_PORT
        self.baud = GSM_BAUD

        self.ser = None
        self.lock = Lock()
        self.queue = Queue(maxsize=MAX_QUEUE_SIZE)

        self.running = False
        self.worker_thread = None

        self.is_connected = False
        self.last_heartbeat = 0.0

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------
    def start(self):
        if self.running:
            return

        log.info("Starting GSM modem worker")
        self.running = True

        self.worker_thread = Thread(
            target=self._worker,
            name="GSMWorker",
            daemon=True,
        )
        self.worker_thread.start()

    def stop(self):
        log.info("Stopping GSM modem worker")
        self.running = False

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=3.0)

        self._disconnect()
        log.info("GSM modem stopped")

    # --------------------------------------------------
    def _set_connected(self, state: bool):
        if self.is_connected != state:
            self.is_connected = state
            modem_signals.modem_connected.emit(state)

            log.info(
                "GSM modem %s",
                "CONNECTED" if state else "DISCONNECTED",
            )

    # --------------------------------------------------
    def _disconnect(self):
        self._set_connected(False)
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        self.ser = None

    # --------------------------------------------------
    def _open_port(self):
        log.info("Connecting to GSM modem on %s", self.port)
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            timeout=1,
            write_timeout=1,
        )
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    # --------------------------------------------------
    def _send_raw(self, cmd: str):
        with self.lock:
            if not self.ser:
                raise RuntimeError("SERIAL_NOT_OPEN")
            self.ser.write((cmd + "\r\n").encode())

    # --------------------------------------------------
    def _wait_for_ok(self, timeout=AT_TIMEOUT) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if not self.ser:
                return False
            if self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line == "OK":
                    return True
            time.sleep(0.05)
        return False

    # --------------------------------------------------
    def _check_alive(self) -> bool:
        try:
            self.ser.reset_input_buffer()
            self._send_raw("AT")
            return self._wait_for_ok()
        except Exception:
            return False

    # --------------------------------------------------
    def _init_modem(self):
        for cmd in [
            "ATE0",
            "AT+CMGF=1",
            'AT+CSCS="GSM"',
            "AT+CSMP=17,167,0,0",
            "AT+CNMI=2,1,0,0,0",
        ]:
            self._send_raw(cmd)
            self._wait_for_ok()
            time.sleep(0.2)

    # --------------------------------------------------
    def _worker(self):
        while self.running:
            try:
                self._open_port()

                if not self._check_alive():
                    raise RuntimeError("MODEM_NOT_RESPONDING")

                self._init_modem()
                self._set_connected(True)
                self.last_heartbeat = time.time()

                while self.running and self.ser and self.ser.is_open:
                    if self.ser.in_waiting:
                        line = self.ser.readline().decode(errors="ignore").strip()
                        if line:
                            try:
                                self.queue.put_nowait(line)
                            except:
                                pass

                    if time.time() - self.last_heartbeat >= HEARTBEAT_INTERVAL:
                        self.last_heartbeat = time.time()
                        if not self._check_alive():
                            raise RuntimeError("MODEM_NO_HEARTBEAT")

                    time.sleep(0.05)

            except Exception as e:
                log.warning("GSM worker error: %s", e)

            self._disconnect()
            time.sleep(RECONNECT_DELAY)

    # --------------------------------------------------
    def send_sms(self, phone: str, message: str):
        if not self.is_connected or not self.ser:
            return False, "MODEM_DISCONNECTED"

        try:
            with self.lock:
                self.ser.write(b"AT+CMGF=1\r\n")
                time.sleep(0.2)
                self.ser.write(f'AT+CMGS="{phone}"\r\n'.encode())
                time.sleep(0.4)
                self.ser.write((message + "\x1A").encode())

            start = time.time()
            while time.time() - start < 15:
                try:
                    line = self.queue.get_nowait()
                    if "+CMGS" in line:
                        return True, None
                    if "ERROR" in line:
                        return False, "SMS_FAILED"
                except Empty:
                    time.sleep(0.1)

            return False, "SMS_TIMEOUT"

        except Exception as e:
            return False, str(e)


# ======================================================
# GLOBAL INSTANCE + COMPATIBILITY WRAPPER
# ======================================================
gsm = GSMModem()

def send_gsm_message(phone: str, message: str):
    ok, error = gsm.send_sms(phone, message)
    return {"success": ok, "error": error}
