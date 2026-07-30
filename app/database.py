from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Engine = actual connection pool to PostgreSQL
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal = factory jo har request ke liye naya DB session banata hai
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = saare models isse inherit karenge (Step 5 mein use hoga)
Base = declarative_base()


def get_db():
    """
    Dependency function — FastAPI ke Depends() ke sath use hoga.
    Har API request ke liye ek fresh DB session deta hai,
    aur request khatam hone pe automatically close kar deta hai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
