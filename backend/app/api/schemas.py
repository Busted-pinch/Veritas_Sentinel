# backend/app/api/schemas.py
from pydantic import BaseModel

class FeatureInput(BaseModel):
    step: float
    amount: float
    isFlaggedFraud: int


class PredictRequest(BaseModel):
    user_id: str
    features: FeatureInput
