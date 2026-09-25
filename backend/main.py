from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException, Query


# ==================================================
# APP
# ==================================================

app = FastAPI(
    title="Forecast Guard API",
    description="PS 26079 - AI Forecast Bust Detection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# PATH
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

NWP_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "nwp_grid.csv"
)


# ==================================================
# LOAD NWP DATA
# ==================================================

def load_nwp_data():

    if not NWP_FILE.exists():
        raise FileNotFoundError(
            f"NWP file not found: {NWP_FILE}"
        )

    df = pd.read_csv(NWP_FILE)

    # Convert time
    df["time"] = pd.to_datetime(
        df["time"],
        errors="coerce"
    )

    # Remove invalid rows
    df = df.dropna(
        subset=[
            "cell_id",
            "latitude",
            "longitude",
            "time",
            "precipitation"
        ]
    ).copy()

    return df


# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "project": "Forecast Guard",
        "problem_statement": "26079"
    }


# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ==================================================
# RAW FORECAST
# ==================================================

@app.get("/api/forecast/raw")
def get_raw_forecast():

    try:

        df = load_nwp_data()

        return {
            "rows": len(df),
            "cells": int(
                df["cell_id"].nunique()
            ),
            "data": (
                df.to_dict(
                    orient="records"
                )
            )
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==================================================
# DAILY GRID FORECAST
# ==================================================

def build_daily_forecast_payload(
    df: pd.DataFrame,
    lead_day: int
):
    start_date = (
        df["time"]
        .min()
        .normalize()
    )

    target_date = (
        start_date
        + pd.Timedelta(
            days=lead_day - 1
        )
    )

    day_df = df[
        df["time"].dt.normalize()
        == target_date
    ].copy()

    if day_df.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No forecast data "
                f"available for Day {lead_day}"
            )
        )

    daily = (
        day_df
        .groupby(
            [
                "cell_id",
                "latitude",
                "longitude"
            ],
            as_index=False
        )
        .agg({
            "precipitation": "sum",
            "temperature_2m": "mean",
            "relative_humidity_2m": "mean",
            "pressure_msl": "mean",
            "wind_speed_10m": "mean"
        })
    )

    daily = daily.rename(
        columns={
            "precipitation": "rainfall_mm",
            "temperature_2m": "temperature_c",
            "relative_humidity_2m": "humidity_percent",
            "pressure_msl": "pressure_hpa",
            "wind_speed_10m": "wind_speed_kmh"
        }
    )

    return {
        "forecast_start": start_date.strftime("%Y-%m-%d"),
        "lead_day": lead_day,
        "valid_date": target_date.strftime("%Y-%m-%d"),
        "grid_resolution": "0.25 degree",
        "cells": daily.to_dict(orient="records"),
        "forecast_data_available": int(len(daily)),
        "total_grid_cells": 4651,
    }


@app.get("/api/forecast/grid")
def get_daily_grid_forecast(

    lead_day: int = Query(
        1,
        ge=1,
        le=10
    )

):

    try:

        df = load_nwp_data()
        payload = build_daily_forecast_payload(df, lead_day)

        return payload

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/forecast/map")
def get_forecast_map(

    lead_day: int = Query(
        1,
        ge=1,
        le=10
    )

):

    try:

        df = load_nwp_data()
        payload = build_daily_forecast_payload(df, lead_day)

        return payload

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==================================================
# SINGLE LOCATION
# ==================================================

@app.get("/api/forecast/location")
def get_location_forecast(

    latitude: float,
    longitude: float,
    lead_day: int = Query(
        1,
        ge=1,
        le=10
    )

):

    try:

        df = load_nwp_data()

        # Find exact/nearest grid point
        df["distance"] = (
            (df["latitude"] - latitude).abs()
            +
            (df["longitude"] - longitude).abs()
        )

        nearest_cell = (
            df.sort_values("distance")
            .iloc[0]["cell_id"]
        )

        df = df[
            df["cell_id"]
            == nearest_cell
        ].copy()

        start_date = (
            df["time"]
            .min()
            .normalize()
        )

        target_date = (
            start_date
            + pd.Timedelta(
                days=lead_day - 1
            )
        )

        day_df = df[
            df["time"].dt.normalize()
            == target_date
        ]

        if day_df.empty:

            raise HTTPException(
                status_code=404,
                detail="Forecast not available"
            )

        return {
            "cell_id":
                nearest_cell,

            "latitude":
                float(
                    day_df["latitude"].iloc[0]
                ),

            "longitude":
                float(
                    day_df["longitude"].iloc[0]
                ),

            "lead_day":
                lead_day,

            "valid_date":
                target_date.strftime(
                    "%Y-%m-%d"
                ),

            "rainfall_mm":
                float(
                    day_df["precipitation"].sum()
                ),

            "temperature_c":
                float(
                    day_df["temperature_2m"].mean()
                ),

            "humidity_percent":
                float(
                    day_df[
                        "relative_humidity_2m"
                    ].mean()
                ),

            "pressure_hpa":
                float(
                    day_df[
                        "pressure_msl"
                    ].mean()
                ),

            "wind_speed":
                float(
                    day_df[
                        "wind_speed_10m"
                    ].mean()
                )
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )