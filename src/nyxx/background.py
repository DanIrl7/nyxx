import curses
import random
import math
import numpy as np
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════════
# CHARACTER DICTIONARIES
# ══════════════════════════════════════════════════════════════════════════════

# Quad-pixel dict: key = 4-bit integer (TL=bit3, TR=bit2, BL=bit1, BR=bit0)
# Each terminal cell = 2×2 virtual pixels. The glyph encodes which sub-pixels
# are "foreground" (on) vs "background" (off).
QUAD_PIXEL_DICT = {
    0:  " ",  1:  "▗",  2:  "▖",  3:  "▄",
    4:  "▝",  5:  "▐",  6:  "▞",  7:  "▟",
    8:  "▘",  9:  "▚",  10: "▌",  11: "▙",
    12: "▀",  13: "▜",  14: "▛",  15: "█",
}

# Shading dict: for full-cell gradient fills (sky, sun, water).
# Index 0–4 maps brightness 0.0–1.0 to increasing density.
SHADE_DICT = [" ", "░", "▒", "▓", "█"]

# Vertical smooth dict: for wave heightmaps if you add them later.
VERTICAL_SMOOTH_DICT = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

# ══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE
#
# Pair ID allocation (0–255 total):
#   1–7    : UIEngine panel / border / hint pairs  (ui.py)
#   8–203  : Scene renderer (vaporwave palette + user image combos)
#   204–235: Layered-theme sky / ground pairs       (registered in ui.py)
#
# PALETTE_8 is the fallback for 8-color terminals — each entry is a standard
# curses color constant approximating the target hue.
#
# PALETTE_256 is used on 256-color terminals that support can_change_color().
# Each entry is (r, g, b) in curses units (0–1000).
# The pair id for palette index i is BASE_PAIR + i.
# ══════════════════════════════════════════════════════════════════════════════

BASE_PAIR = 8  # first curses pair id owned by the scene renderer

# Vaporwave sunset palette — 24 colors, ordered dark→bright within each zone.
# Zones: [0–5] deep sky, [6–11] sun glow / horizon, [12–17] sun disc,
#         [18–20] water, [21–23] palm silhouette
VAPORWAVE_PALETTE_256 = [
    # 0-5: Deep Sky (Black/Navy fading to bright Teal/Cyan)
    (10,   10,   30),    # 0 Void black/navy
    (20,   40,   100),   # 1 Deep space blue
    (30,   150,  250),   # 2 Dark teal
    (40,   300,  400),   # 3 Mid teal
    (50,   450,  550),   # 4 Bright teal
    (100,  600,  700),   # 5 Cyan horizon glow

    # 6-11: Horizon / Sky Transition (Pink to Magenta)
    (500,  100,  400),   # 6 Deep purple
    (700,  150,  500),   # 7 Magenta
    (900,  200,  600),   # 8 Bright magenta
    (1000, 300,  650),   # 9 Hot pink
    (1000, 450,  700),   # 10 Light neon pink
    (1000, 600,  800),   # 11 Pale pink highlight

    # 12-17: Sun (Pink bottom fading to Pale Yellow top)
    (1000, 200,  500),   # 12 Deep pink (sun bottom)
    (1000, 400,  500),   # 13 Orange-pink
    (1000, 600,  400),   # 14 Golden orange
    (1000, 800,  300),   # 15 Bright yellow
    (1000, 900,  500),   # 16 Pale yellow
    (1000, 950,  800),   # 17 Near-white (sun top)

    # 18-20: Water & Reflections
    (20,   100,  250),   # 18 Deep water (dark teal base)
    (1000, 300,  600),   # 19 Pink water reflection (wide)
    (1000, 800,  400),   # 20 Yellow water reflection (core)

    # 21-23: Palm Silhouette (Black with subtle magenta/teal rim light)
    (10,   10,   20),    # 21 Core silhouette black
    (700,  150,  500),   # 22 Magenta rim light (fronds)
    (30,   150,  250),   # 23 Teal rim light (trunk)
]

# 8-color fallback: same 24 slots, each mapped to nearest standard color.
VAPORWAVE_PALETTE_8 = [
    # deep sky
    curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLUE,
    curses.COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_CYAN,
    # sun glow / horizon
    curses.COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA,
    curses.COLOR_MAGENTA, curses.COLOR_RED,     curses.COLOR_RED,
    # sun disc
    curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_YELLOW,
    curses.COLOR_WHITE,  curses.COLOR_WHITE,  curses.COLOR_WHITE,
    # water
    curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_MAGENTA,
    # palm
    curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLUE,
]


# ══════════════════════════════════════════════════════════════════════════════
# SCENE REGISTRY
# A "scene" is a full-screen unified background — no sky/ground split.
# build_fn: which _build_*() method to call to populate the framebuffer.
# palette_256: list of (r,g,b) entries (0–1000 scale) for 256-color mode.
# palette_8:   list of standard curses COLOR_* constants for 8-color fallback.
# ══════════════════════════════════════════════════════════════════════════════def load_scene_themes():
def load_scene_themes():
        themes = {
            # Keep the native file picker as the first option
            "user image": {
                "label": "Browse File...",
                "build_fn": "user_image",
                "palette_256": [],
                "palette_8": [],
            }
        }
        
        # 1. Resolve the path to a new 'assets/backgrounds' folder in your project root
        try:
            project_root = Path(__file__).resolve().parent.parent.parent
            bg_dir = project_root / "assets" / "backgrounds"
            
            # Auto-create the folder if it doesn't exist yet
            bg_dir.mkdir(parents=True, exist_ok=True)
            
            # 2. Scan the folder for any image files
            for ext in ('*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp'):
                for img_path in bg_dir.glob(ext):
                    # Use the filename (without extension) as the scene name
                    scene_name = img_path.stem.lower()
                    
                    themes[scene_name] = {
                        "label": img_path.stem.replace("_", " ").title(),
                        "build_fn": "user_image",         # Reuse your existing image renderer
                        "image_path": str(img_path),      # Store the path
                        "palette_256": [],
                        "palette_8": []
                    }
        except Exception:
            pass
        
        return themes




