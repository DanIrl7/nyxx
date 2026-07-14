# nyxx

A terminal-based directory navigator built with Python and curses. Navigate your filesystem, save frequently visited locations, store reusable shell commands, and customise your terminal background — all without leaving the keyboard.

<img width="1501" height="748" alt="image" src="https://github.com/user-attachments/assets/540d3c0d-66b4-40e0-af3b-d01d7c4b20e1" />



```

nyxx cd       — visual directory browser
nyxx jump     — saved locations
nyxx memo     — saved commands
nyxx theme    — sky + ground themes

```

---

## Install

```bash
git clone [https://github.com/DanIrl7/nyxx.git](https://github.com/DanIrl7/nyxx.git)
cd nyxx
bash install.sh
source ~/.bashrc   # or ~/.zshrc if you use zsh

```

That's it. The install script handles the virtual environment, dependencies, config directory, and shell integration automatically.

---

## Usage

--For the best visual experienve it highly recommended you use a program like windows terminal or fluent terminal


### Directory Navigator

```bash
nyxx cd

```

Browse your filesystem visually. Directories are listed first, files have type icons. Press `Space` to jump to the highlighted directory.

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

### Theme Selector

```bash
nyxx theme

```

Opens a panel with three tabs — Sky, Ground, and Toggles. Pick from 5 sky themes and 5 ground themes independently, or toggle either layer on/off.

---

## Keybindings

| Key                    | Action                                           |
| ---------------------- | ------------------------------------------------ |
| `↑` `↓` or `k` `j`     | Move selection up / down                         |
| `→` `l` or `Enter`     | Enter directory / confirm                        |
| `←` `h` or `Backspace` | Go up a directory / go back                      |
| `Space`                | Jump to selected directory                       |
| `.`                    | Toggle hidden files                              |
| `d`                    | Delete selected jump or memo (with confirmation) |
| `Tab`                  | Switch tabs in the theme panel                   |
| `q` or `Esc`           | Quit                                             |

---

## Themes

nyxx has a two-layer theme system. Sky and ground are independent — mix and match any combination.

**Sky themes:** Starry Night, Vaporwave, Matrix, Sunset, Rainy Day

**Ground themes:** City Skyscrapers, Beach, Forest, Ranch, Ocean

Themes are saved to `~/.nyxx/config.json` and persist across sessions.

### How to add a theme

**Adding a sky theme** — open `src/nyxx/background.py` and add a new entry to `SKY_THEMES`:

```python
"your theme name": {
    "label":            "Your Theme Name",
    "color_pairs":      [5, 6, 7],        # [bright, mid, dim] — reuse existing pairs or add new ones in ui.py
    "glow_pair":        9,                # color pair for the horizon glow line
    "glow_char":        "▁",             # character used for the glow row
    "density":          0.04,             # fraction of sky cells that get a particle (0.0 – 1.0)
    "particle_chars":   ["✦", "·", "*"], # characters scattered across the sky
    "ascii_chars":      ["+", ".", "*"],  # fallback for terminals without unicode
    "particle_weights": [2, 6, 3],        # probability weights matching particle_chars order
},

```

**Adding a ground theme** — add a new entry to `GROUND_THEMES`. Layer-based themes (beach, forest, ranch, ocean style) use a `layers` list:

```python
"your ground theme": {
    "label":          "Your Ground Theme",
    "color_pair":     31,     # main color — define the pair in ui.py if new
    "accent_pair":    32,     # secondary color
    "highlight_pair": 33,     # brightest accent
    "detail_fn":      "beach_surf",   # reuse an existing renderer or add your own
    "tallest":        8,      # height in rows — used to position the sky glow line
    "layers": [
        {"h": 2, "chars": "▓▓▓▓▓▓", "color": "main",      "bold": True,  "dim": False},
        {"h": 2, "chars": "≈ ~ ≈ ~", "color": "accent",    "bold": False, "dim": False},
        {"h": 1, "chars": "~ ≋ ~ ≋", "color": "highlight", "bold": True,  "dim": False},
    ],
},

```

If you need new colors, add a `curses.init_pair(N, ...)` line in `UIEngine.__init__()` in `ui.py` and reference that number in your theme.

No other files need to change. The theme selector picks up new entries automatically.

---

## Config

All persistent data lives in `~/.nyxx/`:

| File          | Contents                               |
| ------------- | -------------------------------------- |
| `config.json` | Active sky/ground theme, layer toggles |
| `jumps.json`  | Saved locations                        |
| `memos.json`  | Saved commands                         |

---

## Manual Install

If `install.sh` doesn't work for your setup:

```bash
# 1. Clone the repo
git clone [https://github.com/DanIrl7/nyxx.git](https://github.com/DanIrl7/nyxx.git)
cd nyxx

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

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
  "ground_enabled": true
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
- A terminal with UTF-8 support (most modern terminals qualify)
- Windows: `windows-curses` is installed automatically by `requirements.txt`

---

## License

MIT — see [LICENSE](https://www.google.com/search?q=LICENSE)

```

```
