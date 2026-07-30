from pydantic import BaseModel, EmailStr
from datetime import datetime


# ---- Request schemas (client se aane wala data) ----

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---- Response schemas (client ko jaane wala data) ----

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy object ko directly is schema mein convert karne deta hai


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
