"""
Seed demo data for Veritas Sentinel.

Creates:
- 1 admin
- 2 users (Alice & Bob)
- 4 transactions each
- Risk evaluation + alerts created via your real pipeline
"""

import uuid
from datetime import datetime
from typing import List

# --- Import your backend internals ---
from backend.app.db.mongo import users_col, txns_col, alerts_col, profiles_col
from backend.app.core.security import get_password_hash  # password hashing :contentReference[oaicite:1]{index=1}
from backend.app.db.models.transaction import TransactionCreate, Location, Device
from backend.app.services.feature_builder import build_features_from_transaction
from backend.app.ml.predictor import predict_transaction
from backend.app.services.profile_service import (
    get_or_create_profile,
    update_profile_with_transaction,
)
from backend.app.api.transactions import _build_alert_reason  # reuse your real alert reason logic :contentReference[oaicite:6]{index=6}


def create_user(name: str, email: str, password: str, role: str, user_code: str) -> str:
    """
    Create a user directly in Mongo if it doesn't already exist.
    Returns the internal Mongo user_id (string).
    """

    existing = users_col.find_one({"email": email})
    if existing:
        print(f"[users] User already exists: {email}")
        return str(existing["_id"])

    password_hash = get_password_hash(password)

    doc = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "user_code": user_code,
        "created_at": datetime.utcnow(),
        "status": "active",
    }

    result = users_col.insert_one(doc)
    user_id = str(result.inserted_id)
    print(f"[users] Created {role} '{name}' ({email}) with user_id={user_id}")
    return user_id


