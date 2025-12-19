import serial
import time

PORT = "COM2"
BAUD = 115200

CTRL_Z = b"\x1A"


def log(rx_tx, msg):
    print(f"[{rx_tx}] {msg}")


def main():
    print(f"🧪 SIM7670A SIMULATOR STARTED on {PORT}")

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

            # -------------------------------
            # SMS MODE (RAW)
            # -------------------------------
            if sms_mode:
                if CTRL_Z in buffer:
                    msg, buffer = buffer.split(CTRL_Z, 1)
                    sms_text += msg

                    log("SMS", sms_text.decode(errors="ignore"))

                    time.sleep(1)
                    ser.write(b"\r\n+CMGS: 45\r\nOK\r\n")

                    sms_mode = False
                    sms_text = b""

                else:
                    sms_text += buffer
                    buffer = b""

                continue

            # -------------------------------
            # COMMAND MODE (LINE-BASED)
            # -------------------------------
            while b"\r\n" in buffer:
                line, buffer = buffer.split(b"\r\n", 1)
                line = line.strip()

                if not line:
                    continue

                cmd = line.decode(errors="ignore")
                log("RX", cmd)

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

                elif cmd.startswith("AT+CMGS"):
                    sms_mode = True
                    sms_text = b""
                    time.sleep(0.3)
                    ser.write(b"> ")

                else:
                    ser.write(b"ERROR\r\n")

                log("TX", "response sent")

        time.sleep(0.02)


if __name__ == "__main__":
    main()
