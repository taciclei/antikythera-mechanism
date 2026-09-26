#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Montage image par image du film « Le ciel dans une boîte » : timeline.json -> film/comp/%05d.png.

Pour chaque image f du film (1-4009), l'image finale 1920 x 1080 RGB est composée ainsi, de bas en haut :

  1. fond : rendu 3D (film/frames/%04d.png) pour les plans 3d / split / card ; schéma plein cadre (diagram) ou
     carte opaque (map) selon la table `map` de la timeline ; carton 7.6 = end_card_fond.png + la machine (CAM_7_5)
     en fondu de 100 % à 25 % (card.machine_fade), le tout sous les textes du carton (end_card_texte) ;
     schémas plein cadre qui portent du texte en bas (6.5a, 7.3a) : réduits d'un bloc (échelle constante sur le
     plan, bords prolongés) pour laisser la place aux sous-titres (avertissement 3 de verify_beats.py) ;
  2. écran partagé : 4.3 = retrograde_split (moitié gauche transparente) par-dessus la 3D ; 7.4 = pleiades_coucher
     réduit dans diagram.rect_px (cadre crème, ombre de la charte) jusqu'à inset_until − 1 ;
  3. incrustation 3D du plan 3.4 (frames/inset_3_4/%04d.png) dans inset.rect_px, cadre crème fin ;
  4. incrustations 2D (inserts.py) : phases, metonic_cell, games_banner, glyph_anatomy ; parapegma_xi translaté sur
     l'ancre sign_under_sun ; parapegma_ligne réduite et posée sur la plaque du haut (ancre parapegma_top) ;
  5. callouts (charte overlay.py : draw_callout, zones, piles, ombre portée, entrée 8 images / sortie 6 images,
     glissement 10 px) et leurs filets vers les ancres de anchors.json (seulement si l'ancre est dans l'image, ni
     sous une incrustation ni sous le sous-titre affiché) ou vers une ancre calculée au montage (VIRTUAL_ANCHORS,
     LEADER_TARGET : axe de la manivelle en 2.1/2.3, anneaux de 3.1, bord du fantôme de b1) ; traits 2D du plan 3.2
     (lines_2d) ;
  6. compteur « Temps écoulé » (overlay.render_counter) sur les images où frames[].counter est défini ;
  7. titres de chapitre (inserts chapter_title_N) ;
  8. sous-titres gravés (overlay.render_subtitle) si burn_in ;
  9. fondus : ouverture au noir (images 1-13), fermeture au noir (dernière seconde), bascule d'éclairage de 5.1
     adoucie sur 2 images (1970-1971).

  ~/voxtral-tts/bin/python tools/explainer/film/composite.py --only-available
  ~/voxtral-tts/bin/python tools/explainer/film/composite.py --placeholder --scale 0.5     # animatique -> preview_comp/
  ~/voxtral-tts/bin/python tools/explainer/film/composite.py --frames 460,1446,3363 --placeholder --out /tmp/x

Reprise : une image déjà écrite est sautée (sauf --overwrite), sauf si elle a été faite avec un fond provisoire et
que le rendu 3D existe maintenant, ou si le rendu 3D est plus récent qu'elle. Chaque PNG porte dans ses métadonnées
la source du fond (comp_src = render | placeholder | 2d) et la version du compositeur.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, PngImagePlugin

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'explainer'))
sys.path.insert(0, str(HERE))
import overlay as O  # noqa: E402  (charte des textes : source unique)
import filmlib as FL  # noqa: E402  (easing des poses de caméra, identique à build_film.py)

FILM = ROOT / 'build' / 'out' / 'explainer' / 'film'
W, H = O.W, O.H
VERSION = 'composite-2'
FPS = 25

# ----------------------------------------------------------------------------- réglages du montage
FADE_IN_FRAMES = 12            # ouverture : noir -> image, images 1 à 13
FADE_OUT_FRAMES = 25           # fermeture : image -> noir sur la dernière seconde (la dernière image est noire)
BASCULE_FRAME = 1971           # 5.1 : première image éclairée par l'arrière (README, « bascule à el = 0 »)
SUB_FADE = 3                   # sous-titres : 3 images d'entrée et de sortie
COUNTER_FADE = 8               # compteur : entrée sur « Tournez-la », sortie sous le carton
INSET_FADE_IN, INSET_FADE_OUT = 8, 6
FIT_GAP = 16                   # marge entre le bas d'un schéma réduit et le haut de la boîte des sous-titres
PP_LIGNE_SCALE = 0.62          # ligne du parapegme : 1007 px de large à l'échelle 1, plus large que la plaque
PP_LIGNE_DY = 170              # posée sur la moitié basse de la plaque du haut (qui fait ≈ 860 px de haut)
PP_XI_CLEAR = 60               # rayon du repère Ξ : le filet s'arrête avant
LEADER = {'core_px': 2.4, 'halo_px': 6.0, 'halo_opacity': 0.42, 'ring_r': 12.0, 'min_len': 36.0,
          'core': O.PALETTE['papier'], 'halo': O.PALETTE['encre']}
LEADER_BOTTOM_Y = H - O.SAFE['y']   # pas de filet vers une ancre sous la zone de sécurité (y > 1026)
LEADER_SUB_PAD = 16            # la boîte du sous-titre affiché (élargie de 16 px) est un obstacle des filets
FRAME_BORDER_PX = 3            # cadre crème des incrustations (3.4 et 7.4)
FRAME_RADIUS = 10
# Pas de filet pour « Parapegme : calendrier des étoiles » (7.2) : les deux plaques sont surlignées dans la 3D ; un
# filet vers la plaque du bas traverse tout le cadran (≈ 850 px) et un filet vers celle du haut croise celui de
# « Ξ : la Pléiade se lève » (callout juste en dessous, qui vise l'échelle du zodiaque en bas à gauche).
LEADER_SKIP = {('7.2', 'Parapegme : calendrier des étoiles')}
# ancres posées au centre d'une inscription gravée : le filet s'arrête avant (rayon en px) pour ne pas la barrer
LEADER_CLEAR = {'games_sector': 96, 'pachon': 50, 'glyph_112': 46}
LEADER_HOLD = 5                # images de fondu du filet quand son ancre sort de la zone permise
# 6.5a : dans le schéma d'éclipse réduit, la bande du bas porte « l'aiguille du Dragon montre les nœuds (hypothèse) »
# dès x = 575 : le callout de bas_gauche (x 96-584) en masquerait la première lettre. Il passe en haut à gauche,
# sous la ligne de sous-titre du schéma (fin à y ≈ 170) et au-dessus du Soleil.
CALLOUT_ZONE_OVERRIDE = {('6.5a', 'Signes calculés par notre modèle'): {'zone': 'haut_gauche', 'y': 200},
                         # 2.3 : dans la même pile que « ≈ 4,6 tours = 1 an », le filet de celui-ci (vers l'axe de la
                         # manivelle, en bas à droite) traversait « Grande roue » ; ce dernier vise le centre du cadran,
                         # à gauche : il passe sous le compteur, les deux filets ne se croisent plus
                         ('2.3', 'Grande roue : 1 tour/an'): {'zone': 'haut_gauche'},
                         # 6.3 : sous « Exeligmos », son filet croisait celui de « Exeligmos » ; en haut à droite (libre
                         # depuis que glyph_anatomy sort plus tôt, voir OVERLAY_RETIME) il vise l'aiguille de près
                         ('6.3', 'Ici : +0 h'): {'zone': 'haut_droite'},
                         # 7.2 : sous « Parapegme » (haut droite), son filet vers le repère Ξ (bas gauche du cadran)
                         # traversait tout le cadran en passant sur le moyeu et les aiguilles ; en haut à gauche, sous
                         # « Ξ et ligne du parapegme : illustration », il descend droit sur le repère
                         ('7.2', 'Ξ : la Pléiade se lève'): {'zone': 'haut_gauche'}}
