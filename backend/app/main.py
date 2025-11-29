# backend/app/main.py
from fastapi import FastAPI

from backend.app.db.mongo import db  # just to ensure import works
from backend.app.api.predict import router as predict_router
from backend.app.api.transactions import router as txn_router

app = FastAPI(title="Veritas Sentinel API")

app.include_router(predict_router, prefix="/ml")
app.include_router(txn_router, prefix="/api")



@app.get("/")
def root():
    # quick sanity check: list collections
    return {"collections": db.list_collection_names()}
