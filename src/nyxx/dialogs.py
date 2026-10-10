"""Native OS dialogs (file picker, color picker) used by the theme screen.

These briefly suspend curses so a native window can take over the
terminal, then restore curses state afterwards.
"""
import curses
import os
import subprocess
import sys

from .background import IMAGE_EXTENSIONS


class DialogUnavailable(Exception):
    """No dialog can be shown on this machine (tkinter missing, no
    graphical display, ...). The message is meant for the user."""


def pick_image_file(initial_path=""):
    """Ask for an image file. Returns its path, or None if cancelled."""
    initial_dir = os.path.dirname(initial_path) if initial_path else os.path.expanduser("~")
    if sys.platform == "win32":
        return _pick_image_file_windows(initial_dir)
    return _pick_image_file_tk(initial_dir)


def _pick_image_file_windows(initial_dir):
    """Use PowerShell to trigger the native Windows file picker."""
    patterns = ";".join("*" + ext for ext in IMAGE_EXTENSIONS)
    # Inside a single-quoted PowerShell string only ' needs escaping ('').
    # The output is forced to UTF-8 (and decoded as such below) so a path
    # with non-ASCII characters isn't garbled by the console code page.
    ps_command = f"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Add-Type -AssemblyName System.Windows.Forms
    $fd = New-Object System.Windows.Forms.OpenFileDialog
    $fd.InitialDirectory = '{initial_dir.replace("'", "''")}'
    $fd.Filter = 'Image Files|{patterns}|All Files|*.*'
    $fd.ShowDialog() | Out-Null
    $fd.FileName
    """
    try:
        result = subprocess.run(
            # -NoProfile: anything the user's profile prints would end up
            # mixed into the path read back from stdout.
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding="utf-8-sig",
        )
        path = result.stdout.strip()
        return path if path else None
    except Exception:
        return None


def _pick_image_file_tk(initial_dir):
    root = _tk_root()
    try:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=root,
            title="Choose a background image",
            initialdir=initial_dir,
            filetypes=[
                ("Image files", " ".join("*" + ext for ext in IMAGE_EXTENSIONS)),
                ("All files", "*"),
            ],
        )
    finally:
        root.destroy()
    return path or None


def _tk_root():
    """A hidden, topmost Tk root window to host a dialog."""
    # Imported lazily: tkinter costs real startup time and most sessions
    # never open a dialog.
    try:
        import tkinter as tk
    except ImportError:
        raise DialogUnavailable(
            "tkinter isn't installed (on Debian/Ubuntu: sudo apt install python3-tk)"
        ) from None
    try:
        root = tk.Tk()
    except tk.TclError:
        raise DialogUnavailable("no graphical display to show it on") from None
    root.withdraw()
    root.attributes('-topmost', True)
    return root


def _rgb_to_xterm(r, g, b):
    if r == g == b:
        if r < 8: return 16
        if r > 248: return 231
        return round(((r - 8) / 247) * 24) + 232

    r_step = int(round((r / 255.0) * 5))
    g_step = int(round((g / 255.0) * 5))
    b_step = int(round((b / 255.0) * 5))
    return 16 + (36 * r_step) + (6 * g_step) + b_step


def pick_color_gui():
    """Returns the picked color as an xterm-256 index, or None if cancelled.
    Raises DialogUnavailable if no color dialog can be shown."""
    curses.def_prog_mode()
    curses.endwin()
    try:
        root = _tk_root()
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Pick a Color", parent=root)
        finally:
            root.destroy()
    finally:
        # Restore curses even when tkinter is missing or there's no display.
        curses.reset_prog_mode()

    if color[0]:
        r, g, b = [int(c) for c in color[0]]
        return _rgb_to_xterm(r, g, b)
    return None
