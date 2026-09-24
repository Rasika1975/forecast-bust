from pathlib import Path
import pandas as pd


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "forecast_error.csv"
)

THRESHOLD_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "bust_thresholds.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "bust_labels.csv"
)


# ==================================================
# LOAD DATA
# ==================================================

print("Loading forecast error data...")

df = pd.read_csv(INPUT_FILE)

required_columns = [
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

for column in required_columns:

    if column not in df.columns:

        raise ValueError(
            f"Missing column: {column}"
        )


# ==================================================
# CHECK NUMBER OF HISTORICAL RUNS
# ==================================================

run_count = df["run"].nunique()

print(
    "Historical runs found:",
    run_count
)

if run_count < 5:

    raise ValueError(
        "\nNot enough historical runs.\n"
        "At least 5 runs are required for this "
        "prototype threshold calculation.\n"
        "For a reliable model, use many more runs."
    )


# ==================================================
# REMOVE INVALID ERRORS
# ==================================================

df = df.dropna(
    subset=["forecast_error_mm"]
).copy()


# ==================================================
# CALCULATE P90 THRESHOLD
# ==================================================

print(
    "\nCalculating P90 threshold "
    "for every cell + lead day..."
)

thresholds = (
    df
    .groupby(
        [
            "cell_id",
            "latitude",
            "longitude",
            "lead_day"
        ]
    )["forecast_error_mm"]
    .quantile(0.90)
    .reset_index()
)


thresholds = thresholds.rename(
    columns={
        "forecast_error_mm":
        "p90_error_threshold_mm"
    }
)


# ==================================================
# MERGE THRESHOLDS
# ==================================================

df = df.merge(
    thresholds,
    on=[
        "cell_id",
        "latitude",
        "longitude",
        "lead_day"
    ],
    how="left"
)


# ==================================================
# CREATE BUST LABEL
# ==================================================

df["bust_label"] = (
    df["forecast_error_mm"]
    >
    df["p90_error_threshold_mm"]
).astype(int)


# ==================================================
# ERROR RATIO
# ==================================================

df["error_ratio"] = (
    df["forecast_error_mm"]
    /
    (df["p90_error_threshold_mm"] + 1e-6)
)


# ==================================================
# SAVE THRESHOLDS
# ==================================================

THRESHOLD_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

thresholds.to_csv(
    THRESHOLD_FILE,
    index=False
)


# ==================================================
# SAVE FINAL DATASET
# ==================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==================================================
# SUMMARY
# ==================================================

print("\n======================================")
print("BUST LABEL GENERATION COMPLETE")
print("======================================")

print(
    "Historical runs:",
    run_count
)

print(
    "Total rows:",
    len(df)
)

print(
    "Bust rows:",
    int(df["bust_label"].sum())
)

print(
    "Non-bust rows:",
    int(
        (df["bust_label"] == 0).sum()
    )
)

print(
    "Bust percentage:",
    round(
        df["bust_label"].mean() * 100,
        2
    ),
    "%"
)

print(
    "\nThreshold file:",
    THRESHOLD_FILE
)

print(
    "Final dataset:",
    OUTPUT_FILE
)


print("\nSample:")
print(
    df[
        [
            "cell_id",
            "lead_day",
            "forecast_error_mm",
            "p90_error_threshold_mm",
            "bust_label",
            "error_ratio"
        ]
    ].head(20)
)