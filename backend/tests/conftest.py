"""Tests rapides : base SQLite en mémoire, sans PostgreSQL, Qdrant ni Ollama."""
import datetime as dt

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.models import Lot, Medicament, Role, User
from app.routers import automation, stock
from app.security import create_token, hash_password

CLE = 'cle-de-test'


@pytest.fixture
def db():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    with Session() as session:
        j = dt.date.today()
        major = User(nom='Major', email='major@test.ma', password_hash=hash_password('x'), role=Role.major)
        para = Medicament(nom='Paracétamol', seuil_alerte=50)
        serum = Medicament(nom='Sérum', seuil_alerte=20)
        amox = Medicament(nom='Amoxicilline', seuil_alerte=30)
        session.add_all([major, para, serum, amox])
        session.flush()
        session.add_all([
            Lot(medicament_id=para.id, numero_lot='P1', date_expiration=j + dt.timedelta(days=200), quantite=300),
            Lot(medicament_id=serum.id, numero_lot='S1', date_expiration=j - dt.timedelta(days=5), quantite=15),
            Lot(medicament_id=amox.id, numero_lot='A1', date_expiration=j + dt.timedelta(days=10), quantite=20),
            Lot(medicament_id=amox.id, numero_lot='A2', date_expiration=j + dt.timedelta(days=60), quantite=5),
        ])
        session.commit()
        yield session


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setattr(settings, 'AUTOMATION_API_KEY', CLE)
    # pas de réindexation dans le vrai Qdrant pendant les tests
    monkeypatch.setattr(stock, 'reindex', lambda med_id: None)
    app = FastAPI()
    app.include_router(automation.router)
    app.include_router(stock.router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


@pytest.fixture
def jeton_major(db):
    major = db.query(User).filter_by(role=Role.major).one()
    return {'Authorization': 'Bearer ' + create_token(str(major.id), 'major')}
