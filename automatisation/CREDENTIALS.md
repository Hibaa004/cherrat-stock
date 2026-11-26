# Registre des credentials et des variables

Aucun secret n'est stocké dans `workflow_n8n_cherrat.json` : n8n chiffre les credentials dans son volume `n8n_data`. Sur une nouvelle machine, il faut les recréer en suivant ce document.

## 1. Credentials n8n

| Nom dans n8n | Service | Type de credential n8n | Identifiant nécessaire | Droits accordés | Utilisé par le nœud |
|---|---|---|---|---|---|
| **Cherrat API Key** | API FastAPI cherrat-stock | Header Auth | Clé `AUTOMATION_API_KEY` du fichier `backend/.env` | Lecture seule de `GET /automation/rapport`, et rien d'autre (pas de connexion utilisateur, pas d'écriture) | API - Rapport du stock |
| **SMTP Cherrat** | Gmail (ou tout serveur SMTP) | SMTP | Adresse Gmail + **mot de passe d'application** (16 caractères) | Envoi d'e-mails depuis ce compte | Envoyer l'e-mail |
| *(aucun)* | Ollama local | — | Aucun : API locale sans authentification | — | Ollama - Rédiger les actions |

### Créer « Cherrat API Key »

1. Générez une clé : `python -c "import secrets;print(secrets.token_urlsafe(32))"`.
2. Mettez-la dans `backend/.env` : `AUTOMATION_API_KEY=<la clé>`, puis redémarrez uvicorn.
3. Dans n8n : **Credentials → Add credential → Header Auth**.
   - Name : `X-API-Key`
   - Value : la même clé
   - Nom du credential : `Cherrat API Key`
4. Dans le nœud *API - Rapport du stock*, sélectionnez ce credential.
5. Vérification : exécutez seulement ce nœud, il doit renvoyer un JSON avec `nb_alertes`.

### Créer « SMTP Cherrat » (Gmail)

1. Sur le compte Google expéditeur, activez la **validation en deux étapes** (Compte Google → Sécurité).
2. Ouvrez **Compte Google → Sécurité → Mots de passe des applications**, créez un mot de passe nommé « n8n Cherrat » et copiez les 16 caractères.
3. Dans n8n : **Credentials → Add credential → SMTP**.
   - User : l'adresse Gmail
   - Password : le mot de passe d'application (pas le mot de passe Gmail)
   - Host : `smtp.gmail.com`
   - Port : `465`
   - SSL/TLS : activé
   - Nom du credential : `SMTP Cherrat`
4. Dans le nœud *Envoyer l'e-mail*, sélectionnez ce credential.
5. `EMAIL_FROM` (nœud *Configuration*) doit être la même adresse Gmail.

> Autre fournisseur : Outlook utilise `smtp-mail.outlook.com`, port `587`, SSL désactivé (STARTTLS).
>
> Test sans vraie boîte mail : lancez `docker compose --profile test up -d mailpit`, puis utilisez Host `host.docker.internal`, Port `1025`, User et Password vides, SSL/TLS désactivé. Les e-mails s'affichent sur http://localhost:8025.

## 2. Variables du nœud « Configuration » (n8n)

| Variable | Valeur par défaut | Rôle | À modifier ? |
|---|---|---|---|
| `API_URL` | `http://host.docker.internal:8000` | Adresse du backend vue depuis le conteneur n8n | Seulement si n8n tourne hors Docker (`http://localhost:8000`) ou sur un autre PC |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Adresse d'Ollama | Idem |
| `LLM_MODEL` | `llama3.2:3b` | Modèle qui rédige | Oui si vous avez téléchargé un autre modèle (`llama3.1:8b`) |
| `EMAIL_FROM` | `votre.adresse@gmail.com` | Expéditeur | **Oui** |
| `EMAIL_TO` | `major@exemple.ma, docteur@exemple.ma` | Destinataires, séparés par des virgules | **Oui** |

## 3. Variables du backend (`backend/.env`)

Modèle complet : `backend/.env.example`.

| Variable | Exemple | Secret ? | Rôle |
|---|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://cherrat:cherrat_pwd@localhost:5432/cherrat_stock` | Oui (mot de passe BD) | Connexion PostgreSQL ; doit correspondre à `docker-compose.yml` |
| `SECRET_KEY` | 48 caractères aléatoires | **Oui** | Signature des jetons JWT de l'application web |
| `QDRANT_URL` | `http://localhost:6333` | Non | Base vectorielle du chatbot |
| `OLLAMA_URL` | `http://localhost:11434` | Non | LLM local du chatbot |
| `LLM_MODEL` / `EMBED_MODEL` | `llama3.2:3b` / `nomic-embed-text` | Non | Modèles du chatbot |
| `AUTOMATION_API_KEY` | 32 caractères aléatoires | **Oui** | Clé partagée avec n8n ; vide = route `/automation` désactivée (503) |
| `SMTP_*`, `ALERT_EMAILS` | *(vide)* | Oui | Facultatif : e-mails envoyés directement par le backend, indépendamment de n8n |

## 4. Variables des conteneurs (`docker-compose.yml`)

| Service | Variable | Valeur | Rôle |
|---|---|---|---|
| db | `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `cherrat` / `cherrat_pwd` / `cherrat_stock` | Compte de la base (à changer en production) |
| n8n | `GENERIC_TIMEZONE`, `TZ` | `Africa/Casablanca` | Pour que « 8 h 15 » soit l'heure locale |
| n8n | `N8N_SECURE_COOKIE` | `false` | Autorise l'accès en HTTP sur `localhost` |

## 5. Bonnes pratiques

- Ne jamais commiter `backend/.env` (déjà exclu par `.gitignore`) ; ne partager que `.env.example`.
- Une clé par machine : pour le test de transférabilité, votre ami génère **sa propre** `AUTOMATION_API_KEY` et utilise **son propre** compte Gmail.
- Si une clé fuit : générez-en une nouvelle dans `.env`, redémarrez uvicorn, mettez à jour le credential n8n. Pour Gmail, révoquez le mot de passe d'application.
