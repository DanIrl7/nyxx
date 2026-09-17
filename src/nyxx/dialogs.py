"""Native OS dialogs (file picker, color picker) used by the theme screen.

These briefly suspend curses so a native window can take over the
terminal, then restore curses state afterwards.
"""
import curses
import os
import subprocess


def pick_image_file(initial_path=""):
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


def pick_color_gui():
    # Imported lazily: tkinter costs real startup time and most sessions
    # never open the color picker.
    import tkinter as tk
    from tkinter import colorchooser

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
