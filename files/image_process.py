from pathlib import Path
from PIL import Image, ImageEnhance

DEFAULT_COLS = 226
DEFAULT_LINES = 62
DEFAULT_PALETTE_SIZE = 14

def process_image_for_terminal(
    image_path,
    target_cols=DEFAULT_COLS,
    target_lines=DEFAULT_LINES,
    palette_size=DEFAULT_PALETTE_SIZE,
):
    """Load, pad to fit (letterbox/pillarbox), enhance, resize, and quantize."""
    target_width = max(1, int(target_cols))
    target_height = max(1, int(target_lines) * 2)
    source_path = Path(image_path)

    img = Image.open(source_path).convert("RGB")

    # 1. Calculate dimensions to fit inside the terminal without stretching
    target_ratio = target_width / target_height
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Image is wider than terminal space -> Fit to width, pad top/bottom
        new_width = target_width
        new_height = int(target_width / img_ratio)
    else:
        # Image is taller than terminal space -> Fit to height, pad sides
        new_height = target_height
        new_width = int(target_height * img_ratio)

    # Scale the image down (or up) to perfectly fit inside the bounds
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create a solid pure black canvas exactly the size of the terminal grid
    canvas = Image.new("RGB", (target_width, target_height), (0, 0, 0))

    # Calculate exact center coordinates
    offset_x = (target_width - new_width) // 2
    offset_y = (target_height - new_height) // 2

    # Paste the resized photo onto the black canvas
    canvas.paste(img, (offset_x, offset_y))
    img = canvas

    # 2. VIBRANCY & BRIGHTNESS BOOST
    # Terminals naturally deaden colors. We counteract this by pumping up the source.
    
    # Boost Color Saturation by 40% to make the neon/tones pop
    color_enhancer = ImageEnhance.Color(img)
    img = color_enhancer.enhance(1.0)
    
    # Boost Brightness by 20% to fight the quantization dimming
    brightness_enhancer = ImageEnhance.Brightness(img)
    img = brightness_enhancer.enhance(1.0)

    # 3. Quantize the padded image
    # (Because the canvas is already target_width x target_height, we skip the second resize)
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