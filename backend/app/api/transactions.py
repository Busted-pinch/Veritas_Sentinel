# backend/app/api/transactions.py

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid

from backend.app.db.mongo import txns_col, alerts_col
from backend.app.db.models.transaction import TransactionCreate
from backend.app.services.profile_service import (
    get_or_create_profile,
    update_profile_with_transaction,
)
from backend.app.services.feature_builder import build_features_from_transaction
from backend.app.ml.predictor import predict_transaction
from backend.app.core.security import get_current_user

router = APIRouter()


@router.post("/transaction/new")
def create_transaction(
    txn: TransactionCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Logged-in USER endpoint:
    - Creates a new transaction for the current user
    - Scores with ML
    - Updates behavior profile
    - Creates alert if high/critical OR flagged by rules
    """

    # Force user_id to be the logged-in user
    user_id = current_user["user_id"]
    txn.user_id = user_id

    ts = txn.timestamp or datetime.utcnow().isoformat()

    # 1. Build ML features (includes rule-based isFlaggedFraud)
    features = build_features_from_transaction(txn)
    is_flagged = features.get("isFlaggedFraud", 0)

    # 2. Fetch or create user profile
    profile = get_or_create_profile(user_id)

    # 3. Run ML risk engine
    try:
        risk_result = predict_transaction(features, profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    final_risk = risk_result["final_risk_score"]
    risk_level = risk_result["risk_level"]

    # 4. Generate transaction id
    txn_id = f"T-{uuid.uuid4().hex[:12]}"

    # 5. Insert transaction doc into Mongo
    txn_doc = {
        "txn_id": txn_id,
        "user_id": user_id,
        "amount": txn.amount,
        "currency": txn.currency,
        "channel": txn.channel,
        "merchant_type": txn.merchant_type,
        "location": txn.location.dict() if txn.location else None,
        "device": txn.device.dict() if txn.device else None,
        "timestamp": ts,  # stored as ISO string
        "ml_scores": risk_result,
        "label": None,
        "status": "normal",
        "created_at": datetime.utcnow().isoformat(),
    }

    txns_col.insert_one(txn_doc)

    # 6. Update user profile with this transaction
    updated_profile = update_profile_with_transaction(
        user_id=user_id,
        amount=txn.amount,
        final_risk_score=final_risk,
    )

    # 7. Create alert if high/critical OR rules flagged it
    alert_id = None
    if risk_level in ["high", "critical"] or is_flagged == 1:
        alert_id = f"A-{uuid.uuid4().hex[:12]}"
        alerts_col.insert_one(
            {
                "alert_id": alert_id,
                "txn_id": txn_id,
                "user_id": user_id,
                "risk_level": risk_level,
                "final_risk_score": final_risk,
                "reason": _build_alert_reason(risk_result, txn, is_flagged),
                "status": "open",
                "created_at": datetime.utcnow().isoformat(),
                "resolved_at": None,
                "resolved_by": None,
                "resolution_note": None,
            }
        )

    return {
        "success": True,
        "txn_id": txn_id,
        "user_id": user_id,
        "ml_scores": risk_result,
        "risk_alert_id": alert_id,
        "risk_level": risk_level,
        "updated_profile": {
            "trust_score": updated_profile["trust_score"],
            "avg_risk_score": updated_profile["risk_stats"]["avg_risk_score"],
            "high_risk_txn_count": updated_profile["risk_stats"][
                "high_risk_txn_count"
            ],
            "total_txn_count": updated_profile["risk_stats"]["total_txn_count"],
        },
    }


def _build_alert_reason(risk_result: dict, txn: TransactionCreate, is_flagged: int):
    """
    Build a human-readable list of reasons why this transaction was alerted.
    Combines ML signals + rule-engine triggers.
    """

    reasons = []

    # --- ML-BASED REASONS ---
    if risk_result.get("fraud_probability", 0) >= 70:
        reasons.append("High fraud probability from supervised model")

    if risk_result.get("anomaly_score", 0) >= 60:
        reasons.append("Unusual transaction pattern detected (anomaly model)")

    if risk_result.get("deviation_score", 0) >= 50:
        reasons.append("Transaction amount deviates strongly from user history")

    if risk_result.get("trust_score", 100) <= 40:
        reasons.append("User has low trust score based on past behaviour")

    # --- RULE-BASED REASONS ---
    if is_flagged:
        # Reconstruct some of the key rule triggers for explanation
        amount = txn.amount
        channel = (txn.channel or "").upper()
        merchant_type = (txn.merchant_type or "").lower()
        country = (txn.location.country if txn.location else None) if txn.location else None

        # Parse timestamp again
        if txn.timestamp:
            try:
                ts = datetime.fromisoformat(txn.timestamp)
            except ValueError:
                ts = datetime.utcnow()
        else:
            ts = datetime.utcnow()

        hour = ts.hour

        if amount >= 500_000:
            reasons.append("Extreme amount (>= 500,000) triggered hard risk rule")

        if amount >= 50_000 and amount < 500_000:
            reasons.append("Very high amount (>= 50,000) triggered risk rule")

        if 0 <= hour <= 5 and amount >= 20_000:
            reasons.append("Night-time high value transaction (00:00–05:00) triggered risk rule")

        risky_merchants = [
            "crypto",
            "betting",
            "gambling",
            "casino",
            "binary options",
            "adult",
        ]
        if any(rm in merchant_type for rm in risky_merchants) and amount >= 10_000:
            reasons.append("Risky merchant type + high amount triggered rule")

        if channel != "UPI" and amount >= 30_000:
            reasons.append("High-value non-UPI transaction triggered rule")

        if country and country.strip().lower() != "india" and amount >= 20_000:
            reasons.append("Cross-border transaction with high amount triggered rule")

        if not reasons:
            reasons.append("Rule engine flagged this transaction as suspicious")

    # Fallback
    if not reasons:
        reasons.append("Combined risk score or rules exceeded alert threshold")

    return reasons
