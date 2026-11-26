# Images de test pour l'OCR

12 photos de boîtes de médicaments **fictives** (noms génériques, laboratoire inventé), générées par `generer_images.py`, pour tester le remplissage automatique du formulaire d'entrée : **médicament, numéro de lot, date d'expiration et quantité**.

Avant de tester, complétez le catalogue (une seule fois) depuis le dossier `backend` :

```powershell
.\.venv\Scripts\python.exe -m app.seed
```

Cette commande ajoute, sans stock, les médicaments des images qui manquent au catalogue (Paracétamol 1 g, Amoxicilline 500 mg, Metformine 850 et 500 mg, Oméprazole 20 et 40 mg). Pensez ensuite à cliquer sur « Réindexer le stock » (page Assistant IA, compte du Major) pour que l'assistant les connaisse. L'Ibuprofène 200 mg est volontairement **absent**, pour montrer que l'application refuse un dosage inconnu.

## Comment tester dans l'application

1. Connectez-vous avec le compte du Major (`major@cherrat.ma`) ou de l'Infirmière.
2. Ouvrez **Entrée de stock (OCR)**.
3. Dans « 1. Photographier la boîte », cliquez sur **Choisir un fichier** et sélectionnez une image de ce dossier.
4. Après quelques secondes, le cadre « Informations détectées » s'affiche, et le formulaire est rempli : médicament, n° de lot, date d'expiration, unités par boîte et quantité. Les champs remplis automatiquement sont **en jaune**.
5. Indiquez le **nombre de boîtes reçues** : la quantité est recalculée (boîtes × unités par boîte).
6. Vérifiez chaque champ jaune avec la boîte, puis enregistrez (ou ne faites rien : scanner une image ne modifie pas le stock).

Le **tout premier scan** prend environ 2 minutes, car PaddleOCR télécharge ses modèles (Internet nécessaire cette fois-là). Les suivants prennent 1 à 5 secondes.

Pour tester sans l'interface : <http://localhost:8000/docs> → bouton **Authorize** (compte du Major) → route `POST /ocr/scan` → **Try it out** → choisir l'image → **Execute**.

## Résultats attendus et obtenus

Tests réalisés le 26/11/2026 avec la chaîne complète de l'application (route `POST /ocr/scan` : PaddleOCR 2.7.3 sur processeur, puis extraction des informations et comparaison avec le catalogue).

| Image | Ce qu'elle teste | Médicament proposé | N° de lot | Date d'expiration | Unités / boîte |
|---|---|---|---|---|---|
| `01_paracetamol_normal` | Cas normal | ✅ Paracétamol 500 mg | ✅ PCT2611 | ✅ 31/05/2027 (haute) | ✅ 20 |
| `02_amoxicilline_fab_et_exp` | Choisir EXP et pas FAB ; année bissextile | ✅ Amoxicilline 1 g | ✅ AMX2603 | ✅ 29/02/2028 (haute) | ✅ 12 |
| `03_ibuprofene_date_complete` | Date jour.mois.année ; mot-clé « PER » | ✅ Ibuprofène 400 mg | ✅ IBU0115 | ✅ 31/01/2028 (haute) | ✅ 30 |
| `04_serum_mois_en_lettres` | Mois en anglais ; nom abrégé « PHYSIO. » ; poche | ✅ Sérum physiologique 0,9 % | ✅ SER4471 | ✅ 31/05/2027 (haute) | ✅ 1 (poche) |
| `05_metformine_format_iso` | Format année-mois | ✅ Metformine 850 mg | ✅ MET0927 | ✅ 30/09/2027 (haute) | ✅ 30 |
| `06_omeprazole_deja_expire` | Lot déjà périmé (message rouge dans le formulaire) | ✅ Oméprazole 20 mg | ✅ OME0924 | ✅ 30/09/2026 (haute) | ✅ 14 |
| `07_amoxicilline_expire_bientot` | Même DCI, autre dosage que l'image 02 | ✅ Amoxicilline 500 mg | ✅ AMX1226 | ✅ 31/12/2026 (haute) | ✅ 16 |
| `08_paracetamol_photo_inclinee` | Photo penchée, bruit, ombre | ✅ Paracétamol 1 g | ✅ PCT1127 | ✅ 30/11/2027 (haute) | ✅ 8 |
| `09_ibuprofene_grave_sur_argent` | Texte gravé ; **dosage absent du catalogue** | ✅ aucun + avertissement (200 mg inconnu) | ✅ IBU0628 | ✅ 30/06/2028 (haute) | ✅ 20 |
| `10_metformine_sans_mot_cle` | Ni « LOT » ni « EXP » | ✅ Metformine 500 mg | ✅ non détecté (pas de mot-clé) | ✅ 30/06/2027 (**moyenne**) | ✅ 50 |
| `11_omeprazole_annee_2_chiffres` | Année sur 2 chiffres | ✅ Oméprazole 40 mg | ✅ OME0828 | ✅ 31/08/2028 (haute) | ✅ 7 |
| `12_paracetamol_tres_floue_echec` | Photo très floue (cas d'échec) | ✅ aucun | ✅ non détecté | ✅ aucune | ✅ non détecté |

**Bilan : 48 informations sur 48 conformes à l'attendu** (12 images × 4 champs). Durée : 1 à 5 secondes par image, sauf le tout premier scan (≈ 2 minutes, téléchargement des modèles).

## Ce qu'on observe

- Une date « mois/année » est enregistrée au **dernier jour du mois** (05/2027 devient le 31/05/2027).
- Quand FAB (ou MFG) et EXP sont présents, l'application garde la date située à côté du mot-clé EXP / PER.
- Sans mot-clé, elle prend la date la plus tardive, mais affiche une confiance **moyenne** : l'utilisateur doit vérifier.
- **Médicament** : l'application compare le nom (ou la DCI) **et le dosage** lus avec le catalogue. Une boîte de Paracétamol 1 g n'est jamais proposée comme Paracétamol 500 mg : si le dosage n'existe pas, aucun médicament n'est choisi et un avertissement s'affiche.
- **N° de lot** : il est cherché après le mot « LOT » (ou « BATCH »). PaddleOCR lit souvent « LOT » comme « L0T » et colle parfois les mots (« L0TPCT1127 ») ; l'extraction le tolère. Un zéro suivi de lettres au début du lot (« 0ME0924 ») est corrigé en lettre O. Sans mot-clé, l'application ne devine pas.
- **Quantité** : l'application lit le contenu d'une boîte (« Boîte de 20 comprimés », « Poche… ») et calcule boîtes × unités. Le nombre de boîtes reçues, lui, n'est pas sur la boîte : il reste à saisir.
- Sur une photo floue, l'application ne devine pas : elle n'affiche aucune date, et l'humain saisit la date lui-même (contrôle humain, HITL).

Ces images sont plus propres que de vraies photos. Pour le rapport, testez aussi quelques vraies boîtes (dates gravées, reflets du plastique, mauvais éclairage).

## Régénérer les images

Depuis le dossier `backend` :

```powershell
.\.venv\Scripts\python.exe ..\images_test_ocr\generer_images.py
```
