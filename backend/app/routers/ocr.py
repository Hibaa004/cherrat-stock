import os
import uuid

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import require_roles
from ..models import Medicament, Role, User
from ..services.ocr_infos import Fiche, extraire_lot, extraire_unites_par_boite, identifier_medicament
from ..services.ocr_service import detecter_expiration

router = APIRouter(prefix='/ocr', tags=['ocr'])


@router.post('/scan')
def scan(file: UploadFile = File(...), db: Session = Depends(get_db),
         user: User = Depends(require_roles(Role.major, Role.infirmier))):
    data = file.file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail='Image trop lourde (10 Mo maximum)')
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail='Fichier image illisible')
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    nom = uuid.uuid4().hex + '.jpg'
    cv2.imwrite(os.path.join(settings.UPLOAD_DIR, nom), img)
    resultat = detecter_expiration(img)
    resultat['image_path'] = nom
    resultat.update(completer_infos(resultat['texte_brut'], db))
    return resultat


def completer_infos(lignes: list[str], db: Session) -> dict:
    """Lot, contenu de la boîte et médicament du catalogue, à partir du texte lu."""
    catalogue = [Fiche(m.id, m.nom, m.dci, m.dosage) for m in db.scalars(select(Medicament)).all()]
    return {
        'numero_lot': extraire_lot(lignes),
        'unites_par_boite': extraire_unites_par_boite(lignes),
        **identifier_medicament(lignes, catalogue),
    }