SCENE_THEMES = load_scene_themes()

# ══════════════════════════════════════════════════════════════════════════════
# LAYERED THEME REGISTRIES (sky + ground — unchanged from before)
# ══════════════════════════════════════════════════════════════════════════════
SKY_THEMES = {
    "starry night": {
        "label":            "Starry Night",
        "color_pairs":      [5, 6, 7],
        "glow_pair":        204,
        "glow_char":        "▁",
        "density":          0.04,
        "particle_chars":   ["✦", "✧", "*", "·", "◇", "★", "☆"],
        "ascii_chars":      ["+", "*", ".", ",", "o", "x", " "],
        "particle_weights": [1, 2, 3, 8, 4, 1, 2],
    },
    "vaporwave": {
        "label":            "Vaporwave",
        "color_pairs":      [205, 206, 207],
        "glow_pair":        208,
        "glow_char":        "─",
        "density":          0.035,
        "particle_chars":   ["◆", "◇", "▪", "·", "░", "▫", "★"],
        "ascii_chars":      ["#", "+", ".", "-", ":", ".", " "],
        "particle_weights": [2, 3, 4, 8, 2, 3, 1],
    },
    "matrix": {
        "label":            "Matrix",
        "color_pairs":      [209, 210, 211],
        "glow_pair":        212,
        "glow_char":        "▄",
        "density":          0.06,
        "particle_chars":   ["0", "1", "│", "┃", "╎", "╏", "▓", "░", "▒"],
        "ascii_chars":      ["0", "1", "|", "!", ":", ".", "#"],
        "particle_weights": [3, 3, 2, 2, 2, 4, 1, 1, 1],
    },
    "sunset": {
        "label":            "Sunset",
        "color_pairs":      [213, 214, 215],
        "glow_pair":        216,
        "glow_char":        "▀",
        "density":          0.025,
        "particle_chars":   ["~", "≈", "─", "∼", "⌒", "v", "ʌ"],
        "ascii_chars":      ["~", "=", "-", "~", "^", "v", " "],
        "particle_weights": [4, 3, 3, 3, 2, 2, 1],
    },
    "rainy day": {
        "label":            "Rainy Day",
        "color_pairs":      [217, 218, 219],
        "glow_pair":        220,
        "glow_char":        "░",
        "density":          0.07,
        "particle_chars":   ["│", "╎", "╏", "┊", "┋", "·", "╷"],
        "ascii_chars":      ["|", "|", ":", ".", "'", ",", "`"],
        "particle_weights": [4, 3, 3, 2, 2, 4, 1],
    },
}

GROUND_THEMES = {
    "city": {
        "label":          "City Skyscrapers",
        "color_pair":     221,
        "accent_pair":    3,
        "highlight_pair": 222,
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
        "color_pair":     223,
        "accent_pair":    224,
        "highlight_pair": 225,
        "detail_fn":      "beach_surf",
        "tallest":        9,
        "layers": [
            {"h": 2, "chars": "▒░▒▒░▒░▒▒░",          "color": "main",      "bold": True,  "dim": False},
            {"h": 1, "chars": "≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~", "color": "highlight", "bold": True,  "dim": False},
            {"h": 2, "chars": "≋≈≋≈≋≈≋≈≋≈",           "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": "~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈", "color": "accent",    "bold": False, "dim": True },
        ],
        "palms":    [{"x_frac": 0.10, "lean": -1, "h": 3},
                     {"x_frac": 0.88, "lean": 1,  "h": 3}],
        "umbrella": {"x_frac": 0.32},
        "crab":     {"x_frac": 0.58},
        "shells":   [0.20, 0.45, 0.70, 0.78],
        "gulls":    [{"x_frac": 0.40, "row_from_top": 1},
                     {"x_frac": 0.60, "row_from_top": 3},
                     {"x_frac": 0.75, "row_from_top": 0}],
    },
    "forest": {
        "label":          "Forest",
        "color_pair":     226,
        "accent_pair":    227,
        "highlight_pair": 228,
        "detail_fn":      "forest_canopy",
        "tallest":        18,
        "layers": [
            {"h": 2, "chars": "████████████",               "color": "main",      "bold": True,  "dim": False},
            {"h": 3, "chars": "▓██▓██▓██▓██",              "color": "main",      "bold": False, "dim": False},
            {"h": 3, "chars": "▒▓█▒▓█▒▓█▒▓█",             "color": "accent",    "bold": False, "dim": False},
            {"h": 4, "chars": " T T T T T T T T T T ",     "color": "accent",    "bold": True,  "dim": False},
            {"h": 3, "chars": "/T\\ /T\\ /T\\ /T\\ /T\\", "color": "highlight", "bold": False, "dim": False},
            {"h": 3, "chars": "^^^^^^^^^^^^^^^^^^^^^^^^^^^", "color": "highlight", "bold": True,  "dim": False},
        ],
    },
    "ranch": {
        "label":          "Ranch",
        "color_pair":     229,
        "accent_pair":    230,
        "highlight_pair": 231,
        "detail_fn":      "ranch_fence",
        "tallest":        10,
        "layers": [
            {"h": 2, "chars": "▓▓▓▓▓▓▓▓▓▓▓▓",           "color": "main",      "bold": True,  "dim": False},
            {"h": 2, "chars": "▒▒▒▒▒▒▒▒▒▒▒▒",           "color": "main",      "bold": False, "dim": False},
            {"h": 1, "chars": "─┤ ├─┤ ├─┤ ├─┤ ├─",      "color": "accent",    "bold": True,  "dim": False},
            {"h": 1, "chars": " │   │   │   │   │ ",     "color": "accent",    "bold": False, "dim": False},
            {"h": 1, "chars": "─┤ ├─┤ ├─┤ ├─┤ ├─",      "color": "accent",    "bold": True,  "dim": False},
            {"h": 1, "chars": " │   │   │   │   │ ",     "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": ".,.,.,wWwWw.,.,.,wWwWw",  "color": "highlight", "bold": False, "dim": False},
        ],
    },
    "ocean": {
        "label":          "Ocean",
        "color_pair":     232,
        "accent_pair":    233,
        "highlight_pair": 234,
        "detail_fn":      "ocean_waves",
        "tallest":        10,
        "layers": [
            {"h": 2, "chars": "████████████",             "color": "main",      "bold": True,  "dim": False},
            {"h": 2, "chars": "▓▓▓▓▓▓▓▓▓▓▓▓",            "color": "main",      "bold": False, "dim": False},
            {"h": 2, "chars": "≋≋≈≋≋≈≋≋≈≋≋≈",            "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": "≈ ~ ≈ ~ ≈ ~ ≈ ~",         "color": "accent",    "bold": True,  "dim": False},
            {"h": 2, "chars": "~ ≋ ~ ≋ ~ ≋ ~ ≋",         "color": "highlight", "bold": True,  "dim": False},
        ],
    },
}

