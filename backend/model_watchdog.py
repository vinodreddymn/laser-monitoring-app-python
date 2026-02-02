"""
Active Model Watchdog – Single Source of Truth

Responsibilities:
- Watch system_state.active_model_id
- Update cached active model ONLY when:
    1) Active model ID changes (user clicks Activate)
    2) Active model data changes while still active
- Notify listeners only on real changes
- Persist active model snapshot to JSON (optional)
"""

import os
import time
import json
import threading
import copy
import logging
from typing import Optional, Callable

from backend.db import query

log = logging.getLogger(__name__)

# ----------------------------------------------------
# Constants / State
# ----------------------------------------------------

ACTIVE_MODEL_FILE = os.path.join(
    os.path.dirname(__file__), "active_model.json"
)

_cached_model: dict = {}
_listeners: list[Callable[[dict], None]] = []

_watchdog_started = False
_lock = threading.Lock()

_last_active_model_id: Optional[int] = None
_last_model_signature: Optional[str] = None


# ----------------------------------------------------
# Public API
# ----------------------------------------------------

def get_cached_model() -> dict:
    """Return a copy of the currently cached active model."""
    with _lock:
        return dict(_cached_model)


def register_listener(callback: Callable[[dict], None]) -> None:
    """
    Register a callback to be notified when active model changes.
    Callback signature: fn(model_dict)
    """
    if callable(callback):
        _listeners.append(callback)


# ----------------------------------------------------
# Internal helpers
# ----------------------------------------------------

def _notify_listeners(model: dict) -> None:
    for cb in list(_listeners):
        try:
            cb(model)
        except Exception:
            log.exception("⚠ model_watchdog: listener failed")


def _fetch_active_model_from_db() -> Optional[dict]:
    """
    Fetch active model using system_state as source of truth.
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


def _model_signature(model: dict) -> str:
    """
    Stable fingerprint of model data.
    Any change here triggers listeners.
    """
    relevant = {
        "id": model.get("id"),
        "name": model.get("name"),
        "model_type": model.get("model_type"),
        "lower_limit": model.get("lower_limit"),
        "upper_limit": model.get("upper_limit"),
        "touch_point": model.get("touch_point"),  # ✅ INCLUDED
    }
    return json.dumps(relevant, sort_keys=True)


def _update_cache_and_notify(model: dict) -> None:
    """
    Update in-memory cache, persist JSON, notify listeners.
    """
    global _cached_model

    with _lock:
        if model == _cached_model:
            return  # absolute no-op

        _cached_model.clear()
        _cached_model.update(model)

    # Persist snapshot (non-critical)
    try:
        with open(ACTIVE_MODEL_FILE, "w") as f:
            json.dump(model, f, indent=4)
    except Exception:
        log.exception("⚠ model_watchdog: failed to write JSON")

    log.info(
        "🔁 model_watchdog: active model updated → %s",
        {
            "id": model.get("id"),
            "name": model.get("name"),
            "touch_point": model.get("touch_point"),
        }
    )

    _notify_listeners(copy.deepcopy(model))


# ----------------------------------------------------
# Watchdog Thread
# ----------------------------------------------------

def _watch_active_model(poll_interval: float = 0.5) -> None:
    """
    Background loop:
    - Detects active model ID changes
    - Detects data changes for the active model
    """
    global _last_active_model_id, _last_model_signature

    while True:
        try:
            row = query(
                "SELECT active_model_id FROM system_state WHERE id = 1",
                fetch_one=True
            )

            active_id = row["active_model_id"] if row else None

            if not active_id:
                time.sleep(poll_interval)
                continue

            model = _fetch_active_model_from_db()
            if not model:
                time.sleep(poll_interval)
                continue

            signature = _model_signature(model)

            # CASE 1: User activated a different model
            if active_id != _last_active_model_id:
                _last_active_model_id = active_id
                _last_model_signature = signature
                _update_cache_and_notify(model)

            # CASE 2: Same active model, but data changed
            elif signature != _last_model_signature:
                _last_model_signature = signature
                _update_cache_and_notify(model)

        except Exception:
            log.exception("⚠ model_watchdog: DB watch error")

        time.sleep(poll_interval)


# ----------------------------------------------------
# Startup
# ----------------------------------------------------

def start_watchdog() -> None:
    """Start the watchdog thread (idempotent)."""
    global _watchdog_started

    if _watchdog_started:
        return

    _watchdog_started = True
    thread = threading.Thread(
        target=_watch_active_model,
        daemon=True,
        name="ModelWatchdog"
    )
    thread.start()
    log.info("👀 model_watchdog: started")


# Auto-start on import
start_watchdog()
