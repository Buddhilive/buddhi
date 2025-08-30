from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
from datetime import datetime

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_on = Column(DateTime, default=datetime.utcnow)
