import numpy as np

class CalibratedBustPredictor:
    """
    Wrapper combining base probability model (XGBoost) with Isotonic Regression
    calibrator fitted on validation split.
    """
    def __init__(self, base_model, calibrator):
        self.base_model = base_model
        self.calibrator = calibrator

    def predict_proba(self, X):
        raw_p = self.base_model.predict_proba(X)[:, 1]
        cal_p = np.clip(self.calibrator.predict(raw_p), 0.001, 0.999)
        return np.column_stack([1.0 - cal_p, cal_p])

    def predict(self, X, threshold=0.40):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)
