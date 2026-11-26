import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Lot, Medicament, Notification


def _creer(db: Session, cle: str, type_: str, message: str, medicament_id: int, nouveaux: list) -> None:
    if db.scalar(select(Notification.id).where(Notification.cle == cle)):
        return  # alerte déjà créée
    db.add(Notification(cle=cle, type=type_,
           message=message, medicament_id=medicament_id))
    db.commit()
    nouveaux.append(message)


def run_checks(db: Session) -> int:
    aujourdhui = dt.date.today()
    nouveaux: list[str] = []
    for lot in db.scalars(select(Lot).where(Lot.quantite > 0)).all():
        jours = (lot.date_expiration - aujourdhui).days
        med = lot.medicament
        if jours < 0:
            palier, type_ = 'expire', 'expire'
            texte = f'⛔ {med.nom} - lot {lot.numero_lot} EXPIRÉ depuis {-jours} jour(s) : {lot.quantite} unité(s) à retirer du stock'
        elif jours <= 30:
            palier, type_ = 'exp30', 'expiration_proche'
            texte = f'🔴 {med.nom} - lot {lot.numero_lot} expire dans {jours} jour(s) ({lot.quantite} unités)'
        elif jours <= 90:
            palier, type_ = 'exp90', 'expiration_proche'
            texte = f'🟠 {med.nom} - lot {lot.numero_lot} expire dans {jours} jour(s) ({lot.quantite} unités)'
        else:
            continue
        _creer(db, palier + ':' + str(lot.id), type_, texte, med.id, nouveaux)

    annee, semaine, _ = aujourdhui.isocalendar()
    for med in db.scalars(select(Medicament)).all():
        total = med.stock_utilisable  # les lots expirés ne comptent pas
        if total <= med.seuil_alerte:
            etat = 'RUPTURE' if total == 0 else 'stock bas'
            texte = f'📉 {med.nom} : {etat} ({total} unité(s), seuil {med.seuil_alerte})'
            _creer(db, f'stock_bas:{med.id}:{annee}-{semaine}',
                   'stock_bas', texte, med.id, nouveaux)
    return len(nouveaux)
