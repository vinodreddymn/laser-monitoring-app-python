# backend/qr_reprint_dao.py

from backend.db import query

def get_qr_by_text(qr_text: str):
    """
    Fetch QR record by exact QR text.
    """
    rows = query(
        """
        SELECT qr_data
        FROM qr_codes
        WHERE qr_data = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (qr_text,),
    )
    return rows[0] if rows else None
