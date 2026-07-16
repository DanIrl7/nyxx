import sys
import os
import curses
import numpy as np
from pathlib import Path

QUAD_PIXEL_DICT = {
    0:  " ",  1:  "▗",  2:  "▖",  3:  "▄",
    4:  "▝",  5:  "▐",  6:  "▞",  7:  "▟",
    8:  "▘",  9:  "▚",  10: "▌",  11: "▙",
    12: "▀",  13: "▜",  14: "▛",  15: "█",
}

BASE_PAIR = 8  

VAPORWAVE_PALETTE_256 = [
    (10,   10,   30),    (20,   40,   100),   (30,   150,  250),   
    (40,   300,  400),   (50,   450,  550),   (100,  600,  700),   
    (500,  100,  400),   (700,  150,  500),   (900,  200,  600),   
    (1000, 300,  650),   (1000, 450,  700),   (1000, 600,  800),   
    (1000, 200,  500),   (1000, 400,  500),   (1000, 600,  400),   
    (1000, 800,  300),   (1000, 900,  500),   (1000, 950,  800),   
    (20,   100,  250),   (1000, 300,  600),   (1000, 800,  400),   
    (10,   10,   20),    (700,  150,  500),   (30,   150,  250),   
]

VAPORWAVE_PALETTE_8 = [
    curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLUE,
    curses.COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_CYAN,
    curses.COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA,
    curses.COLOR_MAGENTA, curses.COLOR_RED,     curses.COLOR_RED,
    curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_YELLOW,
    curses.COLOR_WHITE,  curses.COLOR_WHITE,  curses.COLOR_WHITE,
    curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_MAGENTA,
    curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLUE,
]

def get_backgrounds_dir():
    """Robustly resolves the path to assets/backgrounds across dev and frozen environments."""
    if getattr(sys, 'frozen', False):
        # Running inside a compiled PyInstaller bundle
        exe_dir = Path(sys.executable).resolve().parent
        
        # 1. Try finding assets in the installation folder next to the .exe (Inno Setup style)
        assets_dir = exe_dir / "assets" / "backgrounds"
        if assets_dir.exists():
            return assets_dir
            
        # 2. Try the PyInstaller temporary directory (_MEIPASS) if packaged inside the .exe
        meipass_dir = Path(getattr(sys, '_MEIPASS', ''))
        assets_dir = meipass_dir / "assets" / "backgrounds"
        if assets_dir.exists():
            return assets_dir
            
    # Non-frozen (Development mode): dynamically traverse up to find 'assets/backgrounds'
    file_path = Path(__file__).resolve()
    for parent in file_path.parents:
        potential_assets = parent / "assets" / "backgrounds"
        if potential_assets.exists():
            return potential_assets
            
    # Fallback to standard relative structure
    return Path(__file__).resolve().parent.parent.parent / "assets" / "backgrounds"

def load_scene_themes():
    themes = {
        "user image": {
            "label": "Browse File...",
            "build_fn": "user_image",
            "palette_256": [],
            "palette_8": [],
        }
    }
    try:
        # 1. Determine the backgrounds directory dynamically
        if getattr(sys, 'frozen', False):
            # Running inside a compiled executable bundle (PyInstaller)
            exe_dir = Path(sys.executable).resolve().parent
            bg_dir = exe_dir / "assets" / "backgrounds"
        else:
            # Running in local development mode
            project_root = Path(__file__).resolve().parent.parent.parent
            bg_dir = project_root / "assets" / "backgrounds"

        bg_dir.mkdir(parents=True, exist_ok=True)
        for ext in ('*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp'):
            for img_path in bg_dir.glob(ext):
                scene_name = img_path.stem.lower()
                themes[scene_name] = {
                    "label": img_path.stem.replace("_", " ").title(),
                    "build_fn": "user_image",
                    "image_path": str(img_path),
                    "palette_256": [],
                    "palette_8": []
                }
    except Exception:
        pass
    return themes
    
