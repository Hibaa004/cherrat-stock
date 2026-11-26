from .conftest import CLE


def test_rapport_refuse_sans_cle(client):
    assert client.get('/automation/rapport').status_code == 401
    assert client.get('/automation/rapport', headers={'X-API-Key': 'faux'}).status_code == 401


def test_rapport_desactive_si_cle_absente(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, 'AUTOMATION_API_KEY', '')
    assert client.get('/automation/rapport', headers={'X-API-Key': CLE}).status_code == 503


def test_rapport_contenu(client):
    r = client.get('/automation/rapport', headers={'X-API-Key': CLE})
    assert r.status_code == 200
    data = r.json()
    assert data['total_medicaments'] == 3
    # Le sérum n'a qu'un lot expiré : il est en rupture (stock utilisable = 0)
    assert [x['medicament'] for x in data['ruptures']] == ['Sérum']
    assert [x['medicament'] for x in data['stock_bas']] == ['Amoxicilline']
    assert [x['numero_lot'] for x in data['lots_expires']] == ['S1']
    assert [x['numero_lot'] for x in data['lots_sous_30j']] == ['A1']
    assert [x['numero_lot'] for x in data['lots_sous_90j']] == ['A2']
    assert data['nb_alertes'] == 4


def test_dashboard_ignore_lots_expires(client, jeton_major):
    data = client.get('/stock/dashboard', headers=jeton_major).json()
    assert data['ruptures'] == ['Sérum']
    assert data['stock_bas'] == ['Amoxicilline']
    assert data['nb_expires'] == 1


def test_sortie_fefo_et_stock_insuffisant(client, jeton_major, db):
    from app.models import Lot
    amox_id = db.query(Lot).filter_by(numero_lot='A1').one().medicament_id
    r = client.post('/stock/sortie', json={'medicament_id': amox_id, 'quantite': 22}, headers=jeton_major)
    assert r.status_code == 200
    db.expire_all()
    # FEFO : le lot qui expire en premier (A1) est vidé avant A2
    assert db.query(Lot).filter_by(numero_lot='A1').one().quantite == 0
    assert db.query(Lot).filter_by(numero_lot='A2').one().quantite == 3
    r = client.post('/stock/sortie', json={'medicament_id': amox_id, 'quantite': 4}, headers=jeton_major)
    assert r.status_code == 400


RAPPORT = {
    'date': '2026-01-15', 'nb_alertes': 4, 'synthese': '4 alerte(s) à traiter',
    'actions': '- Retirer le lot S1', 'faits': 'LOTS EXPIRÉS (1)', 'source': 'ia', 'modele': 'llama3.2:3b',
}


def test_depot_rapport_ia_exige_la_cle(client):
    assert client.post('/automation/rapport-ia', json=RAPPORT).status_code == 401


def test_depot_puis_lecture_du_rapport(client, jeton_major):
    assert client.get('/automation/dernier-rapport', headers=jeton_major).json() is None
    r = client.post('/automation/rapport-ia', json=RAPPORT, headers={'X-API-Key': CLE})
    assert r.status_code == 200
    # Une deuxième exécution le même jour remplace le rapport au lieu d'en créer un autre
    client.post('/automation/rapport-ia', json={**RAPPORT, 'source': 'repli', 'actions': ''}, headers={'X-API-Key': CLE})
    client.post('/automation/rapport-ia', json={**RAPPORT, 'date': '2026-01-14'}, headers={'X-API-Key': CLE})
    data = client.get('/automation/dernier-rapport', headers=jeton_major).json()
    assert data['date'] == '2026-01-15'
    assert data['source'] == 'repli'
    assert data['actions'] == ''


def test_lecture_du_rapport_exige_une_connexion(client):
    assert client.get('/automation/dernier-rapport').status_code == 401


def test_source_invalide_refusee(client):
    r = client.post('/automation/rapport-ia', json={**RAPPORT, 'source': 'autre'}, headers={'X-API-Key': CLE})
    assert r.status_code == 422
