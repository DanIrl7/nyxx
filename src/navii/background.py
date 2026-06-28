# src/navii/background.py

import curses
import random


# ══════════════════════════════════════════════════════════════════════════════
# SKY THEME REGISTRY
# Each entry defines everything the sky renderer needs.
# color_pairs: [bright, mid, dim] — referenced by index into UIEngine's pairs
# particle_chars / ascii_chars: what gets scattered across the sky
# particle_weights: probability weights matching particle_chars order
# glow_pair: color pair for the horizon glow line
# glow_char: character used for the glow row
# density: fraction of sky cells that get a particle
# ══════════════════════════════════════════════════════════════════════════════
SKY_THEMES = {
    "starry night": {
        "label":            "Starry Night",
        "color_pairs":      [5, 6, 7],
        "glow_pair":        9,
        "glow_char":        "▁",
        "density":          0.04,
        "particle_chars":   ["✦", "✧", "*", "·", "◇", "★", "☆"],
        "ascii_chars":      ["+", "*", ".", ",", "o", "x", " "],
        "particle_weights": [1, 2, 3, 8, 4, 1, 2],
    },
    "vaporwave": {
        "label":            "Vaporwave",
        "color_pairs":      [13, 14, 15],
        "glow_pair":        17,
        "glow_char":        "─",
        "density":          0.035,
        # Grid lines + floating diamonds give a retro-3D feel
        "particle_chars":   ["◆", "◇", "▪", "·", "░", "▫", "★"],
        "ascii_chars":      ["#", "+", ".", "-", ":", ".", " "],
        "particle_weights": [2, 3, 4, 8, 2, 3, 1],
    },
    "matrix": {
        "label":            "Matrix",
        "color_pairs":      [18, 19, 20],
        "glow_pair":        22,
        "glow_char":        "▄",
        "density":          0.06,
        # Dense digit rain
        "particle_chars":   ["0", "1", "│", "┃", "╎", "╏", "▓", "░", "▒"],
        "ascii_chars":      ["0", "1", "|", "!", ":", ".", "#"],
        "particle_weights": [3, 3, 2, 2, 2, 4, 1, 1, 1],
    },
    "sunset": {
        "label":            "Sunset",
        "color_pairs":      [23, 24, 25],
        "glow_pair":        26,
        "glow_char":        "▀",
        "density":          0.025,
        # Scattered clouds and birds silhouettes
        "particle_chars":   ["~", "≈", "─", "∼", "⌒", "v", "ʌ"],
        "ascii_chars":      ["~", "=", "-", "~", "^", "v", " "],
        "particle_weights": [4, 3, 3, 3, 2, 2, 1],
    },
    "rainy day": {
        "label":            "Rainy Day",
        "color_pairs":      [27, 28, 29],
        "glow_pair":        30,
        "glow_char":        "░",
        "density":          0.07,
        # Vertical rain streaks, heavy density
        "particle_chars":   ["│", "╎", "╏", "┊", "┋", "·", "╷"],
        "ascii_chars":      ["|", "|", ":", ".", "'", ",", "`"],
        "particle_weights": [4, 3, 3, 2, 2, 4, 1],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# GROUND THEME REGISTRY
# Each entry defines everything the ground renderer needs.
# color_pair: main ground/structure color
# accent_pair: secondary color (windows, leaves, waves, etc.)
# highlight_pair: brightest accent (lit windows, foam, flowers, etc.)
# layers: list of row descriptors drawn bottom-up.
#   Each layer is a dict:
#     "h": int        — how many terminal rows tall this layer is
#     "chars": str    — characters tiled across the row (cycled left-to-right)
#     "color": str    — "main", "accent", or "highlight"
#     "bold": bool    — whether to apply A_BOLD
#     "dim": bool     — whether to apply A_DIM
# detail_fn: string key — which detail-drawing function to call on top
#   (None, "city_windows", "forest_canopy", "ocean_waves", "beach_surf",
#    "ranch_fence")
# tallest: int — used to position the glow row above the ground
# ══════════════════════════════════════════════════════════════════════════════
GROUND_THEMES = {
    "city": {
        "label":          "City Skyscrapers",
        "color_pair":     8,
        "accent_pair":    3,    # yellow windows
        "highlight_pair": 11,   # white office light
        "detail_fn":      "city_windows",
        "tallest":        25,
        "buildings": [
            {"w": 8,  "h": 14, "win": "▓"},
            {"w": 5,  "h": 8,  "win": "·"},
            {"w": 12, "h": 20, "win": "▪"},
            {"w": 6,  "h": 10, "win": "░"},
            {"w": 15, "h": 25, "win": "░"},
            {"w": 7,  "h": 12, "win": "·"},
            {"w": 10, "h": 18, "win": "▪"},
            {"w": 5,  "h": 7,  "win": "·"},
            {"w": 11, "h": 22, "win": "▓"},
            {"w": 6,  "h": 9,  "win": "·"},
            {"w": 9,  "h": 16, "win": "▪"},
            {"w": 4,  "h": 6,  "win": "·"},
            {"w": 13, "h": 21, "win": "░"},
            {"w": 7,  "h": 11, "win": "·"},
            {"w": 8,  "h": 15, "win": "▓"},
        ],
    },
    "beach": {
        "label":          "Beach",
        "color_pair":     31,   # sandy yellow
        "accent_pair":    32,   # ocean blue
        "highlight_pair": 33,   # white foam
        "detail_fn":      "beach_surf",
        "tallest":        8,
        # Layers bottom → top (index 0 = bottom row of screen)
        "layers": [
            {"h": 1, "chars": "▓▓▓▓▓▓▓▓▓▓",          "color": "main",      "bold": True,  "dim": False},
            {"h": 2, "chars": "▒▒░▒▒░▒▒░▒",           "color": "main",      "bold": False, "dim": False},
            {"h": 1, "chars": "≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~", "color": "highlight", "bold": True,  "dim": False},
            {"h": 2, "chars": "≋≈≋≈≋≈≋≈≋≈",           "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": "~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈", "color": "accent",    "bold": False, "dim": True },
        ],
    },
    "forest": {
        "label":          "Forest",
        "color_pair":     34,   # dark green
        "accent_pair":    35,   # mid green
        "highlight_pair": 36,   # bright green / yellow-green
        "detail_fn":      "forest_canopy",
        "tallest":        18,
        "layers": [
            {"h": 2, "chars": "████████████",                    "color": "main",      "bold": True,  "dim": False},
            {"h": 3, "chars": "▓██▓██▓██▓██",                   "color": "main",      "bold": False, "dim": False},
            {"h": 3, "chars": "▒▓█▒▓█▒▓█▒▓█",                  "color": "accent",    "bold": False, "dim": False},
            {"h": 4, "chars": " T T T T T T T T T T ",          "color": "accent",    "bold": True,  "dim": False},
            {"h": 3, "chars": "/T\\ /T\\ /T\\ /T\\ /T\\",      "color": "highlight", "bold": False, "dim": False},
            {"h": 3, "chars": "^^^^^^^^^^^^^^^^^^^^^^^^^^^",     "color": "highlight", "bold": True,  "dim": False},
        ],
    },
    "ranch": {
        "label":          "Ranch",
        "color_pair":     37,   # brown/tan ground
        "accent_pair":    38,   # wood fence / barn red
        "highlight_pair": 39,   # sky-touching grass green
        "detail_fn":      "ranch_fence",
        "tallest":        10,
        "layers": [
            {"h": 2, "chars": "▓▓▓▓▓▓▓▓▓▓▓▓",                  "color": "main",      "bold": True,  "dim": False},
            {"h": 2, "chars": "▒▒▒▒▒▒▒▒▒▒▒▒",                  "color": "main",      "bold": False, "dim": False},
            {"h": 1, "chars": "─┤ ├─┤ ├─┤ ├─┤ ├─",             "color": "accent",    "bold": True,  "dim": False},
            {"h": 1, "chars": " │   │   │   │   │ ",            "color": "accent",    "bold": False, "dim": False},
            {"h": 1, "chars": "─┤ ├─┤ ├─┤ ├─┤ ├─",             "color": "accent",    "bold": True,  "dim": False},
            {"h": 1, "chars": " │   │   │   │   │ ",            "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": ".,.,.,wWwWw.,.,.,wWwWw",         "color": "highlight", "bold": False, "dim": False},
        ],
    },
    "ocean": {
        "label":          "Ocean",
        "color_pair":     40,   # deep blue
        "accent_pair":    41,   # mid blue
        "highlight_pair": 42,   # white foam / bright
        "detail_fn":      "ocean_waves",
        "tallest":        10,
        "layers": [
            {"h": 2, "chars": "████████████",                    "color": "main",      "bold": True,  "dim": False},
            {"h": 2, "chars": "▓▓▓▓▓▓▓▓▓▓▓▓",                  "color": "main",      "bold": False, "dim": False},
            {"h": 2, "chars": "≋≋≈≋≋≈≋≋≈≋≋≈",                  "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": "≈ ~ ≈ ~ ≈ ~ ≈ ~",               "color": "accent",    "bold": True,  "dim": False},
            {"h": 2, "chars": "~ ≋ ~ ≋ ~ ≋ ~ ≋",               "color": "highlight", "bold": True,  "dim": False},
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class BackgroundEngine:

    def __init__(self, stdscr,
                 sky_theme="starry night",
                 ground_theme="city",
                 sky_enabled=True,
                 ground_enabled=True):
        self.stdscr       = stdscr
        self.sky_enabled    = sky_enabled
        self.ground_enabled = ground_enabled
        self.ascii_mode     = False
        self.max_y, self.max_x = stdscr.getmaxyx()

        self._set_sky(sky_theme)
        self._set_ground(ground_theme)
        self._generate()

    # ── Theme setters ──────────────────────────────────────────────────────

    def _set_sky(self, name):
        self.sky_name  = name
        self.sky_theme = SKY_THEMES.get(name, SKY_THEMES["starry night"])

    def _set_ground(self, name):
        self.ground_name  = name
        self.ground_theme = GROUND_THEMES.get(name, GROUND_THEMES["city"])

    def set_sky(self, name):
        """Switch sky theme and regenerate."""
        self._set_sky(name)
        self._generate()

    def set_ground(self, name):
        """Switch ground theme and regenerate."""
        self._set_ground(name)
        self._generate()

    def set_sky_enabled(self, enabled):
        self.sky_enabled = enabled

    def set_ground_enabled(self, enabled):
        self.ground_enabled = enabled

    # ── Unicode detection ──────────────────────────────────────────────────

    def _detect_unicode(self):
        try:
            self.stdscr.addstr(0, 0, "✦")
            self.ascii_mode = False
        except curses.error:
            self.ascii_mode = True

    # ── Pre-generation ─────────────────────────────────────────────────────

    def _generate(self):
        """Pre-calculate all static sky particles."""
        self._detect_unicode()
        rows, cols = self.max_y, self.max_x
        sky  = self.sky_theme
        chars = sky["ascii_chars"] if self.ascii_mode else sky["particle_chars"]
        weights = sky["particle_weights"][:len(chars)]

        sky_rows    = int(rows * 0.75)
        total_cells = sky_rows * cols
        count       = int(total_cells * sky["density"])

        self.particles = []
        for _ in range(count):
            y    = random.randint(0, sky_rows - 1)
            x    = random.randint(0, cols - 2)
            char = random.choices(chars, weights=weights, k=1)[0]
            pair = random.choice(sky["color_pairs"])
            self.particles.append((y, x, char, pair))

    # ── Sky drawing ────────────────────────────────────────────────────────

    def _draw_sky(self):
        """Draw scattered particles and horizon glow for current sky theme."""
        sky = self.sky_theme

        # Particles
        for (y, x, char, pair) in self.particles:
            try:
                self.stdscr.addstr(y, x, char, curses.color_pair(pair))
            except curses.error:
                pass

        # Horizon glow — sits just above the ground layer
        rows, cols = self.stdscr.getmaxyx()
        tallest    = self.ground_theme.get("tallest", 10) if self.ground_enabled else 2
        glow_row   = rows - tallest - 2
        if glow_row >= 0:
            glow_char = sky.get("glow_char", "▁")
            for c in range(0, cols - 1):
                char = glow_char if c % 3 == 0 else " "
                try:
                    self.stdscr.addstr(
                        glow_row, c, char,
                        curses.color_pair(sky["glow_pair"]) | curses.A_DIM
                    )
                except curses.error:
                    pass

    # ── Ground drawing ─────────────────────────────────────────────────────

    def _draw_ground(self):
        """Dispatch to the correct ground renderer based on detail_fn."""
        fn_name = self.ground_theme.get("detail_fn")
        dispatch = {
            "city_windows":  self._draw_city,
            "beach_surf":    self._draw_layers,
            "forest_canopy": self._draw_layers,
            "ranch_fence":   self._draw_layers,
            "ocean_waves":   self._draw_layers,
        }
        fn = dispatch.get(fn_name, self._draw_layers)
        fn()

    def _color_attr(self, color_key, bold=False, dim=False):
        """Resolve a color key string to a curses attribute."""
        g = self.ground_theme
        pair_map = {
            "main":      g["color_pair"],
            "accent":    g["accent_pair"],
            "highlight": g["highlight_pair"],
        }
        pair = pair_map.get(color_key, g["color_pair"])
        attr = curses.color_pair(pair)
        if bold:
            attr |= curses.A_BOLD
        if dim:
            attr |= curses.A_DIM
        return attr

    def _draw_layers(self):
        """
        Generic layer renderer — used by beach, forest, ranch, ocean.
        Reads the 'layers' list from the ground theme and tiles each
        layer's chars across the screen width, bottom-up.
        """
        rows, cols = self.stdscr.getmaxyx()
        g      = self.ground_theme
        layers = g.get("layers", [])

        current_row = rows - 1   # start at the very bottom

        for layer in layers:
            h     = layer["h"]
            chars = layer["chars"]
            attr  = self._color_attr(layer["color"], layer.get("bold", False), layer.get("dim", False))
            chars_len = len(chars)

            for row_offset in range(h):
                row = current_row - row_offset
                if row < 0:
                    break
                # Tile the chars string across the full width
                line = (chars * (cols // chars_len + 2))[:cols - 1]
                try:
                    self.stdscr.addstr(row, 0, line, attr)
                except curses.error:
                    pass

            current_row -= h

    def _draw_city(self):
        """
        City-specific renderer — buildings with individually lit windows.
        Kept separate because the logic is per-building, not per-layer.
        """
        rows, cols = self.stdscr.getmaxyx()
        g         = self.ground_theme
        buildings = g.get("buildings", [])
        main_attr = curses.color_pair(g["color_pair"])
        acc_attr  = curses.color_pair(g["accent_pair"])
        hi_attr   = curses.color_pair(g["highlight_pair"])

        col   = 0
        b_idx = 0
        while col < cols - 1:
            b = buildings[b_idx % len(buildings)]
            w = min(b["w"], cols - col - 1)
            h = b["h"]
            b_idx += 1

            for row_offset in range(h):
                row = rows - 1 - row_offset
                if row < 0 or row >= rows - 1:
                    continue

                if row_offset == 0:
                    # Ground floor
                    try:
                        self.stdscr.addstr(row, col, "▀" * w, main_attr | curses.A_BOLD)
                    except curses.error:
                        pass

                elif row_offset == h - 1:
                    # Rooftop
                    roof = ("▄" + "─" * (w - 2) + "▄") if w > 2 else "▄" * w
                    try:
                        self.stdscr.addstr(row, col, roof, main_attr | curses.A_BOLD)
                    except curses.error:
                        pass

                else:
                    # Mid floors — walls then windows on top
                    try:
                        self.stdscr.addstr(row, col, "█" * w, main_attr)
                    except curses.error:
                        pass
                    for wc in range(1, w - 1, 2):
                        lit = (row * 7 + (col + wc) * 3) % 5 != 0
                        win_attr = acc_attr if lit else (main_attr | curses.A_DIM)
                        # Every 4th lit window gets bright highlight
                        if lit and (row + col + wc) % 4 == 0:
                            win_attr = hi_attr
                        try:
                            self.stdscr.addstr(row, col + wc, b["win"], win_attr)
                        except curses.error:
                            pass

            col += b["w"] + 1

    # ── Public draw ────────────────────────────────────────────────────────

    def draw(self):
        """Draw enabled layers in order: sky first, ground on top."""
        if self.sky_enabled:
            self._draw_sky()
        if self.ground_enabled:
            self._draw_ground()

    def handle_resize(self):
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self._generate()