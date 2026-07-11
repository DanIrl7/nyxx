# src/nyxx/icons.py

import os

# File extension → emoji
EXT_ICONS = {
    # Python / scripting
    ".py":   "🐍",
    ".sh":   "💿",
    ".ps1":  "💿",
    ".bash": "💿️",
    # Markup / docs
    ".md":   "📝",
    ".txt":  "📄",
    ".rst":  "📄",
    ".pdf":  "📕",
    # Data / config
    ".json": "🧾",
    ".yaml": "🧾",
    ".yml":  "🧾",
    ".toml": "🧾",
    ".ini":  "🧾",
    ".cfg":  "🧾",
    ".env":  "🧾",
    # Web
    ".html": "🌐",
    ".css":  "🎨",
    ".js":   "🟨",
    ".ts":   "🟦",
    ".jsx":  "🟨",
    ".tsx":  "🟦",
    # Images
    ".png":  "📸",
    ".jpg":  "📸",
    ".jpeg": "📸",
    ".gif":  "📸",
    ".svg":  "📸",
    # Archives
    ".zip":  "📦",
    ".tar":  "📦",
    ".gz":   "📦",
    ".rar":  "📦",
    # Code (other)
    ".c":    "📎",
    ".cpp":  "📎",
    ".h":    "📎",
    ".rs":   "🦀",
    ".go":   "🐹",
    ".rb":   "💎",
    ".java": "☕",
    ".kt":   "📎",
    # Misc
    ".lock": "🔒",
    ".log":  "📋",
    ".csv":  "📊",
    ".sql":  "🗄️",
    ".db":   "🗄️",
}

# Fallback ASCII icons for terminals that can't render emoji
ASCII_ICONS = {
    "dir":     "[d]",
    "symlink": "[~]",
    "file":    "[ ]",
    "up":      "[^]",
}


def get_icon(full_path, ascii_mode=False):
    """
    Return the emoji (or ASCII) icon for a filesystem entry.
    full_path should be the absolute path to the item.
    """
    if ascii_mode:
        if os.path.islink(full_path):
            return ASCII_ICONS["symlink"]
        if os.path.isdir(full_path):
            return ASCII_ICONS["dir"]
        return ASCII_ICONS["file"]

    if os.path.islink(full_path):
        return "🔗"
    if os.path.isdir(full_path):
        return "📁"

    _, ext = os.path.splitext(full_path)
    return EXT_ICONS.get(ext.lower(), "📄") 