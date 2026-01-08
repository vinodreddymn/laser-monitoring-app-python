# backend/models_dao.py

import json
import os
import logging
from .db import query

log = logging.getLogger(__name__)

ACTIVE_MODEL_FILE = os.path.join(os.path.dirname(__file__), "active_model.json")

# ---------------------------------------------------------------------------
#  MODELS CRUD
# ---------------------------------------------------------------------------

def get_models() -> list:
    """
    Returns all models ordered by name.
    Includes: id, name, model_type, lower_limit, upper_limit
    """
    return query("SELECT * FROM models ORDER BY name")


def get_model_by_id(model_id: int) -> dict:
    """
    Fetch a single model by ID.
    """
    return query(
        "SELECT * FROM models WHERE id = %s",
        (model_id,),
        fetch_one=True
    )


def add_model(
    name: str,
    model_type: str,
    lower_limit: float,
    upper_limit: float
) -> int:
    """
    Add a new model.
    model_type examples: RHD, LHD
    """
    result = query(
        """
        INSERT INTO models (name, model_type, lower_limit, upper_limit)
        VALUES (%s, %s, %s, %s)
        """,
        (name, model_type, lower_limit, upper_limit)
    )
    log.info("Added model: %s (%s) limits %.2f-%.2f", name, model_type, lower_limit, upper_limit)
    return result


def update_model(
    model_id: int,
    name: str,
    model_type: str,
    lower_limit: float,
    upper_limit: float
) -> int:
    """
    Update an existing model.
    """
    result = query(
        """
        UPDATE models
        SET name = %s,
            model_type = %s,
            lower_limit = %s,
            upper_limit = %s
        WHERE id = %s
        """,
        (name, model_type, lower_limit, upper_limit, model_id)
    )
    log.info("Updated model %s: %s (%s) limits %.2f-%.2f", model_id, name, model_type, lower_limit, upper_limit)
    return result


def delete_model(model_id: int) -> int:
    """
    Delete a model by ID.
    """
    result = query(
        "DELETE FROM models WHERE id = %s",
        (model_id,)
    )
    log.info("Deleted model %s", model_id)
    return result


# ---------------------------------------------------------------------------
#  ACTIVE MODEL HANDLING (DB + JSON CACHE)
# ---------------------------------------------------------------------------

def set_active_model(model_id: int):
    """
    Updates the active model in DB and writes the same model info
    to a JSON file so detector and UI can read it without repeated DB queries.
    """

    # Update DB
    query(
        "UPDATE system_state SET active_model_id = %s WHERE id = 1",
        (model_id,)
    )

    # Fetch full model details (now includes model_type)
    model = get_model_by_id(model_id)
    if not model:
        return

    # Cache to JSON
    try:
        with open(ACTIVE_MODEL_FILE, "w") as f:
            json.dump(model, f, indent=4)
        log.info("✅ Active model cached: %s", ACTIVE_MODEL_FILE)
    except Exception:
        log.exception("⚠ Failed to write active model JSON")


def get_active_model() -> dict:
    """
    Fast path: JSON
    Fallback: DB
    """

    # 1️⃣ Try JSON cache
    if os.path.exists(ACTIVE_MODEL_FILE):
        try:
            with open(ACTIVE_MODEL_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass  # fallback to DB

    # 2️⃣ Fallback to DB
    model = query(
        """
        SELECT m.*
        FROM system_state s
        JOIN models m ON m.id = s.active_model_id
        WHERE s.id = 1
        """,
        fetch_one=True
    )

    # Refresh JSON cache
    if model:
        try:
            with open(ACTIVE_MODEL_FILE, "w") as f:
                json.dump(model, f, indent=4)
        except Exception:
            pass

    return model
