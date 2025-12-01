from fastapi import APIRouter, HTTPException
from backend.app.api.schemas import PredictRequest
from backend.app.ml.predictor import predict_transaction
from backend.app.services.profile_service import get_or_create_profile

router = APIRouter()

@router.post("/predict")
def predict_ml(request: PredictRequest):

    profile = get_or_create_profile(request.user_id)

    features = {
        "step": request.features.step,
        "amount": request.features.amount,
        "isFlaggedFraud": request.features.isFlaggedFraud
    }

    result = predict_transaction(features, profile)
    return result
