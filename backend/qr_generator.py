# ======================================================
# QR Label Generator – Industrial Grade
# Label: 2" x 1" @ 300 DPI
# ======================================================

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from base64 import b64encode
from typing import Union

import qrcode
from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

from backend.settings_dao import get_qr_settings, save_qr_settings
from backend.qr_codes_dao import save_qr_code, get_qr_code as dao_get_qr_code

# ======================================================
# LOGGING
# ======================================================
log = logging.getLogger(__name__)

# ======================================================
# PATHS
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent
QR_FOLDER = BASE_DIR / "qr_images"
FONTS_DIR = BASE_DIR / "fonts"
FONT_BOLD = FONTS_DIR / "Roboto-Bold.ttf"

# ======================================================
# LABEL SPECS
# ======================================================
DPI = 300
LABEL_W, LABEL_H = 600, 300

QR_SIZE = 230
QR_TOP = 18

TEXT_SIZE = 27
TEXT_GAP = 0

TYPE_SIZE = 120
TYPE_RIGHT_MARGIN = 10
TYPE_VERTICAL_NUDGE = 3

# ======================================================
# VISUAL SETTINGS
# ======================================================
VISUAL_SETTINGS_FILE = BASE_DIR / "config.json"
if VISUAL_SETTINGS_FILE.exists():
    with open(VISUAL_SETTINGS_FILE, "r") as f:
        VISUAL_SETTINGS = json.load(f).get("qr_visual", {})
else:
    VISUAL_SETTINGS = {}

# ======================================================
# HELPERS
# ======================================================
def ensure_dirs():
    QR_FOLDER.mkdir(parents=True, exist_ok=True)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(FONT_BOLD), size)
    except Exception:
        log.warning("Font missing, using default")
        return ImageFont.load_default()


def normalize_timestamp(ts: Optional[Union[str, datetime]]) -> str:
    """
    Normalize timestamp into ISO format (YYYY-MM-DDTHH:MM:SS)

    Accepts:
    - str (ISO or DB format)
    - datetime
    - None
    """

    if ts is None:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # ✅ Already datetime (DB / archive path)
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%dT%H:%M:%S")

    # ✅ String input (live / API path)
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")) \
                .strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass

    # ❌ Fallback (never crash printing)
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ======================================================
# QR TEXT MANAGEMENT (SAFE)
# ======================================================
def _get_next_qr_text() -> str:
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


def _get_model_type() -> str:
    return get_qr_settings().get("model_type", "RHD")


