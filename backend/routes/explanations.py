from fastapi import APIRouter, HTTPException, Query
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.inference.predict import get_engine

router = APIRouter(tags=["explanations"])


@router.get("/api/explanation/cell/{cell_id}")
def get_cell_explanation(
    cell_id: str,
    lead_day: int = Query(1, ge=1, le=10)
):
    try:
        engine = get_engine()
        detail = engine.get_cell_detail(cell_id, lead_day=lead_day)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Cell {cell_id} not found for Day {lead_day}")

        return {
            "cell_id": cell_id,
            "lead_day": lead_day,
            "bust_probability": detail["bust_probability"],
            "confidence": detail["confidence"],
            "risk_level": detail["risk_level"],
            "top_reasons": detail["top_reasons"],
            "shap_drivers": detail["drivers"],
            "context": (
                f"Forecast confidence is {int(detail['confidence']*100)}% because "
                f"atmospheric and historical factors indicate elevated bust risk: "
                f"{'; '.join(detail['top_reasons'])}."
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/similar-events/cell/{cell_id}")
def get_similar_events(
    cell_id: str,
    lead_day: int = Query(1, ge=1, le=10),
    k: int = Query(3, ge=1, le=8)
):
    try:
        engine = get_engine()
        detail = engine.get_cell_detail(cell_id, lead_day=lead_day)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Cell {cell_id} not found for Day {lead_day}")

        return {
            "cell_id": cell_id,
            "lead_day": lead_day,
            "query_forecast_rain_mm": detail["forecast_rainfall_mm"],
            "similar_cases_count": len(detail["similar_historical_events"][:k]),
            "cases": detail["similar_historical_events"][:k]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
