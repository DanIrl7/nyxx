import os
import json

CONFIG_PATH = os.path.expanduser("~/.nyxx/config.json")

DEFAULTS = {
    "theme":          "starry night",   # kept for backward compat
    "sky_theme":      "starry night",
    "ground_theme":   "city",
    "scene_theme":    "vaporwave sunset",
    "user_image_path": "",
    "sky_enabled":    True,
    "ground_enabled": True,
    "bg_mode":        "layered",
}

def load_config():
    """Load config from disk, filling in any missing keys with defaults."""
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return dict(DEFAULTS)
            # Fill in any keys added since the file was created
            for key, val in DEFAULTS.items():
                data.setdefault(key, val)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS)

def save_config(config):
    """Write config dict to disk."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def get(key):
    """Read a single config value."""
    return load_config().get(key, DEFAULTS.get(key))

def set(key, value):
    """Write a single config value, preserving all other keys."""
    config = load_config()
    config[key] = value
    save_config(config)