SCENE_THEMES = load_scene_themes()

class BackgroundEngine:
    def __init__(self, stdscr, scene_theme="vaporwave sunset", user_image_path=""):
        self.stdscr = stdscr
        self.rich_color = False
        self.max_y, self.max_x = stdscr.getmaxyx()
        self.frame = 0
        self.user_image_path = user_image_path
        self.user_image_palette = []
        self.load_error = None

        self._set_scene(scene_theme)
        self.init_bg_colors()
        self._generate()

    def init_bg_colors(self):
        curses.init_pair(235, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.BG_ATTR = curses.color_pair(235)
        
        scene = self.scene_theme
        self.rich_color = curses.has_colors() and curses.can_change_color() and curses.COLORS >= 256

        if self.rich_color:
            palette = scene.get("palette_256", [])
            for i, (r, g, b) in enumerate(palette):
                color_idx = 100 + i
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

    def _set_scene(self, name):
        self.scene_name  = name
        fallback = list(SCENE_THEMES.keys())[0]
        self.scene_theme = SCENE_THEMES.get(name, SCENE_THEMES[fallback])
        
        if "image_path" in self.scene_theme:
            self.user_image_path = self.scene_theme["image_path"]

    def set_scene(self, name):
        self._set_scene(name)
        self.init_bg_colors()
        self._generate()

    def set_user_image_path(self, path):
        self.user_image_path = path or ""
        if self.scene_name == "user image":
            self._generate()

    def _generate(self):
        rows, cols = self.max_y, self.max_x
        self._generate_scene(rows, cols)

    def _generate_scene(self, rows, cols):
        self.fb = np.zeros((rows * 2, cols * 2), dtype=np.uint8)
        self.cb = np.zeros((rows,     cols),     dtype=np.uint8)

        build_fn = self.scene_theme.get("build_fn")
        builders = {
            "user_image":       self._build_user_image,
        }
        builder = builders.get(build_fn)
        builder(rows, cols)

    
    def _build_user_image(self, rows, cols):
        self.fb.fill(0)
        self.cb.fill(0)
        if not self.user_image_path:
            return
        
        try:
            import sys
            from pathlib import Path
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
            
            palette_key = tuple(tuple(c) for c in palette)
            if getattr(self, "_cached_palette_key", None) != palette_key:
                self._register_user_image_combinations(palette)
                self._cached_palette_key = palette_key
            
            px_array = np.array(img, dtype=np.uint8)

            top_pixels    = px_array[0::2, :]
            bottom_pixels = px_array[1::2, :]

            self.cb[:rows, :cols] = (top_pixels[:rows] * 14 + bottom_pixels[:rows]).astype(np.uint8)

            self.fb[0::2, :] = 0
            self.fb[1::2, :] = 1
                    
        except Exception as e:
            self.load_error = str(e)
            self.fb.fill(0)
            self.cb.fill(0)

    def _register_user_image_combinations(self, palette):
        if not palette: return

        self.rich_color = curses.has_colors() and curses.can_change_color() and curses.COLORS >= 256
        self._pair_bold_flags = {}
        
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

        fallback_colors = [
            curses.COLOR_BLACK, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_GREEN,
            curses.COLOR_MAGENTA, curses.COLOR_RED, curses.COLOR_WHITE, curses.COLOR_YELLOW,
        ]

        for top_idx in range(14):
            for bottom_idx in range(14):
                pair_idx = (top_idx * 14) + bottom_idx
                pair_id = BASE_PAIR + pair_idx
                
                if self.rich_color:
                    fg = 16 + bottom_idx  
                    bg = 16 + top_idx     
                    try:
                        curses.init_pair(pair_id, fg, bg)
                    except curses.error:
                        pass
                else:
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



    def draw(self):
        self._blit_scene()
        self.frame += 1
        
    def handle_resize(self):
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self.init_bg_colors()
        self._generate()
        self.frame = 0