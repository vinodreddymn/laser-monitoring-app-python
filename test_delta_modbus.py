import serial
import time

def calculate_lrc(data_bytes):
    total = sum(data_bytes)
    lrc = (-total) & 0xFF
    return f'{lrc:02X}'.upper()

# Configuration
PORT = 'COM4'
BAUDRATE = 9600
SLAVE_ADDR = '01'
START_ADDR = '1000'
NUM_REGS = '0001'

ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=serial.SEVENBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=1.0
)

try:
    print("Monitoring D0... Press Ctrl+C to stop")
    while True:
        # Build & send request (same as before)
        message = SLAVE_ADDR + '03' + START_ADDR + NUM_REGS
        msg_bytes = bytes.fromhex(message)
        lrc = calculate_lrc(msg_bytes)
        frame = ':' + message + lrc + '\r\n'
        ser.write(frame.encode('ascii'))

        raw = ser.read(50)
        if raw:
            try:
                text = raw.decode('ascii').rstrip('\r\n')
                if text.startswith(':') and len(text) >= 11:
                    content = text[1:]
                    if content[2:4] == '03' and content[4:6] == '02':
                        value_hex = content[6:10]
                        value = int(value_hex, 16)
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] D0 = {value:5d}  (hex: {value_hex})")
            except:
                pass  # ignore bad frames

        time.sleep(0.1)  # poll every 0.5 seconds – adjust as needed

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    ser.close()