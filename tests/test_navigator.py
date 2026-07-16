import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx.navigator import Navigator
from src.nyxx.pathhandler import PathHandler

class TestNavigator:
    def test_init_starts_at_home(self):
        """Navigator should start at home directory"""
        nav = Navigator()
        assert nav.get_current_path() == os.path.expanduser("~")
    
    def test_init_with_custom_path(self):
        """Navigator should accept custom start path"""
        nav = Navigator("/tmp")
        assert nav.get_current_path() == "/tmp"
    
    def test_list_items_returns_dict(self):
        """list_items should return dict with success, items, error"""
        nav = Navigator()
        result = nav.list_items()
        assert "success" in result
        assert "items" in result
        assert "error" in result
    
    def test_list_items_filters_hidden(self):
        """list_items should not include hidden files (starting with .)"""
        nav = Navigator()
        result = nav.list_items()
        for item in result["items"]:
            assert item == ".." or not item.startswith('.')

class TestPathHandler:
    def test_validate_path_home(self):
        """Home directory should validate as True"""
        home = os.path.expanduser("~")
        assert PathHandler.validate_path(home) == True
    
    def test_validate_path_nonexistent(self):
        """Nonexistent path should validate as False"""
        assert PathHandler.validate_path("/nonexistent/fake/path") == False
    
    def test_expand_path_tilde(self):
        """expand_path should convert ~ to home"""
        expanded = PathHandler.expand_path("~/Documents")
        assert "~" not in expanded
        assert expanded.startswith(os.path.expanduser("~"))
    
    def test_is_hidden(self):
        """is_hidden should identify files starting with ."""
        assert PathHandler.is_hidden(".bashrc") == True
        assert PathHandler.is_hidden("README.md") == False