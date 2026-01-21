from pymodbus.client.sync import ModbusSerialClient
import time

# -------------------------------
# Modbus RTU Master Configuration
# -------------------------------
client = ModbusSerialClient(
    method='rtu',
    port='COM11',          # Virtual COM (Master side)
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

# -------------------------------
# Connect to Modbus Slave
# -------------------------------
if not client.connect():
    print("❌ Unable to connect to COM11")
    exit(1)

print("✅ Modbus RTU Master connected on COM11")

SLAVE_ID = 1

try:
    while True:
        # Read Holding Register
        # D100 -> 40001 -> address 0 (0-based)
        result = client.read_holding_registers(
            address=0,
            count=1,
            unit=SLAVE_ID
        )

        if result.isError():
            print("❌ Modbus error:", result)
        else:
            laser_distance = result.registers[0]
            print(f"Laser Distance = {laser_distance} mm")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopping Modbus polling...")

finally:
    client.close()
