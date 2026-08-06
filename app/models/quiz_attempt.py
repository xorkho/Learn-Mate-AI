from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    difficulty = Column(String, nullable=False)      # easy / medium / hard
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)

    # Topic-wise breakdown, JSON format mein store hoga:
    # {"Python Basics": {"correct": 3, "total": 4}, "Loops": {"correct": 1, "total": 2}}
    topic_breakdown = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())