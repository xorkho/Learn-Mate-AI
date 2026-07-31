from pydantic import BaseModel
from datetime import datetime


class DocumentOut(BaseModel):
    """
    Response schema — user ko sirf ye fields dikhengi.
    Note: file_path bilkul include nahi kiya — server ka internal disk
    structure client ko batana security risk hai (path traversal attacks
    ke liye clues de sakta hai).
    """
    id: int
    original_filename: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True