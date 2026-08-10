"""User account model."""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.time import utcnow_naive


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=utcnow_naive)

    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