def create_transactions_for_user(user_id: str, user_code: str, who: str):
    """
    Create 4 diverse transactions for a user, running the full scoring pipeline:
    - build_features_from_transaction
    - predict_transaction
    - update_profile_with_transaction
    - create alerts (if applicable)
    """

    print(f"\n[txns] Creating demo transactions for {who} ({user_code})...")

    # A few realistic + diverse samples
    base_now = datetime.utcnow()

    tx_configs: List[dict] = []

    if who.lower() == "alice":
        # 1) Low-risk domestic UPI grocery
        tx_configs.append(
            dict(
                amount=750.0,
                currency="INR",
                channel="UPI",
                merchant_type="groceries",
                location=Location(
                    city="Mumbai",
                    country="India",
                    lat=19.0760,
                    lon=72.8777,
                ),
                device=Device(
                    device_id="alice-phone",
                    device_type="mobile",
                    os="Android",
                    ip="49.32.10.15",
                ),
                timestamp=(base_now.replace(hour=11, minute=15, second=0)).isoformat(),
            )
        )

        # 2) Night-time higher UPI txn to trigger time + amount rule
        tx_configs.append(
            dict(
                amount=25000.0,
                currency="INR",
                channel="UPI",
                merchant_type="electronics",
                location=Location(
                    city="Pune",
                    country="India",
                    lat=18.5204,
                    lon=73.8567,
                ),
                device=Device(
                    device_id="alice-phone",
                    device_type="mobile",
                    os="Android",
                    ip="49.32.10.15",
                ),
                timestamp=(base_now.replace(hour=2, minute=40, second=0)).isoformat(),
            )
        )

        # 3) Very high amount CARD txn (likely high/critical risk)
        tx_configs.append(
            dict(
                amount=525000.0,
                currency="INR",
                channel="CARD",
                merchant_type="luxury_jewellery",
                location=Location(
                    city="Delhi",
                    country="India",
                    lat=28.6139,
                    lon=77.2090,
                ),
                device=Device(
                    device_id="alice-laptop",
                    device_type="laptop",
                    os="Windows",
                    ip="103.21.77.45",
                ),
                timestamp=(base_now.replace(hour=16, minute=5, second=0)).isoformat(),
            )
        )

        # 4) Cross-border gambling-ish txn
        tx_configs.append(
            dict(
                amount=26000.0,
                currency="INR",
                channel="CARD",
                merchant_type="online casino",
                location=Location(
                    city="London",
                    country="UK",
                    lat=51.5074,
                    lon=-0.1278,
                ),
                device=Device(
                    device_id="alice-laptop",
                    device_type="laptop",
                    os="Windows",
                    ip="103.21.77.45",
                ),
                timestamp=(base_now.replace(hour=21, minute=30, second=0)).isoformat(),
            )
        )

    else:  # Bob
        # 1) High-value non-UPI domestic (card)
        tx_configs.append(
            dict(
                amount=35000.0,
                currency="INR",
                channel="CARD",
                merchant_type="electronics",
                location=Location(
                    city="Bengaluru",
                    country="India",
                    lat=12.9716,
                    lon=77.5946,
                ),
                device=Device(
                    device_id="bob-phone",
                    device_type="mobile",
                    os="iOS",
                    ip="125.19.87.101",
                ),
                timestamp=(base_now.replace(hour=10, minute=0, second=0)).isoformat(),
            )
        )

        # 2) Crypto merchant
        tx_configs.append(
            dict(
                amount=15000.0,
                currency="INR",
                channel="CARD",
                merchant_type="crypto exchange",
                location=Location(
                    city="Singapore",
                    country="Singapore",
                    lat=1.3521,
                    lon=103.8198,
                ),
                device=Device(
                    device_id="bob-laptop",
                    device_type="laptop",
                    os="Windows",
                    ip="203.0.113.42",
                ),
                timestamp=(base_now.replace(hour=19, minute=20, second=0)).isoformat(),
            )
        )

        # 3) Normal-ish travel txn
        tx_configs.append(
            dict(
                amount=8000.0,
                currency="INR",
                channel="CARD",
                merchant_type="travel",
                location=Location(
                    city="Goa",
                    country="India",
                    lat=15.2993,
                    lon=74.1240,
                ),
                device=Device(
                    device_id="bob-phone",
                    device_type="mobile",
                    os="iOS",
                    ip="125.19.87.101",
                ),
                timestamp=(base_now.replace(hour=14, minute=45, second=0)).isoformat(),
            )
        )

        # 4) Cross-border high-value travel / shopping
        tx_configs.append(
            dict(
                amount=78000.0,
                currency="INR",
                channel="CARD",
                merchant_type="duty_free_shopping",
                location=Location(
                    city="Dubai",
                    country="UAE",
                    lat=25.2048,
                    lon=55.2708,
                ),
                device=Device(
                    device_id="bob-laptop",
                    device_type="laptop",
                    os="Windows",
                    ip="203.0.113.42",
                ),
                timestamp=(base_now.replace(hour=23, minute=10, second=0)).isoformat(),
            )
        )

    # Ensure profile exists first
    get_or_create_profile(user_id)

    # Run full pipeline for each config
    for i, cfg in enumerate(tx_configs, start=1):
        txn = TransactionCreate(
            user_id=user_id,
            amount=cfg["amount"],
            currency=cfg["currency"],
            channel=cfg["channel"],
            merchant_type=cfg["merchant_type"],
            location=cfg["location"],
            device=cfg["device"],
            timestamp=cfg["timestamp"],
        )

        # 1. Features + rule-based flag
        features = build_features_from_transaction(txn)
        is_flagged = features.get("isFlaggedFraud", 0)

        # 2. Fetch current profile
        profile = get_or_create_profile(user_id)

        # 3. Run ML risk engine
        risk_result = predict_transaction(features, profile)
        final_risk = risk_result["final_risk_score"]
        risk_level = risk_result["risk_level"]

        # 4. Generate txn_id & persist
        txn_id = f"T-{uuid.uuid4().hex[:12]}"
        ts = txn.timestamp or datetime.utcnow().isoformat()

        txn_doc = {
            "txn_id": txn_id,
            "user_id": user_id,
            "amount": txn.amount,
            "currency": txn.currency,
            "channel": txn.channel,
            "merchant_type": txn.merchant_type,
            "location": txn.location.dict() if txn.location else None,
            "device": txn.device.dict() if txn.device else None,
            "timestamp": ts,
            "ml_scores": risk_result,
            "label": None,
            "status": "normal",
            "created_at": datetime.utcnow().isoformat(),
        }

        txns_col.insert_one(txn_doc)

        # 5. Update profile with this txn
        updated_profile = update_profile_with_transaction(
            user_id=user_id,
            amount=txn.amount,
            final_risk_score=final_risk,
        )

        # 6. Create alert if high / critical or rules flagged it
        alert_id = None
        if risk_level in ["high", "critical"] or is_flagged == 1:
            alert_id = f"A-{uuid.uuid4().hex[:12]}"
            reasons = _build_alert_reason(risk_result, txn, is_flagged)

            alerts_col.insert_one(
                {
                    "alert_id": alert_id,
                    "txn_id": txn_id,
                    "user_id": user_id,
                    "user_code": user_code,
                    "risk_level": risk_level,
                    "final_risk_score": final_risk,
                    "reason": reasons,
                    "status": "open",
                    "created_at": datetime.utcnow().isoformat(),
                    "resolved_at": None,
                    "resolved_by": None,
                    "resolution_note": None,
                }
            )

        print(
            f"  [{who}] txn#{i}: amount={txn.amount}, "
            f"risk_level={risk_level}, alert_id={alert_id}"
        )

    # Quick summary
    profile = profiles_col.find_one({"user_id": user_id})
    if profile:
        print(
            f"[profile] {who} trust_score={profile.get('trust_score'):.2f}, "
            f"avg_risk={profile['risk_stats']['avg_risk_score']:.2f}, "
            f"total_txn_count={profile['risk_stats']['total_txn_count']}"
        )


def main():
    print("=== Seeding Veritas Sentinel demo data ===")

    # 1) Admin
    admin_id = create_user(
        name="System Admin",
        email="admin@gmail.com",
        password="Admin@123",
        role="admin",
        user_code="ADMIN-0001",
    )

    # 2) Alice (user)
    alice_id = create_user(
        name="Alice",
        email="alice@gmail.com",
        password="Alice@123",
        role="user",
        user_code="ALIC-0001",
    )

    # 3) Bob (user)
    bob_id = create_user(
        name="Bob",
        email="bob@gmail.com",
        password="Bob@123",
        role="user",
        user_code="BOB-0001",
    )

    # 4) Create transactions + alerts + profiles for Alice & Bob
    create_transactions_for_user(alice_id, "ALIC-0001", "Alice")
    create_transactions_for_user(bob_id, "BOB-0001", "Bob")

    print("\n=== Done. Check your Mongo collections: users, transactions, user_profiles, alerts ===")


if __name__ == "__main__":
    main()
