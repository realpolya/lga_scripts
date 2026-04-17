from pathlib import Path
from PIL import Image

def crop_png_transparency(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    for png_path in input_dir.glob("*.png"):
        try:
            img = Image.open(png_path).convert("RGBA")

            # Get alpha channel
            alpha = img.split()[-1]

            # Get bounding box of non-transparent area
            bbox = alpha.getbbox()

            if bbox:
                cropped = img.crop(bbox)
            else:
                print(f"Skipped (fully transparent): {png_path.name}")
                continue

            output_path = output_dir / png_path.name
            cropped.save(output_path)

            print(f"Cropped: {png_path.name}")

        except Exception as e:
            print(f"Error with {png_path.name}: {e}")


if __name__ == "__main__":
    input_folder = "/Users/polinastepanova/Desktop/Work_2025-2026/LGA_Work/JM6/Silhouettes/Offit Modified/Offit Silhouettes/Combined"
    output_folder = "/Users/polinastepanova/Desktop/Work_2025-2026/LGA_Work/JM6/Silhouettes/Offit Modified/Offit Silhouettes/Combined_Cropped"

    crop_png_transparency(input_folder, output_folder)