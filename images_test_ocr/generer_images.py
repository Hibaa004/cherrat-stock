"""Génère des photos de boîtes de médicaments (fictives) pour tester l'OCR.

Usage (depuis le dossier backend, pour utiliser son Python) :
    .venv\\Scripts\\python.exe ..\\images_test_ocr\\generer_images.py

Les noms sont des DCI génériques et le laboratoire est fictif.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DOSSIER = os.path.dirname(os.path.abspath(__file__))
FONTS = 'C:/Windows/Fonts/'
random.seed(42)


def police(nom, taille):
    return ImageFont.truetype(FONTS + nom, taille)


def boite(nom, dosage, forme, couleur, lignes_flap, flap_style='blanc', dci=''):
    """Dessine la face d'une boîte posée sur une table."""
    img = Image.new('RGB', (1400, 900), (120, 100, 80))
    d = ImageDraw.Draw(img)
    # table en bois (dégradé)
    for y in range(900):
        c = 110 + int(25 * math.sin(y / 37)) + y // 40
        d.line([(0, y), (1400, y)], fill=(c, int(c * 0.82), int(c * 0.62)))
    # ombre puis boîte
    d.rounded_rectangle([170, 130, 1270, 810], 18, fill=(60, 50, 40))
    d.rounded_rectangle([150, 110, 1250, 790], 18, fill=(248, 248, 244))
    d.rectangle([150, 110, 1250, 270], fill=couleur)
    d.text((190, 135), nom, font=police('arialbd.ttf', 72), fill='white')
    d.text((190, 220), dci or forme, font=police('arial.ttf', 34), fill=(235, 240, 245))
    d.text((190, 300), dosage, font=police('arialbd.ttf', 54), fill=couleur)
    d.text((190, 375), forme, font=police('arial.ttf', 34), fill=(60, 60, 60))
    d.text((190, 430), 'Voie orale - Lire attentivement la notice', font=police('arial.ttf', 26), fill=(90, 90, 90))
    d.text((190, 470), 'Tenir hors de la vue et de la portée des enfants', font=police('arial.ttf', 26), fill=(90, 90, 90))
    d.text((190, 720), 'Laboratoire Démo — Casablanca', font=police('arial.ttf', 24), fill=(120, 120, 120))
    # zone imprimée LOT / FAB / EXP
    x0, y0, x1, y1 = 760, 530, 1210, 760
    mono = police('consolab.ttf', 44)
    if flap_style == 'argent':
        d.rectangle([x0, y0, x1, y1], fill=(196, 198, 204))
        for i, l in enumerate(lignes_flap):
            y = y0 + 25 + i * 68
            d.text((x0 + 26, y + 2), l, font=mono, fill=(225, 227, 232))   # reflet (gravure)
            d.text((x0 + 24, y), l, font=mono, fill=(140, 142, 150))
    else:
        d.rectangle([x0, y0, x1, y1], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
        for i, l in enumerate(lignes_flap):
            d.text((x0 + 24, y0 + 25 + i * 68), l, font=mono, fill=(25, 25, 25))
    return img


def photo(img, angle=0.0, flou=0.6, bruit=6, eclairage=0.15):
    """Ajoute les défauts d'une photo de téléphone."""
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=(110, 90, 70))
    if eclairage:
        grad = Image.linear_gradient('L').rotate(-60, expand=False).resize(img.size)
        sombre = Image.new('RGB', img.size, (0, 0, 0))
        masque = grad.point(lambda v: int(v * eclairage))
        img = Image.composite(sombre, img, masque)
    if flou:
        img = img.filter(ImageFilter.GaussianBlur(flou))
    if bruit:
        px = img.load()
        w, h = img.size
        for _ in range(w * h // 6):
            x, y = random.randrange(w), random.randrange(h)
            r, g, b = px[x, y]
            n = random.randint(-bruit, bruit)
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


BLEU, VERT, ROUGE, VIOLET, ORANGE, GRIS = (21, 94, 117), (22, 120, 80), (170, 40, 50), (90, 60, 140), (200, 110, 20), (70, 80, 95)

CAS = [
    ('01_paracetamol_normal', boite('PARACÉTAMOL', '500 mg', 'Boîte de 20 comprimés', BLEU,
     ['LOT : PCT2611', 'FAB : 01/2025', 'EXP : 05/2027']), {}),
    ('02_amoxicilline_fab_et_exp', boite('AMOXICILLINE', '1 g', 'Boîte de 12 comprimés', VERT,
     ['LOT : AMX2603', 'FAB : 03/2026', 'EXP : 02/2028']), {}),
    ('03_ibuprofene_date_complete', boite('IBUPROFÈNE', '400 mg', 'Boîte de 30 comprimés', ROUGE,
     ['LOT : IBU0115', 'FAB : 15.01.2025', 'PER : 31.01.2028']), {}),
    ('04_serum_mois_en_lettres', boite('SÉRUM PHYSIO.', '0,9 % - 500 ml', 'Poche pour perfusion', GRIS,
     ['LOT : SER4471', 'MFG : MAR 2026', 'EXP : MAY 2027'], dci='Chlorure de sodium'), {}),
    ('05_metformine_format_iso', boite('METFORMINE', '850 mg', 'Boîte de 30 comprimés', VIOLET,
     ['LOT : MET0927', 'EXP 2027-09']), {}),
    ('06_omeprazole_deja_expire', boite('OMÉPRAZOLE', '20 mg', 'Boîte de 14 gélules', ORANGE,
     ['LOT : OME0924', 'FAB : 09/2024', 'EXP : 09/2026']), {}),
    ('07_amoxicilline_expire_bientot', boite('AMOXICILLINE', '500 mg', 'Boîte de 16 gélules', VERT,
     ['LOT : AMX1226', 'EXP : 12/2026']), {}),
    ('08_paracetamol_photo_inclinee', boite('PARACÉTAMOL', '1 g', 'Boîte de 8 comprimés', BLEU,
     ['LOT : PCT1127', 'EXP : 11/2027']), dict(angle=7, flou=1.0, bruit=14, eclairage=0.35)),
    ('09_ibuprofene_grave_sur_argent', boite('IBUPROFÈNE', '200 mg', 'Boîte de 20 comprimés', ROUGE,
     ['LOT IBU0628', 'EXP 06/2028'], flap_style='argent'), dict(flou=0.8, bruit=8)),
    ('10_metformine_sans_mot_cle', boite('METFORMINE', '500 mg', 'Boîte de 50 comprimés', VIOLET,
     ['MET0627', '10/01/2025', '06/2027']), {}),
    ('11_omeprazole_annee_2_chiffres', boite('OMÉPRAZOLE', '40 mg', 'Boîte de 7 gélules', ORANGE,
     ['LOT : OME0828', 'EXP : 08/28']), {}),
    ('12_paracetamol_tres_floue_echec', boite('PARACÉTAMOL', '500 mg', 'Boîte de 20 comprimés', BLEU,
     ['LOT : PCT0329', 'EXP : 03/2029']), dict(angle=-4, flou=7, bruit=10, eclairage=0.3)),
]

if __name__ == '__main__':
    for nom, img, defauts in CAS:
        photo(img, **({'angle': 0, 'flou': 0.6, 'bruit': 6, 'eclairage': 0.15} | defauts)).save(
            os.path.join(DOSSIER, nom + '.jpg'), quality=88)
        print('créée :', nom + '.jpg')
