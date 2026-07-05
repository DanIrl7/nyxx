import curses
import os
import sys
import argparse

from .ui import UIEngine
from .navigator import Navigator
from .background import (
    BackgroundEngine,
    SKY_THEMES,
    GROUND_THEMES,
    SCENE_THEMES,
)
from .jumpstore import list_jumps, delete_jump, add_jump
from .memostore import list_memos, delete_memo, add_memo
from .config import get as config_get, set as config_set


def _pick_image_file(initial_path=""):
    """Open a native file picker for choosing a background image."""
    from tkinter import Tk, filedialog

    initial_dir = os.path.dirname(initial_path) if initial_path else os.path.expanduser("~")
    root = Tk()
    root.withdraw()
    try:
        return filedialog.askopenfilename(
            title="Choose a background image",
            initialdir=initial_dir,
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
    finally:
        root.destroy()


def main(stdscr, initial_state="home"):

    curses.curs_set(0)
    stdscr.nodelay(True)

    ui = UIEngine(stdscr)

    sky_theme = config_get("sky_theme")
    ground_theme = config_get("ground_theme")
    scene_theme = config_get("scene_theme") or "vaporwave sunset"

    sky_enabled = config_get("sky_enabled")
    ground_enabled = config_get("ground_enabled")

    bg_mode = config_get("bg_mode") or "layered"

    bg_engine = BackgroundEngine(
        stdscr,
        sky_theme=sky_theme,
        ground_theme=ground_theme,
        sky_enabled=sky_enabled,
        ground_enabled=ground_enabled,
        mode=bg_mode,
        scene_theme=scene_theme,
        user_image_path=config_get("user_image_path") or "",
    )

    navigator = Navigator(
        start_path=os.environ.get(
            "NYXX_CWD",
            os.getcwd()
        )
    )

    state = initial_state
    theme_mode = "sky"

    ui.selection_index = 0

    confirm_delete = False
    running = True


    while running:

        # -------------------------------
        # State data
        # -------------------------------

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
                os.path.join(
                    navigator.get_current_path(),
                    i
                )
                if i != ".."
                else os.path.dirname(
                    navigator.get_current_path()
                )
                for i in items
            ]

            current_path = navigator.get_current_path()
            ui.error_message = None if nav_data["success"] else nav_data["error"]


        elif state == "jump":

            jumps = list_jumps()


        elif state == "memo":

            memos = list_memos()


        elif state == "theme":

            sky_themes = list(SKY_THEMES.keys())
            ground_themes = list(GROUND_THEMES.keys())
            scene_names = list(SCENE_THEMES.keys())



        # -------------------------------
        # Rendering
        # -------------------------------

        stdscr.erase()
        bg_engine.draw()


        if state == "home":
            ui.draw_ui("Nyxx Home", items)

        elif state == "nav":
            ui.draw_cd_panel(
                current_path,
                items,
                full_paths,
                navigator.show_hidden
            )

        elif state == "jump":
            ui.draw_jump_panel(jumps, confirm_delete)

        elif state == "memo":
            ui.draw_memo_panel(memos, confirm_delete)

        elif state == "theme":
            ui.draw_theme_panel(
                sky_themes,
                ground_themes,
                sky_theme,
                ground_theme,
                sky_enabled,
                ground_enabled,
                scene_names=scene_names,
                active_scene=scene_theme,
                mode=theme_mode
            )

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
            running = False
            continue


        # -------------------------------
        # Home
        # -------------------------------

        if state == "home":

            if action in ("up", "down"):
                ui.move_selection(action, len(items))

            elif action == "enter":
                selected = items[ui.selection_index]

                if "cd" in selected:
                    state = "nav"
                elif "jump" in selected:
                    state = "jump"
                    confirm_delete = False
                elif "memo" in selected:
                    state = "memo"
                    confirm_delete = False
                elif "theme" in selected:
                    state = "theme"

                ui.selection_index = 0


        # -------------------------------
        # Navigator
        # -------------------------------

        elif state == "nav":

            if action in ("up", "down"):
                ui.move_selection(action, len(items))

            elif action == "enter":
                if items:
                    result = navigator.go_forward(items[ui.selection_index])
                    if result["success"]:
                        ui.selection_index = 0

            elif action == "confirm":
                if items:
                    selected = items[ui.selection_index]
                    target = (
                        os.path.dirname(navigator.get_current_path())
                        if selected == ".."
                        else os.path.join(navigator.get_current_path(), selected)
                    )

                    print("CD:" + target, flush=True)
                    running = False

            elif action == "back":
                state = "home"


        # -------------------------------
        # Jump / Memo
        # -------------------------------

        elif state in ("jump", "memo"):

            data = jumps if state == "jump" else memos

            if action in ("up", "down"):
                ui.move_selection(action, len(data))

            elif action == "delete" and data:
                confirm_delete = True

            elif confirm_delete and action == "yes" and data:
                if state == "jump":
                    delete_jump(data[ui.selection_index]["name"])
                    jumps = list_jumps()
                else:
                    delete_memo(data[ui.selection_index]["name"])
                    memos = list_memos()
                
                confirm_delete = False
                ui.selection_index = max(0, ui.selection_index - 1)

            elif confirm_delete and action == "no":
                confirm_delete = False

            elif action == "back":
                state = "home"
                confirm_delete = False

            elif action == "enter" and data:
                if state == "jump":
                    path = os.path.expanduser(data[ui.selection_index]["path"])
                    print("CD:" + path, flush=True)
                else:
                    cmd = data[ui.selection_index]["cmd"]
                    print("EXEC:" + cmd, flush=True)

                running = False


        # -------------------------------
        # Theme editor
        # -------------------------------

        elif state == "theme":

            if action == "tab":
                tabs = ["sky", "ground", "toggles", "scenes"]
                index = tabs.index(theme_mode)
                theme_mode = tabs[(index + 1) % len(tabs)]
                ui.selection_index = 0

            elif action in ("up", "down"):
                if theme_mode == "sky":
                    ui.move_selection(action, len(sky_themes))
                elif theme_mode == "ground":
                    ui.move_selection(action, len(ground_themes))
                elif theme_mode == "toggles":
                    ui.move_selection(action, 2)
                elif theme_mode == "scenes":
                    ui.move_selection(action, len(scene_names))

            elif action == "enter":
                if theme_mode == "sky" and sky_themes:
                    sky_theme = sky_themes[ui.selection_index]
                    config_set("sky_theme", sky_theme)
                    bg_engine.set_sky(sky_theme)

                elif theme_mode == "ground" and ground_themes:
                    ground_theme = ground_themes[ui.selection_index]
                    config_set("ground_theme", ground_theme)
                    bg_engine.set_ground(ground_theme)

                elif theme_mode == "toggles":
                    if ui.selection_index == 0:
                        sky_enabled = not sky_enabled
                        config_set("sky_enabled", sky_enabled)
                        bg_engine.set_sky_enabled(sky_enabled)
                    elif ui.selection_index == 1:
                        ground_enabled = not ground_enabled
                        config_set("ground_enabled", ground_enabled)
                        bg_engine.set_ground_enabled(ground_enabled)

                elif theme_mode == "scenes" and scene_names:
                    selected_scene = scene_names[ui.selection_index]
                    if selected_scene == "user image":
                        curses.def_prog_mode()
                        curses.endwin()
                        try:
                            chosen_path = _pick_image_file(config_get("user_image_path") or "")
                        finally:
                            curses.reset_prog_mode()
                            stdscr.refresh()

                        if chosen_path:
                            scene_theme = selected_scene
                            config_set("scene_theme", selected_scene)
                            config_set("user_image_path", chosen_path)
                            config_set("bg_mode", "scene")
                            bg_engine.user_image_path = chosen_path
                            bg_engine.set_mode("scene")
                            bg_engine.set_scene(selected_scene)
                    else:
                        scene_theme = selected_scene
                        config_set("scene_theme", selected_scene)
                        config_set("bg_mode", "scene")
                        bg_engine.set_mode("scene")
                        bg_engine.set_scene(selected_scene)

            elif action == "back":
                state = "home"
                theme_mode = "sky"



    ui.cleanup()


