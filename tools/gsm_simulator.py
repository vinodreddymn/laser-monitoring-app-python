import serial
import time
import random

PORT = "COM2"
BAUD = 115200
CTRL_Z = b"\x1A"


def log(rx_tx, msg):
    print(f"[{rx_tx}] {msg}")


def random_signal():
    """
    Simulate realistic GSM RSSI values
    """
    # Mostly usable signal, sometimes weak, rarely unknown
    choice = random.random()

    if choice < 0.05:
        return 99          # unknown
    elif choice < 0.15:
        return random.randint(5, 9)     # weak
    elif choice < 0.85:
        return random.randint(10, 25)   # normal-good
    else:
        return random.randint(26, 31)   # excellent


def main():
    print(f"🧪 A7670C GSM SIMULATOR STARTED on {PORT}")

    ser = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        timeout=0.1
    )

    buffer = b""
    sms_mode = False
    sms_text = b""

    while True:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            buffer += data

            # ==================================================
            # SMS MODE (RAW TEXT UNTIL CTRL+Z)
            # ==================================================
            if sms_mode:
                if CTRL_Z in buffer:
                    msg, buffer = buffer.split(CTRL_Z, 1)
                    sms_text += msg

                    log("SMS", sms_text.decode(errors="ignore"))

                    time.sleep(random.uniform(0.5, 2.5))

                    behavior = random.choice([
                        "CMGS_OK",
                        "OK_ONLY",
                        "DELAYED_CMGS",
                    ])

                    if behavior == "CMGS_OK":
                        ser.write(b"\r\n+CMGS: 45\r\nOK\r\n")

                    elif behavior == "OK_ONLY":
                        ser.write(b"\r\nOK\r\n")

                    elif behavior == "DELAYED_CMGS":
                        ser.write(b"\r\nOK\r\n")
                        time.sleep(2.5)
                        ser.write(b"\r\n+CMGS: 45\r\n")

                    log("TX", f"SMS response ({behavior})")

                    sms_mode = False
                    sms_text = b""

                else:
                    sms_text += buffer
                    buffer = b""

                continue

            # ==================================================
            # COMMAND MODE (LINE BASED)
            # ==================================================
            while b"\r\n" in buffer:
                line, buffer = buffer.split(b"\r\n", 1)
                line = line.strip()

                if not line:
                    continue

                cmd = line.decode(errors="ignore")
                log("RX", cmd)

                # ------------------------------
                # BASIC AT COMMANDS
                # ------------------------------
                if cmd == "AT":
                    ser.write(b"OK\r\n")

                elif cmd == "ATE0":
                    ser.write(b"OK\r\n")

                elif cmd.startswith("AT+CMGF"):
                    ser.write(b"OK\r\n")

                elif cmd.startswith("AT+CSCS"):
                    ser.write(b"OK\r\n")

                elif cmd.startswith("AT+CSMP"):
                    ser.write(b"OK\r\n")

                elif cmd.startswith("AT+CNMI"):
                    ser.write(b"OK\r\n")

                # ------------------------------
                # SIGNAL STRENGTH (CSQ)
                # ------------------------------
                elif cmd == "AT+CSQ":
                    rssi = random_signal()
                    ber = random.randint(0, 3)
                    ser.write(
                        f"\r\n+CSQ: {rssi},{ber}\r\nOK\r\n".encode()
                    )
                    log("TX", f"+CSQ: {rssi},{ber}")

                # ------------------------------
                # SEND SMS
                # ------------------------------
                elif cmd.startswith("AT+CMGS"):
                    sms_mode = True
                    sms_text = b""
                    time.sleep(0.2)
                    ser.write(b"> ")

                # ------------------------------
                # UNKNOWN COMMAND
                # ------------------------------
                else:
                    ser.write(b"ERROR\r\n")

                log("TX", "response sent")

        time.sleep(0.02)


if __name__ == "__main__":
    main()
