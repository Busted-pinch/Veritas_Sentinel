# backend/app/main.py

from fastapi import FastAPI
from backend.app.db.mongo import db
from fastapi.middleware.cors import CORSMiddleware

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
from backend.app.api.admin_users import router as admin_users_router  # All Users
from backend.app.api.agent_intel import router as intel_router  # User Intel
from backend.app.api.admin_analytics import router as admin_analytics_router # Global Visuals
from backend.app.api.alerts import router as alerts_router


app = FastAPI(title="Veritas Sentinel API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Public Auth Routes ----
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# ---- Core ML ----
app.include_router(predict_router, prefix="/ml", tags=["ml"])

# ---- User Transactions (protected via get_current_user inside router) ----
app.include_router(txn_router, prefix="/api", tags=["transactions"])

# ---- Admin / Analyst Agents ----
app.include_router(intel_router, prefix="/api/agent", tags=["agent"])
app.include_router(behavior_router, prefix="/api/agent", tags=["agent"])
app.include_router(speculate_router, prefix="/api/agent", tags=["agent"])
app.include_router(investigation_router, prefix="/api/agent", tags=["agent"])
app.include_router(admin_users_router, prefix="/api/admin", tags=["admin"])
app.include_router(trend_router, prefix="/api/agent", tags=["agent"])
app.include_router(admin_analytics_router, prefix="/api/admin", tags=["admin-analytics"])
app.include_router(alerts_router, prefix="/api/admin", tags=["alerts"])


@app.get("/")
def root():
    return {"collections": db.list_collection_names()}
@app.get("/health")
def health():
    return {"status": "ok"}

