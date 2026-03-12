#!/usr/bin/env python3
"""
Batch convert silhouette PNGs to SVG outer outlines (no holes).

- Uses alpha channel if present; otherwise separates foreground from background using border color.
- Extracts the largest contour only (outer boundary), so interior holes are ignored.
- Simplifies points with Ramer–Douglas–Peucker to keep SVG lightweight.

Usage:
  python3 png_to_svg_outlines.py /path/to/input_folder /path/to/output_folder

Outputs:
  For each *_silhouette.png (or any .png/.jpg/.tif), writes <name>_contour.svg
"""

from __future__ import annotations
import os
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from skimage import measure

Image.MAX_IMAGE_PIXELS = None

def rdp(points: np.ndarray, epsilon: float) -> np.ndarray:
    """Ramer–Douglas–Peucker simplification for Nx2 points."""
    if len(points) < 3:
        return points

    start = points[0]
    end = points[-1]
    line = end - start
    line_len = float(np.hypot(line[0], line[1]))

    if line_len == 0.0:
        dists = np.hypot(*(points - start).T)
    else:
        v = points - start
        cross = np.abs(v[:, 0] * line[1] - v[:, 1] * line[0])
        dists = cross / line_len

    idx = int(np.argmax(dists))
    dmax = float(dists[idx])

    if dmax > epsilon:
        left = rdp(points[: idx + 1], epsilon)
        right = rdp(points[idx:], epsilon)
        return np.vstack([left[:-1], right])
    else:
        return np.vstack([start, end])


def estimate_bg(rgb: np.ndarray) -> np.ndarray:
    """Estimate background color from the image borders."""
    h, w, _ = rgb.shape
    border = np.concatenate(
        [
            rgb[0:2, :, :].reshape(-1, 3),
            rgb[h - 2 : h, :, :].reshape(-1, 3),
            rgb[:, 0:2, :].reshape(-1, 3),
            rgb[:, w - 2 : w, :].reshape(-1, 3),
        ],
        axis=0,
    )
    return np.median(border, axis=0)


# def make_mask(img: Image.Image) -> np.ndarray:
#     """
#     True = foreground.
#     Prefer alpha if available; otherwise detect background via border color distance.
#     """
#     if img.mode in ("RGBA", "LA"):
#         arr = np.array(img)
#         alpha = arr[:, :, 3].astype(np.uint8)
#         return alpha > 10  # treat near-transparent as background

#     rgb = np.array(img.convert("RGB")).astype(np.int16)
#     bg = estimate_bg(rgb)
#     diff = np.sqrt(np.sum((rgb - bg) ** 2, axis=2))

#     h, w = diff.shape
#     border_diff = np.concatenate(
#         [
#             diff[0:2, :].ravel(),
#             diff[h - 2 : h, :].ravel(),
#             diff[:, 0:2].ravel(),
#             diff[:, w - 2 : w].ravel(),
#         ]
#     )

#     thr = float(np.percentile(border_diff, 99)) + 5.0
#     thr = max(thr, 15.0)
#     return diff > thr

def make_mask(img: Image.Image) -> np.ndarray:
    """
    True = foreground.
    Prefer alpha if available; otherwise detect background via border color distance.
    """
    if "A" in img.getbands():
        alpha = np.array(img.getchannel("A")).astype(np.uint8)
        return alpha > 10  # treat near-transparent as background

    rgb = np.array(img.convert("RGB")).astype(np.int16)
    bg = estimate_bg(rgb)
    diff = np.sqrt(np.sum((rgb - bg) ** 2, axis=2))

    h, w = diff.shape
    border_diff = np.concatenate(
        [
            diff[0:2, :].ravel(),
            diff[h - 2 : h, :].ravel(),
            diff[:, 0:2].ravel(),
            diff[:, w - 2 : w].ravel(),
        ]
    )

    thr = float(np.percentile(border_diff, 99)) + 5.0
    thr = max(thr, 15.0)
    return diff > thr


def largest_contour(mask: np.ndarray) -> np.ndarray | None:
    """
    Return the contour (N x 2) with largest enclosed area.
    Contours are in (row=y, col=x) coords.
    """
    binary = mask.astype(np.uint8)
    contours = measure.find_contours(binary, 0.5)
    if not contours:
        return None

    def poly_area(c: np.ndarray) -> float:
        x = c[:, 1]
        y = c[:, 0]
        return float(0.5 * np.abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))

    return max(contours, key=poly_area)


def contour_to_svg_path(contour: np.ndarray, w: int, h: int, epsilon: float) -> str:
    # Convert to SVG coordinates (x, y) with y flipped
    # pts = np.column_stack([contour[:, 1], h - contour[:, 0]]).astype(np.float32)
    pts = np.column_stack([contour[:, 1], contour[:, 0]]).astype(np.float32)

    # Close it
    if np.hypot(*(pts[0] - pts[-1])) > 1e-6:
        pts = np.vstack([pts, pts[0]])

    # Simplify
    simp = rdp(pts, epsilon)

    # Ensure closed
    if np.hypot(*(simp[0] - simp[-1])) > 1e-6:
        simp = np.vstack([simp, simp[0]])

    # Build path
    parts = [f"{simp[0,0]:.2f},{simp[0,1]:.2f}"]
    parts += [f"{p[0]:.2f},{p[1]:.2f}" for p in simp[1:]]
    return "M " + " L ".join(parts) + " Z"


def write_svg(out_path: Path, w: int, h: int, d: str) -> None:
    svg = f"""<?xml version="1.0" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" version="1.1">
  <path d="{d}" fill="none" stroke="black" stroke-width="2" vector-effect="non-scaling-stroke"/>
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 png_to_svg_outlines.py INPUT_FOLDER OUTPUT_FOLDER")
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
            img = Image.open(p)
            w, h = img.size
            mask = make_mask(img)
            c = largest_contour(mask)
            if c is None:
                print(f"SKIP (no contour): {p.name}")
                continue

            # Adaptive simplification: larger images tolerate a slightly larger epsilon
            eps = max(1.5, min(w, h) / 300.0)

            d = contour_to_svg_path(c, w, h, epsilon=eps)
            base = re.sub(r"\.[^.]+$", "", p.name)
            out_path = out_dir / f"{base}_contour.svg"
            write_svg(out_path, w, h, d)
            print(f"OK: {p.name} -> {out_path.name}")

        except Exception as e:
            print(f"ERROR: {p.name} -> {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())