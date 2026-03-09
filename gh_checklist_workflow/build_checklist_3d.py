import csv
import os
import re
import sys

OUTPUT_CSV = "build_kaplan.csv"

FIELDNAMES = [
    "name",
    "contour_path",
    "units",
    "w",
    "h",
    "d",
    "layer_final_geom",
    "layer_derived_curves",
    "layer_original_curves",
    "layer_images",
    "picture_path",
]

VALID_EXTENSIONS = {".png"}

def extract_item_number(filename: str) -> str:
    """
    Extract the leading item number from filenames like:
    18_silhouette.png -> 18
    """
    stem = os.path.splitext(filename)[0]
    match = re.match(r"^(\d+)_silhouette$", stem, re.IGNORECASE)
    if match:
        return match.group(1)
    return stem

def build_contour_path(contour_dir: str, item_number: str) -> str:
    """
    Builds contour path like:
    /path/to/contours/18_silhouette_contour.svg
    """
    contour_filename = f"{item_number}_silhouette_contour.svg"
    return os.path.abspath(os.path.join(contour_dir, contour_filename))

def build_row(png_path: str, contour_dir: str) -> dict:
    filename = os.path.basename(png_path)
    item_number = extract_item_number(filename)

    base_layer = f"Item_{item_number}"

    return {
        "name": item_number,
        "contour_path": build_contour_path(contour_dir, item_number),
        "units": "",
        "w": "",
        "h": "",
        "d": "",
        "layer_final_geom": f"{base_layer}::Final_Geom",
        "layer_derived_curves": f"{base_layer}::Face_Curves",
        "layer_original_curves": f"{base_layer}::Original_Curve",
        "layer_images": f"{base_layer}::Images",
        "picture_path": os.path.abspath(png_path),
    }

def collect_png_paths(directory: str):
    paths = []

    for filename in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, filename)

        if not os.path.isfile(full_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext in VALID_EXTENSIONS:
            paths.append(os.path.abspath(full_path))

    return paths

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("python build_csv.py /absolute/path/to/png_folder /absolute/path/to/contour_folder")
        return

    png_dir = sys.argv[1]
    contour_dir = sys.argv[2]

    if not os.path.isdir(png_dir):
        print("PNG directory does not exist:")
        print(png_dir)
        return

    if not os.path.isdir(contour_dir):
        print("Contour directory does not exist:")
        print(contour_dir)
        return

    png_paths = collect_png_paths(png_dir)
    rows = [build_row(path, contour_dir) for path in png_paths]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()