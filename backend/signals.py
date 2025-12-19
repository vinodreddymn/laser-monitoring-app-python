# signals.py
from PySide6.QtCore import QObject, Signal

class Signals(QObject):
    laser_value = Signal(float)          # replaces liveData / laserValue
    cycle_detected = Signal(dict)        # replaces onCycleDetected
    sms_sent = Signal(dict)              # replaces onSMSSent
    plc_status = Signal(dict)            # replaces onPLCStatus
    qr_print = Signal(dict)              # if you still need it

# Global instance (import anywhere)
signals = Signals()