import datetime as dt
import uuid

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models import Lot, Medicament

NAMESPACE = uuid.UUID('6f1c2a52-0d0e-4c7e-9a43-2f1c0b7a9e11')
VECTOR_SIZE = 768  # dimension des vecteurs de nomic-embed-text
NL = chr(10)

_store = None

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            'Tu es l’assistant du stock de médicaments du Centre de Santé Cherrat. '
            'Réponds en français, de façon brève et précise, uniquement à partir du CONTEXTE fourni. '
            'Si l’information n’est pas dans le contexte, dis-le clairement et ne l’invente pas. '
            'Ne donne jamais de conseil médical, de diagnostic ni de posologie : '
            'renvoie vers le médecin ou le pharmacien.',
        ),
        ('human', 'CONTEXTE :' + NL +
         '{contexte}' + NL + NL + 'Question : {question}'),
    ]
)


def get_store() -> QdrantVectorStore:
    global _store
    if _store is None:
        client = QdrantClient(url=settings.QDRANT_URL)
        if not client.collection_exists(settings.QDRANT_COLLECTION):
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE, distance=Distance.COSINE),
            )
        embeddings = OllamaEmbeddings(
            model=settings.EMBED_MODEL, base_url=settings.OLLAMA_URL)
        _store = QdrantVectorStore(
            client=client, collection_name=settings.QDRANT_COLLECTION, embedding=embeddings)
    return _store


def point_id(med_id: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f'med-{med_id}'))


def fiche_medicament(med: Medicament) -> Document:
    aujourdhui = dt.date.today()
    total = sum(lot.quantite for lot in med.lots)
    utilisable = sum(
        lot.quantite for lot in med.lots if lot.date_expiration >= aujourdhui)
    lignes_lots = []
    for lot in sorted(med.lots, key=lambda x: x.date_expiration):
        if lot.quantite <= 0:
            continue
        jours = (lot.date_expiration - aujourdhui).days
        etat = 'EXPIRÉ' if jours < 0 else f'expire dans {jours} jours'
        lignes_lots.append(
            f'- Lot {lot.numero_lot} : {lot.quantite} unités, expiration le {lot.date_expiration.isoformat()} ({etat})'
        )
    if utilisable == 0:
        statut = 'RUPTURE DE STOCK'
    elif utilisable <= med.seuil_alerte:
        statut = 'STOCK BAS'
    else:
        statut = 'stock normal'
    parties = [
        f'Médicament : {med.nom}',
        f'DCI (substance) : {med.dci}',
        f'Forme : {med.forme}, dosage : {med.dosage}',
        f'Catégorie : {med.categorie}',
        f'Stock total : {total} unités (dont {utilisable} utilisables, non expirées)',
        f'Seuil d’alerte : {med.seuil_alerte} unités',
        f'Statut : {statut}',
        'Lots en stock :',
    ] + (lignes_lots or ['- aucun lot en stock'])
    return Document(page_content=NL.join(parties), metadata={'medicament_id': med.id, 'nom': med.nom})


def index_medicament(med_id: int) -> None:
    with SessionLocal() as db:
        med = db.get(Medicament, med_id)
        if med is None:
            return
        doc = fiche_medicament(med)
    get_store().add_documents([doc], ids=[point_id(med_id)])


def index_tout(db: Session) -> int:
    meds = db.scalars(select(Medicament)).all()
    if not meds:
        return 0
    docs = [fiche_medicament(m) for m in meds]
    get_store().add_documents(docs, ids=[point_id(m.id) for m in meds])
    return len(docs)


def synthese_globale(db: Session) -> str:
    aujourdhui = dt.date.today()
    meds = db.scalars(select(Medicament)).all()
    totaux = {m.id: m.stock_utilisable for m in meds}
    ruptures = [m.nom for m in meds if totaux[m.id] == 0]
    bas = [m.nom for m in meds if 0 < totaux[m.id] <= m.seuil_alerte]
    lots = db.scalars(
        select(Lot)
        .where(Lot.quantite > 0, Lot.date_expiration <= aujourdhui + dt.timedelta(days=90))
        .order_by(Lot.date_expiration)
    ).all()
    expirant = [
        f'{lot.medicament.nom} lot {lot.numero_lot} ({lot.quantite} unités) le {lot.date_expiration.isoformat()}'
        for lot in lots
    ]
    return NL.join(
        [
            f'Date du jour : {aujourdhui.isoformat()}',
            f'Nombre de médicaments au catalogue : {len(meds)}',
            'Médicaments en rupture : ' + (', '.join(ruptures) or 'aucun'),
            'Médicaments en stock bas : ' + (', '.join(bas) or 'aucun'),
            'Lots expirés ou expirant sous 90 jours : ' +
            ('; '.join(expirant) or 'aucun'),
        ]
    )


def poser_question(question: str, db: Session) -> dict:
    docs = get_store().as_retriever(search_kwargs={'k': 6}).invoke(question)
    contexte = synthese_globale(db) + NL + NL + \
        (NL + NL).join(d.page_content for d in docs)
    llm = ChatOllama(model=settings.LLM_MODEL,
                     base_url=settings.OLLAMA_URL, temperature=0)
    chaine = PROMPT | llm | StrOutputParser()
    reponse = chaine.invoke({'contexte': contexte, 'question': question})
    return {'reponse': reponse, 'sources': sorted({d.metadata.get('nom', '') for d in docs})}
