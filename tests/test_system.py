import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True


def test_latest_run():
    res = client.get("/api/runs/latest")
    assert res.status_code == 200
    data = res.json()
    assert data["total_active_cells"] == 4651
    assert data["lead_days_available"] == 10
    assert "ECMWF" in data["model"]


def test_forecast_map():
    res = client.get("/api/forecast/map?lead_day=1")
    assert res.status_code == 200
    data = res.json()
    assert data["lead_day"] == 1
    assert len(data["cells"]) == 4651
    cell0 = data["cells"][0]
    assert "cell_id" in cell0
    assert "bust_probability" in cell0
    assert "confidence" in cell0
    assert "risk_level" in cell0
    assert "rainfall_mm" in cell0
    assert 0.0 <= cell0["bust_probability"] <= 1.0
    assert abs((cell0["bust_probability"] + cell0["confidence"]) - 1.0) < 0.01


def test_day_summary():
    res = client.get("/api/summary?lead_day=3")
    assert res.status_code == 200
    data = res.json()
    assert data["lead_day"] == 3
    assert data["total_cells"] == 4651
    assert "average_confidence" in data
    assert "high_risk_cells" in data


def test_cell_risk_detail():
    res = client.get("/api/risk/cell/CELL_00100?lead_day=3")
    assert res.status_code == 200
    data = res.json()
    assert data["cell_id"] == "CELL_00100"
    assert "bust_probability" in data
    assert "confidence" in data
    assert "historical_p90_error_mm" in data
    assert len(data["top_reasons"]) > 0
    assert len(data["similar_historical_events"]) > 0


def test_cell_explanation():
    res = client.get("/api/explanation/cell/CELL_00100?lead_day=3")
    assert res.status_code == 200
    data = res.json()
    assert "shap_drivers" in data
    assert len(data["shap_drivers"]) > 0
    assert "top_reasons" in data


def test_similar_events():
    res = client.get("/api/similar-events/cell/CELL_00100?lead_day=3&k=3")
    assert res.status_code == 200
    data = res.json()
    assert data["similar_cases_count"] == 3
    assert len(data["cases"]) == 3
    c0 = data["cases"][0]
    assert "historical_run" in c0
    assert "realized_error_mm" in c0
    assert "similarity_score_percent" in c0


def test_verification_metrics():
    res = client.get("/api/verification/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "metrics_by_lead_day" in data
    metrics = data["metrics_by_lead_day"]
    assert "Day 1" in metrics
    assert "Day 5" in metrics
    assert "Day 10" in metrics
    d5 = metrics["Day 5"]
    assert "pr_auc" in d5
    assert "brier_score" in d5
    assert "recall" in d5


def test_multihazard_forecast():
    for h in ["rain", "temp", "wind"]:
        res = client.get(f"/api/forecast/map?lead_day=1&hazard={h}")
        assert res.status_code == 200
        data = res.json()
        assert data["hazard"] == h
        assert len(data["cells"]) == 4651
        
        summary_res = client.get(f"/api/summary?lead_day=1&hazard={h}")
        assert summary_res.status_code == 200
        summary_data = summary_res.json()
        assert summary_data["hazard"] == h
