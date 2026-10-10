import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx import handlers
from src.nyxx.app_state import AppState
from src.nyxx.dialogs import DialogUnavailable
from src.nyxx.navigator import Navigator


class _StubUI:
    """Just the UIEngine state the handlers touch."""
    def __init__(self, selection_index=0, error_message=None):
        self.selection_index = selection_index
        self.error_message = error_message

    def move_selection(self, direction, total_items):
        step = 1 if direction == "down" else -1
        self.selection_index = max(0, min(self.selection_index + step, total_items - 1))


def _listing(nav):
    items = nav.list_items()["items"]
    paths = [os.path.join(nav.get_current_path(), i) for i in items]
    return items, paths


class TestNavInput:
    def test_back_goes_up_a_folder(self, tmp_path):
        child = tmp_path / "child"
        child.mkdir()
        nav = Navigator(str(child))
        app, ui = AppState("nav"), _StubUI(selection_index=2)

        handlers.handle_nav_input(app, ui, "back", nav, *_listing(nav))

        assert nav.get_current_path() == str(tmp_path)
        assert app.state == "nav"
        assert ui.selection_index == 0

    def test_back_at_filesystem_root_returns_home(self):
        root = os.path.abspath(os.sep)
        nav = Navigator(root)
        app, ui = AppState("nav"), _StubUI()

        handlers.handle_nav_input(app, ui, "back", nav, [".."], [root])

        assert app.state == "home"
        assert nav.get_current_path() == root

    def test_enter_on_a_file_reports_why_not(self, tmp_path):
        (tmp_path / "notes.txt").write_text("x")
        nav = Navigator(str(tmp_path))
        app, ui = AppState("nav"), _StubUI(selection_index=1)

        handlers.handle_nav_input(app, ui, "enter", nav, *_listing(nav))

        assert ui.error_message == "Not a directory"
        assert nav.get_current_path() == str(tmp_path)

    def test_message_clears_on_next_key(self, tmp_path):
        nav = Navigator(str(tmp_path))
        app, ui = AppState("nav"), _StubUI(error_message="Copied 'a' successfully.")

        handlers.handle_nav_input(app, ui, "down", nav, *_listing(nav))

        assert ui.error_message is None


class TestThemeInput:
    def test_missing_color_picker_shows_message_instead_of_crashing(self, monkeypatch):
        saved = []
        def unavailable():
            raise DialogUnavailable("no graphical display to show it on")
        monkeypatch.setattr(handlers, "pick_color_gui", unavailable)
        monkeypatch.setattr(handlers, "config_set", lambda key, value: saved.append(key))
        app, ui = AppState("theme"), _StubUI(selection_index=1)
        app.theme_mode = "toggles"

        handlers.handle_theme_input(app, ui, "enter", None, None, [], [])

        assert "no graphical display" in ui.error_message
        assert saved == []

    def test_scene_switch_replaces_stale_error(self, monkeypatch):
        monkeypatch.setattr(handlers, "config_set", lambda key, value: None)

        class _Engine:
            load_error = None
            def set_scene(self, name):
                self.scene = name

        app, ui = AppState("theme"), _StubUI(selection_index=1, error_message="old failure")
        engine = _Engine()

        handlers.handle_theme_input(app, ui, "enter", None, engine, [], ["user image", "vaporwave sunset"])

        assert engine.scene == "vaporwave sunset"
        assert app.scene_theme == "vaporwave sunset"
        assert ui.error_message is None
