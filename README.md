

```text

forecast-guard/
│
├── frontend/                         # React + Tailwind + Leaflet
│   │
│   ├── public/
│   │   └── data/
│   │       └── india_grid.geojson
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── LeadDaySelector.jsx
│   │   │   ├── ForecastMap.jsx
│   │   │   ├── MapLegend.jsx
│   │   │   ├── GridDetailsPanel.jsx
│   │   │   ├── RiskPanel.jsx
│   │   │   └── ExplanationPanel.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   ├── hooks/
│   │   │   └── useForecast.js
│   │   │
│   │   ├── utils/
│   │   │   └── colorScale.js
│   │   │
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   ├── .env
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
│
├── backend/                          # FastAPI
│   │
│   ├── routes/
│   │   ├── forecast.py
│   │   ├── risk.py
│   │   └── explanation.py
│   │
│   ├── services/
│   │   ├── nwp_service.py
│   │   ├── forecast_service.py
│   │   ├── prediction_service.py
│   │   └── explanation_service.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── config.py
│   └── main.py
│
│
├── ml/                                #  ML
│   │
│   ├── preprocessing/
│   │   └── prepare_training_data.py
│   │
│   ├── features/
│   │   └── feature_engineering.py
│   │
│   ├── training/
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── calibrate.py
│   │
│   ├── inference/
│   │   └── predict.py
│   │
│   ├── explainability/
│   │   └── shap_explainer.py
│   │
│   └── models/
│       └── bust_model.pkl
│
│
├── scripts/                           # Data pipeline
│   │
│   ├── create_india_grid.py
│   ├── inspect_imd.py
│   ├── process_imd.py
│   ├── fetch_nwp_grid.py
│   ├── fetch_historical_nwp.py
│   ├── fetch_historical_india.py
│   ├── fetch_multiple_historical_runs.py
│   ├── match_forecast_observation.py
│   └── create_bust_labels.py
│
│
├── data/                              # Local only, Git ignored
│   │
│   ├── boundaries/
│   │   └── india.geojson
│   │
│   ├── grid/
│   │   ├── india_grid.csv
│   │   └── india_grid.geojson
│   │
│   ├── imd/
│   │   └── rainfall_2024.nc
│   │
│   └── processed/
│       ├── imd_rainfall_2024.csv
│       ├── nwp_grid.csv
│       ├── historical_nwp_test.csv
│       ├── historical_nwp_india_2024-07-15.csv
│       ├── historical_nwp_multi_run.csv
│       ├── forecast_error.csv
│       ├── bust_thresholds.csv
│       └── bust_labels.csv
│
│
├── .gitignore
├── requirements.txt
├── README.md
└── DATA_SETUP.md
```