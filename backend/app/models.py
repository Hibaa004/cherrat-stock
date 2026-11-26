import datetime as dt
import enum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Role(str, enum.Enum):
    docteur = 'docteur'
    major = 'major'
    infirmier = 'infirmier'


class TypeMouvement(str, enum.Enum):
    entree = 'entree'
    sortie = 'sortie'
    ajustement = 'ajustement'


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[Role] = mapped_column(Enum(Role))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class Medicament(Base):
    __tablename__ = 'medicaments'
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), index=True)
    dci: Mapped[str] = mapped_column(String(150), default='')
    forme: Mapped[str] = mapped_column(String(60), default='')
    dosage: Mapped[str] = mapped_column(String(60), default='')
    categorie: Mapped[str] = mapped_column(String(80), default='')
    seuil_alerte: Mapped[int] = mapped_column(Integer, default=10)
    lots: Mapped[list['Lot']] = relationship(back_populates='medicament', cascade='all, delete-orphan')

    @property
    def stock_utilisable(self) -> int:
        # Seules les unités non expirées peuvent être données au patient
        aujourdhui = dt.date.today()
        return sum(lot.quantite for lot in self.lots
                   if lot.quantite > 0 and lot.date_expiration >= aujourdhui)


class Lot(Base):
    __tablename__ = 'lots'
    id: Mapped[int] = mapped_column(primary_key=True)
    medicament_id: Mapped[int] = mapped_column(ForeignKey('medicaments.id'), index=True)
    numero_lot: Mapped[str] = mapped_column(String(60))
    date_expiration: Mapped[dt.date] = mapped_column(Date)
    quantite: Mapped[int] = mapped_column(Integer, default=0)
    date_reception: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    image_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    medicament: Mapped['Medicament'] = relationship(back_populates='lots')


class Mouvement(Base):
    __tablename__ = 'mouvements'
    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey('lots.id'), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    type: Mapped[TypeMouvement] = mapped_column(Enum(TypeMouvement))
    quantite: Mapped[int] = mapped_column(Integer)
    motif: Mapped[str] = mapped_column(String(200), default='')
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lot: Mapped['Lot'] = relationship()
    user: Mapped['User'] = relationship()


class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    cle: Mapped[str] = mapped_column(String(80), unique=True)
    type: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text)
    medicament_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lue: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())