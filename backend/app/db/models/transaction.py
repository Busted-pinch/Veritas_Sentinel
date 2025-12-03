# backend/app/db/models/transaction.py

from pydantic import BaseModel, Field
from typing import Optional

class Location(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class Device(BaseModel):
    device_type: Optional[str] = None
    os: Optional[str] = None


class TransactionCreate(BaseModel):
    amount: float
    channel: str
    currency: str = "INR"
    merchant_type: Optional[str] = None
    location: Optional[Location] = None
    device: Optional[Device] = None
    timestamp: Optional[str] = None  # ISO string from frontend (optional)
    # 🔹 NEW: deposit / withdraw
    txn_type: Optional[str] = Field(
        default="WITHDRAW",
        description="DEPOSIT or WITHDRAW (for balance calc only)",
    )


class TransactionInDB(TransactionCreate):
    txn_id: str
    user_id: str
    ml_scores: dict
