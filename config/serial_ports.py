# config/serial_ports.py

# ===== VIRTUAL SERIAL PAIRS =====
# Laser + PLC Simulator
SIMULATOR_WRITE_PORT = "COM5"   # Simulator writes here
APP_READ_PORT        = "COM6"   # Python app reads here

# GSM Simulator
GSM_SIMULATOR_PORT = "COM2"     # GSM simulator runs here
GSM_APP_PORT       = "COM1"     # Python app GSM modem connects here

# ===== BAUD RATES =====
LASER_BAUD = 9600
PLC_BAUD   = 9600
GSM_BAUD   = 115200
