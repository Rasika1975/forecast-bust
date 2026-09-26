from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks

from backend.scheduler import get_sync_status, run_live_fetch_and_inference

router = APIRouter(tags=["runs"])
BASE_DIR = Path(__file__).resolve().parent.parent.parent


@router.get("/health")
def get_health():
    sync = get_sync_status()
    return {
        "status": "healthy",
        "service": "Forecast Guard AI",
        "model_loaded": True,
        "data_freshness": sync.get("status", "operational"),
        "last_sync": sync.get("last_sync"),
        "data_source": sync.get("data_source"),
    }


@router.get("/api/runs/latest")
def get_latest_run():
    sync = get_sync_status()
    today = datetime.now(timezone.utc)
    day1_str = today.strftime("%Y-%m-%d")
    day10_str = (today + timedelta(days=9)).strftime("%Y-%m-%d")

    return {
        "run_id": f"ECMWF_IFS_{today.strftime('%Y%m%d')}_00Z",
        "init_time": f"{day1_str}T00:00:00Z",
        "model": "ECMWF IFS 0.25° HRES",
        "spatial_resolution": "0.25° × 0.25° (~27 km)",
        "spatial_coverage": "India Domain (6.5°N - 38.5°N, 66.5°E - 100.0°E)",
        "total_active_cells": 4651,
        "lead_days_available": 10,
        "forecast_window": f"Day 1 ({day1_str}) to Day 10 ({day10_str})",
        "model_version": "v1.2.0 (Calibrated XGBoost + SHAP)",
        "status": sync.get("status", "Ready"),
        "last_sync": sync.get("last_sync"),
        "data_source": sync.get("data_source"),
    }


@router.get("/api/runs/sync-status")
def get_sync_info():
    return get_sync_status()


@router.post("/api/runs/sync-now")
def trigger_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_live_fetch_and_inference)
    return {
        "message": "Live automated NWP fetch & ML inference sync initiated in background.",
        "status": "in_progress",
    }
