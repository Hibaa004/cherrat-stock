# Cherrat Stock — gestion du stock de médicaments assistée par IA

Application web du Centre de Santé Cherrat :

- **Entrée de stock avec OCR** : photo de la boîte → OpenCV + PaddleOCR → date d'expiration proposée → validation humaine.
- **Sortie FEFO** : le lot qui expire le plus tôt est utilisé en premier.
- **Alertes** : contrôle quotidien à 8 h (APScheduler) des lots expirés, des lots qui expirent sous 30 ou 90 jours et des stocks bas. Les lots expirés ne comptent pas dans le stock utilisable.
- **Assistant IA (chatbot RAG)** : questions en langage naturel → Qdrant + Llama (Ollama, en local).
- **Automatisation n8n** : rapport quotidien par e-mail rédigé par l'IA → voir [automatisation/README.md](automatisation/README.md).

## Structure

```text
cherrat-stock/
├── docker-compose.yml        PostgreSQL, Qdrant, n8n
├── backend/                  API FastAPI (Python 3.11)
│   ├── .env.example          modèle de configuration
│   ├── app/routers/          auth, users, medicaments, stock, ocr, notifications, chat, automation
│   ├── app/services/         ocr_service, rag_service, notif_service
│   └── tests/                tests pytest (SQLite en mémoire)
├── frontend/                 React + Vite + Tailwind
└── automatisation/           workflow n8n + documentation du livrable « Automatisation »
```

## Démarrage rapide

```powershell
docker compose up -d
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

```powershell
cd backend
Copy-Item .env.example .env
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

- Application : <http://localhost:5173>
- Documentation de l'API : <http://localhost:8000/docs>
- n8n : <http://localhost:5678>

## Comptes de démonstration

| Rôle | E-mail | Mot de passe | Droits |
|---|---|---|---|
| Major | major@cherrat.ma | Major123! | Tout : médicaments, entrées, sorties, ajustements, utilisateurs, réindexation |
| Docteur | docteur@cherrat.ma | Docteur123! | Consultation, tableau de bord, assistant IA |
| Infirmière | infirmiere@cherrat.ma | Infirmier123! | Entrées (OCR), sorties, assistant IA |

## Tests

```powershell
cd backend
python -m pytest
```
