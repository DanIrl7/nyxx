import os
import logging


def write_shell_action(action_type, value):
    """Writes actions to a temporary file to be executed by shell wrappers."""
    action_file = os.path.expanduser("~/.nyxx/action")
    try:
        os.makedirs(os.path.dirname(action_file), exist_ok=True)
        with open(action_file, "w", encoding="utf-8") as f:
            f.write(f"{action_type}:{value}")
    except Exception as e:
        logging.error(f"Failed to write shell action: {e}")
