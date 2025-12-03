# backend/app/services/feature_builder.py

from backend.app.db.models.transaction import TransactionCreate


def build_features_from_transaction(txn: TransactionCreate) -> dict:
    """
    Build ML feature dict from a TransactionCreate instance.
    Must match FEATURE_COLUMNS in ml/engine.py / predictor.py:
        ['step', 'amount', 'isFlaggedFraud']

    'isFlaggedFraud' will be filled later from the rules engine.
    """

    # TODO: later you can make 'step' = time since user's first txn etc.
    step = 1

    features = {
        "step": step,
        "amount": txn.amount,
        "isFlaggedFraud": 0,  # will be updated based on rules
    }

    return features