_BEACH_ASCII_FALLBACK = {
    "≈": "~", "≋": "~", "▒": ".", "░": ".", "▓": "#",
    "⋆": "*", "˚": ".", "∘": "o",
}


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class BackgroundEngine:

    def __init__(self, stdscr,
                sky_theme="starry night",
                ground_theme="city",
                sky_enabled=True,
                ground_enabled=True,
                mode="layered",
                scene_theme="vaporwave sunset",
                user_image_path=""):
        self.stdscr         = stdscr
        self.sky_enabled    = sky_enabled
        self.ground_enabled = ground_enabled
        self.ascii_mode     = False
        self.rich_color     = False   # set True if terminal supports 256 colors
        self.max_y, self.max_x = stdscr.getmaxyx()
        self.frame = 0
        self.user_image_path = user_image_path
        self.user_image_palette = []
        self.load_error = None

        self.mode = mode if mode in ("layered", "scene") else "layered"
        self._set_sky(sky_theme)
        self._set_ground(ground_theme)
        self._set_scene(scene_theme)
        self.init_bg_colors()
        self._generate()

    # ── Color initialisation ───────────────────────────────────────────────

    def init_bg_colors(self):
        """
        Register curses color pairs for the active scene palette.
        Must be called after curses.start_color() has been called (UIEngine
        already calls it in its __init__, which runs before BackgroundEngine).

        For each palette entry i, we register:
          - In 256-color mode: a custom RGB color at index (100 + i), then
            a pair (BASE_PAIR + i) of that custom color on black.
          - In 8-color fallback: a pair (BASE_PAIR + i) using the closest
            standard COLOR_* constant on black.

        This only registers pairs for the *currently active scene* — no
        wasted slots from scenes you're not using.
        """
        
        curses.init_pair(235, curses.COLOR_WHITE, curses.COLOR_BLACK) # Fixed Background Pair
        self.BG_ATTR = curses.color_pair(235)
        
        if self.mode != "scene":
            return

        scene = self.scene_theme
        self.rich_color = curses.has_colors() and curses.can_change_color() and curses.COLORS >= 256

        if self.rich_color:
            palette = scene.get("palette_256", [])
            for i, (r, g, b) in enumerate(palette):
                color_idx = 100 + i          # custom color slot (100–123 for 24 entries)
                pair_id   = BASE_PAIR + i
                try:
                    curses.init_color(color_idx, r, g, b)
                    curses.init_pair(pair_id, color_idx, curses.COLOR_BLACK)
                except curses.error:
                    pass
        else:
            palette_8 = scene.get("palette_8", [])
            for i, color_const in enumerate(palette_8):
                pair_id = BASE_PAIR + i
                try:
                    curses.init_pair(pair_id, color_const, curses.COLOR_BLACK)
                except curses.error:
                    pass

    # ── Theme setters ──────────────────────────────────────────────────────

    def _set_sky(self, name):
        self.sky_name  = name
        self.sky_theme = SKY_THEMES.get(name, SKY_THEMES["starry night"])

    def _set_ground(self, name):
        self.ground_name  = name
        self.ground_theme = GROUND_THEMES.get(name, GROUND_THEMES["city"])

    def _set_scene(self, name):
        self.scene_name  = name
        # Default to the first available theme if something goes wrong
        fallback = list(SCENE_THEMES.keys())[0]
        self.scene_theme = SCENE_THEMES.get(name, SCENE_THEMES[fallback])
        
        # IMPORTANT: If this scene has a predefined path from the folder, 
        # override the user_image_path so _build_user_image() renders it.
        if "image_path" in self.scene_theme:
            self.user_image_path = self.scene_theme["image_path"]

    def set_sky(self, name):
        self._set_sky(name)
        self._generate()

    def set_ground(self, name):
        self._set_ground(name)
        self._generate()

    def set_scene(self, name):
        self._set_scene(name)
        self.init_bg_colors()
        self._generate()

    def set_user_image_path(self, path):
        self.user_image_path = path or ""
        if self.mode == "scene" and self.scene_name == "user image":
            self._generate()

    def set_mode(self, mode):
        if mode in ("layered", "scene"):
            self.mode = mode
            self.init_bg_colors()
            self._generate()

    def set_sky_enabled(self, v):    self.sky_enabled = v
    def set_ground_enabled(self, v): self.ground_enabled = v

    # ── Unicode detection ──────────────────────────────────────────────────

    def _detect_unicode(self):
        try:
            self.stdscr.addstr(0, 0, "✦")
            self.ascii_mode = False
        except curses.error:
            self.ascii_mode = True

    # ── Top-level generate ─────────────────────────────────────────────────

    def _generate(self):
        self._detect_unicode()
        rows, cols = self.max_y, self.max_x

        if self.mode == "scene":
            self._generate_scene(rows, cols)
            return

        # Layered mode — existing particle generation
        sky     = self.sky_theme
        chars   = sky["ascii_chars"] if self.ascii_mode else sky["particle_chars"]
        weights = sky["particle_weights"][:len(chars)]

        sky_rows    = int(rows * 0.75)
        total_cells = max(1, sky_rows * cols)
        count       = int(total_cells * sky["density"])

        self.particles = []
        for _ in range(count):
            y    = random.randint(0, max(0, sky_rows - 1))
            x    = random.randint(0, max(0, cols - 2))
            char = random.choices(chars, weights=weights, k=1)[0]
            pair = random.choice(sky["color_pairs"])
            self.particles.append((y, x, char, pair))

        if self.ground_name == "beach":
            self._generate_beach_props(rows, cols)


