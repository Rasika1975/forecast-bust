# Forecast-Guard AI (PS 26079)
## AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts

> **Problem Statement 26079**: Build an operational AI reliability layer placed on top of Numerical Weather Prediction (NWP) forecasts (ECMWF IFS 0.25° grid over India) that estimates the probability of unusually large forecast errors ($P(Bust)$) for Day 1 to Day 10, provides an interactive confidence map ($Confidence = 1 - P(Bust)$), and delivers interpretable meteorological explanations (SHAP drivers and historical similar-event analogs).

---

## 1. System Overview & Architecture

```text
ECMWF IFS Forecast (Day 1-10) ──┐
                                ├──► Common 0.25° India Grid (4,651 cells)
IMD Daily Gridded Rainfall ─────┘              │
                                               ▼
                              Spatial, Temporal & Regime Features
                                               │
                                               ▼
                                 Calibrated XGBoost Classifier
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               ▼                                                               ▼
   P(Bust) & Confidence Map                                        Explainability Engine
   - 0-20% Green (Very Low Risk)                                   - TreeExplainer SHAP Values
   - 20-40% Lime (Low Risk)                                        - Positive Driver Narratives
   - 40-60% Amber (Moderate Risk)                                  - Historical Similar Events
   - 60-80% Orange (High Risk)                                       (Nearest-Neighbor Analogs)
   - 80-100% Red (Very High Risk)                                              │
               │                                                               │
               └───────────────────────────────┬───────────────────────────────┘
                                               ▼
                                     FastAPI Backend Engine
                                               │
                                               ▼
                               React + Leaflet Interactive Dashboard
```

---

## 2. Core Methodologies Implemented

### A. Grid & Bust Definition
- **Common Grid**: 0.25° × 0.25° regular grid over India containing **4,651 cells** clipped to national boundaries, partitioned into meteorological sub-regions (Western Ghats, North-East, Central India, Northern Plains, etc.).
- **Historical Error Matching**: Realized error $E = |Forecast - Observed|$ computed across historical runs.
- **Bust Threshold**: $Threshold(cell, lead) = P_{90}[E \mid cell, lead]$.
- **Bust Label**: $Bust = 1$ if $E > Threshold(cell, lead)$, else $0$.
- **Confidence Metric**: $Confidence = 1 - P(Bust)$.

### B. Feature Engineering
- **NWP State**: 24h precipitation sum, 2m temperature, relative humidity, sea-level pressure, 10m wind speed.
- **Lead Horizon**: Day 1 to Day 10.
- **Location**: Latitude, longitude, regional macro-zone.
- **Historical Skill**: Grid cell historical MAE, bias, and P90 error threshold.
- **Spatial Context**: 3×3 neighborhood mean, max, std, and local spatial gradient ($|Rain_{cell} - Rain_{mean}|$) computed via sparse matrix projections.
- **Temporal Evolutions**: 24h precipitation difference and baroclinic pressure tendency.
- **Weather Regimes**: Heavy-rainfall regime ($>30$ mm), cyclonic low-pressure/high-shear regime ($P < 1002$ hPa, $W > 22$ km/h), and convective gradient ratios.

### C. Machine Learning Engine
- **Primary Model**: Global XGBoost Classifier handling class imbalance (`scale_pos_weight`).
- **Probability Calibration**: Isotonic Regression fitted strictly on an intermediate validation period.
- **Explainability**: SHAP `TreeExplainer` converting positive contributions into meteorological text (e.g. "Forecast rain exceeds normal grid skill envelope (4.6x P90)", "Rapid baroclinic pressure drop").
- **Historical Analogs**: Nearest-neighbor retrieval over 92,474 historical bust situations returning date, forecast rain, actual realized rain, and error category.
- **Chronological Verification**: Evaluated on unseen holdout test periods reporting PR-AUC, ROC-AUC, Recall/POD, Precision, F1, Brier Score, and Expected Calibration Error (ECE) across all 10 lead days.

---

## 3. Directory Structure

