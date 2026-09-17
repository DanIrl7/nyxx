import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx import memostore


class TestMemostore:
    def setup_method(self, method):
        self._orig_path = memostore.MEMOS_PATH

    def teardown_method(self, method):
        memostore.MEMOS_PATH = self._orig_path

    def _use_tmp_path(self, tmp_path):
        memostore.MEMOS_PATH = str(tmp_path / "memos.json")

    def test_list_memos_empty_when_missing(self, tmp_path):
        self._use_tmp_path(tmp_path)
        assert memostore.list_memos() == []

    def test_add_memo_then_find(self, tmp_path):
        self._use_tmp_path(tmp_path)
        ok, err = memostore.add_memo("virtual", "activates the venv", "source venv/bin/activate")
        assert ok is True
        assert err is None

        found = memostore.find_memo("virtual")
        assert found == {"name": "virtual", "desc": "activates the venv", "cmd": "source venv/bin/activate"}

    def test_find_memo_missing_returns_none(self, tmp_path):
        self._use_tmp_path(tmp_path)
        assert memostore.find_memo("nope") is None

    def test_add_memo_overwrites_existing_name(self, tmp_path):
        self._use_tmp_path(tmp_path)
        memostore.add_memo("virtual", "old desc", "old cmd")
        memostore.add_memo("virtual", "new desc", "new cmd")

        memos = memostore.list_memos()
        assert len(memos) == 1
        assert memos[0]["desc"] == "new desc"
        assert memos[0]["cmd"] == "new cmd"

    def test_delete_memo_removes_entry(self, tmp_path):
        self._use_tmp_path(tmp_path)
        memostore.add_memo("virtual", "desc", "cmd")
        ok, err = memostore.delete_memo("virtual")
        assert ok is True
        assert err is None
        assert memostore.list_memos() == []

    def test_delete_memo_missing_returns_error(self, tmp_path):
        self._use_tmp_path(tmp_path)
        ok, err = memostore.delete_memo("nope")
        assert ok is False
        assert "nope" in err
