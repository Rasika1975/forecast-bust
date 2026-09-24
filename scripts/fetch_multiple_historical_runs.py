from pathlib import Path
import time
from datetime import datetime, timedelta

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
    / "historical_nwp_multi_run.csv"
)


# ==================================================
# API
# ==================================================

URL = "https://single-runs-api.open-meteo.com/v1/forecast"


# ==================================================
# SETTINGS
# ==================================================

BATCH_SIZE = 10

FORECAST_DAYS = 10

# FIRST TEST
NUMBER_OF_RUNS = 5

# Start date
START_DATE = "2024-07-01"

# We use 00 UTC runs
RUN_HOUR = "00:00"


# ==================================================
# CREATE RUN DATES
# ==================================================

start_date = datetime.strptime(
    START_DATE,
    "%Y-%m-%d"
)

run_dates = [
    start_date + timedelta(days=i)
    for i in range(NUMBER_OF_RUNS)
]


run_dates = [
    d.strftime("%Y-%m-%d") + "T" + RUN_HOUR
    for d in run_dates
]


print("Historical runs:")
for run in run_dates:
    print(" ", run)


# ==================================================
# LOAD GRID
# ==================================================

grid = pd.read_csv(GRID_FILE)

required_columns = [
    "cell_id",
    "latitude",
    "longitude"
]

for column in required_columns:

    if column not in grid.columns:

        raise ValueError(
            f"Missing column: {column}"
        )


print(
    "\nTotal grid cells:",
    len(grid)
)


# ==================================================
# FETCH ONE BATCH FOR ONE RUN
# ==================================================

def fetch_batch(batch, run):

    latitudes = ",".join(
        batch["latitude"].astype(str)
    )

    longitudes = ",".join(
        batch["longitude"].astype(str)
    )

    params = {

        "latitude": latitudes,

        "longitude": longitudes,

        "run": run,

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

        print("\nAPI ERROR")
        print(response.status_code)
        print(response.text)


    response.raise_for_status()

    return response.json()


# ==================================================
# MAIN
# ==================================================

for run_number, run in enumerate(
    run_dates,
    start=1
):

    print("\n")
    print("======================================")
    print(
        f"RUN {run_number}/{len(run_dates)}"
    )
    print("ECMWF run:", run)
    print("======================================")


    total = len(grid)

    for start in range(
        0,
        total,
        BATCH_SIZE
    ):

        end = min(
            start + BATCH_SIZE,
            total
        )

        batch = grid.iloc[
            start:end
        ].copy()


        print(
            f"Fetching cells "
            f"{start + 1}-{end}/{total}"
        )


        try:

            data = fetch_batch(
                batch,
                run
            )


            if isinstance(data, list):

                locations = data

            else:

                locations = [data]


            if len(locations) != len(batch):

                raise ValueError(
                    f"Expected "
                    f"{len(batch)} locations, "
                    f"received "
                    f"{len(locations)}"
                )


            batch_records = []


            for index, item in enumerate(
                locations
            ):

                original = batch.iloc[index]

                daily = item["daily"]

                dates = daily["time"]

                rainfall = daily[
                    "precipitation_sum"
                ]


                for lead_index in range(
                    len(dates)
                ):

                    batch_records.append({

                        "run": run,

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


            batch_df = pd.DataFrame(
                batch_records
            )


            # ----------------------------------
            # CHECKPOINT SAVE
            # ----------------------------------

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


            time.sleep(1)


        except KeyboardInterrupt:

            print(
                "\nDownload interrupted."
            )

            print(
                "Already downloaded "
                "batches are saved."
            )

            raise


        except Exception as error:

            print(
                "Batch failed:",
                error
            )

            continue


# ==================================================
# FINAL SUMMARY
# ==================================================

if OUTPUT_FILE.exists():

    final_df = pd.read_csv(
        OUTPUT_FILE
    )

    print("\n")
    print("======================================")
    print("MULTI-RUN DOWNLOAD COMPLETE")
    print("======================================")

    print(
        "Historical runs:",
        final_df["run"].nunique()
    )

    print(
        "Grid cells:",
        final_df["cell_id"].nunique()
    )

    print(
        "Lead days:",
        sorted(
            final_df["lead_day"].unique()
        )
    )

    print(
        "Total rows:",
        len(final_df)
    )

    print(
        "Saved:",
        OUTPUT_FILE
    )