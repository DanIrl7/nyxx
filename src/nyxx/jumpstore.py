import os
import json

from .storage import backup_if_unreadable

JUMPS_PATH = os.path.expanduser("~/.nyxx/jumps.json")

def _load():
    """Load jumps list from disk. Returns [] if file missing or invalid."""
    try:
        with open(JUMPS_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, ValueError):  # ValueError: bad JSON or encoding
        return []

def _save(jumps):
    """Write jumps list to disk."""
    os.makedirs(os.path.dirname(JUMPS_PATH), exist_ok=True)
    backup_if_unreadable(JUMPS_PATH, list)
    with open(JUMPS_PATH, "w") as f:
        json.dump(jumps, f, indent=2)

def list_jumps():
    """Return all saved jumps as a list of dicts: {name, desc, path}."""
    return _load()

def find_jump(name):
    """Return the jump dict matching name, or None."""
    for j in _load():
        if j.get("name") == name:
            return j
    return None

def normalize_jump_path(path):
    """How a path typed for a new jump gets stored. Blank means the current
    directory. A relative path is made absolute, since otherwise it would
    resolve against wherever the jump is later used from. "~/..." is kept
    as typed: it's expanded when the jump is used, so it stays valid in a
    jumps.json copied to another machine or user account."""
    if not path:
        return os.getcwd()
    if path.startswith("~"):
        return path
    return os.path.abspath(path)

def add_jump(name, desc, path):
    """Add or overwrite a jump. Returns (success, error_message)."""
    if not name:
        return False, "Name can't be empty"
    jumps = _load()
    # Overwrite if name already exists
    jumps = [j for j in jumps if j.get("name") != name]
    jumps.append({"name": name, "desc": desc, "path": path})
    try:
        _save(jumps)
        return True, None
    except Exception as e:
        return False, str(e)

def delete_jump(name):
    """Delete a jump by name. Returns (success, error_message)."""
    jumps = _load()
    new_jumps = [j for j in jumps if j.get("name") != name]
    if len(new_jumps) == len(jumps):
        return False, f"No jump named '{name}'"
    try:
        _save(new_jumps)
        return True, None
    except Exception as e:
        return False, str(e)