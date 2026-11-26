# Registre des credentials et des variables

Aucun secret n'est stocké dans `workflow_n8n_cherrat.json` : n8n chiffre les credentials dans son volume `n8n_data`. Sur une nouvelle machine, il faut les recréer en suivant ce document.

## 1. Credentials n8n

| Nom dans n8n | Service | Type de credential n8n | Identifiant nécessaire | Droits accordés | Utilisé par les nœuds |
|---|---|---|---|---|---|
| **Cherrat API Key** | API FastAPI cherrat-stock | Header Auth | Clé `AUTOMATION_API_KEY` du fichier `backend/.env` | Deux routes seulement : lire les faits du stock (`GET /automation/rapport`) et déposer le rapport du jour (`POST /automation/rapport-ia`). Aucun accès aux comptes, aux médicaments ni aux mouvements | API - Rapport du stock, API - Publier le rapport |
| *(aucun)* | Ollama local | — | Aucun : API locale sans authentification | — | Ollama - Rédiger les actions |

Un seul credential est donc nécessaire. Aucun service extérieur (Gmail, cloud…) n'est utilisé : toutes les données restent sur le PC du centre.

### Créer « Cherrat API Key »

1. Générez une clé : `python -c "import secrets;print(secrets.token_urlsafe(32))"`.
2. Mettez-la dans `backend/.env` : `AUTOMATION_API_KEY=<la clé>`, puis redémarrez uvicorn.
3. Dans n8n : **Credentials → Add credential → Header Auth**.
   - Name : `X-API-Key`
   - Value : la même clé
   - Nom du credential : `Cherrat API Key`
4. Sélectionnez ce credential dans les nœuds *API - Rapport du stock* et *API - Publier le rapport*.
5. Vérification : exécutez seulement le nœud *API - Rapport du stock* ; il doit renvoyer un JSON avec `nb_alertes`.

## 2. Variables du nœud « Configuration » (n8n)

| Variable | Valeur par défaut | Rôle | À modifier ? |
|---|---|---|---|
| `API_URL` | `http://host.docker.internal:8000` | Adresse du backend vue depuis le conteneur n8n | Seulement si n8n tourne hors Docker (`http://localhost:8000`) ou sur un autre PC |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Adresse d'Ollama | Idem |
| `LLM_MODEL` | `llama3.2:3b` | Modèle qui rédige | Oui si vous avez téléchargé un autre modèle (`llama3.1:8b`) |

## 3. Variables du backend (`backend/.env`)

Modèle complet : `backend/.env.example`.

| Variable | Exemple | Secret ? | Rôle |
|---|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://cherrat:cherrat_pwd@localhost:5432/cherrat_stock` | Oui (mot de passe BD) | Connexion PostgreSQL ; doit correspondre à `docker-compose.yml` |
| `SECRET_KEY` | 48 caractères aléatoires | **Oui** | Signature des jetons JWT de l'application web |
| `QDRANT_URL` | `http://localhost:6333` | Non | Base vectorielle du chatbot |
| `OLLAMA_URL` | `http://localhost:11434` | Non | LLM local du chatbot |
| `LLM_MODEL` / `EMBED_MODEL` | `llama3.2:3b` / `nomic-embed-text` | Non | Modèles du chatbot |
| `AUTOMATION_API_KEY` | 32 caractères aléatoires | **Oui** | Clé partagée avec n8n ; vide = routes `/automation` désactivées (503) |

## 4. Variables des conteneurs (`docker-compose.yml`)

| Service | Variable | Valeur | Rôle |
|---|---|---|---|
| db | `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `cherrat` / `cherrat_pwd` / `cherrat_stock` | Compte de la base (à changer en production) |
| n8n | `GENERIC_TIMEZONE`, `TZ` | `Africa/Casablanca` | Pour que « 8 h 15 » soit l'heure locale |
| n8n | `N8N_SECURE_COOKIE` | `false` | Autorise l'accès en HTTP sur `localhost` |

## 5. Bonnes pratiques

- Ne jamais commiter `backend/.env` (déjà exclu par `.gitignore`) ; ne partager que `.env.example`.
- Une clé par machine : pour le test de transférabilité, votre ami génère **sa propre** `AUTOMATION_API_KEY`.
- Si la clé fuit : générez-en une nouvelle dans `.env`, redémarrez uvicorn, puis mettez à jour le credential n8n.