# ======================================================
# PUBLIC API – NEW PRODUCTION QR
# ======================================================
def generate_new_qr(
    model_name: str,
    peak_value: float,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a NEW QR (increments counter).
    """
    qr_text = _get_next_qr_text()
    model_type = _get_model_type()

    return _generate_qr_internal(
        qr_text=qr_text,
        model_name=model_name,
        model_type=model_type,
        peak_value=peak_value,
        timestamp=timestamp,
        persist=True,
    )


# ======================================================
# PUBLIC API – REPRINT / ARCHIVE QR
# ======================================================
def generate_qr_for_reprint(
    qr_text: str,
    model_name: str,
    model_type: str,
    peak_value: float,
    timestamp: Optional[str],
) -> Dict[str, Any]:
    """
    Generates QR image for an EXISTING QR TEXT.
    DOES NOT touch counters.
    """
    return _generate_qr_internal(
        qr_text=qr_text,
        model_name=model_name,
        model_type=model_type,
        peak_value=peak_value,
        timestamp=timestamp,
        persist=False,
    )


# ======================================================
# CORE RENDERER (PURE, SAFE)
# ======================================================
def _generate_qr_internal(
    *,
    qr_text: str,
    model_name: str,
    model_type: Optional[str],
    peak_value: float,
    timestamp: Optional[str],
    persist: bool,
) -> Dict[str, Any]:

    ensure_dirs()
    timestamp = normalize_timestamp(timestamp)

    # 🔒 HARD SAFETY (CRITICAL)
    model_type = model_type or "N/A"
    model_name = model_name or "UNKNOWN"
    qr_text = str(qr_text)

    qr_payload = json.dumps(
        {
            "id": qr_text,
            "type": model_type,
            "wd": round(float(peak_value), 2),
            "ts": timestamp,
        },
        separators=(",", ":"),
    )


    filename = f"{qr_text}.png"
    rel_path = Path("qr_images") / filename
    abs_path = QR_FOLDER / filename

    _render_qr_label(
        qr_text=qr_text,
        qr_payload=qr_payload,
        model_name=model_name,
        model_type=model_type,
        peak_value=peak_value,
        timestamp=timestamp,
        output_path=abs_path,
    )

    qr_id = None
    if persist:
        qr_id = save_qr_code(str(rel_path), qr_text)

    return {
        "id": qr_id,
        "qr_text": qr_text,
        "qr_payload": qr_payload,
        "model_name": model_name,
        "model_type": model_type,
        "peak_value": peak_value,
        "timestamp": timestamp,
        "absolutePath": str(abs_path),
        "relativePath": str(rel_path),
    }


# ======================================================
# LABEL RENDERER (NO DB, NO STATE)
# ======================================================
def _render_qr_label(
    *,
    qr_text: str,
    qr_payload: str,
    model_name: str,
    model_type: Optional[str],
    peak_value: float,
    timestamp: str,
    output_path: Path,
):

    model_type = model_type or "N/A"
    model_name = model_name or "UNKNOWN"


    canvas = Image.new("RGB", (LABEL_W, LABEL_H), "white")
    draw = ImageDraw.Draw(canvas)

    # ---------- Vertical Model Type ----------
    type_font = load_font(TYPE_SIZE)
    dummy = Image.new("RGB", (10, 10))
    bbox = ImageDraw.Draw(dummy).textbbox((0, 0), model_type, font=type_font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad = 40
    temp = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(temp).text((pad, pad), model_type, fill="black", font=type_font)
    type_img = temp.rotate(-90, expand=True)

    type_x = LABEL_W - type_img.width - TYPE_RIGHT_MARGIN
    type_y = (LABEL_H - type_img.height) // 2 + TYPE_VERTICAL_NUDGE
    canvas.paste(type_img, (type_x, type_y), type_img)

    # ---------- QR Code ----------
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color=VISUAL_SETTINGS.get("qr_fill_color", "black"),
        back_color="white",
    ).convert("RGB").resize((QR_SIZE, QR_SIZE), Image.LANCZOS)

    text_font = load_font(TEXT_SIZE)
    text_bbox = draw.textbbox((0, 0), qr_text, font=text_font)
    text_w = text_bbox[2] - text_bbox[0]

    block_w = max(QR_SIZE, text_w)
    content_w = type_x
    block_x = (content_w - block_w) // 2

    qr_x = block_x + (block_w - QR_SIZE) // 2
    qr_y = QR_TOP
    text_x = block_x + (block_w - text_w) // 2
    text_y = qr_y + QR_SIZE + TEXT_GAP

    canvas.paste(qr_img, (qr_x, qr_y))
    draw.text(
        (text_x, text_y),
        qr_text,
        fill=VISUAL_SETTINGS.get("text_color", "black"),
        font=text_font,
    )

    # ---------- Metadata ----------
    meta = PngInfo()
    meta.add_text("qr_text", qr_text)
    meta.add_text("model_name", model_name)
    meta.add_text("model_type", model_type)
    meta.add_text("peak_value", str(peak_value))
    meta.add_text("timestamp", timestamp)

    canvas.save(output_path, dpi=(DPI, DPI), pnginfo=meta, optimize=True)


# ======================================================
# FETCH QR (BASE64)
# ======================================================
def get_qr_code(qr_id: int) -> Optional[str]:
    meta = dao_get_qr_code(qr_id)
    if not meta:
        return None

    path = BASE_DIR / meta["filename"]
    if not path.exists():
        return None

    with open(path, "rb") as f:
        return "data:image/png;base64," + b64encode(f.read()).decode()
