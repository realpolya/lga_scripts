import csv
import sys


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    return rows, fieldnames


def combine_csvs(csv1, csv2, output="combined.csv"):
    rows1, fieldnames1 = read_csv(csv1)
    rows2, fieldnames2 = read_csv(csv2)

    if fieldnames1 != fieldnames2:
        raise ValueError("CSV column headers do not match.")

    combined = rows1 + rows2

    unique = {}
    for row in combined:
        unique[row["name"]] = row   # overwrite duplicates

    rows = list(unique.values())

    rows.sort(key=lambda r: r["name"])

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames1)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output}")


def main():
    if len(sys.argv) != 3:
        print("Usage:")
        print("python combine_csv.py file1.csv file2.csv")
        return

    csv1 = sys.argv[1]
    csv2 = sys.argv[2]

    combine_csvs(csv1, csv2)


if __name__ == "__main__":
    main()