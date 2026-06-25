import curses
import pyfiglet
import os

class UIEngine:
    def __init__(self, stdscr):
        # ESSENTIAL - Curses setup
        self.stdscr = stdscr
        
        # ESSENTIAL - Terminal info
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
        # ESSENTIAL - Colors
        curses.start_color()
        self.WHITE = 1
        self.CYAN = 2
        self.YELLOW = 3
        curses.init_pair(self.WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(self.CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(self.YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        
        # ESSENTIAL - Terminal settings
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        self.selection_index = 0
        self.scroll_position = 0

        self.SELECTION = 4
        curses.init_pair(self.SELECTION, curses.COLOR_BLACK, curses.COLOR_CYAN)

        # Background color pairs (used by BackgroundEngine)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)   # bright stars
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)    # mid stars
        curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_BLACK)    # dim stars
        curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_BLUE)   # city silhouette
        curses.init_pair(9, curses.COLOR_BLUE, curses.COLOR_BLACK)    # horizon glow
        curses.init_pair(10, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warm window light
        curses.init_pair(11, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Bright white office light
        curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_BLACK) # Block character in menu 

        self.error_message = None

    def cleanup(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def refresh(self):
        self.stdscr.refresh()
    
    def map_key(self, key):
        # CONVERTS USER KEY INPUT INTO ACTION 
        # Up
        if key == curses.KEY_UP or key == ord("k") or key == 450:
            return "up"
        # Down
        elif key == curses.KEY_DOWN or key == ord("j") or key == 456:
            return "down"
        # Left / Go back
        elif key == curses.KEY_LEFT or key == ord("h") or key == curses.KEY_BACKSPACE or key == ord('\b') or key == 452:
            return "back"
        # Right / Enter directory
        elif key == curses.KEY_RIGHT or key == ord("l") or key == ord('\n') or key == 454:
            return "enter"
        # Confirm selection
        elif key == ord(' '):
            return "confirm"
        # Toggle hidden files
        elif key == ord('.'):
            return "toggle_hidden"
        # Quit
        elif key == 27 or key == ord('q'):
            return "quit"
        elif key == curses.KEY_RESIZE:
            return "resize"
        elif key == ord('d'):
            return "delete"
        else:
            return None  # Unknown key
        

    def get_input(self):
        # GET INPUT AND RETURN ACTION NAME
        key = self.stdscr.getch()
        return self.map_key(key)
    
    def move_selection(self, direction, total_items):
        """Move selection up/down and auto-scroll to keep it visible"""
        if direction == "down":
            self.selection_index = min(self.selection_index + 1, total_items - 1)
        elif direction == "up":
            self.selection_index = max(self.selection_index - 1,0)
        # Auto-scroll to keep selection visible
        viewport_height = self.max_y - 3  # Account for header/footer
        self.scroll_position = max(0, self.selection_index - viewport_height // 2)

    def draw_list(self, items, start_row=1):
        """Draw list of items with selection highlight"""
        viewport_height = self.max_y - 3
    
        for i, item in enumerate(items[self.scroll_position:self.scroll_position + viewport_height]):
            row = start_row + i
            if self.scroll_position + i == self.selection_index:
                self.stdscr.addstr(row, 0, item, curses.color_pair(self.SELECTION))
            else:
                self.stdscr.addstr(row, 0, item, curses.color_pair(self.WHITE))

    
    def _truncate(self, text, max_width):
        """Truncate text with … if it exceeds max_width."""
        if len(text) > max_width:
            return text[:max_width - 1] + "…"
        return text

    def draw_cd_panel(self, current_path, items, full_paths, show_hidden):
        """
        Draw the CD navigator panel:
          - Header with current path
          - Scrollable list with icons
          - Preview line (selected item's full path)
          - Footer with keybindings
          - Scrollbar indicator on the right
        
        full_paths: list of absolute paths parallel to items, used for icons
        show_hidden: bool, shown in footer hint
        """
        from .icons import get_icon

        max_y, max_x = self.stdscr.getmaxyx()

        # Panel dimensions
        panel_w = min(60, max_x - 4)
        panel_h = min(22, max_y - 4)
        panel_x = (max_x - panel_w) // 2
        panel_y = (max_y - panel_h) // 2

        # ── Box ─────────────────────────────────────────────────────────────
        # Top border
        top = "┌" + "─" * (panel_w - 2) + "┐"
        try:
            self.stdscr.addstr(panel_y, panel_x, top, curses.color_pair(self.CYAN))
        except curses.error:
            pass

        # Side borders + blank fill
        for row in range(1, panel_h - 1):
            try:
                self.stdscr.addstr(panel_y + row, panel_x,     "│", curses.color_pair(self.CYAN))
                self.stdscr.addstr(panel_y + row, panel_x + panel_w - 1, "│", curses.color_pair(self.CYAN))
            except curses.error:
                pass

        # Bottom border
        bot = "└" + "─" * (panel_w - 2) + "┘"
        try:
            self.stdscr.addstr(panel_y + panel_h - 1, panel_x, bot, curses.color_pair(self.CYAN))
        except curses.error:
            pass

        # ── Header ──────────────────────────────────────────────────────────
        inner_w = panel_w - 4          # 2 for borders + 1 pad each side
        header = "📂 " + self._truncate(current_path, inner_w - 3)
        try:
            self.stdscr.addstr(panel_y + 1, panel_x + 2, header, curses.color_pair(self.CYAN) | curses.A_BOLD)
        except curses.error:
            pass

        # Divider under header
        div = "├" + "─" * (panel_w - 2) + "┤"
        try:
            self.stdscr.addstr(panel_y + 2, panel_x, div, curses.color_pair(self.CYAN))
        except curses.error:
            pass

        # ── List area ───────────────────────────────────────────────────────
        # Rows available: panel_h - top(1) - header(1) - hdiv(1) - preview(1) - fdiv(1) - footer(1) - bottom(1) = panel_h - 7
        list_rows = panel_h - 7
        list_y    = panel_y + 3

        # Auto-scroll
        half = list_rows // 2
        scroll = max(0, min(self.selection_index - half, len(items) - list_rows))

        visible = items[scroll:scroll + list_rows]
        visible_paths = full_paths[scroll:scroll + list_rows]

        for i, (name, fpath) in enumerate(zip(visible, visible_paths)):
            abs_idx = scroll + i
            selected = abs_idx == self.selection_index

            icon = get_icon(fpath)
            # Emoji chars are double-width — place at even column, text at +3
            # Use a space placeholder for the icon column to avoid alignment issues
            icon_col  = panel_x + 2
            arrow_col = panel_x + 4
            name_col  = panel_x + 6

            max_name = panel_w - 8   # leave room for icon + arrow + right border + scrollbar
            display_name = self._truncate(name, max_name)

            row_y = list_y + i
            if row_y >= panel_y + panel_h - 4:
                break

            if selected:
                attr = curses.color_pair(self.SELECTION)
                # Fill the whole row for highlight
                blank = " " * (panel_w - 2)
                try:
                    self.stdscr.addstr(row_y, panel_x + 1, blank, attr)
                except curses.error:
                    pass
                try:
                    self.stdscr.addstr(row_y, icon_col,  " ",           attr)
                    self.stdscr.addstr(row_y, arrow_col, "▸",           attr)
                    self.stdscr.addstr(row_y, name_col,  display_name,  attr)
                except curses.error:
                    pass
            else:
                attr = curses.color_pair(self.WHITE)
                try:
                    self.stdscr.addstr(row_y, icon_col,  " ",           attr)
                    self.stdscr.addstr(row_y, arrow_col, " ",           attr)
                    self.stdscr.addstr(row_y, name_col,  display_name,  attr)
                except curses.error:
                    pass

        # ── Scrollbar ───────────────────────────────────────────────────────
        if len(items) > list_rows:
            sb_x = panel_x + panel_w - 2
            bar_h = list_rows
            thumb_pos = int(scroll / max(1, len(items) - list_rows) * (bar_h - 1))
            for row in range(bar_h):
                char = "█" if row == thumb_pos else "░"
                try:
                    self.stdscr.addstr(list_y + row, sb_x, char, curses.color_pair(self.CYAN))
                except curses.error:
                    pass

        # ── Preview line ────────────────────────────────────────────────────
        preview_y = panel_y + panel_h - 4
        div2 = "├" + "─" * (panel_w - 2) + "┤"
        try:
            self.stdscr.addstr(preview_y, panel_x, div2, curses.color_pair(self.CYAN))
        except curses.error:
            pass

        selected_name = items[self.selection_index] if items else ""
        if selected_name == "..":
            preview_path = os.path.dirname(current_path) or "/"
        else:
            preview_path = os.path.join(current_path, selected_name)
        preview_text = "→ " + self._truncate(preview_path, inner_w - 2)
        try:
            self.stdscr.addstr(preview_y + 1, panel_x + 2, preview_text, curses.color_pair(self.YELLOW))
        except curses.error:
            pass

        # ── Footer ──────────────────────────────────────────────────────────
        div3 = "├" + "─" * (panel_w - 2) + "┤"
        try:
            self.stdscr.addstr(panel_y + panel_h - 2, panel_x, div3, curses.color_pair(self.CYAN))
        except curses.error:
            pass

        hidden_hint = ". show-hidden" if not show_hidden else ". hide-hidden"
        footer = f"↑↓ move  → enter  ← back  SPC jump  {hidden_hint}  q quit"
        footer = self._truncate(footer, inner_w)
        try:
            self.stdscr.addstr(panel_y + panel_h - 1, panel_x + 1,
                               footer, curses.color_pair(self.YELLOW))
        except curses.error:
            pass

    
    def draw_jump_panel(self, jumps, confirm_delete=False):
        """
        Draw the Jump module panel.
        jumps         — list of dicts: {name, desc, path}
        confirm_delete — if True, show y/n confirmation row instead of footer
        """
        max_y, max_x = self.stdscr.getmaxyx()

        # ── Panel dimensions ───────────────────────────────────
        panel_w = min(60, max_x - 4)
        panel_h = min(18, max_y - 4)
        start_y = (max_y - panel_h) // 2
        start_x = (max_x - panel_w) // 2

        # ── Box border ─────────────────────────────────────────
        # Top edge
        try:
            self.stdscr.addstr(start_y, start_x,
                "┌" + "─" * (panel_w - 2) + "┐",
                curses.color_pair(self.CYAN))
        except curses.error:
            pass
        # Side edges + interior
        for r in range(1, panel_h - 1):
            try:
                self.stdscr.addstr(start_y + r, start_x, "│", curses.color_pair(self.CYAN))
                self.stdscr.addstr(start_y + r, start_x + panel_w - 1, "│", curses.color_pair(self.CYAN))
            except curses.error:
                pass
        # Bottom edge
        try:
            self.stdscr.addstr(start_y + panel_h - 1, start_x,
                "└" + "─" * (panel_w - 2) + "┘",
                curses.color_pair(self.CYAN))
        except curses.error:
            pass

        # ── Header ─────────────────────────────────────────────
        count_str = f"{len(jumps)} saved"
        header_left = " 📌 saved locations"
        # Truncate if needed, then pad to align count on right
        inner_w = panel_w - 2
        header = header_left.ljust(inner_w - len(count_str)) + count_str
        header = self._truncate(header, inner_w)
        try:
            self.stdscr.addstr(start_y + 1, start_x + 1, header, curses.color_pair(self.CYAN))
        except curses.error:
            pass

        # Divider below header
        try:
            self.stdscr.addstr(start_y + 2, start_x,
                "├" + "─" * (panel_w - 2) + "┤",
                curses.color_pair(self.CYAN))
        except curses.error:
            pass

        # ── Empty state ────────────────────────────────────────
        if not jumps:
            empty = " No saved locations yet."
            try:
                self.stdscr.addstr(start_y + 4, start_x + 1,
                    self._truncate(empty, inner_w),
                    curses.color_pair(self.WHITE))
            except curses.error:
                pass
            hint = " Use 'navi jump add' to save a location."
            try:
                self.stdscr.addstr(start_y + 5, start_x + 1,
                    self._truncate(hint, inner_w),
                    curses.color_pair(self.YELLOW))
            except curses.error:
                pass

        # ── List rows ──────────────────────────────────────────
        # Each jump takes 2 rows: name+desc line, then indented path line
        # So viewport fits (panel_h - 6) // 2 entries  (header=2, divider=1, footer=2, bottom=1)
        list_start_row = start_y + 3
        footer_row     = start_y + panel_h - 3
        available_rows = footer_row - list_start_row          # rows available for list
        rows_per_entry = 2
        viewport_entries = max(1, available_rows // rows_per_entry)

        # Clamp scroll so selection stays visible
        scroll = max(0, self.selection_index - (viewport_entries - 1))
        scroll = min(scroll, max(0, len(jumps) - viewport_entries))

        for slot, ji in enumerate(range(scroll, min(scroll + viewport_entries, len(jumps)))):
            entry = jumps[ji]
            selected = (ji == self.selection_index)
            row_y = list_start_row + slot * rows_per_entry

            if row_y >= footer_row:
                break

            # Row 1: ▸ indicator + name (bold/highlight) + description
            indicator = "▸ " if selected else "  "
            name_col  = curses.color_pair(self.SELECTION) if selected else curses.color_pair(self.WHITE)
            desc_col  = curses.color_pair(self.CYAN) if selected else curses.color_pair(self.WHITE)

            name_str = self._truncate(entry.get("name", ""), 12).ljust(12)
            desc_str = self._truncate(entry.get("desc", ""), inner_w - 16)
            line1 = f"{indicator}{name_str}  {desc_str}"
            try:
                self.stdscr.addstr(row_y, start_x + 1,
                    self._truncate(line1, inner_w), name_col)
            except curses.error:
                pass

            # Row 2: indented path (dimmer)
            if row_y + 1 < footer_row:
                path_str = "    " + self._truncate(entry.get("path", ""), inner_w - 4)
                try:
                    self.stdscr.addstr(row_y + 1, start_x + 1,
                        path_str.ljust(inner_w)[:inner_w],
                        curses.color_pair(self.YELLOW))
                except curses.error:
                    pass

        # ── Divider above footer ───────────────────────────────
        try:
            self.stdscr.addstr(footer_row, start_x,
                "├" + "─" * (panel_w - 2) + "┤",
                curses.color_pair(self.CYAN))
        except curses.error:
            pass

        # ── Footer / confirmation ──────────────────────────────
        if confirm_delete:
            sel_name = jumps[self.selection_index]["name"] if jumps else ""
            confirm_text = self._truncate(
                f" Delete '{sel_name}'?  [y] yes   [n] no",
                inner_w)
            try:
                self.stdscr.addstr(footer_row + 1, start_x + 1,
                    confirm_text.ljust(inner_w)[:inner_w],
                    curses.color_pair(self.YELLOW))
            except curses.error:
                pass
        else:
            footer = " ↑↓ move   Enter jump   d delete   q quit"
            try:
                self.stdscr.addstr(footer_row + 1, start_x + 1,
                    self._truncate(footer, inner_w),
                    curses.color_pair(self.YELLOW))
            except curses.error:
                pass
    
    def get_logo_lines(self):
        fig = pyfiglet.figlet_format("navii", font="banner3-D")
        return fig.splitlines()

    def draw_panel(self, lines, footer_lines=None):
        """Draw a centered panel box with content lines and optional footer"""
        padding_x = 3
        padding_y = 1

        # Find the widest line to size the box
        all_lines = lines + (footer_lines or [])
        content_width = max(len(l) for l in all_lines) if all_lines else 20
        box_width = content_width + (padding_x * 2) + 2  # +2 for borders
        box_height = len(lines) + (len(footer_lines) if footer_lines else 0) + (padding_y * 2) + 2

        # Center on screen
        start_y = (self.max_y - box_height) // 2
        start_x = (self.max_x - box_width) // 2

        # Clamp to screen bounds
        start_y = max(0, start_y)
        start_x = max(0, start_x)

        color = curses.color_pair(self.CYAN)
        black_bg = curses.color_pair(self.WHITE)  # Uses pair 1, which has a black background

        # Top border
        try:
            self.stdscr.addstr(start_y, start_x, '┌' + '─' * (box_width - 2) + '┐', color)
        except curses.error:
            pass

        # --- NEW: Fill the empty vertical padding space at the top ---
        for y_offset in range(1, padding_y + 1):
            try:
                self.stdscr.addstr(start_y + y_offset, start_x, '│', color)
                self.stdscr.addstr(start_y + y_offset, start_x + 1, ' ' * (box_width - 2), black_bg)
                self.stdscr.addstr(start_y + y_offset, start_x + box_width - 1, '│', color)
            except curses.error:
                pass

        # Content rows (Now padded with explicit black background spacing)
        for i, line in enumerate(lines):
            row = start_y + 1 + padding_y + i
            # Calculate left and right empty spaces to perfectly pad the line
            left_spaces = ' ' * (padding_x + 1)
            right_spaces = ' ' * (box_width - 2 - len(left_spaces) - len(line))
            try:
                self.stdscr.addstr(row, start_x, '│', color)
                self.stdscr.addstr(row, start_x + 1, left_spaces, black_bg)
                self.stdscr.addstr(row, start_x + 1 + len(left_spaces), line, black_bg)
                self.stdscr.addstr(row, start_x + 1 + len(left_spaces) + len(line), right_spaces, black_bg)
                self.stdscr.addstr(row, start_x + box_width - 1, '│', color)
            except curses.error:
                pass

        # Footer divider + lines
        if footer_lines:
            divider_row = start_y + 1 + padding_y + len(lines)
            try:
                self.stdscr.addstr(divider_row, start_x, '├' + '─' * (box_width - 2) + '┤', color)
            except curses.error:
                pass
            for i, line in enumerate(footer_lines):
                row = divider_row + 1 + i
                left_spaces = ' ' * (padding_x + 1)
                right_spaces = ' ' * (box_width - 2 - len(left_spaces) - len(line))
                try:
                    self.stdscr.addstr(row, start_x, '│', color)
                    self.stdscr.addstr(row, start_x + 1, left_spaces, black_bg)
                    self.stdscr.addstr(row, start_x + 1 + len(left_spaces), line, curses.color_pair(self.YELLOW))
                    self.stdscr.addstr(row, start_x + 1 + len(left_spaces) + len(line), right_spaces, black_bg)
                    self.stdscr.addstr(row, start_x + box_width - 1, '│', color)
                except curses.error:
                    pass

        # Bottom border
        bottom_row = start_y + box_height - 1
        try:
            self.stdscr.addstr(bottom_row, start_x, '└' + '─' * (box_width - 2) + '┘', color)
        except curses.error:
            pass

        return start_y, start_x, box_width

    def draw_home(self, items):
        """Draw the full home screen — logo + menu panel"""

        # --- Logo ---
        logo_lines = self.get_logo_lines()

        # Apply a color gradient — top rows dimmer, bottom rows brighter
        logo_colors = [self.WHITE] * len(logo_lines)
        for i in range(len(logo_lines)):
            if i < len(logo_lines) // 3:
                logo_colors[i] = curses.color_pair(self.WHITE) | curses.A_DIM
            elif i < (len(logo_lines) * 2) // 3:
                logo_colors[i] = curses.color_pair(self.CYAN)
            else:
                logo_colors[i] = curses.color_pair(self.CYAN) | curses.A_BOLD

        # Center and draw logo above the panel
        logo_width = max(len(l) for l in logo_lines) if logo_lines else 0
        logo_start_x = max(0, (self.max_x - logo_width) // 2)
        logo_start_y = max(0, (self.max_y // 2) - len(logo_lines) - 6)

        for i, line in enumerate(logo_lines):
            try:
                self.stdscr.addstr(logo_start_y + i, logo_start_x, line, logo_colors[i])
            except curses.error:
                pass

        # --- Menu panel ---
        menu_lines = []
        for i, item in enumerate(items):
            # Split "cd - Directory Navigator" into icon+name and description
            parts = item.split(" - ", 1)
            name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            prefix = "▸ " if i == self.selection_index else "  "
            menu_lines.append(f"{prefix}{name:<8}  {desc}")

        footer_lines = ["↑↓ Navigate   Enter Select   q Quit"]

        # Draw the panel — we get back the position to overlay selection highlight
        panel_y, panel_x, panel_w = self.draw_panel(menu_lines, footer_lines)

        # Re-draw the selected row with highlight color on top
        padding_x = 3
        selected_row = panel_y + 2 + self.selection_index  # +2 = border + padding
        selected_line = menu_lines[self.selection_index]
        try:
            self.stdscr.addstr(selected_row, panel_x + padding_x + 1, selected_line, curses.color_pair(self.SELECTION))
        except curses.error:
            pass

    def draw_ui(self, current_path, items):

        if current_path == "Navii Home":
            self.draw_home(items)  # <-- use the new home screen draw
            return                 # <-- skip the rest

        # Draw header: Current Path
        self.stdscr.addstr(0, 0, current_path, curses.color_pair(self.CYAN))

        # LIST ITEMS
        self.draw_list(items, start_row=1)

        # Footer: Keybindings
        footer_text = "↑↓/[k][j]: Navigate | Enter[l]: Open | ⌫ Backspace: Go Back | q: Quit"
        try:
            self.stdscr.addstr(self.max_y - 1, 0, footer_text, curses.color_pair(self.YELLOW))
        except curses.error:
            pass

        if self.error_message:
            self.stdscr.addstr(self.max_y - 2, 0, f"Error: {self.error_message}", curses.color_pair(self.YELLOW))


