# NYXX

A terminal-based directory navigator built with Python and curses. Navigate your filesystem, save frequently visited locations, store reusable shell commands, and set any image as your terminal background — all without leaving the keyboard.

<img width="1549" height="740" alt="nyxx screenshot" src="https://github.com/user-attachments/assets/596eb2aa-2d6f-476e-9ef1-71158511cea1" />

```
nyxx cd       — visual directory browser
nyxx jump     — saved locations
nyxx memo     — saved commands
nyxx theme    — backgrounds, scenes, and panel colors
```

---

## Install

### Windows (Recommended)

Download the latest `Nyxx_Setup.exe` from the [Releases](https://github.com/DanIrl7/nyxx/releases) page and run it.

The installer will:

- Install Nyxx to `C:\Program Files\Nyxx`
- Add `nyxx` to your PATH so it works from any terminal
- Automatically configure your PowerShell profile with the shell wrapper
- Optionally create a desktop shortcut

After installing, open a **new** PowerShell window and type `nyxx`.

> **Tip:** For the best visual experience use [Windows Terminal](https://aka.ms/terminal) or [Fluent Terminal](https://github.com/felixse/FluentTerminal) instead of the default PowerShell window. They support true color and render the block-character backgrounds correctly.

---

### Linux / macOS (From Source)

```bash
git clone https://github.com/DanIrl7/nyxx.git
cd nyxx
bash install.sh
source ~/.bashrc   # or ~/.zshrc if you use zsh
```

The install script handles the virtual environment, dependencies, config directory, and shell integration automatically.

---

## Usage

### Directory Navigator

```bash
nyxx cd
```

Browse your filesystem visually. Directories are listed first, files have type icons. Press `Space` to jump to the highlighted directory. Press `c` to copy, `x` to cut, and `v` to paste files directly from the panel.

### Saved Locations

```bash
nyxx jump              # open the saved locations panel
nyxx jump <name>       # jump directly to a saved location
nyxx jump add          # save current directory with a name
```

### Saved Commands

```bash
nyxx memo              # open the saved commands panel
nyxx memo <name>       # run a saved command directly
nyxx memo add          # save a new command with a name
```

### Theme & Background

```bash
nyxx theme
```

Opens a panel with three tabs:

| Tab         | What it does                                                                           |
| ----------- | -------------------------------------------------------------------------------------- |
| Backgrounds | Select a full-screen background image or choose "Browse File..." to select a custom one |
| Toggles     | Toggle the Home logo and individual panel component color features                    |
| Panels      | Switch between built-in UI color palettes/presets (e.g., Cyber Cyan, Matrix Green, etc.)|

---

## Keybindings

| Key                    | Action                                           |
| ---------------------- | ------------------------------------------------ |
| `↑` `↓` or `k` `j`     | Move selection up / down                         |
| `→` `l` or `Enter`     | Enter directory / confirm                        |
| `←` `h` or `Backspace` | Go up a directory / go back                      |
| `Space`                | Jump to selected directory                       |
| `.`                    | Toggle hidden files                              |
| `c`                    | Copy highlighted item                            |
| `x`                    | Cut highlighted item                             |
| `v`                    | Paste item into current directory                |
| `d`                    | Delete selected jump or memo (with confirmation) |
| `Tab`                  | Switch tabs in the theme panel                   |
| `z`                    | Open help screen                                 |
| `q` or `Esc`           | Quit                                             |

---

## Backgrounds

Nyxx renders full-screen background images directly in your terminal using a custom vectorised quad-pixel/half-block rendering engine. 

### Supported Formats
Nyxx can load and display any image in **JPG, PNG, WebP, BMP, GIF, or TIFF** format.

### Resolution & Color Quantization
* **Resolution**: Images are dynamically resized and rendered at double vertical resolution using the `▄` and other quad-pixel Unicode characters (e.g., `▗`, `▖`, `▝`, `▐`, `▞`, `▟`, etc.) to fit your exact terminal window dimensions.
* **Color Quantization**: The rendering engine quantizes images down to 14 colors and maps them using standard or custom terminal color pairs, creating a beautifully stylized terminal-art aesthetic.

---

## Customizing Backgrounds & UI Themes

You can customize both the background scenes and the panel UI presets.

### Adding a New Background Scene
To add a new background scene to the selector tab:
1. Simply place your image file (e.g., `my_background.jpg`) inside the `assets/backgrounds/` directory.
2. Nyxx will automatically scan this directory on startup, convert the filename to a title (e.g., `My Background`), and list it under the **Backgrounds** tab.

Alternatively, you can select the **Browse File...** option from the Backgrounds tab to open a native file picker and load any image from your system.

### Adding a New UI Panel Theme
If you want to add a new preset panel color scheme, open `src/nyxx/ui.py` and add an entry to the `UI_THEMES` dictionary:

```python
"your theme name": {
    "border": curses.COLOR_CYAN,
    "text": curses.COLOR_WHITE,
    "highlight": curses.COLOR_CYAN,
    "hint": curses.COLOR_YELLOW,
    "bg": curses.COLOR_BLACK
}
```
The application will automatically pick up your new theme and add it to the **Panels** tab selection list.

---

## Config

All persistent data lives in `~/.nyxx/`:

| File          | Contents                                                     |
| ------------- | ------------------------------------------------------------ |
| `config.json` | Active theme, background mode, panel colors, last image path |
| `jumps.json`  | Saved locations                                              |
| `memos.json`  | Saved commands                                               |

---

## Manual Install (Linux / macOS)

```bash
# 1. Clone the repo
git clone https://github.com/DanIrl7/nyxx.git
cd nyxx

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create config directory
mkdir -p ~/.nyxx
echo "[]" > ~/.nyxx/jumps.json
echo "[]" > ~/.nyxx/memos.json
cat > ~/.nyxx/config.json << 'EOF'
{
  "sky_theme": "starry night",
  "ground_theme": "city",
  "sky_enabled": true,
  "ground_enabled": true,
  "bg_mode": "layered"
}
EOF

# 5. Add the shell function manually
# Copy the nyxx() function from shell_integrations/nyxx.sh into your ~/.bashrc or ~/.zshrc
# Then update SCRIPT_DIR and PYTHON_BIN inside it to match your actual paths

source ~/.bashrc
```

---

## Requirements

- Python 3.8+
- A terminal with UTF-8 support
- Windows: `windows-curses` is installed automatically via `requirements.txt`
- Custom image backgrounds: `Pillow` (`pip install Pillow`) — included in `requirements.txt`

---

## License

MIT — see [LICENSE](LICENSE)
