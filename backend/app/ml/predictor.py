# backend/app/ml/predictor.py
from backend.app.ml.engine import supervised_model, anomaly_model, scale_features

def compute_deviation(current_amount: float, avg: float, std: float):
    if std == 0:
        return 0.0
    return min(abs(current_amount - avg) / std, 100.0)


def compute_final_risk(fraud_prob, anomaly_score, deviation_score, trust_score):
    """
    Combine all scores into one final risk score.
    """
    final_score = (
        0.45 * fraud_prob +
        0.30 * anomaly_score +
        0.20 * deviation_score +
        0.10 * (100.0 - trust_score)
    )
    return float(round(final_score, 2))


def get_risk_level(score: float) -> str:
    if score < 30:
        return "low"
    elif score < 60:
        return "medium"
    elif score < 80:
        return "high"
    else:
        return "critical"


def _to_float(x):
    # Safely convert numpy / int / float to built-in float
    try:
        return float(x)
    except Exception:
        return x


def predict_transaction(features: dict, user_profile: dict):
    """
    features: cleaned dict of numeric features
    user_profile: dict from MongoDB user_profiles collection
    """

    # 1. Scale numeric features for ML models
    scaled = scale_features(features)

    # 2. Supervised fraud probability
    fraud_prob_raw = supervised_model.predict_proba(scaled)[0][1] * 100
    fraud_prob = _to_float(fraud_prob_raw)

    # 3. Anomaly score
    anomaly_raw = anomaly_model.decision_function(scaled)[0]
    anomaly_score = _to_float(abs(anomaly_raw) * 100)

    # 4. Behavior deviation (amount only for now)
    avg = float(user_profile["amount_stats"]["avg"])
    std = float(user_profile["amount_stats"]["std"])
    deviation_score = _to_float(compute_deviation(features["amount"], avg, std))

    # 5. Trust score from user profile
    trust_score = _to_float(user_profile.get("trust_score", 100.0))

    # 6. Final risk fusion
    final_score = compute_final_risk(fraud_prob, anomaly_score, deviation_score, trust_score)

    return {
        "fraud_probability": float(round(fraud_prob, 2)),
        "anomaly_score": float(round(anomaly_score, 2)),
        "deviation_score": float(round(deviation_score, 2)),
        "trust_score": float(round(trust_score, 2)),
        "final_risk_score": final_score,
        "risk_level": get_risk_level(final_score),
    }
