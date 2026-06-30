import curses
import os
import sys
import argparse
from .ui import UIEngine
from .navigator import Navigator
from .background import BackgroundEngine
from .jumpstore import list_jumps, delete_jump
from .memostore import list_memos, delete_memo
from .config import get as config_get, set as config_set
from .background import SKY_THEMES, GROUND_THEMES

def main(stdscr, initial_state="home"):
    ui = UIEngine(stdscr)
    sky_theme      = config_get("sky_theme")
    ground_theme   = config_get("ground_theme")
    sky_enabled    = config_get("sky_enabled")
    ground_enabled = config_get("ground_enabled")
    bg_engine = BackgroundEngine(
        stdscr,
        sky_theme=sky_theme,
        ground_theme=ground_theme,
        sky_enabled=sky_enabled,
        ground_enabled=ground_enabled,
    )
    start_path = os.environ.get("NYXX_CWD") or os.getcwd()
    navigator = Navigator(start_path=start_path)

    state = initial_state
    theme_mode = "sky"
    ui.selection_index = 0
    confirm_delete = False
    running = True

    while running:
        # ── 1. State Logic ──────────────────────────────────────────────────
        if state == "home":
            items = [
                "cd   - Directory Navigator",
                "jump - Saved Locations",
                "memo - Saved Commands",
                "theme - Change Theme",
            ]
            current_path = "Nyxx Home"

        elif state == "nav":
            nav_data = navigator.list_items()
            items = nav_data["items"]
            full_paths = [
                os.path.join(navigator.get_current_path(), i) if i != ".."
                else os.path.dirname(navigator.get_current_path())
                for i in items
            ]
            current_path = navigator.get_current_path()
            if nav_data["success"]:
                ui.error_message = None
            else:
                ui.error_message = nav_data["error"]

        elif state == "jump":
            jumps = list_jumps()
            current_path = "jump"

        elif state == "memo":
            memos = list_memos()
            current_path = "memo"

        elif state == "theme":
            sky_themes    = list(SKY_THEMES.keys())
            ground_themes = list(GROUND_THEMES.keys())
            current_path  = "theme"

        # ── 2. Rendering ────────────────────────────────────────────────────
        stdscr.erase()
        bg_engine.draw()

        if state == "home":
            ui.draw_ui("Nyxx Home", items)
        elif state == "nav":
            ui.draw_cd_panel(current_path, items, full_paths, navigator.show_hidden)
        elif state == "jump":
            ui.draw_jump_panel(jumps, confirm_delete)
        elif state == "memo":
            ui.draw_memo_panel(memos, confirm_delete)
        elif state == "theme":
            ui.draw_theme_panel(
                sky_themes, ground_themes,
                sky_theme, ground_theme,
                sky_enabled, ground_enabled,
                mode=theme_mode,
            )

        stdscr.refresh()

        # ── 3. Input ────────────────────────────────────────────────────────
        action = ui.get_input()

        if action == "resize":
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            bg_engine.handle_resize()
            continue

        if action == "quit":
            running = False

        # ── Home ────────────────────────────────────────────────────────────
        elif state == "home":
            if action in ["up", "down"]:
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
                elif "theme" in selection:
                    state = "theme"
                    ui.selection_index = 0

        # ── CD Navigator ────────────────────────────────────────────────────
        elif state == "nav":
            if action in ["up", "down"]:
                ui.move_selection(action, len(items))
            elif action == "enter":
                if items:
                    nav_result = navigator.go_forward(items[ui.selection_index])
                    if nav_result["success"]:
                        ui.selection_index = 0
                        ui.scroll_position = 0
                    else:
                        ui.error_message = nav_result["error"]
            elif action == "confirm":
                if items:
                    selected = items[ui.selection_index]
                    if selected == "..":
                        target = os.path.dirname(navigator.get_current_path())
                    else:
                        target = os.path.join(navigator.get_current_path(), selected)
                    sys.stdout.write("CD:" + target + "\n")
                    sys.stdout.flush()
                    running = False
            elif action == "toggle_hidden":
                navigator.toggle_hidden()
                ui.selection_index = 0
                ui.scroll_position = 0
            elif action == "back":
                state = "home"
                ui.selection_index = 0

        # ── Jump ────────────────────────────────────────────────────────────
        elif state == "jump":
            if confirm_delete:
                key = stdscr.getch()
                if key == ord('y'):
                    if jumps:
                        delete_jump(jumps[ui.selection_index]["name"])
                        ui.selection_index = max(0, ui.selection_index - 1)
                    confirm_delete = False
                elif key == ord('n') or key == 27:
                    confirm_delete = False
            else:
                if action in ["up", "down"]:
                    ui.move_selection(action, len(jumps))
                elif action == "enter":
                    if jumps:
                        path = jumps[ui.selection_index].get("path", "")
                        path = os.path.expanduser(path)
                        sys.stdout.write("CD:" + path + "\n")
                        sys.stdout.flush()
                        running = False
                elif action == "delete":
                    if jumps:
                        confirm_delete = True
                elif action == "back":
                    state = "home"
                    ui.selection_index = 0
                    confirm_delete = False

        # ── Memo ────────────────────────────────────────────────────────────
        elif state == "memo":
            if confirm_delete:
                key = stdscr.getch()
                if key == ord('y'):
                    if memos:
                        delete_memo(memos[ui.selection_index]["name"])
                        ui.selection_index = max(0, ui.selection_index - 1)
                    confirm_delete = False
                elif key == ord('n') or key == 27:
                    confirm_delete = False
            else:
                if action in ["up", "down"]:
                    ui.move_selection(action, len(memos))
                elif action == "enter":
                    if memos:
                        cmd = memos[ui.selection_index].get("cmd", "")
                        sys.stdout.write("EXEC:" + cmd + "\n")
                        sys.stdout.flush()
                        running = False
                elif action == "delete":
                    if memos:
                        confirm_delete = True
                elif action == "back":
                    state = "home"
                    ui.selection_index = 0
                    confirm_delete = False

        # ── Theme ────────────────────────────────────────────────────────────
        elif state == "theme":
            if action == "tab":
                modes = ["sky", "ground", "toggles"]
                theme_mode = modes[(modes.index(theme_mode) + 1) % len(modes)]
                ui.selection_index = 0
            elif action in ["up", "down"]:
                if theme_mode == "sky":
                    ui.move_selection(action, len(sky_themes))
                elif theme_mode == "ground":
                    ui.move_selection(action, len(ground_themes))
                else:
                    ui.move_selection(action, 2)  # 2 toggles
            elif action == "enter":
                if theme_mode == "sky":
                    sky_theme = sky_themes[ui.selection_index]
                    config_set("sky_theme", sky_theme)
                    bg_engine.set_sky(sky_theme)
                elif theme_mode == "ground":
                    ground_theme = ground_themes[ui.selection_index]
                    config_set("ground_theme", ground_theme)
                    bg_engine.set_ground(ground_theme)
                elif theme_mode == "toggles":
                    if ui.selection_index == 0:
                        sky_enabled = not sky_enabled
                        config_set("sky_enabled", sky_enabled)
                        bg_engine.set_sky_enabled(sky_enabled)
                    else:
                        ground_enabled = not ground_enabled
                        config_set("ground_enabled", ground_enabled)
                        bg_engine.set_ground_enabled(ground_enabled)
            elif action == "back":
                state = "home"
                ui.selection_index = 0
                theme_mode = "sky"

    ui.cleanup()


