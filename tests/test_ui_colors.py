import sys
import os
import curses
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx import ui as ui_module
from src.nyxx.ui import UIEngine


class TestCustomColors:
    def _engine(self, monkeypatch, saved, colors, can_change_color):
        """A UIEngine with just enough state for _custom_color, on a fake
        terminal with `colors` colors (curses state needs no real screen)."""
        defined = {}
        monkeypatch.setattr(ui_module, "config_get", lambda key: saved.get(key))
        monkeypatch.setattr(curses, "COLORS", colors, raising=False)
        monkeypatch.setattr(curses, "has_colors", lambda: True)
        monkeypatch.setattr(curses, "can_change_color", lambda: can_change_color)
        monkeypatch.setattr(curses, "init_color", lambda n, r, g, b: defined.__setitem__(n, (r, g, b)))
        engine = UIEngine.__new__(UIEngine)
        engine.COLOR_MAP = {"CYAN": curses.COLOR_CYAN}
        return engine, defined

    def test_picked_color_beyond_terminal_range_falls_back(self, monkeypatch):
        """On an 8-color terminal a saved xterm-256 color used to make
        init_pair fail on every launch; now it maps to the nearest basic one"""
        engine, _ = self._engine(monkeypatch, {"panel_color": 196}, colors=8, can_change_color=False)
        assert engine._custom_color("panel_color", curses.COLOR_BLACK) == curses.COLOR_RED

    def test_redefinable_terminal_uses_slot_clear_of_image_palette(self, monkeypatch):
        """The background image redefines colors 16-29, so a custom color
        must not be used by index there"""
        engine, defined = self._engine(monkeypatch, {"panel_color": 17}, colors=256, can_change_color=True)
        slot = engine._custom_color("panel_color", curses.COLOR_BLACK)
        assert not 16 <= slot <= 29
        assert defined[slot] == (0, 0, 95 * 1000 // 255)  # xterm 17 is rgb(0, 0, 95)

    def test_plain_256_color_terminal_uses_index(self, monkeypatch):
        engine, defined = self._engine(monkeypatch, {"panel_color": 17}, colors=256, can_change_color=False)
        assert engine._custom_color("panel_color", curses.COLOR_BLACK) == 17
        assert defined == {}

    def test_legacy_names_and_unset_values(self, monkeypatch):
        engine, _ = self._engine(monkeypatch, {"text_color": "cyan"}, colors=8, can_change_color=False)
        assert engine._custom_color("text_color", curses.COLOR_WHITE) == curses.COLOR_CYAN
        assert engine._custom_color("border_fg", curses.COLOR_WHITE) == curses.COLOR_WHITE
