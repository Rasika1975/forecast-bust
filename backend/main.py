from contextlib import asynccontextmanager
from pathlib import Path
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.routes import explanations, forecast, health, risk, runs, verification
from backend.scheduler import start_daily_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start daily background auto-scheduler thread
    try:
        start_daily_scheduler(interval_hours=24)
    except Exception as e:
        print(f"Scheduler startup warning: {e}")
    yield


# ==================================================
# APP
# ==================================================

app = FastAPI(
    title="Forecast Guard API",
    description="PS 26079 - AI Forecast Bust Detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(runs.router)
app.include_router(risk.router)
app.include_router(explanations.router)
app.include_router(verification.router)
app.include_router(forecast.router)

NWP_FILE = BASE_DIR / "data" / "processed" / "nwp_grid.csv"


# ==================================================
# LOAD NWP DATA
# ==================================================


def load_nwp_data():
    if not NWP_FILE.exists():
        raise FileNotFoundError(f"NWP file not found: {NWP_FILE}")

    df = pd.read_csv(NWP_FILE)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(
        subset=["cell_id", "latitude", "longitude", "time", "precipitation"]
    ).copy()
    return df


# ==================================================
# ROOT & HEALTH
# ==================================================


@app.get("/")
def root():
    return {
        "status": "running",
        "project": "Forecast Guard",
        "problem_statement": "26079",
    }


# ==================================================
# RAW FORECAST & LOCATION
# ==================================================


@app.get("/api/forecast/raw")
def get_raw_forecast():
    try:
        df = load_nwp_data()
        return {
            "rows": len(df),
            "cells": int(df["cell_id"].nunique()),
            "data": df.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast/location")
def get_location_forecast(
    latitude: float, longitude: float, lead_day: int = Query(1, ge=1, le=10)
):
    try:
        df = load_nwp_data()

        # Find exact/nearest grid point
        df["distance"] = (df["latitude"] - latitude).abs() + (
            df["longitude"] - longitude
        ).abs()
        nearest_cell = df.sort_values("distance").iloc[0]["cell_id"]

        df = df[df["cell_id"] == nearest_cell].copy()
        start_date = df["time"].min().normalize()
        target_date = start_date + pd.Timedelta(days=lead_day - 1)
        day_df = df[df["time"].dt.normalize() == target_date]

        if day_df.empty:
            raise HTTPException(
                status_code=404, detail="Forecast not available"
            )

        return {
            "cell_id": nearest_cell,
            "latitude": float(day_df["latitude"].iloc[0]),
            "longitude": float(day_df["longitude"].iloc[0]),
            "lead_day": lead_day,
            "valid_date": target_date.strftime("%Y-%m-%d"),
            "rainfall_mm": float(day_df["precipitation"].sum()),
            "temperature_c": float(day_df["temperature_2m"].mean()),
            "humidity_percent": float(day_df["relative_humidity_2m"].mean()),
            "pressure_hpa": float(day_df["pressure_msl"].mean()),
            "wind_speed": float(day_df["wind_speed_10m"].mean()),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))