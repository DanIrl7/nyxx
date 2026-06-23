import curses
import pyfiglet

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

        # Top border
        try:
            self.stdscr.addstr(start_y, start_x, '┌' + '─' * (box_width - 2) + '┐', color)
        except curses.error:
            pass

        # Content rows
        for i, line in enumerate(lines):
            row = start_y + 1 + padding_y + i
            try:
                self.stdscr.addstr(row, start_x, '│', color)
                self.stdscr.addstr(row, start_x + padding_x + 1, line, curses.color_pair(self.WHITE))
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
                try:
                    self.stdscr.addstr(row, start_x, '│', color)
                    self.stdscr.addstr(row, start_x + padding_x + 1, line, curses.color_pair(self.YELLOW))
                    self.stdscr.addstr(row, start_x + box_width - 1, '│', color)
                except curses.error:
                    pass

        # Bottom border
        bottom_row = start_y + box_height - 1
        try:
            self.stdscr.addstr(bottom_row, start_x, '└' + '─' * (box_width - 2) + '┘', color)
        except curses.error:
            pass

        return start_y, start_x, box_width  # return position so we can draw menu items over it

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


