from pathlib import Path
import time

import pandas as pd
import requests


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

GRID_FILE = (
    BASE_DIR
    / "data"
    / "grid"
    / "india_grid.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_nwp_india_2024-07-15.csv"
)


# ==================================================
# API
# ==================================================

URL = "https://single-runs-api.open-meteo.com/v1/forecast"

RUN = "2024-07-15T00:00"


# ==================================================
# SETTINGS
# ==================================================

# Number of cells in one API request
BATCH_SIZE = 10

# 10-day forecast
FORECAST_DAYS = 10

# Save after every batch
SAVE_EVERY_BATCH = True


# ==================================================
# LOAD GRID
# ==================================================

print("Loading India grid...")

grid = pd.read_csv(GRID_FILE)

required_columns = [
    "cell_id",
    "latitude",
    "longitude"
]

for column in required_columns:
    if column not in grid.columns:
        raise ValueError(
            f"Missing required column: {column}"
        )

print("Total grid cells:", len(grid))


# ==================================================
# RESUME SUPPORT
# ==================================================

processed_cells = set()

if OUTPUT_FILE.exists():

    print("\nExisting output file found.")

    old_data = pd.read_csv(OUTPUT_FILE)

    if "cell_id" in old_data.columns:

        processed_cells = set(
            old_data["cell_id"].astype(str).unique()
        )

    print(
        "Already processed cells:",
        len(processed_cells)
    )

else:

    print("\nNo existing output file.")
    print("Starting from beginning.")


# Remove already processed cells
grid["cell_id"] = grid["cell_id"].astype(str)

remaining_grid = grid[
    ~grid["cell_id"].isin(processed_cells)
].copy()

print(
    "Remaining cells:",
    len(remaining_grid)
)


# ==================================================
# FETCH FUNCTION
# ==================================================

def fetch_batch(batch):

    latitudes = ",".join(
        batch["latitude"].astype(str)
    )

    longitudes = ",".join(
        batch["longitude"].astype(str)
    )

    params = {

        "latitude": latitudes,

        "longitude": longitudes,

        "run": RUN,

        "models": "ecmwf_ifs",

        "daily": "precipitation_sum",

        "forecast_days": FORECAST_DAYS,

        "timezone": "UTC",

        "cell_selection": "nearest"
    }

    response = requests.get(
        URL,
        params=params,
        timeout=180
    )

    if response.status_code != 200:

        print("\n========== API ERROR ==========")
        print("Status:", response.status_code)
        print(response.text)
        print("================================\n")

    response.raise_for_status()

    return response.json()


# ==================================================
# MAIN
# ==================================================

total_remaining = len(remaining_grid)

for start in range(
    0,
    total_remaining,
    BATCH_SIZE
):

    end = min(
        start + BATCH_SIZE,
        total_remaining
    )

    batch = remaining_grid.iloc[start:end].copy()

    print(
        f"\nFetching cells "
        f"{start + 1}-{end} / {total_remaining}"
    )

    try:

        data = fetch_batch(batch)

        if isinstance(data, list):
            locations = data
        else:
            locations = [data]

        if len(locations) != len(batch):

            raise ValueError(
                f"Expected {len(batch)} locations "
                f"but received {len(locations)}"
            )

        batch_records = []

        for index, item in enumerate(locations):

            original = batch.iloc[index]

            daily = item["daily"]

            dates = daily["time"]

            rainfall = daily["precipitation_sum"]

            for lead_index in range(len(dates)):

                batch_records.append({

                    "run": RUN,

                    "cell_id":
                        original["cell_id"],

                    "latitude":
                        original["latitude"],

                    "longitude":
                        original["longitude"],

                    "lead_day":
                        lead_index + 1,

                    "valid_date":
                        dates[lead_index],

                    "forecast_rainfall_mm":
                        rainfall[lead_index]
                })

        batch_df = pd.DataFrame(batch_records)

        # ==================================================
        # CHECKPOINT SAVE
        # ==================================================

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if OUTPUT_FILE.exists():

            batch_df.to_csv(
                OUTPUT_FILE,
                mode="a",
                header=False,
                index=False
            )

        else:

            batch_df.to_csv(
                OUTPUT_FILE,
                index=False
            )

        print(
            f"Batch saved: "
            f"{len(batch)} cells"
        )

        time.sleep(1)

    except KeyboardInterrupt:

        print(
            "\nDownload interrupted by user."
        )

        print(
            "Already completed batches "
            "have been saved."
        )

        print(
            "Run this script again to resume."
        )

        break

    except Exception as error:

        print(
            f"\nFAILED batch "
            f"{start + 1}-{end}"
        )

        print(
            "Reason:",
            error
        )

        print(
            "Continuing with next batch..."
        )


# ==================================================
# FINAL SUMMARY
# ==================================================

if OUTPUT_FILE.exists():

    final_df = pd.read_csv(
        OUTPUT_FILE
    )

    print("\n======================================")
    print("HISTORICAL NWP DOWNLOAD STATUS")
    print("======================================")

    print(
        "Processed cells:",
        final_df["cell_id"].nunique()
    )

    print(
        "Total rows:",
        len(final_df)
    )

    print(
        "Lead days:",
        sorted(
            final_df["lead_day"].unique()
        )
    )

    print(
        "Saved:",
        OUTPUT_FILE
    )

else:

    print(
        "\nNo output file was created."
    )