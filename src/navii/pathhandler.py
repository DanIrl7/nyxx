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