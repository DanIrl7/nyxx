import os
import logging

ACTION_FILE = os.path.expanduser("~/.nyxx/action")


def write_shell_action(action_type, value):
    """Writes actions to a temporary file to be executed by shell wrappers."""
    try:
        os.makedirs(os.path.dirname(ACTION_FILE), exist_ok=True)
        with open(ACTION_FILE, "w", encoding="utf-8") as f:
            f.write(f"{action_type}:{value}")
    except Exception as e:
        logging.error(f"Failed to write shell action: {e}")


def clear_shell_action():
    """Removes an action left behind by an earlier run — e.g. Nyxx.exe
    started from the Start menu, with no shell wrapper around to consume
    it — so a wrapper can't pick it up after some later, unrelated run."""
    try:
        os.remove(ACTION_FILE)
    except FileNotFoundError:
        pass
    except OSError as e:
        logging.error(f"Failed to clear shell action: {e}")
