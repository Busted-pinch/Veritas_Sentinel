# backend/app/services/rules_service.py

from datetime import datetime
from typing import List, Dict, Any

from backend.app.db.models.transaction import TransactionCreate


def _parse_timestamp(ts_str: str | None) -> datetime:
    if not ts_str:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.utcnow()


def basic_flag_rules(txn: TransactionCreate) -> int:
    """
    Simple rule-based pre-flagging.
    Returns 1 if any rule flags the transaction as suspicious, else 0.
    """

    amount = txn.amount
    channel = (txn.channel or "").upper()
    merchant_type = (txn.merchant_type or "").lower()
    country = (txn.location.country if txn.location else None) or ""
    country = country.strip()

    ts = _parse_timestamp(txn.timestamp)
    hour = ts.hour

    # Rule 0: Extreme amount
    if amount >= 500_000:
        return 1

    # Rule 1: Very high amount
    if amount >= 50_000:
        return 1

    # Rule 2: Night + moderately high amount
    if 0 <= hour <= 5 and amount >= 20_000:
        return 1

    # Rule 3: Risky merchants + amount
    risky_merchants = [
        "crypto",
        "betting",
        "gambling",
        "casino",
        "binary options",
        "adult",
    ]
    if any(rm in merchant_type for rm in risky_merchants) and amount >= 10_000:
        return 1

    # Rule 4: Non-UPI + high amount
    if channel != "UPI" and amount >= 30_000:
        return 1

    # Rule 5: Cross-border (not India) + meaningful amount
    if country and country.lower() != "india" and amount >= 20_000:
        return 1

    return 0


def evaluate_rules_for_transaction(
    txn: TransactionCreate, profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Richer rules engine wrapper.

    Input:
        - txn: TransactionCreate
        - profile: user profile dict from Mongo
    Output:
        {
          "isFlaggedFraud": 0/1,
          "matched_rules": [ "R0_EXTREME_AMOUNT", ... ],
        }
    """
    matched: List[str] = []

    amount = txn.amount
    channel = (txn.channel or "").upper()
    merchant_type = (txn.merchant_type or "").lower()
    country = (txn.location.country if txn.location else None) or ""
    country = country.strip()

    ts = _parse_timestamp(txn.timestamp)
    hour = ts.hour

    # ---- SAME RULE SET, BUT COLLECT IDs ----
    if amount >= 500_000:
        matched.append("R0_EXTREME_AMOUNT")

    if amount >= 50_000:
        matched.append("R1_VERY_HIGH_AMOUNT")

    if 0 <= hour <= 5 and amount >= 20_000:
        matched.append("R2_NIGHT_HIGH_AMOUNT")

    risky_merchants = [
        "crypto",
        "betting",
        "gambling",
        "casino",
        "binary options",
        "adult",
    ]
    if any(rm in merchant_type for rm in risky_merchants) and amount >= 10_000:
        matched.append("R3_RISKY_MERCHANT")

    if channel != "UPI" and amount >= 30_000:
        matched.append("R4_NON_UPI_HIGH_AMOUNT")

    if country and country.lower() != "india" and amount >= 20_000:
        matched.append("R5_CROSS_BORDER")

    # Profile-aware rule: amount way above this user's norm
    avg_amt = (profile.get("amount_stats") or {}).get("avg", 0.0)
    try:
        avg_amt = float(avg_amt)
    except Exception:
        avg_amt = 0.0

    if avg_amt > 0 and amount > avg_amt * 5:
        matched.append("R6_5X_ABOVE_AVG_PROFILE_AMOUNT")

    is_flagged = 1 if matched else 0

    return {
        "isFlaggedFraud": is_flagged,
        "matched_rules": matched,
    }
