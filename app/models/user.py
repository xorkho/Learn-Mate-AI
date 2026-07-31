from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # user.documents likhne se uske saare documents mil jate hain (list of Document objects)
    # cascade="all, delete-orphan" -> agar user delete ho, uske saare documents bhi khud-b-khud delete ho jayein
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")