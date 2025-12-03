# backend/app/ml/engine.py

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any

from backend.app.ml.predictor import predict_transaction as heuristic_predict

BASE_PATH = Path(__file__).resolve().parent / "models"

# These are loaded for future use if you want to plug in real models.
supervised_model = joblib.load(BASE_PATH / "supervised_xgb.pkl")
anomaly_model = joblib.load(BASE_PATH / "anomaly_iforest.pkl")
scaler = joblib.load(BASE_PATH / "scaler.pkl")

print("✔ ML models loaded successfully")

# MUST match Colab FEATURE_COLUMNS exactly
FEATURE_COLUMNS = [
    "step",
    "amount",
    "isFlaggedFraud",
]


def scale_features(raw_features: dict):
    """
    raw_features: dict from API
    returns: scaled numpy array in correct order
    """
    try:
        row = [raw_features[col] for col in FEATURE_COLUMNS]
    except KeyError as e:
        missing = str(e)
        raise ValueError(
            f"Missing feature in request: {missing}. "
            f"Required keys: {FEATURE_COLUMNS}"
        )

    arr = np.array(row).reshape(1, -1)
    return scaler.transform(arr)


class TransactionEngine:
    """
    Thin wrapper so the rest of the app can call
    engine.predict_transaction(features, profile).

    Right now this delegates to the heuristic predictor in predictor.py.
    Later you can swap to supervised_model / anomaly_model + scaler.
    """

    def __init__(self):
        self.supervised_model = supervised_model
        self.anomaly_model = anomaly_model
        self.scaler = scaler

    def predict_transaction(self, features: Dict, profile: Dict) -> Dict[str, Any]:
        # Currently we just use the heuristic predictor
        return heuristic_predict(features, profile)
