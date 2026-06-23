import curses
import os
import sys
from .ui import UIEngine
from .navigator import Navigator
from .background import BackgroundEngine
from .pathhandler import PathHandler


# =====================================================================
# 1. ARGUMENT PARSING
# =====================================================================

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

    return {"action": "ui", "state": "home"}


# =====================================================================
# 2. MAIN TUI LOOP
# =====================================================================

def main(stdscr, initial_state="home"):  # <-- accepts initial_state now
    """
    Main controller loop for Navii.
    """
    ui = UIEngine(stdscr)
    bg_engine = BackgroundEngine(stdscr)
    navigator = Navigator()

    state = initial_state  # <-- uses it here
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
        bg_engine.draw()
        ui.draw_ui(current_path, items)
        stdscr.refresh()

        # 3. Input Handling
        action = ui.get_input()

        if action == "resize":
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            bg_engine.handle_resize()  # <-- add this line
            continue

        if action == "resize":
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            continue
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
                nav_result = navigator.go_back()
                if not nav_result["success"]:
                    state = "home"
                    ui.selection_index = 0
                    ui.scroll_position = 0
                    ui.error_message = None

    ui.cleanup()


# =====================================================================
# 3. ENTRY POINTS
# =====================================================================

def run_cli(args):
    # Placeholder for CLI commands (jump add, memo add, etc.)
    print(f"Executing {args['action']}...")
    sys.exit(0)


def run_tui(args):
    curses.wrapper(lambda stdscr: main(stdscr, initial_state=args["state"]))


def main_entry():
    args = parse_arguments()
    if args["action"] == "ui":
        run_tui(args)
    else:
        run_cli(args)


# =====================================================================
# 4. SCRIPT ENTRY (keep this simple — just call main_entry)
# =====================================================================

if __name__ == "__main__":
    main_entry()