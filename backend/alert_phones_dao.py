# backend/alert_phones_dao.py

import logging
from .db import query

log = logging.getLogger(__name__)


# ---------------------------------------------------
# BASIC CRUD
# ---------------------------------------------------
def get_phones_by_model_id(model_id: int) -> list:
    return query(
        "SELECT * FROM alert_phones WHERE model_id = %s",
        (model_id,)
    )


def add_phone(model_id: int, name: str, phone_number: str) -> int:
    return query(
        """
        INSERT INTO alert_phones (model_id, name, phone_number)
        VALUES (%s, %s, %s)
        """,
        (model_id, name, phone_number),
    )


def update_phone(phone_id: int, name: str, phone_number: str) -> int:
    return query(
        """
        UPDATE alert_phones
        SET name = %s, phone_number = %s
        WHERE id = %s
        """,
        (name, phone_number, phone_id),
    )


def delete_phone(phone_id: int) -> int:
    return query(
        "DELETE FROM alert_phones WHERE id = %s",
        (phone_id,),
    )


# ---------------------------------------------------
# SMS / ALERT HELPERS
# ---------------------------------------------------
def get_all_phone_numbers(model_id: int) -> list[str]:
    """
    Legacy helper (kept for compatibility)
    """
    rows = query(
        "SELECT phone_number FROM alert_phones WHERE model_id = %s",
        (model_id,),
    )
    return [row["phone_number"] for row in rows]


def get_all_alert_contacts(model_id: int) -> list:
    """
    Preferred helper.

    Returns:
    [
        { "name": str, "phone_number": str }
    ]
    """
    return query(
        """
        SELECT name, phone_number
        FROM alert_phones
        WHERE model_id = %s
        """,
        (model_id,),
    )
