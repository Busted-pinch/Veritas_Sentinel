# backend/app/main.py
from fastapi import FastAPI

from backend.app.db.mongo import db
from backend.app.api.predict import router as predict_router
from backend.app.api.transactions import router as txn_router
from backend.app.api.agent import router as agent_router
from backend.app.api.agent_behavior import router as behavior_router
from backend.app.api.agent_investigation import router as investigation_router
from backend.app.api.agent_risk_trend import router as trend_router

app = FastAPI(title="Veritas Sentinel API")

app.include_router(behavior_router, prefix="/api/agent")
app.include_router(investigation_router, prefix="/api/agent")
app.include_router(predict_router, prefix="/ml")
app.include_router(txn_router, prefix="/api")
app.include_router(agent_router, prefix="/api/agent")
app.include_router(trend_router, prefix="/api/agent")



@app.get("/")
def root():
    # quick sanity check: list collections
    return {"collections": db.list_collection_names()}
