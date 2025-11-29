# backend/app/services/rules_service.py
from datetime import datetime
from backend.app.db.models.transaction import TransactionCreate

def basic_flag_rules(txn: TransactionCreate) -> int:
    """
    Simple rule-based pre-flagging.
    Returns 1 if any rule flags the transaction as suspicious, else 0.
    """

    amount = txn.amount
    channel = txn.channel.upper()
    merchant_type = (txn.merchant_type or "").lower()

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

    # Rule 1: Very high amount
    if amount >= 50000:  # adjust threshold as you like
        return 1

    # Rule 2: Odd hours + moderately high amount
    if hour >= 0 and hour <= 5 and amount >= 20000:
        return 1

    # Rule 3: Certain merchant types + amount
    risky_merchants = ["crypto", "betting", "gambling"]
    if any(rm in merchant_type for rm in risky_merchants) and amount >= 10000:
        return 1

    # Rule 4: Non-UPI channel + high amount
    if channel != "UPI" and amount >= 30000:
        return 1

    # If no rules triggered
    return 0
