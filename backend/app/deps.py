import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Role, User
from .security import ALGORITHM

oauth2 = OAuth2PasswordBearer(tokenUrl='/auth/login')


def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[ALGORITHM])
        user_id = int(payload['sub'])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail='Token invalide ou expiré')
    user = db.get(User, user_id)
    if not user or not user.actif:
        raise HTTPException(
            status_code=401, detail='Utilisateur inconnu ou désactivé')
    return user


def require_roles(*roles: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=403, detail='Accès refusé pour votre rôle')
        return user

    return checker
