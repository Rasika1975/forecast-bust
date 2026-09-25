from __future__ import annotations

import pandas as pd

try:
    from ..config import GRID_RESOLUTION, NWP_FILE, TOTAL_INDIA_GRID_CELLS
except ImportError:
    from config import GRID_RESOLUTION, NWP_FILE, TOTAL_INDIA_GRID_CELLS


class ForecastDataUnavailableError(Exception):
    """Raised when the requested forecast period has no data."""


_REQUIRED_COLUMNS = {
    "cell_id",
    "latitude",
    "longitude",
    "time",
    "precipitation",
    "temperature_2m",
    "relative_humidity_2m",
    "pressure_msl",
    "wind_speed_10m",
}


def load_nwp_data() -> pd.DataFrame:
    if not NWP_FILE.exists():
        raise FileNotFoundError(f"NWP file not found: {NWP_FILE}")

    data = pd.read_csv(NWP_FILE)
    missing_columns = sorted(_REQUIRED_COLUMNS - set(data.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"NWP file is missing required columns: {missing}")

    data["time"] = pd.to_datetime(data["time"], errors="coerce")
    return data.dropna(
        subset=["cell_id", "latitude", "longitude", "time", "precipitation"]
    ).copy()


def _target_day(data: pd.DataFrame, lead_day: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    start_date = data["time"].min().normalize()
    target_date = start_date + pd.Timedelta(days=lead_day - 1)
    return start_date, target_date


def build_daily_forecast_payload(data: pd.DataFrame, lead_day: int) -> dict:
    start_date, target_date = _target_day(data, lead_day)
    day_data = data[data["time"].dt.normalize() == target_date].copy()

    if day_data.empty:
        raise ForecastDataUnavailableError(
            f"No forecast data available for Day {lead_day}"
        )

    daily = (
        day_data.groupby(
            ["cell_id", "latitude", "longitude"],
            as_index=False,
        )
        .agg(
            {
                "precipitation": "sum",
                "temperature_2m": "mean",
                "relative_humidity_2m": "mean",
                "pressure_msl": "mean",
                "wind_speed_10m": "mean",
            }
        )
        .rename(
            columns={
                "precipitation": "rainfall_mm",
                "temperature_2m": "temperature_c",
                "relative_humidity_2m": "humidity_percent",
                "pressure_msl": "pressure_hpa",
                "wind_speed_10m": "wind_speed_kmh",
            }
        )
    )

    return {
        "forecast_start": start_date.strftime("%Y-%m-%d"),
        "lead_day": lead_day,
        "valid_date": target_date.strftime("%Y-%m-%d"),
        "grid_resolution": GRID_RESOLUTION,
        "cells": daily.to_dict(orient="records"),
        "forecast_data_available": int(len(daily)),
        "total_grid_cells": TOTAL_INDIA_GRID_CELLS,
    }


def get_daily_forecast(lead_day: int) -> dict:
    return build_daily_forecast_payload(load_nwp_data(), lead_day)


def get_raw_forecast() -> dict:
    data = load_nwp_data()
    return {
        "rows": len(data),
        "cells": int(data["cell_id"].nunique()),
        "data": data.to_dict(orient="records"),
    }


def get_location_forecast(
    latitude: float,
    longitude: float,
    lead_day: int,
) -> dict:
    data = load_nwp_data()
    data["distance"] = (
        (data["latitude"] - latitude).abs()
        + (data["longitude"] - longitude).abs()
    )

    nearest_cell = data.sort_values("distance").iloc[0]["cell_id"]
    cell_data = data[data["cell_id"] == nearest_cell].copy()
    start_date, target_date = _target_day(cell_data, lead_day)
    day_data = cell_data[cell_data["time"].dt.normalize() == target_date]

    if day_data.empty:
        raise ForecastDataUnavailableError("Forecast not available")

    return {
        "cell_id": nearest_cell,
        "latitude": float(day_data["latitude"].iloc[0]),
        "longitude": float(day_data["longitude"].iloc[0]),
        "lead_day": lead_day,
        "valid_date": target_date.strftime("%Y-%m-%d"),
        "rainfall_mm": float(day_data["precipitation"].sum()),
        "temperature_c": float(day_data["temperature_2m"].mean()),
        "humidity_percent": float(day_data["relative_humidity_2m"].mean()),
        "pressure_hpa": float(day_data["pressure_msl"].mean()),
        "wind_speed": float(day_data["wind_speed_10m"].mean()),
    }
