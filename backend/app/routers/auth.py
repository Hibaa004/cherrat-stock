from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import Token, UserOut
from ..security import create_token, verify_password

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Le formulaire standard OAuth2 nomme le champ email 'username'
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not user.actif or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=401, detail='Email ou mot de passe incorrect')
    return Token(access_token=create_token(str(user.id), user.role.value))


@router.get('/me', response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
