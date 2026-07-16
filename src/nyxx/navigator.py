

import os
import shutil

class Navigator:
    def __init__(self, start_path=None):
        self.current_path = os.path.expanduser("~") if start_path is None else start_path
        self.history = [self.current_path]
        self.show_hidden = False  

        self.clipboard_path = None
        self.clipboard_mode = None   
        
    def set_clipboard(self, path, mode):
        """Stores the target file path and operation type."""
        self.clipboard_path = path
        self.clipboard_mode = mode

    def execute_paste(self):
        """Executes the copy or move operation into the current directory."""
        if not self.clipboard_path or not os.path.exists(self.clipboard_path):
            return {"success": False, "error": "Nothing in clipboard or file missing."}

        src = self.clipboard_path
        filename = os.path.basename(src)
        dest = os.path.join(self.current_path, filename)

        if os.path.exists(dest):
            return {"success": False, "error": f"File '{filename}' already exists here."}

        try:
            if self.clipboard_mode == "copy":
                # copytree handles folders, copy2 handles files (and preserves metadata)
                if os.path.isdir(src):
                    shutil.copytree(src, dest)
                else:
                    shutil.copy2(src, dest)
                return {"success": True, "error": f"Copied '{filename}' successfully."}
                
            elif self.clipboard_mode == "cut":
                shutil.move(src, dest)
                # Clear the clipboard after a successful cut so it can't be pasted twice
                self.clipboard_path = None 
                self.clipboard_mode = None
                return {"success": True, "error": f"Moved '{filename}' successfully."}
                
        except PermissionError:
            return {"success": False, "error": "Permission denied."}
        except Exception as e:
            return {"success": False, "error": str(e)}# toggled by '.' key

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