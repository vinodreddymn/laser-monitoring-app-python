import logging
import socket
import win32print
from backend.db import query
from backend.usb_printer_manager import usb_printer
from backend.gsm_modem import gsm

log = logging.getLogger(__name__)


def check_database():
    try:
        query("SELECT 1")
        log.info("DB check OK")
        return True
    except Exception as e:
        log.error("DB check FAILED: %s", e)
        return False


def check_printer():
    if usb_printer.is_connected:
        log.info("Printer ONLINE")
        return True
    log.warning("Printer OFFLINE at startup")
    return False


def check_gsm():
    try:
        gsm.start()
        log.info("GSM modem started")
        return True
    except Exception as e:
        log.error("GSM init failed: %s", e)
        return False


def run_startup_checks():
    log.info("Running startup self-checks")

    results = {
        "db": check_database(),
        "printer": check_printer(),
        "gsm": check_gsm()
    }

    return results
