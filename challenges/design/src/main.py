import os
import time
import secrets
import hashlib
import logging
from fastapi import FastAPI, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
import redis
from sqlalchemy.orm import Session

from src.database import init_db, get_db, APIKeyRecord
from src.crypto import encrypt_key_data, decrypt_key_data

# Logging configuration setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("api_key_service")

app = FastAPI(title="Rate-Limited API Key Issuance Infrastructure Service")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Metrics Tracking state elements (Stretch Objective implementation)
metrics_store = {"keys_issued_total": 0, "rate_limit_blocks_total": 0}

@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database schemas fully synced. Distributed infrastructure online.")

class KeyGenerationRequest(BaseModel):
    owner_email: EmailStr

@app.post("/keys", status_code=status.HTTP_201_CREATED)
def issue_api_key(payload: KeyGenerationRequest, db: Session = Depends(get_db)):
    email = payload.owner_email.lower().strip()
    current_time = time.time()
    window_start = current_time - 3600  # 1 rolling hour window bound definition
    
    redis_key = f"rl:issuance:{email}"

    # Sliding Window Limiter implementation utilizing Multi/Exec Transaction Pipelines
    pipeline = redis_client.pipeline()
    pipeline.zremrangebyscore(redis_key, "-inf", window_start) # Evict stale logs
    pipeline.zcard(redis_key)                                   # Compute active elements count
    _, active_request_count = pipeline.execute()

    if active_request_count >= 3:
        metrics_store["rate_limit_blocks_total"] += 1
        logger.warning(f"Rate limit hit for email identifier: {email}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 3 tokens can be generated within a rolling hour."
        )

    # Logging current invocation item back into the Sorted Set tracking array
    pipeline.zadd(redis_key, {f"{current_time}:{secrets.token_hex(4)}": current_time})
    pipeline.expire(redis_key, 3600)
    pipeline.execute()

    # Core generation execution sequence routines
    raw_api_key = f"sk_live_{secrets.token_urlsafe(32)}"
    blind_index_id = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
    
    ciphertext, nonce = encrypt_key_data(raw_api_key)

    new_record = APIKeyRecord(
        id=blind_index_id,
        owner_email=email,
        encrypted_payload=ciphertext,
        nonce=nonce
    )
    db.add(new_record)
    db.commit()

    metrics_store["keys_issued_total"] += 1
    logger.info(f"Successfully minted new security credential signature vector for user: {email}")
    return {"api_key": raw_api_key}

@app.get("/keys", status_code=status.HTTP_200_OK)
def get_owner_keys(owner_email: EmailStr, db: Session = Depends(get_db)):
    email = owner_email.lower().strip()
    records = db.query(APIKeyRecord).filter(APIKeyRecord.owner_email == email).order_by(APIKeyRecord.created_at.desc()).all()
    
    response_list = []
    for r in records:
        # Decrypt payload variables transparently upon request verification pipelines
        plaintext_key = decrypt_key_data(r.encrypted_payload, r.nonce)
        response_list.append({
            "api_key": plaintext_key,
            "created_at": r.created_at.isoformat()
        })
        
    return response_list

@app.get("/metrics", status_code=status.HTTP_200_OK)
def get_telemetry():
    return metrics_store
