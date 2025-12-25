# backend/model_watchdog.py

import os
import time
import json
import threading
import copy

from backend.db import query
from typing import Optional


ACTIVE_MODEL_FILE = os.path.join(os.path.dirname(__file__), "active_model.json")

_cached_model = {}
_listeners = []
_watchdog_started = False
_lock = threading.Lock()

_last_active_model_id = None


# ---------------------------------------------------
def get_cached_model() -> dict:
    """Return a copy of the current cached active model."""
    with _lock:
        return dict(_cached_model)


def register_listener(callback):
    """
    Register a listener callback that accepts one argument: the model dict.
    """
    if callable(callback):
        _listeners.append(callback)


def _notify_listeners(model: dict):
    for cb in list(_listeners):
        try:
            cb(model)
        except Exception as e:
            print("⚠ model_watchdog: listener failed:", e)


# ---------------------------------------------------
def _fetch_active_model_from_db() -> Optional[dict]:

    """
    Fetch active model using system_state as the source of truth.
    """
    return query(
        """
        SELECT m.*
        FROM system_state s
        JOIN models m ON m.id = s.active_model_id
        WHERE s.id = 1
        """,
        fetch_one=True
    )


def _update_cache_and_notify(model: dict):
    global _cached_model

    with _lock:
        if model == _cached_model:
            return  # no change

        _cached_model.clear()
        _cached_model.update(model)

    # Persist JSON cache (optional but useful)
    try:
        with open(ACTIVE_MODEL_FILE, "w") as f:
            json.dump(model, f, indent=4)
    except Exception as e:
        print("⚠ model_watchdog: failed to write JSON:", e)

    print("🔁 model_watchdog: active model updated:", model)
    _notify_listeners(copy.deepcopy(model))


# ---------------------------------------------------
def _watch_active_model(poll_interval: float = 0.5):
    """
    Background loop watching active model from DB.
    """
    global _last_active_model_id

    while True:
        try:
            row = query(
                "SELECT active_model_id FROM system_state WHERE id = 1",
                fetch_one=True
            )

            active_id = row["active_model_id"] if row else None

            if active_id != _last_active_model_id:
                _last_active_model_id = active_id

                if active_id is None:
                    continue

                model = _fetch_active_model_from_db()
                if model:
                    _update_cache_and_notify(model)

        except Exception as e:
            print("⚠ model_watchdog: DB watch error:", e)

        time.sleep(poll_interval)


# ---------------------------------------------------
def start_watchdog():
    """Start the DB watchdog thread (idempotent)."""
    global _watchdog_started

    if _watchdog_started:
        return

    _watchdog_started = True
    thread = threading.Thread(target=_watch_active_model, daemon=True)
    thread.start()
    print("👀 model_watchdog: DB watchdog started")


# Auto-start
start_watchdog()
