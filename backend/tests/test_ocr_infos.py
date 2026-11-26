from app.services.ocr_infos import Fiche, extraire_lot, extraire_unites_par_boite, identifier_medicament

CATALOGUE = [
    Fiche(1, 'Paracétamol 500 mg', 'Paracétamol', '500 mg'),
    Fiche(2, 'Amoxicilline 1 g', 'Amoxicilline', '1 g'),
    Fiche(3, 'Ibuprofène 400 mg', 'Ibuprofène', '400 mg'),
    Fiche(4, 'Sérum physiologique 0,9 %', 'Chlorure de sodium', '500 ml'),
]


def test_lot_avec_erreurs_ocr():
    assert extraire_lot(['L0T : PCT2611']) == 'PCT2611'      # « O » lu comme « 0 »
    assert extraire_lot(['L0TPCT1127']) == 'PCT1127'         # espaces perdus
    assert extraire_lot(['Lot n° AB-123']) == 'AB-123'
    assert extraire_lot(['BATCH 4471X']) == '4471X'
    assert extraire_lot(['L0T :0ME0828']) == 'OME0828'        # zéro lu à la place de la lettre O
    assert extraire_lot(['LOT 0123A']) == '0123A'             # un vrai zéro suivi de chiffres est gardé
    assert extraire_lot(['PARACETAMOL', 'MET0627']) is None   # pas de mot-clé : on ne devine pas


def test_unites_par_boite():
    assert extraire_unites_par_boite(['Boîte de 20 comprimés']) == 20
    assert extraire_unites_par_boite(['BOITE DE 14 GÉLULES']) == 14
    assert extraire_unites_par_boite(['Poche pour perfusion']) == 1
    assert extraire_unites_par_boite(['Boitede16gélules']) == 16   # espaces perdus par l'OCR
    assert extraire_unites_par_boite(['Pochepour perfusion']) == 1
    assert extraire_unites_par_boite(['PARACETAMOL 500 mg']) is None


def test_medicament_nom_et_dosage():
    r = identifier_medicament(['PARACÉTAMOL', 'Boîte de 20 comprimés', '500 mg'], CATALOGUE)
    assert (r['medicament_id'], r['medicament_confiance']) == (1, 'haute')


def test_medicament_par_dci_et_abreviation():
    r = identifier_medicament(['SÉRUM PHYSIO.', 'Chlorure de sodium', '0,9 % - 500 ml'], CATALOGUE)
    assert r['medicament_id'] == 4


def test_dosage_different_refuse():
    r = identifier_medicament(['PARACÉTAMOL', '1 g', 'Boîte de 8 comprimés'], CATALOGUE)
    assert r['medicament_id'] is None
    assert 'dosage' in r['avertissement']


def test_medicament_absent_du_catalogue():
    r = identifier_medicament(['METFORMINE', '850 mg'], CATALOGUE)
    assert r['medicament_id'] is None
    assert 'METFORMINE' in r['avertissement']
