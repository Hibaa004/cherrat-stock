import datetime as dt

import pytest

cv2 = pytest.importorskip('cv2')
from app.services.ocr_service import choisir_date, extraire_dates  # noqa: E402

AN = dt.date.today().year + 1


@pytest.mark.parametrize('texte,attendu', [
    (f'EXP: 05/{AN}', dt.date(AN, 5, 31)),
    (f'EXP {AN}-02', dt.date(AN, 2, 28 if AN % 4 else 29)),
    (f'EXP 31.05.{AN}', dt.date(AN, 5, 31)),
    (f'MAY {AN}', dt.date(AN, 5, 31)),
])
def test_formats(texte, attendu):
    assert attendu in extraire_dates(texte)


def test_priorite_mot_exp_sur_fabrication():
    lignes = [f'FAB: 01/{AN - 1}', 'LOT: PAR2401', f'EXP: 01/{AN + 2}']
    date, confiance = choisir_date(lignes)
    assert date == dt.date(AN + 2, 1, 31)
    assert confiance == 'haute'


def test_aucune_date():
    assert choisir_date(['PARACETAMOL 500 mg']) == (None, 'aucune')
