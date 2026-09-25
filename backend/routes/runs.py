from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(tags=["runs"])
BASE_DIR = Path(__file__).resolve().parent.parent.parent
METRICS_FILE = BASE_DIR / "ml" / "artifacts" / "metrics.json"

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": "Forecast Guard AI",
        "model_loaded": True,
        "data_freshness": "operational",
        "timestamp": "2026-09-24T18:30:00Z"
    }

@router.get("/api/runs/latest")
def get_latest_run():
    return {
        "run_id": "ECMWF_IFS_20260924_00Z",
        "init_time": "2026-09-24T00:00:00Z",
        "model": "ECMWF IFS 0.25° HRES",
        "spatial_resolution": "0.25° × 0.25° (~27 km)",
        "spatial_coverage": "India Domain (6.5°N - 38.5°N, 66.5°E - 100.0°E)",
        "total_active_cells": 4651,
        "lead_days_available": 10,
        "forecast_window": "Day 1 (2026-09-24) to Day 10 (2026-10-03)",
        "model_version": "v1.2.0 (Calibrated XGBoost + SHAP)",
        "status": "Ready"
    }
