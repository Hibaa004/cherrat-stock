# Environnement technique et dépendances

## 1. Environnement de développement et de test

| Élément | Version utilisée | Minimum conseillé |
|---|---|---|
| Système | Windows 11 Pro | Windows 10/11 64 bits, macOS ou Linux |
| RAM | — | 8 Go (llama3.2:3b) ; 16 Go pour llama3.1:8b |
| Disque libre | — | 15 Go (images Docker + modèles + dépendances Python) |
| Docker Desktop | 29.1 | 4.x avec WSL 2 (Windows) |
| Python | 3.11 | 3.11 (PaddlePaddle 2.6 ne supporte pas 3.13) |
| Node.js | 22.13 | 20 LTS |
| Ollama | installé sous Windows | dernière version |
| n8n | 2.16.1 (image `n8nio/n8n:latest`) | 1.x ou 2.x |
| Navigateur | Chrome / Edge | récent |

## 2. Services et ports

| Service | Lancement | Port | Rôle dans l'automatisation |
|---|---|---|---|
| n8n | Docker (`cherrat_n8n`) | 5678 | Orchestrateur du workflow |
| API FastAPI | `uvicorn` (PC hôte) | 8000 | Fournit les faits du stock et enregistre le rapport du jour (`/automation/...`) |
| PostgreSQL 16 | Docker (`cherrat_db`) | 5432 | Données du stock |
| Ollama | Application Windows | 11434 | LLM local qui rédige |
| Qdrant | Docker (`cherrat_qdrant`) | 6333 | Utilisé par le chatbot de l'application (pas par le workflow) |
| Frontend React | `npm run dev` | 5173 | Tableau de bord où le personnel lit le rapport |

Le conteneur n8n joint l'API et Ollama via `host.docker.internal` (déclaré par `extra_hosts` dans `docker-compose.yml`).

## 3. Dépendances

### Modèles d'IA (Ollama)

| Modèle | Taille | Usage |
|---|---|---|
| `llama3.2:3b` | 2,0 Go | Rédaction des actions (workflow) et réponses du chatbot |
| `nomic-embed-text` | 274 Mo | Embeddings du chatbot (RAG) |

### Nœuds n8n (tous intégrés à n8n, aucun nœud communautaire)

Schedule Trigger, Manual Trigger, Set (v3.4), HTTP Request (v4.2), Code (v2), IF (v2), Sticky Note.

### Backend Python (`backend/requirements.txt`)

| Paquet | Rôle |
|---|---|
| fastapi, uvicorn[standard] | API web |
| sqlalchemy ≥ 2.0, psycopg2-binary | Accès à PostgreSQL |
| pydantic-settings | Lecture du fichier `.env` |
| python-multipart | Envoi de formulaires et d'images |
| PyJWT, bcrypt | Authentification de l'application web |
| apscheduler 3.x, tzdata | Contrôle quotidien des expirations dans le backend |
| langchain, langchain-core, langchain-ollama, langchain-qdrant, qdrant-client | Chatbot RAG |
| numpy 1.26.4, paddlepaddle 2.6.2, paddleocr 2.7.3 | Lecture OCR des dates sur les boîtes |
| pytest, httpx | Tests automatiques (`python -m pytest`, 15 tests) |

### Frontend (`frontend/package.json`)

react 19, react-dom 19, react-router-dom 7, axios, tailwindcss 4 + @tailwindcss/vite, vite 8, oxlint.

### Images Docker

`postgres:16-alpine`, `qdrant/qdrant:latest`, `n8nio/n8n:latest`.

Aucun service en ligne n'est nécessaire une fois l'installation terminée : tout fonctionne hors connexion.

## 4. Vérifier l'environnement

```powershell
docker compose ps
ollama list
curl.exe http://localhost:8000/health
curl.exe -H "X-API-Key: <votre clé>" http://localhost:8000/automation/rapport
```

Le dernier appel doit renvoyer un JSON contenant `nb_alertes`. Les tests du backend se lancent depuis `backend` avec `python -m pytest` (ils n'ont besoin ni de PostgreSQL, ni d'Ollama).
