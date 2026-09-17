import curses
import os
import sys
import argparse
import logging

from .ui import UIEngine
from .navigator import Navigator
from .background import BackgroundEngine, SCENE_THEMES
from .jumpstore import list_jumps, add_jump
from .memostore import list_memos, add_memo
from .config import get as config_get
from .app_state import AppState
from .shell_actions import write_shell_action
from . import screens
from . import handlers

_log_dir = os.path.expanduser("~/.nyxx")
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, 'nyxx_debug.log')

logging.basicConfig(
    filename=_log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main(stdscr, initial_state="home"):
    curses.curs_set(0)
    stdscr.nodelay(True)

    ui = UIEngine(stdscr)
    app = AppState(initial_state)

    app.scene_theme = config_get("scene_theme") or "user image"
    app.ui_theme = config_get("ui_theme")
    ui.apply_ui_theme(app.ui_theme)

    app.logo_enabled = config_get("logo_enabled")
    if app.logo_enabled is None:
        app.logo_enabled = True

    bg_engine = BackgroundEngine(
        stdscr,
        scene_theme=app.scene_theme,
        user_image_path=config_get("user_image_path") or "",
    )

    if getattr(bg_engine, "load_error", None):
        ui.error_message = bg_engine.load_error

    navigator = Navigator(
        start_path=os.environ.get("NYXX_CWD", os.getcwd())
    )

    ui.selection_index = 0

    while app.running:
        items = full_paths = jumps = memos = ui_themes = scene_names = None
        current_path = None

        # -------------------------------
        # Per-state data
        # -------------------------------
        if app.state == "home":
            items = [
                "cd   - Directory Navigator",
                "jump - Saved Locations",
                "memo - Saved Commands",
                "theme - Change Theme",
            ]
            current_path = "Nyxx Home"

        elif app.state == "nav":
            nav_data = navigator.list_items()
            items = nav_data["items"]
            full_paths = [
                os.path.join(navigator.get_current_path(), i)
                if i != ".."
                else os.path.dirname(navigator.get_current_path())
                for i in items
            ]
            current_path = navigator.get_current_path()
            ui.error_message = None if nav_data["success"] else nav_data["error"]

        elif app.state == "jump":
            jumps = list_jumps()

        elif app.state == "memo":
            memos = list_memos()

        elif app.state == "theme":
            ui_themes = list(ui.UI_THEMES.keys())
            scene_names = list(SCENE_THEMES.keys())

        # -------------------------------
        # Rendering
        # -------------------------------
        stdscr.erase()
        bg_engine.draw()

        if app.state == "home":
            screens.draw_ui(ui, "Nyxx Home", items, logo_enabled=app.logo_enabled)
        elif app.state == "nav":
            screens.draw_cd_panel(ui, current_path, items, full_paths, navigator.show_hidden)
        elif app.state == "jump":
            screens.draw_jump_panel(ui, jumps, app.confirm_delete)
        elif app.state == "memo":
            screens.draw_memo_panel(ui, memos, app.confirm_delete)
        elif app.state == "theme":
            screens.draw_theme_panel(
                ui, ui_themes, app.ui_theme, app.logo_enabled,
                scene_names=scene_names, active_scene=app.scene_theme, mode=app.theme_mode,
            )
        elif app.state == "help":
            screens.draw_help_panel(ui)

        stdscr.refresh()

        # -------------------------------
        # Input
        # -------------------------------
        action = ui.get_input()

        if action == "resize":
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            bg_engine.handle_resize()
            continue

        if action == "quit":
            app.running = False
            continue

        if action == "help":
            if app.state != "help":
                app.previous_state = app.state
                app.state = "help"
            else:
                app.state = app.previous_state
            continue

        if app.state == "help":
            if action is not None:
                app.state = app.previous_state
            continue

        if app.state == "home":
            handlers.handle_home_input(app, ui, action, items)
        elif app.state == "nav":
            handlers.handle_nav_input(app, ui, action, navigator, items, full_paths)
        elif app.state in ("jump", "memo"):
            data = jumps if app.state == "jump" else memos
            handlers.handle_jump_memo_input(app, ui, action, data, app.state)
        elif app.state == "theme":
            handlers.handle_theme_input(app, ui, action, stdscr, bg_engine, ui_themes, scene_names)

    ui.cleanup()


def run_tui(initial_state="home"):
    curses.wrapper(
        lambda stdscr: main(stdscr, initial_state=initial_state)
    )


def run_cli():
    parser = argparse.ArgumentParser(description="Nyxx terminal navigator", add_help=False)
    parser.add_argument("subcommand", nargs="?", default="home")
    parser.add_argument("name", nargs="?", default=None)
    parser.add_argument("-h", "--help", action="store_true")

    args = parser.parse_args()

    valid_subcommands = ["home", "cd", "jump", "memo", "theme"]
    if args.help or args.subcommand not in valid_subcommands:
        print("Usage: nyxx [home|cd|jump|memo|theme]")
        sys.exit(0)

    # Handle direct CLI lookups (e.g., executing a memo)
    if args.name and args.name != "add":
        if args.subcommand == "jump":
            from .jumpstore import find_jump
            entry = find_jump(args.name)
            if entry:
                write_shell_action("CD", os.path.expanduser(entry["path"]))
            else:
                print(f"nyxx: no jump named '{args.name}'", file=sys.stderr)
                sys.exit(1)
        elif args.subcommand == "memo":
            from .memostore import find_memo
            entry = find_memo(args.name)
            if entry:
                write_shell_action("EXEC", entry["cmd"])
            else:
                print(f"nyxx: no memo named '{args.name}'", file=sys.stderr)
                sys.exit(1)
        sys.exit(0)

    # Handle adding commands (e.g., nyxx memo add)
    if args.name == "add":
        if args.subcommand == "jump":
            name = input("Jump name: ").strip()
            desc = input("Description: ").strip()
            path = input("Path (leave blank for current dir): ").strip()
            if not path:
                path = os.getcwd()
            success, err = add_jump(name, desc, path)
            print(f"Jump '{name}' saved." if success else f"Error: {err}")
        elif args.subcommand == "memo":
            name = input("Memo name: ").strip()
            desc = input("Description: ").strip()
            cmd  = input("Command: ").strip()
            success, err = add_memo(name, desc, cmd)
            print(f"Memo '{name}' saved." if success else f"Error: {err}")
        sys.exit(0)

    # If no quick commands were run, boot the visual UI
    state_map = {
        "home": "home",
        "cd": "nav",
        "jump": "jump",
        "memo": "memo",
        "theme": "theme"
    }

    run_tui(state_map[args.subcommand])


if __name__ == "__main__":
    run_cli()
