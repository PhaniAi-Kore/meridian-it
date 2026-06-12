import os
import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/key_issuance")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class APIKeyRecord(Base):
    __tablename__ = "issued_api_keys"

    id = Column(String, primary_key=True, index=True) # Hashed Key Value representation (Blind Index)
    owner_email = Column(String, index=True, nullable=False)
    encrypted_payload = Column(Text, nullable=False) # Store actual ciphertext
    nonce = Column(String, nullable=False)            # Unique salt/nonce tracking
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
