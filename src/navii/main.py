import curses
import os
import sys
from .ui import UIEngine
from .navigator import Navigator
from .background import BackgroundEngine
from .pathhandler import PathHandler
from .icons import get_icon
from .jumpstore import list_jumps, find_jump, add_jump, delete_jump
from .memostore import list_memos, find_memo, add_memo, delete_memo

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

def main(stdscr, mode=None):
    """
    Main controller loop for Navii.
    mode — optional starting state: "cd", "jump", "memo"
    """
    ui = UIEngine(stdscr)
    bg_engine = BackgroundEngine(stdscr)
    navigator = Navigator()

    # Determine starting state
    # parse_arguments() uses "nav" for cd state, "jump" for jump state
    if mode == "jump":
        state = "jump"
    elif mode == "memo":
        state = "memo"
    elif mode == "cd":
        state = "nav"
    else:
        state = "home"

    confirm_delete = False   # used by jump (and later memo) delete flow
    running = True

    while running:
        # ── 1. State data ──────────────────────────────────
        if state == "home":
            items = ["cd - Directory Navigator", "jump - Saved Locations", "memo - Saved Commands"]
            current_path = "Navii Home"

        elif state == "nav":
            nav_data = navigator.list_items()
            items = nav_data["items"]
            current_path = navigator.get_current_path()
            ui.error_message = None if nav_data["success"] else nav_data["error"]

        elif state == "jump":
            jumps = list_jumps()   # fresh read each frame (cheap, small file)
            current_path = "jump"  # sentinel so draw_ui knows which panel to show

        elif state == "memo":
            memos = list_memos()
            current_path = "memo"

        # ── 2. Render ──────────────────────────────────────
        stdscr.erase()
        bg_engine.draw()

        if state == "jump":
            ui.draw_jump_panel(jumps, confirm_delete=confirm_delete)
        elif state == "memo":
            ui.draw_memo_panel(memos, confirm_delete=confirm_delete)
        else:
            ui.draw_ui(current_path, items)

        stdscr.refresh()

        # ── 3. Input ───────────────────────────────────────
        if confirm_delete and state == "jump":
            raw = ui.stdscr.getch()
            if raw == ord('y') or raw == ord('Y'):
                if jumps:
                    delete_jump(jumps[ui.selection_index]["name"])
                    if ui.selection_index >= len(jumps) - 1 and ui.selection_index > 0:
                        ui.selection_index -= 1
                confirm_delete = False
                continue
            elif raw in (ord('n'), ord('N'), 27):   # n or Esc cancels
                confirm_delete = False
                continue

        elif confirm_delete and state == "memo":
            raw = ui.stdscr.getch()
            if raw in (ord('y'), ord('Y')):
                if memos:
                    delete_memo(memos[ui.selection_index]["name"])
                    if ui.selection_index >= len(memos) - 1 and ui.selection_index > 0:
                        ui.selection_index -= 1
                confirm_delete = False
                continue
            elif raw in (ord('n'), ord('N'), 27):
                confirm_delete = False
                continue

        action = ui.get_input()

        # ── Global actions (handled before state blocks) ───
        if action == "resize":
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            continue

        if action == "quit":
            running = False
            continue

        # ── Home ───────────────────────────────────────────
        if state == "home":
            if action in ("up", "down"):
                ui.move_selection(action, len(items))
            elif action == "enter":
                selection = items[ui.selection_index]
                if "cd" in selection:
                    state = "nav"
                    ui.selection_index = 0
                elif "jump" in selection:
                    state = "jump"
                    ui.selection_index = 0
                    confirm_delete = False
                elif "memo" in selection:
                    state = "memo"
                    ui.selection_index = 0
                    confirm_delete = False

        # ── CD nav ─────────────────────────────────────────
        elif state == "nav":
            if action in ("up", "down"):
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

        # ── Jump ───────────────────────────────────────────
        elif state == "jump":
            if action in ("up", "down"):
                ui.move_selection(action, len(jumps))
            elif action == "enter":
                if jumps:
                    jump = jumps[ui.selection_index]
                    print(f"CD:{jump['path']}")
                    running = False
            elif action == "back":
                state = "home"
                ui.selection_index = 0
                confirm_delete = False
            elif action == "delete":
                if jumps:
                    confirm_delete = True

        # ── Memo ───────────────────────────────────────────
        elif state == "memo":
            if action in ("up", "down"):
                ui.move_selection(action, len(memos))
            elif action == "enter":
                if memos:
                    memo = memos[ui.selection_index]
                    print(f"EXEC:{memo['cmd']}")
                    running = False
            elif action == "back":
                state = "home"
                ui.selection_index = 0
                confirm_delete = False
            elif action == "delete":
                if memos:
                    confirm_delete = True
        

    ui.cleanup()


# =====================================================================
# 3. ENTRY POINTS 
# =====================================================================

def run_cli(args):
    if args["action"] == "jump_add":
        # Prompt inline — no curses
        path = os.getcwd()
        name = input("Name for this location: ").strip()
        if not name:
            print("Cancelled.")
            return
        desc = input("Description (optional): ").strip()
        success, err = add_jump(name, desc, path)
        if success:
            print(f"Saved '{name}' → {path}")
        else:
            print(f"Error saving jump: {err}")

    elif args["action"] == "jump_lookup":
        # navi jump <name> — no UI, just print CD: for shell wrapper
        jump = find_jump(args["name"])
        if jump:
            print(f"CD:{jump['path']}")
        else:
            print(f"navi: no jump named '{args['name']}'", file=sys.stderr)

    # --- CORRECTED MEMO LOGIC ---
    elif args["action"] == "memo_add":
        name = input("Name for this command: ").strip()
        if not name:
            print("Cancelled.")
            return
        desc = input("Description (optional): ").strip()
        cmd  = input("Command: ").strip()
        if not cmd:
            print("Cancelled — command cannot be empty.")
            return
        success, err = add_memo(name, desc, cmd)
        if success:
            print(f"Saved '{name}' → {cmd}")
        else:
            print(f"Error saving memo: {err}")

    elif args["action"] == "memo_lookup":
        memo = find_memo(args["name"])
        if memo:
            print(f"EXEC:{memo['cmd']}")
        else:
            print(f"navi: no memo named '{args['name']}'", file=sys.stderr)

def run_tui(args):
    curses.wrapper(lambda stdscr: main(stdscr, mode=args["state"]))


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