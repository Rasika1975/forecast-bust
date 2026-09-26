from fastapi import APIRouter, HTTPException, Query
import json
from pathlib import Path

router = APIRouter(tags=["verification"])
BASE_DIR = Path(__file__).resolve().parent.parent.parent
METRICS_FILE = BASE_DIR / "ml" / "artifacts" / "metrics.json"
METRICS_MULTI_FILE = BASE_DIR / "ml" / "artifacts" / "metrics_multihazard.json"


@router.get("/api/verification/metrics")
def get_verification_metrics(hazard: str = Query("rain")):
    multi = None
    if METRICS_MULTI_FILE.exists():
        with open(METRICS_MULTI_FILE) as f:
            multi = json.load(f)
        metrics = multi.get(hazard, multi.get("rain", {}))
    elif METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            metrics = json.load(f)
    else:
        raise HTTPException(status_code=404, detail="Metrics not found")

    return {
        "model_name": f"Forecast-Guard Calibrated XGBoost ({hazard.upper()} Hazard)",
        "model_version": "1.2.0",
        "hazard": hazard,
        "evaluation_split": "Held-Out Test Runs (Chronological 2025 Holdout)",
        "target_definition": "P90 Historical Absolute Forecast Error (Grid & Lead Specific)",
        "total_test_samples": sum(m.get('samples', 0) for m in metrics.values()),
        "metrics_by_lead_day": metrics,
        "multihazard_summary": multi,
        "methodology_notes": [
            "Evaluated strictly on held-out test periods to avoid temporal leakage.",
            "Probabilities are calibrated with isotonic regression on a separate validation period.",
            "Evaluation focuses on PR-AUC, Brier score, and Expected Calibration Error (ECE) suitable for rare event modeling."
        ]
    }
