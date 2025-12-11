# backend/db.py  ← NEW VERSION (copy-paste this)
import mysql.connector
from mysql.connector import pooling
import logging

# Force old collation that EVERY connector supports
pool = pooling.MySQLConnectionPool(
    pool_name="pqc_pool",
    pool_size=5,
    host="localhost",
    user="svr_user",
    password="india123",
    database="pneumatic_qc",
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
            return cursor.lastrowid or cursor.rowcount
        else:
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            return result
    except Exception as e:
        logging.error(f"DB Error: {e}")
        if conn:
            conn.rollback()
        return None if fetch_one else []
    finally:
        if conn and conn.in_transaction:
            conn.rollback()
        if conn:
            conn.close()