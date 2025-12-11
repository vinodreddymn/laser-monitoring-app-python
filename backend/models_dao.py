# backend/models_dao.py
import json
import os
from .db import query

ACTIVE_MODEL_FILE = os.path.join(os.path.dirname(__file__), "active_model.json")


def get_models() -> list:
    return query("SELECT * FROM models ORDER BY name")


def get_model_by_id(model_id: int) -> dict:
    return query("SELECT * FROM models WHERE id = %s", (model_id,), fetch_one=True)


def add_model(name: str, lower_limit: float, upper_limit: float) -> int:
    return query(
        "INSERT INTO models (name, lower_limit, upper_limit) VALUES (%s, %s, %s)",
        (name, lower_limit, upper_limit)
    )


def update_model(model_id: int, name: str, lower_limit: float, upper_limit: float) -> int:
    return query(
        "UPDATE models SET name = %s, lower_limit = %s, upper_limit = %s WHERE id = %s",
        (name, lower_limit, upper_limit, model_id)
    )


def delete_model(model_id: int) -> int:
    return query("DELETE FROM models WHERE id = %s", (model_id,))


# ---------------------------------------------------------------------------
#  ACTIVE MODEL HANDLING (DB + JSON)
# ---------------------------------------------------------------------------

def set_active_model(model_id: int):
    """
    Updates the active model in DB and writes the same model info to a JSON file
    so detector and UI can read it without repeating DB queries.
    """

    # Update DB first
    query("UPDATE system_state SET active_model_id = %s WHERE id = 1", (model_id,))

    # Get full model details
    model = get_model_by_id(model_id)

    if not model:
        return

    # Save to JSON file for fast access
    try:
        with open(ACTIVE_MODEL_FILE, "w") as f:
            json.dump(model, f, indent=4)
        print(f"✅ Active model saved to JSON: {ACTIVE_MODEL_FILE}")
    except Exception as e:
        print("⚠ Failed to write active model JSON:", e)


def get_active_model() -> dict:
    """
    First tries reading from JSON (fast).
    Falls back to DB only if JSON does not exist.
    """

    # Try JSON first
    if os.path.exists(ACTIVE_MODEL_FILE):
        try:
            with open(ACTIVE_MODEL_FILE, "r") as f:
                return json.load(f)
        except:
            pass  # fallback to DB

    # Fallback: read from DB
    model = query("""
        SELECT m.*
        FROM system_state s
        JOIN models m ON m.id = s.active_model_id
        WHERE s.id = 1
    """, fetch_one=True)

    # If DB read works, refresh JSON cache
    if model:
        try:
            with open(ACTIVE_MODEL_FILE, "w") as f:
                json.dump(model, f, indent=4)
        except:
            pass

    return model