def run_tui(initial_state="home"):
    curses.wrapper(lambda s: main(s, initial_state))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nyxx terminal navigator")
    parser.add_argument(
        "subcommand",
        nargs="?",
        default="home",
        choices=["home", "cd", "jump", "memo", "theme"]
    )
    parser.add_argument("name", nargs="?", default=None)

    args = parser.parse_args()

    # --- Handle direct lookup: nyxx jump <name> / nyxx memo <name> ---
    if args.name and args.name != "add":
        if args.subcommand == "jump":
            from .jumpstore import find_jump
            entry = find_jump(args.name)
            if entry:
                print("CD:" + os.path.expanduser(entry["path"]), flush=True)
            else:
                print(f"nyxx: no jump named '{args.name}'", file=sys.stderr)
                sys.exit(1)
        elif args.subcommand == "memo":
            from .memostore import find_memo
            entry = find_memo(args.name)
            if entry:
                print("EXEC:" + entry["cmd"], flush=True)
            else:
                print(f"nyxx: no memo named '{args.name}'", file=sys.stderr)
                sys.exit(1)
        sys.exit(0)

    # --- Handle "add" action before launching the TUI ---
    if args.name == "add":
        if args.subcommand == "jump":
            name = input("Jump name: ").strip()
            desc = input("Description: ").strip()
            path = input("Path (leave blank for current dir): ").strip()
            if not path:
                path = os.getcwd()
            success, err = add_jump(name, desc, path)
            if success:
                print(f"Jump '{name}' saved.")
            else:
                print(f"Error saving jump: {err}")
        elif args.subcommand == "memo":
            name = input("Memo name: ").strip()
            desc = input("Description: ").strip()
            cmd = input("Command: ").strip()
            success, err = add_memo(name, desc, cmd)
            if success:
                print(f"Memo '{name}' saved.")
            else:
                print(f"Error saving memo: {err}")
        sys.exit(0)

    state_map = {
        "home": "home",
        "cd": "nav",
        "jump": "jump",
        "memo": "memo",
        "theme": "theme"
    }

    run_tui(state_map[args.subcommand])