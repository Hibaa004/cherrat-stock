from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Role, User
from ..services.rag_service import index_tout, poser_question

router = APIRouter(prefix='/chat', tags=['assistant IA'])


class QuestionIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@router.post('')
def poser(body: QuestionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return poser_question(body.question, db)
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f'Assistant IA indisponible (Ollama et Qdrant démarrés ?) : {e}')


@router.post('/reindex')
def reindexer(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.major))):
    try:
        return {'fiches_indexees': index_tout(db)}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f'Indexation impossible : {e}')
