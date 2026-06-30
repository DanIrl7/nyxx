

import os

class Navigator:
    def __init__(self, start_path=None):
        self.current_path = os.getcwd() if start_path is None else start_path
        self.history = [self.current_path]
        self.show_hidden = False          # toggled by '.' key

    def get_current_path(self):
        return self.current_path

    def toggle_hidden(self):
        self.show_hidden = not self.show_hidden

    def list_items(self):
        """
        Returns a dict:
          { "success": bool, "items": [str, ...], "error": str|None }
        Items are plain filenames (not full paths).
        Hidden files are excluded unless show_hidden is True.
        The '..' entry is always prepended.
        """
        try:
            raw = os.listdir(self.current_path)
            if not self.show_hidden:
                raw = [i for i in raw if not i.startswith('.')]
            items = [".."] + sorted(raw, key=lambda x: (
                not os.path.isdir(os.path.join(self.current_path, x)),
                x.lower()
            ))
            return {"success": True, "items": items, "error": None}
        except PermissionError:
            return {"success": False, "items": [], "error": "Permission denied"}
        except Exception as e:
            return {"success": False, "items": [], "error": str(e)}

    def go_forward(self, item_name):
        """Navigate into a directory. Returns {"success": bool, "error": str|None}."""
        if item_name == "..":
            return self.go_back()
        try:
            new_path = os.path.join(self.current_path, item_name)
            if not os.path.isdir(new_path):
                return {"success": False, "error": "Not a directory"}
            self.current_path = new_path
            self.history.append(self.current_path)
            return {"success": True, "error": None}
        except PermissionError:
            return {"success": False, "error": "Permission denied"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def go_back(self):
        """Navigate to parent directory."""
        try:
            parent = os.path.dirname(self.current_path)
            if parent == self.current_path:
                return {"success": False, "error": "Already at filesystem root"}
            self.current_path = parent
            self.history.append(self.current_path)
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}