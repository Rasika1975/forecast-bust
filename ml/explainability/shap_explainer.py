from pathlib import Path
import joblib
import numpy as np
import shap

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_FILE = BASE_DIR / "ml" / "artifacts" / "bust_model.joblib"


class ShapExplainerService:
    def __init__(self, model_file=None):
        self.model_file = model_file or MODEL_FILE
        self._load_model()

    def _load_model(self):
        bundle = joblib.load(self.model_file)
        self.base_xgb = bundle['base_xgb']
        self.feature_columns = bundle['feature_columns']
        # Initialize SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.base_xgb)

    def explain_row(self, feature_row, top_k=4):
        """
        Explains a single feature row (dict or pd.Series/1D array).
        Returns top positive drivers and human-readable natural language text.
        """
        if isinstance(feature_row, dict):
            vals = np.array([[feature_row.get(col, 0.0) for col in self.feature_columns]])
        elif hasattr(feature_row, 'values'):
            vals = feature_row[self.feature_columns].values.reshape(1, -1)
        else:
            vals = np.array(feature_row).reshape(1, -1)

        shap_values = self.explainer.shap_values(vals)
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            sv = shap_values[0]

        row_dict = {col: float(vals[0][i]) for i, col in enumerate(self.feature_columns)}
        
        # Rank by positive impact (increasing bust risk)
        ranked_indices = np.argsort(sv)[::-1]

        reasons = []
        detailed_drivers = []

        for idx in ranked_indices:
            col = self.feature_columns[idx]
            impact = float(sv[idx])
            val = float(vals[0][idx])

            if impact <= 0.01 and len(detailed_drivers) >= top_k:
                break

            reason_text = self._format_reason(col, val, row_dict)
            detailed_drivers.append({
                "feature": col,
                "impact": round(impact, 3),
                "feature_value": round(val, 2),
                "driver_label": reason_text
            })
            reasons.append(reason_text)

            if len(detailed_drivers) >= top_k:
                break

        return {
            "top_reasons": reasons,
            "drivers": detailed_drivers
        }

    def _format_reason(self, col, val, row):
        lead = int(row.get('lead_day', 5))
        if col == 'historical_p90_error':
            return f"High historical Day-{lead} baseline error (P90 threshold: {val:.1f} mm)"
        elif col == 'spatial_gradient':
            return f"Strong local rainfall contrast ({val:.1f} mm gradient across 3×3 grid)"
        elif col == 'temporal_pressure_diff':
            sign = "drop" if val < 0 else "shift"
            return f"Rapid pressure {sign} ({abs(val):.1f} hPa / 24h)"
        elif col == 'temporal_rain_diff':
            return f"Sudden forecast precipitation swing ({val:+.1f} mm)"
        elif col == 'forecast_rainfall_mm':
            return f"Heavy forecast rainfall accumulation ({val:.1f} mm)"
        elif col == 'is_cyclonic_convective' and val > 0.5:
            return "Active cyclonic low-pressure & high-wind regime"
        elif col == 'is_heavy_rain_regime' and val > 0.5:
            return "Heavy-rainfall monsoon convective regime"
        elif col == 'wind_speed_kmh':
            return f"Elevated surface wind velocity ({val:.1f} km/h)"
        elif col == 'rain_to_p90_ratio':
            return f"Forecast rain exceeds normal grid skill envelope ({val:.1f}x P90)"
        elif col == 'neighbor_max_rain':
            return f"Intense adjacent precipitation cell ({val:.1f} mm in neighborhood)"
        elif col == 'humidity_percent':
            return f"High atmospheric moisture saturation ({val:.1f}%)"
        else:
            clean_name = col.replace('_', ' ').capitalize()
            return f"Elevated {clean_name} ({val:.1f})"
