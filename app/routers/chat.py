from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.documents import Document
from app.models.chat_message import ChatMessage
from app.models.quiz_attempt import QuizAttempt
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    SummaryRequest, SummaryResponse,
    QuizRequest, QuizResponse,
    ChatHistoryResponse,
    QuizSubmitRequest, QuizSubmitResponse, TopicScore,
    ChatRequest, ChatResponse,
    SummaryRequest, SummaryResponse,
    QuizRequest, QuizResponse,
    ChatHistoryResponse,
    QuizSubmitRequest, QuizSubmitResponse, TopicScore,
    DocumentProgress, TopicWeakness, ProgressResponse,
)
from app.auth.dependencies import get_current_user
from app.services.embedding import get_embeddings
from app.services.faiss import search_faiss, get_all_chunks
from app.services.llm import ask_llm, generate_summary, generate_quiz

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == request.document_id).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document",
        )

    query_embedding = get_embeddings([request.query])[0]

    relevant_chunks = search_faiss(
        document_id=request.document_id,
        query_embedding=query_embedding,
        top_k=3,
    )

    if not relevant_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexed content found for this document",
        )

    # --- LLM ko bhejo (error handling ke saath) ---
    try:
        answer = ask_llm(request.query, relevant_chunks)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    user_msg = ChatMessage(
        document_id=request.document_id,
        user_id=current_user.id,
        role="user",
        message=request.query,
    )
    db.add(user_msg)

    assistant_msg = ChatMessage(
        document_id=request.document_id,
        user_id=current_user.id,
        role="assistant",
        message=answer,
    )
    db.add(assistant_msg)

    db.commit()

    return ChatResponse(answer=answer, sources=relevant_chunks)


@router.get("/history/{document_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document",
        )

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.document_id == document_id,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return ChatHistoryResponse(messages=messages)


@router.post("/summary", response_model=SummaryResponse)
def get_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == request.document_id).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document",
        )

    chunks = get_all_chunks(request.document_id)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexed content found for this document",
        )

    # --- LLM ko bhejo (error handling ke saath) ---
    try:
        summary = generate_summary(chunks)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return SummaryResponse(summary=summary)


@router.post("/quiz", response_model=QuizResponse)
def get_quiz(
    request: QuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == request.document_id).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document",
        )

    chunks = get_all_chunks(request.document_id)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexed content found for this document",
        )

    try:
        quiz_data = generate_quiz(
            chunks,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    return QuizResponse(questions=quiz_data)


@router.post("/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == request.document_id).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document",
        )

    topic_breakdown = {}
    correct_count = 0

    for ans in request.answers:
        topic = ans.topic
        if topic not in topic_breakdown:
            topic_breakdown[topic] = {"correct": 0, "total": 0}

        topic_breakdown[topic]["total"] += 1

        is_correct = ans.selected_answer.strip() == ans.correct_answer.strip()
        if is_correct:
            topic_breakdown[topic]["correct"] += 1
            correct_count += 1

    total_questions = len(request.answers)
    score_percentage = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0

    attempt = QuizAttempt(
        document_id=request.document_id,
        user_id=current_user.id,
        difficulty=request.difficulty,
        total_questions=total_questions,
        correct_answers=correct_count,
        topic_breakdown=topic_breakdown,
    )
    db.add(attempt)
    db.commit()

    return QuizSubmitResponse(
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=score_percentage,
        topic_breakdown={k: TopicScore(**v) for k, v in topic_breakdown.items()},
    )

@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --- Saare documents count karo ---
    total_documents = db.query(Document).filter(Document.user_id == current_user.id).count()

    # --- Saare quiz attempts nikaalo ---
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.created_at.asc())
        .all()
    )

    total_attempts = len(attempts)

    if total_attempts == 0:
        return ProgressResponse(
            total_documents=total_documents,
            total_attempts=0,
            overall_average_score=0,
            documents=[],
            weak_topics=[],
        )

    # --- Overall average score ---
    all_scores = [
        (a.correct_answers / a.total_questions) * 100
        for a in attempts if a.total_questions > 0
    ]
    overall_average = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0

    # --- Per-document breakdown ---
    doc_stats = {}
    for a in attempts:
        if a.document_id not in doc_stats:
            doc_stats[a.document_id] = []
        score = (a.correct_answers / a.total_questions) * 100 if a.total_questions > 0 else 0
        doc_stats[a.document_id].append(score)

    documents_progress = []
    for doc_id, scores in doc_stats.items():
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            documents_progress.append(DocumentProgress(
                document_id=doc_id,
                document_name=document.original_filename,
                attempts=len(scores),
                best_score=round(max(scores), 1),
                latest_score=round(scores[-1], 1),
            ))

    # --- Weak topics (saare attempts ke topic_breakdown ko combine karo) ---
    topic_totals = {}
    for a in attempts:
        for topic, stats in a.topic_breakdown.items():
            if topic not in topic_totals:
                topic_totals[topic] = {"correct": 0, "total": 0}
            topic_totals[topic]["correct"] += stats["correct"]
            topic_totals[topic]["total"] += stats["total"]

    weak_topics = [
        TopicWeakness(
            topic=topic,
            correct=stats["correct"],
            total=stats["total"],
            accuracy=round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0,
        )
        for topic, stats in topic_totals.items()
    ]
    # Sabse kam accuracy wale topics pehle dikhao
    weak_topics.sort(key=lambda t: t.accuracy)
    weak_topics = weak_topics[:5]   # top 5 weak topics

    return ProgressResponse(
        total_documents=total_documents,
        total_attempts=total_attempts,
        overall_average_score=overall_average,
        documents=documents_progress,
        weak_topics=weak_topics,
    )