from pathlib import Path
from PIL import Image, ImageEnhance  # Added ImageEnhance

DEFAULT_COLS = 226
DEFAULT_LINES = 62
DEFAULT_PALETTE_SIZE = 14

def process_image_for_terminal(
    image_path,
    target_cols=DEFAULT_COLS,
    target_lines=DEFAULT_LINES,
    palette_size=DEFAULT_PALETTE_SIZE,
):
    """Load, center-crop, enhance, resize, and quantize an image for terminal use."""
    target_width = max(1, int(target_cols))
    target_height = max(1, int(target_lines) * 2)
    source_path = Path(image_path)

    img = Image.open(source_path).convert("RGB")

    # 1. Calculate Center Crop
    target_ratio = target_width / target_height
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        new_width = int(target_ratio * img.height)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    # 2. VIBRANCY & BRIGHTNESS BOOST (The Fix)
    # Terminals naturally deaden colors. We counteract this by pumping up the source.
    
    # Boost Color Saturation by 40% to make the neon/tones pop
    color_enhancer = ImageEnhance.Color(img)
    img = color_enhancer.enhance(1.0)
    
    # Boost Brightness by 20% to fight the quantization dimming
    brightness_enhancer = ImageEnhance.Brightness(img)
    img = brightness_enhancer.enhance(1.0)

    # 3. Resize and Quantize
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    img = img.quantize(colors=palette_size, method=Image.Quantize.MAXCOVERAGE)

    raw_palette = img.getpalette()[: palette_size * 3]
    rgb_palette = [
        (raw_palette[i], raw_palette[i + 1], raw_palette[i + 2])
        for i in range(0, len(raw_palette), 3)
    ]

    # Boost the extracted palette colors directly so the values that reach
    # curses.init_color() are vivid, not the averaged-down quantization centroids.
    rgb_palette = [_boost_palette_color(r, g, b) for r, g, b in rgb_palette]

    return img, rgb_palette

def _boost_palette_color(r, g, b, saturation=1.0, brightness=1.0):

    """
    Push each palette color toward vivid and bright.
    Saturation: pulls each channel away from the grey midpoint.
    Brightness: scales all channels up, clamped to 255.
    Minimum floor: prevents true black from swallowing dark-but-colored entries.
    """
    # Normalize to 0.0–1.0
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0

    # Brightness boost
    rf = min(1.0, rf * brightness)
    gf = min(1.0, gf * brightness)
    bf = min(1.0, bf * brightness)

    # Saturation boost: push away from perceptual grey
    grey = 0.299 * rf + 0.587 * gf + 0.114 * bf
    rf = min(1.0, grey + (rf - grey) * saturation)
    gf = min(1.0, grey + (gf - grey) * saturation)
    bf = min(1.0, grey + (bf - grey) * saturation)

    # Floor: no channel goes below 8/255 so dark colors stay colored, not black
    rf = max(0.031, rf)
    gf = max(0.031, gf)
    bf = max(0.031, bf)

    return int(rf * 255), int(gf * 255), int(bf * 255)