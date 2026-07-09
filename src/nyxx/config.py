import os
import json

CONFIG_PATH = os.path.expanduser("~/.nyxx/config.json")

DEFAULTS = {
    "theme":          "starry night",   
    "sky_theme":      "starry night",
    "ground_theme":   "city",
    "scene_theme":    "vaporwave sunset",
    "ui_theme":       "cyber cyan",
    "user_image_path": "",
    "sky_enabled":    True,
    "ground_enabled": True,
    "logo_enabled":   True,
    "bg_mode":        "layered",
    
    "panel_color":           None,
    "text_color":            None,
    "highlight_panel_color": None,
    "highlight_text_color":  None,
    "border_fg":             None,
    "border_bg":             None,
}

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return dict(DEFAULTS)
            for key, val in DEFAULTS.items():
                data.setdefault(key, val)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def get(key):
    return load_config().get(key, DEFAULTS.get(key))

def set(key, value):
    config = load_config()
    config[key] = value
    save_config(config)