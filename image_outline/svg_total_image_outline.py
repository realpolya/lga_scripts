'''
Example for Offit
py svg_total_image_outline.py "../../Silhouettes/Offit Modified/Offit Silhouettes/total_image_for_contours" "../../Silhouettes/Offit Modified/Offit Contours/resolve_problematic"

'''


from __future__ import annotations
import re
import sys
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def rectangle_to_svg_path(w: int, h: int) -> str:
    return f"M 0,0 L {w},0 L {w},{h} L 0,{h} L 0,0 Z"


def write_svg(out_path: Path, w: int, h: int, d: str) -> None:
    svg = f"""<?xml version="1.0" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" version="1.1">
  <path d="{d}" fill="none" stroke="black" stroke-width="2" vector-effect="non-scaling-stroke"/>
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 png_to_svg_rectangles.py INPUT_FOLDER OUTPUT_FOLDER")
        return 2

    in_dir = Path(sys.argv[1]).expanduser().resolve()
    out_dir = Path(sys.argv[2]).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    files = sorted([p for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() in exts])

    if not files:
        print(f"No image files found in {in_dir}")
        return 1

    for p in files:
        try:
            with Image.open(p) as img:
                w, h = img.size

            d = rectangle_to_svg_path(w, h)
            base = re.sub(r"\.[^.]+$", "", p.name)
            out_path = out_dir / f"{base}_contour.svg"
            write_svg(out_path, w, h, d)
            print(f"OK: {p.name} -> {out_path.name}")

        except Exception as e:
            print(f"ERROR: {p.name} -> {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())