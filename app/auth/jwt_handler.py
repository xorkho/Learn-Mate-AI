from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings


def create_access_token(data: dict) -> str:
    """
    JWT token banata hai. 'data' mein hum sirf user identifier daalte hain
    (jaise user_id), koi sensitive info nahi — kyunki JWT encrypted nahi,
    sirf signed hota hai. Koi bhi ise decode karke content padh sakta hai,
    bas usko tamper nahi kar sakta bina SECRET_KEY ke.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
