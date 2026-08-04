from sqlalchemy import Column, Integer, String, DateTime, ForeignKey,Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key — batata hai ye document KIS user ka hai
    # index=True isliye kyunki hum baar baar "WHERE user_id = ?" query karenge
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    original_filename = Column(String, nullable=False)   # jo naam user ne upload kiya (e.g. "notes.pdf")
    stored_filename = Column(String, nullable=False, unique=True)  # disk pe actual unique naam
    file_path = Column(String, nullable=False)            # disk pe pura path
    file_size = Column(Integer, nullable=False)            # bytes mein
    extracted_text = Column(Text, nullable=True) 
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationship() — Python side pe convenience deta hai:
    # document.owner likhne se seedha User object mil jayega, alag query ki zarurat nahi
    owner = relationship("User", back_populates="documents")