import os

class PathHandler:
    @staticmethod
    def validate_path(path):
        try:
            return os.path.isdir(path) and os.access(path, os.R_OK)
        except:
            return False
        
    @staticmethod
    def expand_path(path):
        return os.path.expanduser(path)
    
    @staticmethod
    def get_parent_path(path):
        parent = os.path.dirname(path)
        return parent if parent != path else path
    
    @staticmethod
    def is_hidden(filename):
        return filename.startswith('.')

    @staticmethod
    def initialize_storage():
        navi_dir = os.path.expanduser("~/.navi")
        if not os.path.exists(navi_dir):
            os.makedirs(navi_dir)

        for filename in ["jumps.json", "memos.json"]:
            filepath = os.path.join(navi_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, "w") as f:
                    f.write("[]")
