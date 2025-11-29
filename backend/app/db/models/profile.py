# backend/app/db/models/profile.py
from pydantic import BaseModel
from typing import List, Optional

class AmountStats(BaseModel):
    avg: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0
    last_n: Optional[List[float]] = None  # recent amounts

class RiskStats(BaseModel):
    avg_risk_score: float = 0.0
    max_risk_score: float = 0.0
    high_risk_txn_count: int = 0
    total_txn_count: int = 0

class UserProfile(BaseModel):
    user_id: str
    amount_stats: AmountStats
    risk_stats: RiskStats
    trust_score: float = 100.0
