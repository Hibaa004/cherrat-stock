import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from .models import Role


class UserCreate(BaseModel):
    nom: str
    email: str
    password: str = Field(min_length=8)
    role: Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    email: str
    role: Role
    actif: bool


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class MedicamentIn(BaseModel):
    nom: str
    dci: str = ''
    forme: str = ''
    dosage: str = ''
    categorie: str = ''
    seuil_alerte: int = Field(default=10, ge=0)


class MedicamentOut(MedicamentIn):
    id: int
    stock_total: int
    prochaine_expiration: dt.date | None = None


class EntreeIn(BaseModel):
    medicament_id: int
    numero_lot: str
    date_expiration: dt.date
    quantite: int = Field(gt=0)
    image_path: str | None = None


class SortieIn(BaseModel):
    medicament_id: int
    quantite: int = Field(gt=0)
    motif: str = ''


class AjustementIn(BaseModel):
    lot_id: int
    nouvelle_quantite: int = Field(ge=0)
    motif: str


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    message: str
    lue: bool
    created_at: dt.datetime
