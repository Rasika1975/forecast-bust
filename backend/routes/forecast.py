from fastapi import APIRouter, HTTPException, Query
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.inference.predict import get_engine

router = APIRouter(tags=["forecast"])


@router.get("/api/forecast/map")
def get_forecast_map(
    lead_day: int = Query(1, ge=1, le=10),
    hazard: str = Query("rain")
):
    try:
        engine = get_engine()
        df = engine.get_lead_day_predictions(lead_day=lead_day, hazard=hazard)
        if df.empty:
            raise HTTPException(
                status_code=404, detail=f"No forecast data available for Day {lead_day}"
            )

        cells = []
        for _, row in df.iterrows():
            cells.append({
                "cell_id": str(row["cell_id"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "region": str(row.get("region", "India")),
                "state": str(row.get("state", "Unknown")),
                "rainfall_mm": float(row.get("forecast_rainfall_mm", 0.0)),
                "forecast_rainfall_mm": float(row.get("forecast_rainfall_mm", 0.0)),
                "temperature_c": float(row.get("temperature_c", 25.0)),
                "humidity_percent": float(row.get("humidity_percent", 70.0)),
                "pressure_hpa": float(row.get("pressure_hpa", 1010.0)),
                "wind_speed_kmh": float(row.get("wind_speed_kmh", 10.0)),
                "hazard": hazard,
                "bust_probability": float(row["bust_probability"]),
                "confidence": float(row["confidence"]),
                "risk_level": str(row["risk_level"]),
                "valid_date": str(row.get("valid_date", "")),
            })

        start_date = (
            str(df["forecast_start"].iloc[0])
            if "forecast_start" in df.columns and not df.empty
            else "2026-09-24"
        )
        valid_date = (
            str(df["valid_date"].iloc[0])
            if "valid_date" in df.columns and not df.empty
            else ""
        )

        return {
            "forecast_start": start_date,
            "lead_day": lead_day,
            "hazard": hazard,
            "valid_date": valid_date,
            "grid_resolution": "0.25 degree",
            "cells": cells,
            "forecast_data_available": len(cells),
            "total_grid_cells": 4651,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
