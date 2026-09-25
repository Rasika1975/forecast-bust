from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter(tags=["verification"])
BASE_DIR = Path(__file__).resolve().parent.parent.parent
METRICS_FILE = BASE_DIR / "ml" / "artifacts" / "metrics.json"


@router.get("/api/verification/metrics")
def get_verification_metrics():
    if not METRICS_FILE.exists():
        raise HTTPException(status_code=404, detail="Metrics not found")
    
    with open(METRICS_FILE) as f:
        metrics = json.load(f)

    return {
        "model_name": "Forecast-Guard Calibrated XGBoost",
        "model_version": "1.2.0",
        "evaluation_split": "Held-Out Test Runs (Chronological 2025 Holdout)",
        "target_definition": "P90 Historical Absolute Forecast Error (Grid & Lead Specific)",
        "total_test_samples": sum(m.get('samples', 0) for m in metrics.values()),
        "metrics_by_lead_day": metrics,
        "methodology_notes": [
            "Evaluated strictly on held-out test periods to avoid temporal leakage.",
            "Probabilities are calibrated with isotonic regression on a separate validation period.",
            "Evaluation focuses on PR-AUC, Brier score, and Expected Calibration Error (ECE) suitable for rare event modeling."
        ]
    }
