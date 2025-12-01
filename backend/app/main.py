# backend/app/main.py

from fastapi import FastAPI

from backend.app.db.mongo import db

# Auth
from backend.app.api.auth import router as auth_router

# Core ML
from backend.app.api.predict import router as predict_router

# User transactions
from backend.app.api.transactions import router as txn_router

# Admin / analyst agents
from backend.app.api.agent import router as speculate_router
from backend.app.api.agent_behavior import router as behavior_router
from backend.app.api.agent_investigation import router as investigation_router
from backend.app.api.agent_risk_trend import router as trend_router


app = FastAPI(title="Veritas Sentinel API")


# ---- Public Auth Routes ----
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# ---- Core ML ----
app.include_router(predict_router, prefix="/ml", tags=["ml"])

# ---- User Transactions (protected via get_current_user inside router) ----
app.include_router(txn_router, prefix="/api", tags=["transactions"])

# ---- Admin / Analyst Agents ----
app.include_router(speculate_router, prefix="/api/agent", tags=["agent"])
app.include_router(behavior_router, prefix="/api/agent", tags=["agent"])
app.include_router(investigation_router, prefix="/api/agent", tags=["agent"])
app.include_router(trend_router, prefix="/api/agent", tags=["agent"])


@app.get("/")
def root():
    """
    Simple root endpoint to list Mongo collections.
    """
    return {"collections": db.list_collection_names()}
