#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Habillage du film « Le ciel dans une boîte » : charte des textes incrustés par le montage.

Source unique de la charte (polices, tailles, couleurs, boîtes, ombre portée, zones de l'écran, animations) pour les
callouts, le compteur « Temps écoulé » et les sous-titres. Elle reprend l'identité des schémas 2D
(tools/explainer/diagrams.py) et des incrustations (tools/explainer/inserts.py) : parchemin, encre, bronze, or,
violet « hypothèse », vert-de-gris « modèle » (mêmes couleurs que la page web docs/lire/).

Dépend seulement de Pillow (pas de matplotlib) : importable depuis n'importe quel script de montage.

  ~/voxtral-tts/bin/python tools/explainer/overlay.py style
        écrit build/out/explainer/film/overlay_style.json et des planches d'exemple dans
        build/out/explainer/film/overlay_samples/ (compteur, callouts, sous-titre, planche sur une image de la machine)
  ~/voxtral-tts/bin/python tools/explainer/overlay.py counter --crank 2.31 --out /tmp/c.png
  ~/voxtral-tts/bin/python tools/explainer/overlay.py callout --text "Station" --kind normal --out /tmp/a.png
  ~/voxtral-tts/bin/python tools/explainer/overlay.py subtitle --text "Voici notre reconstruction." --out /tmp/s.png

API Python (images RGBA 1920x1080, alpha droit, prêtes pour un overlay ffmpeg) :
  counter_text(crank)                      -> « 2 ans 113 j »
  render_counter(crank, alpha=1.0)
  render_callouts([{'text': ..., 'sub': ..., 'kind': 'normal|hyp|modele|illustration|exemple'}], zone='haut_droite')
  render_subtitle(texte, alpha=1.0)        (retours à la ligne du .srt respectés, sinon coupure automatique)
  add_shadow(image)                        (ombre portée de la charte, calculée sur l'alpha du calque)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / 'build' / 'cache' / 'fonts'
FILM = ROOT / 'build' / 'out' / 'explainer' / 'film'
W, H, FPS = 1920, 1080, 25

# ----------------------------------------------------------------------------- charte (source unique)
PALETTE = {
    'parchemin': '#F3EAD8',       # fond des schémas plein écran (diagrams.BG)
    'papier': '#FBF5EA',          # boîtes, cartes (diagrams.PAPER)
    'encre': '#2A2118',           # texte principal (diagrams.INK)
    'encre_douce': '#6B5B47',     # texte secondaire (diagrams.MUTED)
    'filet': '#E0CFAF',           # filets fins (diagrams.RULE)
    'filet_fort': '#CDB48A',      # bord des boîtes (diagrams.RULE_STRONG)
    'bronze': '#9A6B2F',          # titres en petites capitales, grec (diagrams.BRONZE)
    'bronze_fort': '#7A4614',     # étiquettes « illustration » / « exemple » (page web --bronze-strong)
    'or': '#C8963E',              # barre d'accent, médaillons, surlignage (diagrams.GOLD)
    'laiton': '#EDD9AA',          # fond surligné (diagrams.BRASS)
    'hypothese': '#62529A',       # violet « hypothèse » (diagrams.HYP, page web --hyp)
    'modele': '#2C7263',          # vert-de-gris « calculé par notre modèle » (page web --verdigris)
    'alerte': '#A2381F',          # épave, mise en garde (page web --alert)
    'grave': '#3A2915',           # lettres gravées (page web --engrave)
    'eclipse_lune': '#2A4F80',    # Σ (page web --glyph-moon)
    'eclipse_soleil': '#9A4A08',  # Η (page web --glyph-sun)
}

FONTS = {   # clé -> (fichier dans build/cache/fonts, famille, style)
    'sans': ('IBMPlexSans-Regular.ttf', 'IBM Plex Sans', 'Regular'),
    'sansm': ('IBMPlexSans-Medium.ttf', 'IBM Plex Sans', 'Medium'),
    'sansb': ('IBMPlexSans-SemiBold.ttf', 'IBM Plex Sans', 'SemiBold'),
    'sansi': ('IBMPlexSans-Italic.ttf', 'IBM Plex Sans', 'Italic'),
    'display': ('Marcellus-Regular.ttf', 'Marcellus', 'Regular'),
    'greek': ('GentiumBookPlus-Bold.ttf', 'Gentium Book Plus', 'Bold'),
    'serif': ('GentiumBookPlus-Regular.ttf', 'Gentium Book Plus', 'Regular'),
    'quote': ('GentiumBookPlus-Italic.ttf', 'Gentium Book Plus', 'Italic'),
}

SHADOW = {'dx': 0, 'dy': 6, 'sigma_px': 7.0, 'couleur': PALETTE['encre'], 'opacite': 0.42}

BOX = {   # boîte des callouts et du compteur
    'remplissage': PALETTE['papier'], 'opacite': 0.94, 'bord': PALETTE['filet_fort'], 'bord_px': 2,
    'rayon_px': 14, 'marge_px': [24, 14], 'barre_accent': {'couleur': PALETTE['or'], 'largeur_px': 6},
}

SAFE = {'x': 96, 'y': 54}           # zone de sécurité : 5 % de 1920 x 1080

TEXT = {  # clé -> (police, taille en px = corps em, couleur, interlettrage en em, capitales)
    'callout': ('sansb', 40, PALETTE['encre'], 0.0, False),
    'callout_sous': ('sans', 28, PALETTE['encre_douce'], 0.0, False),
    'mention_hyp': ('sansm', 28, PALETTE['hypothese'], 0.0, False),
    'mention_modele': ('sansm', 28, PALETTE['modele'], 0.0, False),
    'mention_illustration': ('sansi', 26, PALETTE['bronze_fort'], 0.0, False),
    'compteur_libelle': ('sansm', 28, PALETTE['encre_douce'], 0.0, False),
    'compteur_valeur': ('sansb', 40, PALETTE['encre'], 0.0, False),
    'sous_titre': ('sansm', 42, PALETTE['encre'], 0.0, False),
    'petites_capitales': ('sansb', 26, PALETTE['bronze'], 0.06, True),
}

KINDS = {  # nature d'un callout -> (style du texte secondaire, couleur de la barre d'accent)
    'normal': ('callout_sous', PALETTE['or']),
    'hyp': ('mention_hyp', PALETTE['hypothese']),
    'modele': ('mention_modele', PALETTE['modele']),
    'illustration': ('mention_illustration', PALETTE['bronze_fort']),
    'exemple': ('mention_illustration', PALETTE['bronze_fort']),
}

ZONES = {
    'compteur': {'ancre': 'haut_gauche', 'x': SAFE['x'], 'y': SAFE['y']},
    'haut_droite': {'ancre': 'haut_droite', 'x': W - SAFE['x'], 'y': SAFE['y'], 'sens': 'bas'},
    'haut_gauche': {'ancre': 'haut_gauche', 'x': SAFE['x'], 'y': 150, 'sens': 'bas'},   # sous le compteur
    'bas_gauche': {'ancre': 'bas_gauche', 'x': SAFE['x'], 'y': 876, 'sens': 'haut'},    # au-dessus des sous-titres
    'bas_droite': {'ancre': 'bas_droite', 'x': W - SAFE['x'], 'y': 876, 'sens': 'haut'},
}
STACK_GAP = 14

SUB = {'largeur_max_px': 1500, 'lignes_max': 2, 'interligne': 1.28, 'bas_px': H - SAFE['y'],
       'remplissage': PALETTE['papier'], 'opacite': 0.88, 'rayon_px': 12, 'marge_px': [26, 12],
       'car_par_ligne_max': 48}

ANIM = {'entree_images': 8, 'sortie_images': 6, 'glissement_px': 10, 'decalage_pile_images': 5,
        'courbe': 'smoothstep u*u*(3-2u)', 'tenue_min_s': 2.0}


def hexrgb(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def font_file(key):
    return FONT_DIR / FONTS[key][0]


@lru_cache(maxsize=None)
def font(key, px):
    return ImageFont.truetype(str(font_file(key)), int(round(px)))


def is_greek(ch):
    return 'Ͱ' <= ch <= 'Ͽ' or 'ἀ' <= ch <= '῿'


def split_runs(s, key):
    """Découpe un texte en séquences (texte, police) : les lettres grecques passent en Gentium Book Plus Bold,
    comme dans les schémas ; les espaces et la ponctuation restent dans la police du texte."""
    runs = []
    for ch in s:
        k = 'greek' if is_greek(ch) else key
        if runs and runs[-1][1] == k:
            runs[-1][0] += ch
        else:
            runs.append([ch, k])
    return [(a, b) for a, b in runs]


def text_width(s, key, px, tracking=0.0):
    if tracking:
        return sum(font(k, px).getlength(c) + tracking * px for a, k in split_runs(s, key) for c in a) - tracking * px
    return sum(font(k, px).getlength(a) for a, k in split_runs(s, key))


def draw_text(layer, x, y, s, key, px, color, tracking=0.0, anchor='ls'):
    """Texte sur une ligne de base (x = gauche, y = ligne de base) dans un calque RGBA (composition alpha propre)."""
    mask = Image.new('L', layer.size, 0)
    d = ImageDraw.Draw(mask)
    xx = x
    for a, k in split_runs(s, key):
        f = font(k, px)
        if tracking:
            for c in a:
                d.text((xx, y), c, font=f, fill=255, anchor=anchor)
                xx += f.getlength(c) + tracking * px
        else:
            d.text((xx, y), a, font=f, fill=255, anchor=anchor)
            xx += f.getlength(a)
    col = Image.new('RGBA', layer.size, hexrgb(color))
    col.putalpha(mask)
    layer.alpha_composite(col)
    return xx - x


def rounded_box(layer, box, fill, opacity, border=None, border_px=0, radius=14, ss=4):
    """Rectangle arrondi anticrénelé (suréchantillonné) composé dans le calque."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    big = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius=radius * ss, fill=255)
    m = big.resize((w, h), Image.LANCZOS)
    if border and border_px:
        inner = Image.new('L', (w * ss, h * ss), 0)
        b = border_px * ss
        ImageDraw.Draw(inner).rounded_rectangle((b, b, w * ss - 1 - b, h * ss - 1 - b),
                                                radius=max(1, radius * ss - b), fill=255)
        mi = inner.resize((w, h), Image.LANCZOS)
        face = Image.new('RGBA', (w, h), hexrgb(fill))
        face.putalpha(mi.point(lambda v: int(v * opacity)))
        edge = Image.new('RGBA', (w, h), hexrgb(border))
        edge.putalpha(ImageChops.subtract(m, mi))
        tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        tile.alpha_composite(face)
        tile.alpha_composite(edge)
    else:
        tile = Image.new('RGBA', (w, h), hexrgb(fill))
        tile.putalpha(m.point(lambda v: int(v * opacity)))
    layer.alpha_composite(tile, (x0, y0))
    return m


def add_shadow(img, shadow=SHADOW):
    """Ombre portée de la charte : flou gaussien de l'alpha du calque, décalé, sous le calque."""
    a = img.getchannel('A')
    blur = a.filter(ImageFilter.GaussianBlur(shadow['sigma_px']))
    blur = ImageChops.offset(blur, shadow['dx'], shadow['dy'])
    sh = Image.new('RGBA', img.size, hexrgb(shadow['couleur']))
    sh.putalpha(blur.point(lambda v: int(v * shadow['opacite'])))
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.alpha_composite(sh)
    out.alpha_composite(img)
    return out


def scale_alpha(img, alpha):
    if alpha >= 0.999:
        return img
    a = img.getchannel('A').point(lambda v: int(v * max(0.0, alpha)))
    img = img.copy()
    img.putalpha(a)
    return img


# ----------------------------------------------------------------------------- compteur
def counter_text(crank):
    """« X an(s) Y j » : X = partie entière, Y = partie décimale x 365,2422 (arrondi vers le bas, 0 à 365)."""
    c = max(0.0, float(crank))
    y = int(math.floor(c))
    d = int(math.floor((c - y) * 365.2422 + 1e-9))
    d = min(d, 365)
    return f'{y} {"an" if y < 2 else "ans"} {d} j'


COUNTER_LABEL = 'Temps écoulé : '
COUNTER_WIDEST = '10 ans 365 j'


def counter_box():
    fl, pl = TEXT['compteur_libelle'][0], TEXT['compteur_libelle'][1]
    fv, pv = TEXT['compteur_valeur'][0], TEXT['compteur_valeur'][1]
    mx, my = BOX['marge_px']
    wl = text_width(COUNTER_LABEL, fl, pl)
    wv = text_width(COUNTER_WIDEST, fv, pv)
    w = mx + BOX['barre_accent']['largeur_px'] + 4 + wl + wv + mx
    h = my * 2 + int(pv * 1.25)
    x0, y0 = ZONES['compteur']['x'], ZONES['compteur']['y']
    return (x0, y0, x0 + w, y0 + h), wl


def render_counter(crank, alpha=1.0, dy=0.0, shadow=True):
    """Compteur (coin haut gauche, largeur fixe pour que la boîte ne bouge pas ; chiffres à chasse fixe
    dans IBM Plex Sans)."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    (x0, y0, x1, y1), wl = counter_box()
    y0 += dy; y1 += dy
    rounded_box(img, (x0, y0, x1, y1), BOX['remplissage'], BOX['opacite'], BOX['bord'], BOX['bord_px'],
                BOX['rayon_px'])
    acc = BOX['barre_accent']
    rounded_box(img, (x0 + 8, y0 + 12, x0 + 8 + acc['largeur_px'], y1 - 12), acc['couleur'], 1.0, radius=3)
    fl, pl, cl = TEXT['compteur_libelle'][:3]
    fv, pv, cv = TEXT['compteur_valeur'][:3]
    base = y0 + (y1 - y0) / 2 + pv * 0.36
    xt = x0 + BOX['marge_px'][0] + acc['largeur_px'] + 4
    draw_text(img, xt, base, COUNTER_LABEL, fl, pl, cl)
    draw_text(img, xt + wl, base, counter_text(crank), fv, pv, cv)
    if shadow:
        img = add_shadow(img)
    return scale_alpha(img, alpha)


# ----------------------------------------------------------------------------- callouts
def callout_size(item):
    key, px = TEXT['callout'][0], TEXT['callout'][1]
    mx, my = BOX['marge_px']
    wt = text_width(item['text'], key, px) if item.get('text') else 0
    sub_key = KINDS[item.get('kind', 'normal')][0]
    ws = text_width(item['sub'], TEXT[sub_key][0], TEXT[sub_key][1]) if item.get('sub') else 0
    h = my
    if item.get('text'):
        h += int(px * 1.22)
    if item.get('sub'):
        h += int(TEXT[sub_key][1] * 1.35)
    h += my
    return int(mx + BOX['barre_accent']['largeur_px'] + 6 + max(wt, ws) + mx), h


def draw_callout(img, x0, y0, item):
    kind = item.get('kind', 'normal')
    sub_key, acc_col = KINDS[kind]
    w, h = callout_size(item)
    rounded_box(img, (x0, y0, x0 + w, y0 + h), BOX['remplissage'], BOX['opacite'], BOX['bord'], BOX['bord_px'],
                BOX['rayon_px'])
    acc = BOX['barre_accent']
    rounded_box(img, (x0 + 8, y0 + 12, x0 + 8 + acc['largeur_px'], y0 + h - 12), acc_col, 1.0, radius=3)
    xt = x0 + BOX['marge_px'][0] + acc['largeur_px'] + 6
    y = y0 + BOX['marge_px'][1]
    if item.get('text'):
        key, px, col = TEXT['callout'][:3]
        y += px * 0.98
        draw_text(img, xt, y, item['text'], key, px, col)
        y += px * 0.24
    if item.get('sub'):
        key, px, col = TEXT[sub_key][:3]
        y += px * 1.08
        draw_text(img, xt, y, item['sub'], key, px, col)
    return w, h


def render_callouts(items, zone='haut_droite', alpha=1.0, shadow=True, alphas=None):
    """Pile de callouts dans une zone de la charte. items : [{'text', 'sub', 'kind'}] ; alphas : opacité par callout
    (pour les apparitions décalées)."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    z = ZONES[zone]
    sizes = [callout_size(it) for it in items]
    y = z['y'] if z['sens'] == 'bas' else z['y'] - sum(s[1] for s in sizes) - STACK_GAP * (len(items) - 1)
    for i, (it, (w, h)) in enumerate(zip(items, sizes)):
        x = z['x'] - w if z['ancre'].endswith('droite') else z['x']
        a = 1.0 if alphas is None else alphas[i]
        if a > 0.003:
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            draw_callout(lay, x, y + (1 - smooth(a)) * ANIM['glissement_px'], it)
            img.alpha_composite(scale_alpha(lay, a))
        y += h + STACK_GAP
    if shadow:
        img = add_shadow(img)
    return scale_alpha(img, alpha)


# ----------------------------------------------------------------------------- sous-titres
def wrap_subtitle(text, key=None, px=None):
    key = key or TEXT['sous_titre'][0]
    px = px or TEXT['sous_titre'][1]
    maxw = SUB['largeur_max_px'] - 2 * SUB['marge_px'][0]
    if '\n' in text:
        return [l.strip() for l in text.split('\n') if l.strip()]
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if text_width(t, key, px) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    if len(lines) == 2 and len(lines[1]) < 12:      # équilibrer deux lignes
        ws = text.split()
        best = min(range(1, len(ws)), key=lambda i: abs(text_width(' '.join(ws[:i]), key, px) -
                                                       text_width(' '.join(ws[i:]), key, px)))
        lines = [' '.join(ws[:best]), ' '.join(ws[best:])]
    return lines


def render_subtitle(text, alpha=1.0, shadow=False):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    key, px, col = TEXT['sous_titre'][:3]
    lines = wrap_subtitle(text)
    lh = px * SUB['interligne']
    mx, my = SUB['marge_px']
    wmax = max(text_width(l, key, px) for l in lines)
    h = my * 2 + lh * len(lines) - (lh - px * 1.18)
    y1 = SUB['bas_px']
    y0 = y1 - h
    x0 = W / 2 - wmax / 2 - mx
    rounded_box(img, (x0, y0, W / 2 + wmax / 2 + mx, y1), SUB['remplissage'], SUB['opacite'], radius=SUB['rayon_px'])
    y = y0 + my + px * 0.93
    for l in lines:
        draw_text(img, W / 2 - text_width(l, key, px) / 2, y, l, key, px, col)
        y += lh
    if shadow:
        img = add_shadow(img)
    return scale_alpha(img, alpha)


# ----------------------------------------------------------------------------- charte JSON + planches
def style_dict():
    fonts = {k: {'fichier': str(font_file(k)), 'fichier_relatif': str(font_file(k).relative_to(ROOT)),
                 'famille': v[1], 'style': v[2]} for k, v in FONTS.items()}
    txt = {k: {'police': v[0], 'px': v[1], 'couleur': v[2], 'interlettrage_em': v[3], 'capitales': v[4]}
           for k, v in TEXT.items()}
    (cx0, cy0, cx1, cy1), _ = counter_box()
    return {
        'genere_par': 'tools/explainer/overlay.py style (source unique : dictionnaires PALETTE, FONTS, TEXT, BOX, '
                      'SHADOW, ZONES, SUB, ANIM de ce fichier)',
        'taille': [W, H], 'fps': FPS,
        'unites': "px = taille du corps (em) en pixels, comme ImageFont.truetype(size=px) de Pillow ; ffmpeg drawtext "
                  "fontsize=px donne le même corps. Lignes de base en px depuis le haut de l'image.",
        'polices': fonts,
        'regle_grec': "Toute lettre grecque (U+0370-03FF, U+1F00-1FFF) est composée en Gentium Book Plus Bold "
                      "(clé 'greek') à la même taille que le texte qui l'entoure, dans la même couleur (bronze pour "
                      "un nom grec isolé). Marcellus n'a pas de grec ; IBM Plex Sans n'a pas le stigma Ϛ.",
        'regle_chiffres': "Dans un texte en Marcellus (titres, carton final), les chiffres sont composés en Gentium "
                          "Book Plus Regular (clé 'serif') : le « 1 » de Marcellus se lit comme un « I ». IBM Plex Sans "
                          "a des chiffres à chasse fixe (0,60 em) : les nombres qui changent ne font pas bouger le texte.",
        'palette': PALETTE,
        'textes': txt,
        'boite': {**BOX, 'note': "fond papier à 94 %, bord 2 px, rayon 14 px, marges 24 x 14 px ; barre d'accent "
                                 "verticale de 6 px à 8 px du bord gauche, couleur selon la nature du callout"},
        'ombre_portee': {**SHADOW, 'note': "calculée sur l'alpha du calque entier : flou gaussien sigma 7 px, "
                                           "décalage (0, +6) px, encre à 42 %, placée sous le calque"},
        'zone_de_securite_px': SAFE,
        'zones': {**ZONES, 'note': "compteur en haut à gauche ; callouts empilés en haut à droite par défaut ; "
                                   "si une incrustation occupe la droite (phases, metonic_cell, glyph_anatomy), "
                                   "passer en 'haut_gauche' (sous le compteur) ou 'bas_gauche' ; rien sous y = 880 "
                                   "sauf les sous-titres", 'ecart_pile_px': STACK_GAP},
        'callouts': {
            'titre': 'callout', 'texte_secondaire': "selon la nature : " + ', '.join(
                f"{k} -> {v[0]} (barre {v[1]})" for k, v in KINDS.items()),
            'natures': {k: {'style_secondaire': v[0], 'couleur_barre': v[1]} for k, v in KINDS.items()},
            'regles': ["Les mentions d'honnêteté sont des callouts de nature 'hyp' (violet), 'modele' (vert-de-gris) "
                       "ou 'illustration'/'exemple' (bronze foncé, italique) : jamais en simple texte gris.",
                       "Un callout = une idée : titre 40 px SemiBold, au plus une ligne secondaire 28 px.",
                       "Au plus 3 callouts à l'écran en même temps ; apparition décalée de 5 images.",
                       "Textes exacts : ceux de script.md (colonne « Textes à l'écran »)."],
        },
        'compteur': {
            'boite_px': [cx0, cy0, cx1, cy1],
            'libelle': COUNTER_LABEL.strip(), 'style_libelle': 'compteur_libelle', 'style_valeur': 'compteur_valeur',
            'format': "« X an Y j » si X < 2, sinon « X ans Y j » ; X = partie entière de la manivelle, "
                      "Y = floor(partie décimale x 365,2422), de 0 à 365",
            'exemples': {str(c): counter_text(c) for c in (0.0, 0.6, 0.972, 1.009, 2.31, 5.95, 9.014, 9.6)},
            'largeur_fixe': f"boîte calculée pour « {COUNTER_WIDEST} » : elle ne bouge pas quand les chiffres changent "
                            "(chiffres à chasse fixe dans IBM Plex Sans : 0,60 em)",
            'visible': "à partir du chapitre 2 (plan 2.1) ; masqué pendant la reprise du plan 4.3",
        },
        'sous_titres': {**SUB, 'style': 'sous_titre',
                        'note': "centrés, boîte papier à 88 % sans bord, bas de la boîte à y = 1026 ; retours à la "
                                "ligne de narration.srt respectés ; pas d'ombre portée"},
        'animation': ANIM,
        'incrustations_2d': "voir build/out/explainer/inserts/timing.json (boîtes, segments, ancres)",
    }


def cmd_style(args):
    FILM.mkdir(parents=True, exist_ok=True)
    out = FILM / 'overlay_style.json'
    out.write_text(json.dumps(style_dict(), ensure_ascii=False, indent=1), encoding='utf-8')
    print('charte ->', out)
    sd = FILM / 'overlay_samples'
    sd.mkdir(parents=True, exist_ok=True)
    # compteur : planche de valeurs
    render_counter(2.31).save(sd / 'compteur_2.31.png')
    sheet = Image.new('RGBA', (900, 620), hexrgb(PALETTE['parchemin']))
    (x0, y0, x1, y1), _ = counter_box()
    for i, c in enumerate((0.0, 0.972, 1.009, 2.31, 5.95, 9.014)):
        im = render_counter(c).crop((x0 - 30, y0 - 20, x0 - 30 + 900, y0 - 20 + 100))
        sheet.alpha_composite(im, (0, 10 + i * 100))
    sheet.convert('RGB').save(sd / 'compteur_planche.png')
    # callouts : les quatre natures
    items = [{'text': 'Lune : 1 tour/mois', 'sub': 'Vitesse variable (Hipparque)', 'kind': 'normal'},
             {'text': 'Planètes : lire sur le zodiaque', 'sub': 'Hypothèse · Freeth et al. 2021', 'kind': 'hyp'},
             {'text': 'Σ = éclipse de Lune', 'sub': 'Signe calculé par notre modèle', 'kind': 'modele'},
             {'text': 'Ξ : la Pléiade se lève', 'sub': 'illustration', 'kind': 'illustration'}]
    render_callouts(items, 'haut_droite').save(sd / 'callouts_haut_droite.png')
    render_subtitle("Il y a plus de deux mille ans, quelqu'un\na enfermé le ciel dans une boîte :").save(
        sd / 'sous_titre.png')
    # planche sur une image de la machine (look2)
    bg_path = ROOT / 'build' / 'out' / 'explainer' / 'look2' / 'CAM_front_close_eevee.png'
    if bg_path.exists():
        bg = Image.open(bg_path).convert('RGBA').resize((W, H))
        bg.alpha_composite(render_counter(2.31))
        bg.alpha_composite(render_callouts(items[:2], 'haut_droite'))
        bg.alpha_composite(render_callouts(items[2:], 'bas_gauche'))
        bg.alpha_composite(render_subtitle("Autour du centre, cinq petites sphères :\nles planètes, lues sur le "
                                           "zodiaque."))
        bg.convert('RGB').save(sd / 'planche_sur_machine.jpg', quality=90)
    print('planches ->', sd)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('style')
    c = sub.add_parser('counter'); c.add_argument('--crank', type=float, required=True); c.add_argument('--out')
    a = sub.add_parser('callout'); a.add_argument('--text', default=''); a.add_argument('--sub', default='')
    a.add_argument('--kind', default='normal', choices=list(KINDS)); a.add_argument('--zone', default='haut_droite')
    a.add_argument('--out')
    s = sub.add_parser('subtitle'); s.add_argument('--text', required=True); s.add_argument('--out')
    args = ap.parse_args()
    if args.cmd == 'style':
        cmd_style(args)
    elif args.cmd == 'counter':
        render_counter(args.crank).save(args.out or 'compteur.png')
    elif args.cmd == 'callout':
        render_callouts([{'text': args.text, 'sub': args.sub, 'kind': args.kind}], args.zone).save(
            args.out or 'callout.png')
    elif args.cmd == 'subtitle':
        render_subtitle(args.text.replace('\\n', '\n')).save(args.out or 'sous_titre.png')


if __name__ == '__main__':
    main()
