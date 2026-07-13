# nyxx

A terminal-based directory navigator built with Python and curses. Navigate your filesystem, save frequently visited locations, store reusable shell commands, and customise your terminal background — all without leaving the keyboard.

```text
nyxx cd       — visual directory browser
nyxx jump     — saved locations
nyxx memo     — saved commands
nyxx theme    — sky + ground themes
```

## Installation

### Windows (Recommended)

Download the latest `Navii_Setup_v1.0.exe` from our releases page:
https://github.com/DanIrl7/nyxx/releases

Running this installer will set up the application and ensure all necessary assets are in the correct location.

### Manual / Source Install

```bash
git clone https://github.com/DanIrl7/nyxx.git
cd nyxx
bash install.sh
source ~/.bashrc   # or ~/.zshrc if you use zsh
```

## Usage

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

## Keybindings

| Key | Action |
|------|--------|
| `↑` `↓` or `k` `j` | Move selection up / down |
| `→` `l` or `Enter` | Enter directory / confirm |
| `←` `h` or `Backspace` | Go up a directory / go back |
| `Space` | Jump to selected directory |
| `.` | Toggle hidden files |
| `d` | Delete selected jump or memo (with confirmation) |
| `Tab` | Switch tabs in the theme panel |
| `q` or `Esc` | Quit |

## Themes

nyxx has a two-layer theme system. Sky and ground are independent — mix and match any combination.

**Sky themes:** Starry Night, Vaporwave, Matrix, Sunset, Rainy Day

**Ground themes:** City Skyscrapers, Beach, Forest, Ranch, Ocean

Themes are saved to `~/.nyxx/config.json` (Windows: your User Profile directory) and persist across sessions.

### How to add a theme

**Adding a sky theme** — add a new entry to `SKY_THEMES` in `src/nyxx/background.py`:

```python
"your theme name": {
    "label": "Your Theme Name",
    "color_pairs": [5, 6, 7],
    "glow_pair": 9,
    "glow_char": "▁",
    "density": 0.04,
    "particle_chars": ["✦", "·", "*"],
    "ascii_chars": ["+", ".", "*"],
    "particle_weights": [2, 6, 3],
},
```

**Adding a ground theme** — add a new entry to `GROUND_THEMES`:

```python
"your ground theme": {
    "label": "Your Ground Theme",
    "color_pair": 31,
    "accent_pair": 32,
    "highlight_pair": 33,
    "detail_fn": "beach_surf",
    "tallest": 8,
    "layers": [
        {"h": 2, "chars": "▓▓▓▓▓▓", "color": "main", "bold": True, "dim": False},
        {"h": 2, "chars": "≈ ~ ≈ ~", "color": "accent", "bold": False, "dim": False},
        {"h": 1, "chars": "~ ≋ ~ ≋", "color": "highlight", "bold": True, "dim": False},
    ],
},
```

## Configuration & Data

| File | Contents |
|------|----------|
| `config.json` | Active sky/ground theme, layer toggles |
| `jumps.json` | Saved locations |
| `memos.json` | Saved commands |

## Requirements

- Python 3.8+
- A terminal with UTF-8 support
- Windows: `windows-curses` (included in source install requirements)
