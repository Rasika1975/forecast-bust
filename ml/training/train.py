import json
import os
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
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
    """Computes Expected Calibration Error across probability bins."""
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


def main():
    print("=" * 60)
    print("PS 26079: TRAINING XGBOOST FORECAST BUST MODEL")
    print("=" * 60)

    print("\n[1/5] Loading historical labeled runs...")
    df_raw = pd.read_csv(LABELS_FILE)
    print(f"Loaded {len(df_raw)} records across {df_raw['run'].nunique()} runs.")

    print("\n[2/5] Engineering meteorological and spatial features...")
    fe = FeatureEngineer()
    df_features = fe.transform_dataframe(df_raw)
    print(f"Features created: {len(FEATURE_COLUMNS)} columns.")

    # Chronological Split (Section 13.1)
    # 12 runs: 0-7 = Train (66%), 8-9 = Validation (17%), 10-11 = Test (17%)
    runs_sorted = sorted(df_features['run'].unique())
    train_runs = runs_sorted[:8]
    val_runs = runs_sorted[8:10]
    test_runs = runs_sorted[10:]

    print(f"Train runs: {train_runs}")
    print(f"Val runs  : {val_runs}")
    print(f"Test runs : {test_runs}")

    train_mask = df_features['run'].isin(train_runs)
    val_mask = df_features['run'].isin(val_runs)
    test_mask = df_features['run'].isin(test_runs)

    X_train = df_features.loc[train_mask, FEATURE_COLUMNS]
    y_train = df_features.loc[train_mask, 'bust_label']

    X_val = df_features.loc[val_mask, FEATURE_COLUMNS]
    y_val = df_features.loc[val_mask, 'bust_label']

    X_test = df_features.loc[test_mask, FEATURE_COLUMNS]
    y_test = df_features.loc[test_mask, 'bust_label']

    print(f"Train samples: {len(X_train)} (Bust rate: {y_train.mean():.3f})")
    print(f"Val samples  : {len(X_val)} (Bust rate: {y_val.mean():.3f})")
    print(f"Test samples : {len(X_test)} (Bust rate: {y_test.mean():.3f})")

    # Class imbalance handling
    pos_weight = float((len(y_train) - sum(y_train)) / max(1, sum(y_train)))
    print(f"Class imbalance scale_pos_weight: {pos_weight:.2f}")

    print("\n[3/5] Fitting XGBoost Classifier...")
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

    print("\n[4/5] Probability Calibration (Isotonic Regression on Val)...")
    val_raw_probs = xgb.predict_proba(X_val)[:, 1]
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99)
    iso.fit(val_raw_probs, y_val)
    calibrated_model = CalibratedBustPredictor(xgb, iso)
    print("Probability calibration complete.")

    print("\n[5/5] Lead-Time Verification on Held-Out Test Set (Section 19)...")
    test_df_eval = df_features.loc[test_mask].copy()
    test_probs = calibrated_model.predict_proba(X_test)[:, 1]
    test_df_eval['p_bust'] = test_probs
    test_df_eval['pred_bust'] = (test_probs >= 0.40).astype(int)

    metrics_by_lead = {}
    print(f"{'Lead Day':<10} | {'PR-AUC':<8} | {'ROC-AUC':<8} | {'Recall':<8} | {'Precision':<10} | {'F1':<8} | {'Brier':<8} | {'ECE':<8}")
    print("-" * 84)

    for lead in range(1, 11):
        lead_mask = (test_df_eval['lead_day'] == lead)
        y_true_lead = test_df_eval.loc[lead_mask, 'bust_label'].values
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

        print(f"Day {lead:<6} | {pr_auc:<8.3f} | {roc_auc:<8.3f} | {recall:<8.3f} | {prec:<10.3f} | {f1:<8.3f} | {brier:<8.4f} | {ece:<8.4f}")

    # Feature Importance
    importances = xgb.feature_importances_
    feat_imp = sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True)
    print("\nTop 7 Model Features:")
    for feat, imp in feat_imp[:7]:
        print(f"  {feat:<25}: {imp:.4f}")

    # Save artifacts
    model_bundle = {
        'calibrated_model': calibrated_model,
        'base_xgb': xgb,
        'feature_columns': FEATURE_COLUMNS,
        'feature_importances': dict(feat_imp),
        'version': '1.2.0',
        'train_samples': len(X_train),
        'trained_at': '2026-09-24T18:00:00Z'
    }

    joblib.dump(model_bundle, ARTIFACTS_DIR / "bust_model.joblib")
    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics_by_lead, f, indent=2)

    print(f"\nTrained model and metrics saved in {ARTIFACTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
