# backend/app/api/schemas.py
from pydantic import BaseModel
from typing import Dict

class PredictRequest(BaseModel):
    user_id: str
    features: Dict[str, float]
