# Images de test pour l'OCR

12 photos de boîtes de médicaments **fictives** (noms génériques, laboratoire inventé), générées par `generer_images.py`, pour tester la lecture automatique de la date d'expiration.

## Comment tester dans l'application

1. Connectez-vous avec le compte du Major (`major@cherrat.ma`) ou de l'Infirmière.
2. Ouvrez **Entrée de stock (OCR)**.
3. Dans « 1. Photographier la boîte », cliquez sur **Choisir un fichier** et sélectionnez une image de ce dossier.
4. Après quelques secondes, la date détectée et le niveau de confiance s'affichent, et la date est recopiée dans le formulaire.
5. Vérifiez la date, choisissez le médicament, saisissez le numéro de lot et la quantité, puis enregistrez (ou ne faites rien : le test de l'OCR ne modifie pas le stock).

Le **tout premier scan** prend environ 2 minutes, car PaddleOCR télécharge ses modèles (Internet nécessaire cette fois-là). Les suivants prennent 1 à 5 secondes.

Pour tester sans l'interface : <http://localhost:8000/docs> → bouton **Authorize** (compte du Major) → route `POST /ocr/scan` → **Try it out** → choisir l'image → **Execute**.

## Résultats attendus et obtenus

Tests réalisés le 26/11/2026 avec l'OCR de l'application (`detecter_expiration`, PaddleOCR 2.7.3, sur processeur).

| Image | Ce qu'elle teste | Texte sur la boîte | Date attendue | Résultat obtenu | Confiance | Durée |
|---|---|---|---|---|---|---|
| `01_paracetamol_normal` | Cas normal | `FAB : 01/2025`, `EXP : 05/2027` | 31/05/2027 | ✅ 2027-05-31 | haute | 129 s (1er scan) |
| `02_amoxicilline_fab_et_exp` | Choisir EXP et pas FAB ; année bissextile | `FAB : 03/2026`, `EXP : 02/2028` | 29/02/2028 | ✅ 2028-02-29 | haute | 1,2 s |
| `03_ibuprofene_date_complete` | Date jour.mois.année ; mot-clé « PER » | `FAB : 15.01.2025`, `PER : 31.01.2028` | 31/01/2028 | ✅ 2028-01-31 | haute | 1,3 s |
| `04_serum_mois_en_lettres` | Mois en anglais ; « MFG » | `MFG : MAR 2026`, `EXP : MAY 2027` | 31/05/2027 | ✅ 2027-05-31 | haute | 1,2 s |
| `05_metformine_format_iso` | Format année-mois | `EXP 2027-09` | 30/09/2027 | ✅ 2027-09-30 | haute | 1,2 s |
| `06_omeprazole_deja_expire` | Lot déjà périmé | `EXP : 09/2026` | 30/09/2026 (expiré) | ✅ 2026-09-30 | haute | 1,2 s |
| `07_amoxicilline_expire_bientot` | Lot qui expire sous 90 jours | `EXP : 12/2026` | 31/12/2026 | ✅ 2026-12-31 | haute | 1,1 s |
| `08_paracetamol_photo_inclinee` | Photo penchée, bruit, ombre | `EXP : 11/2027` | 30/11/2027 | ✅ 2027-11-30 | haute | 1,2 s |
| `09_ibuprofene_grave_sur_argent` | Texte gris gravé sur fond argenté | `EXP 06/2028` | 30/06/2028 | ✅ 2028-06-30 | haute | 1,3 s |
| `10_metformine_sans_mot_cle` | Aucun mot « EXP » : deux dates nues | `10/01/2025`, `06/2027` | 30/06/2027 (la plus tardive) | ✅ 2027-06-30 | **moyenne** | 5,2 s |
| `11_omeprazole_annee_2_chiffres` | Année sur 2 chiffres | `EXP : 08/28` | 31/08/2028 | ✅ 2028-08-31 | haute | 1,8 s |
| `12_paracetamol_tres_floue_echec` | Photo très floue (cas d'échec) | illisible | aucune date | ✅ aucune date → saisie manuelle | aucune | 2,8 s |

**Bilan : 12 résultats conformes sur 12.**

## Ce qu'on observe

- Une date « mois/année » est enregistrée au **dernier jour du mois** (05/2027 devient le 31/05/2027).
- Quand FAB (ou MFG) et EXP sont présents, l'application garde la date située à côté du mot-clé EXP / PER.
- Sans mot-clé, elle prend la date la plus tardive, mais affiche une confiance **moyenne** : l'utilisateur doit vérifier.
- PaddleOCR lit souvent « LOT » comme « L0T » (zéro au lieu de O). Ce n'est pas un problème, car le numéro de lot est saisi à la main.
- Sur une photo floue, l'application ne devine pas : elle n'affiche aucune date, et l'humain saisit la date lui-même (contrôle humain, HITL).

Ces images sont plus propres que de vraies photos. Pour le rapport, testez aussi quelques vraies boîtes (dates gravées, reflets du plastique, mauvais éclairage).

## Régénérer les images

Depuis le dossier `backend` :

```powershell
.\.venv\Scripts\python.exe ..\images_test_ocr\generer_images.py
```
