from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.inference.predict import get_engine

router = APIRouter(tags=["risk"])


@router.get("/api/risk")
def get_risk_grid(
    lead_day: int = Query(1, ge=1, le=10),
    risk_level: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    hazard: str = Query("rain")
):
    try:
        engine = get_engine()
        df = engine.get_lead_day_predictions(
            lead_day=lead_day,
            risk_filter=risk_level,
            region_filter=region,
            hazard=hazard
        )
        
        records = df[[
            'cell_id', 'latitude', 'longitude', 'region', 'state',
            'forecast_rainfall_mm', 'temperature_c', 'wind_speed_kmh',
            'bust_probability', 'confidence', 'risk_level', 'valid_date'
        ]].to_dict(orient="records")

        return {
            "run_time": "2026-09-24T00:00:00Z",
            "lead_day": lead_day,
            "hazard": hazard,
            "valid_date": records[0]['valid_date'] if records else None,
            "total_cells": len(records),
            "grid": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/risk/cell/{cell_id}")
def get_cell_risk(
    cell_id: str,
    lead_day: int = Query(1, ge=1, le=10),
    hazard: str = Query("rain")
):
    try:
        engine = get_engine()
        detail = engine.get_cell_detail(cell_id, lead_day=lead_day, hazard=hazard)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Cell {cell_id} not found for Day {lead_day}")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/summary")
def get_lead_summary(
    lead_day: int = Query(1, ge=1, le=10),
    hazard: str = Query("rain")
):
    try:
        engine = get_engine()
        df = engine.get_lead_day_predictions(lead_day=lead_day, hazard=hazard)

        total = len(df)
        high_risk_count = int(df['risk_level'].isin(['high', 'very_high']).sum())
        moderate_risk_count = int((df['risk_level'] == 'moderate').sum())
        low_risk_count = int(df['risk_level'].isin(['low', 'very_low']).sum())
        
        avg_confidence = float(df['confidence'].mean())
        avg_bust_prob = float(df['bust_probability'].mean())
        max_rain = float(df['forecast_rainfall_mm'].max())

        # Regional breakdown of high risk cells
        reg_breakdown = (
            df[df['risk_level'].isin(['high', 'very_high'])]
            .groupby('region')['cell_id']
            .count()
            .to_dict()
        )

        return {
            "lead_day": lead_day,
            "hazard": hazard,
            "valid_date": df['valid_date'].iloc[0] if not df.empty else None,
            "total_cells": total,
            "high_risk_cells": high_risk_count,
            "moderate_risk_cells": moderate_risk_count,
            "low_risk_cells": low_risk_count,
            "high_risk_percentage": round((high_risk_count / max(1, total)) * 100, 1),
            "average_confidence": round(avg_confidence * 100, 1),
            "average_bust_probability": round(avg_bust_prob * 100, 1),
            "max_forecast_rainfall_mm": round(max_rain, 1),
            "regional_high_risk_breakdown": reg_breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
