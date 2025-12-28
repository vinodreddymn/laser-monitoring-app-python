# ======================================================
# QR Label Generator – 2" x 1" @ 300 DPI
#
# LABEL TEXT  : Part.<counter>
# DB qr_text  : Part.<counter>
# QR PAYLOAD  : JSON
#
# Example QR payload:
# {"id":"Part.1023","model":"Toyota Innova","type":"RHD","peak":76.44,"ts":"2025-12-22T22:31:14"}
#
# PNG METADATA:
#  - qr_text
#  - model_type
#  - peak_value
#  - timestamp
# ======================================================

import json
import logging
from pathlib import Path
from base64 import b64encode
from typing import Optional, Dict, Any
from datetime import datetime

import qrcode
from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

from backend.settings_dao import get_qr_settings, save_qr_settings
from backend.qr_codes_dao import save_qr_code, get_qr_code as dao_get_qr_code

# ======================================================
# LOGGING
# ======================================================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ======================================================
# PATHS
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent
QR_FOLDER = BASE_DIR / "qr_images"
VISUAL_SETTINGS_FILE = BASE_DIR / "backend" / "qr_generator.json"

BASE_DIR = Path(__file__).resolve().parents[1]
FONTS_DIR = BASE_DIR / "fonts"

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

TYPE_SIZE = 120
TYPE_RIGHT_MARGIN = 10
TYPE_VERTICAL_NUDGE = 3

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


def normalize_timestamp(ts: Optional[str] = None) -> str:
    """
    Ensures timestamp is in ISO format with seconds only (no microseconds).
    """
    if not ts:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        # fallback if format is unexpected
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    return dt.strftime("%Y-%m-%dT%H:%M:%S")



# ======================================================
# SETTINGS (DAO-BASED)
# ======================================================
def get_next_qr_text() -> str:
    """
    Returns next QR ID and safely increments counter.
    Format: <prefix>.<counter>
    """
    cfg = get_qr_settings()

    prefix = cfg.get("qr_text_prefix", "Part")
    counter = int(cfg.get("qr_start_counter", 1))

    qr_text = f"{prefix}.{counter}"

    save_qr_settings(
        prefix=prefix,
        counter=counter + 1,
        model_type=cfg.get("model_type", "RHD"),
    )

    return qr_text


def get_model_type() -> str:
    cfg = get_qr_settings()
    return cfg.get("model_type", "RHD")


# ======================================================
# MAIN GENERATOR
# ======================================================
def generate_and_save_qr_code(
    model_name: str,
    peak_value: float,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates QR label with:
    - Printed text = qr_text
    - DB qr_text   = qr_text
    - QR payload   = JSON
    """

    ensure_dirs()

    timestamp = normalize_timestamp(timestamp)


    visual = json.load(open(VISUAL_SETTINGS_FILE, "r", encoding="utf-8"))

    qr_text = get_next_qr_text()      # ID ONLY
    model_type = get_model_type()

    # --------------------------------------------------
    # QR PAYLOAD (JSON)
    # --------------------------------------------------
    qr_payload = json.dumps(
        {
            "id": qr_text,
            "type": model_type,
            "peak": round(float(peak_value), 2),
            "ts": timestamp,
        },
        separators=(",", ":")  # compact JSON
    )

    log.info("Generating QR %s | payload=%s", qr_text, qr_payload)

    filename = f"{qr_text}.png"
    rel_path = Path("qr_images") / filename
    abs_path = QR_FOLDER / filename

    # --------------------------------------------------
    # BASE CANVAS
    # --------------------------------------------------
    canvas = Image.new("RGB", (LABEL_W, LABEL_H), "white")
    draw = ImageDraw.Draw(canvas)

    # --------------------------------------------------
    # VERTICAL MODEL TYPE (RIGHT)
    # --------------------------------------------------
    type_font = load_font(TYPE_SIZE)

    dummy = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(dummy)
    bbox = d.textbbox((0, 0), model_type, font=type_font)

    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    pad = 40
    temp = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    td = ImageDraw.Draw(temp)
    td.text((pad, pad), model_type, fill="black", font=type_font)

    type_img = temp.rotate(-90, expand=True)

    type_x = LABEL_W - type_img.width - TYPE_RIGHT_MARGIN
    type_y = (LABEL_H - type_img.height) // 2 + TYPE_VERTICAL_NUDGE

    canvas.paste(type_img, (type_x, type_y), type_img)

    # --------------------------------------------------
    # CONTENT AREA
    # --------------------------------------------------
    CONTENT_RIGHT = type_x
    CONTENT_WIDTH = CONTENT_RIGHT

    # --------------------------------------------------
    # QR CODE (JSON PAYLOAD)
    # --------------------------------------------------
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color=visual.get("qr_fill_color", "black"),
        back_color="white",
    ).convert("RGB")

    qr_img = qr_img.resize((QR_SIZE, QR_SIZE), Image.LANCZOS)

    # --------------------------------------------------
    # LABEL TEXT (ID ONLY)
    # --------------------------------------------------
    text_font = load_font(TEXT_SIZE)
    bbox = draw.textbbox((0, 0), qr_text, font=text_font)
    text_w = bbox[2] - bbox[0]

    block_w = max(QR_SIZE, text_w)
    block_x = (CONTENT_WIDTH - block_w) // 2

    qr_x = block_x + (block_w - QR_SIZE) // 2
    qr_y = QR_TOP

    text_x = block_x + (block_w - text_w) // 2
    text_y = qr_y + QR_SIZE + TEXT_GAP

    canvas.paste(qr_img, (qr_x, qr_y))
    draw.text(
        (text_x, text_y),
        qr_text,
        fill=visual.get("text_color", "black"),
        font=text_font,
    )

    # --------------------------------------------------
    # PNG METADATA (FULL DETAILS)
    # --------------------------------------------------
    meta = PngInfo()
    meta.add_text("qr_text", qr_text)
    meta.add_text("model_name", model_name)
    meta.add_text("model_type", model_type)
    meta.add_text("peak_value", str(peak_value))
    meta.add_text("timestamp", timestamp)
    

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    canvas.save(
        abs_path,
        dpi=(DPI, DPI),
        pnginfo=meta,
        optimize=True,
    )

    qr_id = save_qr_code(str(rel_path), qr_text)

    log.info("QR label generated successfully: %s", qr_text)

    return {
        "id": qr_id,
        "text": qr_text,                 # DB + label
        "qr_payload": qr_payload,        # JSON (optional use)
        "model_name": model_name,
        "model_type": model_type,
        "peak_value": peak_value,
        "timestamp": timestamp,
        "filename": filename,
        "absolutePath": str(abs_path),
        "relativePath": str(rel_path),
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
