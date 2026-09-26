import json
import os
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score
)
from xgboost import XGBClassifier

# Add parent path to allow ml imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.stdout.reconfigure(line_buffering=True)
from ml.features.feature_engineering import FEATURE_COLUMNS, FeatureEngineer
from ml.models.calibrator import CalibratedBustPredictor

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LABELS_FILE = BASE_DIR / "data" / "processed" / "bust_labels.csv"
ARTIFACTS_DIR = BASE_DIR / "ml" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_ece(y_true, y_prob, n_bins=10):
    bin_limits = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)
    for i in range(n_bins):
        bin_mask = (y_prob >= bin_limits[i]) & (y_prob < bin_limits[i + 1])
        if np.sum(bin_mask) > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(y_prob[bin_mask])
            ece += (np.sum(bin_mask) / total_samples) * np.abs(bin_acc - bin_conf)
    return float(ece)


def train_single_hazard(hazard_key, label_col, artifact_filename, df_features):
    print(f"\n--- Training XGBoost for Hazard: {hazard_key.upper()} ({label_col}) ---")

    runs_sorted = sorted(df_features['run'].unique())
    train_runs = runs_sorted[:8]
    val_runs = runs_sorted[8:10]
    test_runs = runs_sorted[10:]

    train_mask = df_features['run'].isin(train_runs)
    val_mask = df_features['run'].isin(val_runs)
    test_mask = df_features['run'].isin(test_runs)

    X_train = df_features.loc[train_mask, FEATURE_COLUMNS]
    y_train = df_features.loc[train_mask, label_col]

    X_val = df_features.loc[val_mask, FEATURE_COLUMNS]
    y_val = df_features.loc[val_mask, label_col]

    X_test = df_features.loc[test_mask, FEATURE_COLUMNS]
    y_test = df_features.loc[test_mask, label_col]

    pos_weight = float((len(y_train) - sum(y_train)) / max(1, sum(y_train)))

    xgb = XGBClassifier(
        n_estimators=160,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=pos_weight * 0.7,
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1
    )
    xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    val_raw_probs = xgb.predict_proba(X_val)[:, 1]
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99)
    iso.fit(val_raw_probs, y_val)
    calibrated_model = CalibratedBustPredictor(xgb, iso)

    test_df_eval = df_features.loc[test_mask].copy()
    test_probs = calibrated_model.predict_proba(X_test)[:, 1]
    test_df_eval['p_bust'] = test_probs
    test_df_eval['pred_bust'] = (test_probs >= 0.40).astype(int)

    metrics_by_lead = {}
    for lead in range(1, 11):
        lead_mask = (test_df_eval['lead_day'] == lead)
        y_true_lead = test_df_eval.loc[lead_mask, label_col].values
        y_prob_lead = test_df_eval.loc[lead_mask, 'p_bust'].values
        y_pred_lead = test_df_eval.loc[lead_mask, 'pred_bust'].values

        if len(y_true_lead) > 0 and sum(y_true_lead) > 0:
            pr_auc = float(average_precision_score(y_true_lead, y_prob_lead))
            roc_auc = float(roc_auc_score(y_true_lead, y_prob_lead))
            recall = float(recall_score(y_true_lead, y_pred_lead, zero_division=0))
            prec = float(precision_score(y_true_lead, y_pred_lead, zero_division=0))
            f1 = float(f1_score(y_true_lead, y_pred_lead, zero_division=0))
            brier = float(brier_score_loss(y_true_lead, y_prob_lead))
            ece = compute_ece(y_true_lead, y_prob_lead)
        else:
            pr_auc, roc_auc, recall, prec, f1, brier, ece = 0, 0, 0, 0, 0, 0, 0

        metrics_by_lead[f"Day {lead}"] = {
            "lead_day": lead,
            "pr_auc": round(pr_auc, 3),
            "roc_auc": round(roc_auc, 3),
            "recall": round(recall, 3),
            "precision": round(prec, 3),
            "f1": round(f1, 3),
            "brier_score": round(brier, 4),
            "ece": round(ece, 4),
            "samples": len(y_true_lead),
            "actual_busts": int(sum(y_true_lead))
        }

    importances = xgb.feature_importances_
    feat_imp = sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True)

    model_bundle = {
        'calibrated_model': calibrated_model,
        'base_xgb': xgb,
        'hazard': hazard_key,
        'feature_columns': FEATURE_COLUMNS,
        'feature_importances': dict(feat_imp),
        'version': '1.2.0',
        'train_samples': len(X_train),
        'trained_at': '2026-09-24T18:00:00Z'
    }

    joblib.dump(model_bundle, ARTIFACTS_DIR / artifact_filename)
    return metrics_by_lead


def main():
    print("=" * 60)
    print("PS 26079: MULTI-HAZARD XGBOOST TRAINING ENGINE (RAINFALL, HEATWAVE, WINDSTORM)")
    print("=" * 60)

    df_raw = pd.read_csv(LABELS_FILE)
    fe = FeatureEngineer()
    df_features = fe.transform_dataframe(df_raw)

    metrics_rain = train_single_hazard("rain", "bust_label_rain", "bust_model.joblib", df_features)
    metrics_temp = train_single_hazard("temp", "bust_label_temp", "bust_model_temp.joblib", df_features)
    metrics_wind = train_single_hazard("wind", "bust_label_wind", "bust_model_wind.joblib", df_features)

    combined_metrics = {
        "rain": metrics_rain,
        "temp": metrics_temp,
        "wind": metrics_wind
    }

    # Save default metrics.json (rain) and multi-hazard metrics
    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics_rain, f, indent=2)

    with open(ARTIFACTS_DIR / "metrics_multihazard.json", "w") as f:
        json.dump(combined_metrics, f, indent=2)

    print(f"\nAll 3 multi-hazard models and evaluation metrics saved in {ARTIFACTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
