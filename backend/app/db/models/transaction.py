# backend/app/db/models/transaction.py
from pydantic import BaseModel, Field
from typing import Optional, Dict

class Location(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = "India"
    lat: Optional[float] = None
    lon: Optional[float] = None

class Device(BaseModel):
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os: Optional[str] = None
    ip: Optional[str] = None

class TransactionCreate(BaseModel):
    user_id: str
    amount: float
    currency: str = "INR"
    channel: str  # e.g. "UPI", "CARD", "WALLET"
    merchant_type: Optional[str] = None
    location: Optional[Location] = None
    device: Optional[Device] = None
    timestamp: Optional[str] = None  # ISO string; if None, backend sets it

class TransactionInDB(TransactionCreate):
    txn_id: str
    ml_scores: Dict
    label: Optional[int] = None  # 0/1 if manually labelled later
    status: str = "normal"       # normal / flagged / confirmed_fraud / false_positive
