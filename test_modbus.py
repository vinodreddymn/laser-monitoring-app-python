import serial
import time

def calculate_lrc(data_bytes):
    total = sum(data_bytes)
    lrc = (-total) & 0xFF
    return f'{lrc:02X}'.upper()

PORT = 'COM7'
BAUDRATE = 9600
SLAVE_ADDR = '01'
START_ADDR = '1001'  # D1; change to '1000' for D0
NUM_REGS = '0001'

ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=serial.SEVENBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=1.0
)

print(f"Polling {PORT} @ {BAUDRATE} 7E1 – Reading D{int(START_ADDR,16)-4096} (addr 0x{START_ADDR})")
print("Press Ctrl+C to stop\n")

def send_and_read():
    message = SLAVE_ADDR + '03' + START_ADDR + NUM_REGS
    msg_bytes = bytes.fromhex(message)
    lrc = calculate_lrc(msg_bytes)
    frame = ':' + message + lrc + '\r\n'

    ser.reset_input_buffer()
    ser.write(frame.encode('ascii'))
    ser.flush()

    raw = ser.read(60)
    ts = time.strftime("%H:%M:%S")

    if not raw:
        print(f"[{ts}] No bytes received")
        return None

    hex_str = raw.hex().upper()
    try:
        text = raw.decode('ascii').rstrip('\r\n')
        print(f"[{ts}] Raw: {hex_str} → '{text}'")
    except:
        print(f"[{ts}] Raw (decode failed): {hex_str}")
        return None

    if not text.startswith(':') or '\r\n' not in text:
        print(f"[{ts}] No complete ASCII frame")
        return None

    # Process first complete frame
    frame_text = text.split('\r\n')[0]
    content = frame_text[1:]

    if len(content) < 8:
        print(f"[{ts}] Frame too short")
        return None

    recv_lrc = content[-2:]
    calc_lrc = calculate_lrc(bytes.fromhex(content[:-2]))

    if recv_lrc.upper() != calc_lrc:
        print(f"[{ts}] LRC error: recv {recv_lrc}, calc {calc_lrc}")
        return None

    if content[0:2] != SLAVE_ADDR:
        print(f"[{ts}] Wrong slave addr: {content[0:2]}")
        return None

    if content[2:4] == '03' and content[4:6] == '02':
        value_hex = content[6:10]
        value = int(value_hex, 16)
        print(f"[{ts}] SUCCESS! D{int(START_ADDR,16)-4096} = {value} (hex {value_hex})")
        return value
    else:
        print(f"[{ts}] Unsolicited / wrong type: func {content[2:4]}, count {content[4:6]}")
        return None

try:
    while True:
        value = None
        for attempt in range(3):  # retry up to 3 times
            value = send_and_read()
            if value is not None:
                break
            time.sleep(0.1)  # small delay between retries

        if value is None:
            print(f"[{time.strftime('%H:%M:%S')}] Failed after retries – check wiring/ISPSoft settings")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    ser.close()
    print("Port closed")