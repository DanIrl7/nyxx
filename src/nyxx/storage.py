"""Helpers shared by the JSON stores in ~/.nyxx (config, jumps, memos)."""
import json
import os


def backup_if_unreadable(path, expected_type):
    """Call before overwriting `path`. If the file exists but doesn't hold
    valid JSON of `expected_type`, the store has been reading it as empty,
    so writing now would silently wipe whatever the user had in it (say,
    after a typo while hand-editing). Move it aside to `<path>.bak` first."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            if isinstance(json.load(f), expected_type):
                return
    except FileNotFoundError:
        return
    except ValueError:  # malformed JSON, or not valid UTF-8
        pass
    os.replace(path, path + ".bak")
