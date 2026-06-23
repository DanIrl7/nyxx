import curses
import random

class BackgroundEngine:
    STAR_CHARS = ['✦', '✧', '*', '·', '◇']
    STAR_CHARS_ASCII = ['+', '*', '.', ',', ' ']  # fallback for basic terminals
    THEMES = {
        "starry night": {
            "star_density": 0.04,   # 4% of all cells will have a star
            "star_color_pairs": [5, 6, 7],  # bright, mid, dim — defined in UIEngine
            "city_color_pair": 8,
            "glow_color_pair": 9,
        }
    }

    def __init__(self, stdscr, theme_name="starry night"):
        self.stdscr = stdscr
        self.theme = self.THEMES.get(theme_name, self.THEMES["starry night"])
        self.max_y, self.max_x = stdscr.getmaxyx()
        self.ascii_mode = False
        self._generate(self.max_y, self.max_x)

    def _detect_unicode(self):
        """Try rendering a unicode char — fall back to ASCII if it fails"""
        try:
            self.stdscr.addstr(0, 0, '✦')
            self.ascii_mode = False
        except:
            self.ascii_mode = True

    def _generate(self, rows, cols):
        """Generate star positions based on density % of total cells"""
        self._detect_unicode()
        chars = self.STAR_CHARS_ASCII if self.ascii_mode else self.STAR_CHARS
        total_cells = rows * cols
        star_count = int(total_cells * self.theme["star_density"])

        # Reserve bottom 20% for city silhouette
        sky_rows = int(rows * 0.80)

        self.stars = []
        for _ in range(star_count):
            y = random.randint(0, sky_rows - 1)
            x = random.randint(0, cols - 2)  # -2 to avoid rightmost column
            char = random.choices(
                chars,
                weights=[1, 2, 4, 6, 3],  # denser mid/dim stars, fewer bright ones
                k=1
            )[0]
            brightness = random.choice(self.theme["star_color_pairs"])
            self.stars.append((y, x, char, brightness))

    def _draw_stars(self):
        for (y, x, char, color_pair) in self.stars:
            try:
                self.stdscr.addstr(y, x, char, curses.color_pair(color_pair))
            except curses.error:
                pass

    def _draw_city(self):
        """Draw a city silhouette along the bottom rows using block characters"""
        rows, cols = self.stdscr.getmaxyx()
        color = curses.color_pair(self.theme["city_color_pair"])

        # Define building heights as a repeating pattern
        # Each value = how many rows tall that building segment is
        building_pattern = [6, 10, 4, 12, 7, 9, 5, 11, 8, 6, 10, 4, 7, 9, 5]
        pattern_width = 5  # each building segment is 5 chars wide

        city_start_row = rows - max(building_pattern) - 1

        for col in range(0, cols - 1, pattern_width):
            building_idx = (col // pattern_width) % len(building_pattern)
            height = building_pattern[building_idx]
            for row_offset in range(height):
                row = rows - 1 - row_offset
                if row < 0 or row >= rows:
                    continue
                for c in range(col, min(col + pattern_width - 1, cols - 1)):
                    try:
                        char = '█' if row_offset > 0 else '▄'
                        self.stdscr.addstr(row, c, char, color)
                    except curses.error:
                        pass

    def _draw_glow(self):
        """Draw a dim horizon glow just above the city"""
        rows, cols = self.stdscr.getmaxyx()
        color = curses.color_pair(self.theme["glow_color_pair"])
        glow_row = rows - max([6, 10, 4, 12, 7, 9, 5, 11, 8]) - 2

        if glow_row >= 0:
            try:
                glow_line = '▒' * (cols - 1)
                self.stdscr.addstr(glow_row, 0, glow_line, color | curses.A_DIM)
            except curses.error:
                pass

    def draw(self):
        self._draw_stars()
        self._draw_city()
        self._draw_glow()

    def handle_resize(self):
        """Call this when a KEY_RESIZE event is detected — regenerates to new size"""
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self._generate(self.max_y, self.max_x)