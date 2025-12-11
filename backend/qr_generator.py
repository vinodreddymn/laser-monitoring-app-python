import os
import json
import qrcode
from base64 import b64encode
from PIL import Image, ImageDraw, ImageFont

from .qr_codes_dao import save_qr_code, get_qr_code as dao_get_qr_code
from .settings_dao import get_settings, save_settings


# ===========================
# PATH CONFIG
# ===========================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
QR_FOLDER = os.path.join(BASE_DIR, 'qr_images')
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Roboto-Bold.ttf")


# ===========================
# SETTINGS HANDLING
# ===========================

def default_settings():
    return {
        "qr_text_prefix": "qr",
        "qr_start_counter": 1
    }


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        settings = default_settings()
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return settings

    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)


def save_settings_local(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def build_qr_name_from_settings():
    settings = load_settings()

    prefix = settings.get('qr_text_prefix', 'qr')
    counter = int(settings.get('qr_start_counter', 1))

    name = f"{prefix}-{counter}"

    settings['qr_start_counter'] = counter + 1
    save_settings_local(settings)

    return name


# ===========================
# FILE SYSTEM
# ===========================

def ensure_folder():
    os.makedirs(QR_FOLDER, exist_ok=True)


# ===========================
# TEXT WRAPPING & CENTERING
# ===========================

def draw_wrapped_text(draw, text, center_x, start_y, font, max_width, line_spacing=6):
    """
    Draws wrapped, center-aligned text starting from a Y position.
    """

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]

        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    _, _, _, line_height = draw.textbbox((0, 0), "Ay", font=font)

    y = start_y

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = center_x - (text_width // 2)

        draw.text((x, y), line, fill="black", font=font)
        y += line_height + line_spacing

    return y


# ===========================
# QR CODE GENERATION
# ===========================

def generate_and_save_qr_code():
    ensure_folder()

    qr_name = build_qr_name_from_settings()
    filename = f"{qr_name}.png"
    rel_path = os.path.join("qr_images", filename)
    abs_path = os.path.join(QR_FOLDER, filename)

    # --- QR ENGINE ---
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2
    )
    qr.add_data(qr_name)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # --- CANVAS SETUP ---
    canvas_width = 500
    canvas_height = 600
    qr_size = 420

    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    # --- QR POSITION ---
    qr_x = (canvas_width - qr_size) // 2
    qr_y = 30
    qr_resized = qr_img.resize((qr_size, qr_size))

    canvas.paste(qr_resized, (qr_x, qr_y))

    # --- LOAD FONT ---
    try:
        font = ImageFont.truetype(FONT_PATH, 30)
        sub_font = ImageFont.truetype(FONT_PATH, 18)
    except:
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # --- DRAW MAIN TEXT (CENTERED BELOW QR) ---
    center_x = canvas_width // 2
    text_start_y = qr_y + qr_size + 20

    final_y = draw_wrapped_text(
        draw=draw,
        text=qr_name,
        center_x=center_x,
        start_y=text_start_y,
        font=font,
        max_width=qr_size
    )

    # --- SUBTITLE ---
    subtitle = "Scan QR or read code above"
    sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sub_width = sub_bbox[2] - sub_bbox[0]

    draw.text(
        ((canvas_width - sub_width) // 2, final_y + 10),
        subtitle,
        fill="#666",
        font=sub_font
    )

    # --- SAVE FILE ---
    canvas.save(abs_path)

    qr_id = save_qr_code(rel_path, qr_name)

    return {
        "id": qr_id,
        "filename": filename,
        "text": qr_name,
        "relativePath": rel_path,
        "absolutePath": abs_path
    }


# ===========================
# GET QR AS BASE64
# ===========================

def get_qr_code(qr_id):
    meta = dao_get_qr_code(qr_id)

    if not meta or not meta.get('filename'):
        return None

    filename = meta['filename']

    abs_path = filename if os.path.isabs(filename) else os.path.join(BASE_DIR, filename)

    if not os.path.exists(abs_path):
        return None

    with open(abs_path, 'rb') as f:
        return f"data:image/png;base64,{b64encode(f.read()).decode('utf-8')}"
