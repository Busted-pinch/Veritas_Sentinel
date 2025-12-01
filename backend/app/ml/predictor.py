# backend/app/ml/predictor.py

from typing import Dict
from math import exp

"""
Heuristic risk engine for Veritas Sentinel.

Inputs:
- features: {
    "step": float,
    "amount": float,
    "isFlaggedFraud": int (0/1 from rules)
  }
- profile: Mongo user profile document:
    {
      "amount_stats": {
        "avg": float,
        "std": float,
        "min": float,
        "max": float,
        "last_n": [ ... ]
      },
      "risk_stats": {
        "avg_risk_score": float,
        "max_risk_score": float,
        "high_risk_txn_count": int,
        "total_txn_count": int
      },
      "trust_score": float,
      ...
    }

Output:
- dict with keys:
    fraud_probability: 0–100
    anomaly_score: 0–100
    deviation_score: 0–100
    trust_score: 0–100 (from profile)
    final_risk_score: 0–100
    risk_level: "low" | "medium" | "high" | "critical"
"""


def _safe_get(d: Dict, path, default=0.0):
    cur = d
    try:
        for key in path:
            cur = cur[key]
        return float(cur)
    except Exception:
        return float(default)


def _sigmoid(x: float) -> float:
    """Standard sigmoid, mapped to 0–1."""
    try:
        return 1 / (1 + exp(-x))
    except OverflowError:
        return 1.0 if x > 0 else 0.0


def predict_transaction(features: Dict, profile: Dict) -> Dict:
    amount = float(features.get("amount", 0.0))
    is_flagged = int(features.get("isFlaggedFraud", 0))

    # ---- PROFILE STATS ----
    avg_amt = _safe_get(profile, ["amount_stats", "avg"], 0.0)
    std_amt = _safe_get(profile, ["amount_stats", "std"], 0.0)
    trust_score = float(profile.get("trust_score", 100.0))

    # basic z-score-like deviation for amount
    if std_amt > 0:
        z = (amount - avg_amt) / max(std_amt, 1e-6)
    elif avg_amt > 0:
        # fallback: relative deviation vs avg
        z = (amount - avg_amt) / max(avg_amt, 1e-6)
    else:
        z = 0.0

    # clip z to a sensible range for scoring
    z_clamped = max(-5.0, min(5.0, z))

    # ---- COMPONENT 1: deviation_score (0–100) ----
    # |z| of 0 -> 0, |z| of 3+ -> ~100
    deviation_score = min(abs(z_clamped) / 3.0 * 100.0, 100.0)

    # ---- COMPONENT 2: anomaly_score (0–100) ----
    # Similar to deviation, but a bit softer
    anomaly_score = min(abs(z_clamped) / 4.0 * 100.0, 100.0)

    # ---- COMPONENT 3: base fraud probability (0–100) ----
    # Factors:
    # - Higher amount => more risk (non-linearly)
    # - Higher deviation => more risk
    # - Rule flag => strong boost
    # - Lower trust_score => more risk
    # This is a heuristic, but deterministic and monotonic.

    # amount-based component: saturate around ~1,00,000+
    amount_factor = min(amount / 100_000.0, 5.0)  # 0 to 5
    amount_component = _sigmoid(amount_factor - 1.5) * 60.0  # up to ~60

    # deviation / anomaly factor (already 0–100)
    deviation_component = deviation_score * 0.4  # up to 40

    # rule flag: strong signal
    rule_component = 0.0
    if is_flagged:
        rule_component = 25.0  # strong bump if rules triggered

    # trust_score effect: lower trust => higher risk
    trust_component = (100.0 - trust_score) * 0.3  # up to 30

    # raw fraud probability
    fraud_probability = amount_component + deviation_component + rule_component + trust_component
    fraud_probability = max(0.0, min(fraud_probability, 100.0))

    # HARD OVERRIDES for extreme scenarios:
    # - If rules flagged & amount extremely high, push probability up
    if is_flagged and amount >= 500_000:
        fraud_probability = max(fraud_probability, 90.0)
    if is_flagged and amount >= 1_000_000:
        fraud_probability = max(fraud_probability, 95.0)

    # ---- FINAL RISK SCORE ----
    # Combine fraud_probability, anomaly, deviation.
    final_risk_score = (
        fraud_probability * 0.6 +
        anomaly_score * 0.2 +
        deviation_score * 0.2
    )

    # Ensure consistency: final_risk_score should never be far BELOW fraud_probability
    final_risk_score = max(final_risk_score, fraud_probability * 0.8)
    final_risk_score = min(final_risk_score, 100.0)

    # ---- RISK LEVEL MAPPING ----
    # Primary driver: final_risk_score
    if final_risk_score >= 85:
        risk_level = "critical"
    elif final_risk_score >= 65:
        risk_level = "high"
    elif final_risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Additional override: if fraud_probability is extremely high, force high/critical
    if fraud_probability >= 95 and risk_level != "critical":
        risk_level = "critical"
        final_risk_score = max(final_risk_score, 90.0)
    elif fraud_probability >= 85 and risk_level == "medium":
        risk_level = "high"
        final_risk_score = max(final_risk_score, 75.0)

    # Clamp scores
    anomaly_score = max(0.0, min(anomaly_score, 100.0))
    deviation_score = max(0.0, min(deviation_score, 100.0))
    trust_score = max(0.0, min(trust_score, 100.0))

    return {
        "fraud_probability": round(fraud_probability, 2),
        "anomaly_score": round(anomaly_score, 2),
        "deviation_score": round(deviation_score, 2),
        "trust_score": round(trust_score, 2),
        "final_risk_score": round(final_risk_score, 2),
        "risk_level": risk_level,
    }
