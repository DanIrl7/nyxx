"""Input handling for each screen. Each function takes the shared
`AppState`/`UIEngine` plus whatever screen-specific data it needs, and
mutates `app`/`ui` in place in response to the given `action`."""
import curses
import os

from .config import get as config_get, set as config_set
from .dialogs import pick_color_gui, pick_image_file
from .jumpstore import delete_jump
from .memostore import delete_memo
from .shell_actions import write_shell_action

_TOGGLE_COLOR_KEYS = [
    "panel_color", "text_color", "highlight_panel_color",
    "highlight_text_color", "border_fg", "border_bg",
]


def handle_home_input(app, ui, action, items):
    if action in ("up", "down"):
        ui.move_selection(action, len(items))
    elif action == "enter":
        selected = items[ui.selection_index]
        if "cd" in selected:
            app.state = "nav"
        elif "jump" in selected:
            app.state = "jump"
            app.confirm_delete = False
        elif "memo" in selected:
            app.state = "memo"
            app.confirm_delete = False
        elif "theme" in selected:
            app.state = "theme"
        ui.selection_index = 0


def handle_nav_input(app, ui, action, navigator, items, full_paths):
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
            app.running = False
    elif action == "back":
        app.state = "home"
        ui.selection_index = 0


def handle_jump_memo_input(app, ui, action, data, kind):
    """`kind` is "jump" or "memo". `data` is the currently loaded list
    of jumps/memos for this frame (re-read from disk each loop, so a
    delete here doesn't need to mutate it)."""
    if action in ("up", "down"):
        ui.move_selection(action, len(data))
    elif action == "delete" and data:
        app.confirm_delete = True
    elif app.confirm_delete and action == "yes" and data:
        if kind == "jump":
            delete_jump(data[ui.selection_index]["name"])
        else:
            delete_memo(data[ui.selection_index]["name"])
        app.confirm_delete = False
        ui.selection_index = max(0, ui.selection_index - 1)
    elif app.confirm_delete and action == "no":
        app.confirm_delete = False
    elif action == "back":
        app.state = "home"
        app.confirm_delete = False
        ui.selection_index = 0
    elif action == "enter" and data:
        if kind == "jump":
            path = os.path.expanduser(data[ui.selection_index]["path"])
            write_shell_action("CD", path)
        else:
            cmd = data[ui.selection_index]["cmd"]
            write_shell_action("EXEC", cmd)
        app.running = False


def _handle_toggle_selection(app, ui):
    if ui.selection_index == 0:
        app.logo_enabled = not app.logo_enabled
        config_set("logo_enabled", app.logo_enabled)
        return

    key = _TOGGLE_COLOR_KEYS[ui.selection_index - 1]
    chosen = pick_color_gui()
    if chosen is not None:
        config_set(key, chosen)
        config_set("ui_theme", "custom")
        app.ui_theme = "custom"
        ui.refresh_custom_colors()


def handle_theme_input(app, ui, action, stdscr, bg_engine, ui_themes, scene_names):
    if action == "tab":
        tabs = ["scenes", "toggles", "ui"]
        index = tabs.index(app.theme_mode)
        app.theme_mode = tabs[(index + 1) % len(tabs)]
        ui.selection_index = 0

    elif action in ("up", "down"):
        if app.theme_mode == "scenes":
            ui.move_selection(action, len(scene_names))
        elif app.theme_mode == "toggles":
            ui.move_selection(action, len(_TOGGLE_COLOR_KEYS) + 1)
        elif app.theme_mode == "ui":
            ui.move_selection(action, len(ui_themes))

    elif action == "enter":
        if app.theme_mode == "scenes" and scene_names:
            selected_scene = scene_names[ui.selection_index]
            if selected_scene == "user image":
                curses.def_prog_mode()
                curses.endwin()
                try:
                    chosen_path = pick_image_file(config_get("user_image_path") or "")
                finally:
                    curses.reset_prog_mode()
                    stdscr.refresh()
                if chosen_path:
                    app.scene_theme = selected_scene
                    config_set("scene_theme", selected_scene)
                    config_set("user_image_path", chosen_path)
                    bg_engine.user_image_path = chosen_path
                    bg_engine.set_scene(selected_scene)
                    if getattr(bg_engine, "load_error", None):
                        ui.error_message = bg_engine.load_error
            else:
                app.scene_theme = selected_scene
                config_set("scene_theme", selected_scene)
                bg_engine.set_scene(selected_scene)
                if getattr(bg_engine, "load_error", None):
                    ui.error_message = bg_engine.load_error

        elif app.theme_mode == "toggles":
            _handle_toggle_selection(app, ui)

        elif app.theme_mode == "ui" and ui_themes:
            app.ui_theme = ui_themes[ui.selection_index]
            config_set("ui_theme", app.ui_theme)
            ui.apply_ui_theme(app.ui_theme)

    elif action == "back":
        app.state = "home"
        app.theme_mode = "scenes"
        ui.selection_index = 0
