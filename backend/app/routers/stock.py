import datetime as dt

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Lot, Medicament, Mouvement, Role, TypeMouvement, User
from ..schemas import AjustementIn, EntreeIn, SortieIn
from ..services.reindex import reindex

router = APIRouter(prefix='/stock', tags=['stock'])
PEUT_MODIFIER = require_roles(Role.major, Role.infirmier)


@router.post('/entree', status_code=201)
def entree(body: EntreeIn, bg: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(PEUT_MODIFIER)):
    med = db.get(Medicament, body.medicament_id)
    if not med:
        raise HTTPException(status_code=404, detail='Médicament introuvable')
    lot = db.scalar(select(Lot).where(Lot.medicament_id ==
                    med.id, Lot.numero_lot == body.numero_lot))
    if lot:
        lot.quantite += body.quantite
    else:
        lot = Lot(
            medicament_id=med.id,
            numero_lot=body.numero_lot,
            date_expiration=body.date_expiration,
            quantite=body.quantite,
            image_path=body.image_path,
        )
        db.add(lot)
        db.flush()
    db.add(Mouvement(lot_id=lot.id, user_id=user.id,
           type=TypeMouvement.entree, quantite=body.quantite, motif='Réception'))
    db.commit()
    bg.add_task(reindex, med.id)
    return {'lot_id': lot.id, 'message': 'Entrée enregistrée'}


@router.post('/sortie')
def sortie(body: SortieIn, bg: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(PEUT_MODIFIER)):
    aujourdhui = dt.date.today()
    lots = db.scalars(
        select(Lot)
        .where(Lot.medicament_id == body.medicament_id, Lot.quantite > 0, Lot.date_expiration >= aujourdhui)
        .order_by(Lot.date_expiration)
        .with_for_update()
    ).all()
    disponible = sum(lot.quantite for lot in lots)
    if disponible < body.quantite:
        raise HTTPException(
            status_code=400, detail=f'Stock insuffisant : {disponible} unité(s) utilisable(s)')
    reste = body.quantite
    for lot in lots:
        prelevement = min(lot.quantite, reste)
        lot.quantite -= prelevement
        db.add(
            Mouvement(
                lot_id=lot.id,
                user_id=user.id,
                type=TypeMouvement.sortie,
                quantite=prelevement,
                motif=body.motif or 'Dispensation',
            )
        )
        reste -= prelevement
        if reste == 0:
            break
    db.commit()
    bg.add_task(reindex, body.medicament_id)
    return {'message': 'Sortie enregistrée (FEFO)'}


@router.post('/ajustement')
def ajustement(
    body: AjustementIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.major)),
):
    lot = db.get(Lot, body.lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail='Lot introuvable')
    difference = body.nouvelle_quantite - lot.quantite
    lot.quantite = body.nouvelle_quantite
    db.add(
        Mouvement(lot_id=lot.id, user_id=user.id, type=TypeMouvement.ajustement,
                  quantite=abs(difference), motif=body.motif)
    )
    db.commit()
    bg.add_task(reindex, lot.medicament_id)
    return {'message': 'Quantité corrigée'}


@router.get('/mouvements')
def mouvements(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lignes = db.scalars(select(Mouvement).order_by(
        Mouvement.created_at.desc(), Mouvement.id.desc()).limit(limit)).all()
    return [
        {
            'id': m.id,
            'date': m.created_at,
            'type': m.type.value,
            'quantite': m.quantite,
            'motif': m.motif,
            'medicament': m.lot.medicament.nom,
            'lot': m.lot.numero_lot,
            'utilisateur': m.user.nom,
        }
        for m in lignes
    ]


@router.get('/dashboard')
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    aujourdhui = dt.date.today()
    meds = db.scalars(select(Medicament)).all()
    ruptures, stock_bas = [], []
    for m in meds:
        total = m.stock_utilisable  # les lots expirés ne comptent pas
        if total == 0:
            ruptures.append(m.nom)
        elif total <= m.seuil_alerte:
            stock_bas.append(m.nom)
    lots = db.scalars(
        select(Lot)
        .where(Lot.quantite > 0, Lot.date_expiration <= aujourdhui + dt.timedelta(days=90))
        .order_by(Lot.date_expiration)
    ).all()
    a_surveiller = [
        {
            'lot_id': lot.id,
            'medicament': lot.medicament.nom,
            'numero_lot': lot.numero_lot,
            'date_expiration': lot.date_expiration,
            'quantite': lot.quantite,
            'jours_restants': (lot.date_expiration - aujourdhui).days,
        }
        for lot in lots
    ]
    return {
        'total_medicaments': len(meds),
        'ruptures': ruptures,
        'stock_bas': stock_bas,
        'lots_a_surveiller': a_surveiller,
        'nb_expires': sum(1 for x in a_surveiller if x['jours_restants'] < 0),
    }
