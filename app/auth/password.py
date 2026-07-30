from passlib.context import CryptContext

# bcrypt algorithm use karte hain — slow-by-design, jo brute force attacks ko mushkil banata hai
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
