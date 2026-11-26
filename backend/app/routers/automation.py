"""Routes de l'automatisation n8n.

n8n s'authentifie avec une clé d'API (en-tête X-API-Key) au lieu d'un compte
utilisateur : la clé permet seulement de lire les faits du stock et de déposer
le rapport du jour. Le personnel lit ce rapport sur le tableau de bord.
"""
import datetime as dt
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import Lot, Medicament, Notification, RapportIA, User

router = APIRouter(prefix='/automation', tags=['automatisation n8n'])


def verifier_cle(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.AUTOMATION_API_KEY:
        raise HTTPException(
            status_code=503, detail='Automatisation désactivée : AUTOMATION_API_KEY absente du fichier .env')
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.AUTOMATION_API_KEY):
        raise HTTPException(status_code=401, detail='Clé API invalide')


@router.get('/rapport', dependencies=[Depends(verifier_cle)])
def rapport(db: Session = Depends(get_db)):
    """Faits du stock, calculés par le code (jamais par l'IA)."""
    aujourdhui = dt.date.today()
    ruptures, stock_bas = [], []
    for med in db.scalars(select(Medicament).order_by(Medicament.nom)).all():
        utilisable = med.stock_utilisable
        ligne = {'medicament': med.nom, 'stock_utilisable': utilisable,
                 'seuil_alerte': med.seuil_alerte}
        if utilisable == 0:
            ruptures.append(ligne)
        elif utilisable <= med.seuil_alerte:
            stock_bas.append(ligne)

    lots = db.scalars(
        select(Lot)
        .where(Lot.quantite > 0, Lot.date_expiration <= aujourdhui + dt.timedelta(days=90))
        .order_by(Lot.date_expiration)
    ).all()
    expires, sous_30j, sous_90j = [], [], []
    for lot in lots:
        jours = (lot.date_expiration - aujourdhui).days
        ligne = {
            'medicament': lot.medicament.nom,
            'numero_lot': lot.numero_lot,
            'quantite': lot.quantite,
            'date_expiration': lot.date_expiration.isoformat(),
            'jours_restants': jours,
        }
        (expires if jours < 0 else sous_30j if jours <= 30 else sous_90j).append(ligne)

    non_lues = db.scalars(
        select(Notification.message).where(Notification.lue.is_(False))
        .order_by(Notification.created_at.desc()).limit(50)
    ).all()

    return {
        'date': aujourdhui.isoformat(),
        'total_medicaments': db.scalar(select(func.count(Medicament.id))),
        'ruptures': ruptures,
        'stock_bas': stock_bas,
        'lots_expires': expires,
        'lots_sous_30j': sous_30j,
        'lots_sous_90j': sous_90j,
        'notifications_non_lues': list(non_lues),
        'nb_alertes': len(ruptures) + len(stock_bas) + len(expires) + len(sous_30j),
    }


class RapportIAIn(BaseModel):
    date: dt.date
    nb_alertes: int = Field(ge=0)
    synthese: str = Field(min_length=1, max_length=2000)
    actions: str = Field(default='', max_length=5000)
    faits: str = Field(default='', max_length=20000)
    source: str = Field(pattern='^(ia|repli|sans_alerte)$')
    modele: str = Field(default='', max_length=60)


@router.post('/rapport-ia', dependencies=[Depends(verifier_cle)])
def deposer_rapport(body: RapportIAIn, db: Session = Depends(get_db)):
    """Appelé par n8n : un rapport par jour (une nouvelle exécution le remplace)."""
    rapport_ = db.scalar(select(RapportIA).where(RapportIA.date == body.date))
    if rapport_ is None:
        rapport_ = RapportIA(date=body.date)
        db.add(rapport_)
    for champ, valeur in body.model_dump().items():
        setattr(rapport_, champ, valeur)
    db.commit()
    return {'id': rapport_.id, 'message': 'Rapport enregistré'}


@router.get('/dernier-rapport')
def dernier_rapport(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Lu par le tableau de bord du personnel (tous les rôles)."""
    r = db.scalar(select(RapportIA).order_by(RapportIA.date.desc()).limit(1))
    if r is None:
        return None
    return {
        'date': r.date.isoformat(),
        'nb_alertes': r.nb_alertes,
        'synthese': r.synthese,
        'actions': r.actions,
        'faits': r.faits,
        'source': r.source,
        'modele': r.modele,
        'mis_a_jour': r.created_at,
        'du_jour': r.date == dt.date.today(),
    }
