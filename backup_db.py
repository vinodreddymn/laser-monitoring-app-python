# backup_db.py
# ======================================================
# Database Backup Script
# Pneumatic Laser QC System
#
# Creates a schema-only backup of the MySQL database using mysqldump.
# Output: backup_YYYYMMDD_HHMMSS.sql in the project root.
# ======================================================

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config.app_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Database configuration (from config)
# DB_HOST = "localhost"
# DB_USER = "svr_user"
# DB_PASSWORD = "india123"
# DB_NAME = "pneumatic_qc"

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent

def create_backup():
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = PROJECT_ROOT / f"backup_{timestamp}.sql"

    # mysqldump command (schema only, no data)
    command = [
        "mysqldump",
        f"--host={DB_HOST}",
        f"--user={DB_USER}",
        f"--password={DB_PASSWORD}",
        "--no-data",
        DB_NAME
    ]

    try:
        print(f"Starting database backup to {backup_file}...")

        with open(backup_file, "w") as f:
            result = subprocess.run(
                command,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

        print(f"Backup completed successfully: {backup_file}")
        return str(backup_file)

    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: mysqldump not found. Ensure MySQL is installed and in PATH.")
        sys.exit(1)

if __name__ == "__main__":
    create_backup()