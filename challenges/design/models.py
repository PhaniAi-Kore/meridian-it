from sqlalchemy import Column, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class APIKeyRecord(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, index=True)
    encrypted_metadata = Column(Text, nullable=False)  # Stores AES-GCM cipher text
    nonce = Column(String, nullable=False)             # Unique IV/Nonce per record
