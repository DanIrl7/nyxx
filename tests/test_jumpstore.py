import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx import jumpstore


class TestJumpstore:
    def setup_method(self, method):
        self._orig_path = jumpstore.JUMPS_PATH

    def teardown_method(self, method):
        jumpstore.JUMPS_PATH = self._orig_path

    def _use_tmp_path(self, tmp_path):
        jumpstore.JUMPS_PATH = str(tmp_path / "jumps.json")

    def test_list_jumps_empty_when_missing(self, tmp_path):
        self._use_tmp_path(tmp_path)
        assert jumpstore.list_jumps() == []

    def test_add_jump_then_find(self, tmp_path):
        self._use_tmp_path(tmp_path)
        ok, err = jumpstore.add_jump("code", "my projects folder", "/home/user/projects")
        assert ok is True
        assert err is None

        found = jumpstore.find_jump("code")
        assert found == {"name": "code", "desc": "my projects folder", "path": "/home/user/projects"}

    def test_find_jump_missing_returns_none(self, tmp_path):
        self._use_tmp_path(tmp_path)
        assert jumpstore.find_jump("nope") is None

    def test_add_jump_overwrites_existing_name(self, tmp_path):
        self._use_tmp_path(tmp_path)
        jumpstore.add_jump("code", "old desc", "/old/path")
        jumpstore.add_jump("code", "new desc", "/new/path")

        jumps = jumpstore.list_jumps()
        assert len(jumps) == 1
        assert jumps[0]["desc"] == "new desc"
        assert jumps[0]["path"] == "/new/path"

    def test_delete_jump_removes_entry(self, tmp_path):
        self._use_tmp_path(tmp_path)
        jumpstore.add_jump("code", "desc", "/path")
        ok, err = jumpstore.delete_jump("code")
        assert ok is True
        assert err is None
        assert jumpstore.list_jumps() == []

    def test_delete_jump_missing_returns_error(self, tmp_path):
        self._use_tmp_path(tmp_path)
        ok, err = jumpstore.delete_jump("nope")
        assert ok is False
        assert "nope" in err