def run_cli(subcommand, name):
    from .jumpstore import find_jump, add_jump
    from .memostore import find_memo, add_memo
    import os

    if subcommand == "jump" and name:
        if name == "add":
            print("--- Add New Jump ---")
            j_name = input("Name: ").strip()
            if j_name.lower() == "add":
                print("Error: Cannot name a jump 'add'.")
                return True
            j_desc = input("Description: ").strip()
            j_path = input(f"Path [default: {os.getcwd()}]: ").strip()
            if not j_path:
                j_path = os.getcwd()
            success, err = add_jump(j_name, j_desc, j_path)
            if success:
                print(f"Jump '{j_name}' saved.")
            else:
                print(f"Error saving jump: {err}")
            return True
            
        entry = find_jump(name)
        if entry:
            path = os.path.expanduser(entry.get("path", ""))
            sys.stdout.write("CD:" + path + "\n")
            sys.stdout.flush()
            return True
        else:
            sys.stderr.write(f"nyxx: no jump named '{name}'\n")
            sys.exit(1)

    if subcommand == "memo" and name:
        if name == "add":
            print("--- Add New Memo ---")
            m_name = input("Name: ").strip()
            if m_name.lower() == "add":
                print("Error: Cannot name a memo 'add'.")
                return True
            m_desc = input("Description: ").strip()
            m_cmd = input("Command: ").strip()
            if not m_cmd:
                print("Error: Command cannot be empty.")
                return True
            success, err = add_memo(m_name, m_desc, m_cmd)
            if success:
                print(f"Memo '{m_name}' saved.")
            else:
                print(f"Error saving memo: {err}")
            return True
            
        entry = find_memo(name)
        if entry:
            sys.stdout.write("EXEC:" + entry.get("cmd", "") + "\n")
            sys.stdout.flush()
            return True
        else:
            sys.stderr.write(f"nyxx: no memo named '{name}'\n")
            sys.exit(1)

    return False


def run_tui(initial_state="home"):
    if sys.platform == "win32":
        curses.wrapper(lambda s: main(s, initial_state))
        return

    tty_fd = open("/dev/tty", "r+b", buffering=0)
    try:
        old_stdin  = sys.__stdin__
        old_stdout = sys.__stdout__
        sys.__stdin__  = tty_fd
        sys.__stdout__ = tty_fd
        curses.wrapper(lambda s: main(s, initial_state))
    finally:
        sys.__stdin__  = old_stdin
        sys.__stdout__ = old_stdout
        tty_fd.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Nyxx: A terminal directory navigator.')
    parser.add_argument('--project-root', type=str)
    parser.add_argument('subcommand', nargs='?', default='home',
                        choices=['home', 'cd', 'jump', 'memo', 'theme'])
    parser.add_argument('name', nargs='?', default=None)   # ← the lookup name
    args = parser.parse_args()

    if args.project_root:
        sys.path.insert(0, os.path.join(args.project_root, 'src'))

    # If a name was given, try the CLI lookup first — no TUI needed
    if run_cli(args.subcommand, args.name):
        sys.exit(0)

    # Otherwise launch the TUI at the right starting state
    state_map = {'home': 'home', 'cd': 'nav', 'jump': 'jump', 'memo': 'memo', 'theme': 'theme'}
    run_tui(state_map.get(args.subcommand, 'home'))