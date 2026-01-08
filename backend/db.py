# backend/db.py  ← UPDATED VERSION (uses config)
import mysql.connector
from mysql.connector import pooling
import logging

from config.app_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

log = logging.getLogger(__name__)

# Force old collation that EVERY connector supports
pool = pooling.MySQLConnectionPool(
    pool_name="pqc_pool",
    pool_size=5,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    autocommit=True,
    charset='utf8mb4',
    collation='utf8mb4_general_ci',   # ← This one is 100% supported everywhere
    use_unicode=True
)

def query(sql: str, params=None, fetch_one=False):
    conn = None
    try:
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        
        if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
            conn.commit()
            result = cursor.lastrowid or cursor.rowcount
            log.debug("DB write: %s -> %s", sql.replace('\n', ' ').strip(), result)
            return result
        else:
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            log.debug("DB read: %s -> %d rows", sql.replace('\n', ' ').strip(), len(result) if isinstance(result, list) else (1 if result else 0))
            return result
    except Exception as e:
        log.error("DB Error: %s", e)
        if conn:
            conn.rollback()
        return None if fetch_one else []
    finally:
        if conn and conn.in_transaction:
            conn.rollback()
        if conn:
            conn.close()