# Ancres calculées au montage (monde, mm) : projetées avec la caméra du plan (poses de la timeline, cibles fixes
# seulement ; même calcul que build_film.pose_params, écart aux ancres de anchors.json < 0,1 px).
VIRTUAL_ANCHORS = {
    # axe de la manivelle dans le plan du bouton : centre du cercle décrit par crank_knob (R = 23,0 mm, écart 0,05 mm)
    'crank_hub': (106.0, 0.0, 19.16),
    # anneaux de la face avant en haut à droite de l'image (az 85° et 45°), sous leurs callouts de 3.1 ; les ancres
    # de la timeline (az −50° et −20°) tombent dans la boîte des sous-titres : aucun filet n'était possible
    'calendar_ring_ne': (75.03 * math.cos(math.radians(85)), 75.03 * math.sin(math.radians(85)), 42.4),
    'zodiac_ring_ne': (66.0 * math.cos(math.radians(45)), 66.0 * math.sin(math.radians(45)), 41.6),
    # 2.3 : bord denté du fantôme de b1 (rayon de b1_rim, 65 mm ; plan du fantôme z = 42,58, GHOST_Z de
    # build_film.py) à gauche du cadran, sous le callout « Grande roue » : le filet montre la roue et non le moyeu
    # central, où se croisent toutes les aiguilles
    'b1_ghost_rim_w': (65.0 * math.cos(math.radians(220)), 65.0 * math.sin(math.radians(220)), 42.58),
}
# Cible du filet d'un callout, à la place de c['anchor'] : [(image début, image fin, ancre | (ancre a, ancre b))] ;
# un couple (a, b) glisse de a vers b en douceur sur l'intervalle.
# 2.1 et 2.3 : dès que la manivelle tourne (≈ 15° par image), le bouton fouette et sort sans cesse de l'image ou passe
# sous les sous-titres (filet qui tourne et clignote) : le filet vise alors l'axe de la manivelle, immobile.
LEADER_TARGET = {
    ('2.1', 'La manivelle = le temps'): [(631, 651, 'crank_knob'), (652, 659, ('crank_knob', 'crank_hub')),
                                         (660, 10 ** 6, 'crank_hub')],
    ('2.3', '≈ 4,6 tours = 1 an'): [(0, 10 ** 6, 'crank_hub')],
    ('2.3', 'Grande roue : 1 tour/an'): [(0, 10 ** 6, 'b1_ghost_rim_w')],
    ('3.1', 'Calendrier égyptien · 365 j'): [(0, 10 ** 6, 'calendar_ring_ne')],
    ('3.1', 'Zodiaque · 12 signes'): [(0, 10 ** 6, 'zodiac_ring_ne')],
}
# Retiming d'une incrustation : [(image du film, image de la séquence)] (linéaire entre deux points, rien après le
# dernier). 6.3 : glyph_anatomy (boîte x 1064-1824) couvrait la moitié droite de l'Exeligmos et toute son aiguille
# dès l'arrivée du panoramique (2725) jusqu'à la fin du plan, pendant « zéro, huit ou seize heures » et « Ici : +0 h ».
# Il se construit plus vite (ΩΡ + chiffre sur « l'heure », 2679-2695), tient pendant le panoramique et sort à
# l'arrivée sur l'Exeligmos (2725-2733).
OVERLAY_RETIME = {
    'glyph_anatomy': [(2669, 1), (2675, 10), (2676, 11), (2683, 25), (2684, 26), (2694, 47), (2695, 48),
                      (2708, 79), (2709, 80), (2724, 104), (2725, 105), (2733, 113)],
}
# Titres de chapitre : pendant l'entrée, la boîte s'ouvre de gauche à droite mais le texte apparaît déjà en entier ;
# tout ce qui dépasse le bord droit de la boîte (mesuré sur la ligne y = 778, sous le filet du haut) est masqué.
TITLE_EDGE_ROW = 778
# 4.3 : le schéma retrograde_split occupe toute la moitié droite, légende comprise (« Mars recule : rétrogradation »
# en bas) : les sous-titres passent au centre de la moitié gauche.
SUB_SPLIT_CENTER_X = 480
# 1.3 : la carte porte en bas à gauche le cartouche « Printemps 1900 / Pêcheurs d'éponges de Symi » (x 96-700,
# y 706-880) ; centré, le sous-titre (x ≈ 610-1310, y 899-1026) s'y collait. Il passe à droite du cartouche, entre lui
# et l'échelle « 50 km » (x ≥ 1540).
SUB_CENTER_X = {'1.3': 1100}

BG_PARCH = O.hexrgb(O.PALETTE['parchemin'])[:3]


