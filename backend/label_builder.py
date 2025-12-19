# backend/label_builder.py
# ======================================================
# ZPL LABEL BUILDER (For REAL Zebra Printers)
# ======================================================

def build_zpl_label(qr_text: str, model_name: str, result: str) -> str:
    """
    2cm x 2cm label @ 203 DPI (≈200x200 dots)
    """
    return f"""
^XA
^PW200
^LL200

^FO20,20
^BQN,2,4
^FDLA,{qr_text}^FS

^FO20,140
^A0N,18,18
^FD{model_name}^FS

^FO20,165
^A0N,18,18
^FD{result}^FS

^XZ
"""
