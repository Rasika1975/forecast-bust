from pathlib import Path
import requests
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_nwp_test.csv"
)

URL = "https://single-runs-api.open-meteo.com/v1/forecast"

# Test location
LATITUDE = 19.25
LONGITUDE = 73.00

# Historical ECMWF run
RUN = "2024-07-15T00:00"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,

    # Exact historical model run
    "run": RUN,

    # IMPORTANT:
    # Single Runs historical ECMWF model
    "models": "ecmwf_ifs",

    "hourly": ",".join([
        "precipitation",
        "temperature_2m",
        "relative_humidity_2m",
        "pressure_msl",
        "wind_speed_10m"
    ]),

    "forecast_days": 10,

    "timezone": "UTC",

    "cell_selection": "nearest"
}


print("======================================")
print("HISTORICAL ECMWF FORECAST DOWNLOAD")
print("======================================")
print("Run      :", RUN)
print("Location :", LATITUDE, LONGITUDE)
print("Model    : ECMWF IFS HRES")
print()


try:

    response = requests.get(
        URL,
        params=params,
        timeout=120
    )

    print("HTTP Status:", response.status_code)

    # If API returns an error,
    # print the actual reason.
    if response.status_code != 200:
        print("\nAPI ERROR:")
        print(response.text)
        response.raise_for_status()

    data = response.json()

    print("Historical forecast downloaded successfully.")


    # -----------------------------------------
    # Extract hourly data
    # -----------------------------------------

    hourly = data["hourly"]

    df = pd.DataFrame({
        "run": RUN,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "time": hourly["time"],

        "precipitation": hourly["precipitation"],
        "temperature_2m": hourly["temperature_2m"],
        "relative_humidity_2m": hourly["relative_humidity_2m"],
        "pressure_msl": hourly["pressure_msl"],
        "wind_speed_10m": hourly["wind_speed_10m"]
    })


    # -----------------------------------------
    # Save
    # -----------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print()
    print("======================================")
    print("SUCCESS")
    print("======================================")
    print("Rows :", len(df))
    print("File :", OUTPUT_FILE)

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nLast 5 rows:")
    print(df.tail())


except requests.RequestException as e:

    print()
    print("REQUEST FAILED")
    print(e)