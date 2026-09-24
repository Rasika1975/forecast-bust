from pathlib import Path
import time
import pandas as pd
import requests


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
    / "nwp_grid.csv"
)

URL = "https://api.open-meteo.com/v1/ecmwf"

# 50 coordinates per request
BATCH_SIZE = 50

FORECAST_DAYS = 10


# ==================================================
# LOAD GRID
# ==================================================

grid = pd.read_csv(GRID_FILE)

print("Total India grid cells:", len(grid))

required = [
    "cell_id",
    "latitude",
    "longitude"
]

for col in required:
    if col not in grid.columns:
        raise ValueError(f"Missing column: {col}")


# ==================================================
# REMOVE OLD TEST FILE
# ==================================================

if OUTPUT_FILE.exists():
    print("Existing nwp_grid.csv found.")
    print("For full fresh download, deleting old file...")
    OUTPUT_FILE.unlink()


# ==================================================
# FETCH BATCH
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

        "hourly": ",".join([
            "precipitation",
            "temperature_2m",
            "relative_humidity_2m",
            "pressure_msl",
            "wind_speed_10m"
        ]),

        "forecast_days": FORECAST_DAYS,

        "timezone": "UTC",

        "models": "ecmwf_ifs025",

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

total = len(grid)
successful_cells = 0

for start in range(
    0,
    total,
    BATCH_SIZE
):

    end = min(
        start + BATCH_SIZE,
        total
    )

    batch = grid.iloc[start:end].copy()

    print(
        f"Fetching cells "
        f"{start + 1}-{end}/{total}"
    )

    try:

        data = fetch_batch(batch)

        if not isinstance(data, list):
            data = [data]

        if len(data) != len(batch):
            raise ValueError(
                f"Expected {len(batch)} responses, "
                f"got {len(data)}"
            )

        records = []

        for idx, item in enumerate(data):

            row = batch.iloc[idx]

            hourly = item["hourly"]

            times = hourly["time"]

            precipitation = hourly["precipitation"]
            temperature = hourly["temperature_2m"]
            humidity = hourly["relative_humidity_2m"]
            pressure = hourly["pressure_msl"]
            wind = hourly["wind_speed_10m"]

            for i in range(len(times)):

                records.append({
                    "cell_id": row["cell_id"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "time": times[i],
                    "precipitation": precipitation[i],
                    "temperature_2m": temperature[i],
                    "relative_humidity_2m": humidity[i],
                    "pressure_msl": pressure[i],
                    "wind_speed_10m": wind[i]
                })

        batch_df = pd.DataFrame(records)

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

        successful_cells += len(batch)

        print(
            f"Saved {len(batch)} cells"
        )

        time.sleep(1)

    except Exception as e:

        print(
            f"FAILED batch "
            f"{start + 1}-{end}: {e}"
        )


# ==================================================
# FINAL CHECK
# ==================================================

print("\n===================================")
print("CURRENT NWP FULL INDIA COMPLETE")
print("===================================")

if OUTPUT_FILE.exists():

    df = pd.read_csv(OUTPUT_FILE)

    print(
        "Unique cells:",
        df["cell_id"].nunique()
    )

    print(
        "Rows:",
        len(df)
    )

    print(
        "Time range:",
        df["time"].min(),
        "→",
        df["time"].max()
    )

else:

    print("Output file not created.")