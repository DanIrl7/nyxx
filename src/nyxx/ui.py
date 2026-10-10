import curses
from .background import nearest_standard_color
from .config import get as config_get

# Custom panel colors are saved as xterm-256 indices (dialogs.pick_color_gui).
# Where the terminal lets us redefine colors, each is loaded into its own
# slot below instead of being used by index: the background image redefines
# colors 16–29 for its palette (background.py), which would otherwise
# repaint any custom color that happens to fall in that range.
_CUSTOM_COLOR_SLOTS = {
    "panel_color": 30, "text_color": 31, "highlight_panel_color": 32,
    "highlight_text_color": 33, "border_fg": 34, "border_bg": 35,
}

_XTERM_CUBE_STEPS = (0, 95, 135, 175, 215, 255)


def _xterm_to_rgb(index):
    """RGB (0–255) of xterm-256 palette entry `index` (16–255)."""
    if index >= 232:
        level = 8 + (index - 232) * 10
        return level, level, level
    index -= 16
    return (_XTERM_CUBE_STEPS[index // 36],
            _XTERM_CUBE_STEPS[(index // 6) % 6],
            _XTERM_CUBE_STEPS[index % 6])


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

        # Error/status lines are drawn with this pair.
        curses.init_pair(self.YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)

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

        self.theme_name = "cyber cyan"
        self.apply_ui_theme(config_get("ui_theme"))

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def _custom_color(self, key, default):
        """The custom color saved under `key` (an xterm-256 index, or a
        legacy color name), as a curses color this terminal can show."""
        val = config_get(key)
        if isinstance(val, str) and val:
            return self.COLOR_MAP.get(val.upper(), default)
        if not isinstance(val, int) or not 0 <= val <= 255:
            return default
        if val < 16:
            # The 8 basic colors and their bright variants; on an 8-color
            # terminal fall back from the bright one to the basic one.
            return val if val < curses.COLORS else val % 8

        rgb = _xterm_to_rgb(val)
        if curses.has_colors() and curses.can_change_color() and curses.COLORS >= 256:
            slot = _CUSTOM_COLOR_SLOTS[key]
            try:
                curses.init_color(slot, *(c * 1000 // 255 for c in rgb))
                return slot
            except curses.error:
                pass
        if val < curses.COLORS:
            return val
        # Fewer colors than the one that was picked (e.g. TERM=xterm):
        # use the closest basic color rather than fail to start.
        return nearest_standard_color(rgb)

    def refresh_custom_colors(self):
        # Only while the custom theme is in use: resolving can redefine
        # terminal colors, which some terminals keep after Nyxx exits.
        if self.theme_name == "custom":
            self.UI_THEMES["custom"] = {
                "bg": self._custom_color("panel_color", curses.COLOR_BLACK),
                "text": self._custom_color("text_color", curses.COLOR_WHITE),
                "highlight": self._custom_color("highlight_panel_color", curses.COLOR_CYAN),
                "hint": curses.COLOR_YELLOW,
                "border": self._custom_color("border_fg", curses.COLOR_WHITE),
                "hl_fg": self._custom_color("highlight_text_color", curses.COLOR_BLACK),
                "b_bg": self._custom_color("border_bg", curses.COLOR_BLACK)
            }

        theme = self.UI_THEMES.get(self.theme_name, self.UI_THEMES["cyber cyan"])

        for pair, fg, bg in (
            (self.PANEL_PAIR, theme["text"], theme["bg"]),
            (self.BORDER_PAIR, theme["border"], theme.get("b_bg", curses.COLOR_BLACK)),
            (self.SELECTION, theme.get("hl_fg", curses.COLOR_BLACK), theme["highlight"]),
            (self.PANEL_HINT_PAIR, theme["hint"], theme["bg"]),
        ):
            try:
                curses.init_pair(pair, fg, bg)
            except curses.error:
                pass

        self.error_message = None

    def apply_ui_theme(self, theme_name):
        """Switch the on-screen theme. Doesn't save anything — callers that
        want the choice remembered write it to the config themselves — so
        starting Nyxx never rewrites config.json."""
        if theme_name in self.UI_THEMES:
            self.theme_name = theme_name
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
        # pyfiglet costs real import time and isn't needed unless the home
        # screen's logo is actually shown, so import it lazily; the
        # rendered banner never changes at runtime, so cache it too.
        if not hasattr(self, "_logo_lines_cache"):
            import pyfiglet
            fig = pyfiglet.figlet_format("nyxx", font="banner3-D")
            self._logo_lines_cache = fig.splitlines()
        return self._logo_lines_cache

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
