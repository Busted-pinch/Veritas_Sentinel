# backend/app/services/profile_service.py
from typing import Dict
from statistics import mean, pstdev
from datetime import datetime

from backend.app.db.mongo import profiles_col
from backend.app.db.models.profile import UserProfile, AmountStats, RiskStats


def get_or_create_profile(user_id: str) -> Dict:
    profile = profiles_col.find_one({"user_id": user_id})
    if profile:
        return profile

    # create default profile
    amount_stats = AmountStats(
        avg=0.0, std=0.0, min=0.0, max=0.0, last_n=[]
    )
    risk_stats = RiskStats(
        avg_risk_score=0.0,
        max_risk_score=0.0,
        high_risk_txn_count=0,
        total_txn_count=0
    )
    user_profile = UserProfile(
        user_id=user_id,
        amount_stats=amount_stats,
        risk_stats=risk_stats,
        trust_score=100.0
    )

    profiles_col.insert_one(user_profile.dict())
    return profiles_col.find_one({"user_id": user_id})


def _recompute_amount_stats(amount_stats: Dict, new_amount: float) -> Dict:
    last_n = amount_stats.get("last_n") or []
    last_n.append(new_amount)
    # keep only last 50 amounts
    last_n = last_n[-50:]

    avg_val = mean(last_n)
    std_val = pstdev(last_n) if len(last_n) > 1 else 0.0
    min_val = min(last_n)
    max_val = max(last_n)

    return {
        "avg": avg_val,
        "std": std_val,
        "min": min_val,
        "max": max_val,
        "last_n": last_n
    }


def _recompute_risk_stats(risk_stats: Dict, new_risk: float) -> Dict:
    total_txn = risk_stats.get("total_txn_count", 0) + 1
    prev_avg = risk_stats.get("avg_risk_score", 0.0)
    # incremental average
    new_avg = ((prev_avg * (total_txn - 1)) + new_risk) / total_txn

    max_risk = max(risk_stats.get("max_risk_score", 0.0), new_risk)
    high_risk_count = risk_stats.get("high_risk_txn_count", 0)
    if new_risk >= 70:  # threshold for "high"
        high_risk_count += 1

    return {
        "avg_risk_score": new_avg,
        "max_risk_score": max_risk,
        "high_risk_txn_count": high_risk_count,
        "total_txn_count": total_txn
    }


def _compute_trust_score(risk_stats: Dict) -> float:
    avg_risk = risk_stats.get("avg_risk_score", 0.0)
    high_risk_txn_count = risk_stats.get("high_risk_txn_count", 0)
    total_txn_count = risk_stats.get("total_txn_count", 1)

    high_risk_ratio = high_risk_txn_count / total_txn_count

    # simple heuristic: more avg risk + more high-risk ratio => lower trust
    score = 100
    score -= avg_risk * 0.3
    score -= high_risk_ratio * 100 * 0.4  # convert ratio to 0–100 scale

    # clamp between 0 and 100
    score = max(0, min(100, score))
    return score


def update_profile_with_transaction(user_id: str, amount: float, final_risk_score: float):
    profile = get_or_create_profile(user_id)

    amount_stats = _recompute_amount_stats(profile["amount_stats"], amount)
    risk_stats = _recompute_risk_stats(profile["risk_stats"], final_risk_score)
    trust_score = _compute_trust_score(risk_stats)

    profiles_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "amount_stats": amount_stats,
                "risk_stats": risk_stats,
                "trust_score": trust_score,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )

    # return refreshed profile
    return profiles_col.find_one({"user_id": user_id})
