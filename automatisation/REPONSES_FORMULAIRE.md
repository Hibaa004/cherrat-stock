# Réponses au formulaire « Projet d'automatisation — Generative AI & Everyday Tasks | EMSI »

Réponses prêtes à copier-coller, dans l'ordre du formulaire (9 pages). Elles reprennent le guide Word et décrivent la version réellement développée et testée.

- **⚠ À COMPLÉTER** : information que toi seule connais (nom, liens, résultats d'un test pas encore fait).
- ☑ : case à cocher.
- Les durées « avant/après » sont des **estimations** (le guide le dit aussi). Si tu chronomètres avec le Major, remplace-les par tes mesures.

---

## Page 1 — 0. Identification du projet

**Titre du projet d'automatisation**

> Cherrat Stock : rapport quotidien du stock de médicaments rédigé par une IA locale (n8n + Ollama) — Centre de Santé Cherrat

**Organisation du travail**
Travail en binôme

**Nom et prénom — Membre 1**
Hiba KAAOUACH

**Nom et prénom — Membre 2** (facultatif)
Oumaima BOUMAZOUED

**Numéro du document partagé**
6

**Lien du prototype / workflow fonctionnel**

> https://github.com/Hibaa004/cherrat-stock

**Prototype / Workflow / Autres documents** (envoi de fichiers)

> À téléverser : `automatisation/workflow_n8n_cherrat.json`, `automatisation/architecture.svg` (ou sa version PNG), le guide Word rempli.

---

## STEP 1 — DATA & PLANNING

**1.1 — Quel problème ou quelle tâche avez-vous choisi(e) ?**

> La gestion manuelle du stock de médicaments au Centre de Santé Cherrat, et en particulier le contrôle quotidien du stock : repérer les lots périmés à retirer, les lots qui vont expirer, les ruptures et les stocks bas, puis dire à l'équipe quoi faire en priorité. Aujourd'hui, ce contrôle repose sur un registre papier ou un fichier Excel et sur la lecture des dates « EXP » boîte par boîte. En pratique, il n'est pas fait tous les jours : un lot périmé ou une rupture est découvert trop tard, parfois devant le patient.
>
> L'automatisation présentée est un workflow n8n qui, chaque matin à 8 h 15, interroge l'application de gestion du stock (cherrat-stock), fait rédiger la liste des actions du jour par un LLM local (Llama 3.2 via Ollama) et publie ce rapport en haut du tableau de bord du personnel.

**1.2 — Qui réalise actuellement cette tâche ?**

> Le Major (infirmier major, responsable de la pharmacie du centre) fait l'essentiel du travail : réceptions, contrôle des dates, inventaires et réponses aux questions de disponibilité. Les Infirmiers effectuent les sorties pour les patients et posent des questions de disponibilité. Le Docteur consulte le stock avant de prescrire et valide les décisions importantes (commandes, retraits).

**1.3 — Comment la tâche est-elle réalisée aujourd'hui ?**

> Registre papier et/ou fichier Excel. Le Major lit à l'œil nu les dates « EXP » imprimées ou gravées sur chaque boîte, recopie à la main le numéro de lot et la date, compte physiquement les boîtes lors des inventaires et parcourt le registre pour trouver les produits proches de l'expiration ou sous le seuil de commande. Il n'existe aucune alerte automatique. Les questions (« est-ce qu'il nous reste… ? ») lui sont posées oralement ou par téléphone, et il va vérifier sur l'étagère ou dans le registre.

**1.4 — À quelle fréquence la tâche est-elle réalisée ?**

