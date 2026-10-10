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

    def test_typed_home_path_is_kept_as_typed(self):
        """'~' paths are expanded on use, so a copied jumps.json still works
        under a different user name"""
        assert jumpstore.normalize_jump_path("~/projects") == "~/projects"

    def test_typed_relative_path_is_made_absolute(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert jumpstore.normalize_jump_path("projects") == os.path.join(os.getcwd(), "projects")

    def test_blank_path_means_current_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert jumpstore.normalize_jump_path("") == os.getcwd()

    def test_add_jump_rejects_empty_name(self, tmp_path):
        self._use_tmp_path(tmp_path)
        ok, err = jumpstore.add_jump("", "desc", "/path")
        assert ok is False
        assert jumpstore.list_jumps() == []

    def test_add_jump_backs_up_unreadable_file(self, tmp_path):
        """Adding to a jumps.json that doesn't parse must not silently
        replace everything in it with the one new jump."""
        self._use_tmp_path(tmp_path)
        broken = '[{"name": "work", "desc": "", "path": "/work"},]'
        with open(jumpstore.JUMPS_PATH, "w") as f:
            f.write(broken)

        ok, err = jumpstore.add_jump("code", "desc", "/code")

        assert ok is True
        assert [j["name"] for j in jumpstore.list_jumps()] == ["code"]
        with open(jumpstore.JUMPS_PATH + ".bak") as f:
            assert f.read() == broken
