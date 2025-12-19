# ======================================================
# QR Label Generator – 2" x 1" @ 300 DPI
# Final layout:
#   [ centered QR + text ] | [ fixed vertical RHD ]
# ======================================================

import json
import logging
from pathlib import Path
from base64 import b64encode
from typing import Optional, Dict, Any

import qrcode
from PIL import Image, ImageDraw, ImageFont

from .qr_codes_dao import save_qr_code, get_qr_code as dao_get_qr_code

# ======================================================
# LOGGING
# ======================================================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ======================================================
# PATHS
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SETTINGS_FILE = BASE_DIR / "settings.json"
VISUAL_SETTINGS_FILE = BASE_DIR / "backend" / "qr_generator.json"
QR_FOLDER = BASE_DIR / "qr_images"

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONT_BOLD = FONTS_DIR / "Roboto-Bold.ttf"

# ======================================================
# LABEL SIZE – 2" x 1" @ 300 DPI
# ======================================================
DPI = 300
LABEL_W = 600
LABEL_H = 300

# ======================================================
# CONTENT SIZES
# ======================================================
QR_SIZE = 230
QR_TOP = 18

TEXT_SIZE = 27
TEXT_GAP = 0

RHD_TEXT = "LHD"       # common for now
RHD_SIZE = 120
RHD_RIGHT_MARGIN = 10
RHD_VERTICAL_NUDGE = 6

# ======================================================
# HELPERS
# ======================================================
def ensure_dirs():
    QR_FOLDER.mkdir(parents=True, exist_ok=True)

def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(FONT_BOLD), size)
    except Exception:
        log.warning("Roboto-Bold.ttf not found, using default font")
        return ImageFont.load_default()

# ======================================================
# SETTINGS / AUTO COUNTER
# ======================================================
def load_settings() -> Dict[str, Any]:
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data: Dict[str, Any]):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_next_qr_text() -> str:
    cfg = load_settings()
    text = f"{cfg['qr_text_prefix']}.{cfg['qr_start_counter']}"
    cfg["qr_start_counter"] += 1
    save_settings(cfg)
    return text

# ======================================================
# MAIN GENERATOR
# ======================================================
def generate_and_save_qr_code() -> Dict[str, Any]:
    ensure_dirs()

    visual = json.load(open(VISUAL_SETTINGS_FILE, "r"))
    qr_text = get_next_qr_text()

    filename = f"{qr_text}.png"
    rel_path = Path("qr_images") / filename
    abs_path = QR_FOLDER / filename

    # --------------------------------------------------
    # BASE CANVAS
    # --------------------------------------------------
    canvas = Image.new("RGB", (LABEL_W, LABEL_H), "white")
    draw = ImageDraw.Draw(canvas)

    # --------------------------------------------------
    # BUILD RHD FIRST (LOCK RIGHT)
    # --------------------------------------------------
    rhd_font = load_font(RHD_SIZE)

    dummy = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(dummy)
    rhd_bbox = d.textbbox((0, 0), RHD_TEXT, font=rhd_font)

    rhd_w = rhd_bbox[2] - rhd_bbox[0]
    rhd_h = rhd_bbox[3] - rhd_bbox[1]

    PADDING = 40
    rhd_temp = Image.new(
        "RGBA",
        (rhd_w + PADDING * 2, rhd_h + PADDING * 2),
        (0, 0, 0, 0)
    )

    td = ImageDraw.Draw(rhd_temp)
    td.text((PADDING, PADDING), RHD_TEXT, fill="black", font=rhd_font)

    rhd_img = rhd_temp.rotate(-90, expand=True)

    rhd_x = LABEL_W - rhd_img.width - RHD_RIGHT_MARGIN
    rhd_y = (LABEL_H - rhd_img.height) // 2 + RHD_VERTICAL_NUDGE

    canvas.paste(rhd_img, (rhd_x, rhd_y), rhd_img)

    # --------------------------------------------------
    # DEFINE CONTENT AREA (LEFT OF RHD)
    # --------------------------------------------------
    CONTENT_LEFT = 0
    CONTENT_RIGHT = rhd_x
    CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT

    # --------------------------------------------------
    # QR CODE
    # --------------------------------------------------
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color=visual.get("qr_fill_color", "black"),
        back_color="white"
    ).convert("RGB")

    qr_img = qr_img.resize((QR_SIZE, QR_SIZE), Image.LANCZOS)

    # --------------------------------------------------
    # TEXT MEASUREMENT
    # --------------------------------------------------
    text_font = load_font(TEXT_SIZE)
    text_bbox = draw.textbbox((0, 0), qr_text, font=text_font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    # --------------------------------------------------
    # QR + TEXT BLOCK SIZE
    # --------------------------------------------------
    BLOCK_WIDTH = max(QR_SIZE, text_w)
    BLOCK_HEIGHT = QR_SIZE + TEXT_GAP + text_h

    # --------------------------------------------------
    # CENTER BLOCK IN REMAINING SPACE
    # --------------------------------------------------
    block_x = CONTENT_LEFT + (CONTENT_WIDTH - BLOCK_WIDTH) // 2

    qr_x = block_x + (BLOCK_WIDTH - QR_SIZE) // 2
    qr_y = QR_TOP

    text_x = block_x + (BLOCK_WIDTH - text_w) // 2
    text_y = qr_y + QR_SIZE + TEXT_GAP

    canvas.paste(qr_img, (qr_x, qr_y))
    draw.text(
        (text_x, text_y),
        qr_text,
        fill=visual.get("text_color", "black"),
        font=text_font
    )

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    canvas.save(abs_path, dpi=(DPI, DPI), optimize=True)

    qr_id = save_qr_code(str(rel_path), qr_text)
    log.info(f"QR label generated: {qr_text}")

    return {
        "id": qr_id,
        "text": qr_text,
        "filename": filename,
        "absolutePath": str(abs_path),
        "relativePath": str(rel_path)
    }

# ======================================================
# FETCH QR (BASE64)
# ======================================================
def get_qr_code(qr_id: int) -> Optional[str]:
    meta = dao_get_qr_code(qr_id)
    if not meta:
        return None

    file_path = BASE_DIR / meta["filename"]
    if not file_path.exists():
        return None

    with open(file_path, "rb") as f:
        return "data:image/png;base64," + b64encode(f.read()).decode()
