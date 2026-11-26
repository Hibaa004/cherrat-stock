from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import Role, User
from ..schemas import UserCreate, UserOut
from ..security import hash_password

router = APIRouter(prefix='/users', tags=['utilisateurs'],
                   dependencies=[Depends(require_roles(Role.major))])


@router.get('', response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.nom)).all()


@router.post('', response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(
            status_code=409, detail='Cet email est déjà utilisé')
    user = User(nom=body.nom, email=body.email,
                password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch('/{user_id}/actif', response_model=UserOut)
def toggle_actif(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Utilisateur introuvable')
    user.actif = not user.actif
    db.commit()
    db.refresh(user)
    return user