def rel(p):
    return ROOT / p


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def timecode(f):
    t = (f - 1) / FPS
    return '%02d:%02d.%02d' % (int(t // 60), int(t % 60), int(round((t - int(t)) * FPS)) % FPS)


# ----------------------------------------------------------------------------- données
class Film:
    def __init__(self):
        T = json.loads((FILM / 'timeline.json').read_text(encoding='utf-8'))
        self.T = T
        self.n = T['frame_end']
        self.frames = {x['f']: x for x in T['frames']}
        self.seg = {s['id']: s for s in T['segments']}
        self.seg_order = [s['id'] for s in T['segments']]
        A = json.loads((FILM / 'anchors.json').read_text(encoding='utf-8'))
        self.anchors = {k: {int(r[0]): (r[1], r[2], bool(r[4])) for r in v['frames']}
                        for k, v in A['anchors'].items()}
        self.ovl = []
        for o in T['overlays']:
            o = dict(o)
            o['fmap'] = {int(a): int(b) for a, b in o['map']}
            if o['sequence'] in OVERLAY_RETIME:
                o['fmap'] = retime_map(OVERLAY_RETIME[o['sequence']])
                o['frames'] = [min(o['fmap']), max(o['fmap'])]
            self.ovl.append(o)
        for s in T['segments']:
            d = s.get('diagram')
            if d:
                d['fmap'] = {int(a): int(b) for a, b in d['map']}
        self.subs = T['subtitles']
        self.card = self.seg['7.6'].get('card') if '7.6' in self.seg else None

    def segment(self, f):
        return self.seg[self.frames[f]['seg']]


def retime_map(keys):
    """[(image du film, image de la séquence)] -> {image du film: image de la séquence}, linéaire par morceaux."""
    out = {}
    for (fa, na), (fb, nb) in zip(keys, keys[1:]):
        for f in range(fa, fb + 1):
            out[f] = na if fb == fa else int(round(na + (nb - na) * (f - fa) / float(fb - fa)))
    return out


# ----------------------------------------------------------------------------- caméra (ancres calculées au montage)
def _pose(poses, f):
    """Pose interpolée à l'image f (build_film.pose_params) ; None si une cible n'est pas un point fixe."""
    def un(p):
        if not isinstance(p['target'], (list, tuple)):
            raise LookupError
        return (np.array(p['target'], float), p['az'], p['el'], p['dist'], p['lens'], np.array(p['up'], float),
                np.array(p['shift'], float))
    try:
        if f <= poses[0]['f']:
            return un(poses[0])
        if f >= poses[-1]['f']:
            return un(poses[-1])
        i = max(k for k in range(len(poses)) if poses[k]['f'] <= f)
        a, b = poses[i], poses[i + 1]
        pa, pb = un(a), un(b)
    except LookupError:
        return None
    w = FL.ease01((f - a['f']) / float(b['f'] - a['f']), a.get('ease', 'SINE_IN_OUT'))
    up = pa[5] + (pb[5] - pa[5]) * w
    n = float(np.linalg.norm(up))
    return tuple(x + (y - x) * w for x, y in zip(pa[:5], pb[:5])) + (up / n if n > 1e-9 else pa[5],
                                                                        pa[6] + (pb[6] - pa[6]) * w)


def project_world(s, f, p):
    """Point du monde (mm) -> (x_px, y_px, dans_l_image) à l'image f du plan s (1920 x 1080, décentrement compris)."""
    cam = s.get('camera')
    pose = _pose(cam['poses'], f) if cam else None
    if pose is None:
        return None
    tgt, az, el, dist, lens, up, shift = pose
    a, e = math.radians(az), math.radians(el)
    loc = tgt + dist * np.array([math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)])
    fw = (tgt - loc) / np.linalg.norm(tgt - loc)
    if abs(float(fw @ up)) > 0.999:
        up = np.array([0.0, 1.0, 0.0])
    r = np.cross(fw, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, fw)
    d = np.asarray(p, float) - loc
    z = float(d @ fw)
    if z <= 1e-6:
        return None
    k = lens / 36.0                       # sensor_fit AUTO, 36 mm sur la largeur (image paysage)
    x = W * (0.5 + k * float(d @ r) / z - shift[0])
    y = H / 2.0 - W * (k * float(d @ u) / z - shift[1])
    return (x, y, bool(0 <= x < W and 0 <= y < H))


FILM_DATA = None


def film():
    global FILM_DATA
    if FILM_DATA is None:
        FILM_DATA = Film()
    return FILM_DATA


# ----------------------------------------------------------------------------- chemins des rendus 3D
def frame3d_path(frames_dir, f, sub=None):
    d = Path(frames_dir) / sub if sub else Path(frames_dir)
    for name in ('%04d.png' % f, '%05d.png' % f):
        p = d / name
        try:
            if p.stat().st_size > 0:
                return p
        except OSError:
            pass
    return None


def needs(F, f):
    """Rendus 3D dont l'image f a besoin : [(chemin relatif, sous-dossier)]."""
    s = F.segment(f)
    req = []
    if s.get('render_3d') and s['kind'] in ('3d', 'split', 'card'):
        req.append((f, None))
        if s.get('inset'):
            req.append((f, 'inset_3_4'))
        if f in (BASCULE_FRAME - 1, BASCULE_FRAME) and s['id'] == '5.1':
            req.append((BASCULE_FRAME - 1 if f == BASCULE_FRAME else BASCULE_FRAME, None))
    return req


# ----------------------------------------------------------------------------- images (cache)
@lru_cache(maxsize=24)
def load_rgba_cropped(path):
    """Calque RGBA plein cadre -> (morceau utile, (x0, y0)) ; None si vide."""
    im = Image.open(path).convert('RGBA')
    bb = im.getchannel('A').getbbox()
    if not bb:
        return None
    return im.crop(bb), bb[:2]


@lru_cache(maxsize=6)
def load_rgb(path):
    return Image.open(path).convert('RGB')


def paste_rgba(base, im, x, y):
    """alpha_composite de im à (x, y) (entiers, éventuellement hors cadre)."""
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    dx0, dy0 = max(0, x), max(0, y)
    w = min(im.width - sx0, base.width - dx0)
    h = min(im.height - sy0, base.height - dy0)
    if w <= 0 or h <= 0:
        return
    if (sx0, sy0, w, h) != (0, 0, im.width, im.height):
        im = im.crop((sx0, sy0, sx0 + w, sy0 + h))
    base.alpha_composite(im, dest=(dx0, dy0))


def composite_layer(base, path, alpha=1.0, dx=0, dy=0):
    got = load_rgba_cropped(str(path))
    if got is None or alpha <= 0.003:
        return
    im, (x0, y0) = got
    paste_rgba(base, O.scale_alpha(im, alpha), x0 + dx, y0 + dy)


def seq_path(seq_dir, pattern, n):
    return rel(seq_dir) / (pattern % n)


@lru_cache(maxsize=32)
def title_edge(path):
    """Bord droit de la boîte d'un titre de chapitre (alpha > 200 sur la ligne TITLE_EDGE_ROW), ou None."""
    a = np.asarray(Image.open(path).getchannel('A'))
    r = np.nonzero(a[TITLE_EDGE_ROW] > 200)[0]
    return int(r.max()) if len(r) else None


@lru_cache(maxsize=8)
def title_clipped(path, ref):
    """Image d'un titre de chapitre, masquée à droite du bord de sa boîte tant que celle-ci s'ouvre (ref = image de
    tenue, boîte entière) -> (morceau utile, (x0, y0)) ou None."""
    im = Image.open(path).convert('RGBA')
    e, e_full = title_edge(path), title_edge(ref)
    if e is not None and e_full is not None and e < e_full - 1:
        arr = np.array(im)
        arr[:, e + 3:, 3] = 0
        im = Image.fromarray(arr, 'RGBA')
    bb = im.getchannel('A').getbbox()
    return (im.crop(bb), bb[:2]) if bb else None


# ----------------------------------------------------------------------------- schémas plein cadre : place des sous-titres
def sub_box_top(lines=2):
    px = O.TEXT['sous_titre'][1]
    lh = px * O.SUB['interligne']
    my = O.SUB['marge_px'][1]
    return O.SUB['bas_px'] - (2 * my + lh * lines - (lh - px * 1.18))


@lru_cache(maxsize=None)
def fit_params(seg_id):
    """Échelle constante d'un schéma plein cadre pour que son contenu reste au-dessus de la boîte des sous-titres
    (2 lignes). Mesurée sur la première, la médiane et la dernière image utilisées. None si rien à faire.
    -> (échelle, x fixe, y fixe) : le point (x, y) du schéma ne bouge pas ; x = bord que le dessin touche."""
    F = film()
    s = F.seg[seg_id]
    d = s.get('diagram')
    if s['kind'] != 'diagram' or not d:
        return None
    if not any(sb['burn_in'] and sb['in'] <= s['frames'][1] and sb['out'] >= s['frames'][0] for sb in F.subs):
        return None
    imgs = sorted(set(d['fmap'].values()))
    top, bot, left, right = H, 0, 0, 0
    bg = np.array(BG_PARCH, dtype=np.int16)
    for n in (imgs[0], imgs[len(imgs) // 2], imgs[-1]):
        a = np.asarray(Image.open(seq_path(d['dir'], d['pattern'], n)).convert('RGB')).astype(np.int16)
        m = np.abs(a - bg).sum(2) > 30
        rows = np.nonzero(m.any(1))[0]
        if not len(rows):
            continue
        top, bot = min(top, rows[0]), max(bot, rows[-1])
        left, right = max(left, int(m[:, 0].sum())), max(right, int(m[:, -1].sum()))
    target = sub_box_top(2) - FIT_GAP
    if bot <= target:
        return None
    sc = (target - top) / float(bot - top)
    ax = 0.0 if (left >= right and left > 0) else (float(W) if right > 0 else W / 2.0)
    return sc, ax, float(top)


def apply_fit(img, fp):
    sc, ax, ay = fp
    w, h = int(round(W * sc)), int(round(H * sc))
    small = np.asarray(img.convert('RGB').resize((w, h), Image.LANCZOS))
    x0 = int(round(ax * (1 - sc)))
    y0 = int(round(ay * (1 - sc)))
    x0 = min(max(0, x0), W - w)
    y0 = min(max(0, y0), H - h)
    out = np.pad(small, ((y0, H - h - y0), (x0, W - w - x0), (0, 0)), mode='edge')
    return Image.fromarray(out, 'RGB')


# ----------------------------------------------------------------------------- fond provisoire (animatique)
def _wrap(text, key, px, maxw):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if O.text_width(t, key, px) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


@lru_cache(maxsize=4)
def placeholder_base(seg_id, size=(W, H), inset=False):
    F = film()
    s = F.seg[seg_id]
    w, h = size
    im = Image.new('RGBA', size, O.hexrgb('#E7DAC0'))
    d = ImageDraw.Draw(im)
    m = 24 if inset else 40
    d.rectangle((m, m, w - m, h - m), outline=O.hexrgb(O.PALETTE['filet_fort']), width=2)
    for k in range(-h, w, 90 if not inset else 60):     # hachures légères : on voit tout de suite que c'est provisoire
        d.line((k, h, k + h, 0), fill=O.hexrgb('#E0D2B6'), width=2)
    cx = w / 2
    if inset:
        for y, txt, key, px, col in ((h / 2 - 20, 'Incrustation 3.4', 'sansb', 34, O.PALETTE['encre']),
                                     (h / 2 + 24, 'boule des phases (CAM_3_4_ball)', 'sans', 24,
                                      O.PALETTE['encre_douce']),
                                     (h / 2 + 64, 'rendu 3D à venir', 'sansi', 24, O.PALETTE['bronze_fort'])):
            O.draw_text(im, cx - O.text_width(txt, key, px) / 2, y, txt, key, px, col)
        return im
    k1 = 'RENDU 3D À VENIR'
    O.draw_text(im, cx - O.text_width(k1, 'sansb', 30, 0.06) / 2, 330, k1, 'sansb', 30, O.PALETTE['bronze'], 0.06)
    t = 'Plan %s' % s['id']
    O.draw_text(im, cx - O.text_width(t, 'sansb', 112) / 2, 460, t, 'sansb', 112, O.PALETTE['encre'])
    info = '%s · mode %s · images %d-%d' % (s['kind'], s.get('mode', '-'), s['frames'][0], s['frames'][1])
    O.draw_text(im, cx - O.text_width(info, 'sansm', 34) / 2, 520, info, 'sansm', 34, O.PALETTE['encre_douce'])
    y = 590
    for line in _wrap(s.get('cadrage', ''), 'sans', 30, 1250)[:4]:
        O.draw_text(im, cx - O.text_width(line, 'sans', 30) / 2, y, line, 'sans', 30, O.PALETTE['encre_douce'])
        y += 42
    return im


def placeholder(seg_id, f):
    im = placeholder_base(seg_id).copy()
    t = 'image %d · %s' % (f, timecode(f))
    O.draw_text(im, W / 2 - O.text_width(t, 'sansm', 36) / 2, 790, t, 'sansm', 36, O.PALETTE['bronze_fort'])
    return im


# ----------------------------------------------------------------------------- incrustations encadrées (3.4, 7.4)
@lru_cache(maxsize=4)
def frame_masks(w, h, r=FRAME_RADIUS, b=FRAME_BORDER_PX, ss=4):
    big = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius=r * ss, fill=255)
    outer = big.resize((w, h), Image.LANCZOS)
    big = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(big).rounded_rectangle((b * ss, b * ss, (w - b) * ss - 1, (h - b) * ss - 1),
                                          radius=max(1, (r - b) * ss), fill=255)
    inner = big.resize((w, h), Image.LANCZOS)
    return outer, inner


def framed(base, img, rect, alpha=1.0):
    """Image dans un rectangle (x, y, w, h) : coins arrondis, cadre crème de 3 px, ombre portée de la charte."""
    x, y, w, h = [int(round(v)) for v in rect]
    if alpha <= 0.003:
        return
    if img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    outer, inner = frame_masks(w, h)
    pad = 32
    tile = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    face = img.convert('RGBA')
    face.putalpha(inner)
    edge = Image.new('RGBA', (w, h), O.hexrgb(O.PALETTE['papier']))
    edge.putalpha(outer)
    t = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    t.alpha_composite(edge)
    t.alpha_composite(face)
    tile.alpha_composite(t, dest=(pad, pad))
    tile = O.add_shadow(tile)
    paste_rgba(base, O.scale_alpha(tile, alpha), x - pad, y - pad)


# ----------------------------------------------------------------------------- filets (anticrénelés, en numpy)
def draw_strokes(layer, prims):
    """prims : ('seg', (x0, y0), (x1, y1), a) | ('ring', (x, y), r, a) | ('dot', (x, y), r, a).
    Trait crème de la charte (papier) sur un halo d'encre, dessinés par distance (anticrénelage exact)."""
    if not prims:
        return
    hw = LEADER['halo_px'] / 2 + 2
    xs, ys = [], []
    for p in prims:
        if p[0] == 'seg':
            xs += [p[1][0], p[2][0]]
            ys += [p[1][1], p[2][1]]
        else:
            xs += [p[1][0] - p[2], p[1][0] + p[2]]
            ys += [p[1][1] - p[2], p[1][1] + p[2]]
    x0 = max(0, int(math.floor(min(xs) - hw)))
    y0 = max(0, int(math.floor(min(ys) - hw)))
    x1 = min(W, int(math.ceil(max(xs) + hw)) + 1)
    y1 = min(H, int(math.ceil(max(ys) + hw)) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    xx += 0.5
    yy += 0.5
    core = np.zeros(xx.shape, np.float32)
    halo = np.zeros(xx.shape, np.float32)
    cw, hwid = LEADER['core_px'] / 2, LEADER['halo_px'] / 2
    for p in prims:
        if p[0] == 'seg':
            (ax, ay), (bx, by), a = p[1], p[2], p[3]
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy or 1e-6
            t = np.clip(((xx - ax) * vx + (yy - ay) * vy) / L2, 0, 1)
            d = np.hypot(xx - (ax + t * vx), yy - (ay + t * vy))
        elif p[0] == 'ring':
            (cx, cy), r, a = p[1], p[2], p[3]
            d = np.abs(np.hypot(xx - cx, yy - cy) - r)
        else:
            (cx, cy), r, a = p[1], p[2], p[3]
            d = np.hypot(xx - cx, yy - cy) - r + cw      # disque plein de rayon r
        core = np.maximum(core, a * np.clip(cw + 0.5 - d, 0, 1))
        halo = np.maximum(halo, a * np.clip(hwid + 0.5 - d, 0, 1))
    ha = halo * LEADER['halo_opacity']
    out_a = core + ha * (1 - core)
    cc = np.array(O.hexrgb(LEADER['core'])[:3], np.float32)
    hc = np.array(O.hexrgb(LEADER['halo'])[:3], np.float32)
    rgb = (cc[None, None] * core[..., None] + hc[None, None] * (ha * (1 - core))[..., None]) / np.maximum(
        out_a[..., None], 1e-6)
    arr = np.dstack([np.clip(rgb, 0, 255), np.clip(out_a * 255, 0, 255)]).astype(np.uint8)
    layer.alpha_composite(Image.fromarray(arr, 'RGBA'), dest=(x0, y0))


def seg_hits_rect(p0, p1, r, margin=4):
    x0, y0, x1, y1 = r[0] - margin, r[1] - margin, r[2] + margin, r[3] + margin
    n = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 4))
    for i in range(1, n):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


def attach_point(box, anchor, obstacles, below, above):
    """Point de départ du filet sur la boîte (x0, y0, x1, y1) : le plus proche de l'ancre, sans traverser un autre
    élément ; jamais le bord qui touche une autre boîte de la même pile."""
    x0, y0, x1, y1 = box
    r = O.BOX['rayon_px']
    ax, ay = anchor
    k = r * (1 - 1 / math.sqrt(2))       # milieu de l'arrondi d'un coin
    cands = [('left', (x0, min(max(ay, y0 + r), y1 - r))), ('right', (x1, min(max(ay, y0 + r), y1 - r))),
             ('bottom', (min(max(ax, x0 + r), x1 - r), y1)), ('top', (min(max(ax, x0 + r), x1 - r), y0)),
             ('corner', (x0 + k, y1 - k)), ('corner', (x1 - k, y1 - k)), ('corner', (x0 + k, y0 + k)),
             ('corner', (x1 - k, y0 + k))]
    own = (x0 + 3, y0 + 3, x1 - 3, y1 - 3)
    ok = []
    for side, p in cands:
        if side == 'bottom' and (below or ay <= y1):
            continue
        if side == 'top' and (above or ay >= y0):
            continue
        dist = math.hypot(ax - p[0], ay - p[1])
        if seg_hits_rect(p, anchor, own, margin=0):
            continue
        clash = any(seg_hits_rect(p, anchor, o) for o in obstacles)
        ok.append((clash, dist, p))
    if not ok:
        return None
    ok.sort()
    return ok[0][2]


# ----------------------------------------------------------------------------- callouts
@lru_cache(maxsize=64)
def callout_tile(text, sub, kind):
    item = {'kind': kind}
    if text:
        item['text'] = text
    if sub:
        item['sub'] = sub
    w, h = O.callout_size(item)
    tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    O.draw_callout(tile, 0, 0, item)
    return tile


def callout_alpha(c, f):
    if f < c['in'] or f > c['out']:
        return 0.0
    ent, sor = O.ANIM['entree_images'], O.ANIM['sortie_images']
    return smooth(min((f - c['in'] + 1) / ent, (c['out'] - f + 1) / sor))


def slot_factor(c, later, f):
    """Hauteur occupée (0-1) par la place du callout c dans sa pile ; later = callouts visibles posés après lui."""
    ent, sor = O.ANIM['entree_images'], O.ANIM['sortie_images']
    ue = (f - c['in'] + 1) / float(ent)
    ux = (c['out'] - f + 1) / float(sor)
    # la place s'ouvre dans la première moitié de l'entrée (les autres s'écartent avant que la boîte soit opaque) et
    # se referme dans la seconde moitié de la sortie (quand la boîte est déjà à moitié effacée)
    if ue < 1 and any(d['in'] < c['in'] for d in later):       # il arrive et pousse des callouts déjà là
        return smooth(2 * ue)
    if ux < 1 and any(d['out'] > c['out'] for d in later):     # il part et des callouts restent après lui
        return smooth(2 * ux)
    return 1.0


def anchor_at(F, name, f):
    if name in VIRTUAL_ANCHORS:
        return project_world(F.segment(f), f, VIRTUAL_ANCHORS[name])
    a = F.anchors.get(name)
    if not a:
        return None
    return a.get(f)


def leader_point(F, s, c, f):
    """Point visé par le filet du callout c à l'image f : (x, y, dans_l_image) ou None (LEADER_TARGET, sinon
    c['anchor'])."""
    spec = LEADER_TARGET.get((s['id'], c['text']))
    if not spec:
        return anchor_at(F, c['anchor'], f) if c.get('anchor') else None
    for f0, f1, tgt in spec:
        if f0 <= f <= f1:
            if isinstance(tgt, tuple):
                pa, pb = anchor_at(F, tgt[0], f), anchor_at(F, tgt[1], f)
                if not (pa and pb):
                    return None
                u = smooth((f - f0 + 1) / float(f1 - f0 + 2))
                return (pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u, pa[2] and pb[2])
            return anchor_at(F, tgt, f)
    return None


def leader_name(s, c, f):
    """Nom de l'ancre visée (pour LEADER_CLEAR / PP_XI_CLEAR)."""
    for f0, f1, tgt in LEADER_TARGET.get((s['id'], c['text']), ()):
        if f0 <= f <= f1:
            return tgt[1] if isinstance(tgt, tuple) else tgt
    return c.get('anchor')


def leader_valid(F, s, c, f, obstacles):
    p = leader_point(F, s, c, f)
    if not p or not p[2]:
        return None
    x, y = p[0], p[1]
    if not (8 <= x <= W - 8 and 8 <= y <= LEADER_BOTTOM_Y):
        return None
    for r in obstacles:
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            return None
    return (x, y)


def active_rects(F, s, f):
    """Éléments 2D posés à l'image f (hors callouts) : obstacles des filets (dont la boîte du sous-titre affiché,
    élargie de LEADER_SUB_PAD : un filet ne passe ni ne s'arrête dessous)."""
    out = []
    sr = subtitle_rect(F, s, f)
    if sr:
        p = LEADER_SUB_PAD
        out.append((sr[0] - p, sr[1] - p, sr[2] + p, sr[3] + p))
    fr = F.frames[f]
    if fr['counter']:
        b = F.T['layout']['counter_box_px']
        out.append(tuple(b))
    for o in F.ovl:
        if f in o['fmap'] and o.get('box_px') and not o['sequence'].startswith('end_card'):
            out.append(tuple(o['box_px']))
    ins = s.get('inset')
    if ins:
        r = ins['rect_px']
        out.append((r[0], r[1], r[0] + r[2], r[1] + r[3]))
    if s['kind'] == 'split' and f < s.get('inset_until', 10 ** 9):
        r = s['diagram'].get('rect_px', [960, 0, 960, 1080])
        out.append((r[0], r[1], r[0] + r[2], r[1] + r[3]))
    return out


def zone_of(s, c):
    """Zone de la charte d'un callout (timeline), sauf réglage de CALLOUT_ZONE_OVERRIDE pour ce plan."""
    ov = CALLOUT_ZONE_OVERRIDE.get((s['id'], c['text']))
    if ov:
        if set(ov) == {'zone'}:              # simple changement de pile : il rejoint la pile de cette zone
            return ov['zone'], O.ZONES[ov['zone']]
        z = dict(O.ZONES[ov['zone']])
        z.update({k: v for k, v in ov.items() if k != 'zone'})
        return ov['zone'] + '*', z
    return c['zone'], O.ZONES[c['zone']]


def callout_layer(F, s, f):
    cs = [c for c in s.get('callouts', []) if c['in'] <= f <= c['out']]
    lines = [ln for ln in s.get('lines_2d', []) if ln['in'] <= f <= min(ln['out'], s['frames'][1])]
    if not cs and not lines:
        return None
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    placed = []
    gap = O.STACK_GAP
    zones = {}
    for c in cs:
        zname, zdef = zone_of(s, c)
        zones.setdefault(zname, (zdef, []))[1].append(c)
    for zname in sorted(zones):
        z, items = zones[zname]
        items = sorted(items, key=lambda c: c['stack'])
        geo = []
        for c in items:
            it = c['item']
            tile = callout_tile(it.get('text'), it.get('sub'), it.get('kind', 'normal'))
            geo.append((c, tile, callout_alpha(c, f)))
        # ordre de pose depuis le bord de la zone : en haut, stack croissant vers le bas ; en bas, stack décroissant
        # vers le haut. La place d'un callout ne s'ouvre (entrée) ou ne se referme (sortie) en douceur que s'il
        # pousse un callout posé après lui, déjà là avant lui ou qui reste après lui ; sinon elle est pleine : des
        # callouts qui sortent ensemble s'effacent sur place au lieu de se replier les uns sur les autres.
        order = geo if z['sens'] == 'bas' else list(reversed(geo))
        y = float(z['y'])
        tmp = []
        for i, (c, tile, a) in enumerate(order):
            k = slot_factor(c, [d for d, _, _ in order[i + 1:]], f)
            if z['sens'] == 'bas':
                tmp.append((c, tile, a, y, zname, z))
                y += k * (tile.height + gap)
            else:
                tmp.append((c, tile, a, y - tile.height, zname, z))
                y -= k * (tile.height + gap)
        placed += tmp if z['sens'] == 'bas' else list(reversed(tmp))
    boxes = []
    for c, tile, a, y, zname, z in placed:
        x = z['x'] - tile.width if z['ancre'].endswith('droite') else z['x']
        yy = y + (1 - a) * O.ANIM['glissement_px']
        boxes.append((c, tile, a, (x, yy, x + tile.width, yy + tile.height), zname))
    # filets
    base_obs = active_rects(F, s, f)
    prims = []
    xi_on = any(o['sequence'] == 'parapegma_xi' and f in o['fmap'] for o in F.ovl)
    for i, (c, tile, a, box, zone) in enumerate(boxes):
        name = None if (s['id'], c['text']) in LEADER_SKIP else leader_name(s, c, f)
        if not name or a <= 0.003:
            continue
        others = [b[3] for j, b in enumerate(boxes) if j != i and b[2] > 0.05]
        obs = base_obs + others
        p = leader_valid(F, s, c, f, base_obs)
        ref, fade = f, 1.0
        if not p:
            # l'ancre vient de sortir (bord de l'image, bande des sous-titres, sous une incrustation) : le filet
            # s'efface en LEADER_HOLD images sur sa dernière position au lieu de disparaître d'un coup
            for k in range(1, LEADER_HOLD + 1):
                if f - k < c['in']:
                    break
                p = leader_valid(F, s, c, f - k, active_rects(F, s, f - k))
                if p:
                    ref, fade = f - k, 1 - k / float(LEADER_HOLD + 1)
                    break
            if not p:
                continue
        # entrée du filet : il se déroule depuis la boîte pendant 8 images à partir de la première image valide
        start = ref
        while start > c['in'] and leader_valid(F, s, c, start - 1, active_rects(F, s, start - 1)):
            start -= 1
        grow = smooth((ref - start + 1) / O.ANIM['entree_images'])
        a = a * fade
        same = [b for b in boxes if b[4] == zone and b[2] > 0.05 and b is not boxes[i]]
        below = any(b[3][1] >= box[3] - 1 for b in same)
        above = any(b[3][3] <= box[1] + 1 for b in same)
        q = attach_point(box, p, obs, below, above)
        if q is None:
            continue
        rr = PP_XI_CLEAR if (xi_on and name == 'sign_under_sun') else LEADER_CLEAR.get(name, LEADER['ring_r'])
        dx, dy = p[0] - q[0], p[1] - q[1]
        L = math.hypot(dx, dy)
        if L - rr < LEADER['min_len']:
            continue
        end = (p[0] - dx / L * rr, p[1] - dy / L * rr)
        tip = (q[0] + (end[0] - q[0]) * grow, q[1] + (end[1] - q[1]) * grow)
        prims.append(('seg', q, tip, a))
        if rr == LEADER['ring_r']:
            prims.append(('ring', p, rr, a * smooth((grow - 0.75) / 0.25)))
        elif name in LEADER_CLEAR:
            prims.append(('dot', end, 3.5, a * smooth((grow - 0.75) / 0.25)))
    for ln in lines:
        p0 = anchor_at(F, ln['from'], f)
        p1 = anchor_at(F, ln['to'], f)
        if not (p0 and p1 and p0[2] and p1[2]):
            continue
        a = smooth((min(ln['out'], s['frames'][1]) - f + 1) / O.ANIM['sortie_images'])
        grow = smooth((f - ln['in'] + 1) / O.ANIM['entree_images'])
        tip = (p0[0] + (p1[0] - p0[0]) * grow, p0[1] + (p1[1] - p0[1]) * grow)
        prims += [('dot', (p0[0], p0[1]), 4.0, a), ('seg', (p0[0], p0[1]), tip, a)]
        if grow > 0.75:
            prims.append(('dot', (p1[0], p1[1]), 4.0, a * smooth((grow - 0.75) / 0.25)))
    draw_strokes(layer, prims)
    for c, tile, a, box, zone in boxes:
        if a > 0.003:
            paste_rgba(layer, O.scale_alpha(tile, a), box[0], box[1])
    return shadowed(layer)


def shadowed(layer):
    """Ombre portée de la charte (overlay.add_shadow) calculée sur la seule partie utile du calque."""
    bb = layer.getchannel('A').getbbox()
    if not bb:
        return None
    m = 40
    x0, y0, x1, y1 = max(0, bb[0] - m), max(0, bb[1] - m), min(W, bb[2] + m), min(H, bb[3] + m)
    part = O.add_shadow(layer.crop((x0, y0, x1, y1)))
    return part, (x0, y0)


# ----------------------------------------------------------------------------- compteur, sous-titres
def counter_state(F, f):
    """(manivelle, alpha, dy) ou None."""
    fr = F.frames[f]
    if fr['counter']:
        first = f
        while first > 1 and F.frames[first - 1]['counter'] and F.frames[first - 1]['seg'] == fr['seg']:
            first -= 1
        # entrée en fondu seulement quand le compteur apparaît au milieu d'un plan (« Tournez-la ») ;
        # aux coupes de plan il arrive et part avec l'image
        s = F.seg[fr['seg']]
        if first > s['frames'][0]:
            u = smooth((f - first + 1) / COUNTER_FADE)
            return fr['crank'], u, (1 - u) * O.ANIM['glissement_px']
        return fr['crank'], 1.0, 0.0
    s = F.seg[fr['seg']]
    if s['kind'] == 'card':      # sous le carton : il s'efface avec l'arrivée du fond
        k = f - s['frames'][0]
        prev = F.frames.get(s['frames'][0] - 1)
        if prev and prev['counter'] and k < COUNTER_FADE + 4:
            return fr['crank'], 1 - smooth((k + 1) / (COUNTER_FADE + 4)), 0.0
    return None


@lru_cache(maxsize=4)
def counter_img(text_key):
    crank = float(text_key)
    img = O.render_counter(crank)
    bb = img.getchannel('A').getbbox()
    return img.crop(bb), bb[:2]


@lru_cache(maxsize=3)
def subtitle_img(text):
    img = O.render_subtitle(text)
    bb = img.getchannel('A').getbbox()
    return img.crop(bb), bb[:2]


def subtitle_at(F, f):
    for sb in F.subs:
        if sb['burn_in'] and sb['in'] <= f <= sb['out']:
            a = smooth(min((f - sb['in'] + 1) / SUB_FADE, (sb['out'] - f + 1) / SUB_FADE))
            return sb, a
    return None


def subtitle_place(F, s, f):
    """Sous-titre de l'image f : (image, x0, y0, alpha) ou None (décalages de 4.3 et 1.3 compris)."""
    st = subtitle_at(F, f)
    if not st:
        return None
    sb, a = st
    im, (x0, y0) = subtitle_img(sb['text'])
    if s['kind'] == 'split' and not s['diagram'].get('rect_px') and f < s.get('inset_until', 10 ** 9):
        x0 = max(24, min(SUB_SPLIT_CENTER_X - im.width / 2, W / 2 - 24 - im.width))
    elif s['id'] in SUB_CENTER_X:
        x0 = SUB_CENTER_X[s['id']] - im.width / 2
    return im, x0, y0, a


def subtitle_rect(F, s, f):
    p = subtitle_place(F, s, f)
    if not p:
        return None
    im, x0, y0, _ = p
    return (x0, y0, x0 + im.width, y0 + im.height)


# ----------------------------------------------------------------------------- une image
class Missing(Exception):
    pass


def get3d(frames_dir, f, sub=None, placeholder_ok=False, seg_id=None):
    p = frame3d_path(frames_dir, f, sub)
    if p:
        return Image.open(p).convert('RGBA'), 'render'
    if not placeholder_ok:
        raise Missing('%s%04d' % ((sub + '/') if sub else '', f))
    if sub:
        return placeholder_base(seg_id, (480, 480), True).copy(), 'placeholder'
    return placeholder(seg_id, f), 'placeholder'


def compose(f, frames_dir, placeholder_ok=False, bascule_blend=True):
    F = film()
    s = F.segment(f)
    kind = s['kind']
    src = '2d'
    # 1. fond
    if kind in ('3d', 'split'):
        base, src = get3d(frames_dir, f, placeholder_ok=placeholder_ok, seg_id=s['id'])
        if bascule_blend and s['id'] == '5.1' and f in (BASCULE_FRAME - 1, BASCULE_FRAME) and src == 'render':
            other_f = BASCULE_FRAME if f == BASCULE_FRAME - 1 else BASCULE_FRAME - 1
            p = frame3d_path(frames_dir, other_f)
            if p:
                other = Image.open(p).convert('RGBA')
                base = Image.blend(base, other, 1 / 3.0)
            elif not placeholder_ok:
                raise Missing('%04d' % other_f)
    elif kind == 'diagram':
        d = s['diagram']
        img = load_rgb(str(seq_path(d['dir'], d['pattern'], d['fmap'][f])))
        fp = fit_params(s['id'])
        base = (apply_fit(img, fp) if fp else img).convert('RGBA')
    elif kind == 'map':
        o = next(o for o in F.ovl if o['sequence'] == s.get('insert', 'map'))
        base = load_rgb(str(seq_path(o['dir'], o['pattern'], o['fmap'][f]))).convert('RGBA')
    elif kind == 'card':
        o = next(o for o in F.ovl if o['sequence'] == 'end_card_texte')
        base = load_rgb(str(rel(o['background']))).convert('RGBA')
        f0, f1, lo = F.card['machine_fade']
        m = 1.0 - (1.0 - lo) * smooth((f - f0) / float(f1 - f0))
        p = frame3d_path(frames_dir, f)
        if p:
            base = Image.blend(base, Image.open(p).convert('RGBA'), m)
            src = 'render'
        elif not placeholder_ok:
            raise Missing('%04d' % f)
        else:
            src = 'placeholder'
    else:
        raise ValueError('plan de nature inconnue : %s' % kind)
    # 2. écran partagé
    if kind == 'split' and f < s.get('inset_until', 10 ** 9):
        d = s['diagram']
        if f in d['fmap']:
            path = seq_path(d['dir'], d['pattern'], d['fmap'][f])
            if d.get('rect_px'):
                keys = sorted(d['fmap'])
                a = smooth(min((f - keys[0] + 1) / INSET_FADE_IN, (keys[-1] - f + 1) / INSET_FADE_OUT))
                framed(base, load_rgb(str(path)), d['rect_px'], a)
            else:
                composite_layer(base, path)
    # 3. incrustation 3D (3.4)
    ins = s.get('inset')
    if ins:
        img, src2 = get3d(frames_dir, f, 'inset_3_4', placeholder_ok, s['id'])
        if src2 == 'placeholder' and src == 'render':
            src = 'placeholder'
        a = smooth((f - s['frames'][0] + 1) / INSET_FADE_IN)
        framed(base, img, ins['rect_px'], a)
    # 4. incrustations 2D
    for o in F.ovl:
        if f not in o['fmap'] or o['sequence'] in ('map', 'end_card_texte') or \
                o['sequence'].startswith('chapter_title_'):
            continue
        path = seq_path(o['dir'], o['pattern'], o['fmap'][f])
        if o['sequence'] == 'parapegma_xi':
            p = anchor_at(F, o['anchor'], f)
            if p:
                ax, ay = o.get('anchor_px_in_image', [W // 2, H // 2])
                composite_layer(base, path, 1.0, p[0] - ax, p[1] - ay)
        elif o['sequence'] == 'parapegma_ligne':
            p = anchor_at(F, o['anchor'], f)
            if p:
                place_ligne(base, path, p)
        else:
            composite_layer(base, path)
    if kind == 'card':
        o = next(o for o in F.ovl if o['sequence'] == 'end_card_texte')
        if f in o['fmap']:
            composite_layer(base, seq_path(o['dir'], o['pattern'], o['fmap'][f]))
    # 5. callouts et filets
    cl = callout_layer(F, s, f)
    if cl:
        paste_rgba(base, cl[0], *cl[1])
    # 6. compteur
    cs = counter_state(F, f)
    if cs:
        crank, a, dy = cs
        im, (x0, y0) = counter_img('%.9f' % crank)
        paste_rgba(base, O.scale_alpha(im, a), x0, y0 + dy)
    # 7. titres de chapitre (texte masqué au-delà du bord de la boîte pendant qu'elle s'ouvre)
    for o in F.ovl:
        if o['sequence'].startswith('chapter_title_') and f in o['fmap']:
            got = title_clipped(str(seq_path(o['dir'], o['pattern'], o['fmap'][f])),
                                str(seq_path(o['dir'], o['pattern'], max(o['fmap'].values()) // 2)))
            if got:
                paste_rgba(base, got[0], *got[1])
    # 8. sous-titres
    sp = subtitle_place(F, s, f)
    if sp:
        im, x0, y0, a = sp
        paste_rgba(base, O.scale_alpha(im, a), x0, y0)
    out = base.convert('RGB')
    # 9. fondus au noir
    k = 1.0
    if f <= FADE_IN_FRAMES + 1:
        k = smooth((f - 1) / FADE_IN_FRAMES)
    if f > F.n - FADE_OUT_FRAMES:
        k = min(k, 1 - smooth((f - (F.n - FADE_OUT_FRAMES)) / FADE_OUT_FRAMES))
    if k < 0.999:
        out = Image.eval(out, lambda v, k=k: int(v * k + 0.5))
    return out, src


@lru_cache(maxsize=8)
def ligne_scaled(path):
    im = Image.open(path).convert('RGBA')
    w, h = int(round(W * PP_LIGNE_SCALE)), int(round(H * PP_LIGNE_SCALE))
    sm = im.resize((w, h), Image.LANCZOS)
    bb = sm.getchannel('A').getbbox()
    return (sm.crop(bb), bb) if bb else None


def place_ligne(base, path, anchor):
    """Ligne du parapegme (centre horizontal x = 960, milieu des lettres y ≈ 185 dans son image) réduite et posée sous
    le centre de la plaque du haut, gardée dans la zone de sécurité."""
    got = ligne_scaled(str(path))
    if not got:
        return
    im, bb = got
    sc = PP_LIGNE_SCALE
    ox = anchor[0] - 960 * sc
    oy = anchor[1] + PP_LIGNE_DY - 185 * sc
    x0 = ox + bb[0]
    x0 = min(max(x0, O.SAFE['x']), W - O.SAFE['x'] - im.width)
    paste_rgba(base, im, x0, oy + bb[1])


# ----------------------------------------------------------------------------- lots, reprise
def out_path(out_dir, f):
    return Path(out_dir) / ('%05d.png' % f)


def done_already(F, f, out_dir, frames_dir, placeholder_mode):
    p = out_path(out_dir, f)
    if not p.exists() or p.stat().st_size == 0:
        return False
    try:
        info = Image.open(p).text
    except Exception:
        return False
    if info.get('comp_version') != VERSION:
        return False
    if info.get('comp_src') == 'placeholder':
        # refaire si les rendus sont là maintenant
        if all(frame3d_path(frames_dir, ff, sub) for ff, sub in needs(F, f)):
            return False
        return placeholder_mode
    mt = p.stat().st_mtime
    for ff, sub in needs(F, f):
        q = frame3d_path(frames_dir, ff, sub)
        if q and q.stat().st_mtime > mt:
            return False
    return True


ARGS = None


def _init(args):
    global ARGS
    ARGS = args
    film()


def work(f):
    a = ARGS
    t0 = time.time()
    try:
        img, src = compose(f, a['frames_dir'], a['placeholder'], a['bascule_blend'])
    except Missing as e:
        return f, 'missing', str(e), time.time() - t0
    if a['scale'] != 1.0:
        size = (int(round(W * a['scale'])), int(round(H * a['scale'])))
        img = img.reduce(2) if a['scale'] == 0.5 else img.resize(size, Image.LANCZOS)
    meta = PngImagePlugin.PngInfo()
    meta.add_text('comp_version', VERSION)
    meta.add_text('comp_src', src)
    meta.add_text('comp_frame', str(f))
    p = out_path(a['out'], f)
    tmp = p.with_name('.%s.part.png' % p.stem)
    img.save(tmp, 'PNG', compress_level=a['compress'], pnginfo=meta)
    os.replace(tmp, p)
    return f, 'ok', src, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--start', type=int, default=1)
    ap.add_argument('--end', type=int, default=None)
    ap.add_argument('--frames', help='liste d\'images (1-based, « 460,1446,3363 » ou « 400-420 »)')
    ap.add_argument('--only-available', action='store_true', help='sauter les images dont le rendu 3D manque')
    ap.add_argument('--placeholder', action='store_true',
                    help='fond provisoire (parchemin, plan, image) quand le rendu 3D manque : animatique')
    ap.add_argument('--scale', type=float, default=1.0, help='0.5 -> 960 x 540 (aperçus)')
    ap.add_argument('--out', help='dossier de sortie (défaut : film/comp, ou film/preview_comp avec --placeholder '
                                  'ou --scale ≠ 1)')
    ap.add_argument('--frames-dir', default=str(FILM / 'frames'))
    ap.add_argument('--overwrite', action='store_true')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--compress', type=int, default=3, help='niveau de compression PNG (0-9)')
    ap.add_argument('--no-bascule-blend', action='store_true', help='5.1 : pas de fondu de 2 images à la bascule')
    ap.add_argument('--nice', type=int, default=10)
    args = ap.parse_args()

    F = film()
    end = args.end or F.n
    if args.frames:
        fl = []
        for part in args.frames.split(','):
            if '-' in part:
                a, b = part.split('-')
                fl += list(range(int(a), int(b) + 1))
            else:
                fl.append(int(part))
        frames = [f for f in fl if 1 <= f <= F.n]
    else:
        frames = list(range(max(1, args.start), min(F.n, end) + 1))
    out = Path(args.out) if args.out else (FILM / ('preview_comp' if (args.placeholder or args.scale != 1.0)
                                                   else 'comp'))
    if not args.out and args.placeholder and args.scale == 1.0:
        out = FILM / 'preview_comp_full'
    out.mkdir(parents=True, exist_ok=True)
    try:
        cur = os.nice(0)
        if cur < args.nice:
            os.nice(args.nice - cur)
    except OSError:
        pass

    todo, skipped, unavailable = [], 0, []
    for f in frames:
        if not args.overwrite and done_already(F, f, out, args.frames_dir, args.placeholder):
            skipped += 1
            continue
        if args.only_available and not args.placeholder:
            if not all(frame3d_path(args.frames_dir, ff, sub) for ff, sub in needs(F, f)):
                unavailable.append(f)
                continue
        todo.append(f)
    print('[comp] %d images demandées -> %s : %d à faire, %d déjà faites, %d sans rendu 3D (sautées)'
          % (len(frames), out, len(todo), skipped, len(unavailable)), flush=True)
    for s in ('6.5a', '7.3a'):
        fp = fit_params(s) if s in F.seg else None
        if fp and any(F.frames[f]['seg'] == s for f in todo):
            print('[comp] %s : schéma réduit à %.3f (point fixe x=%d, y=%d) pour les sous-titres' % (s, *fp),
                  flush=True)
    if not todo:
        return 0
    a = {'frames_dir': args.frames_dir, 'placeholder': args.placeholder, 'scale': args.scale, 'out': str(out),
         'compress': args.compress, 'bascule_blend': not args.no_bascule_blend}
    t0 = time.time()
    stats = {'ok': 0, 'missing': 0}
    srcs = {}
    missing = []
    n = len(todo)
    if args.workers <= 1:
        _init(a)
        it = map(work, todo)
        pool = None
    else:
        import multiprocessing as mp
        pool = mp.get_context('spawn').Pool(min(3, args.workers), initializer=_init, initargs=(a,))
        it = pool.imap_unordered(work, todo, chunksize=2)
    try:
        for i, (f, st, info, dt) in enumerate(it, 1):
            stats[st] = stats.get(st, 0) + 1
            if st == 'ok':
                srcs[info] = srcs.get(info, 0) + 1
            else:
                missing.append(info)
            if i % 50 == 0 or i == n:
                el = time.time() - t0
                print('[comp] %d/%d  %.2f s/image (mur)  reste ~%.1f min' % (i, n, el / i, el / i * (n - i) / 60),
                      flush=True)
    finally:
        if pool:
            pool.close()
            pool.join()
    print('[comp] terminé en %.1f min : %d écrites (%s), %d manquantes%s'
          % ((time.time() - t0) / 60, stats['ok'], ', '.join('%s %d' % kv for kv in sorted(srcs.items())),
             stats['missing'], (' : ' + ' '.join(missing[:12]) + (' …' if len(missing) > 12 else '')) if missing
             else ''), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
