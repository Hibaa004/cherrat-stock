from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .routers import automation, auth, chat, medicaments, notifications, ocr, stock, users
from .services.notif_service import run_checks

scheduler = BackgroundScheduler(timezone='Africa/Casablanca')


def job_notifications():
    try:
        with SessionLocal() as db:
            run_checks(db)
    except Exception as e:
        print('Erreur vérification des expirations :', e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(job_notifications, 'cron', hour=8,
                      minute=0, id='verif_quotidienne', replace_existing=True)
    scheduler.start()
    job_notifications()  # une vérification immédiate au démarrage
    yield
    scheduler.shutdown()


app = FastAPI(title='Stock Médicaments - Centre de Santé Cherrat',
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Toute page servie en local (localhost ou 127.0.0.1, quel que soit le port :
    # Vite prend 5174, 5175… si le port 5173 est déjà occupé)
    allow_origin_regex=r'http://(localhost|127\.0\.0\.1)(:\d+)?',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

for module in (auth, users, medicaments, stock, ocr, notifications, chat, automation):
    app.include_router(module.router)


@app.get('/health')
def health():
    return {'status': 'ok'}
