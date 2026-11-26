import datetime as dt

from sqlalchemy import func, select

from .database import Base, SessionLocal, engine
from .models import Lot, Medicament, Role, User
from .security import hash_password


def run():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count(User.id))):
            print('Base déjà initialisée')
            return
        db.add_all(
            [
                User(nom='Major Mohammed', email='major@cherrat.ma',
                     password_hash=hash_password('Major123!'), role=Role.major),
                User(nom='Dr Narjiss', email='docteur@cherrat.ma',
                     password_hash=hash_password('Docteur123!'), role=Role.docteur),
                User(nom='Infirmiere Siham', email='infirmiere@cherrat.ma',
                     password_hash=hash_password('Infirmier123!'), role=Role.infirmier),
            ]
        )
        meds = [
            Medicament(nom='Paracétamol 500 mg', dci='Paracétamol', forme='Comprimé',
                       dosage='500 mg', categorie='Antalgique', seuil_alerte=50),
            Medicament(nom='Amoxicilline 1 g', dci='Amoxicilline', forme='Comprimé',
                       dosage='1 g', categorie='Antibiotique', seuil_alerte=30),
            Medicament(nom='Ibuprofène 400 mg', dci='Ibuprofène', forme='Comprimé',
                       dosage='400 mg', categorie='Anti-inflammatoire', seuil_alerte=40),
            Medicament(nom='Sérum physiologique 0,9 %', dci='Chlorure de sodium',
                       forme='Poche', dosage='500 ml', categorie='Solucé', seuil_alerte=20),
        ]
        db.add_all(meds)
        db.flush()
        j = dt.date.today()
        db.add_all(
            [
                Lot(medicament_id=meds[0].id, numero_lot='PCT-001',
                    date_expiration=j + dt.timedelta(days=200), quantite=300),
                Lot(medicament_id=meds[1].id, numero_lot='AMX-014',
                    date_expiration=j + dt.timedelta(days=25), quantite=60),
                Lot(medicament_id=meds[1].id, numero_lot='AMX-020',
                    date_expiration=j + dt.timedelta(days=400), quantite=100),
                Lot(medicament_id=meds[2].id, numero_lot='IBU-007',
                    date_expiration=j + dt.timedelta(days=300), quantite=12),
                Lot(medicament_id=meds[3].id, numero_lot='SER-100',
                    date_expiration=j - dt.timedelta(days=5), quantite=15),
            ]
        )
        db.commit()
        print('Données de départ créées')


if __name__ == '__main__':
    run()
