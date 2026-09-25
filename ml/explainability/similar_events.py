from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LABELS_FILE = BASE_DIR / "data" / "processed" / "bust_labels.csv"
INDEX_FILE = BASE_DIR / "ml" / "artifacts" / "similar_events.joblib"

ANALOG_FEATURES = [
    'lead_day',
    'forecast_rainfall_mm',
    'temperature_c',
    'humidity_percent',
    'pressure_hpa',
    'wind_speed_kmh',
    'latitude',
    'longitude'
]


class SimilarEventsRetriever:
    def __init__(self, index_file=None):
        self.index_file = index_file or INDEX_FILE
        if not Path(self.index_file).exists():
            self.build_index()
        else:
            self._load_index()

    def build_index(self):
        print("Building Similar Events nearest-neighbor retrieval index...")
        df = pd.read_csv(LABELS_FILE)
        # Filter to historical cases that were actual busts (bust_label == 1) or large errors
        busts = df[df['bust_label'] == 1].copy()
        if len(busts) < 50:
            busts = df.nlargest(1000, 'forecast_error_mm').copy()

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(busts[ANALOG_FEATURES].values)

        nn = NearestNeighbors(n_neighbors=8, metric='euclidean')
        nn.fit(X_scaled)

        # Store metadata table
        meta = busts[[
            'run', 'valid_date', 'cell_id', 'latitude', 'longitude',
            'region', 'lead_day', 'forecast_rainfall_mm', 'actual_rainfall',
            'forecast_error_mm', 'bias_mm'
        ]].copy().reset_index(drop=True)

        bundle = {
            'scaler': scaler,
            'nn': nn,
            'metadata': meta,
            'features': ANALOG_FEATURES
        }
        joblib.dump(bundle, self.index_file)
        self.scaler = scaler
        self.nn = nn
        self.metadata = meta
        print(f"Similar events index built with {len(meta)} historical bust cases.")

    def _load_index(self):
        bundle = joblib.load(self.index_file)
        self.scaler = bundle['scaler']
        self.nn = bundle['nn']
        self.metadata = bundle['metadata']

    def find_similar(self, query_dict, k=3):
        """
        Given a cell's current conditions, finds the k most similar historical forecast busts.
        """
        query_vec = np.array([[query_dict.get(col, 0.0) for col in ANALOG_FEATURES]])
        query_scaled = self.scaler.transform(query_vec)
        distances, indices = self.nn.kneighbors(query_scaled, n_neighbors=k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            row = self.metadata.iloc[idx]
            sim_pct = max(10, int(round(100.0 / (1.0 + dist))))
            
            bias = float(row['bias_mm'])
            if bias > 15:
                outcome_desc = "Overpredicted Rain (False Alarm)"
            elif bias < -15:
                outcome_desc = "Underpredicted Extreme Rain (Missed Event)"
            else:
                outcome_desc = "Timing / Spatial Displacement Bust"

            results.append({
                "historical_run": str(row['run']),
                "valid_date": str(row['valid_date']),
                "region": str(row['region']),
                "lead_day": int(row['lead_day']),
                "cell_id": str(row['cell_id']),
                "lat": float(row['latitude']),
                "lon": float(row['longitude']),
                "forecast_rainfall_mm": float(row['forecast_rainfall_mm']),
                "actual_rainfall_mm": float(row['actual_rainfall']),
                "realized_error_mm": float(row['forecast_error_mm']),
                "bust_category": outcome_desc,
                "similarity_score_percent": sim_pct
            })
        return results
