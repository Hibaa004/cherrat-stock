from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Notification, Role, User
from ..schemas import NotificationOut
from ..services.notif_service import run_checks

router = APIRouter(prefix='/notifications', tags=['notifications'])


@router.get('', response_model=list[NotificationOut])
def lister(non_lues: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Notification)
    if non_lues:
        stmt = stmt.where(Notification.lue.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc(),
                         Notification.id.desc()).limit(100)
    return db.scalars(stmt).all()


@router.post('/{notif_id}/lue')
def marquer_lue(notif_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notif = db.get(Notification, notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail='Notification introuvable')
    notif.lue = True
    db.commit()
    return {'ok': True}


@router.post('/verifier')
def verifier_maintenant(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.major))):
    return {'nouvelles': run_checks(db)}
