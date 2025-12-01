# backend/app/services/rules_service.py

from datetime import datetime
from typing import Tuple, List

from backend.app.db.models.transaction import TransactionCreate


def basic_flag_rules(txn: TransactionCreate) -> int:
    """
    Simple rule-based pre-flagging.
    Returns 1 if any rule flags the transaction as suspicious, else 0.

    Rules are intentionally conservative:
    if ANY of these trigger, we treat the transaction as "needs attention".
    """

    amount = txn.amount
    channel = (txn.channel or "").upper()
    merchant_type = (txn.merchant_type or "").lower()
    country = (txn.location.country if txn.location else None) or ""
    country = country.strip()

    # Parse timestamp if present, otherwise use now
    if txn.timestamp:
        try:
            ts = datetime.fromisoformat(txn.timestamp)
        except ValueError:
            ts = datetime.utcnow()
    else:
        ts = datetime.utcnow()

    hour = ts.hour

    # --- RULES ---

    # Rule 0: Extreme amount (very likely fraud or requires manual review)
    # e.g. 5,00,000+ INR in a single transaction
    if amount >= 500_000:
        return 1

    # Rule 1: Very high amount
    if amount >= 50_000:
        return 1

    # Rule 2: Odd hours + moderately high amount
    # Night window: 00:00–05:00
    if 0 <= hour <= 5 and amount >= 20_000:
        return 1

    # Rule 3: Certain merchant types + amount
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

    # Rule 4: Non-UPI channel + high amount
    if channel != "UPI" and amount >= 30_000:
        return 1

    # Rule 5: Cross-border transactions (country not India) + meaningful amount
    if country and country.lower() != "india" and amount >= 20_000:
        return 1

    # If no rules triggered
    return 0