> ☑ Une fois par jour
>
> (Le contrôle devrait être quotidien ; en pratique il est souvent fait une fois par mois ou à l'inventaire. Les sorties et les questions de disponibilité, elles, ont lieu plusieurs fois par jour.)

**1.5 — Combien de temps prend une exécution manuelle ?**

> Contrôle complet des dates et des seuils : environ 3 heures par contrôle (quelques centaines de boîtes) ; enregistrement d'un lot reçu : environ 90 secondes ; réponse à une question de disponibilité : environ 3 minutes. (Estimations.)

**1.6 — Pourquoi cette tâche est-elle répétitive, difficile ou inefficace ?**

> (1) La même lecture de date est répétée sur des centaines de boîtes. (2) Les formats varient (05/2027, 2027-05, MAY 27, EXP 31.05.27, caractères gravés peu lisibles), d'où des erreurs de recopie. (3) Il n'y a aucune alerte : un lot périmé n'est découvert que si quelqu'un le cherche. (4) Les ruptures sont découvertes au moment de servir le patient. (5) L'information dépend d'une seule personne, le Major : en son absence, personne ne sait quoi faire en priorité. Comme le contrôle est long, il est repoussé, et c'est justement ce qui crée le risque.

**1.7 — À quoi ressemblerait une réussite ? Quels résultats permettraient de le vérifier ?**

> - Chaque matin, sans action humaine, un rapport du jour est affiché sur le tableau de bord (vérifiable dans l'onglet Executions de n8n et par la date du rapport).
> - Zéro lot périmé ou rupture non signalé : chaque alerte calculée par l'application apparaît dans le rapport (comparaison rapport ↔ données brutes affichées sous le rapport).
> - Aucun chiffre inventé : la phrase de synthèse et les quantités correspondent exactement aux données de la base.
> - Le rapport est publié même si l'IA est en panne (branche de repli).
> - Le temps de contrôle passe d'environ 3 h par contrôle à quelques minutes de lecture et de traitement des alertes.

---

## STEP 2 — DECOMPOSITION & ORGANIZATION

**2.1 — Inputs : quelles données ou informations sont nécessaires ?**

> - Les données du stock dans PostgreSQL : médicaments (nom, DCI, dosage, seuil d'alerte), lots (numéro, quantité, date d'expiration), notifications non lues.
> - La date du jour.
> - Pour l'application en amont : photos des boîtes (zone LOT / EXP), saisies du personnel (entrées, sorties, motifs).
> - Configuration du workflow : adresse de l'API, adresse d'Ollama, nom du modèle, clé d'API (credential n8n « Cherrat API Key »).

**2.2 — Processing steps : quelles sont les étapes de traitement ?**

> 1. Déclenchement chaque jour à 8 h 15 (Schedule Trigger), ou manuellement pour la démonstration.
> 2. Lecture de la configuration (adresses de l'API et d'Ollama, modèle).
> 3. Appel `GET /automation/rapport` (en-tête X-API-Key) : le backend calcule les faits à partir de PostgreSQL — lots expirés, lots expirant sous 30 et 90 jours, ruptures, stocks bas, nombre d'alertes.
> 4. Nœud Code « Préparer le prompt » : met les faits en texte, calcule la phrase de synthèse chiffrée et construit le prompt.
> 5. Nœud IF « Des alertes ? » : sans alerte, on n'appelle pas l'IA et on prépare un rapport « aucune alerte ».
> 6. Appel à Ollama (`POST /api/generate`, llama3.2:3b, température 0,1) : rédaction de la liste d'actions.
> 7. Mise en forme du rapport (synthèse + actions + faits vérifiables), ou branche de repli si Ollama ne répond pas.
> 8. Publication `POST /automation/rapport-ia` : le rapport du jour est enregistré dans la table rapports_ia (une nouvelle exécution le même jour le remplace).
> 9. Le tableau de bord de chaque utilisateur affiche la carte « Rapport du jour (IA) ».

**2.3 — Decisions : quelles décisions ou conditions interviennent ?**

> - Un lot est-il expiré, expire-t-il sous 30 jours ou entre 31 et 90 jours ?
> - Le stock utilisable (lots non expirés) est-il à zéro (rupture) ou sous le seuil d'alerte (stock bas) ?
> - Y a-t-il au moins une alerte ? Sinon, pas d'appel à l'IA.
> - Ollama a-t-il répondu à temps ? Sinon, branche de repli sans IA.
> - Un rapport existe-t-il déjà pour aujourd'hui ? Si oui, il est remplacé.
> - Côté humain : quels lots retirer, quoi commander, dans quel ordre.

**2.4 — Outputs : quels résultats doivent être produits ?**

> Un rapport quotidien enregistré dans l'application et affiché en haut du tableau de bord (Docteur, Major, Infirmier) : une phrase de synthèse chiffrée (« 4 alerte(s) à traiter aujourd'hui : 1 lot expiré, 1 lot expirant sous 30 jours, 1 rupture, 1 stock bas »), la liste des actions prioritaires rédigée par l'IA, la source (IA, repli ou sans alerte) et un bouton qui affiche les données calculées par l'application pour vérifier. Bordure de couleur selon l'état (vert : aucune alerte ; orange : repli).

**2.5 — Constraints : quelles contraintes doivent être respectées ?**

> - Données de santé : tout tourne en local (Ollama, n8n dans Docker), aucune donnée n'est envoyée à un service cloud, aucune donnée patient dans le prompt.
> - PC modeste (8 à 16 Go de RAM) : modèle léger llama3.2:3b.
> - Exactitude : aucune quantité, date ou nombre d'alertes ne doit être inventé.
> - Langue : français ; personnel peu habitué à l'informatique : rapport court (120 mots maximum), affiché là où il regarde déjà.
> - Pas de conseil médical, de prescription ou de posologie.
> - Robustesse : le rapport doit être publié même si l'IA est arrêtée.
> - Sécurité : l'API d'automatisation est protégée par une clé (X-API-Key) stockée dans un credential n8n, jamais dans le JSON exporté.
> - Budget nul : outils gratuits et open source.

**2.6 — Human actions : quelles actions sont actuellement réalisées par une personne ?**

> Parcourir le registre et les étagères ; lire les dates d'expiration ; repérer les lots périmés ou proches de l'expiration ; repérer les ruptures et stocks bas ; décider quoi retirer et quoi commander ; prévenir le Docteur et les infirmiers ; retirer physiquement les lots périmés ; passer les commandes.

**2.7 — Repetitive operations : quelles opérations sont répétées ?**

> La lecture des dates d'expiration boîte par boîte, le calcul des jours restants, la comparaison des quantités avec les seuils, la recherche des produits proches de l'expiration dans le registre, la rédaction de la liste des choses à faire et les réponses aux mêmes questions de disponibilité.

**2.8 — Possible failure cases : dans quels cas le processus peut-il échouer ?**

> - Ollama arrêté ou trop lent → pas de liste rédigée par l'IA (géré : branche de repli).
> - Le LLM se trompe dans un chiffre ou invente une ligne (observé : « 2 problèmes » au lieu de 4).
> - Backend arrêté ou injoignable depuis le conteneur n8n (uvicorn lancé sans `--host 0.0.0.0`) → le workflow échoue.
> - Mauvaise clé API → erreur 401, rapport non mis à jour.
> - PC éteint à 8 h 15 ou workflow désactivé → pas de rapport du jour (le tableau de bord l'indique).
> - Données fausses à la source (entrée mal saisie, mauvaise date lue par l'OCR et non corrigée).

**2.9 — Que choisissez-vous d'automatiser, et pourquoi ?**

> - Le contrôle quotidien des dates et des seuils (calculé par le backend) : c'est une opération répétitive, longue, et exacte par nature.
> - La rédaction de la liste d'actions du jour (LLM) : transformer des listes de faits en consignes claires et ordonnées est une tâche de langage.
> - La publication sur le tableau de bord : l'information arrive là où le personnel regarde déjà, sans e-mail à ouvrir.
> - Le déclenchement chaque matin : le contrôle n'est plus repoussé.
>   Ces opérations sont répétitives, sans décision médicale, et leur résultat est vérifiable.

**2.10 — Que doit-on maintenir sous contrôle humain (HITL), et pourquoi ?**

> - La vérification du rapport avec les données calculées (bouton sous le rapport) : le LLM peut se tromper.
> - Le retrait physique des lots périmés et sa confirmation dans l'application (ajustement par le Major).
> - Les décisions de commande, de prescription et de substitution : la responsabilité médicale reste humaine.
> - La validation des informations lues par l'OCR à la réception (champs surlignés en jaune) : une date erronée est un risque pour le patient.
>   L'automatisation informe et alerte ; elle ne décide pas.

**2.11 — Lien vers un schéma du processus / diagramme de décomposition** (facultatif)

> https://github.com/Hibaa004/cherrat-stock/blob/main/automatisation/architecture.svg

---

## STEP 3 — ALGORITHMIC STRUCTURING

**3.1 — Quel(s) composant(s) ou outil(s) d'IA utilisez-vous ?**

> - Llama 3.2 3B exécuté en local par Ollama (API `POST /api/generate`, température 0,1) : rédaction de la liste d'actions du rapport n8n.
> - Dans l'application : le même LLM pour l'assistant RAG (LangChain + base vectorielle Qdrant + embeddings nomic-embed-text), et PaddleOCR (IA de vision, non générative) pour lire les boîtes.
> - Orchestration : n8n 2.16.1 (Schedule Trigger, Set, HTTP Request avec Header Auth, Code JavaScript, IF).
>   Tout le reste (dates, seuils, comptes, FEFO) est du code déterministe.

**3.2 — Pourquoi l'IA générative est-elle appropriée pour cette tâche ?**

> Les faits sont des listes brutes (lots, quantités, jours restants). Le personnel a besoin de consignes courtes, ordonnées par urgence et formulées en français (« retirer le lot SER-100… », « commander… »). Un gabarit fixe produit des phrases rigides et doit être réécrit pour chaque cas ; un LLM rédige naturellement un texte adapté au nombre et au type d'alertes du jour. En revanche, l'IA n'est pas utilisée pour calculer : la détection des alertes et la phrase chiffrée sont faites par le code, car le modèle 3B s'est trompé en comptant. Le modèle tourne en local, ce qui protège des données de santé.

**3.3 — Quel(s) prompt(s) utilisez-vous ?**

> **Prompt du workflow n8n** (nœud « Préparer le prompt ») :
>
> ```
> Tu es l'assistant de gestion du stock de médicaments du Centre de Santé Cherrat.
> Rédige en français la liste des actions du jour pour le Docteur et le Major, à partir des FAITS ci-dessous.
>
> Règles :
> - Utilise UNIQUEMENT les faits fournis. N'invente aucun médicament, aucune quantité, aucune date.
> - Écris uniquement une liste à puces d'actions (une ligne par action, commençant par "- "), de la plus urgente à la moins urgente :
>   1) retirer les lots expirés, 2) utiliser en premier les lots qui expirent sous 30 jours, 3) commander les médicaments en rupture, 4) commander les médicaments en stock bas.
> - Chaque ligne cite le médicament, le numéro de lot s'il existe et la quantité, recopiés exactement depuis les faits.
> - Ne mentionne pas les catégories vides. Pas d'introduction ni de conclusion.
> - Aucun conseil médical, de prescription ou de posologie.
> - 120 mots maximum, texte simple, sans tableau ni mise en forme Markdown (pas de ** ni de #).
>
> FAITS :
> ${faits}
> ```
>
> Variable : `${faits}` = texte construit par le code à partir du JSON de l'API (date, nombre de médicaments, et une section par catégorie : lots expirés, lots sous 30 jours, ruptures, stocks bas, lots entre 31 et 90 jours).
>
> **Prompt de l'assistant RAG de l'application** (`backend/app/services/rag_service.py`, température 0) :
>
> ```
> [system] Tu es l'assistant du stock de médicaments du Centre de Santé Cherrat. Réponds en français, de façon brève et précise, uniquement à partir du CONTEXTE fourni. Si l'information n'est pas dans le contexte, dis-le clairement et ne l'invente pas. Ne donne jamais de conseil médical, de diagnostic ni de posologie : renvoie vers le médecin ou le pharmacien.
> [human] CONTEXTE : {contexte}   Question : {question}
> ```

**3.4 — Quelles informations sont transmises au modèle ?**

> Uniquement des faits agrégés sur le stock, calculés par l'application, au format texte : date du rapport ; nombre de médicaments au catalogue ; pour chaque lot concerné : médicament, numéro de lot, quantité, date d'expiration et jours restants (ou « expiré depuis N jours ») ; pour chaque médicament en rupture ou en stock bas : stock utilisable et seuil d'alerte. Les données arrivent de l'API en JSON (`GET /automation/rapport`) et sont converties en texte par le nœud Code. Aucune donnée de patient, aucun nom d'utilisateur.

**3.5 — Quel résultat / output attendez-vous du modèle ?**

> Une liste à puces en texte simple (une action par ligne, commençant par « - »), en français, 120 mots maximum, ordonnée par urgence : retirer les lots expirés, utiliser en premier les lots sous 30 jours, commander les ruptures, puis les stocks bas. Critères de qualité : chaque ligne cite le médicament, le lot et la quantité exactement comme dans les faits ; aucune catégorie vide ; pas d'introduction, de Markdown ni de conseil médical. Le modèle ne produit que cette liste : la synthèse chiffrée est écrite par le code.

**3.6 — Le traitement comporte-t-il plusieurs étapes ? Décrivez-les.**

> Oui :
>
> 1. Calcul des faits par le backend (SQL + règles Python).
> 2. Mise en texte des faits, calcul de la synthèse et construction du prompt (nœud Code).
> 3. Condition : alertes ou non (IF).
> 4. Génération de la liste d'actions par Llama (Ollama).
> 5. Assemblage du rapport : synthèse (code) + actions (IA) + faits (code) ; ou repli sans IA en cas d'erreur.
> 6. Publication par l'API et affichage sur le tableau de bord.

**3.7 — Quelles opérations sont déterministes et ne nécessitent pas d'IA ?**

> La majorité : déclenchement à heure fixe, lecture de la base, calcul du stock utilisable (lots non expirés), calcul des jours restants, classement expiré / ≤ 30 j / ≤ 90 j, détection des ruptures et stocks bas, comptage des alertes, phrase de synthèse chiffrée, condition IF, branche de repli, authentification par clé, enregistrement et affichage du rapport. Dans l'application : prétraitement OpenCV, expressions régulières des dates et des lots, choix du lot à sortir (FEFO), notifications et droits par rôle. Une date ou une quantité doit être exacte et reproductible : c'est le rôle du code, pas du LLM.

**3.8 — Où et comment les validations sont-elles effectuées ?**

> - API : clé `X-API-Key` comparée en temps constant (401 si fausse, 503 si non configurée) ; schéma Pydantic du rapport publié (champs obligatoires, `source` limitée à ia / repli / sans_alerte, sinon 422).
> - n8n : l'appel à l'API réessaie 3 fois ; le nœud Ollama a une sortie d'erreur (délai de 180 s) qui mène à la branche de repli.
> - Cohérence : les chiffres de la synthèse sont calculés par le code ; le prompt interdit d'inventer et impose de recopier exactement ; les faits bruts sont affichés sous le rapport pour comparaison.
> - Humain : le Major compare les actions aux données calculées avant d'agir.
> - Tests automatiques (pytest, 21 tests) : rapport, publication, clé API, FEFO, OCR.

**3.9 — À quels moments l'humain intervient-il dans le workflow ?**

> - Après la publication : lecture du rapport et vérification avec les données calculées (bouton « données calculées »).
> - Décision : retrait des lots expirés, sortie en priorité des lots proches de l'expiration, commandes ; le Docteur valide les décisions importantes.
> - Correction : ajustement des quantités dans l'application après le retrait physique ; correction des données à la source si une alerte est fausse.
> - En amont : validation des champs lus par l'OCR à chaque réception.
> - Supervision : en cas de « pas de rapport aujourd'hui », vérification de n8n (onglet Executions).

**3.10 — Lien vers le diagramme d'architecture / workflow** (facultatif)

> https://github.com/Hibaa004/cherrat-stock/blob/main/automatisation/architecture.svg

---

## STEP 4 — GENERALIZATION & TRANSFER

**4.1 — Quel(s) scénario(s) de transfert avez-vous choisi(s) ?**

> ☑ Une autre tâche
> ☑ Un autre contexte professionnel
> ☑ Une autre langue
> ☑ Une autre organisation

**4.2 — Décrivez le contexte initial et le scénario de transfert choisi.**

> Contexte initial : rapport quotidien du stock de médicaments du Centre de Santé Cherrat (lots expirés, lots proches de l'expiration, ruptures, stocks bas), rédigé par un LLM local et affiché sur le tableau de bord.
>
> Transfert 1 (autre organisation, autre tâche) : suivi des vaccins et consommables (seringues, gants, réactifs) dans un hôpital provincial ou une pharmacie d'officine, avec la chaîne du froid.
> Transfert 2 (autre contexte professionnel) : suivi des dates limites de consommation (DLC) dans une épicerie ou un supermarché : rapport du matin « produits à mettre en promotion, à retirer, à commander ».
> Transfert 3 (autre langue) : rapport et questions en arabe ou en darija pour le personnel.

**4.3 — Quels éléments de l'automatisation restent inchangés ?**

> - L'architecture du workflow : déclencheur planifié → API qui calcule les faits → nœud Code → IF → LLM local → mise en forme → publication sur le tableau de bord, avec la branche de repli.
> - Le principe « le code calcule, l'IA rédige » et l'affichage des données brutes pour vérification humaine.
> - Les règles génériques : dates d'expiration, seuils, FEFO, mouvements et traçabilité.
> - L'exécution locale (Ollama, Docker) et la sécurisation par clé d'API dans un credential.
> - Le pipeline OCR de lecture des dates et des lots, et la validation humaine.

**4.4 — Quels éléments doivent être adaptés, et pourquoi ?**

> - Le prompt : vocabulaire et ordre des actions propres au métier (vaccins : chaîne du froid ; supermarché : promotion, don, retrait ; DLC ≠ DDM).
> - Les données et règles métier : nouveaux champs (température de conservation, doses par flacon), seuils différents (vaccins : alerte à 60 jours), plusieurs dépôts ou rayons.
> - Les rôles et droits d'accès : pharmacien, magasinier, chef de service ; caissier, gérant.
> - Le type d'input : lecture du code DataMatrix GS1 ou du code-barres EAN, plus fiable que l'OCR pour de gros volumes.
> - La langue : modèle OCR arabe (PaddleOCR lang="ar"), modèle d'embeddings multilingue (ex. bge-m3), test de la qualité de Llama en arabe, interface de droite à gauche.
> - Le volume : indexation incrémentale et rapport découpé par service.
>   Ces adaptations sont surtout dans la configuration (.env, nœud Configuration) et le prompt : le cœur déterministe et le workflow ne changent pas.

---

## STEP 5 — COMMUNICATION : TUTORIAL & VIDEO

**5A.1 — Lien vers le tutoriel reproductible**

> https://github.com/Hibaa004/cherrat-stock/blob/main/automatisation/README.md

**5A.2 — Le tutoriel contient-il les éléments suivants ?**

> ☑ Problème ☑ Outils utilisés ☑ Prérequis ☑ Configuration ☑ Données d'entrée (input) ☑ Prompt(s) ☑ Workflow ☑ Étapes d'implémentation ☑ Résultat attendu (output) ☑ Erreurs fréquentes ☑ Dépannage / troubleshooting
>
> (Tous présents dans `automatisation/README.md` + `CREDENTIALS.md` + `ENVIRONNEMENT.md`, et dans l'étape 5 du guide.)

**5A.3 — Quelles instructions permettent à un autre étudiant de reproduire l'automatisation ?**

> Le dossier `automatisation/` contient : le workflow exporté (`workflow_n8n_cherrat.json`), un README avec l'installation pas à pas sur une nouvelle machine (récupérer le projet ; `docker compose up -d` pour PostgreSQL, Qdrant et n8n ; `ollama pull llama3.2:3b` ; configurer `backend/.env` et générer les clés ; `python -m app.seed` puis `uvicorn … --host 0.0.0.0` ; lancer l'interface ; importer le workflow dans n8n, créer le credential et cliquer sur Execute workflow), avec un point de contrôle après chaque étape ; `ENVIRONNEMENT.md` (versions de tous les outils et dépendances) ; `CREDENTIALS.md` (le credential « Cherrat API Key » : type Header Auth, droits, étapes de création) ; `architecture.svg` (schéma de la chaîne) ; un tableau des cas limites à tester et un tableau de dépannage (ECONNREFUSED, 401, 503, 422, modèle introuvable…). `TEST_TRANSFERABILITE.md` décrit le protocole du test avec un pair.

**5A.4 — Selon vous, un autre étudiant peut-il reproduire l'automatisation sans demander d'aide aux auteurs ?**

> ☑ Oui, avec quelques difficultés mineures
>
> ⚠ À ajuster après ton test réel avec ton ami.

**5B.1 — Lien vers la vidéo de démonstration**

> ⚠ À COMPLÉTER : lien Google Drive ou YouTube non répertorié, accessible au professeur.

**5B.2 — Langue principale de la vidéo**

> ⚠ À COMPLÉTER selon ta vidéo (le guide conseille l'anglais ; le script du guide est en anglais).

**5B.3 — La vidéo présente-t-elle les éléments suivants ?**

> Si tu suis le script ci-dessous, coche les 6 :
> ☑ Le problème ☑ Le processus avant automatisation ☑ La solution et son fonctionnement ☑ Une exécution réelle ☑ Le résultat et les bénéfices ☑ Au moins une limite ou un cas d'échec

**5B.4 — Quelle partie du mécanisme d'automatisation expliquez-vous explicitement dans la vidéo ?**

> La chaîne complète du workflow n8n, nœud par nœud : le déclencheur planifié à 8 h 15 ; l'appel à l'API protégé par la clé X-API-Key ; le nœud Code qui calcule la synthèse chiffrée et construit le prompt ; la condition IF qui évite d'appeler l'IA quand il n'y a pas d'alerte ; l'appel à Ollama (llama3.2:3b, température 0,1) qui rédige seulement la liste d'actions ; la branche de repli quand Ollama est arrêté ; la publication dans l'application et l'affichage sur le tableau de bord avec les données brutes. J'explique pourquoi les chiffres sont calculés par le code (le modèle 3B annonçait « 2 problèmes » au lieu de 4) et où l'humain intervient.

---

## STEP 6 — SELF-EVALUATION & CREATIVITY

**6.1 — Temps moyen nécessaire AVANT automatisation**

> 900 minutes par mois (estimation : contrôle des dates et des seuils 180 min + 40 lots reçus × 90 s = 60 min + 220 questions de disponibilité × 3 min = 660 min). Pour le seul contrôle du stock : 180 minutes par contrôle.

**6.2 — Temps moyen nécessaire APRÈS automatisation**

> 96 minutes par mois (estimation : lecture du rapport et traitement des alertes 10 min + 40 lots × 20 s ≈ 13 min + 220 questions × 20 s ≈ 73 min). Pour le contrôle du stock : 0 minute de préparation (le workflow tourne seul, 20 à 60 s) + environ 2 minutes de lecture du rapport par jour.

**6.3 — Nombre d'opérations / actions AVANT automatisation** (facultatif)

> Environ 900 actions par contrôle (environ 300 boîtes × prendre, lire la date, noter), puis la rédaction de la liste des choses à faire.

**6.4 — Nombre d'opérations / actions APRÈS automatisation** (facultatif)

> Environ 3 actions : ouvrir le tableau de bord, lire le rapport, vérifier les données calculées ; puis le traitement des alertes (retrait, commande).

**6.5 — Comparez les erreurs ou difficultés observées avant et après automatisation.**

> Avant : erreurs de lecture et de recopie des dates (formats variés, caractères gravés), contrôle repoussé faute de temps, lots périmés découverts trop tard, ruptures découvertes devant le patient, information concentrée chez le Major.
> Après : les alertes sont calculées chaque jour, sans oubli, et le rapport est vu par toute l'équipe. Difficultés observées pendant le développement : le modèle 3B s'est trompé en comptant (« 2 problèmes » au lieu de 4) → la synthèse chiffrée est maintenant calculée par le code ; l'IA peut être indisponible → branche de repli ; le conteneur n8n ne joignait pas l'API (localhost dans Docker) → `host.docker.internal` et `--host 0.0.0.0`. Erreurs restantes possibles : PC éteint à 8 h 15 (pas de rapport, signalé sur le tableau de bord) et données fausses à la source (d'où la validation humaine de l'OCR).

**6.6 — Quels scénarios avez-vous testés ?**

> ☑ Cas normal ☑ Input inattendu ☑ Cas simple ☑ Cas d'échec / erreur

**6.7 — Décrivez vos tests et les résultats observés. Ajoutez des preuves si possible.**

> Tests du workflow n8n (n8n 2.16.1, 26/11/2026) :
>
> - Import du JSON par `n8n import:workflow` : réussi.
> - Cas normal (données de démonstration, 4 alertes) : exécution complète avec l'API et Ollama ; rapport publié et visible sur le tableau de bord du Docteur, avec la synthèse « 4 alerte(s)… » et la liste des actions rédigée par l'IA. Appel à Ollama : 20 à 30 s.
> - Cas d'échec : adresse Ollama injoignable → la branche de repli publie quand même le rapport (synthèse + données brutes + message « L'assistant IA n'a pas répondu »).
> - Cas simple : sans alerte, le nœud IF n'appelle pas l'IA et publie « Aucune alerte aujourd'hui ». ⚠ Ce cas n'a pas encore été exécuté dans n8n : fais-le (corrige le stock pour supprimer les alertes, puis Execute workflow) avant d'envoyer, ou retire cette ligne.
> - Input inattendu : clé API absente ou fausse → 401 ; clé non configurée → 503 ; rapport publié avec une source invalide → 422 (tests automatiques).
>   Tests automatiques du backend : 21 tests pytest réussis (rapport, publication, clé API, tableau de bord, FEFO et stock insuffisant, OCR).
>   Tests de l'OCR de l'application : 12 photos de boîtes fictives (normale, FAB et EXP, mois en lettres, année sur 2 chiffres, photo inclinée, gravure sur fond argenté, photo très floue…) → 48 champs sur 48 conformes à l'attendu ; sur la photo floue, rien n'est deviné ; un dosage absent du catalogue n'est jamais proposé.
>   Preuves : captures du tableau de bord et de l'onglet Executions de n8n, tableau des résultats dans `images_test_ocr/README.md`.

**6.8 — Lien vers les preuves / résultats de tests** (facultatif)

> https://github.com/Hibaa004/cherrat-stock/blob/main/images_test_ocr/README.md

**6.9 — Quelle(s) amélioration(s) avez-vous proposée(s) ou implémentée(s) ?**

> ☑ Amélioration du prompt ☑ Validation supplémentaire ☑ Output structuré ☑ Approbation humaine ☑ Mécanisme de secours (fallback) ☑ Autre architecture de workflow

**6.10 — Décrivez une ou deux améliorations et justifiez leur intérêt.**

> 1. Implémentée — « le code calcule, l'IA rédige » + mécanisme de secours. Lors des tests, llama3.2:3b annonçait « 2 problèmes » alors qu'il y en avait 4. La phrase de synthèse chiffrée est donc calculée dans le nœud Code, le LLM ne rédige que la liste d'actions, et les données brutes sont affichées sous le rapport. Si Ollama ne répond pas, une branche de repli publie quand même le rapport. Intérêt : aucun chiffre faux sur le tableau de bord et un rapport tous les jours, même sans IA.
> 2. Proposée — sortie structurée validée. Demander au LLM un JSON ({actions: [{type, medicament, lot, quantite}]}) avec le format JSON d'Ollama, puis comparer chaque ligne aux faits de l'API dans un nœud Code : toute ligne dont le lot ou la quantité ne correspond pas est rejetée ou signalée. Intérêt : éliminer le risque d'hallucination au lieu de seulement le signaler.

**6.11 — Quel est votre niveau de confiance dans la fiabilité de l'automatisation ?**

> ☑ 4
>
> (Tous les tests passent et la branche de repli fonctionne ; pas 5, car le texte de l'IA peut encore contenir une erreur et le workflow dépend du PC allumé à 8 h 15.)

---

## STEP 7 — REFLECTION & METACOGNITION (individuel)

> Brouillon issu du guide, à la première personne. **Relis-le et réécris-le avec ta propre expérience** : le professeur demande une réflexion personnelle.

**Membre 1 — Nom et prénom**

> ⚠ À COMPLÉTER

**Membre 1 — À propos du problème : qu'ai-je mieux compris après avoir analysé la tâche ?**

> En analysant la tâche, j'ai compris que le vrai problème n'était pas de « saisir des données » mais de ne jamais rater une date d'expiration et de rendre l'information accessible à toute l'équipe, même en l'absence du Major. J'ai aussi découvert les règles du métier (gestion par lots, FEFO, seuils d'alerte, dates « mois/année » valables jusqu'à la fin du mois), et j'ai compris qu'un contrôle long est un contrôle qu'on repousse : l'automatiser chaque matin change vraiment la sécurité.

**Membre 1 — À propos de l'IA générative : que peut-elle automatiser efficacement ?**

> L'IA générative est efficace pour transformer des faits en texte clair et ordonné, et pour comprendre une question libre, dans la langue de l'utilisateur. Elle n'est pas fiable pour calculer, compter ou garantir une date exacte : le modèle 3B a annoncé « 2 problèmes » au lieu de 4. Ces tâches doivent rester dans le code.

**Membre 1 — À propos de l'ingénierie : qu'est-ce qui a nécessité davantage qu'une simple question posée à un LLM ?**

> Presque tout : concevoir l'API qui calcule les faits, sécuriser l'accès par une clé, construire le workflow n8n avec sa condition et sa branche de repli, faire communiquer le conteneur n8n avec l'API et Ollama (host.docker.internal, --host 0.0.0.0), écrire les tests, documenter les credentials, et surtout décider où ne pas utiliser l'IA. Le LLM n'est qu'un nœud parmi une dizaine.

**Membre 1 — À propos de la fiabilité : dans quels cas l'automatisation peut-elle échouer ?**

> Quand Ollama est arrêté ou trop lent (géré par le repli), quand le backend est arrêté ou la clé API fausse, quand le PC est éteint à 8 h 15, quand les données à la source sont fausses (mauvaise saisie, date mal lue par l'OCR et non corrigée), ou quand le LLM reformule mal un fait. C'est pour cela que les données brutes sont affichées et que l'humain vérifie avant d'agir.

**Membre 1 — À propos des humains : que doit-on maintenir sous contrôle humain ?**

> La vérification du rapport avant d'agir, le retrait physique des lots périmés, les commandes, la validation des dates lues par l'OCR et toute décision médicale (prescription, substitution). L'application informe et alerte ; la responsabilité reste celle du Docteur et du Major.

**Membre 1 — À propos de mon apprentissage : qu'ai-je appris en concevant cette automatisation ?**

> J'ai appris à découper un problème réel en entrées, décisions et sorties, à construire un workflow n8n (déclencheur, HTTP, Code, IF, gestion d'erreur), à appeler un LLM local par API, à combiner IA et règles déterministes, à gérer les secrets avec des credentials, et à documenter un projet pour qu'une autre personne puisse le reproduire.

**Membre 1 — Ai-je réellement automatisé la tâche, ou ai-je simplement déplacé le travail ailleurs ? Justifiez.**

> En grande partie, je l'ai réellement automatisée : le contrôle quotidien (parcourir le stock, repérer les lots et les seuils, rédiger la liste des choses à faire) se fait seul chaque matin, alors qu'il prenait plusieurs heures et était souvent repoussé. Une petite partie du travail est déplacée : lire et vérifier le rapport, maintenir l'application et le workflow, et garder des données justes à la source. Mais ce travail est court et régulier, et la surveillance des dates est désormais continue : le bilan est un vrai gain de temps et de sécurité.

**Membre 2 — Nom et prénom**
> Oumaima BOUMAZOUED

> Brouillon saisi dans le formulaire : **Oumaima doit le relire et le réécrire avec sa propre expérience** avant l'envoi (réflexion individuelle).

**Membre 2 — À propos du problème**
> J'ai compris que la difficulté n'était pas technique au départ, mais organisationnelle : l'information sur le stock existait (registre, boîtes), mais personne n'avait le temps de la relire chaque jour, et elle dépendait d'une seule personne. Le vrai besoin était donc une information à jour, au bon moment et au bon endroit (le tableau de bord), plutôt qu'un outil de plus à consulter.

**Membre 2 — À propos de l'IA générative**
> Elle est utile pour reformuler des données brutes en consignes compréhensibles et adaptées à chaque situation, sans écrire un modèle de texte pour chaque cas. En revanche, nos tests ont montré ses limites : même avec un prompt strict, un petit modèle peut se tromper de catégorie (stock bas appelé « rupture ») ou répéter une ligne. Elle convient donc à la rédaction, pas à la décision ni au calcul.

**Membre 2 — À propos de l'ingénierie**
> Tout ce qui rend le résultat fiable et reproductible : définir les données que l'API doit renvoyer, choisir quelles opérations restent dans le code, gérer le cas où Ollama ne répond pas, tester les cas limites (clé fausse, IA indisponible), et surtout rédiger la documentation (README, credentials, environnement) pour qu'une autre personne puisse installer le workflow sans nous.

**Membre 2 — À propos de la fiabilité**
> Elle peut échouer quand un service est arrêté (Ollama, backend, Docker), quand le PC est éteint à l'heure prévue, quand la configuration est différente sur une autre machine (adresse localhost dans un conteneur, pare-feu), ou quand le texte de l'IA contient une erreur. C'est pour cela que nous affichons toujours les données calculées et que nous avons prévu une branche de repli.

**Membre 2 — À propos des humains**
> La lecture critique du rapport, toute décision qui engage le patient ou le budget (retrait d'un lot, commande, prescription) et la correction des données à la source. L'outil doit rester une aide : il signale, mais c'est l'équipe soignante qui reste responsable.

**Membre 2 — À propos de mon apprentissage**
> J'ai appris à concevoir un workflow avec un déclencheur, des conditions et une gestion d'erreur, à faire communiquer plusieurs services (n8n, API, base de données, LLM local), à tester une automatisation sur des cas normaux et des cas d'échec, et à évaluer honnêtement ses limites au lieu de seulement montrer ce qui marche.

**Membre 2 — Ai-je réellement automatisé la tâche, ou ai-je simplement déplacé le travail ailleurs ? Justifiez.**
> Oui pour l'essentiel : la préparation quotidienne de la liste des actions ne demande plus aucune intervention. Mais une partie du travail s'est déplacée vers la maintenance (services à lancer, workflow à surveiller) et vers la vérification du rapport. Ce travail est beaucoup plus court que le contrôle manuel, et il est mieux réparti dans l'équipe : le gain est réel, à condition de garder cette vérification.

---

## Dernière page

**Reproductibilité** — ☑ « J'ai envoyé cela à mon camarade et cela a fonctionné. »

> ⚠ À cocher seulement après le vrai test de transférabilité avec ton ami (`TEST_TRANSFERABILITE.md`).

**Je voudrais joindre quelques images / documents supplémentaires** (envoi de fichiers, obligatoire)

> Suggestions : capture du tableau de bord avec la carte « Rapport du jour (IA) », capture du workflow dans n8n, capture de l'onglet Executions, fiche de test remplie par ton ami.

**Un commentaire ou une réflexion ?**

> Ce projet m'a montré que la partie la plus importante d'une automatisation avec l'IA n'est pas le prompt, mais tout ce qui l'entoure : calculer les faits de façon fiable, prévoir le cas où l'IA ne répond pas, et laisser l'humain vérifier. Merci pour ce projet très concret.
>
> (À personnaliser.)
