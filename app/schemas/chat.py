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
    difficulty: str = "medium"   # "easy", "medium", "hard"


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: str
    topic: str


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]



class QuizAnswerSubmit(BaseModel):
    question: str
    topic: str
    selected_answer: str
    correct_answer: str


class QuizSubmitRequest(BaseModel):
    document_id: int
    difficulty: str
    answers: list[QuizAnswerSubmit]


class TopicScore(BaseModel):
    correct: int
    total: int


class QuizSubmitResponse(BaseModel):
    total_questions: int
    correct_answers: int
    score_percentage: float
    topic_breakdown: dict[str, TopicScore]


class DocumentProgress(BaseModel):
    document_id: int
    document_name: str
    attempts: int
    best_score: float
    latest_score: float


class TopicWeakness(BaseModel):
    topic: str
    correct: int
    total: int
    accuracy: float


class ProgressResponse(BaseModel):
    total_documents: int
    total_attempts: int
    overall_average_score: float
    documents: list[DocumentProgress]
    weak_topics: list[TopicWeakness]