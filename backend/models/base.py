from sqlalchemy import Column, ForeignKey, Integer, String, Table, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from backend.api.database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    username = Column(String)
    age = Column(Integer)

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_on = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # Hugging Face model name
    local_path = Column(String, nullable=False)  # Local cache path
    status = Column(String, nullable=False, default="downloaded")  # downloaded, failed, deleted
    download_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    size_bytes = Column(Integer, nullable=True)  # Model size in bytes
    model_type = Column(String, nullable=True)  # text-generation, text-classification, etc.
    description = Column(Text, nullable=True)  # Model description from HF
    author = Column(String, nullable=True)  # Model author/organization
    license = Column(String, nullable=True)  # Model license
    language = Column(String, nullable=True)  # Primary language
    tags = Column(Text, nullable=True)  # JSON string of tags
    downloads = Column(Integer, nullable=True)  # Number of downloads on HF
    likes = Column(Integer, nullable=True)  # Number of likes on HF
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
