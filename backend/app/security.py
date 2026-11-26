import datetime as dt

import bcrypt
import jwt

from .config import settings

ALGORITHM = 'HS256'


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, role: str) -> str:
    expire = dt.datetime.now(
        dt.timezone.utc) + dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({'sub': user_id, 'role': role, 'exp': expire}, settings.SECRET_KEY, algorithm=ALGORITHM)
