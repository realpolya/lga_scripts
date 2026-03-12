import csv
import sys


# DOMINANT_FILE = "./combine_sheets/build_heller.csv"
# DOMINANT_FILE = "./combine_sheets/build_bloomberg.csv"
# DOMINANT_FILE = "./combine_sheets/build_hurst.csv"
DOMINANT_FILE = "./combine_sheets/build_offit.csv"
OUTPUT_CSV = "offit_combined.csv"
# OUTPUT_CSV = "hurst_combined.csv"
# OUTPUT_CSV = "bloomberg_combined.csv"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    return rows, fieldnames


def combine_csvs(dominant_csv, secondary_csv, output="combined.csv"):
    dominant_rows, fieldnames1 = read_csv(dominant_csv)
    secondary_rows, fieldnames2 = read_csv(secondary_csv)

    if fieldnames1 != fieldnames2:
        raise ValueError("CSV column headers do not match.")

    existing_names = set()
    combined_rows = []

    for row in dominant_rows:
        combined_rows.append(row)
        existing_names.add(row["name"])

    for row in secondary_rows:
        if row["name"] not in existing_names:
            combined_rows.append(row)
            existing_names.add(row["name"])

    combined_rows.sort(key=lambda r: r["name"])

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames1)
        writer.writeheader()
        writer.writerows(combined_rows)

    print(f"Wrote {len(combined_rows)} rows to {output}")


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("python combine_csv.py secondary_file.csv")
        return

    secondary_csv = sys.argv[1]
    combine_csvs(DOMINANT_FILE, secondary_csv, OUTPUT_CSV)


if __name__ == "__main__":
    main()