import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from files.image_process import process_image_for_terminal

sample_image = REPO_ROOT / "files" / "bear_lying_ing_grass.jpg"
img, palette = process_image_for_terminal(str(sample_image), target_cols=80, target_lines=24)
print("size:", img.size)
print("mode:", img.mode)
print("palette entries:", len(palette))
img.save(str(Path(__file__).resolve().parent / "processed_preview.png"))
