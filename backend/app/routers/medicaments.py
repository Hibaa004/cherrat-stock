from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Medicament, Role, User
from ..schemas import MedicamentIn, MedicamentOut
from ..services.reindex import reindex

router = APIRouter(prefix='/medicaments', tags=['médicaments'])


def to_out(m: Medicament) -> MedicamentOut:
    lots = [lot for lot in m.lots if lot.quantite > 0]
    return MedicamentOut(
        id=m.id,
        nom=m.nom,
        dci=m.dci,
        forme=m.forme,
        dosage=m.dosage,
        categorie=m.categorie,
        seuil_alerte=m.seuil_alerte,
        stock_total=sum(lot.quantite for lot in lots),
        prochaine_expiration=min(
            (lot.date_expiration for lot in lots), default=None),
    )


@router.get('', response_model=list[MedicamentOut])
def list_medicaments(q: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Medicament).order_by(Medicament.nom)
    if q:
        motif = '%' + q + '%'
        stmt = stmt.where(or_(Medicament.nom.ilike(
            motif), Medicament.dci.ilike(motif)))
    return [to_out(m) for m in db.scalars(stmt).all()]


@router.post('', response_model=MedicamentOut, status_code=201)
def create_medicament(
    body: MedicamentIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.major)),
):
    med = Medicament(**body.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    bg.add_task(reindex, med.id)
    return to_out(med)


@router.put('/{med_id}', response_model=MedicamentOut)
def update_medicament(
    med_id: int,
    body: MedicamentIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.major)),
):
    med = db.get(Medicament, med_id)
    if not med:
        raise HTTPException(status_code=404, detail='Médicament introuvable')
    for champ, valeur in body.model_dump().items():
        setattr(med, champ, valeur)
    db.commit()
    db.refresh(med)
    bg.add_task(reindex, med.id)
    return to_out(med)