```text
forecast-bust/
├── backend/                          # FastAPI Backend
│   ├── routes/
│   │   ├── runs.py                   # Latest run metadata & health
│   │   ├── risk.py                   # Grid risk predictions & cell drilldown
│   │   ├── explanations.py           # SHAP drivers & similar historical analogs
│   │   ├── verification.py           # Section 19 model evaluation metrics
│   │   └── forecast.py               # Combined map payload
│   └── main.py                       # FastAPI application & CORS
│
├── frontend/                         # React + Vite + Leaflet + Tailwind
│   ├── public/data/
│   │   ├── india.geojson             # India boundary
│   │   └── india_grid.geojson        # 4,651 0.25° grid cells
│   ├── src/
│   │   ├── components/
│   │   │   ├── IndiaMap.jsx          # Interactive Leaflet confidence & risk map
│   │   │   ├── DaySelector.jsx       # Day 1 to 10 horizon selector
│   │   │   ├── MapLegend.jsx         # Dual-mode legend (Risk & Precipitation)
│   │   │   ├── GridInfoPanel.jsx     # 4-tab drilldown (Risk, Weather, SHAP, Analogs)
│   │   │   └── VerificationModal.jsx # Section 19 model evaluation report
│   │   ├── services/
│   │   │   └── api.js                # API client
│   │   └── App.jsx                   # Main operational dashboard
│   ├── package.json
│   └── vite.config.js
│
├── ml/                               # Machine Learning System
│   ├── features/
│   │   └── feature_engineering.py   # Spatial, temporal, regime, & skill features
│   ├── models/
│   │   └── calibrator.py            # CalibratedBustPredictor wrapper
│   ├── training/
│   │   └── train.py                 # Time-split XGBoost training & calibration
│   ├── explainability/
│   │   ├── shap_explainer.py        # TreeExplainer positive driver translator
│   │   └── similar_events.py        # Nearest-neighbor historical analog engine
│   ├── inference/
│   │   └── predict.py               # Operational prediction caching & serving
│   └── artifacts/
│       ├── bust_model.joblib        # Calibrated model bundle
│       ├── metrics.json             # Day 1 to 10 verification metrics
│       └── similar_events.joblib    # Historical analog database
│
├── data/
│   ├── boundaries/india.geojson      # India national boundary
│   ├── grid/
│   │   ├── india_grid.csv            # 4,651 grid points
│   │   └── india_grid_enriched.csv   # Points with state & region metadata
│   └── processed/
│       ├── forecast_error.csv        # Historical forecast-observation logs
│       ├── bust_thresholds.csv       # Cell & lead specific P90 thresholds
│       ├── bust_labels.csv           # Labeled bust events
│       └── nwp_grid.csv              # Operational 10-day ECMWF forecast
│
├── scripts/
│   └── build_complete_dataset.py     # Reproducible foundation data generator
│
├── tests/
│   └── test_system.py               # Pytest automated test suite
├── requirements.txt
└── README.md
```

---

## 4. Running the Project

### 1. Backend Setup
```bash
# From forecast-bust/
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Docs available at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
# In another terminal, from forecast-bust/frontend/
npm install
npm run dev
```
Dashboard available at: `http://localhost:5173`

### 3. Run Automated Tests
```bash
pytest tests/test_system.py -v
```

---

## 5. API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service and data freshness status |
| `GET` | `/api/runs/latest` | Latest operational NWP forecast metadata |
| `GET` | `/api/forecast/map?lead_day=5` | Map payload combining weather & bust probability |
| `GET` | `/api/risk?lead_day=5` | Grid predictions with bust probability & risk level |
| `GET` | `/api/risk/cell/{cell_id}?lead_day=5` | Cell drilldown with P90 threshold & drivers |
| `GET` | `/api/summary?lead_day=5` | Domain-wide KPI metrics and regional summary |
| `GET` | `/api/explanation/cell/{cell_id}?lead_day=5` | SHAP drivers and natural language reasons |
| `GET` | `/api/similar-events/cell/{cell_id}?lead_day=5` | Historical matching bust events |
| `GET` | `/api/verification/metrics` | Day 1 to Day 10 model evaluation metrics |