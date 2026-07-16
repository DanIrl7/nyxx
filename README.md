
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

Opens a panel with five tabs:

| Tab | What it does |
| --- | --- |
| Sky | Choose a sky particle theme (layered mode) |
| Ground | Choose a ground theme (layered mode) |
| Toggles | Toggle sky/ground layers on or off, enable/disable the logo |
| Scenes | Switch to a full-screen scene (Vaporwave Sunset or a custom image) |
| Panels | Customise panel background, text, highlight, and border colors |

---

## Keybindings

| Key | Action |
| --- | --- |
| `↑` `↓` or `k` `j` | Move selection up / down |
| `→` `l` or `Enter` | Enter directory / confirm |
| `←` `h` or `Backspace` | Go up a directory / go back |
| `Space` | Jump to selected directory |
| `.` | Toggle hidden files |
| `c` | Copy highlighted item |
| `x` | Cut highlighted item |
| `v` | Paste item into current directory |
| `d` | Delete selected jump or memo (with confirmation) |
| `Tab` | Switch tabs in the theme panel |
| `z` | Open help screen |
| `q` or `Esc` | Quit |

---

## Backgrounds

Nyxx has two background modes that are switched from the theme panel.

### Layered Mode

Two independent layers — sky on top, ground on the bottom — that you can mix, match, and toggle independently.

**Sky themes:** Starry Night, Vaporwave, Matrix, Sunset, Rainy Day

**Ground themes:** City Skyscrapers, Beach, Forest, Ranch, Ocean

### Scene Mode

A single full-screen background that replaces the layered system entirely.

**Built-in scene:** Vaporwave Sunset — a procedurally generated pink and blue sunset with a palm tree silhouette, rendered using Unicode half-block characters.

**Custom image:** Select any image from your filesystem (JPG, PNG, WebP, BMP, GIF, TIFF). Nyxx quantizes it to 14 colors and renders it at double vertical resolution using the `▄` half-block technique, fitting it to your exact terminal dimensions automatically.

### Panel Colors

The Panels tab in the theme editor lets you pick custom colors for:
- Panel background
- Panel text
- Highlighted item background and text
- Border foreground and background

Colors are chosen from a native color picker and saved to config. They persist across sessions and are applied independently of whichever background mode is active.

---

## How to Add a Theme

### Adding a sky theme

Open `src/nyxx/background.py` and add a new entry to `SKY_THEMES`:

```python
"your theme name": {
    "label":            "Your Theme Name",
    "color_pairs":      [5, 6, 7],        # [bright, mid, dim] — reuse existing pairs or add new ones in ui.py
    "glow_pair":        9,                # color pair for the horizon glow line
    "glow_char":        "▁",             # character used for the glow row
    "density":          0.04,             # fraction of sky cells that get a particle (0.0–1.0)
    "particle_chars":   ["✦", "·", "*"], # characters scattered across the sky
    "ascii_chars":      ["+", ".", "*"],  # fallback for terminals without unicode
    "particle_weights": [2, 6, 3],        # probability weights matching particle_chars
},
```

### Adding a ground theme

Add a new entry to `GROUND_THEMES`:

```python
"your ground theme": {
    "label":          "Your Ground Theme",
    "color_pair":     31,
    "accent_pair":    32,
    "highlight_pair": 33,
    "detail_fn":      "beach_surf",   # reuse an existing renderer or add your own
    "tallest":        8,
    "layers": [
        {"h": 2, "chars": "▓▓▓▓▓▓", "color": "main",      "bold": True,  "dim": False},
        {"h": 2, "chars": "≈ ~ ≈ ~", "color": "accent",    "bold": False, "dim": False},
        {"h": 1, "chars": "~ ≋ ~ ≋", "color": "highlight", "bold": True,  "dim": False},
    ],
},
```

If you need new colors, add a `curses.init_pair(N, ...)` line in `UIEngine.__init__()` in `ui.py` and reference that number in your theme. The theme selector picks up new entries automatically — no other files need to change.

---

## Config

All persistent data lives in `~/.nyxx/`:

| File | Contents |
| --- | --- |
| `config.json` | Active theme, background mode, panel colors, last image path |
| `jumps.json` | Saved locations |
| `memos.json` | Saved commands |

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
```

The main additions compared to your original are the Windows installer section at the top, the copy/cut/paste keybindings, the `z` help key, the full Scenes and Panels tab descriptions in the theme section, and the updated config table that includes the new keys added during development.
