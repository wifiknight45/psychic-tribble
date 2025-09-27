from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from src.psychic_tribble.core.models import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    google_refresh_token = Column(Text, nullable=True)

    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
