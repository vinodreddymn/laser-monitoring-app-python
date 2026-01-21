# ======================================================
# Database Full Backup Script
# Pneumatic Laser QC System
#
# Creates a FULL backup (schema + data) of the MySQL database
# using mysqldump.
#
# Output: backup_full_YYYYMMDD_HHMMSS.sql in the project root.
# ======================================================

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config.app_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent


def create_full_backup():
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = PROJECT_ROOT / f"backup_full_{timestamp}.sql"

    # mysqldump command (schema + data)
    command = [
        "mysqldump",
        f"--host={DB_HOST}",
        f"--user={DB_USER}",
        f"--password={DB_PASSWORD}",
        "--routines",
        "--triggers",
        "--events",
        "--single-transaction",
        "--quick",
        "--databases",
        DB_NAME,
    ]

    try:
        print(f"Starting FULL database backup to {backup_file}...")

        with open(backup_file, "w", encoding="utf-8") as f:
            subprocess.run(
                command,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

        print(f"Full backup completed successfully: {backup_file}")
        return str(backup_file)

    except subprocess.CalledProcessError as e:
        print("Backup failed:")
        print(e.stderr)
        sys.exit(1)

    except FileNotFoundError:
        print("Error: mysqldump not found. Ensure MySQL/MariaDB client is installed and in PATH.")
        sys.exit(1)


if __name__ == "__main__":
    create_full_backup()
