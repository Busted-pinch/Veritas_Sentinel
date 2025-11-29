import joblib
import numpy as np
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent / "models"

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
