from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    document_id: int
    query: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]   # jo chunks use hue jawab dene ke liye


class ChatMessageOut(BaseModel):
    role: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageOut]


class SummaryRequest(BaseModel):
    document_id: int


class SummaryResponse(BaseModel):
    summary: str


class QuizRequest(BaseModel):
    document_id: int
    num_questions: int = 5


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: str


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]