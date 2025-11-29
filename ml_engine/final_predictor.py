import joblib
import numpy as np
from behavior.deviation import deviation_score
from behavior.trust import compute_trust

# Load models
supervised = joblib.load("models/supervised_xgb.pkl")
iso = joblib.load("models/anomaly_iforest.pkl")

def predict_full(features, user_profile):

    # 1. Fraud Probability
    fraud_prob = supervised.predict_proba([features])[0][1] * 100

    # 2. Anomaly Score
    anomaly_raw = iso.decision_function([features])[0]
    anomaly_score = abs(anomaly_raw) * 100

    # 3. Behavior Deviation
    deviation = deviation_score(
        features["amount"],
        user_profile["avg_amount"],
        user_profile["std_amount"]
    )

    # 4. Trust Score
    trust = user_profile["trust"]

    # 5. Combined Scam Probability
    final = (
        0.45 * fraud_prob +
        0.30 * anomaly_score +
        0.20 * deviation +
        0.10 * (100 - trust)
    )

    return {
        "fraud_probability": fraud_prob,
        "anomaly_score": anomaly_score,
        "deviation": deviation,
        "trust_score": trust,
        "final_risk_score": final
    }
