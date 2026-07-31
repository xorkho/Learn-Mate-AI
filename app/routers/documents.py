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

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "app/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024 
ALLOWED_CONTENT_TYPE = "application/pdf"


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --- Validation 1: Extension check ---
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # --- Validation 2: Content-Type check ---
    # Extension aasani se fake ki ja sakti hai (virus.exe ko virus.pdf rename karna),
    # isliye content_type bhi check karte hain (double layer of defense)
    if file.content_type != ALLOWED_CONTENT_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type",
        )

    # --- Validation 3: Size check ---
    # file.file ek SpooledTemporaryFile hai — seek/tell se size nikal sakte hain
    # bina pura file memory mein load kiye
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # wapas start pe le aao, warna save karte waqt khali file save hogi

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Max size is 10MB",
        )

    # --- Unique filename generate karna (collision avoid karne ke liye) ---
    unique_name = f"{uuid.uuid4().hex}.pdf"
    destination_path = os.path.join(UPLOAD_DIR, unique_name)

    # --- File ko disk pe save karna ---
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # --- DB record banana ---
    new_document = Document(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=unique_name,
        file_path=destination_path,
        file_size=file_size,
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


@router.get("", response_model=list[DocumentOut])
def list_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Security-critical line: sirf CURRENT USER ke documents, kisi aur ke nahi
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

    # --- Authorization check ---
    # Sirf 404 dena kaafi nahi — ye check zaroori hai ke document
    # USSI user ka hai jo delete request kar raha hai. Warna User A,
    # User B ke document ka ID guess karke uska document delete kar sakta hai.
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document",
        )

    # Pehle disk se file hatao, phir DB record
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()
    return None