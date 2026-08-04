from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.documents import Document
from app.models.chat_message import ChatMessage
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    SummaryRequest, SummaryResponse,
    QuizRequest, QuizResponse,
    ChatHistoryResponse,
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
    # --- Document exist karta hai aur is user ka hai, verify karo ---
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

    # --- Query embed karo ---
    query_embedding = get_embeddings([request.query])[0]

    # --- FAISS se relevant chunks dhoondo ---
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

    # --- LLM ko bhejo ---
    answer = ask_llm(request.query, relevant_chunks)

    # --- User ka message save karo ---
    user_msg = ChatMessage(
        document_id=request.document_id,
        user_id=current_user.id,
        role="user",
        message=request.query,
    )
    db.add(user_msg)

    # --- AI ka jawab save karo ---
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

    summary = generate_summary(chunks)
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
        quiz_data = generate_quiz(chunks, num_questions=request.num_questions)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    return QuizResponse(questions=quiz_data)