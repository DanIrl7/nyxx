import curses
import os
import sys
import argparse
from .ui import UIEngine
from .navigator import Navigator
from .background import BackgroundEngine
from .pathhandler import PathHandler

def parse_arguments():
    if len(sys.argv) < 2:
        return {"action": "ui", "state": "home"}

    subcommand = sys.argv[1]

    if subcommand == "cd":
        return {"action": "ui", "state": "nav"}
    elif subcommand == "jump":
        if len(sys.argv) == 2:
            return {"action": "ui", "state": "jump"}
        elif sys.argv[2] == "add":
            return {"action": "jump_add"}
        else:
            return {"action": "jump_lookup", "name": sys.argv[2]}
            
    elif subcommand == "memo":
        if len(sys.argv) == 2:
            return {"action": "ui", "state": "memo"}
        elif sys.argv[2] == "add":
            return {"action": "memo_add"}
        else:
            return {"action": "memo_lookup", "name": sys.argv[2]}
            
    # Default to UI home screen for unknown commands
    return {"action": "ui", "state": "home"}

def run_cli(args):
    # Logic for CLI commands (jump/memo)
    # No curses.wrapper here
    print(f"Executing {args['action']}...")
    sys.exit(0)

def run_tui(args):
    # Launch TUI
    curses.wrapper(lambda stdscr: main(stdscr, initial_state=args["state"]))

def main_entry():
    # This is the single entry point
    args = parse_arguments()
    
    if args["action"] == "ui":
        run_tui(args)
    else:
        run_cli(args)

if __name__ == "__main__":
    main_entry()


def main(stdscr):
    """
    Main controller loop for Navii.
    Manages application state ('home' vs 'nav') and coordinates 
    input between the UIEngine and the Navigator.
    """
    PathHandler.initialize_storage()
    ui = UIEngine(stdscr)
    bg_engine = BackgroundEngine(stdscr)
    navigator = Navigator()

    state = "home"
    running = True

    while running:
        # 1. State Logic
        if state == "home":
            items = ["cd - Directory Navigator", "jump - Saved Locations", "memo - Saved Commands"]
            current_path = "Navii Home"
        else:
            nav_data = navigator.list_items()
            items = nav_data["items"]
            current_path = navigator.get_current_path()
            ui.error_message = None if nav_data["success"] else nav_data["error"]

        # 2. Rendering (Layered)
        stdscr.clear()
        bg_engine.draw()      # Background
        ui.draw_ui(current_path, items) # Foreground (use current_path, not path)
        stdscr.refresh()
        
        # 3. Input Handling
        # ui.get_input() inside uses stdscr.getch()
        action = ui.get_input()
        
        # Check for resize specifically
        if action == "resize": 
            # Logic to handle resize signal
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            continue # Skip processing until next redraw
        if action == "quit":
            running = False
        
        elif state == "home":
            if action in ["up", "down"]:
                ui.move_selection(action, len(items))
            elif action == "enter":
                selection = items[ui.selection_index]
                if "cd" in selection:
                    state = "nav"
                    ui.selection_index = 0
            
        elif state == "nav":
            if action in ["up", "down"]:
                ui.move_selection(action, len(items))
            elif action == "enter":
                if items:
                    nav_result = navigator.go_forward(items[ui.selection_index])
                    if nav_result["success"]:
                        ui.selection_index, ui.scroll_position = 0, 0
                    else:
                        ui.error_message = nav_result["error"]
            elif action == "confirm":
                if items:
                    print(os.path.join(current_path, items[ui.selection_index]))
                    running = False
            elif action == "back":
                state = "home"
                ui.selection_index = 0

    ui.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Navii: A terminal directory navigator.')
    parser.add_argument('--project-root', type=str)
    args, _ = parser.parse_known_args()

    if args.project_root:
        sys.path.insert(0, os.path.join(args.project_root, 'src'))

    curses.wrapper(main)