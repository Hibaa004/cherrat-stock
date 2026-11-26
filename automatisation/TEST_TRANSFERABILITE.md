# Test de transférabilité

**Objectif :** vérifier qu'une personne qui n'a pas participé au projet peut installer et faire fonctionner l'automatisation sur sa propre machine, **avec les seuls documents fournis**, sans demander d'aide à l'auteur.

## 1. Préparer le test

À envoyer à l'ami testeur :

- le dépôt (lien Git ou archive `.zip` **sans** `backend/.env`, `node_modules`, `.venv`) ;
- `automatisation/README.md`, `ENVIRONNEMENT.md`, `CREDENTIALS.md`, `architecture.svg`, `workflow_n8n_cherrat.json`.

Consignes au testeur :

1. Suivre le README dans l'ordre, sans me contacter.
2. Chronométrer chaque étape et noter chaque blocage (message d'erreur exact, capture d'écran).
3. N'appeler à l'aide qu'après 15 minutes bloqué sur une même étape, et noter ce moment comme « intervention ».
4. Utiliser son propre compte Gmail et générer sa propre clé API.

## 2. Fiche de test (à remplir par le testeur)

| Champ | Réponse |
|---|---|
| Prénom du testeur / formation | |
| Date | |
| Machine (OS, RAM, CPU/GPU) | |
| Outils déjà installés avant le test | |

| Étape du README | Durée | Réussie seule ? (oui / non / avec aide) | Problème rencontré | Solution trouvée |
|---|---|---|---|---|
| 1. Récupérer le projet | | | | |
| 2. Docker (PostgreSQL, Qdrant, n8n) | | | | |
| 3. Modèles Ollama | | | | |
| 4. Backend (.env, venv, seed, uvicorn) | | | | |
| 5. Frontend (facultatif) | | | | |
| 6. Import du workflow + credentials | | | | |
| Premier e-mail reçu | | | | |
| Cas « Ollama arrêté » (repli) | | | | |

Questions au testeur, avec une note de 1 à 5 :

- Les documents étaient-ils clairs ?
- Le registre des credentials était-il suffisant pour créer les connexions ?
- Le schéma d'architecture vous a-t-il aidé à comprendre le workflow ?
- Le contenu de l'e-mail est-il utile pour un Major ? Que changeriez-vous ?
- Quelle étape a été la plus difficile, et pourquoi ?

## 3. Indicateurs de réussite

| Indicateur | Objectif |
|---|---|
| E-mail reçu sur la machine du testeur | Oui |
| Nombre d'interventions de l'auteur | 0 (au plus 1) |
| Durée totale de l'installation (hors téléchargements) | Moins de 60 min |
| Étapes réussies sans aide | Au moins 6 sur 8 |

## 4. Réflexion sur l'expérience (à rédiger par vous après le test)

Rédigez cette partie avec ce qui s'est **réellement** passé. Pistes :

- **Ce qui a fonctionné** : quelles étapes le testeur a réussies seul, et grâce à quel élément de la documentation ?
- **Ce qui a bloqué** : erreurs rencontrées, hypothèses implicites que vous n'aviez pas écrites (un outil supposé déjà installé, Docker non démarré, pare-feu, Gmail sans validation en deux étapes…).
- **Corrections apportées** : ce que vous avez ajouté ou modifié dans le README ou le registre après le test (indiquez la ligne ou la section).
- **Dépendance à l'environnement** : qu'est-ce qui dépend de votre machine (GPU, RAM, Windows, ports) ? Comment le rendre plus portable (tout dans Docker, modèle plus petit…) ?
- **Bilan** : l'automatisation est-elle vraiment transférable ? Combien de temps faudrait-il à un centre de santé pour l'adopter, et qui devrait l'installer ?

Points de vigilance connus avant le test, à vérifier pendant celui-ci :

1. L'accès du conteneur n8n à l'API et à Ollama du PC hôte (`--host 0.0.0.0`, `OLLAMA_HOST`, pare-feu Windows).
2. La création du mot de passe d'application Gmail (nécessite la validation en deux étapes).
3. Le temps de la première réponse d'Ollama sur un PC sans GPU.
4. L'installation de PaddleOCR (Python 3.11 obligatoire). Elle n'est pas nécessaire au workflow, mais elle fait partie de `requirements.txt`.
