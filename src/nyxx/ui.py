import curses
import pyfiglet
from .config import get as config_get, set as config_set


class UIEngine:
    """Owns curses color/theme state, keyboard input mapping, and the
    generic drawing primitives (panel frames, lists, text truncation)
    that every screen in `screens.py` is built from."""

    UI_THEMES = {
        "cyber cyan": {
            "border": curses.COLOR_CYAN,
            "text": curses.COLOR_WHITE,
            "highlight": curses.COLOR_CYAN,
            "hint": curses.COLOR_YELLOW,
            "bg": curses.COLOR_BLACK
        },
        "matrix green": {
            "border": curses.COLOR_GREEN,
            "text": curses.COLOR_GREEN,
            "highlight": curses.COLOR_GREEN,
            "hint": curses.COLOR_WHITE,
            "bg": curses.COLOR_BLACK
        },
        "vaporwave": {
            "border": curses.COLOR_MAGENTA,
            "text": curses.COLOR_WHITE,
            "highlight": curses.COLOR_MAGENTA,
            "hint": curses.COLOR_CYAN,
            "bg": curses.COLOR_BLACK
        },
        "dracula": {
            "border": curses.COLOR_RED,
            "text": curses.COLOR_WHITE,
            "highlight": curses.COLOR_RED,
            "hint": curses.COLOR_YELLOW,
            "bg": curses.COLOR_BLACK
        },
        "ocean depth": {
            "border": curses.COLOR_CYAN,
            "text": curses.COLOR_WHITE,
            "highlight": curses.COLOR_CYAN,
            "hint": curses.COLOR_WHITE,
            "bg": curses.COLOR_BLUE
        },
        "high contrast": {
            "border": curses.COLOR_WHITE,
            "text": curses.COLOR_BLACK,
            "highlight": curses.COLOR_CYAN,
            "hint": curses.COLOR_BLACK,
            "bg": curses.COLOR_WHITE,
        },
        "custom": {
            "border": curses.COLOR_WHITE,
            "text": curses.COLOR_WHITE,
            "highlight": curses.COLOR_BLUE,
            "hint": curses.COLOR_YELLOW,
            "bg": curses.COLOR_BLACK
        }
    }

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.max_y, self.max_x = self.stdscr.getmaxyx()

        curses.start_color()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        self.selection_index = 0
        self.scroll_position = 0

        name_map = {
            "BLACK": curses.COLOR_BLACK,
            "RED": curses.COLOR_RED,
            "GREEN": curses.COLOR_GREEN,
            "YELLOW": curses.COLOR_YELLOW,
            "BLUE": curses.COLOR_BLUE,
            "MAGENTA": curses.COLOR_MAGENTA,
            "CYAN": curses.COLOR_CYAN,
            "WHITE": curses.COLOR_WHITE,
        }
        self.COLOR_MAP = name_map

        self.WHITE = 1
        self.CYAN = 2
        self.YELLOW = 3
        self.SELECTION = 4
        self.PANEL_PAIR = 5
        self.BORDER_PAIR = 6
        self.PANEL_HINT_PAIR = 7

        _vw8 = [
            curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLUE,
            curses.COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_CYAN,
            curses.COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA,
            curses.COLOR_MAGENTA, curses.COLOR_RED,     curses.COLOR_RED,
            curses.COLOR_YELLOW,  curses.COLOR_YELLOW,  curses.COLOR_YELLOW,
            curses.COLOR_WHITE,   curses.COLOR_WHITE,   curses.COLOR_WHITE,
            curses.COLOR_BLUE,    curses.COLOR_CYAN,    curses.COLOR_MAGENTA,
            curses.COLOR_BLUE,    curses.COLOR_BLUE,    curses.COLOR_BLUE,
        ]
        for _i, _c in enumerate(_vw8):
            curses.init_pair(8 + _i, _c, curses.COLOR_BLACK)

        self.apply_ui_theme(config_get("ui_theme") or "cyber cyan")
        self.refresh_custom_colors()

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def refresh_custom_colors(self):
        p_bg_name = config_get("panel_color")
        text_col_name = config_get("text_color")
        hl_bg_name = config_get("highlight_panel_color")
        hl_fg_name = config_get("highlight_text_color")
        b_fg_name = config_get("border_fg")
        b_bg_name = config_get("border_bg")

        def _resolve(val, default):
            if isinstance(val, int):
                return val
            if isinstance(val, str) and val:
                return self.COLOR_MAP.get(val.upper(), default)
            return default

        self.UI_THEMES["custom"] = {
            "bg": _resolve(p_bg_name, curses.COLOR_BLACK),
            "text": _resolve(text_col_name, curses.COLOR_WHITE),
            "highlight": _resolve(hl_bg_name, curses.COLOR_CYAN),
            "hint": curses.COLOR_YELLOW,
            "border": _resolve(b_fg_name, curses.COLOR_WHITE),
            "hl_fg": _resolve(hl_fg_name, curses.COLOR_BLACK),
            "b_bg": _resolve(b_bg_name, curses.COLOR_BLACK)
        }

        theme_name = config_get("ui_theme") or "cyber cyan"
        theme = self.UI_THEMES.get(theme_name, self.UI_THEMES["cyber cyan"])

        curses.init_pair(self.PANEL_PAIR, theme["text"], theme["bg"])
        curses.init_pair(self.BORDER_PAIR, theme["border"], theme.get("b_bg", curses.COLOR_BLACK))
        curses.init_pair(self.SELECTION, theme.get("hl_fg", curses.COLOR_BLACK), theme["highlight"])
        curses.init_pair(self.PANEL_HINT_PAIR, theme["hint"], theme["bg"])

        curses.init_pair(235, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.error_message = None

    def apply_ui_theme(self, theme_name):
        if theme_name and theme_name in self.UI_THEMES:
            config_set("ui_theme", theme_name)
        self.refresh_custom_colors()

    def apply_custom_colors(self, panel_color_name=None, border_color_name=None):
        self.refresh_custom_colors()

    def cleanup(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def refresh(self):
        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def map_key(self, key):
        if key == -1: return None
        if key == curses.KEY_UP or key == ord("k") or key == 450: return "up"
        elif key == curses.KEY_DOWN or key == ord("j") or key == 456: return "down"
        elif key == curses.KEY_LEFT or key == ord("h") or key == curses.KEY_BACKSPACE or key == ord('\b') or key == 452: return "back"
        elif key == curses.KEY_RIGHT or key == ord("l") or key == ord('\n') or key == 454: return "enter"
        elif key == ord('c'): return "copy_item"
        elif key == ord('x'): return "cut_item"
        elif key == ord('v'): return "paste_item"
        elif key == ord(' '): return "confirm"
        elif key == ord('.'): return "toggle_hidden"
        elif key == ord('z'): return "help"
        elif key == 27 or key == ord('q'): return "quit"
        elif key == curses.KEY_RESIZE: return "resize"
        elif key == ord('d'): return "delete"
        elif key == ord('y'): return "yes"
        elif key == ord('n'): return "no"
        elif key == ord('\t'): return "tab"
        else: return None

    def get_input(self):
        key = self.stdscr.getch()
        return self.map_key(key)

    # ------------------------------------------------------------------
    # Generic drawing primitives shared by every screen
    # ------------------------------------------------------------------

    def fill_panel_bg(self, y, x, w, h):
        for r in range(1, h - 1):
            try:
                self.stdscr.addstr(y + r, x + 1, " " * (w - 2), curses.color_pair(self.PANEL_PAIR))
            except curses.error: pass

    def move_selection(self, direction, total_items):
        if total_items == 0:
            return
        if direction == "down":
            self.selection_index = min(self.selection_index + 1, total_items - 1)
        elif direction == "up":
            self.selection_index = max(self.selection_index - 1, 0)
        viewport_height = self.max_y - 3
        self.scroll_position = max(0, self.selection_index - viewport_height // 2)

    def draw_list(self, items, start_row=1):
        viewport_height = self.max_y - 3
        for i, item in enumerate(items[self.scroll_position:self.scroll_position + viewport_height]):
            row = start_row + i
            if self.scroll_position + i == self.selection_index:
                self.stdscr.addstr(row, 0, item, curses.color_pair(self.SELECTION))
            else:
                self.stdscr.addstr(row, 0, item, curses.color_pair(self.PANEL_PAIR))

    def truncate(self, text, max_width):
        if len(text) > max_width:
            return text[:max_width - 1] + "…"
        return text

    def get_logo_lines(self):
        fig = pyfiglet.figlet_format("nyxx", font="banner3-D")
        return fig.splitlines()

    def draw_panel(self, lines, footer_lines=None):
        padding_x = 3
        curses.curs_set(0)
        padding_y = 1
        all_lines = lines + (footer_lines or [])
        content_width = max(len(l) for l in all_lines) if all_lines else 20
        box_width = content_width + (padding_x * 2) + 2
        box_height = len(lines) + (len(footer_lines) if footer_lines else 0) + (padding_y * 2) + 2

        start_y = max(0, (self.max_y - box_height) // 2)
        start_x = max(0, (self.max_x - box_width) // 2)

        color = curses.color_pair(self.BORDER_PAIR)
        panel_bg = curses.color_pair(self.PANEL_PAIR)

        try:
            self.stdscr.addstr(start_y, start_x, '╔' + '═' * (box_width - 2) + '╗', color)
        except curses.error: pass

        for y_offset in range(1, padding_y + 1):
            try:
                self.stdscr.addstr(start_y + y_offset, start_x, '║', color)
                self.stdscr.addstr(start_y + y_offset, start_x + 1, ' ' * (box_width - 2), panel_bg)
                self.stdscr.addstr(start_y + y_offset, start_x + box_width - 1, '║', color)
            except curses.error: pass

        for i, line in enumerate(lines):
            row = start_y + 1 + padding_y + i
            left_spaces = ' ' * (padding_x + 1)
            right_spaces = ' ' * (box_width - 2 - len(left_spaces) - len(line))
            try:
                self.stdscr.addstr(row, start_x, '║', color)
                self.stdscr.addstr(row, start_x + 1, left_spaces, panel_bg)
                self.stdscr.addstr(row, start_x + 1 + len(left_spaces), line, panel_bg)
                self.stdscr.addstr(row, start_x + 1 + len(left_spaces) + len(line), right_spaces, panel_bg)
                self.stdscr.addstr(row, start_x + box_width - 1, '║', color)
            except curses.error: pass

        if footer_lines:
            divider_row = start_y + 1 + padding_y + len(lines)
            try:
                self.stdscr.addstr(divider_row, start_x, '╠' + '═' * (box_width - 2) + '╣', color)
            except curses.error: pass
            for i, line in enumerate(footer_lines):
                row = divider_row + 1 + i
                left_spaces = ' ' * (padding_x + 1)
                right_spaces = ' ' * (box_width - 2 - len(left_spaces) - len(line))
                try:
                    self.stdscr.addstr(row, start_x, '║', color)
                    self.stdscr.addstr(row, start_x + 1, left_spaces, panel_bg)
                    self.stdscr.addstr(row, start_x + 1 + len(left_spaces), line, curses.color_pair(self.PANEL_HINT_PAIR))
                    self.stdscr.addstr(row, start_x + 1 + len(left_spaces) + len(line), right_spaces, panel_bg)
                    self.stdscr.addstr(row, start_x + box_width - 1, '║', color)
                except curses.error: pass

        bottom_row = start_y + box_height - 1
        try:
            self.stdscr.addstr(bottom_row, start_x, '╚' + '═' * (box_width - 2) + '╝', color)
        except curses.error: pass

        return start_y, start_x, box_width
