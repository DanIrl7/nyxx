# src/navii/memostore.py
import os
import json

MEMOS_PATH = os.path.expanduser("~/.navi/memos.json")

def _load():
    """Load memos list from disk. Returns [] if file missing or invalid."""
    try:
        with open(MEMOS_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save(memos):
    """Write memos list to disk."""
    os.makedirs(os.path.dirname(MEMOS_PATH), exist_ok=True)
    with open(MEMOS_PATH, "w") as f:
        json.dump(memos, f, indent=2)

def list_memos():
    """Return all saved memos as a list of dicts: {name, desc, cmd}."""
    return _load()

def find_memo(name):
    """Return the memo dict matching name, or None."""
    for m in _load():
        if m.get("name") == name:
            return m
    return None

def add_memo(name, desc, cmd):
    """Add or overwrite a memo. Returns (success, error_message)."""
    memos = _load()
    memos = [m for m in memos if m.get("name") != name]
    memos.append({"name": name, "desc": desc, "cmd": cmd})
    try:
        _save(memos)
        return True, None
    except Exception as e:
        return False, str(e)

def delete_memo(name):
    """Delete a memo by name. Returns (success, error_message)."""
    memos = _load()
    new_memos = [m for m in memos if m.get("name") != name]
    if len(new_memos) == len(memos):
        return False, f"No memo named '{name}'"
    try:
        _save(new_memos)
        return True, None
    except Exception as e:
        return False, str(e)