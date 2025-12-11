# gsm_simulator.py
import serial
import time
import threading
import random

# Python simulator connects to COM2 (VSPE pair: COM2 ↔ COM1)
ser = serial.Serial(
    port="COM2",
    baudrate=115200,
    timeout=1,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

print("GSM Simulator running on COM2 → connected to Electron on COM1")
print("Send 'STATUS?' or 'SENDSMS:number:message'")

operators = ["Airtel", "Jio", "Vodafone-Idea", "BSNL", "Aircel"]

def generate_status():
    signal = random.randint(35, 99)
    network = random.choice(operators)
    return f"STATUS:READY,SIGNAL={signal},NETWORK={network}\r\n"

def read_loop():
    while True:
        try:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                print(f"Received: {line}")

                # STATUS request → return random operator + signal
                if line == "STATUS?":
                    status_msg = generate_status()
                    ser.write(status_msg.encode())
                    print("Sent:", status_msg.strip())

                # SEND SMS
                elif line.startswith("SENDSMS:"):
                    parts = line.split(":", 2)
                    if len(parts) == 3:
                        number, message = parts[1], parts[2]
                        print(f"Sending SMS to {number}: {message}")
                        time.sleep(1)
                        ser.write(b"SMS:SENT\r\n")
                    else:
                        ser.write(b"ERROR:INVALID_FORMAT\r\n")

                else:
                    ser.write(b"OK\r\n")

        except Exception as e:
            print("Error:", e)
            break

# Run listener thread
threading.Thread(target=read_loop, daemon=True).start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nGSM Simulator stopped")
    ser.close()
