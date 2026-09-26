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
MODEL_FILE_RAIN = BASE_DIR / "ml" / "artifacts" / "bust_model.joblib"
MODEL_FILE_TEMP = BASE_DIR / "ml" / "artifacts" / "bust_model_temp.joblib"
MODEL_FILE_WIND = BASE_DIR / "ml" / "artifacts" / "bust_model_wind.joblib"

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
    def __init__(self, nwp_file=None):
        self.nwp_file = nwp_file or NWP_FILE
        self._load_resources()

    def _load_resources(self):
        # Load multi-hazard models
        self.models = {}
        for h_key, f_path in [('rain', MODEL_FILE_RAIN), ('temp', MODEL_FILE_TEMP), ('wind', MODEL_FILE_WIND)]:
            if f_path.exists():
                bundle = joblib.load(f_path)
                self.models[h_key] = bundle['calibrated_model']
            else:
                bundle = joblib.load(MODEL_FILE_RAIN)
                self.models[h_key] = bundle['calibrated_model']

        bundle_rain = joblib.load(MODEL_FILE_RAIN)
        self.feature_columns = bundle_rain['feature_columns']
        self.model_version = bundle_rain.get('version', '1.2.0')

        self.feature_engineer = FeatureEngineer()
        self.shap_service = ShapExplainerService(MODEL_FILE_RAIN)
        self.similar_retriever = SimilarEventsRetriever()
        self.grid_df = pd.read_csv(GRID_FILE)
        self.grid_meta = {r['cell_id']: {'region': r['region'], 'state': r['state']} for _, r in self.grid_df.iterrows()}

        self._ensure_operational_predictions()

    def _ensure_operational_predictions(self):
        if PREDICTIONS_CACHE.exists():
            df = pd.read_csv(PREDICTIONS_CACHE)
            # Require at least 46,510 rows (4,651 cells * 10 lead days)
            if len(df) >= 46510:
                print("Loading cached operational predictions (4,651 cells)...")
                self.predictions_df = df
                return
            print(f"Predictions cache incomplete ({len(df)} rows). Regenerating full predictions...")

        self.run_full_inference()

    def run_full_inference(self):
        # Auto-rebuild nwp_grid if missing or incomplete (<4651 cells)
        if not self.nwp_file.exists() or pd.read_csv(self.nwp_file)['cell_id'].nunique() < 4651:
            print("nwp_grid.csv missing or incomplete. Rebuilding full national dataset...")
            import subprocess
            subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "build_complete_dataset.py")], check=True)

        raw_nwp = pd.read_csv(self.nwp_file)
        raw_nwp['time'] = pd.to_datetime(raw_nwp['time'])
        start_date = raw_nwp['time'].min().normalize()

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
        df_features = self.feature_engineer.transform_dataframe(df_daily)
        X = df_features[self.feature_columns]

        # Predict multi-hazard probabilities
        for h_key in ['rain', 'temp', 'wind']:
            model = self.models[h_key]
            probs = model.predict_proba(X)[:, 1]
            p_col = 'bust_probability' if h_key == 'rain' else f'bust_probability_{h_key}'
            c_col = 'confidence' if h_key == 'rain' else f'confidence_{h_key}'
            r_col = 'risk_level' if h_key == 'rain' else f'risk_level_{h_key}'

            df_features[p_col] = np.round(probs, 3)
            df_features[c_col] = np.round(1.0 - probs, 3)
            df_features[r_col] = [get_risk_level(p) for p in probs]

        df_features['model_version'] = self.model_version
        df_features['forecast_start'] = start_date.strftime("%Y-%m-%d")

        df_features['region'] = df_features['cell_id'].map(lambda cid: self.grid_meta.get(cid, {}).get('region', 'India'))
        df_features['state'] = df_features['cell_id'].map(lambda cid: self.grid_meta.get(cid, {}).get('state', 'Unknown'))

        df_features.to_csv(PREDICTIONS_CACHE, index=False)
        self.predictions_df = df_features
        print(f"Operational predictions cached: {len(df_features)} cells across 10 lead days.")

    def get_lead_day_predictions(self, lead_day=1, risk_filter=None, region_filter=None, hazard='rain'):
        df = self.predictions_df[self.predictions_df['lead_day'] == lead_day].copy()

        # Map hazard specific columns to primary bust_probability & risk_level
        p_col = 'bust_probability' if hazard == 'rain' else f'bust_probability_{hazard}'
        c_col = 'confidence' if hazard == 'rain' else f'confidence_{hazard}'
        r_col = 'risk_level' if hazard == 'rain' else f'risk_level_{hazard}'

        if p_col in df.columns:
            df['bust_probability'] = df[p_col]
            df['confidence'] = df[c_col]
            df['risk_level'] = df[r_col]

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

    def get_cell_detail(self, cell_id, lead_day=1, hazard='rain'):
        cell_match = self.predictions_df[
            (self.predictions_df['cell_id'] == cell_id) &
            (self.predictions_df['lead_day'] == lead_day)
        ]
        if cell_match.empty:
            return None

        row = cell_match.iloc[0]
        row_dict = row.to_dict()

        p_col = 'bust_probability' if hazard == 'rain' else f'bust_probability_{hazard}'
        c_col = 'confidence' if hazard == 'rain' else f'confidence_{hazard}'
        r_col = 'risk_level' if hazard == 'rain' else f'risk_level_{hazard}'

        prob = float(row.get(p_col, row['bust_probability']))
        conf = float(row.get(c_col, row['confidence']))
        r_lvl = str(row.get(r_col, row['risk_level']))

        expl = self.shap_service.explain_row(row_dict, top_k=4)
        similar = self.similar_retriever.find_similar(row_dict, k=3)

        return {
            "cell_id": str(row['cell_id']),
            "latitude": float(row['latitude']),
            "longitude": float(row['longitude']),
            "region": str(row.get('region', 'India')),
            "state": str(row.get('state', 'Unknown')),
            "hazard": hazard,
            "lead_day": int(row['lead_day']),
            "valid_date": str(row['valid_date']),
            "forecast_rainfall_mm": float(row['forecast_rainfall_mm']),
            "temperature_c": float(row['temperature_c']),
            "humidity_percent": float(row['humidity_percent']),
            "pressure_hpa": float(row['pressure_hpa']),
            "wind_speed_kmh": float(row['wind_speed_kmh']),
            "bust_probability": prob,
            "confidence": conf,
            "risk_level": r_lvl,
            "historical_p90_error_mm": float(row.get('historical_p90_error', 25.0)),
            "top_reasons": expl['top_reasons'],
            "drivers": expl['drivers'],
            "similar_historical_events": similar
        }


_engine_instance = None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = InferenceEngine()
    return _engine_instance
