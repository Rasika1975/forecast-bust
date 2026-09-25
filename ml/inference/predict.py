import os
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

# Add parent path to allow ml imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.features.feature_engineering import FEATURE_COLUMNS, FeatureEngineer
from ml.explainability.shap_explainer import ShapExplainerService
from ml.explainability.similar_events import SimilarEventsRetriever

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_FILE = BASE_DIR / "ml" / "artifacts" / "bust_model.joblib"
NWP_FILE = BASE_DIR / "data" / "processed" / "nwp_grid.csv"
GRID_FILE = BASE_DIR / "data" / "grid" / "india_grid_enriched.csv"
PREDICTIONS_CACHE = BASE_DIR / "data" / "processed" / "operational_predictions.csv"


def get_risk_level(prob):
    if prob < 0.20:
        return "very_low"
    elif prob < 0.40:
        return "low"
    elif prob < 0.60:
        return "moderate"
    elif prob < 0.80:
        return "high"
    else:
        return "very_high"


class InferenceEngine:
    def __init__(self, model_file=None, nwp_file=None):
        self.model_file = model_file or MODEL_FILE
        self.nwp_file = nwp_file or NWP_FILE
        self._load_resources()

    def _load_resources(self):
        bundle = joblib.load(self.model_file)
        self.calibrated_model = bundle['calibrated_model']
        self.feature_columns = bundle['feature_columns']
        self.model_version = bundle.get('version', '1.2.0')
        self.trained_at = bundle.get('trained_at', '2026-09-24T18:00:00Z')

        self.feature_engineer = FeatureEngineer()
        self.shap_service = ShapExplainerService(self.model_file)
        self.similar_retriever = SimilarEventsRetriever()
        self.grid_df = pd.read_csv(GRID_FILE)
        self.grid_meta = {r['cell_id']: {'region': r['region'], 'state': r['state']} for _, r in self.grid_df.iterrows()}

        # Generate or load operational predictions
        self._ensure_operational_predictions()

    def _ensure_operational_predictions(self):
        if PREDICTIONS_CACHE.exists():
            print("Loading cached operational predictions...")
            self.predictions_df = pd.read_csv(PREDICTIONS_CACHE)
        else:
            print("Generating operational 10-day predictions...")
            self.run_full_inference()

    def run_full_inference(self):
        """
        Loads the active operational NWP forecast (10 days), computes features,
        runs calibrated XGBoost inference, and caches the results.
        """
        raw_nwp = pd.read_csv(self.nwp_file)
        raw_nwp['time'] = pd.to_datetime(raw_nwp['time'])
        start_date = raw_nwp['time'].min().normalize()

        # Aggregate hourly NWP data to daily
        daily_list = []
        for lead_day in range(1, 11):
            target_date = start_date + pd.Timedelta(days=lead_day - 1)
            day_slice = raw_nwp[raw_nwp['time'].dt.normalize() == target_date]
            if day_slice.empty:
                continue

            daily = (
                day_slice.groupby(['cell_id', 'latitude', 'longitude'], as_index=False)
                .agg({
                    'precipitation': 'sum',
                    'temperature_2m': 'mean',
                    'relative_humidity_2m': 'mean',
                    'pressure_msl': 'mean',
                    'wind_speed_10m': 'mean'
                })
                .rename(columns={
                    'precipitation': 'forecast_rainfall_mm',
                    'temperature_2m': 'temperature_c',
                    'relative_humidity_2m': 'humidity_percent',
                    'pressure_msl': 'pressure_hpa',
                    'wind_speed_10m': 'wind_speed_kmh'
                })
            )
            daily['lead_day'] = lead_day
            daily['valid_date'] = target_date.strftime("%Y-%m-%d")
            daily_list.append(daily)

        df_daily = pd.concat(daily_list, ignore_index=True)
        # Transform features
        df_features = self.feature_engineer.transform_dataframe(df_daily)

        # Run inference
        X = df_features[self.feature_columns]
        probs = self.calibrated_model.predict_proba(X)[:, 1]

        df_features['bust_probability'] = np.round(probs, 3)
        df_features['confidence'] = np.round(1.0 - probs, 3)
        df_features['risk_level'] = [get_risk_level(p) for p in probs]
        df_features['model_version'] = self.model_version
        df_features['forecast_start'] = start_date.strftime("%Y-%m-%d")

        # Add region and state
        df_features['region'] = df_features['cell_id'].map(lambda cid: self.grid_meta.get(cid, {}).get('region', 'India'))
        df_features['state'] = df_features['cell_id'].map(lambda cid: self.grid_meta.get(cid, {}).get('state', 'Unknown'))

        # Cache predictions
        df_features.to_csv(PREDICTIONS_CACHE, index=False)
        self.predictions_df = df_features
        print(f"Operational predictions cached: {len(df_features)} cells across 10 lead days.")

    def get_lead_day_predictions(self, lead_day=1, risk_filter=None, region_filter=None):
        df = self.predictions_df[self.predictions_df['lead_day'] == lead_day].copy()
        if risk_filter and risk_filter != 'all':
            if risk_filter == 'high_risk':
                df = df[df['risk_level'].isin(['high', 'very_high'])]
            elif risk_filter == 'moderate_plus':
                df = df[df['risk_level'].isin(['moderate', 'high', 'very_high'])]
            else:
                df = df[df['risk_level'] == risk_filter]

        if region_filter and region_filter != 'all':
            df = df[df['region'] == region_filter]

        return df

    def get_cell_detail(self, cell_id, lead_day=1):
        cell_match = self.predictions_df[
            (self.predictions_df['cell_id'] == cell_id) &
            (self.predictions_df['lead_day'] == lead_day)
        ]
        if cell_match.empty:
            return None

        row = cell_match.iloc[0]
        row_dict = row.to_dict()

        # SHAP explanation
        expl = self.shap_service.explain_row(row_dict, top_k=4)

        # Similar events
        similar = self.similar_retriever.find_similar(row_dict, k=3)

        return {
            "cell_id": str(row['cell_id']),
            "latitude": float(row['latitude']),
            "longitude": float(row['longitude']),
            "region": str(row.get('region', 'India')),
            "state": str(row.get('state', 'Unknown')),
            "lead_day": int(row['lead_day']),
            "valid_date": str(row['valid_date']),
            "forecast_rainfall_mm": float(row['forecast_rainfall_mm']),
            "temperature_c": float(row['temperature_c']),
            "humidity_percent": float(row['humidity_percent']),
            "pressure_hpa": float(row['pressure_hpa']),
            "wind_speed_kmh": float(row['wind_speed_kmh']),
            "bust_probability": float(row['bust_probability']),
            "confidence": float(row['confidence']),
            "risk_level": str(row['risk_level']),
            "historical_p90_error_mm": float(row.get('historical_p90_error', 25.0)),
            "historical_mae_mm": float(row.get('historical_mae', 12.0)),
            "top_reasons": expl['top_reasons'],
            "drivers": expl['drivers'],
            "similar_historical_events": similar
        }


# Singleton engine instance
_engine_instance = None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = InferenceEngine()
    return _engine_instance
