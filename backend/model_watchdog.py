# backend/model_watchdog.py
import os
import time
import json
import threading

ACTIVE_MODEL_FILE = os.path.join(os.path.dirname(__file__), "active_model.json")

_last_mtime = None
_listeners = []       # callbacks: callback(model_dict)
_cached_model = {}    # shared cache visible to other modules


def get_cached_model() -> dict:
    """Return the current cached active model (may be empty {})."""
    return _cached_model


def register_listener(callback):
    """
    Register a listener callback that accepts one argument: the model dict.
    Example: register_listener(detector.update_model_limits)
    """
    if callable(callback):
        _listeners.append(callback)


def _notify_listeners(model: dict):
    for cb in list(_listeners):
        try:
            cb(model)
        except Exception as e:
            print("⚠ model_watchdog: listener callback failed:", e)


def _load_model():
    """Read JSON file and update cache + notify listeners."""
    global _cached_model
    try:
        with open(ACTIVE_MODEL_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            print("⚠ model_watchdog: active_model.json invalid format (expected object).")
            return
        _cached_model = data
        print("🔁 model_watchdog: active model loaded:", _cached_model)
        _notify_listeners(_cached_model)
    except FileNotFoundError:
        # No JSON yet — leave cache empty but notify listeners with {} once if needed
        print("⚠ model_watchdog: active_model.json not found.")
    except Exception as e:
        print("⚠ model_watchdog: failed to load active_model.json:", e)


def _watch_file(poll_interval: float = 0.5):
    """Background loop that watches file modification time."""
    global _last_mtime
    while True:
        try:
            if os.path.exists(ACTIVE_MODEL_FILE):
                mtime = os.path.getmtime(ACTIVE_MODEL_FILE)
                if _last_mtime is None:
                    _last_mtime = mtime
                    _load_model()
                elif mtime != _last_mtime:
                    _last_mtime = mtime
                    print("👀 model_watchdog: detected change in active_model.json")
                    _load_model()
        except Exception as e:
            print("⚠ model_watchdog: watch error:", e)
        time.sleep(poll_interval)


def start_watchdog():
    """Start the background watcher thread (idempotent)."""
    # start thread only once
    thread = threading.Thread(target=_watch_file, daemon=True)
    thread.start()
    print("👀 model_watchdog: watchdog started (polling active_model.json).")


# Auto-start on import so modules that import model_watchdog immediately benefit.
start_watchdog()
