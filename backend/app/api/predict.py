from fastapi import APIRouter, HTTPException
from backend.app.db.mongo import profiles_col
from backend.app.ml.predictor import predict_transaction
from backend.app.api.schemas import PredictRequest

router = APIRouter()

@router.post("/predict")
def predict_api(payload: PredictRequest):

    user_id = payload.user_id
    features = payload.features

    # Fetch profile
    profile = profiles_col.find_one({"user_id": user_id})

    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Run ML engine
    result = predict_transaction(features, profile)

    return {
        "success": True,
        "user_id": user_id,
        "result": result
    }
