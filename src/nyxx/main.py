import curses
import os
import sys
import argparse
import subprocess
import tkinter as tk
from tkinter import colorchooser
import logging
from .ui import UIEngine
from .navigator import Navigator
from .background import BackgroundEngine, SCENE_THEMES
from .jumpstore import list_jumps, delete_jump, add_jump
from .memostore import list_memos, delete_memo, add_memo
from .config import get as config_get, set as config_set

_log_dir = os.path.expanduser("~/.nyxx")
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, 'nyxx_debug.log')

logging.basicConfig(
    filename=_log_file, 
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def _pick_image_file(initial_path=""):
    """Use PowerShell to trigger the native Windows file picker."""
    initial_dir = os.path.dirname(initial_path) if initial_path else os.path.expanduser("~")
    
    ps_command = f"""
    Add-Type -AssemblyName System.Windows.Forms
    $fd = New-Object System.Windows.Forms.OpenFileDialog
    $fd.InitialDirectory = '{initial_dir}'
    $fd.Filter = 'Image Files|*.png;*.jpg;*.jpeg;*.webp;*.bmp|All Files|*.*'
    $fd.ShowDialog() | Out-Null
    $fd.FileName
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True
        )
        path = result.stdout.strip()
        return path if path else None
    except Exception:
        return None
        
def _rgb_to_xterm(r, g, b):
    if r == g == b:
        if r < 8: return 16
        if r > 248: return 231
        return round(((r - 8) / 247) * 24) + 232
    
    r_step = int(round((r / 255.0) * 5))
    g_step = int(round((g / 255.0) * 5))
    b_step = int(round((b / 255.0) * 5))
    return 16 + (36 * r_step) + (6 * g_step) + b_step

def _pick_color_gui():
    curses.def_prog_mode()
    curses.endwin()
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True) 
    
    color = colorchooser.askcolor(title="Pick a Color")
    root.destroy()
    
    curses.reset_prog_mode()
    
    if color[0]: 
        r, g, b = [int(c) for c in color[0]]
        return _rgb_to_xterm(r, g, b)
    return None
    
def write_shell_action(action_type, value):
    """Writes actions to a temporary file to be executed by shell wrappers."""
    action_file = os.path.expanduser("~/.nyxx/action")
    try:
        os.makedirs(os.path.dirname(action_file), exist_ok=True)
        with open(action_file, "w", encoding="utf-8") as f:
            f.write(f"{action_type}:{value}")
    except Exception as e:
        logging.error(f"Failed to write shell action: {e}")

def main(stdscr, initial_state="home"):
    curses.curs_set(0)
    stdscr.nodelay(True)

    ui = UIEngine(stdscr)

    scene_theme = config_get("scene_theme") or "user image"
    ui_theme = config_get("ui_theme") 

    ui.apply_ui_theme(ui_theme)

    logo_enabled = config_get("logo_enabled")
    if logo_enabled is None:
        logo_enabled = True

    bg_engine = BackgroundEngine(
        stdscr,
        scene_theme=scene_theme,
        user_image_path=config_get("user_image_path") or "",
    )
    
    if hasattr(bg_engine, "load_error") and bg_engine.load_error:
        ui.error_message = bg_engine.load_error

    navigator = Navigator(
        start_path=os.environ.get("NYXX_CWD", os.getcwd())
    )

    state = initial_state
    previous_state = "home"
    theme_mode = "scenes" # Default to scenes tab

    ui.selection_index = 0
    confirm_delete = False
    running = True

    while running:

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
                os.path.join(navigator.get_current_path(), i)
                if i != ".."
                else os.path.dirname(navigator.get_current_path())
                for i in items
            ]
            current_path = navigator.get_current_path()
            ui.error_message = None if nav_data["success"] else nav_data["error"]

        elif state == "jump":
            jumps = list_jumps()

        elif state == "memo":
            memos = list_memos()

        elif state == "theme":
            ui_themes = list(ui.UI_THEMES.keys())
            scene_names = list(SCENE_THEMES.keys())

        elif state == "help":
            pass

        # -------------------------------
        # Rendering
        # -------------------------------
        stdscr.erase()
        bg_engine.draw()

        if state == "home":
            ui.draw_ui("Nyxx Home", items, logo_enabled=logo_enabled)

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
                ui_themes,
                ui_theme,
                logo_enabled,
                scene_names=scene_names,
                active_scene=scene_theme,
                mode=theme_mode
            )

        elif state == "help":
            ui.draw_help_panel()

        stdscr.refresh()

        # -------------------------------
        # Input Interceptions
        # -------------------------------
        action = ui.get_input()
        
        if action == "resize":
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            bg_engine.handle_resize()
            continue

        if action == "quit":
            running = False
            continue

        if action == "help":
            if state != "help":
                previous_state = state
                state = "help"
            else:
                state = previous_state
            continue

        if state == "help":
            if action is not None:
                state = previous_state
            continue

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

        elif state == "nav":
            if action in ("up", "down"):
                ui.move_selection(action, len(items))
            elif action == "toggle_hidden":
                navigator.show_hidden = not navigator.show_hidden
                ui.selection_index = 0
            elif action in ("copy_item", "cut_item"):
                if items and items[ui.selection_index] != "..":
                    target_path = full_paths[ui.selection_index]
                    mode = "copy" if action == "copy_item" else "cut"
                    navigator.set_clipboard(target_path, mode)
            elif action == "paste_item":
                result = navigator.execute_paste()
                ui.error_message = result["error"]
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
                    write_shell_action("CD", target)
                    running = False
            elif action == "back":
                state = "home"
                ui.selection_index = 0

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
                ui.selection_index = 0
            elif action == "enter" and data:
                if state == "jump":
                    path = os.path.expanduser(data[ui.selection_index]["path"])
                    write_shell_action("CD", path)
                else:
                    cmd = data[ui.selection_index]["cmd"]
                    write_shell_action("EXEC", cmd)
                running = False

        elif state == "theme":
            if action == "tab":
                tabs = ["scenes", "toggles", "ui"]
                index = tabs.index(theme_mode)
                theme_mode = tabs[(index + 1) % len(tabs)]
                ui.selection_index = 0

            elif action in ("up", "down"):
                if theme_mode == "scenes":
                    ui.move_selection(action, len(scene_names))
                elif theme_mode == "toggles":
                    ui.move_selection(action, 7)
                elif theme_mode == "ui":
                    ui.move_selection(action, len(ui_themes))

            elif action == "enter":
                if theme_mode == "scenes" and scene_names:
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
                            bg_engine.user_image_path = chosen_path
                            bg_engine.set_scene(selected_scene) 
                            
                            if hasattr(bg_engine, "load_error") and bg_engine.load_error:
                                ui.error_message = bg_engine.load_error
                    else:
                        scene_theme = selected_scene
                        config_set("scene_theme", selected_scene)
                        bg_engine.set_scene(selected_scene)

                        if hasattr(bg_engine, "load_error") and bg_engine.load_error:
                                ui.error_message = bg_engine.load_error

                elif theme_mode == "toggles":
                    if ui.selection_index == 0:
                        logo_enabled = not logo_enabled
                        config_set("logo_enabled", logo_enabled)
                    elif ui.selection_index == 1:
                        chosen = _pick_color_gui()
                        if chosen is not None:
                            config_set("panel_color", chosen)
                            config_set("ui_theme", "custom")
                            ui_theme = "custom"
                            ui.refresh_custom_colors()
                    elif ui.selection_index == 2:
                        chosen = _pick_color_gui()
                        if chosen is not None:
                            config_set("text_color", chosen)
                            config_set("ui_theme", "custom")
                            ui_theme = "custom"
                            ui.refresh_custom_colors()
                    elif ui.selection_index == 3:
                        chosen = _pick_color_gui()
                        if chosen is not None:
                            config_set("highlight_panel_color", chosen)
                            config_set("ui_theme", "custom")
                            ui_theme = "custom"
                            ui.refresh_custom_colors()
                    elif ui.selection_index == 4:
                        chosen = _pick_color_gui()
                        if chosen is not None:
                            config_set("highlight_text_color", chosen)
                            config_set("ui_theme", "custom")
                            ui_theme = "custom"
                            ui.refresh_custom_colors()
                    elif ui.selection_index == 5:
                        chosen = _pick_color_gui()
                        if chosen is not None:
                            config_set("border_fg", chosen)
                            config_set("ui_theme", "custom")
                            ui_theme = "custom"
                            ui.refresh_custom_colors()
                    elif ui.selection_index == 6:
                        chosen = _pick_color_gui()
                        if chosen is not None:
                            config_set("border_bg", chosen)
                            config_set("ui_theme", "custom")
                            ui_theme = "custom"
                            ui.refresh_custom_colors()

                elif theme_mode == "ui" and ui_themes:
                    ui_theme = ui_themes[ui.selection_index]
                    config_set("ui_theme", ui_theme)
                    ui.apply_ui_theme(ui_theme)

            elif action == "back":
                state = "home"
                theme_mode = "scenes"
                ui.selection_index = 0

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
            from .jumpstore import add_jump
            name = input("Jump name: ").strip()
            desc = input("Description: ").strip()
            path = input("Path (leave blank for current dir): ").strip()
            if not path:
                path = os.getcwd()
            success, err = add_jump(name, desc, path)
            print(f"Jump '{name}' saved." if success else f"Error: {err}")
        elif args.subcommand == "memo":
            from .memostore import add_memo
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