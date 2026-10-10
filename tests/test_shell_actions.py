import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx import shell_actions


class TestShellActions:
    def setup_method(self, method):
        self._orig_path = shell_actions.ACTION_FILE

    def teardown_method(self, method):
        shell_actions.ACTION_FILE = self._orig_path

    def _use_tmp_path(self, tmp_path):
        shell_actions.ACTION_FILE = str(tmp_path / "action")

    def test_write_shell_action_format(self, tmp_path):
        self._use_tmp_path(tmp_path)
        shell_actions.write_shell_action("CD", "C:\\Program Files (x86)\\Música")
        with open(shell_actions.ACTION_FILE, encoding="utf-8") as f:
            assert f.read() == "CD:C:\\Program Files (x86)\\Música"

    def test_clear_removes_leftover_action(self, tmp_path):
        """An action no wrapper consumed must not survive into a later run"""
        self._use_tmp_path(tmp_path)
        shell_actions.write_shell_action("EXEC", "rm -rf build")
        shell_actions.clear_shell_action()
        assert not os.path.exists(shell_actions.ACTION_FILE)

    def test_clear_without_action_is_a_no_op(self, tmp_path):
        self._use_tmp_path(tmp_path)
        shell_actions.clear_shell_action()
        assert not os.path.exists(shell_actions.ACTION_FILE)
