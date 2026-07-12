import curses
import pyfiglet
import os
from .config import get as config_get, set as config_set
import time

class UIEngine:
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
        elif key == ord('\t'): return "tab"
        else: return None  
        
    def get_input(self):
        key = self.stdscr.getch()
        return self.map_key(key)
    
    def _fill_panel_bg(self, y, x, w, h):
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

    def _truncate(self, text, max_width):
        if len(text) > max_width:
            return text[:max_width - 1] + "…"
        return text

    def draw_cd_panel(self, current_path, items, full_paths, show_hidden):
        from .icons import get_icon
        curses.curs_set(0)
        max_y, max_x = self.stdscr.getmaxyx()
        panel_w = min(60, max_x - 4)
        panel_h = min(22, max_y - 4)
        panel_x = (max_x - panel_w) // 2
        panel_y = (max_y - panel_h) // 2

        self._fill_panel_bg(panel_y, panel_x, panel_w, panel_h)

        top = "╔" + "═" * (panel_w - 2) + "╗"
        try:
            self.stdscr.addstr(panel_y, panel_x, top, curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        for row in range(1, panel_h - 1):
            try:
                self.stdscr.addstr(panel_y + row, panel_x,     "║", curses.color_pair(self.BORDER_PAIR))
                self.stdscr.addstr(panel_y + row, panel_x + panel_w - 1, "║", curses.color_pair(self.BORDER_PAIR))
            except curses.error: pass

        bot = "╚" + "═" * (panel_w - 2) + "╝"
        try:
            self.stdscr.addstr(panel_y + panel_h - 1, panel_x, bot, curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        inner_w = panel_w - 4          
        header = "📂 " + self._truncate(current_path, inner_w - 3)
        try:
            self.stdscr.addstr(panel_y + 1, panel_x + 2, header, curses.color_pair(self.PANEL_PAIR) | curses.A_BOLD)
        except curses.error: pass

        div = "╠" + "═" * (panel_w - 2) + "╣"
        try:
            self.stdscr.addstr(panel_y + 2, panel_x, div, curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        list_rows = panel_h - 9
        list_y    = panel_y + 3
        half = list_rows // 2
        scroll = max(0, min(self.selection_index - half, len(items) - list_rows))

        visible = items[scroll:scroll + list_rows]
        visible_paths = full_paths[scroll:scroll + list_rows]

        for i, (name, fpath) in enumerate(zip(visible, visible_paths)):
            abs_idx = scroll + i
            selected = abs_idx == self.selection_index
            icon = get_icon(fpath)
            icon_col  = panel_x + 2
            arrow_col = panel_x + 4
            name_col  = panel_x + 6
            max_name = panel_w - 8   
            display_name = self._truncate(name, max_name)
            row_y = list_y + i
            if row_y >= panel_y + panel_h - 6:
                break

            if selected:
                attr = curses.color_pair(self.SELECTION)
                blank = " " * (panel_w - 2)
                try:
                    self.stdscr.addstr(row_y, panel_x + 1, blank, attr)
                    self.stdscr.addstr(row_y, icon_col,  icon,          attr)
                    self.stdscr.addstr(row_y, arrow_col, "▸",           attr)
                    self.stdscr.addstr(row_y, name_col,  display_name,  attr)
                except curses.error: pass
            else:
                attr = curses.color_pair(self.PANEL_PAIR)
                try:
                    self.stdscr.addstr(row_y, panel_x + 1, " " * (panel_w - 2), attr)
                    self.stdscr.addstr(row_y, icon_col,  icon,          attr)
                    self.stdscr.addstr(row_y, arrow_col, " ",           attr)
                    self.stdscr.addstr(row_y, name_col,  display_name,  attr)
                except curses.error: pass

        if len(items) > list_rows:
            sb_x = panel_x + panel_w - 2
            bar_h = list_rows
            thumb_pos = int(scroll / max(1, len(items) - list_rows) * (bar_h - 1))
            for row in range(bar_h):
                char = "█" if row == thumb_pos else "░"
                try:
                    self.stdscr.addstr(list_y + row, sb_x, char, curses.color_pair(self.BORDER_PAIR))
                except curses.error: pass

        preview_y = panel_y + panel_h - 6
        div2 = "╠" + "═" * (panel_w - 2) + "╣"
        try:
            self.stdscr.addstr(preview_y, panel_x, div2, curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        selected_name = items[self.selection_index] if items else ""
        if selected_name == "..":
            preview_path = os.path.dirname(current_path) or "/"
        else:
            preview_path = os.path.join(current_path, selected_name)
        preview_text = "→ " + self._truncate(preview_path, inner_w - 2)
        try:
            self.stdscr.addstr(preview_y + 1, panel_x + 2, preview_text.ljust(inner_w - 2), curses.color_pair(self.PANEL_HINT_PAIR))
        except curses.error: pass

        div3 = "╠" + "═" * (panel_w - 2) + "╣"
        try:
            self.stdscr.addstr(panel_y + panel_h - 4, panel_x, div3, curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass
        
        hidden_hint = ". show-hidden" if not show_hidden else ". hide-hidden"
        footer_line1 = "[↑↓ move]   [→ enter]  [← back]  [z hint]"
        footer_line2 = f" [SPC jump]   {hidden_hint}   [q quit]"
        
        try:
            self.stdscr.addstr(panel_y + panel_h - 3, panel_x + 1, footer_line1.ljust(inner_w), curses.color_pair(self.PANEL_HINT_PAIR))
            self.stdscr.addstr(panel_y + panel_h - 2, panel_x + 1, footer_line2.ljust(inner_w), curses.color_pair(self.PANEL_HINT_PAIR))
        except curses.error: pass

    def draw_jump_panel(self, jumps, confirm_delete=False):
        curses.curs_set(0)
        max_y, max_x = self.stdscr.getmaxyx()
        panel_w = min(60, max_x - 4)
        panel_h = min(18, max_y - 4)
        start_y = (max_y - panel_h) // 2
        start_x = (max_x - panel_w) // 2

        self._fill_panel_bg(start_y, start_x, panel_w, panel_h)

        try:
            self.stdscr.addstr(start_y, start_x, "╔" + "═" * (panel_w - 2) + "╗", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass
        for r in range(1, panel_h - 1):
            try:
                self.stdscr.addstr(start_y + r, start_x,             "║", curses.color_pair(self.BORDER_PAIR))
                self.stdscr.addstr(start_y + r, start_x + panel_w - 1, "║", curses.color_pair(self.BORDER_PAIR))
            except curses.error: pass
        try:
            self.stdscr.addstr(start_y + panel_h - 1, start_x, "╚" + "═" * (panel_w - 2) + "╝", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        count_str  = f"{len(jumps)} saved"
        header_left = " 📌 saved locations"
        inner_w    = panel_w - 2
        header     = header_left.ljust(inner_w - len(count_str)) + count_str
        try:
            self.stdscr.addstr(start_y + 1, start_x + 1, self._truncate(header, inner_w), curses.color_pair(self.PANEL_PAIR))
        except curses.error: pass
        try:
            self.stdscr.addstr(start_y + 2, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        if not jumps:
            try:
                self.stdscr.addstr(start_y + 4, start_x + 1, self._truncate(" No saved locations yet.", inner_w).ljust(inner_w), curses.color_pair(self.PANEL_PAIR))
                self.stdscr.addstr(start_y + 5, start_x + 1, self._truncate(" Use 'nyxx jump add' to save a location.", inner_w).ljust(inner_w), curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass

        # ── List area ──────────────────────────────────────────────────────
        list_start_row   = start_y + 3
        footer_row       = start_y + panel_h - 3   # FIX: was panel_h (off by 3)
        available_rows   = footer_row - list_start_row
        rows_per_entry   = 2
        viewport_entries = max(1, available_rows // rows_per_entry)

        # Centre scroll on selection so items above and below are always visible
        half   = viewport_entries // 2
        scroll = max(0, self.selection_index - half)
        scroll = min(scroll, max(0, len(jumps) - viewport_entries))

        for slot, ji in enumerate(range(scroll, min(scroll + viewport_entries, len(jumps)))):
            entry    = jumps[ji]
            selected = (ji == self.selection_index)
            row_y    = list_start_row + slot * rows_per_entry
            if row_y >= footer_row:
                break

            indicator = "▸ " if selected else "  "
            name_col  = curses.color_pair(self.SELECTION) if selected else curses.color_pair(self.PANEL_PAIR)
            name_str  = self._truncate(entry.get("name", ""), 12).ljust(12)
            desc_str  = self._truncate(entry.get("desc", ""), inner_w - 16)
            line1     = f"{indicator}{name_str}  {desc_str}"
            path_str  = "    " + self._truncate(entry.get("path", ""), inner_w - 4)

            try:
                fill = curses.color_pair(self.PANEL_PAIR)
                self.stdscr.addstr(row_y,     start_x + 1, " " * inner_w, name_col if selected else fill)
                self.stdscr.addstr(row_y + 1, start_x + 1, " " * inner_w, name_col if selected else fill)
                self.stdscr.addstr(row_y,     start_x + 1, self._truncate(line1, inner_w), name_col)
                self.stdscr.addstr(row_y + 1, start_x + 1, path_str.ljust(inner_w)[:inner_w],
                                   curses.color_pair(self.SELECTION) if selected else curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass

        # ── Scrollbar ──────────────────────────────────────────────────────
        if len(jumps) > viewport_entries:
            sb_x  = start_x + panel_w - 2
            bar_h = available_rows
            thumb = int(scroll / max(1, len(jumps) - viewport_entries) * (bar_h - 1))
            for i in range(bar_h):
                try:
                    self.stdscr.addstr(list_start_row + i, sb_x, "█" if i == thumb else "░", curses.color_pair(self.BORDER_PAIR))
                except curses.error: pass

        # ── Footer ─────────────────────────────────────────────────────────
        try:
            self.stdscr.addstr(footer_row, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        if confirm_delete:
            sel_name     = jumps[self.selection_index]["name"] if jumps else ""
            confirm_text = self._truncate(f" Delete '{sel_name}'?  [y] yes   [n] no", inner_w)
            try:
                self.stdscr.addstr(footer_row + 1, start_x + 1, confirm_text.ljust(inner_w)[:inner_w], curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass
        else:
            try:
                self.stdscr.addstr(footer_row + 1, start_x + 1, " ↑↓ move   Enter jump   d delete   q quit".ljust(inner_w), curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass

    def draw_memo_panel(self, memos, confirm_delete=False):
        curses.curs_set(0)
        max_y, max_x = self.stdscr.getmaxyx()
        panel_w = min(60, max_x - 4)
        panel_h = min(18, max_y - 4)
        start_y = (max_y - panel_h) // 2
        start_x = (max_x - panel_w) // 2

        self._fill_panel_bg(start_y, start_x, panel_w, panel_h)

        try:
            self.stdscr.addstr(start_y, start_x, "╔" + "═" * (panel_w - 2) + "╗", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass
        for r in range(1, panel_h - 1):
            try:
                self.stdscr.addstr(start_y + r, start_x,             "║", curses.color_pair(self.BORDER_PAIR))
                self.stdscr.addstr(start_y + r, start_x + panel_w - 1, "║", curses.color_pair(self.BORDER_PAIR))
            except curses.error: pass
        try:
            self.stdscr.addstr(start_y + panel_h - 1, start_x, "╚" + "═" * (panel_w - 2) + "╝", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        count_str   = f"{len(memos)} saved"
        header_left = " 📝 saved commands"
        inner_w     = panel_w - 2
        header      = header_left.ljust(inner_w - len(count_str)) + count_str
        try:
            self.stdscr.addstr(start_y + 1, start_x + 1, self._truncate(header, inner_w), curses.color_pair(self.PANEL_PAIR))
        except curses.error: pass
        try:
            self.stdscr.addstr(start_y + 2, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        if not memos:
            try:
                self.stdscr.addstr(start_y + 4, start_x + 1, self._truncate(" No saved commands yet.", inner_w).ljust(inner_w), curses.color_pair(self.PANEL_PAIR))
                self.stdscr.addstr(start_y + 5, start_x + 1, self._truncate(" Use 'nyxx memo add' to save a command.", inner_w).ljust(inner_w), curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass

        # ── List area ──────────────────────────────────────────────────────
        list_start_row   = start_y + 3
        footer_row       = start_y + panel_h - 3
        available_rows   = footer_row - list_start_row
        rows_per_entry   = 2
        viewport_entries = max(1, available_rows // rows_per_entry)

        # Centre scroll on selection
        half   = viewport_entries // 2
        scroll = max(0, self.selection_index - half)
        scroll = min(scroll, max(0, len(memos) - viewport_entries))

        for slot, mi in enumerate(range(scroll, min(scroll + viewport_entries, len(memos)))):
            entry    = memos[mi]
            selected = (mi == self.selection_index)
            row_y    = list_start_row + slot * rows_per_entry
            if row_y >= footer_row:
                break

            indicator = "▸ " if selected else "  "
            name_col  = curses.color_pair(self.SELECTION) if selected else curses.color_pair(self.PANEL_PAIR)
            name_str  = self._truncate(entry.get("name", ""), 12).ljust(12)
            desc_str  = self._truncate(entry.get("desc", ""), inner_w - 16)
            line1     = f"{indicator}{name_str}  {desc_str}"
            cmd_str   = "    $ " + self._truncate(entry.get("cmd", ""), inner_w - 6)

            try:
                fill = curses.color_pair(self.PANEL_PAIR)
                self.stdscr.addstr(row_y,     start_x + 1, " " * inner_w, name_col if selected else fill)
                self.stdscr.addstr(row_y + 1, start_x + 1, " " * inner_w, name_col if selected else fill)
                self.stdscr.addstr(row_y,     start_x + 1, self._truncate(line1, inner_w), name_col)
                self.stdscr.addstr(row_y + 1, start_x + 1, cmd_str.ljust(inner_w)[:inner_w],
                                   curses.color_pair(self.SELECTION) if selected else curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass

        # ── Scrollbar ──────────────────────────────────────────────────────
        if len(memos) > viewport_entries:
            sb_x  = start_x + panel_w - 2
            bar_h = available_rows
            thumb = int(scroll / max(1, len(memos) - viewport_entries) * (bar_h - 1))
            for i in range(bar_h):
                try:
                    self.stdscr.addstr(list_start_row + i, sb_x, "█" if i == thumb else "░", curses.color_pair(self.BORDER_PAIR))
                except curses.error: pass

        # ── Footer ─────────────────────────────────────────────────────────
        try:
            self.stdscr.addstr(footer_row, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        if confirm_delete:
            sel_name     = memos[self.selection_index]["name"] if memos else ""
            confirm_text = self._truncate(f" Delete '{sel_name}'?  [y] yes   [n] no", inner_w)
            try:
                self.stdscr.addstr(footer_row + 1, start_x + 1, confirm_text.ljust(inner_w)[:inner_w], curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass
        else:
            try:
                self.stdscr.addstr(footer_row + 1, start_x + 1, " ↑↓ move   Enter run   d delete   q quit".ljust(inner_w), curses.color_pair(self.PANEL_HINT_PAIR))
            except curses.error: pass

    def get_logo_lines(self):
        fig = pyfiglet.figlet_format("nyxx", font="banner3-D")
        return fig.splitlines()
        
    def draw_help_panel(self):
        max_y, max_x = self.stdscr.getmaxyx()
        curses.curs_set(0)
        panel_w = min(60, max_x - 4)
        panel_h = min(21, max_y - 4)
        start_y = (max_y - panel_h) // 2
        start_x = (max_x - panel_w) // 2
        inner_w = panel_w - 2

        self._fill_panel_bg(start_y, start_x, panel_w, panel_h)

        try:
            self.stdscr.addstr(start_y, start_x, "╔" + "═" * (panel_w - 2) + "╗", curses.color_pair(self.BORDER_PAIR))
            for r in range(1, panel_h - 1):
                self.stdscr.addstr(start_y + r, start_x, "║", curses.color_pair(self.BORDER_PAIR))
                self.stdscr.addstr(start_y + r, start_x + panel_w - 1, "║", curses.color_pair(self.BORDER_PAIR))
            self.stdscr.addstr(start_y + panel_h - 1, start_x, "╚" + "═" * (panel_w - 2) + "╝", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        header = " 💡 Nyxx Keyboard Controls"
        try:
            self.stdscr.addstr(start_y + 1, start_x + 1, header.ljust(inner_w)[:inner_w], curses.color_pair(self.PANEL_PAIR) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 2, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        help_lines = [
            ("General Navigation", ""),
            ("  ↑ / k", "Move selection row up"),
            ("  ↓ / j", "Move selection row down"),
            ("  ← / h / Back", "Go back / return to Home dashboard"),
            ("  z", "Toggle this Help menu info"),
            ("  q / Esc", "Quit application fully"),
            ("", ""),
            ("Directory Browser (cd)", ""),
            ("  → / l / Enter", "Enter highlighted folder branch"),
            ("  Space", "Confirm pick & change shell directory"),
            ("  .", "Toggle visibility of hidden dotfiles"),
            ("", ""),
            ("Saved Jumps & Memos", ""),
            ("  Enter", "Trigger saved branch/command sequence"),
            ("  d", "Delete custom item (requires confirm)"),
            ("", ""),
            ("Theme Customizer", ""),
            ("  Tab", "Cycle categories (Backgrounds, Toggles, Panels)"),
            ("  Enter", "Apply selected option block"),
        ]

        curr_row = start_y + 3
        for title, desc in help_lines:
            if curr_row >= start_y + panel_h - 2: break
            if not title and not desc:
                curr_row += 1
                continue
            
            try:
                self.stdscr.addstr(curr_row, start_x + 1, " " * inner_w, curses.color_pair(self.PANEL_PAIR))
                if desc == "":
                    self.stdscr.addstr(curr_row, start_x + 2, title.ljust(inner_w - 2)[:inner_w - 2], curses.color_pair(self.PANEL_PAIR) | curses.A_UNDERLINE)
                else:
                    self.stdscr.addstr(curr_row, start_x + 3, title, curses.color_pair(self.PANEL_HINT_PAIR))
                    self.stdscr.addstr(curr_row, start_x + 20, desc.ljust(inner_w - 20)[:inner_w - 20], curses.color_pair(self.PANEL_PAIR))
            except curses.error: pass
            curr_row += 1

        footer_row = start_y + panel_h - 2
        try:
            self.stdscr.addstr(footer_row, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
            footer_text = " Press any key to close help overlay..."
            self.stdscr.addstr(footer_row + 1, start_x + 1, footer_text.ljust(inner_w)[:inner_w], curses.color_pair(self.PANEL_HINT_PAIR))
        except curses.error: pass

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

    def draw_theme_panel(self, ui_themes, active_ui, logo_enabled=True, scene_names=None, active_scene=None, mode="scenes"):
        if scene_names is None: scene_names = []
        if active_scene is None: active_scene = ""
        curses.curs_set(0)
        max_y, max_x = self.stdscr.getmaxyx()
        panel_w = min(60, max_x - 4)
        panel_h = min(18, max_y - 4)
        start_y = (max_y - panel_h) // 2
        start_x = (max_x - panel_w) // 2
        inner_w = panel_w - 2

        self._fill_panel_bg(start_y, start_x, panel_w, panel_h)

        tabs = [("scenes", "⟡ Backgrounds ⟡"), ("toggles", "⟡ Toggles ⟡"), ("ui", "⟡ Panels ⟡")]

        tab_x = start_x + 2
        for key, label in tabs:
            attr = curses.color_pair(self.SELECTION) if mode == key else curses.color_pair(self.PANEL_PAIR)
            try:
                self.stdscr.addstr(start_y + 1, tab_x, label, attr)
            except curses.error: pass
            tab_x += len(label) + 2

        try:
            self.stdscr.addstr(start_y + 1, start_x + panel_w - 1, " ")
        except curses.error: pass

        try:
            self.stdscr.addstr(start_y, start_x, "╔" + "═" * (panel_w - 2) + "╗", curses.color_pair(self.BORDER_PAIR))
            for r in range(1, panel_h ):
                self.stdscr.addstr(start_y + r, start_x, "║", curses.color_pair(self.BORDER_PAIR))
                self.stdscr.addstr(start_y + r, start_x + panel_w - 1, "║", curses.color_pair(self.BORDER_PAIR))
            self.stdscr.addstr(start_y + panel_h - 1, start_x, "╚" + "═" * (panel_w - 2) + "╝", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        try:
            self.stdscr.addstr(start_y + 2, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
        except curses.error: pass

        list_start  = start_y + 3
        footer_row  = start_y + panel_h - 3

        if mode == "scenes":

            visible_rows = footer_row - list_start
            start = 0

            if self.selection_index >= visible_rows:
                start = self.selection_index - visible_rows + 1

            visible = scene_names[start:start + visible_rows]

            for i, name in enumerate(visible):

                real_index = start + i
                row_y = list_start + i

                selected = (real_index == self.selection_index)
                active = (name == active_scene)

                indicator = "▸ " if selected else "  "
                marker = " ✓" if active else "  "

                line = self._truncate(
                    f"{indicator}{name}{marker}",
                    inner_w
                )

                attr = (
                    curses.color_pair(self.SELECTION)
                    if selected
                    else curses.color_pair(self.PANEL_PAIR)
                )

                try:
                    self.stdscr.addstr(
                        row_y,
                        start_x + 1,
                        line.ljust(inner_w)[:inner_w],
                        attr,
                    )
                except curses.error:
                    pass

        elif mode == "ui":

            visible_rows = footer_row - list_start
            start = 0

            if self.selection_index >= visible_rows:
                start = self.selection_index - visible_rows + 1

            visible = ui_themes[start:start + visible_rows]

            for i, name in enumerate(visible):

                real_index = start + i
                row_y = list_start + i

                selected = (real_index == self.selection_index)
                active = (name == active_ui)

                indicator = "▸ " if selected else "  "
                marker = " ✓" if active else "  "

                line = self._truncate(
                    f"{indicator}{name}{marker}",
                    inner_w
                )

                attr = (
                    curses.color_pair(self.SELECTION)
                    if selected
                    else curses.color_pair(self.PANEL_PAIR)
                )

                try:
                    self.stdscr.addstr(
                        row_y,
                        start_x + 1,
                        line.ljust(inner_w)[:inner_w],
                        attr,
                    )
                except curses.error:
                    pass

        elif mode == "toggles":
            toggles = [
                ("Home logo",         logo_enabled),
                ("Panel Bg color",    config_get("panel_color")),
                ("Text color",        config_get("text_color")),
                ("Highlight Bg",      config_get("highlight_panel_color")),
                ("Highlight Text",    config_get("highlight_text_color")),
                ("Border Fg color",   config_get("border_fg")),
                ("Border Bg color",   config_get("border_bg")),
            ]
            for i, (label, val) in enumerate(toggles):
                row_y = list_start + i
                if row_y >= footer_row: break
                selected  = (i == self.selection_index)
                indicator = "▸ " if selected else "  "
                
                status = f"[ON] " if val is True else f"[OFF]" if val is False else f"[{val}]"
                line = self._truncate(f"{indicator}{label:<16}  {status}", inner_w)
                
                attr = curses.color_pair(self.SELECTION) if selected else curses.color_pair(self.PANEL_PAIR)
                try:
                    self.stdscr.addstr(row_y, start_x + 1, line.ljust(inner_w)[:inner_w], attr)
                except curses.error: pass
                
        try:
            self.stdscr.addstr(footer_row, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(self.BORDER_PAIR))
            footer = "[Tab: switch tab] [⇅⇆: move] [Enter: select] [Esc: back]"
            self.stdscr.addstr(footer_row + 1 , start_x + 1, footer.ljust(inner_w), curses.color_pair(self.PANEL_HINT_PAIR))
        except curses.error: pass
        
        if getattr(self, "error_message", None):
                self.stdscr.addstr(max_y - 2, 0, f" Error: {self.error_message} ".ljust(max_x), curses.color_pair(self.YELLOW) | curses.A_BOLD)
                
    def draw_home(self, items, logo_enabled=True):
        curses.curs_set(0)
        if logo_enabled:
            logo_lines = self.get_logo_lines()
            logo_colors = [self.PANEL_PAIR] * len(logo_lines)
            for i in range(len(logo_lines)):
                if i < len(logo_lines) // 3:
                    logo_colors[i] = curses.color_pair(self.PANEL_PAIR) | curses.A_DIM
                elif i < (len(logo_lines) * 2) // 3:
                    logo_colors[i] = curses.color_pair(self.BORDER_PAIR)
                else:
                    logo_colors[i] = curses.color_pair(self.BORDER_PAIR) | curses.A_BOLD

            logo_width = max(len(l) for l in logo_lines) if logo_lines else 0
            logo_start_x = max(0, (self.max_x - logo_width) // 2)
            logo_start_y = max(0, (self.max_y // 2) - len(logo_lines) - 6)

            for i, line in enumerate(logo_lines):
                try:
                    self.stdscr.addstr(logo_start_y + i, logo_start_x, line, logo_colors[i])
                except curses.error: pass

        menu_lines = []
        for i, item in enumerate(items):
            parts = item.split(" - ", 1)
            name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            prefix = "⫸ " if i == self.selection_index else "  "
            menu_lines.append(f"{prefix}{name:<8}  {desc}")

        footer_lines = ["↑↓:Navigate  z:Help  Enter:Select  q:Quit"]
        panel_y, panel_x, panel_w = self.draw_panel(menu_lines, footer_lines)

        padding_x = 4
        selected_row = panel_y + 2 + self.selection_index  
        selected_line = menu_lines[self.selection_index]
        try:
            self.stdscr.addstr(selected_row, panel_x + padding_x + 1, selected_line, curses.color_pair(self.SELECTION))
        except curses.error: pass

    def draw_ui(self, current_path, items, logo_enabled=True):
        curses.curs_set(0)
        if current_path == "Navii Home":
            self.draw_home(items, logo_enabled=logo_enabled)
            return

        self.stdscr.addstr(0, 0, current_path, curses.color_pair(self.PANEL_PAIR))
        self.draw_list(items, start_row=1)
        footer_text = "↑↓ Navigate  Enter Open  ← Back  q Quit"
        try:
            self.stdscr.addstr(self.max_y - 1, 0, footer_text, curses.color_pair(self.YELLOW))
        except curses.error: pass
        if self.error_message:
            try:
                self.stdscr.addstr(self.max_y - 2, 0, f"Error: {self.error_message}", curses.color_pair(self.YELLOW))
            except curses.error: pass