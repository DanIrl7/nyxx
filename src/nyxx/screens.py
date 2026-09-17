"""Draw functions for each Nyxx screen.

Every function takes the shared `UIEngine` (theming, input, and generic
panel primitives) as its first argument plus whatever data that screen
needs to render.
"""
import curses
import os

from .icons import get_icon


def draw_ui(ui, current_path, items, logo_enabled=True):
    curses.curs_set(0)
    if current_path == "Nyxx Home":
        draw_home(ui, items, logo_enabled=logo_enabled)
        return

    ui.stdscr.addstr(0, 0, current_path, curses.color_pair(ui.PANEL_PAIR))
    ui.draw_list(items, start_row=1)
    footer_text = "↑↓ Navigate  Enter Open  ← Back  q Quit"
    try:
        ui.stdscr.addstr(ui.max_y - 1, 0, footer_text, curses.color_pair(ui.YELLOW))
    except curses.error: pass
    if ui.error_message:
        try:
            ui.stdscr.addstr(ui.max_y - 2, 0, f"Error: {ui.error_message}", curses.color_pair(ui.YELLOW))
        except curses.error: pass


def draw_home(ui, items, logo_enabled=True):
    curses.curs_set(0)
    if logo_enabled:
        logo_lines = ui.get_logo_lines()
        logo_colors = [ui.PANEL_PAIR] * len(logo_lines)
        for i in range(len(logo_lines)):
            if i < len(logo_lines) // 3:
                logo_colors[i] = curses.color_pair(ui.PANEL_PAIR) | curses.A_DIM
            elif i < (len(logo_lines) * 2) // 3:
                logo_colors[i] = curses.color_pair(ui.BORDER_PAIR)
            else:
                logo_colors[i] = curses.color_pair(ui.BORDER_PAIR) | curses.A_BOLD

        logo_width = max(len(l) for l in logo_lines) if logo_lines else 0
        logo_start_x = max(0, (ui.max_x - logo_width) // 2)
        logo_start_y = max(0, (ui.max_y // 2) - len(logo_lines) - 6)

        for i, line in enumerate(logo_lines):
            try:
                ui.stdscr.addstr(logo_start_y + i, logo_start_x, line, logo_colors[i])
            except curses.error: pass

    menu_lines = []
    for i, item in enumerate(items):
        parts = item.split(" - ", 1)
        name = parts[0].strip()
        desc = parts[1].strip() if len(parts) > 1 else ""
        prefix = "⫸ " if i == ui.selection_index else "  "
        menu_lines.append(f"{prefix}{name:<8}  {desc}")

    footer_lines = ["↑↓:Navigate  z:Help  Enter:Select  q:Quit"]
    panel_y, panel_x, panel_w = ui.draw_panel(menu_lines, footer_lines)

    padding_x = 4
    selected_row = panel_y + 2 + ui.selection_index
    selected_line = menu_lines[ui.selection_index]
    try:
        ui.stdscr.addstr(selected_row, panel_x + padding_x + 1, selected_line, curses.color_pair(ui.SELECTION))
    except curses.error: pass


def draw_cd_panel(ui, current_path, items, full_paths, show_hidden):
    curses.curs_set(0)
    max_y, max_x = ui.stdscr.getmaxyx()
    panel_w = min(60, max_x - 4)
    panel_h = min(22, max_y - 4)
    panel_x = (max_x - panel_w) // 2
    panel_y = (max_y - panel_h) // 2

    ui.fill_panel_bg(panel_y, panel_x, panel_w, panel_h)

    top = "╔" + "═" * (panel_w - 2) + "╗"
    try:
        ui.stdscr.addstr(panel_y, panel_x, top, curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    for row in range(1, panel_h - 1):
        try:
            ui.stdscr.addstr(panel_y + row, panel_x,     "║", curses.color_pair(ui.BORDER_PAIR))
            ui.stdscr.addstr(panel_y + row, panel_x + panel_w - 1, "║", curses.color_pair(ui.BORDER_PAIR))
        except curses.error: pass

    bot = "╚" + "═" * (panel_w - 2) + "╝"
    try:
        ui.stdscr.addstr(panel_y + panel_h - 1, panel_x, bot, curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    inner_w = panel_w - 4
    header = "📂 " + ui.truncate(current_path, inner_w - 3)
    try:
        ui.stdscr.addstr(panel_y + 1, panel_x + 2, header, curses.color_pair(ui.PANEL_PAIR) | curses.A_BOLD)
    except curses.error: pass

    div = "╠" + "═" * (panel_w - 2) + "╣"
    try:
        ui.stdscr.addstr(panel_y + 2, panel_x, div, curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    list_rows = panel_h - 9
    list_y    = panel_y + 3
    half = list_rows // 2
    scroll = max(0, min(ui.selection_index - half, len(items) - list_rows))

    visible = items[scroll:scroll + list_rows]
    visible_paths = full_paths[scroll:scroll + list_rows]

    for i, (name, fpath) in enumerate(zip(visible, visible_paths)):
        abs_idx = scroll + i
        selected = abs_idx == ui.selection_index
        icon = get_icon(fpath)
        icon_col  = panel_x + 2
        arrow_col = panel_x + 4
        name_col  = panel_x + 6
        max_name = panel_w - 8
        display_name = ui.truncate(name, max_name)
        row_y = list_y + i
        if row_y >= panel_y + panel_h - 6:
            break

        if selected:
            attr = curses.color_pair(ui.SELECTION)
            blank = " " * (panel_w - 2)
            try:
                ui.stdscr.addstr(row_y, panel_x + 1, blank, attr)
                ui.stdscr.addstr(row_y, icon_col,  icon,          attr)
                ui.stdscr.addstr(row_y, arrow_col, "▸",           attr)
                ui.stdscr.addstr(row_y, name_col,  display_name,  attr)
            except curses.error: pass
        else:
            attr = curses.color_pair(ui.PANEL_PAIR)
            try:
                ui.stdscr.addstr(row_y, panel_x + 1, " " * (panel_w - 2), attr)
                ui.stdscr.addstr(row_y, icon_col,  icon,          attr)
                ui.stdscr.addstr(row_y, arrow_col, " ",           attr)
                ui.stdscr.addstr(row_y, name_col,  display_name,  attr)
            except curses.error: pass

    if len(items) > list_rows:
        sb_x = panel_x + panel_w - 2
        bar_h = list_rows
        thumb_pos = int(scroll / max(1, len(items) - list_rows) * (bar_h - 1))
        for row in range(bar_h):
            char = "█" if row == thumb_pos else "░"
            try:
                ui.stdscr.addstr(list_y + row, sb_x, char, curses.color_pair(ui.BORDER_PAIR))
            except curses.error: pass

    preview_y = panel_y + panel_h - 6
    div2 = "╠" + "═" * (panel_w - 2) + "╣"
    try:
        ui.stdscr.addstr(preview_y, panel_x, div2, curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    selected_name = items[ui.selection_index] if items else ""
    if selected_name == "..":
        preview_path = os.path.dirname(current_path) or "/"
    else:
        preview_path = os.path.join(current_path, selected_name)
    preview_text = "→ " + ui.truncate(preview_path, inner_w - 2)
    try:
        ui.stdscr.addstr(preview_y + 1, panel_x + 2, preview_text.ljust(inner_w - 2), curses.color_pair(ui.PANEL_HINT_PAIR))
    except curses.error: pass

    div3 = "╠" + "═" * (panel_w - 2) + "╣"
    try:
        ui.stdscr.addstr(panel_y + panel_h - 4, panel_x, div3, curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    hidden_hint = ". show-hidden" if not show_hidden else ". hide-hidden"
    footer_line1 = "[↑↓ move]   [→ enter]  [← back]  [z hint]"
    footer_line2 = f" [SPC jump]   {hidden_hint}   [q quit]"

    try:
        ui.stdscr.addstr(panel_y + panel_h - 3, panel_x + 1, footer_line1.ljust(inner_w), curses.color_pair(ui.PANEL_HINT_PAIR))
        ui.stdscr.addstr(panel_y + panel_h - 2, panel_x + 1, footer_line2.ljust(inner_w), curses.color_pair(ui.PANEL_HINT_PAIR))
    except curses.error: pass


def _draw_entry_list_panel(ui, entries, confirm_delete, *, icon, title, noun, empty_hint,
                            detail_key, detail_prefix, enter_label):
    """Shared layout for the jump and memo panels — both show a titled
    list of named entries with a one-line detail (a path or a command)
    underneath each, plus a delete-confirm footer."""
    curses.curs_set(0)
    max_y, max_x = ui.stdscr.getmaxyx()
    panel_w = min(60, max_x - 4)
    panel_h = min(18, max_y - 4)
    start_y = (max_y - panel_h) // 2
    start_x = (max_x - panel_w) // 2

    ui.fill_panel_bg(start_y, start_x, panel_w, panel_h)

    try:
        ui.stdscr.addstr(start_y, start_x, "╔" + "═" * (panel_w - 2) + "╗", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass
    for r in range(1, panel_h - 1):
        try:
            ui.stdscr.addstr(start_y + r, start_x,             "║", curses.color_pair(ui.BORDER_PAIR))
            ui.stdscr.addstr(start_y + r, start_x + panel_w - 1, "║", curses.color_pair(ui.BORDER_PAIR))
        except curses.error: pass
    try:
        ui.stdscr.addstr(start_y + panel_h - 1, start_x, "╚" + "═" * (panel_w - 2) + "╝", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    count_str   = f"{len(entries)} saved"
    header_left = f" {icon} {title}"
    inner_w     = panel_w - 2
    header      = header_left.ljust(inner_w - len(count_str)) + count_str
    try:
        ui.stdscr.addstr(start_y + 1, start_x + 1, ui.truncate(header, inner_w), curses.color_pair(ui.PANEL_PAIR))
    except curses.error: pass
    try:
        ui.stdscr.addstr(start_y + 2, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    if not entries:
        try:
            ui.stdscr.addstr(start_y + 4, start_x + 1, ui.truncate(f" No saved {noun} yet.", inner_w).ljust(inner_w), curses.color_pair(ui.PANEL_PAIR))
            ui.stdscr.addstr(start_y + 5, start_x + 1, ui.truncate(f" Use '{empty_hint}' to save a {noun[:-1]}.", inner_w).ljust(inner_w), curses.color_pair(ui.PANEL_HINT_PAIR))
        except curses.error: pass

    list_start_row   = start_y + 3
    footer_row       = start_y + panel_h - 3
    available_rows   = footer_row - list_start_row
    rows_per_entry   = 2
    viewport_entries = max(1, available_rows // rows_per_entry)

    half   = viewport_entries // 2
    scroll = max(0, ui.selection_index - half)
    scroll = min(scroll, max(0, len(entries) - viewport_entries))

    for slot, idx in enumerate(range(scroll, min(scroll + viewport_entries, len(entries)))):
        entry    = entries[idx]
        selected = (idx == ui.selection_index)
        row_y    = list_start_row + slot * rows_per_entry
        if row_y >= footer_row:
            break

        indicator = "▸ " if selected else "  "
        name_col  = curses.color_pair(ui.SELECTION) if selected else curses.color_pair(ui.PANEL_PAIR)
        name_str  = ui.truncate(entry.get("name", ""), 12).ljust(12)
        desc_str  = ui.truncate(entry.get("desc", ""), inner_w - 16)
        line1     = f"{indicator}{name_str}  {desc_str}"
        detail_str = detail_prefix + ui.truncate(entry.get(detail_key, ""), inner_w - len(detail_prefix))

        try:
            fill = curses.color_pair(ui.PANEL_PAIR)
            ui.stdscr.addstr(row_y,     start_x + 1, " " * inner_w, name_col if selected else fill)
            ui.stdscr.addstr(row_y + 1, start_x + 1, " " * inner_w, name_col if selected else fill)
            ui.stdscr.addstr(row_y,     start_x + 1, ui.truncate(line1, inner_w), name_col)
            ui.stdscr.addstr(row_y + 1, start_x + 1, detail_str.ljust(inner_w)[:inner_w],
                              curses.color_pair(ui.SELECTION) if selected else curses.color_pair(ui.PANEL_HINT_PAIR))
        except curses.error: pass

    if len(entries) > viewport_entries:
        sb_x  = start_x + panel_w - 2
        bar_h = available_rows
        thumb = int(scroll / max(1, len(entries) - viewport_entries) * (bar_h - 1))
        for i in range(bar_h):
            try:
                ui.stdscr.addstr(list_start_row + i, sb_x, "█" if i == thumb else "░", curses.color_pair(ui.BORDER_PAIR))
            except curses.error: pass

    try:
        ui.stdscr.addstr(footer_row, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    if confirm_delete:
        sel_name     = entries[ui.selection_index]["name"] if entries else ""
        confirm_text = ui.truncate(f" Delete '{sel_name}'?  [y] yes   [n] no", inner_w)
        try:
            ui.stdscr.addstr(footer_row + 1, start_x + 1, confirm_text.ljust(inner_w)[:inner_w], curses.color_pair(ui.PANEL_HINT_PAIR))
        except curses.error: pass
    else:
        try:
            ui.stdscr.addstr(footer_row + 1, start_x + 1, f" ↑↓ move   Enter {enter_label}   d delete   q quit".ljust(inner_w), curses.color_pair(ui.PANEL_HINT_PAIR))
        except curses.error: pass


def draw_jump_panel(ui, jumps, confirm_delete=False):
    _draw_entry_list_panel(
        ui, jumps, confirm_delete,
        icon="📌", title="saved locations", noun="locations", empty_hint="nyxx jump add",
        detail_key="path", detail_prefix="    ", enter_label="jump",
    )


def draw_memo_panel(ui, memos, confirm_delete=False):
    _draw_entry_list_panel(
        ui, memos, confirm_delete,
        icon="📝", title="saved commands", noun="commands", empty_hint="nyxx memo add",
        detail_key="cmd", detail_prefix="    $ ", enter_label="run",
    )


def draw_help_panel(ui):
    max_y, max_x = ui.stdscr.getmaxyx()
    curses.curs_set(0)
    panel_w = min(60, max_x - 4)
    panel_h = min(21, max_y - 4)
    start_y = (max_y - panel_h) // 2
    start_x = (max_x - panel_w) // 2
    inner_w = panel_w - 2

    ui.fill_panel_bg(start_y, start_x, panel_w, panel_h)

    try:
        ui.stdscr.addstr(start_y, start_x, "╔" + "═" * (panel_w - 2) + "╗", curses.color_pair(ui.BORDER_PAIR))
        for r in range(1, panel_h - 1):
            ui.stdscr.addstr(start_y + r, start_x, "║", curses.color_pair(ui.BORDER_PAIR))
            ui.stdscr.addstr(start_y + r, start_x + panel_w - 1, "║", curses.color_pair(ui.BORDER_PAIR))
        ui.stdscr.addstr(start_y + panel_h - 1, start_x, "╚" + "═" * (panel_w - 2) + "╝", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    header = " 💡 Nyxx Keyboard Controls"
    try:
        ui.stdscr.addstr(start_y + 1, start_x + 1, header.ljust(inner_w)[:inner_w], curses.color_pair(ui.PANEL_PAIR) | curses.A_BOLD)
        ui.stdscr.addstr(start_y + 2, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    help_lines = [
        ("General Navigation", ""),
        ("  ↑ / k", "Move selection row up"),
        ("  ↓ / j", "Move selection row down"),
        ("  ← / h / Back", "Go back / return to Home dashboard"),
        ("  z", "Toggle this Help menu info"),
        ("  q / Esc", "Quit application fully"),
        ("", ""),
        ("Directory Browser (cd)", ""),
        ("  → / l / Enter", "Enter highlighted folder branch"),
        ("  Space", "Confirm pick & change shell directory"),
        ("  .", "Toggle visibility of hidden dotfiles"),
        ("", ""),
        ("Saved Jumps & Memos", ""),
        ("  Enter", "Trigger saved branch/command sequence"),
        ("  d", "Delete custom item (requires confirm)"),
        ("", ""),
        ("Theme Customizer", ""),
        ("  Tab", "Cycle categories (Backgrounds, Toggles, Panels)"),
        ("  Enter", "Apply selected option block"),
    ]

    curr_row = start_y + 3
    for title, desc in help_lines:
        if curr_row >= start_y + panel_h - 2: break
        if not title and not desc:
            curr_row += 1
            continue

        try:
            ui.stdscr.addstr(curr_row, start_x + 1, " " * inner_w, curses.color_pair(ui.PANEL_PAIR))
            if desc == "":
                ui.stdscr.addstr(curr_row, start_x + 2, title.ljust(inner_w - 2)[:inner_w - 2], curses.color_pair(ui.PANEL_PAIR) | curses.A_UNDERLINE)
            else:
                ui.stdscr.addstr(curr_row, start_x + 3, title, curses.color_pair(ui.PANEL_HINT_PAIR))
                ui.stdscr.addstr(curr_row, start_x + 20, desc.ljust(inner_w - 20)[:inner_w - 20], curses.color_pair(ui.PANEL_PAIR))
        except curses.error: pass
        curr_row += 1

    footer_row = start_y + panel_h - 2
    try:
        ui.stdscr.addstr(footer_row, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(ui.BORDER_PAIR))
        footer_text = " Press any key to close help overlay..."
        ui.stdscr.addstr(footer_row + 1, start_x + 1, footer_text.ljust(inner_w)[:inner_w], curses.color_pair(ui.PANEL_HINT_PAIR))
    except curses.error: pass


def draw_theme_panel(ui, ui_themes, active_ui, logo_enabled=True, scene_names=None, active_scene=None, mode="scenes"):
    if scene_names is None: scene_names = []
    if active_scene is None: active_scene = ""
    curses.curs_set(0)
    max_y, max_x = ui.stdscr.getmaxyx()
    panel_w = min(60, max_x - 4)
    panel_h = min(18, max_y - 4)
    start_y = (max_y - panel_h) // 2
    start_x = (max_x - panel_w) // 2
    inner_w = panel_w - 2

    ui.fill_panel_bg(start_y, start_x, panel_w, panel_h)

    tabs = [("scenes", "⟡ Backgrounds ⟡"), ("toggles", "⟡ Toggles ⟡"), ("ui", "⟡ Panels ⟡")]

    tab_x = start_x + 2
    for key, label in tabs:
        attr = curses.color_pair(ui.SELECTION) if mode == key else curses.color_pair(ui.PANEL_PAIR)
        try:
            ui.stdscr.addstr(start_y + 1, tab_x, label, attr)
        except curses.error: pass
        tab_x += len(label) + 2

    try:
        ui.stdscr.addstr(start_y + 1, start_x + panel_w - 1, " ")
    except curses.error: pass

    try:
        ui.stdscr.addstr(start_y, start_x, "╔" + "═" * (panel_w - 2) + "╗", curses.color_pair(ui.BORDER_PAIR))
        for r in range(1, panel_h):
            ui.stdscr.addstr(start_y + r, start_x, "║", curses.color_pair(ui.BORDER_PAIR))
            ui.stdscr.addstr(start_y + r, start_x + panel_w - 1, "║", curses.color_pair(ui.BORDER_PAIR))
        ui.stdscr.addstr(start_y + panel_h - 1, start_x, "╚" + "═" * (panel_w - 2) + "╝", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    try:
        ui.stdscr.addstr(start_y + 2, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(ui.BORDER_PAIR))
    except curses.error: pass

    list_start  = start_y + 3
    footer_row  = start_y + panel_h - 3

    if mode in ("scenes", "ui"):
        names = scene_names if mode == "scenes" else ui_themes
        active = active_scene if mode == "scenes" else active_ui

        visible_rows = footer_row - list_start
        start = 0
        if ui.selection_index >= visible_rows:
            start = ui.selection_index - visible_rows + 1

        visible = names[start:start + visible_rows]

        for i, name in enumerate(visible):
            real_index = start + i
            row_y = list_start + i

            selected = (real_index == ui.selection_index)
            is_active = (name == active)

            indicator = "▸ " if selected else "  "
            marker = " ✓" if is_active else "  "
            line = ui.truncate(f"{indicator}{name}{marker}", inner_w)
            attr = curses.color_pair(ui.SELECTION) if selected else curses.color_pair(ui.PANEL_PAIR)

            try:
                ui.stdscr.addstr(row_y, start_x + 1, line.ljust(inner_w)[:inner_w], attr)
            except curses.error: pass

    elif mode == "toggles":
        from .config import get as config_get
        toggles = [
            ("Home logo",         logo_enabled),
            ("Panel Bg color",    config_get("panel_color")),
            ("Text color",        config_get("text_color")),
            ("Highlight Bg",      config_get("highlight_panel_color")),
            ("Highlight Text",    config_get("highlight_text_color")),
            ("Border Fg color",   config_get("border_fg")),
            ("Border Bg color",   config_get("border_bg")),
        ]
        for i, (label, val) in enumerate(toggles):
            row_y = list_start + i
            if row_y >= footer_row: break
            selected  = (i == ui.selection_index)
            indicator = "▸ " if selected else "  "

            status = "[ON] " if val is True else "[OFF]" if val is False else f"[{val}]"
            line = ui.truncate(f"{indicator}{label:<16}  {status}", inner_w)

            attr = curses.color_pair(ui.SELECTION) if selected else curses.color_pair(ui.PANEL_PAIR)
            try:
                ui.stdscr.addstr(row_y, start_x + 1, line.ljust(inner_w)[:inner_w], attr)
            except curses.error: pass

    try:
        ui.stdscr.addstr(footer_row, start_x, "╠" + "═" * (panel_w - 2) + "╣", curses.color_pair(ui.BORDER_PAIR))
        footer = "[Tab: switch tab] [⇅⇆: move] [Enter: select] [Esc: back]"
        ui.stdscr.addstr(footer_row + 1, start_x + 1, footer.ljust(inner_w), curses.color_pair(ui.PANEL_HINT_PAIR))
    except curses.error: pass

    if getattr(ui, "error_message", None):
        ui.stdscr.addstr(max_y - 2, 0, f" Error: {ui.error_message} ".ljust(max_x), curses.color_pair(ui.YELLOW) | curses.A_BOLD)
