import os
import secrets
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Domain Modules Routing Requirements
from challenges.design.models import Base, APIKeyRecord
from challenges.design.services import encrypt_data
from challenges.ui.template import DASHBOARD_HTML
from challenges.algorithm.engine import BatchQueryPayload, process_fast_queries

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/challenge_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MASTER_SECRET = os.getenv("MASTER_SECRET", "default_secret_key_must_be_changed_in_prod_32bytes").encode()

app = FastAPI(title="Multi-Challenge Distributed Architecture Suite")

# Setup Infrastructure
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class IssueKeyRequest(BaseModel):
    user_id: str
    rate_limit_tier: str

# --- CHALLENGE 1: DESIGN ENDPOINT ---
@app.post("/api/v1/challenges/design")
def issue_api_key(payload: IssueKeyRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    rate_limit_key = f"rl:issuance:{client_ip}"
    
    current_requests = redis_client.incr(rate_limit_key)
    if current_requests == 1:
        redis_client.expire(rate_limit_key, 60)
    elif current_requests > 5:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Limit is 5 requests/min.")

    api_key_raw = f"sk_{secrets.token_urlsafe(32)}"
    metadata_json = f'{{"user_id": "{payload.user_id}", "tier": "{payload.rate_limit_tier}"}}'
    
    ciphertext, nonce = encrypt_data(metadata_json, MASTER_SECRET)
    
    db_record = APIKeyRecord(id=api_key_raw, encrypted_metadata=ciphertext, nonce=nonce)
    db.add(db_record)
    db.commit()

    return {"status": "success", "api_key": api_key_raw}

# --- CHALLENGE 2: UI ENDPOINT ---
@app.get("/api/v1/challenges/ui", response_class=HTMLResponse)
def get_ui_dashboard():
    return DASHBOARD_HTML

# --- CHALLENGE 3: ALGORITHM ENDPOINT ---
@app.post("/api/v1/challenges/algorithm")
def execute_algorithmic_batch(payload: BatchQueryPayload):
    return process_fast_queries(payload)
