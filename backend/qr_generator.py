# backend/qr_generator.py

import json
import qrcode
import logging
from datetime import datetime
from base64 import b64encode
from pathlib import Path
from typing import Optional, Dict, Any

from PIL import Image, ImageDraw, ImageFont

from .qr_codes_dao import save_qr_code, get_qr_code as dao_get_qr_code

# ======================================================
# Logging & Paths
# ======================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

ROOT_SETTINGS_FILE = BASE_DIR / "settings.json"
VISUAL_SETTINGS_FILE = BASE_DIR / "backend" / "qr_generator.json"

QR_FOLDER = BASE_DIR / "qr_images"

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONT_BOLD_PATH = FONTS_DIR / "roboto-bold.ttf"
FONT_REGULAR_PATH = FONTS_DIR / "roboto-regular.ttf"

# ======================================================
# LABEL DIMENSIONS (60mm x 30mm @ 300 DPI)
# ======================================================
DPI = 300
MM_TO_PX = DPI / 25.4
LABEL_WIDTH = int(60 * MM_TO_PX)
LABEL_HEIGHT = int(30 * MM_TO_PX)

# ======================================================
# SETTINGS LOADING
# ======================================================
def load_root_settings() -> Dict[str, Any]:
    if not ROOT_SETTINGS_FILE.exists():
        raise FileNotFoundError(f"Root settings missing: {ROOT_SETTINGS_FILE}")
    try:
        with open(ROOT_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        if "qr_text_prefix" not in settings or "qr_start_counter" not in settings:
            raise ValueError("settings.json missing qr_text_prefix or qr_start_counter")
        return settings
    except Exception as e:
        logger.error(f"Root settings error: {e}")
        raise

def save_root_settings(settings: Dict[str, Any]):
    try:
        with open(ROOT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save root settings: {e}")
        raise

def load_visual_settings() -> Dict[str, Any]:
    if not VISUAL_SETTINGS_FILE.exists():
        raise FileNotFoundError(f"Visual settings missing: {VISUAL_SETTINGS_FILE}")
    try:
        with open(VISUAL_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Visual settings error: {e}")
        raise

# ======================================================
# QR NAME GENERATION
# ======================================================
def get_next_qr_name() -> str:
    settings = load_root_settings()
    prefix = settings["qr_text_prefix"]  # Exact user input preserved
    counter = settings["qr_start_counter"]
    qr_name = f"{prefix}-{counter:04d}"
    settings["qr_start_counter"] = counter + 1
    save_root_settings(settings)
    return qr_name

def ensure_folder():
    QR_FOLDER.mkdir(parents=True, exist_ok=True)

def load_font(path: Path, size: int):
    try:
        return ImageFont.truetype(str(path), size)
    except IOError as e:
        logger.error(f"Font error: {path} → {e}")
        raise

# ======================================================
# SMART WRAPPING: Break only at _ - or space
# ======================================================
def wrap_text_at_special_chars(draw: ImageDraw.Draw, text: str, max_width: float, font) -> list[str]:
    """
    Split text into segments separated by space, underscore, or hyphen.
    Each segment (word between separators) is kept intact.
    Lines are built by adding whole segments until width exceeded.
    Separators are preserved in display.
    """
    if not text:
        return [""]

    # Define break characters (including space)
    break_chars = {' ', '_', '-'}

    # Split text into tokens: (segment, separator)
    segments = []
    current_segment = ""
    for char in text:
        if char in break_chars:
            if current_segment:
                segments.append((current_segment, char))
                current_segment = ""
            else:
                # Multiple separators in a row — treat as one
                if segments:
                    prev_seg, prev_sep = segments[-1]
                    segments[-1] = (prev_seg, prev_sep + char)
                else:
                    segments.append(("", char))
        else:
            current_segment += char
    if current_segment:
        segments.append((current_segment, ""))

    # Build lines
    lines = []
    current_line_tokens = []

    for segment, separator in segments:
        test_tokens = current_line_tokens + [(segment, separator)]
        test_text = "".join(seg + sep for seg, sep in test_tokens)

        if draw.textlength(test_text, font=font) <= max_width:
            current_line_tokens = test_tokens
        else:
            if current_line_tokens:
                line_text = "".join(seg + sep for seg, sep in current_line_tokens).rstrip()
                lines.append(line_text)
            # Start new line with current token
            current_line_tokens = [(segment, separator)]

    if current_line_tokens:
        final_text = "".join(seg + sep for seg, sep in current_line_tokens).rstrip()
        lines.append(final_text)

    return lines

# ======================================================
# MAIN GENERATOR
# ======================================================
def generate_and_save_qr_code(
    display_text: Optional[str] = None,
    cycle_timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    ensure_folder()

    visual = load_visual_settings()
    qr_name = get_next_qr_name()
    cycle_timestamp = cycle_timestamp or datetime.now()
    timestamp_str = cycle_timestamp.strftime("%d-%m-%Y %H:%M:%S")

    # Use custom display or extract prefix exactly
    if display_text is not None:
        prefix_display = display_text
    else:
        prefix_display = qr_name.rsplit("-", 1)[0]  # Everything before final counter hyphen

    counter_str = qr_name.split("-")[-1]

    filename = f"{qr_name}.png"
    rel_path = Path("qr_images") / filename
    abs_path = QR_FOLDER / filename

    canvas = Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    # ==================== QR CODE ====================
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
    qr.add_data(qr_name)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=visual["qr_fill_color"], back_color=visual["qr_back_color"]).convert("RGB")

    qr_size = int(LABEL_HEIGHT * visual["qr_size_ratio"])
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    qr_x = visual["qr_margin"]
    qr_y = (LABEL_HEIGHT - qr_size) // 2
    canvas.paste(qr_img, (qr_x, qr_y))

    # ==================== TEXT AREA ====================
    text_x = qr_x + qr_size + visual["text_margin"]
    text_width = LABEL_WIDTH - text_x - visual["text_margin"]

    main_font_size = visual["title_font_size"]
    main_font = load_font(FONT_BOLD_PATH, main_font_size)
    ts_font = load_font(FONT_REGULAR_PATH, visual["timestamp_font_size"])

    # Wrap only at special chars
    prefix_lines = wrap_text_at_special_chars(draw, prefix_display, text_width, main_font)

    # Auto-shrink font if needed (max 3 lines for prefix)
    while main_font_size > visual["min_title_font_size"] and len(prefix_lines) > 3:
        main_font_size -= 4
        main_font = load_font(FONT_BOLD_PATH, main_font_size)
        prefix_lines = wrap_text_at_special_chars(draw, prefix_display, text_width, main_font)

    counter_font = main_font

    # Heights
    prefix_line_height = main_font.getbbox("Ay")[3] - main_font.getbbox("Ay")[1] + 12
    counter_line_height = counter_font.getbbox(counter_str)[3] - counter_font.getbbox(counter_str)[1] + 12
    ts_line_height = ts_font.getbbox("Ay")[3] - ts_font.getbbox("Ay")[1] + 6

    total_text_height = (
        len(prefix_lines) * prefix_line_height +
        counter_line_height +
        24 +
        ts_line_height
    )
    start_y = (LABEL_HEIGHT - total_text_height) // 2

    # Draw prefix lines (with special chars preserved)
    y = start_y
    for line in prefix_lines:
        bbox = draw.textbbox((0, 0), line, font=main_font)
        w = bbox[2] - bbox[0]
        x = text_x + (text_width - w) // 2
        draw.text((x, y), line, fill=visual["text_color"], font=main_font)
        y += prefix_line_height

    # Draw counter
    bbox = draw.textbbox((0, 0), counter_str, font=counter_font)
    w = bbox[2] - bbox[0]
    x = text_x + (text_width - w) // 2
    draw.text((x, y), counter_str, fill=visual["text_color"], font=counter_font)
    y += counter_line_height + 24

    # Draw timestamp
    bbox = draw.textbbox((0, 0), timestamp_str, font=ts_font)
    w = bbox[2] - bbox[0]
    x = text_x + (text_width - w) // 2
    draw.text((x, y), timestamp_str, fill=visual["timestamp_color"], font=ts_font)

    canvas.save(abs_path, dpi=(DPI, DPI), optimize=True)

    qr_id = save_qr_code(str(rel_path), qr_name)

    logger.info(f"Generated QR: {abs_path} | Code: {qr_name}")

    return {
        "id": qr_id,
        "text": qr_name,
        "absolutePath": str(abs_path),
        "filename": filename,
        "relativePath": str(rel_path),
    }

# ======================================================
# GET QR AS BASE64
# ======================================================
def get_qr_code(qr_id: int) -> Optional[str]:
    meta = dao_get_qr_code(qr_id)
    if not meta or not meta.get("filename"):
        return None

    file_path = Path(meta["filename"])
    if not file_path.is_absolute():
        file_path = BASE_DIR / file_path

    if not file_path.exists():
        return None

    try:
        with open(file_path, "rb") as f:
            data = b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{data}"
    except Exception as e:
        logger.error(f"QR read error: {e}")
        return None