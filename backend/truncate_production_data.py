"""
ONE-TIME PRODUCTION RESET SCRIPT

⚠️ WARNING:
This will PERMANENTLY delete all historical production data.
Use ONLY before starting fresh production.
"""

import logging
import os
import sys

# --------------------------------------------------
# Ensure PROJECT ROOT is on PYTHON PATH
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.db import query   # ✅ now works

log = logging.getLogger(__name__)

TABLES_TO_TRUNCATE = [
    "cycle_print_log",
    "cycle_print_log_archive",
    "qr_codes",
    "qr_codes_archive",
    "sms_queue",
    "sms_queue_archive",
]

def truncate_tables():
    log.warning("🚨 STARTING FULL PRODUCTION DATA TRUNCATION 🚨")

    # Child tables first
    for table in TABLES_TO_TRUNCATE:
        query(f"TRUNCATE TABLE {table}")
        log.info("🧹 Truncated table: %s", table)

    # Parent table → DELETE, not TRUNCATE
    query("DELETE FROM cycles")
    query("ALTER TABLE cycles AUTO_INCREMENT = 1")
    log.info("🧹 Deleted all rows from cycles")

    # Archive can still be truncated
    query("TRUNCATE TABLE cycles_archive")
    log.info("🧹 Truncated table: cycles_archive")

    log.warning("✅ ALL PRODUCTION TABLES CLEARED")



if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    truncate_tables()
