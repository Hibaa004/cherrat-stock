import calendar
import datetime as dt
import re

import cv2

_ocr = None

MOIS = {
    'JAN': 1, 'JANV': 1, 'FEB': 2, 'FEV': 2, 'FEVR': 2, 'MAR': 3, 'MARS': 3,
    'APR': 4, 'AVR': 4, 'AVRIL': 4, 'MAY': 5, 'MAI': 5, 'JUN': 6, 'JUIN': 6,
    'JUL': 7, 'JUIL': 7, 'AUG': 8, 'AOU': 8, 'AOUT': 8, 'SEP': 9, 'SEPT': 9,
    'OCT': 10, 'NOV': 11, 'DEC': 12,
}

MOTS_CLES = re.compile(
    r'(?<![A-Z])(EXP|EXPIRY|EXPIRATION|PER|PEREMPTION|PÉREMPTION|UTIL|USE BY|BEST BEFORE|BB)(?![A-Z])')


def get_ocr():
    # Chargement paresseux : les modèles ne se chargent qu'au premier scan
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR

        _ocr = PaddleOCR(use_angle_cls=True, lang='fr', show_log=False)
    return _ocr


def preparer_images(img):
    h, w = img.shape[:2]
    plus_grand = max(h, w)
    if plus_grand < 1200 or plus_grand > 2000:
        echelle = 1600 / plus_grand
        img = cv2.resize(img, None, fx=echelle, fy=echelle,
                         interpolation=cv2.INTER_CUBIC)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gris = cv2.fastNlMeansDenoising(gris, None, 10, 7, 21)
    contraste = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gris)
    binaire = cv2.adaptiveThreshold(
        contraste, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    return [img, cv2.cvtColor(contraste, cv2.COLOR_GRAY2BGR), cv2.cvtColor(binaire, cv2.COLOR_GRAY2BGR)]


def lire_lignes(img) -> list[str]:
    resultat = get_ocr().ocr(img, cls=True)
    if not resultat or not resultat[0]:
        return []
    return [ligne[1][0] for ligne in resultat[0]]


def _date(annee, mois, jour=None):
    if annee < 100:
        annee += 2000
    if not 1 <= mois <= 12:
        return None
    if jour is None:
        jour = calendar.monthrange(annee, mois)[1]  # dernier jour du mois
    try:
        return dt.date(annee, mois, jour)
    except ValueError:
        return None


def _consommer(motif, texte, convertir, trouvees):
    # Cherche un motif, mémorise la date trouvée et efface le texte utilisé
    # pour qu'un motif suivant ne le relise pas.
    def remplacer(m):
        d = convertir(m)
        if d is None:
            return m.group(0)
        trouvees.append(d)
        return ' ' * len(m.group(0))

    return re.sub(motif, remplacer, texte)


def _mois_nom(m):
    mois = MOIS.get(m[1])
    return None if mois is None else _date(int(m[2]), mois)


def extraire_dates(texte: str) -> list[dt.date]:
    t = texte.upper()
    trouvees: list[dt.date] = []
    t = _consommer(r'(?<![0-9])([0-9]{4})[/.-]([0-9]{1,2})[/.-]([0-9]{1,2})(?![0-9])',
                   t, lambda m: _date(int(m[1]), int(m[2]), int(m[3])), trouvees)
    t = _consommer(r'(?<![0-9])([0-9]{1,2})[/. -]([0-9]{1,2})[/. -]([0-9]{4})(?![0-9])',
                   t, lambda m: _date(int(m[3]), int(m[2]), int(m[1])), trouvees)
    t = _consommer(
        r'(?<![A-Z0-9])([A-Z]{3,5})[ ./-]*([0-9]{4}|[0-9]{2})(?![0-9])', t, _mois_nom, trouvees)
    t = _consommer(r'(?<![0-9])([0-9]{4})[/.-]([0-9]{1,2})(?![0-9])',
                   t, lambda m: _date(int(m[1]), int(m[2])), trouvees)
    t = _consommer(r'(?<![0-9])([0-9]{1,2})[/. -]([0-9]{4})(?![0-9])',
                   t, lambda m: _date(int(m[2]), int(m[1])), trouvees)
    t = _consommer(r'(?<![0-9])([0-9]{1,2})[/.-]([0-9]{2})(?![0-9])',
                   t, lambda m: _date(int(m[2]), int(m[1])), trouvees)
    an = dt.date.today().year
    return [d for d in trouvees if an - 1 <= d.year <= an + 15]


def choisir_date(lignes: list[str]):
    haut = [ligne.upper() for ligne in lignes]
    prioritaires: list[dt.date] = []
    for i, ligne in enumerate(haut):
        if MOTS_CLES.search(ligne):
            suite = haut[i + 1] if i + 1 < len(haut) else ''
            prioritaires += extraire_dates(ligne + ' | ' + suite)
    if prioritaires:
        return max(prioritaires), 'haute'
    toutes = extraire_dates(' | '.join(haut))
    if toutes:
        return max(toutes), 'moyenne'
    return None, 'aucune'


def detecter_expiration(img) -> dict:
    ordre = {'aucune': 0, 'moyenne': 1, 'haute': 2}
    meilleur = {'date_expiration': None,
                'confiance': 'aucune', 'texte_brut': []}
    tous_textes: list[str] = []
    for variante in preparer_images(img):
        lignes = lire_lignes(variante)
        tous_textes.extend(lignes)
        date, confiance = choisir_date(lignes)
        if ordre[confiance] > ordre[meilleur['confiance']]:
            meilleur = {
                'date_expiration': date.isoformat() if date else None,
                'confiance': confiance,
                'texte_brut': lignes,
            }
        if confiance == 'haute':
            break
    if not meilleur['texte_brut']:
        meilleur['texte_brut'] = tous_textes
    return meilleur
