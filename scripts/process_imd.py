from pathlib import Path
import xarray as xr
import pandas as pd


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "imd"
    / "rainfall_2024.nc"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "imd_rainfall_2024.csv"
)


# --------------------------------------------------
# LOAD IMD NETCDF
# --------------------------------------------------

print("Loading IMD rainfall dataset...")

ds = xr.open_dataset(INPUT_FILE)

print("Dataset loaded successfully.")


# --------------------------------------------------
# EXTRACT RAINFALL
# --------------------------------------------------

rainfall = ds["RAINFALL"]


# --------------------------------------------------
# CONVERT TO TABLE
# --------------------------------------------------

df = rainfall.to_dataframe(
    name="actual_rainfall"
).reset_index()


# --------------------------------------------------
# RENAME COLUMNS
# --------------------------------------------------

df = df.rename(
    columns={
        "TIME": "date",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude"
    }
)


# --------------------------------------------------
# REMOVE MISSING VALUES
# --------------------------------------------------

df = df.dropna(
    subset=["actual_rainfall"]
)


# --------------------------------------------------
# KEEP ONLY REQUIRED COLUMNS
# --------------------------------------------------

df = df[
    [
        "date",
        "latitude",
        "longitude",
        "actual_rainfall"
    ]
]


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# RESULT
# --------------------------------------------------

print("\n===================================")
print("IMD PROCESSING COMPLETE")
print("===================================")

print("Rows:", len(df))

print("Columns:")
print(df.columns.tolist())

print("\nSample:")
print(df.head())

print("\nSaved to:")
print(OUTPUT_FILE)