import curses

class UIEngine:
    def __init__(self):
        # ESSENTIAL - Curses setup
        self.stdscr = curses.initscr()
        
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
        if key == curses.KEY_UP or key == ord("k"):
            return "up"
        # Down
        elif key == curses.KEY_DOWN or key == ord("j"):
            return "down"
        # Left / Go back
        elif key == curses.KEY_LEFT or key == ord("h") or key == curses.KEY_BACKSPACE or key == ord('\b'):
            return "back"
        # Right / Enter directory
        elif key == curses.KEY_RIGHT or key == ord("l") or key == ord('\n'):
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

    def draw_ui(self, current_path, items):
        self.stdscr.clear()

        # Draw header: Current Path
        self.stdscr.addstr(0, 0, current_path, curses.color_pair(self.CYAN))

        # LIST ITEMS
        self.draw_list(items, start_row=1)

        # Footer: Keybindings
        footer_text = "↑↓: Navigate | Enter: Open | q: Quit"
        self.stdscr.addstr(self.max_y - 1, 0, footer_text, curses.color_pair(self.YELLOW))
    
        self.refresh()

