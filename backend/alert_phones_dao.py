# backend/alert_phones_dao.py
from .db import query

def get_phones_by_model_id(model_id: int) -> list:
    return query("SELECT * FROM alert_phones WHERE model_id = %s", (model_id,))

def get_all_phone_numbers(model_id: int) -> list[str]:
    rows = query("SELECT phone_number FROM alert_phones WHERE model_id = %s", (model_id,))
    return [row["phone_number"] for row in rows]

def add_phone(model_id: int, phone_number: str) -> int:
    return query(
        "INSERT INTO alert_phones (model_id, phone_number) VALUES (%s, %s)",
        (model_id, phone_number)
    )

def update_phone(phone_id: int, phone_number: str) -> int:
    return query(
        "UPDATE alert_phones SET phone_number = %s WHERE id = %s",
        (phone_number, phone_id)
    )

def delete_phone(phone_id: int) -> int:
    return query("DELETE FROM alert_phones WHERE id = %s", (phone_id,))