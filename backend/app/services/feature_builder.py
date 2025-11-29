# backend/app/services/feature_builder.py
from datetime import datetime
from backend.app.db.models.transaction import TransactionCreate
from backend.app.services.rules_service import basic_flag_rules

def build_features_from_transaction(txn: TransactionCreate) -> dict:
    """
    Build ML feature dict from a TransactionCreate instance.
    Must match FEATURE_COLUMNS in ml/engine.py:
    ['step', 'amount', 'isFlaggedFraud']
    """

    # You can make 'step' more sophisticated later (e.g., minutes since first txn)
    step = 1

    is_flagged = basic_flag_rules(txn)

    features = {
        "step": step,
        "amount": txn.amount,
        "isFlaggedFraud": is_flagged
    }

    return features