# ══════════════════════════════════════════════════════════════════════
    # SCENE FRAMEBUFFER SYSTEM
    # ══════════════════════════════════════════════════════════════════════

    def _generate_scene(self, rows, cols):
        self.fb = np.zeros((rows * 2, cols * 2), dtype=np.uint8)
        self.cb = np.zeros((rows,     cols),     dtype=np.uint8)

        build_fn = self.scene_theme.get("build_fn")
        builders = {
            "vaporwave_sunset": self._build_vaporwave_sunset,
            "user_image":       self._build_user_image,
        }
        builder = builders.get(build_fn, self._build_vaporwave_sunset)
        builder(rows, cols)

    def _build_vaporwave_sunset(self, rows, cols):
        # ── 1. Coordinate grids ───────────────────────────────────────────
        row_idx = np.arange(rows, dtype=np.float32)
        col_idx = np.arange(cols, dtype=np.float32)
        Y = row_idx[:, np.newaxis] * np.ones((1, cols), dtype=np.float32)
        X = np.ones((rows, 1), dtype=np.float32) * col_idx[np.newaxis, :]

        yn = Y / max(rows - 1, 1)
        xn = X / max(cols - 1, 1)

        # ── 2. Sun geometry ───────────────────────────────────────────────
        horizon_y  = 0.65          
        sun_cx     = 0.35          # Shifted slightly left to balance the palm tree
        sun_cy     = horizon_y - 0.05
        sun_radius = 0.25          
        aspect = cols / (rows * 2.0)   
        dx = xn - sun_cx
        dy = (yn - sun_cy) * aspect
        sun_dist = np.sqrt(dx * dx + dy * dy)   
        sun_mask = (sun_dist <= sun_radius)      

        # ── 3. Scanline mask (vaporwave signature) ────────────────────────
        # Cut horizontal slices out of the bottom half of the sun
        sun_lower_half = yn > sun_cy
        scanline_suppress = (row_idx[:, np.newaxis] % 2 != 0) & sun_lower_half & (sun_dist > sun_radius * 0.1)
        sun_visible = sun_mask & ~scanline_suppress

        # ── 4. Sky gradient (Teal to Magenta) ─────────────────────────────
        sky_mask = (yn < horizon_y)
        sky_t = np.clip(yn / max(horizon_y, 0.01), 0.0, 1.0)
        
        # Exponential curve so the dark teal dominates the top, and magenta compresses at the horizon
        sky_band = (np.power(sky_t, 1.5) * 11.99).astype(np.uint8)   # Maps to 0-11
        self.cb[sky_mask] = sky_band[sky_mask]
        
        sky_px = np.repeat(np.repeat(sky_mask, 2, axis=0), 2, axis=1)
        self.fb[sky_px] = 1

        # ── 5. Sun colouring (Vertical Gradient) ──────────────────────────
        # Yellow at the top (17), fading to Pink at the bottom (12)
        sun_top = sun_cy - (sun_radius / aspect)
        sun_bottom = sun_cy + (sun_radius / aspect)
        sun_t = np.clip((yn - sun_top) / max(sun_bottom - sun_top, 0.001), 0.0, 1.0)
        
        sun_band = 17 - (sun_t * 5.99).astype(np.uint8)
        self.cb[sun_mask] = sun_band[sun_mask]
        
        sun_px = np.repeat(np.repeat(sun_visible, 2, axis=0), 2, axis=1)
        self.fb[sun_px] = 1

        # ── 6. Water with Ripples ─────────────────────────────────────────
        water_mask = (yn >= horizon_y)
        self.cb[water_mask] = 18 # Deep teal water base
        
        # Horizontal lines for ripples
        ripple_y_pink = (row_idx[:, np.newaxis] % 2 == 0)
        ripple_y_yellow = (row_idx[:, np.newaxis] % 3 == 0)
        
        # Wide pink reflection
        pink_refl_mask = water_mask & ripple_y_pink & (np.abs(xn - sun_cx) < sun_radius * 1.5)
        self.cb[pink_refl_mask] = 19
        
        # Narrow yellow reflection in the center
        yellow_refl_mask = water_mask & ripple_y_yellow & (np.abs(xn - sun_cx) < sun_radius * 0.5)
        self.cb[yellow_refl_mask] = 20

        water_px = np.repeat(np.repeat(water_mask, 2, axis=0), 2, axis=1)
        self.fb[water_px] = 1

        # ── 7. Palm Silhouette ────────────────────────────────────────────
        palm_rows_data = [
            "       _.-'~~~'-._       ",
            "    .-~ \\__/  \\__/ ~-.   ",
            "  .~  /    |  |    \\  ~. ",
            " /   /     |  |     \\   \\",
            "|   |      |  |      |   |",
            " \\   \\     |  |     /   /",
            "  `~._\\    |  |    /_.~` ",
            "       `~--|  |--~`      ",
            "           |  |          ",
            "           |  |          ",
            "          /   |          ",
            "         |    |          ",
            "         |    |          ",
        ]

        palm_h    = len(palm_rows_data)
        palm_w    = max(len(r) for r in palm_rows_data)
        palm_top  = int(rows * 0.35)
        palm_left = cols - palm_w - max(4, cols // 15)

        for ri, line in enumerate(palm_rows_data):
            cy = palm_top + ri
            if not (0 <= cy < rows):
                continue
            
            # Apply magenta highlights to the fronds (top half), teal to trunk (bottom half)
            palm_color = 22 if ri < palm_h // 2 else 23
            
            for ci, ch in enumerate(line):
                cx = palm_left + ci
                if ch != ' ' and 0 <= cx < cols:
                    # Inner core of the palm remains pure black (21)
                    final_color = 21 if ch in ['|', '\\', '/'] else palm_color
                    self.cb[cy, cx] = final_color
                    py, px = cy * 2, cx * 2
                    self.fb[py:py+2, px:px+2] = 1

    def _build_user_image(self, rows, cols):
        """Load and render a user-selected image using the half-block matrix rule."""
        self.fb.fill(0)
        self.cb.fill(0)
        if not self.user_image_path:
            return
        
        try:
            import sys
            from pathlib import Path
            
            # Find the project root by going up from this file's directory
            project_root = Path(__file__).resolve().parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from files.image_process import process_image_for_terminal
            cache_key = (self.user_image_path, cols, rows)
            if getattr(self, "_img_cache_key", None) != cache_key:
                self._cached_palette_key = None
                img, palette = process_image_for_terminal(
                    self.user_image_path,
                    target_cols=cols,
                    target_lines=rows,
                    palette_size=14,
                )
                self._cached_img     = img
                self._cached_palette = palette
                self._img_cache_key  = cache_key
            else:
                img     = self._cached_img
                palette = self._cached_palette
            self.user_image_palette = palette
            
            # Register the full 196 combination matrix
            palette_key = tuple(tuple(c) for c in palette)
            if getattr(self, "_cached_palette_key", None) != palette_key:
                self._register_user_image_combinations(palette)
                self._cached_palette_key = palette_key
            
            px_array = np.array(img, dtype=np.uint8)   # shape (rows*2, cols)

            top_pixels    = px_array[0::2, :]           # even rows = top half of ▄
            bottom_pixels = px_array[1::2, :]           # odd rows  = bottom half of ▄

            self.cb[:rows, :cols] = (top_pixels[:rows] * 14 + bottom_pixels[:rows]).astype(np.uint8)

            # fb: top half always off (bg), bottom half always on (fg)
            self.fb[0::2, :] = 0
            self.fb[1::2, :] = 1
                    
        except Exception as e:
            self.load_error = str(e)
            self.fb.fill(0)
            self.cb.fill(0)

    def _register_user_image_combinations(self, palette):
        """Registers all 196 combinations of foreground and background pairs dynamically."""
        if not palette:
            return

        self.rich_color = curses.has_colors() and curses.can_change_color() and curses.COLORS >= 256
        self._pair_bold_flags = {}
        
        # 1. Initialize the 14 base colors into safe system slots (16-29)
        if self.rich_color:
            for i, (r, g, b) in enumerate(palette):
                color_idx = 16 + i
                c_r = r * 1000 // 255
                c_g = g * 1000 // 255
                c_b = b * 1000 // 255
                try:
                    curses.init_color(color_idx, c_r, c_g, c_b)
                except curses.error:
                    pass

        # 2. Map every possible Top/Bottom background/foreground pair combination
        fallback_colors = [
            curses.COLOR_BLACK, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_GREEN,
            curses.COLOR_MAGENTA, curses.COLOR_RED, curses.COLOR_WHITE, curses.COLOR_YELLOW,
        ]

        for top_idx in range(14):
            for bottom_idx in range(14):
                pair_idx = (top_idx * 14) + bottom_idx
                pair_id = BASE_PAIR + pair_idx
                
                if self.rich_color:
                    fg = 16 + bottom_idx  # Character color (bottom half)
                    bg = 16 + top_idx     # Background color (top half)
                    try:
                        curses.init_pair(pair_id, fg, bg)
                    except curses.error:
                        pass
                else:
                    # 8-Color fallback matrix pairing
                    r_fg, g_fg, b_fg = palette[bottom_idx]
                    r_bg, g_bg, b_bg = palette[top_idx]
                    
                    fg_const = self._nearest_standard_color((r_fg, g_fg, b_fg), fallback_colors)
                    bg_const = self._nearest_standard_color((r_bg, g_bg, b_bg), fallback_colors)
                    
                    self._pair_bold_flags[pair_id] = max(r_fg, g_fg, b_fg) > 128
                    try:
                        curses.init_pair(pair_id, fg_const, bg_const)
                    except curses.error:
                        pass

    def _nearest_standard_color(self, rgb, color_constants):
        """Map an RGB triplet to the nearest standard curses color."""
        stdlib_rgb = {
            curses.COLOR_BLACK:   (0, 0, 0),
            curses.COLOR_RED:     (205, 0, 0),
            curses.COLOR_GREEN:   (0, 205, 0),
            curses.COLOR_YELLOW:  (205, 205, 0),
            curses.COLOR_BLUE:    (0, 0, 238),
            curses.COLOR_MAGENTA: (205, 0, 205),
            curses.COLOR_CYAN:    (0, 205, 205),
            curses.COLOR_WHITE:   (229, 229, 229),
        }

        best_color = curses.COLOR_WHITE
        best_distance = None
        for color_const in color_constants:
            cr, cg, cb = stdlib_rgb.get(color_const, (255, 255, 255))
            distance = ((rgb[0] - cr) ** 2) + ((rgb[1] - cg) ** 2) + ((rgb[2] - cb) ** 2)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_color = color_const
        return best_color

# ══════════════════════════════════════════════════════════════════════
    # BLITTER — converts framebuffer + color buffer → terminal output
    # ══════════════════════════════════════════════════════════════════════

    def _blit_scene(self):
        rows, cols = self.max_y, self.max_x
        rows = min(rows - 1, self.fb.shape[0] // 2)  # -1 avoids bottom-right curses error
        cols = min(cols - 1, self.fb.shape[1] // 2)

        # ── Vectorised quad-pixel encoding ─────────────────────────────
        TL = self.fb[0::2, 0::2][:rows, :cols]
        TR = self.fb[0::2, 1::2][:rows, :cols]
        BL = self.fb[1::2, 0::2][:rows, :cols]
        BR = self.fb[1::2, 1::2][:rows, :cols]
        quad_idx = (TL * 8 + TR * 4 + BL * 2 + BR).astype(np.uint8)

        cb_slice = self.cb[:rows, :cols]

        # ── Precompute per-row string buffers ───────────────────────────
        # Build a lookup: pair_id → curses attr integer (computed once, not per cell)
        # Max pair index in cb is 14*14-1 = 195, so pair_ids run BASE_PAIR to BASE_PAIR+195
        bold_flags = getattr(self, "_pair_bold_flags", {})
        max_pair_idx = int(cb_slice.max()) + 1 if cb_slice.size > 0 else 1
        attr_cache = {}
        for idx in range(max_pair_idx):
            pid = BASE_PAIR + idx
            a = curses.color_pair(pid)
            if bold_flags.get(pid, False):
                a |= curses.A_BOLD
            attr_cache[idx] = a

        # ── Terminal I/O loop — Python overhead here is unavoidable ────
        addstr = self.stdscr.addstr   # local binding avoids attribute lookup per call
        glyph_lut = QUAD_PIXEL_DICT   # local binding

        for r in range(rows):
            row_quad = quad_idx[r]
            row_cb   = cb_slice[r]
            for c in range(cols):
                try:
                    addstr(r, c, glyph_lut[row_quad[c]], attr_cache[row_cb[c]])
                except curses.error:
                    pass


# ══════════════════════════════════════════════════════════════════════
    # LAYERED MODE — existing methods (unchanged)
    # ══════════════════════════════════════════════════════════════════════

    def _generate_beach_props(self, rows, cols):
        """Lay out palm trees, umbrella, crab, shells, and gulls once per
        generation, seeded from terminal size so layout is stable across
        redraws but adapts sensibly on resize."""
        g = self.ground_theme
        tallest = g.get("tallest", 9)

        self.beach_palms = []
        for p in g.get("palms", []):
            x = int(cols * p["x_frac"])
            self.beach_palms.append({"x": x, "lean": p["lean"], "h": p.get("h", 5)})

        u = g.get("umbrella")
        self.beach_umbrella = {"x": int(cols * u["x_frac"])} if u else None

        c = g.get("crab")
        self.beach_crab = {"x": int(cols * c["x_frac"])} if c else None

        self.beach_shells = [int(cols * f) for f in g.get("shells", [])]
        rng = random.Random(cols * 7919 + rows * 104729)  # stable per terminal size
        shell_glyphs = ["⋆", "˚", "∘"] if not self.ascii_mode else ["*", ".", "o"]
        self.beach_shell_glyphs = [rng.choice(shell_glyphs) for _ in self.beach_shells]

        self.beach_gulls = []
        for gpos in g.get("gulls", []):
            x = int(cols * gpos["x_frac"])
            y = max(0, rows - tallest - 3 - gpos["row_from_top"])
            self.beach_gulls.append({"x": x, "y": y})

    # ── Sky drawing ────────────────────────────────────────────────────────

    def _draw_sky(self):
        """Draw scattered particles and horizon glow for current sky theme."""
        sky = self.sky_theme

        # Particles
        for (y, x, char, pair) in self.particles:
            self._safe_addstr(y, x, char, curses.color_pair(pair))

        # Beach gulls live in the sky pass so they sit above the horizon glow
        if self.ground_enabled and self.ground_name == "beach":
            self._draw_gulls()

        # Horizon glow — sits just above the ground layer
        rows, cols = self.stdscr.getmaxyx()
        tallest    = self.ground_theme.get("tallest", 10) if self.ground_enabled else 2
        glow_row   = rows - tallest - 2
        if glow_row >= 0:
            glow_char = sky.get("glow_char", "▁")
            for c in range(0, cols - 1):
                char = glow_char if c % 3 == 0 else " "
                self._safe_addstr(
                    glow_row, c, char,
                    curses.color_pair(sky["glow_pair"]) | curses.A_DIM
                )

    def _draw_gulls(self):
        glyph = "v" if self.ascii_mode else "⌃"
        attr = curses.color_pair(self.ground_theme["highlight_pair"]) | curses.A_BOLD
        for gull in getattr(self, "beach_gulls", []):
            self._safe_addstr(gull["y"], gull["x"], glyph, attr)

    # ── Ground drawing ─────────────────────────────────────────────────────

    def _draw_ground(self):
        """Dispatch to the correct ground renderer based on detail_fn."""
        fn_name = self.ground_theme.get("detail_fn")
        dispatch = {
            "city_windows":  self._draw_city,
            "beach_surf":    self._draw_beach,
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

    def _safe_addstr(self, y, x, text, attr):
        if y < 0 or x < 0 or not text:
            return
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def _glyph(self, char):
        """Return the right glyph for the current render mode."""
        if not self.ascii_mode:
            return char
        return _BEACH_ASCII_FALLBACK.get(char, char)

    def _draw_layers(self):
        """
        Generic layer renderer — used by forest, ranch, ocean, and as a
        safe fallback for beach on very small terminals.
        """
        rows, cols = self.stdscr.getmaxyx()
        g      = self.ground_theme
        layers = g.get("layers", [])

        current_row = rows - 1   # start at the very bottom

        for layer in layers:
            h     = layer["h"]
            chars = layer["chars"]
            attr  = self._color_attr(layer["color"], layer.get("bold", False), layer.get("dim", False))
            chars_len = max(1, len(chars))

            for row_offset in range(h):
                row = current_row - row_offset
                if row < 0:
                    break
                line = (chars * (cols // chars_len + 2))[:max(0, cols - 1)]
                self._safe_addstr(row, 0, line, attr)

            current_row -= h

    # ── Beach renderer ───────────────────────────────────────────────────────

    def _draw_beach(self):
        """
        Beach-specific renderer:
          1. Textured sand bed (stippled, not a single tiled block)
          2. Foam line that gently animates between frames
          3. Two wave bands above the foam
        Then overlays props rooted on the sand: two leaning palm trees,
        a beach umbrella + towel, a crab, and a few scattered shells.
        Gulls are drawn separately in the sky pass.
        """
        rows, cols = self.stdscr.getmaxyx()
        if cols < 20 or rows < 10:
            # Too small to safely place props — fall back to flat bands
            self._draw_layers()
            return

        sand_attr      = self._color_attr("main", bold=True)
        sand_dim_attr  = self._color_attr("main", dim=True)
        foam_attr      = self._color_attr("highlight", bold=True)
        surf_attr      = self._color_attr("accent", bold=True)
        water_attr     = self._color_attr("accent", dim=True)

        bottom = rows - 1

        # --- Sand bed: 2 rows, textured with a small mix of glyphs so it
        #     reads as grainy sand rather than a repeating tiled pattern.
        sand_glyphs = [self._glyph(c) for c in ["▒", "░", "▒", "▓", "░", "·"]]
        rng = random.Random(rows * 31 + cols)  # stable texture per terminal size
        sand_rows = min(2, rows)
        for r in range(sand_rows):
            row = bottom - r
            if row < 0:
                break
            line = "".join(rng.choice(sand_glyphs) for _ in range(max(0, cols - 1)))
            self._safe_addstr(row, 0, line, sand_attr if r == 0 else sand_dim_attr)

        # --- Foam line: alternates glyph offset each frame for a gentle
        #     lapping effect as the screen redraws.
        foam_row = bottom - sand_rows
        if foam_row >= 0:
            offset = self.frame % 2
            pair = [self._glyph("≈"), self._glyph("~")]
            if offset:
                pair.reverse()
            line = "".join((pair[i % 2] + " ") for i in range(cols // 2 + 1))[:max(0, cols - 1)]
            self._safe_addstr(foam_row, 0, line, foam_attr)

        # --- Surf band directly above the foam
        surf_row = foam_row - 1
        if surf_row >= 0:
            line = (self._glyph("≋") + self._glyph("≈")) * (cols // 2 + 1)
            self._safe_addstr(surf_row, 0, line[:max(0, cols - 1)], surf_attr)

        # --- Calmer open-water band above that
        water_row = surf_row - 1
        if water_row >= 0:
            line = (self._glyph("~") + " " + self._glyph("≈") + " ") * (cols // 4 + 1)
            self._safe_addstr(water_row, 0, line[:max(0, cols - 1)], water_attr)

        sand_top_row = bottom - sand_rows + 1  # topmost sand row, where props sit

        self._draw_palms(sand_top_row)
        self._draw_umbrella(sand_top_row)
        self._draw_crab(sand_top_row)
        self._draw_shells(sand_top_row)

    def _draw_palms(self, sand_top_row):
        """Two palm trees, each a leaning trunk topped with a simple
        frond crown — proportions adapted from classic ASCII palm-tree
        sketches (lean trunk of slashes, a compact V-shaped crown)."""
        trunk_attr = self._color_attr("main", dim=True) | curses.A_BOLD
        crown_attr = self._color_attr("accent", bold=True)

        for palm in getattr(self, "beach_palms", []):
            x, lean, h = palm["x"], palm["lean"], palm["h"]
            trunk_glyph = self._glyph("\\") if lean < 0 else self._glyph("/")
            if lean == 0:
                trunk_glyph = self._glyph("|")

            for i in range(h):
                row = sand_top_row - 1 - i
                if row < 0:
                    break
                dx = lean if i >= h // 2 else 0
                self._safe_addstr(row, x + dx, trunk_glyph, trunk_attr)

            crown_row = sand_top_row - 1 - h
            crown_x   = x + (lean if h >= 1 else 0)
            if crown_row >= 0:
                fronds_top = self._glyph("/") + self._glyph("‾") + self._glyph("\\") if not self.ascii_mode else "/^\\"
                self._safe_addstr(crown_row, max(0, crown_x - 1), fronds_top, crown_attr)
            if crown_row + 1 >= 0:
                wide = self._glyph("\\") + self._glyph("_") + self._glyph("/") + " " + self._glyph("\\") + self._glyph("_") + self._glyph("/")
                self._safe_addstr(crown_row + 1, max(0, crown_x - 3), wide, crown_attr)

    def _draw_umbrella(self, sand_top_row):
        """A simple beach umbrella with a pole, plus a folded towel beside it."""
        if not getattr(self, "beach_umbrella", None):
            return
        ux = self.beach_umbrella["x"]
        canopy_attr = self._color_attr("highlight", bold=True)
        pole_attr   = self._color_attr("main", dim=True)
        towel_attr  = self._color_attr("accent")

        canopy_row = sand_top_row - 3
        self._safe_addstr(canopy_row,     ux - 2, " ___ ",  canopy_attr)
        self._safe_addstr(canopy_row + 1, ux - 3, "/___\\", canopy_attr)
        self._safe_addstr(canopy_row + 2, ux,     "|",      pole_attr)
        if sand_top_row - 1 >= 0:
            self._safe_addstr(sand_top_row - 1, ux, "|", pole_attr)

        # Folded towel a couple cells to the side
        self._safe_addstr(sand_top_row, ux + 3, "▭▭▭", towel_attr)

    def _draw_crab(self, sand_top_row):
        """A small crab glyph sitting on the sand — claws, body, claws."""
        if not getattr(self, "beach_crab", None):
            return
        cx = self.beach_crab["x"]
        crab_attr = self._color_attr("highlight")
        crab_glyph = self._glyph("(") + self._glyph("\\") + self._glyph("/") + self._glyph(")") if not self.ascii_mode else "(\\/)"
        self._safe_addstr(sand_top_row, cx, crab_glyph, crab_attr)

    def _draw_shells(self, sand_top_row):
        """A few small shell/starfish marks scattered in the sand."""
        attr = self._color_attr("highlight", dim=True)
        for sx, glyph in zip(getattr(self, "beach_shells", []),
                              getattr(self, "beach_shell_glyphs", [])):
            self._safe_addstr(sand_top_row, sx, glyph, attr)

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
                    self._safe_addstr(row, col, "▀" * w, main_attr | curses.A_BOLD)

                elif row_offset == h - 1:
                    # Rooftop
                    roof = ("▄" + "─" * (w - 2) + "▄") if w > 2 else "▄" * w
                    self._safe_addstr(row, col, roof, main_attr | curses.A_BOLD)

                else:
                    # Mid floors — walls then windows on top
                    self._safe_addstr(row, col, "█" * w, main_attr)
                    for wc in range(1, w - 1, 2):
                        lit = (row * 7 + (col + wc) * 3) % 5 != 0
                        win_attr = acc_attr if lit else (main_attr | curses.A_DIM)
                        # Every 4th lit window gets bright highlight
                        if lit and (row + col + wc) % 4 == 0:
                            win_attr = hi_attr
                        self._safe_addstr(row, col + wc, b["win"], win_attr)

            col += b["w"] + 1


# ══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════════

    def draw(self):
        """
        In scene mode:  blit the pre-built framebuffer to the terminal.
        In layered mode: draw sky then ground as before.
        frame counter drives any future animation (foam, scanline shift, etc.)
        """
        if self.mode == "scene":
            self._blit_scene()
        else:
            if self.sky_enabled:
                self._draw_sky()
            if self.ground_enabled:
                self._draw_ground()
        self.frame += 1

    def handle_resize(self):
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self.init_bg_colors()   # re-register pairs in case terminal changed
        self._generate()
        self.frame = 0