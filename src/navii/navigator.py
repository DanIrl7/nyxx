import os

class Navigator:
    def __init__(self, start_path=None):
        if start_path is None:
            self.current_path = os.path.expanduser("~")  
        else:
            self.current_path = start_path

        self.history = [self.current_path]

    def get_current_path(self):
        return self.current_path
    
    def list_items(self):
        try:
            items = os.listdir(self.current_path)
            items = [item for item in items if not item.startswith('.')]
            return { "success": True, "items": sorted(items), "error": None }
        except PermissionError:
            return {"success": False, "items": [], "error": "Permission denied"}
        except Exception as e:
            return {"success": False, "items": [], "error": str(e)}
    
    def go_forward(self, item_name):
        try:
            # Build new path
            new_path = os.path.join(self.current_path, item_name)
            
            # Check if it's a directory
            if not os.path.isdir(new_path):
                return {"success": False, "error": "That's a file, not a folder"}
            
            # Update current path and add to history
            self.current_path = new_path
            self.history.append(self.current_path)
            return {"success": True, "error": None}
        
        except PermissionError:
            return {"success": False, "error": "Permission denied"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def go_back(self):
        try:
            if len(self.history) > 1:
                self.history.pop()  # Remove current path
                self.current_path = self.history[-1]  # Go back to previous path
                return {"success": True, "error": None}
            else:
                return {"success": False, "error": "Already at root directory"}
            
        except PermissionError:
            return {"success": False, "error": "Permission denied"}
        except Exception as e:
            return {"success": False, "error": str(e)}