"""Extraction des informations d'une boîte à partir du texte lu par l'OCR.

Tout est déterministe (expressions régulières + comparaison avec le catalogue) :
- numéro de lot (mot-clé LOT / BATCH) ;
- nombre d'unités dans une boîte (« Boîte de 20 comprimés ») ;
- médicament du catalogue (nom ou DCI + dosage).
Le dosage doit correspondre : on ne propose jamais « Paracétamol 500 mg »
pour une boîte de « Paracétamol 1 g ».
"""
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

MOTS_VIDES = {'DE', 'DU', 'LA', 'LE', 'LES', 'DES', 'ET', 'EN', 'POUR', 'AVEC'}

LOT_RE = re.compile(
    r'(?<![A-Z])(?:L[O0]T|BATCH|B\.N\.)(?:\s*N\s*[O°º]?\.?)?\s*[:.#]?\s*([A-Z0-9][A-Z0-9/-]{2,19})')
UNITES_RE = re.compile(  # espaces facultatifs : l'OCR colle souvent les mots (« Boitede16gélules »)
    r'(?:BOITE|ETUI|FLACON|TUBE|PLAQUETTE)S?\s*DE\s*(\d{1,4})\s*'
    r'(?:COMPRIM|GELUL|SACHET|AMPOUL|CAPSUL|SUPPOSITOIR|OVUL|DOSE|UNITE|SERINGUE)')
DOSAGE_RE = re.compile(r'(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(MG|G|ML|MCG|UI|%)(?![A-Z])')


def normaliser(texte: str) -> str:
    """Majuscules, sans accents (« Gélule » → « GELULE »)."""
    sans_accents = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode()
    return sans_accents.upper()


def extraire_lot(lignes: list[str]) -> str | None:
    for ligne in lignes:
        m = LOT_RE.search(normaliser(ligne))
        if m and any(c.isdigit() for c in m[1]):  # un n° de lot contient toujours un chiffre
            lot = m[1].strip('-/')
            # « 0ME0924 » : un zéro suivi de lettres est presque toujours la lettre O mal lue
            return re.sub(r'^0(?=[A-Z]{2})', 'O', lot)
    return None


def extraire_unites_par_boite(lignes: list[str]) -> int | None:
    texte = normaliser(' | '.join(lignes))
    m = UNITES_RE.search(texte)
    if m:
        return int(m[1])
    if re.search(r'(?<![A-Z])POCHE', texte):
        return 1  # une poche = une unité
    return None


def _dosages(texte: str) -> set[tuple[float, str]]:
    return {(float(n.replace(',', '.')), u) for n, u in DOSAGE_RE.findall(normaliser(texte))}


def _mots(texte: str) -> list[str]:
    return [m for m in re.findall(r'[A-Z]{3,}', normaliser(texte)) if m not in MOTS_VIDES]


def _present(mot: str, mots_lus: list[str]) -> bool:
    for lu in mots_lus:
        if SequenceMatcher(None, mot, lu).ratio() >= 0.8:
            return True
        # abréviation sur la boîte : « PHYSIO. » pour « PHYSIOLOGIQUE »
        if len(lu) >= 5 and mot.startswith(lu):
            return True
    return False


@dataclass
class Fiche:
    id: int
    nom: str
    dci: str
    dosage: str


def identifier_medicament(lignes: list[str], catalogue: list[Fiche]) -> dict:
    texte = ' | '.join(lignes)
    mots_lus = _mots(texte)
    dosages_lus = _dosages(texte)
    dosage_lu = next((f'{n} {u.lower()}' for n, u in DOSAGE_RE.findall(normaliser(texte))), '')
    nom_lu = next((l for l in lignes if len(re.findall(r'[A-ZÀ-Ý]', l)) >= 4 and l == l.upper()), lignes[0] if lignes else '')

    candidats = []
    for f in catalogue:
        mots_nom = [m for m in _mots(f.nom) if m not in {'MG', 'ML'}]
        mots_dci = _mots(f.dci)
        score_nom = sum(_present(m, mots_lus) for m in mots_nom) / len(mots_nom) if mots_nom else 0
        dci_ok = bool(mots_dci) and all(_present(m, mots_lus) for m in mots_dci)
        if score_nom >= 0.5 or dci_ok:
            candidats.append((max(score_nom, 1.0 if dci_ok else 0), f))

    resultat = {'medicament_id': None, 'medicament': None, 'medicament_confiance': 'aucune',
                'nom_lu': nom_lu, 'dosage_lu': dosage_lu, 'avertissement': None}
    if not candidats:
        resultat['avertissement'] = (f'Médicament absent du catalogue (texte lu : {nom_lu} {dosage_lu}). '
                                     'Ajoutez-le dans la page Médicaments ou choisissez-le dans la liste.').replace('  ', ' ')
        return resultat

    bons = [(s, f) for s, f in candidats if not _dosages(f.dosage) or _dosages(f.dosage) <= dosages_lus]
    if not bons:
        noms = ', '.join(sorted({f.nom for _, f in candidats}))
        resultat['avertissement'] = (f'Le dosage lu ({dosage_lu or "illisible"}) ne correspond à aucun médicament '
                                     f'du catalogue ({noms}). Vérifiez la boîte ou ajoutez ce dosage.')
        return resultat

    bons.sort(key=lambda x: x[0], reverse=True)
    score, choix = bons[0]
    ex_aequo = len(bons) > 1 and bons[1][0] == score
    resultat.update(medicament_id=choix.id, medicament=choix.nom,
                    medicament_confiance='moyenne' if ex_aequo or score < 1 else 'haute')
    if ex_aequo:
        resultat['avertissement'] = 'Plusieurs médicaments du catalogue correspondent : vérifiez le choix.'
    return resultat
