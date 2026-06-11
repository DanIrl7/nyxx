import curses
import sys
from .ui import UIEngine
from .navigator import Navigator

def main(stdscr):
    # Initialize UIEngine and Navigator
    ui = UIEngine()
    navigator = Navigator() # Starts at home directory

    running = True
    while running:
        # 1. Get current path and items from Navigator
        current_path = navigator.get_current_path()
        list_result = navigator.list_items()

        if not list_result["success"]:
            # Handle error (e.g., permission denied)
            # For now, let's just quit or show an error
            # TODO: Improve error display in UI
            ui.cleanup()
            print(f"Error: {list_result['error']}", file=sys.stderr)
            sys.exit(1)
        
        items = list_result["items"]
        
        # 2. Draw the UI
        ui.draw_ui(current_path, items)
        
        # 3. Get user input
        action = ui.get_input()
        
        # 4. Process input
        if action == "quit":
            running = False
        elif action == "up":
            ui.move_selection("up", len(items))
        elif action == "down":
            ui.move_selection("down", len(items))
        elif action == "enter":
            if items: # Only try to go forward if there are items to select
                selected_item = items[ui.selection_index]
                nav_result = navigator.go_forward(selected_item)
                if nav_result["success"]:
                    # Reset selection and scroll when entering new directory
                    ui.selection_index = 0
                    ui.scroll_position = 0
                else:
                    # TODO: Display nav_result["error"] in UI
                    pass
            # TODO: Handle "confirm" action to output path and exit
            pass
        elif action == "back":
            nav_result = navigator.go_back()
            if nav_result["success"]:
                # Reset selection and scroll when going back
                ui.selection_index = 0
                ui.scroll_position = 0
            else:
                # TODO: Display nav_result["error"] in UI
                pass


    ui.cleanup()

if __name__ == "__main__":
    curses.wrapper(main)
