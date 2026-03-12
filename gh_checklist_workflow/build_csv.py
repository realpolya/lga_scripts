import csv
import os
import re
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

'''

Run like this:
python build_csv.py "/absolute/path/to/png_folder" "/absolute/path/to/contour_folder"

py build_csv.py "../../Silhouettes/Kaplan Modified/Kaplan Silhouettes/3D Silhouettes" 
"../../Silhouettes/Kaplan Modified/Kaplan Contours"

py build_csv.py 
"../../Silhouettes/Bloomberg Modified/Bloomberg SIlhouettes/Combined" 
"../../Silhouettes/Bloomberg Modified/Bloomberg Contours"

py build_csv.py 
"../../Silhouettes/Hurst Modified/Hurst Silhouettes/Combined" 
"../../Silhouettes/Hurst Modified/Hurst Contours"

py build_csv.py 
"../../Silhouettes/Heller Modified/Heller Silhouettes/Combined" 
"../../Silhouettes/Heller Modified/Heller Contours"

py build_csv.py 
"../../Silhouettes/Offit Modified/Offit Silhouettes/Combined" 
"../../Silhouettes/Offit Modified/Offit Contours"


'''

# OUTPUT_CSV = "build_hurst.csv"
# OUTPUT_CSV = "build_kaplan.csv"
# OUTPUT_CSV = "build_bloomberg.csv"
OUTPUT_CSV = "build_heller.csv"
# OUTPUT_CSV = "build_offit.csv"

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
    "layer_scaled_curve",
    "layer_curve_bbox",
    "layer_images",
    "picture_path",
    "img_w",
    "img_h",
    "min_x",
    "min_z",
    "max_x",
    "max_z",
    "left_margin",
    "right_margin",
    "top_margin",
    "bottom_margin",
]

VALID_EXTENSIONS = {".png"}
ALPHA_THRESHOLD = 10


# def extract_item_number(filename: str) -> str:
#     """
#     18_silhouette.png -> 18
#     """
#     stem = os.path.splitext(filename)[0]
#     match = re.match(r"^(\d+)_silhouette$", stem, re.IGNORECASE)
#     if match:
#         return match.group(1)
#     return stem

def extract_item_number(filename: str) -> str:
    """
    18_silhouette.png -> 18
    178a_silhouette.png -> 178a
    """
    stem = os.path.splitext(filename)[0]
    match = re.match(r"^(\d+[A-Za-z]?)_silhouette$", stem, re.IGNORECASE)
    if match:
        return match.group(1)
    return stem


def build_contour_path(contour_dir: str, item_number: str) -> str:
    """
    /path/to/contours/18_silhouette_contour.svg
    """
    contour_filename = f"{item_number}_silhouette_contour.svg"
    return os.path.abspath(os.path.join(contour_dir, contour_filename))


def analyze_png(png_path: str, alpha_threshold: int = ALPHA_THRESHOLD) -> dict:
    """
    Reads a PNG, ignores transparent background, and returns:
    - full image width/height
    - visible silhouette bbox
    - transparent margins
    """
    with Image.open(png_path).convert("RGBA") as img:
        img_w, img_h = img.size
        pixels = img.load()

        minx = img_w
        minz = img_h
        maxx = -1
        maxz = -1

        for z in range(img_h):
            for x in range(img_w):
                alpha = pixels[x, z][3]
                if alpha > alpha_threshold:
                    if x < minx:
                        minx = x
                    if z < minz:
                        minz = z
                    if x > maxx:
                        maxx = x
                    if z > maxz:
                        maxz = z

        if maxx < 0:
            # image is fully transparent
            return {
                "img_w": img_w,
                "img_h": img_h,
                "min_x": "",
                "min_z": "",
                "max_x": "",
                "max_z": "",
                "left_margin": "",
                "right_margin": "",
                "top_margin": "",
                "bottom_margin": "",
            }

        left_margin = minx
        right_margin = img_w - (maxx + 1)
        top_margin = minz
        bottom_margin = img_h - (maxz + 1)

        return {
            "img_w": img_w,
            "img_h": img_h,
            "min_x": minx,
            "min_z": minz,
            "max_x": maxx,
            "max_z": maxz,
            "left_margin": left_margin,
            "right_margin": right_margin,
            "top_margin": top_margin,
            "bottom_margin": bottom_margin,
        }


def build_row(png_path: str, contour_dir: str) -> dict:
    filename = os.path.basename(png_path)
    item_number = extract_item_number(filename)
    base_layer = f"Item_{item_number}"

    png_data = analyze_png(png_path)

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
        "layer_scaled_curve": f"AutoCAD::{base_layer}::Scaled_Curve",
        "layer_curve_bbox": f"AutoCAD::{base_layer}::Curve_Bbox",
        "layer_images": f"{base_layer}::Images",
        "picture_path": os.path.abspath(png_path),
        "img_w": png_data["img_w"],
        "img_h": png_data["img_h"],
        "min_x": png_data["min_x"],
        "min_z": png_data["min_z"],
        "max_x": png_data["max_x"],
        "max_z": png_data["max_z"],
        "left_margin": png_data["left_margin"],
        "right_margin": png_data["right_margin"],
        "top_margin": png_data["top_margin"],
        "bottom_margin": png_data["bottom_margin"],
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