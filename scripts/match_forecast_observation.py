from pathlib import Path
import pandas as pd


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

NWP_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_nwp_india_2024-07-15.csv"
)

IMD_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "imd_rainfall_2024.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "forecast_error.csv"
)


# ==================================================
# LOAD
# ==================================================

print("Loading ECMWF historical forecast...")

nwp = pd.read_csv(NWP_FILE)

print("NWP rows:", len(nwp))

print("\nLoading IMD observations...")

imd = pd.read_csv(IMD_FILE)

print("IMD rows:", len(imd))


# ==================================================
# DATE CONVERSION
# ==================================================

nwp["valid_date"] = pd.to_datetime(
    nwp["valid_date"]
).dt.strftime("%Y-%m-%d")

imd["date"] = pd.to_datetime(
    imd["date"]
).dt.strftime("%Y-%m-%d")


# ==================================================
# COORDINATE NORMALIZATION
# ==================================================

nwp["latitude"] = nwp["latitude"].round(2)
nwp["longitude"] = nwp["longitude"].round(2)

imd["latitude"] = imd["latitude"].round(2)
imd["longitude"] = imd["longitude"].round(2)


# ==================================================
# KEEP REQUIRED IMD COLUMNS
# ==================================================

imd = imd[
    [
        "date",
        "latitude",
        "longitude",
        "actual_rainfall"
    ]
].copy()


# ==================================================
# MERGE
# ==================================================

print("\nMatching ECMWF with IMD...")

merged = nwp.merge(
    imd,
    left_on=[
        "valid_date",
        "latitude",
        "longitude"
    ],
    right_on=[
        "date",
        "latitude",
        "longitude"
    ],
    how="inner"
)


# ==================================================
# ERROR
# ==================================================

merged["forecast_error_mm"] = (
    merged["forecast_rainfall_mm"]
    - merged["actual_rainfall"]
).abs()


# ==================================================
# FINAL COLUMNS
# ==================================================

result = merged[
    [
        "run",
        "cell_id",
        "latitude",
        "longitude",
        "lead_day",
        "valid_date",
        "forecast_rainfall_mm",
        "actual_rainfall",
        "forecast_error_mm"
    ]
].copy()


# ==================================================
# SAVE
# ==================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==================================================
# SUMMARY
# ==================================================

print("\n======================================")
print("FORECAST + IMD MATCH COMPLETE")
print("======================================")

print("Matched rows:", len(result))

print(
    "Cells matched:",
    result["cell_id"].nunique()
)

print(
    "Lead days:",
    sorted(result["lead_day"].unique())
)

print("\nSaved:")
print(OUTPUT_FILE)

print("\nSample:")
print(result.head(15))