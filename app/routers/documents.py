import os
import uuid
import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.documents import Document
from app.schemas.documents import DocumentOut
from app.auth.dependencies import get_current_user
from app.services.pdf_services import extract_text
from app.services.chunking import chunk_text
from app.services.embedding import get_embeddings
from app.services.faiss import save_to_faiss

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "app/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --- Validation 1: Extension check ---
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and TXT files are allowed",
        )

    # --- Validation 2: Size check ---
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Max size is 10MB",
        )

    # --- Unique filename generate karna (sahi extension ke saath) ---
    unique_name = f"{uuid.uuid4().hex}{file_extension}"
    destination_path = os.path.join(UPLOAD_DIR, unique_name)

    # --- File ko disk pe save karna ---
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # --- Text extract karo (extension ke hisaab se) ---
    try:
        extracted_text = extract_text(destination_path, file_extension)
    except ValueError as e:
        os.remove(destination_path)  # invalid file ko disk se hata do
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # --- DB record banana ---
    new_document = Document(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=unique_name,
        file_path=destination_path,
        file_size=file_size,
        extracted_text=extracted_text,
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    # --- Chunking ---
    chunks = chunk_text(extracted_text)

    # --- Embeddings ---
    embeddings = get_embeddings(chunks)

    # --- FAISS mein save karo ---
    save_to_faiss(new_document.id, chunks, embeddings)

    return new_document


@router.get("", response_model=list[DocumentOut])
def list_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return documents


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
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
            detail="You don't have permission to delete this document",
        )

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()
    return None