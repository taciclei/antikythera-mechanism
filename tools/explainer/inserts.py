#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Incrustations 2D du film « Le ciel dans une boîte » (build/out/explainer/script.md), dans l'identité des schémas
de tools/explainer/diagrams.py (mêmes polices, palette, courbes d'animation, classe Frame).

Séquences PNG 1920x1080, 25 i/s, dans build/out/explainer/inserts/<nom>/%04d.png (première image 0001), un aperçu
MP4 par séquence (<nom>_apercu.mp4, les calques transparents posés sur une image de la machine) et timing.json
(images, durées, boîtes, segments, ancres, manivelle image par image, textes affichés).

  map              plan 1.3   carte de la mer au sud de la Grèce (Natural Earth 10 m, domaine public), épave qui pulse
                              au nord-est d'Anticythère, « Printemps 1900 », « Pêcheurs d'éponges de Symi »,
                              « 40–50 m de fond ». Plein écran, opaque.
  phases           plan 3.4   vue du dessus Soleil-Terre-Lune, « aiguilles » Soleil et Lune, boule des phases ; la Lune
                              suit l'élongation de notre modèle (engine.py) pour la manivelle 0,972 -> 1,009 (timing.json).
  metonic_cell     plan 5.2   case agrandie « ΦΟΙΝΙΚΑΙΟΣ / L Α » : Phoinikaios… an 1 (illustration d'après Freeth
                              et al. 2008).
  games_banner     plan 5.3   bandeau des 4 années d'origine, curseur synchronisé sur l'aiguille des Jeux (manivelle
                              3,0 -> 5,95), an 1 surligné à l'arrivée sur ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ.
  glyph_anatomy    plan 6.3   anatomie d'un signe d'éclipse (Σ, ΩΡ + chiffre, lettre d'index), marquée « exemple ».
  parapegma_line   plan 7.2   repère Ξ + ligne « La Pléiade se lève le matin » qui s'écrit (or gravé), « illustration ».
  parapegma_xi     plan 7.2   le repère Ξ seul, centré sur (960, 540), à déplacer sur l'échelle du zodiaque.
  parapegma_ligne  plan 7.2   la ligne seule (sans le repère).
  end_card         plan 7.6   carton final opaque (parchemin + vignettage) : les 6 étapes, la question, les crédits.
  end_card_texte   plan 7.6   mêmes textes sur fond transparent (pour poser la machine en fondu derrière).
  chapter_title_N  chapitres  7 titres en bas à gauche (« 1 · Le ciel dans une boîte » … « 7 · Et la navigation ? »),
                              titres lus dans script.md.

Les calques transparents (RGBA, alpha droit) portent l'ombre portée de la charte (overlay.py) ; la charte des
callouts, du compteur et des sous-titres est écrite par `overlay.py style` (build/out/explainer/film/overlay_style.json).
Tout texte passe par typo() : espace insécable avant « : » et dans « », espace fine insécable avant ; ! ?, insécable
entre un nombre et son unité ; le grec et les chiffres en Gentium sont mis à la hauteur de capitale du texte.
index.json (build/out/explainer/inserts/) liste les séquences rendues : chemin, images, i/s, transparence, plan visé.

Usage (Python du venv ~/voxtral-tts : matplotlib, Pillow, numpy) :
  ~/voxtral-tts/bin/python tools/explainer/inserts.py                       # tout (≈ 2 000 images)
  ~/voxtral-tts/bin/python tools/explainer/inserts.py phases games_banner   # quelques séquences
  ~/voxtral-tts/bin/python tools/explainer/inserts.py map --frames 1,60,120 --out /tmp/x   # images tests
  ~/voxtral-tts/bin/python tools/explainer/inserts.py --check               # vérifie les textes (honnêteté)
  ~/voxtral-tts/bin/python tools/explainer/inserts.py --index               # réécrit index.json seulement
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import urllib.request
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import diagrams as D  # noqa: E402  (matplotlib en mode Agg, polices, palette, Frame)
import overlay as OV  # noqa: E402  (charte, ombre portée)
from diagrams import (BG, BRASS, BRONZE, EARTH, EARTH_NIGHT, FPS, GOLD, H, HYP, INK, MOON, MUTED, PAPER,  # noqa: E402
                      RULE, RULE_STRONG, SUN, W, Frame, arrow, clamp01, ease, fp, mix, ramp, smooth, star4,
                      vgradient)
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import to_rgba  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle, Wedge  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / 'build' / 'out' / 'explainer' / 'inserts'
SCRIPT_MD = ROOT / 'build' / 'out' / 'explainer' / 'script.md'
LOOK2 = ROOT / 'build' / 'out' / 'explainer' / 'look2'
GEO_DIR = ROOT / 'build' / 'cache' / 'geo'

P = OV.PALETTE
BRONZE_FORT = P['bronze_fort']
VERDIGRIS = P['modele']
ALERT = P['alerte']
ENGRAVE = P['grave']
BRASS_HI = '#F4E1B2'
BRASS_LO = '#D9B56E'
BRASS_EDGE = '#A67A37'
GROOVE = '#5A3F1E'

# la charte d'habillage (overlay.py) et les schémas (diagrams.py) doivent parler des mêmes couleurs
assert (P['parchemin'], P['papier'], P['encre'], P['encre_douce'], P['bronze'], P['or'], P['laiton'],
        P['hypothese'], P['filet_fort']) == (BG, PAPER, INK, MUTED, BRONZE, GOLD, BRASS, HYP, RULE_STRONG)


# ============================================================================= aides communes
_MEAS = None


@lru_cache(maxsize=None)
def mw(s, key, px):
    """largeur (px) d'un texte telle que matplotlib la dessine (mesurée une fois par processus)"""
    global _MEAS
    if _MEAS is None:
        fig = plt.figure(figsize=(W / D.DPI, H / D.DPI), dpi=D.DPI)
        _MEAS = (fig, fig.canvas.get_renderer())
    fig, rend = _MEAS
    t = fig.text(0, 0, s, fontproperties=fp(key, px))
    wd = t.get_window_extent(renderer=rend).width
    t.remove()
    return wd


NBSP, NNBSP = ' ', ' '     # espace insécable, espace fine insécable


@lru_cache(maxsize=None)
def typo(s):
    """Typographie française de tout texte affiché : espace insécable avant « : » et à l'intérieur des guillemets
    « », espace fine insécable avant ; ! ?, insécable entre un nombre et son unité (40–50 m, 50 km, +8 h) et dans
    « An 1 ». Idempotente."""
    s = re.sub(r'[   ]*:(?=\s|$)', NBSP + ':', s)
    s = re.sub(r'[   ]*([;!?])', NNBSP + r'\1', s)
    s = re.sub(r'«[   ]*', '«' + NBSP, s)
    s = re.sub(r'[   ]*»', NBSP + '»', s)
    s = re.sub(r'(\d) (m|km|h|j|ans?)\b', r'\1' + NBSP + r'\2', s)
    s = re.sub(r'\b(An|an|AN) (\d)', r'\1' + NBSP + r'\2', s)
    return s


def plain(s):
    """texte comparable à script.md (espaces insécables -> espaces)"""
    return s.replace(NBSP, ' ').replace(NNBSP, ' ')


# Gentium Book Plus a des capitales plus basses (0,615 em) qu'IBM Plex Sans et Marcellus (0,70 em) : dans un texte
# en Plex ou en Marcellus, le grec et les chiffres en Gentium sont agrandis pour avoir la même hauteur de capitale
CAP_SCALE = 0.70 / 0.615


def runs_of(s, key):
    """séquences (texte, police, échelle) après typographie : grec en Gentium Book Plus Bold ; dans un texte en
    Marcellus, les chiffres (le « 1 » de Marcellus se lit comme un « I ») et l'espace fine insécable (absente de
    Marcellus) passent en Gentium Book Plus"""
    out = []
    for a, k in OV.split_runs(typo(s), key):
        if k != 'display':
            out.append((a, k))
            continue
        for ch in a:
            kk = 'serif' if (ch.isdigit() or ch == NNBSP) else 'display'
            if out and out[-1][1] == kk:
                out[-1] = (out[-1][0] + ch, kk)
            else:
                out.append((ch, kk))
    return [(a, k, CAP_SCALE if (k in ('greek', 'serif') and key not in ('greek', 'serif', 'quote')
                                 and a.strip(NNBSP)) else 1.0) for a, k in out]


def txt_w(s, key, px):
    return sum(mw(a, k, px * sc) for a, k, sc in runs_of(s, key))


def txt(fr, x, y, s, key, px, color, alpha=1.0, ha='left', z=50, halo=None, halo_w=6, greek_color=None, clip=None):
    """texte sur une ligne de base, les lettres grecques en Gentium Book Plus Bold (comme overlay.split_runs)"""
    if alpha <= 0.003 or not s:
        return 0
    runs = runs_of(s, key)
    total = sum(mw(a, k, px * sc) for a, k, sc in runs)
    x0 = x - (total if ha == 'right' else total / 2 if ha == 'center' else 0)
    for a, k, sc in runs:
        col = greek_color if (greek_color and k == 'greek' and key != 'greek') else color
        fr.text(x0, y, a, px * sc, k, col, alpha, z=z, halo=halo, halo_w=halo_w, clip=clip)
        x0 += mw(a, k, px * sc)
    return total


def spaced(fr, x, y, s, key, px, color, alpha=1.0, track=0.16, ha='center', z=50, halo=None, halo_w=6):
    """texte espacé (petites capitales, noms de régions)"""
    if alpha <= 0.003:
        return 0
    s = typo(s)
    ws = [mw(c, key, px) for c in s]
    total = sum(ws) + track * px * (len(s) - 1)
    x0 = x - (total if ha == 'right' else total / 2 if ha == 'center' else 0)
    for c, w_ in zip(s, ws):
        fr.text(x0, y, c, px, key, color, alpha, z=z, halo=halo, halo_w=halo_w)
        x0 += w_ + track * px
    return total


def card(fr, x0, y0, x1, y1, alpha, fill=PAPER, fill_a=0.95, edge=RULE_STRONG, lw=2.5, r=18, z=1):
    if alpha <= 0.003:
        return None
    p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=f'round,pad=0,rounding_size={r}',
                       facecolor=to_rgba(fill, fill_a * alpha), edgecolor=to_rgba(edge, alpha), lw=lw, zorder=z)
    fr.ax.add_patch(p)
    return p


def clip_box(fr, x0, y0, x1, y1, r=18):
    p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=f'round,pad=0,rounding_size={r}', facecolor='none',
                       edgecolor='none', transform=fr.ax.transData)
    fr.ax.add_patch(p)
    return p


def chip(fr, x, y, s, color, alpha, ha='left', px=24, key='sansm', z=60, fill=PAPER):
    """étiquette arrondie (hypothèse, modèle, illustration, exemple) ; y = ligne de base du texte"""
    if alpha <= 0.003:
        return 0
    w_ = txt_w(s, key, px)
    padx, h_ = 12, px * 1.55
    x0 = x - (w_ + 2 * padx if ha == 'right' else (w_ + 2 * padx) / 2 if ha == 'center' else 0)
    fr.ax.add_patch(FancyBboxPatch((x0, y - px * 1.08), w_ + 2 * padx, h_, boxstyle='round,pad=0,rounding_size=9',
                                   facecolor=to_rgba(mix(fill, color, 0.07), alpha), edgecolor=to_rgba(color, alpha),
                                   lw=1.8, zorder=z))
    txt(fr, x0 + padx, y, s, key, px, color, alpha, z=z + 1)
    return w_ + 2 * padx


def heading(fr, x, y, s, alpha, px=26, ha='left', color=BRONZE):
    return spaced(fr, x, y, s.upper(), 'sansb', px, color, alpha, track=0.06, ha=ha)


def enter(f, a, b, dist=16):
    """(alpha, décalage vertical) d'une entrée entre les images a et b"""
    u = ramp(f, a, b)
    return u, (1 - u) * dist


def life(f, n, fin=10, fout=10):
    """opacité globale d'un calque : entrée sur fin images, sortie sur les fout dernières"""
    return ramp(f, 0, fin) * (1 - ramp(f, n - fout, n - 1)) if fout else ramp(f, 0, fin)


def save_frame(fr, path, rgba, shadow):
    fr.fig.canvas.draw()
    buf = np.asarray(fr.fig.canvas.buffer_rgba())
    im = Image.fromarray(buf.copy(), 'RGBA')
    plt.close(fr.fig)
    if rgba:
        if shadow:
            im = OV.add_shadow(im)
        im.save(path, compress_level=4)
    else:
        im.convert('RGB').save(path, compress_level=4)


def engraved(fr, x, y, s, key, px, alpha, z=30, rotation=0, ha='center', dark=ENGRAVE, light='#F8EBC8'):
    """lettres gravées dans le laiton : reflet clair décalé puis trait sombre"""
    if alpha <= 0.003:
        return
    for dx, dy, col, a in ((1.4, 1.6, light, 0.9), (0, 0, dark, 1.0)):
        t = fr.ax.text(x + dx, y + dy, s, fontproperties=fp(key, px), color=col, alpha=alpha * a, ha=ha,
                       va='baseline', zorder=z + (0.1 if dx == 0 else 0), rotation=rotation, rotation_mode='anchor')


# ============================================================================= 1. CARTE (plan 1.3)
NE_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson'
MAP_BBOX = (19.4, 34.0, 28.8, 38.6)
MAP_N = 120
PHI0 = math.radians(36.1)
COSP = math.cos(PHI0)
# vue : lent travelling avant vers Anticythère
MAP_V0 = (23.72, 36.02, 400.0)       # (longitude, latitude du centre, px par degré de latitude)
MAP_V1 = (23.50, 35.97, 452.0)
ANTIKYTHERA = (23.30, 35.865)
KYTHERA = (22.99, 36.25)
SYMI = (27.84, 36.60)
SEA_TOP, SEA_BOT = '#C3D3CF', '#AFC4C3'
SEA_LINE = '#D6E2DD'
LAND = '#F5EBD6'
WAVE = '#7F9A9E'


def _clip_poly(pts, bbox):
    """Sutherland-Hodgman : anneau (liste de (lon, lat)) découpé par un rectangle"""
    x0, y0, x1, y1 = bbox
    edges = [(lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
             (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))]
    out = list(pts)
    for inside, inter in edges:
        if not out:
            break
        inp, out = out, []
        prev = inp[-1]
        for cur in inp:
            if inside(cur):
                if not inside(prev):
                    out.append(inter(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(inter(prev, cur))
            prev = cur
    return out


def _dp(pts, tol):
    """Douglas-Peucker (itératif)"""
    pts = np.asarray(pts, float)
    n = len(pts)
    if n < 4:
        return pts
    keep = np.zeros(n, bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        seg = pts[i + 1:j]
        ab = b - a
        L = math.hypot(*ab)
        if L < 1e-12:
            d = np.hypot(*(seg - a).T)
        else:
            d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(d))
        if d[k] > tol:
            m = i + 1 + k
            keep[m] = True
            stack += [(i, m), (m, j)]
    return pts[keep]


@lru_cache(maxsize=None)
def geo_rings():
    """anneaux côtiers (lon, lat) de la zone, découpés et simplifiés ; cache build/cache/geo/aegee_10m.json"""
    cache = GEO_DIR / 'aegee_10m.json'
    if cache.exists():
        return [np.array(r) for r in json.loads(cache.read_text())['anneaux']]
    GEO_DIR.mkdir(parents=True, exist_ok=True)
    src = GEO_DIR / 'ne_10m_land.geojson'
    if not src.exists():
        print('  téléchargement Natural Earth 10 m (domaine public)…', file=sys.stderr)
        urllib.request.urlretrieve(NE_URL, src)
    d = json.loads(src.read_text())
    rings = []
    for ft in d['features']:
        g = ft['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            ring = poly[0]
            xs = [c[0] for c in ring]
            ys = [c[1] for c in ring]
            if max(xs) < MAP_BBOX[0] or min(xs) > MAP_BBOX[2] or max(ys) < MAP_BBOX[1] or min(ys) > MAP_BBOX[3]:
                continue
            c = _clip_poly([(p[0], p[1]) for p in ring], MAP_BBOX)
            if len(c) >= 3:
                s = _dp(c + [c[0]], 0.0022)
                if len(s) >= 4:
                    rings.append(s)
    cache.write_text(json.dumps({'source': 'Natural Earth 10 m land (domaine public), ' + NE_URL,
                                 'bbox': MAP_BBOX, 'tolerance_deg': 0.0022,
                                 'anneaux': [np.round(r, 5).tolist() for r in rings]}))
    return rings


@lru_cache(maxsize=None)
def island_ring(lon, lat):
    from matplotlib.path import Path as MPath
    for r in geo_rings():
        if MPath(r).contains_point((lon, lat)):
            return r
    return None


def wreck_lonlat():
    """épave : au nord-est d'Anticythère (faits.md 1.5), au pied de la côte (40–50 m de fond)"""
    r = island_ring(*ANTIKYTHERA)
    k = int(np.argmax(r[:, 0] + r[:, 1]))
    return float(r[k, 0]) + 0.010, float(r[k, 1]) + 0.010


def map_view(f):
    u = ease(f / (MAP_N - 1.0))
    return tuple(a + (b - a) * u for a, b in zip(MAP_V0, MAP_V1))


def proj(lon, lat, view):
    lc, pc, k = view
    return W / 2 + (np.asarray(lon) - lc) * COSP * k, H / 2 - (np.asarray(lat) - pc) * k


@lru_cache(maxsize=None)
def wave_seeds():
    rng = np.random.default_rng(1900)
    pts = []
    step = 0.11
    for i, lat in enumerate(np.arange(34.3, 38.0, step * 0.8)):
        for lon in np.arange(19.8, 28.0, step):
            pts.append((lon + (i % 2) * step / 2 + rng.uniform(-0.03, 0.03), lat + rng.uniform(-0.02, 0.02),
                        rng.uniform(0, 2 * np.pi), rng.uniform(0.7, 1.15)))
    return np.array(pts)


def map_frame(f):
    fr = Frame(bg=BG)
    ax = fr.ax
    view = map_view(f)
    k = view[2]
    # --- mer : dégradé, graticule, vaguelettes animées
    fr.img(vgradient([(0, SEA_TOP), (1, SEA_BOT)]), 0, 0, W, H, z=0)
    for lon in range(19, 29):
        x, _ = proj(lon, 0, view)
        ax.plot([x, x], [0, H], color='#FFFFFF', lw=1.2, alpha=0.22, zorder=1)
    for lat in range(34, 39):
        _, y = proj(0, lat, view)
        ax.plot([0, W], [y, y], color='#FFFFFF', lw=1.2, alpha=0.22, zorder=1)
    S = wave_seeds()
    wlon = S[:, 0] + 0.0016 * f           # houle poussée vers l'est-sud-est
    wlat = S[:, 1] - 0.0005 * f
    X, Y = proj(wlon, wlat, view)
    vis = (X > -30) & (X < W + 30) & (Y > -30) & (Y < H + 30)
    xs = np.linspace(-1, 1, 9)
    segs, cols = [], []
    for x_, y_, ph, sc in zip(X[vis], Y[vis], S[vis, 2], S[vis, 3]):
        a = 0.5 + 0.5 * math.sin(ph + 2 * math.pi * f / 50.0)        # scintillement (période 2 s)
        if a < 0.08:
            continue
        ww = 11 * sc * k / 420
        segs.append(np.column_stack([x_ + ww * xs, y_ - 2.6 * sc * np.sin(np.pi * (xs + 1))]))
        cols.append(to_rgba(WAVE, 0.55 * a))
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=1.6, zorder=2, capstyle='round'))
    # --- terres : lignes d'eau le long des côtes, remplissage, trait de côte
    rings = geo_rings()
    for r in rings:
        x, y = proj(r[:, 0], r[:, 1], view)
        if x.max() < -50 or x.min() > W + 50 or y.max() < -50 or y.min() > H + 50:
            continue
        ax.plot(x, y, color=SEA_LINE, lw=22, alpha=0.45, zorder=3, solid_joinstyle='round')
        ax.plot(x, y, color=SEA_LINE, lw=9, alpha=0.75, zorder=3.1, solid_joinstyle='round')
        ax.add_patch(Polygon(np.column_stack([x, y]), closed=True, facecolor=LAND, edgecolor=BRONZE, lw=1.6,
                             zorder=4, joinstyle='round'))
    # --- vignettage léger
    yy, xx = np.mgrid[-1:1:108j, -1:1:192j]
    vg = np.zeros((108, 192, 4))
    vg[..., :3] = np.array(to_rgba('#4A3A26')[:3])
    vg[..., 3] = 0.20 * np.clip(np.hypot(xx * 0.9, yy) - 0.55, 0, 1) ** 1.5
    fr.img(vg, 0, 0, W, H, z=40)

    # --- noms (terres et îles) : la carte est lisible dès la première image
    a_lbl = 1.0
    x, y = proj(22.45, 36.98, view)          # sur le Taygète : reste dans le cadre jusqu'à la fin du travelling
    spaced(fr, float(x), float(y), 'PÉLOPONNÈSE', 'display', 36, MUTED, a_lbl, track=0.2, z=20, halo=LAND, halo_w=9)
    x, y = proj(24.80, 35.26, view)
    spaced(fr, float(x), float(y), 'CRÈTE', 'display', 44, MUTED, a_lbl, track=0.3, z=20)
    x, y = proj(KYTHERA[0] + 0.15, KYTHERA[1] - 0.02, view)
    txt(fr, float(x), float(y), 'Cythère', 'sansm', 32, INK, a_lbl, z=21, halo=SEA_TOP, halo_w=7)
    x, y = proj(ANTIKYTHERA[0] - 0.07, ANTIKYTHERA[1] - 0.075, view)
    txt(fr, float(x), float(y), 'Anticythère', 'sansm', 32, INK, a_lbl, ha='right', z=21, halo=SEA_TOP, halo_w=7)

    # --- épave : point qui pulse (période 1,2 s)
    wl = wreck_lonlat()
    ex, ey = [float(v) for v in proj(*wl, view)]
    a_w = ramp(f, 6, 16)
    if a_w > 0:
        for off in (0.0, 0.5):
            ph = ((f - 6) / 30.0 + off) % 1.0
            ax.add_patch(Circle((ex, ey), 9 + 46 * ph, facecolor='none', edgecolor=ALERT, lw=3.2 * (1 - ph) + 0.8,
                                alpha=a_w * 0.85 * (1 - ph) ** 1.3, zorder=30))
        fr.glow(ex, ey, 34, ALERT, alpha=0.35 * a_w, z=29)
        ax.add_patch(Circle((ex, ey), 8.5, facecolor=ALERT, edgecolor=PAPER, lw=2.2, alpha=a_w, zorder=31))
    a_e, dy = enter(f, 12, 24, 10)
    txt(fr, ex + 30, ey - 4 + dy, 'épave', 'sansb', 36, ALERT, a_e, z=32, halo=SEA_TOP, halo_w=8)
    a_p, dy = enter(f, 44, 56, 10)
    txt(fr, ex + 30, ey + 38 + dy, '40–50 m de fond', 'sansm', 32, INK, a_p, z=32, halo=SEA_TOP, halo_w=8)

    # --- Symi : hors carte, vers l'est
    a_s, dx = enter(f, 30, 42, 14)
    if a_s > 0:
        _, sy = proj(*SYMI, view)
        sy = float(np.clip(sy, 200, 700))
        xr = W - 70
        arrow(fr, xr - 150 - dx, sy, xr - dx, sy, INK, lw=3, alpha=a_s, head=16, z=33)
        txt(fr, xr - 164 - dx, sy + 11, 'Symi', 'sansb', 34, INK, a_s, ha='right', z=33, halo=SEA_TOP, halo_w=8)

    # --- échelle et nord (en haut à droite)
    km = 50.0
    Lpx = km / 111.2 * k
    xr, yb = W - 96, 1012
    a_sc = 0.9
    ax.plot([xr - Lpx, xr], [yb, yb], color=INK, lw=3, alpha=a_sc, zorder=35, solid_capstyle='butt')
    for xx_ in (xr - Lpx, xr - Lpx / 2, xr):
        ax.plot([xx_, xx_], [yb - 9, yb + 1], color=INK, lw=2, alpha=a_sc, zorder=35)
    txt(fr, xr - Lpx / 2, yb - 18, '50 km', 'sansm', 26, INK, a_sc, ha='center', z=35, halo=SEA_TOP, halo_w=6)
    nx = xr - Lpx - 60
    ax.add_patch(Polygon([(nx, yb - 46), (nx - 11, yb - 16), (nx + 11, yb - 16)], closed=True, facecolor=INK,
                         alpha=a_sc, zorder=35, lw=0))
    txt(fr, nx, yb + 12, 'N', 'sansb', 26, INK, a_sc, ha='center', z=35, halo=SEA_TOP, halo_w=6)

    # --- cartouche : Printemps 1900, pêcheurs d'éponges de Symi
    a_c, dy = enter(f, 16, 28, 14)
    if a_c > 0:
        x0, y0 = 96, 706
        w1 = txt_w('Printemps 1900', 'display', 76)
        w2 = txt_w("Pêcheurs d'éponges de Symi", 'sansm', 38)
        x1 = x0 + 40 + max(w1, w2) + 34
        card(fr, x0, y0 + dy, x1, y0 + 176 + dy, a_c, fill_a=0.93, z=45)
        ax.add_patch(FancyBboxPatch((x0 + 12, y0 + 18 + dy), 6, 140, boxstyle='round,pad=0,rounding_size=3',
                                    facecolor=GOLD, edgecolor='none', alpha=a_c, zorder=46))
        txt(fr, x0 + 40, y0 + 88 + dy, 'Printemps 1900', 'display', 76, INK, a_c, z=46)
        a_f = ramp(f, 30, 42)
        txt(fr, x0 + 40, y0 + 144 + dy, "Pêcheurs d'éponges de Symi", 'sansm', 38, INK, a_c * a_f, z=46)
    return fr


# ============================================================================= 2. PHASES (plan 3.4)
PH_N = 175
PH_GO, PH_ARR = 90, 140           # images (0-based) : départ de la manivelle (« Opposées »), arrivée à la pleine lune
PH_T0, PH_T1 = 0.972, 1.009
PH_BOX = (1096, 96, 1824, 716)


def phases_crank(f):
    return PH_T0 + (PH_T1 - PH_T0) * smooth((f - PH_GO) / float(PH_ARR - PH_GO))


@lru_cache(maxsize=None)
def machine():
    import engine
    return engine.get_machine(False)


@lru_cache(maxsize=None)
def elongation(t):
    """élongation Lune − Soleil moyen montrée par la boule des phases (degrés, 0 = nouvelle lune), engine.py"""
    return float(np.degrees(machine().sun_moon_node(float(t))['q'])) % 360.0


def phase_ball(fr, cx, cy, r, Dd, alpha, z=30):
    """boule mi-noire mi-blanche vue de face, comme sur la machine : noire à 0°, blanche à 180°"""
    dark, light = '#1F1A15', '#F5F2EA'
    ax = fr.ax
    ax.add_patch(Circle((cx, cy), r, facecolor=dark, edgecolor='none', alpha=alpha, zorder=z))
    c = math.cos(math.radians(Dd))
    if Dd % 360 <= 180:          # croissante : partie claire à droite
        ax.add_patch(Wedge((cx, cy), r, -90, 90, facecolor=light, edgecolor='none', alpha=alpha, zorder=z + 0.1))
        ax.add_patch(Ellipse((cx, cy), 2 * r * abs(c), 2 * r, facecolor=dark if c > 0 else light, edgecolor='none',
                             alpha=alpha, zorder=z + 0.2))
    else:
        ax.add_patch(Wedge((cx, cy), r, 90, 270, facecolor=light, edgecolor='none', alpha=alpha, zorder=z + 0.1))
        ax.add_patch(Ellipse((cx, cy), 2 * r * abs(c), 2 * r, facecolor=dark if c > 0 else light, edgecolor='none',
                             alpha=alpha, zorder=z + 0.2))
    fr.glow(cx - r * 0.35, cy - r * 0.4, r * 0.7, '#FFFFFF', alpha=0.18 * alpha, z=z + 0.3)
    ax.add_patch(Circle((cx, cy), r, facecolor='none', edgecolor=BRONZE, lw=3, alpha=alpha, zorder=z + 0.4))


def phases_frame(f):
    fr = Frame(transparent=True)
    ax = fr.ax
    A = life(f, PH_N, 12, 10)
    x0, y0, x1, y1 = PH_BOX
    dy = (1 - ramp(f, 0, 12)) * 16
    y0d, y1d = y0 + dy, y1 + dy
    card(fr, x0, y0d, x1, y1d, A)
    clip = clip_box(fr, x0, y0d, x1, y1d)
    t = phases_crank(f)
    Dd = elongation(round(t, 6))
    heading(fr, x0 + 30, y0d + 50, 'Vue du dessus', A)
    txt(fr, x1 - 30, y0d + 50, 'pas à l\'échelle', 'sansi', 24, MUTED, A, ha='right')
    ex, ey = x0 + 322, y0d + 272
    R = 140
    # Soleil (au loin, à gauche) et sa lumière
    fr.glow(x0 - 20, ey, 240, SUN, alpha=0.55 * A, z=2, clip=clip)
    sun = Circle((x0 - 40, ey), 112, facecolor=SUN, edgecolor=GOLD, lw=3, alpha=A, zorder=3)
    ax.add_patch(sun)
    sun.set_clip_path(clip)
    txt(fr, x0 + 34, ey + 150, 'Soleil', 'sansm', 30, BRONZE, A, z=10)
    for dy_ in (-80, 80):
        arrow(fr, x0 + 104, ey + dy_, x0 + 170, ey + dy_, GOLD, lw=3, alpha=0.75 * A, head=14, z=4)
    # orbite de la Lune
    th = np.linspace(0, 2 * np.pi, 240)
    ax.plot(ex + R * np.cos(th), ey + R * np.sin(th), color=INK, lw=1.8, alpha=0.35 * A, ls=(0, (5, 6)), zorder=5)
    # trace de la Lune depuis la nouvelle lune
    Dd0 = elongation(PH_T0)
    if Dd > Dd0 + 0.5 and Dd < 200:
        dd = np.radians(np.linspace(Dd0, Dd, 80))
        ax.plot(ex - R * np.cos(dd), ey + R * np.sin(dd), color='#8E96A8', lw=6, alpha=0.55 * A, zorder=6,
                solid_capstyle='round')
    # « aiguilles » : direction du Soleil (or) et de la Lune (argent), vues de la Terre
    Lh = R + 30
    ax.plot([ex, ex - Lh], [ey, ey], color=GOLD, lw=8, alpha=A, zorder=8, solid_capstyle='round')
    rad = math.radians(Dd)
    mx, my = ex - R * math.cos(rad), ey + R * math.sin(rad)
    ax.plot([ex, ex - Lh * math.cos(rad)], [ey, ey + Lh * math.sin(rad)], color='#7E8698', lw=4, alpha=A,
            zorder=9, solid_capstyle='round')
    # Terre (jour à gauche)
    ax.add_patch(Circle((ex, ey), 26, facecolor=EARTH_NIGHT, edgecolor='none', alpha=A, zorder=12))
    ax.add_patch(Wedge((ex, ey), 26, 90, 270, facecolor=EARTH, edgecolor='none', alpha=A, zorder=12.5))
    ax.add_patch(Circle((ex, ey), 26, facecolor='none', edgecolor=INK, lw=2.2, alpha=A, zorder=13))
    # au-dessus de la Terre : la Lune ne passe que dans la moitié basse entre la nouvelle et la pleine lune
    txt(fr, ex, ey - 42, 'Terre', 'sansb', 30, EARTH, A, ha='center', z=14, halo=PAPER, halo_w=6)
    # Lune (moitié éclairée vers le Soleil)
    ax.add_patch(Circle((mx, my), 18, facecolor='#6F7380', edgecolor='none', alpha=A, zorder=15))
    ax.add_patch(Wedge((mx, my), 18, 90, 270, facecolor=MOON, edgecolor='none', alpha=A, zorder=15.5))
    ax.add_patch(Circle((mx, my), 18, facecolor='none', edgecolor=INK, lw=2, alpha=A, zorder=16))
    txt(fr, mx, my + 60, 'Lune', 'sansb', 28, INK, A, ha='center', z=17, halo=PAPER, halo_w=6)
    # boule des phases (ce que montre la machine)
    bx_, by_ = x1 - 98, y0d + 196
    phase_ball(fr, bx_, by_, 38, Dd, A, z=20)
    txt(fr, bx_, by_ + 74, 'boule des phases', 'sans', 22, MUTED, A, ha='center', z=21)
    a_n = 1 - ramp(Dd, 25, 45)
    a_b = ramp(Dd, 150, 172)
    txt(fr, bx_, by_ + 104, 'noire', 'sansb', 26, INK, A * a_n, ha='center', z=21)
    txt(fr, bx_, by_ + 104, 'blanche', 'sansb', 26, INK, A * a_b, ha='center', z=21)
    # légende des aiguilles
    ly = y0d + 520
    lx = x0 + 60
    ax.plot([lx, lx + 36], [ly - 8, ly - 8], color=GOLD, lw=8, alpha=A, zorder=20, solid_capstyle='round')
    w_ = txt(fr, lx + 50, ly, 'aiguille du Soleil', 'sans', 24, MUTED, A, z=20)
    lx2 = lx + 50 + w_ + 40
    ax.plot([lx2, lx2 + 36], [ly - 8, ly - 8], color='#7E8698', lw=5, alpha=A, zorder=20, solid_capstyle='round')
    txt(fr, lx2 + 50, ly, 'aiguille de la Lune', 'sans', 24, MUTED, A, z=20)
    # légende dynamique (textes du plan 3.4)
    ax.plot([x0 + 30, x1 - 30], [y0d + 548, y0d + 548], color=RULE, lw=1.5, alpha=A, zorder=20)
    cx = (x0 + x1) / 2
    txt(fr, cx, y0d + 598, 'Superposées : nouvelle lune', 'display', 42, INK, A * a_n, ha='center', z=21)
    txt(fr, cx, y0d + 598, 'Opposées : pleine lune', 'display', 42, INK, A * a_b, ha='center', z=21)
    return fr


# ============================================================================= 3. CASE DE MÉTON (plan 5.2)
MC_N = 100
MC_BOX = (1096, 150, 1824, 700)


def metonic_frame(f):
    fr = Frame(transparent=True)
    ax = fr.ax
    A = life(f, MC_N, 10, 8)
    x0, y0, x1, y1 = MC_BOX
    dy = (1 - ramp(f, 0, 10)) * 16
    y0 += dy; y1 += dy
    card(fr, x0, y0, x1, y1, A)
    clip = clip_box(fr, x0, y0, x1, y1)
    heading(fr, x0 + 30, y0 + 50, 'Une case agrandie', A)
    txt(fr, x1 - 30, y0 + 50, 'spirale de Méton', 'sans', 24, MUTED, A, ha='right')
    # case en arc (le centre de la spirale est sous la case)
    cx, cy = (x0 + x1) / 2, y0 + 88 + 610
    Rout, Rin = 610, 430
    half = 17.0
    FADE = 16.0                   # les cases voisines et le sillon s'estompent sur 16° de part et d'autre
    a_cell = A * ramp(f, 3, 14)
    nsl = 24
    for sgn in (-1, 1):           # cases voisines : bande de laiton qui s'efface en s'éloignant (fondu angulaire)
        for j in range(nsl):
            al = (1 - (j + 0.5) / nsl) ** 1.3
            a0 = half + FADE * j / nsl
            a1 = half + FADE * (j + 1) / nsl + 0.05
            lo, hi = (270 + a0, 270 + a1) if sgn > 0 else (270 - a1, 270 - a0)
            wdg = Wedge((cx, cy), Rout, lo, hi, width=Rout - Rin, facecolor=to_rgba(BRASS, 0.75 * al * a_cell),
                        edgecolor='none', zorder=5)
            ax.add_patch(wdg)
        # début du trait qui sépare la case voisine suivante, lui aussi estompé
        th = math.radians(270 + sgn * (half + 0.55 * FADE))
        ax.plot([cx + Rin * math.cos(th), cx + Rout * math.cos(th)], [cy + Rin * math.sin(th), cy + Rout * math.sin(th)],
                color=BRASS_EDGE, lw=2, alpha=0.3 * a_cell, zorder=5.2)
    cell = Wedge((cx, cy), Rout, 270 - half, 270 + half, width=Rout - Rin, facecolor='none', edgecolor='none',
                 transform=ax.transData)
    ax.add_patch(cell)
    fr.img(vgradient([(0, BRASS_HI), (0.55, '#E9CF94'), (1, BRASS_LO)]), cx - 200, cy - Rout, cx + 200, cy - Rin * 0.94,
           z=6, alpha=a_cell, clip=cell)
    ax.add_patch(Wedge((cx, cy), Rout, 270 - half, 270 + half, width=Rout - Rin, facecolor='none',
                       edgecolor=to_rgba(BRASS_EDGE, a_cell), lw=3, zorder=7))
    # sillons de la spirale au-dessus et au-dessous
    for rr in (Rout + 14, Rin - 14):      # anneaux fins (secteurs), en tranches pour le fondu : pas de coutures
        ax.add_patch(Wedge((cx, cy), rr + 4.5, 270 - half, 270 + half, width=9,
                           facecolor=to_rgba(GROOVE, 0.85 * a_cell), edgecolor='none', zorder=7))
        for sgn in (-1, 1):
            for j in range(nsl):
                al = (1 - (j + 0.5) / nsl) ** 1.3
                a0 = half + FADE * j / nsl - 0.02
                a1 = half + FADE * (j + 1) / nsl
                lo, hi = (270 + a0, 270 + a1) if sgn > 0 else (270 - a1, 270 - a0)
                ax.add_patch(Wedge((cx, cy), rr + 4.5, lo, hi, width=9,
                                   facecolor=to_rgba(GROOVE, 0.85 * al * a_cell), edgecolor='none', zorder=7))
    # reflet qui balaie la case
    u = ramp(f, 14, 42)
    if 0 < u < 1:
        band = np.zeros((1, 64, 4))
        band[..., :3] = 1.0
        band[0, :, 3] = np.exp(-((np.linspace(-1, 1, 64)) ** 2) / 0.08) * 0.55
        bx = cx - 260 + 520 * u
        fr.img(band, bx - 60, cy - Rout, bx + 60, cy - Rin * 0.94, z=8, alpha=a_cell, clip=cell)

    # inscriptions gravées le long de l'arc
    def arc_text(s, r, px, a):
        ws = [mw(c, 'greek', px) for c in s]
        track = 0.04 * px
        total = sum(ws) + track * (len(s) - 1)
        pos = -total / 2
        for c, w_ in zip(s, ws):
            phi = (pos + w_ / 2) / r
            x_ = cx + r * math.sin(phi)
            y_ = cy - r * math.cos(phi)
            engraved(fr, x_, y_, c, 'greek', px, a, z=9, rotation=-math.degrees(phi))
            pos += w_ + track
    arc_text('ΦΟΙΝΙΚΑΙΟΣ', Rout - 70, 50, a_cell)
    arc_text('L Α', Rout - 140, 50, a_cell)
    # légendes
    a1, d1 = enter(f, 24, 36, 10)
    a2, d2 = enter(f, 36, 48, 10)
    ya = y0 + 392
    xl, xr = x0 + 70, x0 + 470
    if a1 > 0:
        ax.plot([cx - 150, cx - 150, xl + 80], [y0 + 190, ya - 70, ya - 48], color=INK, lw=1.6, alpha=0.6 * A * a1,
                zorder=10)
        ax.add_patch(Circle((cx - 150, y0 + 190), 4.5, facecolor=INK, alpha=0.7 * A * a1, zorder=10))
        txt(fr, xl, ya + d1, 'Phoinikaios', 'sansb', 38, INK, A * a1, z=11)
        txt(fr, xl, ya + 36 + d1, 'nom du mois (corinthien)', 'sans', 24, MUTED, A * a1, z=11)
    if a2 > 0:
        ax.plot([cx + 22, cx + 22, xr + 30], [y0 + 244, ya - 70, ya - 48], color=INK, lw=1.6, alpha=0.6 * A * a2,
                zorder=10)
        ax.add_patch(Circle((cx + 22, y0 + 244), 4.5, facecolor=INK, alpha=0.7 * A * a2, zorder=10))
        txt(fr, xr, ya + d2, '… an 1', 'sansb', 38, INK, A * a2, z=11)
        txt(fr, xr, ya + 36 + d2, 'L = année, Α = 1', 'sans', 24, MUTED, A * a2, z=11, greek_color=BRONZE)
    a3 = ramp(f, 46, 58)
    chip(fr, (x0 + x1) / 2, y1 - 34, "illustration d'après Freeth et al. 2008", BRONZE_FORT, A * a3, ha='center',
         key='sansi', px=24)
    return fr


# ============================================================================= 4. BANDEAU DES JEUX (plan 5.3)
GB_N = 150
GB_F0, GB_F1 = 12, 112            # la manivelle va de 3,0 à 5,95 entre ces images (rapide puis ralenti)
GB_T0, GB_T1 = 3.0, 5.95
GB_BOX = (150, 648, 1770, 884)
GAMES = [('An 1', 'Isthmia, Olympia', 'ΙΣΘΜΙΑ · ΟΛΥΜΠΙΑ'), ('An 2', 'Nemea, Naa', 'ΝΕΜΕΑ · ΝΑΑ'),
         ('An 3', 'Isthmia, Pythia', 'ΙΣΘΜΙΑ · ΠΥΘΙΑ'), ('An 4', 'Nemea, Halieia', 'ΝΕΜΕΑ · ΑΛΙΕΙΑ')]


def games_crank(f):
    u = clamp01((f - GB_F0) / float(GB_F1 - GB_F0))
    return GB_T0 + (GB_T1 - GB_T0) * (1 - (1 - u) ** 2.6)


@lru_cache(maxsize=None)
def games_year_start():
    """instant (manivelle) où l'aiguille des Jeux entre dans l'an 1 (ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ) entre 5,8 et 5,95 (engine.py)"""
    m = machine()
    lo, hi = 5.80, 5.95
    assert m.read_back(lo)['jeux']['annee_de_l_olympiade'] == 4 and m.read_back(hi)['jeux']['annee_de_l_olympiade'] == 1
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if m.read_back(mid)['jeux']['annee_de_l_olympiade'] == 1:
            hi = mid
        else:
            lo = mid
    return hi


def games_year_pos(t):
    """position continue de l'aiguille dans le bandeau : 0 = début de l'an 1, 4 = fin de l'an 4"""
    return (t - games_year_start()) % 4.0


def games_arrival_frame():
    ts = games_year_start()
    for f in range(GB_N):
        if games_crank(f) >= ts:
            return f
    return None


def games_frame(f):
    fr = Frame(transparent=True)
    ax = fr.ax
    A = life(f, GB_N, 12, 10)
    x0, y0, x1, y1 = GB_BOX
    dy = (1 - ramp(f, 0, 12)) * 18
    y0 += dy; y1 += dy
    card(fr, x0, y0, x1, y1, A)
    heading(fr, x0 + 28, y0 + 42, 'Cadran des Jeux : les 4 années de l\'original', A, px=24)
    txt(fr, x1 - 28, y0 + 42, 'Freeth et al. 2008 ; Iversen 2017', 'sansi', 24, MUTED, A, ha='right')
    t = games_crank(f)
    pos = games_year_pos(t)
    cur = int(pos) % 4
    fa = games_arrival_frame()
    hl = ramp(f, fa, fa + 8) if fa is not None else 0.0
    gap = 16
    cw = (x1 - x0 - 48 - 3 * gap) / 4.0
    cy0, cy1 = y0 + 62, y1 - 34
    for i, (yr, fr_names, gr) in enumerate(GAMES):
        cx0 = x0 + 24 + i * (cw + gap)
        a_i = A * ramp(f, 4 + 3 * i, 14 + 3 * i)
        is1 = i == 0
        fill = mix('#F6ECD9', BRASS, hl) if is1 else '#F6ECD9'
        edge = mix(RULE_STRONG, GOLD, hl) if is1 else (BRONZE if (i == cur and f >= GB_F0) else RULE_STRONG)
        lw = 2 + 3 * hl if is1 else (2.5 if (i == cur and f >= GB_F0) else 1.6)
        if is1 and hl > 0:
            pulse = 0.5 + 0.5 * math.cos(2 * math.pi * (f - fa) / 25.0)
            fr.glow(cx0 + cw / 2, (cy0 + cy1) / 2, cw * 0.62, GOLD, alpha=0.35 * hl * (0.6 + 0.4 * pulse) * A, z=2,
                    power=1.6)
        ax.add_patch(FancyBboxPatch((cx0, cy0), cw, cy1 - cy0, boxstyle='round,pad=0,rounding_size=12',
                                    facecolor=to_rgba(fill, a_i), edgecolor=to_rgba(edge, a_i), lw=lw, zorder=3))
        mid = cx0 + cw / 2
        spaced(fr, mid, cy0 + 36, yr.upper(), 'sansb', 24, BRONZE, a_i, track=0.12, z=5)
        txt(fr, mid, cy0 + 88, fr_names, 'display', 42, INK, a_i, ha='center', z=5)
        txt(fr, mid, cy0 + 124, gr, 'greek', 26, BRONZE, 0.9 * a_i, ha='center', z=5)
    # rail et curseur de l'aiguille (position continue sur les 4 ans)
    ry = y1 - 17
    ax.plot([x0 + 24, x1 - 24], [ry, ry], color=RULE_STRONG, lw=3, alpha=A, zorder=4, solid_capstyle='round')
    if f >= GB_F0 - 6:
        a_c = A * ramp(f, GB_F0 - 6, GB_F0)
        p = pos
        k_ = int(p)
        xc = x0 + 24 + k_ * (cw + gap) + (p - k_) * cw
        col = mix(BRONZE, GOLD, hl)
        ax.add_patch(FancyBboxPatch((xc - 22, ry - 5), 44, 10, boxstyle='round,pad=0,rounding_size=5',
                                    facecolor=to_rgba(col, a_c), edgecolor='none', zorder=6))
    return fr


# ============================================================================= 5. ANATOMIE D'UN SIGNE (plan 6.3)
GA_N = 113
GA_BOX = (1064, 100, 1824, 716)


def glyph_frame(f):
    fr = Frame(transparent=True)
    ax = fr.ax
    A = life(f, GA_N, 10, 9)
    x0, y0, x1, y1 = GA_BOX
    dy = (1 - ramp(f, 0, 10)) * 16
    y0 += dy; y1 += dy
    card(fr, x0, y0, x1, y1, A)
    heading(fr, x0 + 30, y0 + 50, 'Anatomie d\'un signe', A)
    chip(fr, x1 - 30, y0 + 50, 'exemple', BRONZE_FORT, A, ha='right', key='sansm', px=24)
    # case gravée (agrandie)
    c0, c1 = x0 + 44, x0 + 264
    t0, t1 = y0 + 84, y0 + 514
    a_c = A * ramp(f, 3, 14)
    cellp = FancyBboxPatch((c0, t0), c1 - c0, t1 - t0, boxstyle='round,pad=0,rounding_size=10', facecolor='none',
                           edgecolor='none', transform=ax.transData)
    ax.add_patch(cellp)
    fr.img(vgradient([(0, BRASS_HI), (0.5, '#E9CF94'), (1, BRASS_LO)]), c0, t0, c1, t1, z=4, alpha=a_c, clip=cellp)
    ax.add_patch(FancyBboxPatch((c0, t0), c1 - c0, t1 - t0, boxstyle='round,pad=0,rounding_size=10', facecolor='none',
                                edgecolor=to_rgba(BRASS_EDGE, a_c), lw=3, zorder=5))
    for yy in (t0 - 9, t1 + 9):
        ax.plot([c0 - 16, c1 + 16], [yy, yy], color=GROOVE, lw=8, alpha=0.85 * a_c, zorder=5, solid_capstyle='round')
    mid = (c0 + c1) / 2
    items = [  # (texte gravé, px, ligne de base, y du repère, image d'apparition, titre, sous-titre)
        ('Σ', 118, t0 + 142, t0 + 100, 12, 'Σ = éclipse de Lune', '(Η = éclipse de Soleil)'),
        ('ΩΡ Δ', 62, t0 + 262, t0 + 240, 34, 'ΩΡ + chiffre = heure', 'ici Δ = 4'),
        ('Κ', 66, t0 + 386, t0 + 364, 56, 'Lettre d\'index → détails', 'direction, grandeur, couleur'),
    ]
    for s, px, base, ym, fa_, title, sub in items:
        a_i, d_i = enter(f, fa_, fa_ + 12, 10)
        glow = a_i * (1 - ramp(f, fa_ + 14, fa_ + 34))
        if glow > 0:
            fr.glow(mid, ym, 90, GOLD, alpha=0.55 * glow * A, z=5.5)
        engraved(fr, mid, base, s, 'greek', px, a_c, z=7)
        if a_i > 0:
            xa = x0 + 312
            half_w = mw(s, 'greek', px) / 2
            ax.plot([mid + half_w + 14, xa - 16], [ym, ym], color=INK, lw=1.6, alpha=0.65 * A * a_i, zorder=8)
            ax.add_patch(Circle((mid + half_w + 14, ym), 4.5, facecolor=INK, alpha=0.75 * A * a_i, zorder=8))
            txt(fr, xa, ym + 10 + d_i, title, 'sansb', 34, INK, A * a_i, z=9, greek_color=BRONZE)
            txt(fr, xa, ym + 48 + d_i, sub, 'sans', 24, MUTED, A * a_i, z=9, greek_color=BRONZE)
    a_n = ramp(f, 66, 78)
    txt(fr, x0 + 30, y1 - 52, 'Dans notre modèle, la case 112 ne porte ni heure ni lettre.', 'sansi', 25, MUTED,
        A * a_n, z=9)
    txt(fr, x0 + 30, y1 - 20, 'Forme des signes : Freeth et al. 2008 ; Freeth 2014', 'sans', 24, MUTED, A * a_n, z=9)
    return fr


# ============================================================================= 6. PARAPEGME (plan 7.2)
PP_N = 125
PP_LINE_Y = 214                   # ligne de base de la ligne du parapegme
PP_XI = (960, 700)                # ancre par défaut du repère Ξ dans parapegma_line
PP_W0, PP_W1 = 22, 72             # la ligne s'écrit entre ces images
PP_LINE = [('Ξ', 'greek', 82), ('  La Pléiade se lève le matin', 'display', 74)]


def xi_mark(fr, cx, cy, f, A):
    ax = fr.ax
    u = ramp(f, 0, 12)
    a = A * u
    if a <= 0.003:
        return
    # impulsions
    for off in (0.0, 0.5):
        ph = ((f - 10) / 28.0 + off) % 1.0 if f >= 10 else None
        if ph is not None and f < 70:
            ax.add_patch(Circle((cx, cy), 52 + 50 * ph, facecolor='none', edgecolor=GOLD, lw=3 * (1 - ph) + 0.5,
                                alpha=0.8 * A * (1 - ph) ** 1.4 * (1 - ramp(f, 55, 70)), zorder=20))
    fr.glow(cx, cy, 110, GOLD, alpha=0.45 * a, z=19, power=1.8)
    th = np.linspace(math.pi / 2, math.pi / 2 - 2 * math.pi * smooth(u), 100)
    ax.plot(cx + 50 * np.cos(th), cy - 50 * np.sin(th), color=ENGRAVE, lw=10, alpha=0.9 * A, zorder=21,
            solid_capstyle='round')
    ax.plot(cx + 50 * np.cos(th), cy - 50 * np.sin(th), color=GOLD, lw=5, alpha=A, zorder=22, solid_capstyle='round')
    ax.add_patch(Circle((cx, cy), 46, facecolor=to_rgba(PAPER, 0.25 * a), edgecolor='none', zorder=20.5))
    gold_text(fr, cx - mw('Ξ', 'greek', 64) / 2, cy + 22, [('Ξ', 'greek', 64)], a, None, z=23)


def gold_text(fr, x, y, runs, alpha, wipe_x=None, z=30):
    """or gravé : remplissage or, contour sombre, reflet clair sur le haut des lettres ; wipe_x = bord de l'écriture"""
    ax = fr.ax
    import matplotlib.patheffects as pe
    xx = x
    top = y - max(px for _, _, px in runs) * 0.8
    for s, key, px in runs:
        for pass_ in (0, 1):
            t = ax.text(xx, y, s, fontproperties=fp(key, px), color=GOLD if pass_ == 0 else BRASS_HI, alpha=alpha,
                        ha='left', va='baseline', zorder=z + pass_)
            if pass_ == 0:
                t.set_path_effects([pe.withStroke(linewidth=5, foreground=ENGRAVE, alpha=alpha)])
                cx1 = wipe_x if wipe_x is not None else W
                t.set_clip_path(Rectangle((0, 0), cx1, H, transform=ax.transData))
            else:
                cx1 = wipe_x if wipe_x is not None else W
                t.set_clip_path(Rectangle((0, top - 20), cx1, (y - top) * 0.5 + 20, transform=ax.transData))
        xx += mw(s, key, px)
    return xx - x


def parapegma_frame(f, part='both'):
    fr = Frame(transparent=True)
    ax = fr.ax
    A = 1 - ramp(f, PP_N - 10, PP_N - 1)
    if part in ('both', 'xi'):
        cx, cy = PP_XI if part == 'both' else (W / 2, H / 2)
        xi_mark(fr, cx, cy, f, A)
    if part in ('both', 'line'):
        total = sum(mw(s, k, px) for s, k, px in PP_LINE)
        x0 = W / 2 - total / 2
        u = ramp(f, PP_W0, PP_W1)
        a_bk = A * ramp(f, PP_W0 - 8, PP_W0 + 6)
        if a_bk > 0:      # fond sombre très doux derrière la ligne, pour la lire sur le bronze
            fr.img(D.radial(INK, 1.4), x0 - 140, PP_LINE_Y - 120, x0 + total + 140, PP_LINE_Y + 60, z=25,
                   alpha=0.30 * a_bk)
        if u > 0:
            wipe = x0 - 10 + (total + 30) * (0.08 * u + 0.92 * ease(u))
            gold_text(fr, x0, PP_LINE_Y, PP_LINE, A, wipe_x=wipe)
            if u < 1:
                fr.glow(wipe, PP_LINE_Y - 26, 60, '#FFE7B0', alpha=0.85 * A * math.sin(math.pi * u) ** 0.5, z=35,
                        power=1.6)
                fr.glow(wipe, PP_LINE_Y - 26, 16, '#FFFFFF', alpha=0.9 * A * math.sin(math.pi * u) ** 0.5, z=36)
        a_t, dy = enter(f, PP_W1 + 2, PP_W1 + 14, 8)
        if a_t > 0:
            s1 = 'illustration'
            s2 = "ligne du parapegme d'après Bitsakis & Jones 2016"
            w1 = txt_w(s1, 'sansm', 24) + 24
            w2 = txt_w(s2, 'sans', 24)
            wt = w1 + 14 + w2
            xl = W / 2 - wt / 2 - 16
            card(fr, xl, PP_LINE_Y + 36 + dy, xl + wt + 32, PP_LINE_Y + 88 + dy, A * a_t, fill_a=0.92, r=12, z=40)
            chip(fr, xl + 16, PP_LINE_Y + 71 + dy, s1, BRONZE_FORT, A * a_t, px=24, z=42)
            txt(fr, xl + 16 + w1 + 14, PP_LINE_Y + 71 + dy, s2, 'sans', 24, MUTED, A * a_t, z=42)
    return fr


# ============================================================================= 7. CARTON FINAL (plan 7.6)
EC_N = 125
EC_Q0 = 44                        # la question apparaît (image, 0-based)
STEPS = [('1', 'Tournez la manivelle', None), ('2', 'Soleil : date, saison', None), ('3', 'Lune : place, phase', None),
         ('4', 'Planètes : place', ' (hypothèse)'), ('5', 'Dos : mois, Jeux', None), ('6', 'Signe : éclipse, heure', None)]
CREDITS = 'taciclei · github.com/taciclei/antikythera-mechanism · rapports prouvés en Lean 4'
QUESTION = 'Et vous, quelle date ?'


def vignette_img():
    yy, xx = np.mgrid[-1:1:270j, -1:1:480j]
    v = np.zeros((270, 480, 4))
    v[..., :3] = np.array(to_rgba('#7A5A36')[:3])
    v[..., 3] = 0.30 * np.clip(np.hypot(xx * 0.92, yy * 1.05) - 0.45, 0, 1) ** 1.6
    return v


def end_frame(f, opaque=True):
    fr = Frame(bg=BG) if opaque else Frame(transparent=True)
    ax = fr.ax
    if opaque:
        fr.img(vignette_img(), 0, 0, W, H, z=0)
    a_s, dy = enter(f, 0, 14, 14)
    # titre
    hw = heading(fr, W / 2, 196 + dy, 'Comment lire la machine', a_s, px=30, ha='center')
    for sgn in (-1, 1):
        xa = W / 2 + sgn * (hw / 2 + 28)
        ax.plot([xa, xa + sgn * 120], [186 + dy, 186 + dy], color=GOLD, lw=2, alpha=a_s, zorder=5)
    # les six étapes, ensemble, en deux colonnes
    px = 50
    colw = []
    for c in (STEPS[:3], STEPS[3:]):
        colw.append(max(txt_w(t, 'display', px) + (txt_w(h_, 'display', px) if h_ else 0) for _, t, h_ in c))
    med = 84
    gapc = 130
    total = med + colw[0] + gapc + med + colw[1]
    xs = [W / 2 - total / 2, W / 2 - total / 2 + med + colw[0] + gapc]
    for i, (n, t, h_) in enumerate(STEPS):
        col, row = divmod(i, 3)
        x = xs[col]
        y = 330 + row * 104 + dy
        ax.add_patch(Circle((x + 30, y - 17), 30, facecolor=to_rgba(BRASS, a_s), edgecolor=to_rgba(BRONZE, a_s),
                            lw=2.5, zorder=6))
        txt(fr, x + 30, y - 4, n, 'display', 36, INK, a_s, ha='center', z=7)
        w_ = txt(fr, x + med, y, t, 'display', px, INK, a_s, z=7)
        if h_:
            txt(fr, x + med + w_, y, h_, 'display', px, HYP, a_s, z=7)
    # la question
    a_q, dq = enter(f, EC_Q0, EC_Q0 + 14, 16)
    txt(fr, W / 2, 742 + dq, QUESTION, 'display', 104, INK, a_q, ha='center', z=8)
    ax.add_patch(Polygon(star4(W / 2, 800 + dq, 13), closed=True, facecolor=to_rgba(GOLD, a_q),
                         edgecolor=to_rgba(BRONZE, a_q), lw=1.5, zorder=8))
    for sgn in (-1, 1):
        ax.plot([W / 2 + sgn * 26, W / 2 + sgn * 150], [800 + dq, 800 + dq], color=GOLD, lw=2, alpha=a_q, zorder=8)
    # crédits
    a_c = ramp(f, EC_Q0 + 16, EC_Q0 + 30)
    txt(fr, W / 2, 986, CREDITS, 'sans', 30, MUTED, a_c, ha='center', z=8)
    return fr


# ============================================================================= 8. TITRES DE CHAPITRE
CT_N = 63
CT_X0, CT_YB = 96, 876            # coin bas gauche de la carte


@lru_cache(maxsize=None)
def chapter_titles():
    """titres lus dans script.md : « ## 1. Le ciel dans une boîte (environ 24 s) »"""
    out = {}
    for line in SCRIPT_MD.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^## (\d)\. (.+?) \(environ', line)
        if m:
            out[int(m.group(1))] = m.group(2).strip()
    assert sorted(out) == list(range(1, 8)), out
    return out


def chapter_frame(f, n):
    fr = Frame(transparent=True)
    ax = fr.ax
    title = chapter_titles()[n]
    px = 56
    num = str(n)
    sep = '  ·  '
    wn, ws, wt = txt_w(num, 'display', px), txt_w(sep, 'display', px), txt_w(title, 'display', px)
    w_ = 34 + wn + ws + wt + 40
    h_ = 104
    x0, y1 = CT_X0, CT_YB
    y0 = y1 - h_
    a_out = 1 - ramp(f, CT_N - 11, CT_N - 1)
    dy = 8 * ramp(f, CT_N - 11, CT_N - 1)
    u = ease(clamp01((f - 3) / 13.0))
    if u <= 0:
        return fr
    A = a_out
    clip = Rectangle((x0 - 4, y0 - 20 + dy), (w_ + 8) * u + 1, h_ + 40, transform=ax.transData)
    p = card(fr, x0, y0 + dy, x0 + w_, y1 + dy, A, fill_a=0.95, r=14)
    if p is None:
        return fr
    p.set_clip_path(clip)
    bar = ramp(f, 0, 9)
    ax.add_patch(FancyBboxPatch((x0 + 10, y0 + dy + h_ / 2 * (1 - bar) + 14 * bar), 7, max(1, (h_ - 28) * bar),
                                boxstyle='round,pad=0,rounding_size=3', facecolor=GOLD, edgecolor='none', alpha=A,
                                zorder=3))
    a_t = ramp(f, 8, 20) * A
    dx = (1 - ramp(f, 8, 20)) * -14
    base = y0 + dy + 71
    x = x0 + 34 + dx
    txt(fr, x, base, num, 'display', px, BRONZE, a_t, z=5)
    txt(fr, x + wn, base, sep, 'display', px, MUTED, a_t, z=5)
    if n == 4 and title.endswith('hypothèse'):
        head = title[:-len('hypothèse')]
        w0 = txt(fr, x + wn + ws, base, head, 'display', px, INK, a_t, z=5)
        txt(fr, x + wn + ws + w0, base, 'hypothèse', 'display', px, HYP, a_t, z=5)
    else:
        txt(fr, x + wn + ws, base, title, 'display', px, INK, a_t, z=5)
    return fr


# ============================================================================= orchestration
INSERTS = {   # nom -> (images, fonction, RGBA, ombre, fond de l'aperçu)
    'map': (MAP_N, map_frame, False, False, None),
    'phases': (PH_N, phases_frame, True, True, 'CAM_front_close'),
    'metonic_cell': (MC_N, metonic_frame, True, True, 'CAM_back_close'),
    'games_banner': (GB_N, games_frame, True, True, 'CAM_games_close'),
    'glyph_anatomy': (GA_N, glyph_frame, True, True, 'CAM_saros_close'),
    'parapegma_line': (PP_N, lambda f: parapegma_frame(f, 'both'), True, True, 'CAM_front_close'),
    'parapegma_xi': (PP_N, lambda f: parapegma_frame(f, 'xi'), True, True, 'CAM_front_close'),
    'parapegma_ligne': (PP_N, lambda f: parapegma_frame(f, 'line'), True, True, 'CAM_front_close'),
    'end_card': (EC_N, lambda f: end_frame(f, True), False, False, None),
    'end_card_texte': (EC_N, lambda f: end_frame(f, False), True, False, 'parchemin'),
}
for _n in range(1, 8):
    INSERTS[f'chapter_title_{_n}'] = (CT_N, (lambda n: (lambda f: chapter_frame(f, n)))(_n), True, True, 'CAM_front34')


def _render(job):
    name, f, outdir = job
    n, fn, rgba, shadow, _ = INSERTS[name]
    save_frame(fn(f), Path(outdir) / f'{f + 1:04d}.png', rgba, shadow)
    return f


def preview(name, outdir):
    exe = D.ffmpeg_exe()
    if not exe:
        return None
    mp4 = OUT / f'{name}_apercu.mp4'
    _, _, rgba, _, bg = INSERTS[name]
    cmd = [exe, '-y', '-loglevel', 'error']
    if rgba:
        if bg == 'parchemin' or not (LOOK2 / f'{bg}_eevee.png').exists():
            cmd += ['-f', 'lavfi', '-i', f'color=c=0x{BG[1:]}:s={W}x{H}:r={FPS}']
        else:
            cmd += ['-loop', '1', '-framerate', str(FPS), '-i', str(LOOK2 / f'{bg}_eevee.png')]
        cmd += ['-framerate', str(FPS), '-start_number', '1', '-i', str(outdir / '%04d.png'),
                '-filter_complex', '[0:v]format=rgb24[bg];[bg][1:v]overlay=shortest=1:format=auto,format=yuv420p']
    else:
        cmd += ['-framerate', str(FPS), '-start_number', '1', '-i', str(outdir / '%04d.png'), '-pix_fmt', 'yuv420p']
    cmd += ['-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-movflags', '+faststart', str(mp4)]
    subprocess.run(cmd, check=True)
    return mp4


def chapter_preview():
    """un seul aperçu pour les 7 titres de chapitre, à la suite"""
    exe = D.ffmpeg_exe()
    parts = [OUT / f'chapter_title_{n}_apercu.mp4' for n in range(1, 8)]
    if not exe or not all(p.exists() for p in parts):
        return None
    lst = OUT / '_chapitres.txt'
    lst.write_text(''.join(f"file '{p}'\n" for p in parts))
    mp4 = OUT / 'chapter_titles_apercu.mp4'
    subprocess.run([exe, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy',
                    str(mp4)], check=True)
    lst.unlink()
    return mp4


# ----------------------------------------------------------------------------- textes affichés et vérification
def texts():
    """textes affichés, tels qu'ils sont composés (typographie française, espaces insécables)"""
    return {k: [typo(s) for s in v] for k, v in _texts().items()}


def _texts():
    ct = chapter_titles()
    return {
        'map': ['PÉLOPONNÈSE', 'CRÈTE', 'Cythère', 'Anticythère', 'épave', '40–50 m de fond', 'Symi', '50 km', 'N',
                'Printemps 1900', "Pêcheurs d'éponges de Symi"],
        'phases': ['Vue du dessus', "pas à l'échelle", 'Soleil', 'Terre', 'Lune', 'boule des phases', 'noire',
                   'blanche', 'aiguille du Soleil', 'aiguille de la Lune', 'Superposées : nouvelle lune',
                   'Opposées : pleine lune'],
        'metonic_cell': ['Une case agrandie', 'spirale de Méton', 'ΦΟΙΝΙΚΑΙΟΣ', 'L Α', 'Phoinikaios',
                         'nom du mois (corinthien)', '… an 1', 'L = année, Α = 1',
                         "illustration d'après Freeth et al. 2008"],
        'games_banner': ["Cadran des Jeux : les 4 années de l'original", 'Freeth et al. 2008 ; Iversen 2017'] +
                        [f'{a} : {b}' for a, b, _ in GAMES] + [g for _, _, g in GAMES],
        'glyph_anatomy': ["Anatomie d'un signe", 'exemple', 'Σ', 'ΩΡ Δ', 'Κ', 'Σ = éclipse de Lune',
                          '(Η = éclipse de Soleil)', 'ΩΡ + chiffre = heure', 'ici Δ = 4', "Lettre d'index → détails",
                          'direction, grandeur, couleur',
                          'Dans notre modèle, la case 112 ne porte ni heure ni lettre.',
                          'Forme des signes : Freeth et al. 2008 ; Freeth 2014'],
        'parapegma_line': ['Ξ', 'La Pléiade se lève le matin', 'illustration',
                           "ligne du parapegme d'après Bitsakis & Jones 2016"],
        'end_card': ['Comment lire la machine'] + [f'{n}. {t}{h_ or ""}' for n, t, h_ in STEPS] + [QUESTION, CREDITS],
        'chapter_titles': [f'{n} · {ct[n]}' for n in range(1, 8)],
    }


FORBIDDEN = ['premier ordinateur', 'archimède', 'date exacte', '1901', 'navigation instrument']
REQUIRED = {   # textes imposés par script.md (colonne « Textes à l'écran » / « Schéma 2D ») ou par la tâche
    'map': ['Printemps 1900', "Pêcheurs d'éponges de Symi", '40–50 m de fond', 'Cythère', 'Anticythère', 'épave'],
    'phases': ['Superposées : nouvelle lune', 'Opposées : pleine lune'],
    'metonic_cell': ['Phoinikaios', "illustration d'après Freeth et al. 2008"],
    'games_banner': ['An 1 : Isthmia, Olympia', 'An 2 : Nemea, Naa', 'An 3 : Isthmia, Pythia', 'An 4 : Nemea, Halieia',
                     'Freeth et al. 2008 ; Iversen 2017'],
    'glyph_anatomy': ['exemple', 'ΩΡ + chiffre = heure', "Lettre d'index → détails"],
    'parapegma_line': ['La Pléiade se lève le matin', 'illustration'],
    'end_card': ['1. Tournez la manivelle', '2. Soleil : date, saison', '3. Lune : place, phase',
                 '4. Planètes : place (hypothèse)', '5. Dos : mois, Jeux', '6. Signe : éclipse, heure',
                 'Et vous, quelle date ?', CREDITS],
    'chapter_titles': ['1 · Le ciel dans une boîte', '7 · Et la navigation ?'],
}


def check_texts():
    T = texts()
    script = SCRIPT_MD.read_text(encoding='utf-8')
    errs = []
    for name, lst in T.items():
        low = plain(' '.join(lst)).lower()
        errs += [f'{name}: mot interdit « {w} »' for w in FORBIDDEN if w in low]
        errs += [f'{name}: texte imposé absent « {r} »' for r in REQUIRED.get(name, []) if typo(r) not in lst]
        # typographie : insécable avant : ; ! ? et dans « », jamais d'espace ordinaire
        errs += [f'{name}: typographie « {s} »' for s in lst
                 if re.search(r'( [:;!?])|(« )|( »)|(\d [mh]\b)', s) or re.search(r'[^\u00a0]:(\s|$)', s)
                 or re.search(r'[^\u202f][;!?]', s)]
    # les étapes du carton final et les textes de la carte doivent être ceux de script.md
    for s in REQUIRED['end_card'][:7] + REQUIRED['map'][:3] + REQUIRED['games_banner'][:4]:
        if plain(s) not in script:
            errs.append(f'absent de script.md : « {s} »')
    # titres de chapitre : ceux de script.md (« ## N. Titre (environ … s) »)
    for n in range(1, 8):
        if f'## {n}. {chapter_titles()[n]} (environ' not in script:
            errs.append(f'titre du chapitre {n} absent de script.md')
    if 'taciclei' not in CREDITS or 'Lean 4' not in CREDITS:
        errs.append('crédits incomplets')
    return errs


def timing():
    fa = games_arrival_frame()
    ts = games_year_start()
    return {
        'fps': FPS, 'taille': [W, H], 'numerotation': '%04d.png, première image 0001',
        'alpha': "RGBA à alpha droit (non prémultiplié) ; ombre portée de la charte déjà incluse dans les calques "
                 "transparents ; ffmpeg : overlay=format=auto",
        'charte': 'build/out/explainer/film/overlay_style.json (tools/explainer/overlay.py)',
        'map': {'images': MAP_N, 'duree_s': MAP_N / FPS, 'plan': '1.3 (plein écran, opaque)', 'rgba': False,
                'segments': {'carte_lisible_des': 1, 'epave_pulse': [7, MAP_N], 'printemps_1900': [17, 29],
                             'symi': [31, 43], 'profondeur': [45, 57], 'tout_est_lisible_a_partir_de': 58},
                'note': "Lent travelling avant vers Anticythère sur toute la durée (vue MAP_V0 -> MAP_V1). Côtes : "
                        "Natural Earth 10 m (domaine public), simplifiées à 0,0022° ; épave au nord-est d'Anticythère "
                        "(faits.md 1.5). Aucune ville. Symi est hors carte, à l'est (flèche).",
                'textes': texts()['map']},
        'phases': {'images': PH_N, 'duree_s': PH_N / FPS, 'plan': '3.4 (incrustation, transparent)', 'rgba': True,
                   'boite': list(PH_BOX),
                   'segments': {'entree': [1, 12], 'nouvelle_lune_tenue': [13, PH_GO],
                                'manivelle_0972_1009': [PH_GO + 1, PH_ARR + 1], 'pleine_lune_tenue': [PH_ARR + 2, PH_N - 10],
                                'sortie': [PH_N - 9, PH_N]},
                   'note': ("Caler l'image %d sur « Opposées » : AM_Controller[\"crank\"] = colonne « manivelle » "
                            "image par image ; la Lune du schéma et la boule de la machine suivent la même élongation "
                            "(engine.py). La légende « Superposées : nouvelle lune » / « Opposées : pleine lune » est "
                            "dans l'incrustation : ne pas la doubler en callout ; reste « Lune dans ΧΗΛΑΙ (Balance) »."
                            % (PH_GO + 1)),
                   'manivelle_par_image': [{'image': f + 1, 'manivelle': round(phases_crank(f), 6),
                                            'elongation_deg': round(elongation(round(phases_crank(f), 6)), 2)}
                                           for f in range(PH_N)],
                   'textes': texts()['phases']},
        'metonic_cell': {'images': MC_N, 'duree_s': MC_N / FPS, 'plan': '5.2 (incrustation, transparent)', 'rgba': True,
                         'boite': list(MC_BOX),
                         'segments': {'entree': [1, 10], 'reflet': [15, 42], 'phoinikaios': [25, 37], 'an_1': [37, 49],
                                      'mention_illustration': [47, 59], 'tenue': [60, MC_N - 8],
                                      'sortie': [MC_N - 7, MC_N]},
                         'note': "Case illustrative (le modèle n'a pas de noms dans les cases, script.md note 4).",
                         'textes': texts()['metonic_cell']},
        'games_banner': {'images': GB_N, 'duree_s': GB_N / FPS, 'plan': '5.3 (bandeau, transparent)', 'rgba': True,
                         'boite': list(GB_BOX),
                         'segments': {'entree': [1, 12], 'manivelle_3_595': [GB_F0 + 1, GB_F1 + 1],
                                      'arrivee_an_1': fa + 1, 'tenue': [fa + 2, GB_N - 10], 'sortie': [GB_N - 9, GB_N]},
                         'an_1_commence_a_la_manivelle': round(ts, 5),
                         'note': ("Le curseur sous les cases suit l'aiguille des Jeux de notre modèle (engine.py, "
                                  "étiquettes historiques par paires). Poser AM_Controller[\"crank\"] = colonne "
                                  "« manivelle » pour que l'aiguille arrive sur ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ à l'image %d, sur "
                                  "« Olympia ! » de la voix." % (fa + 1)),
                         'manivelle_par_image': [{'image': f + 1, 'manivelle': round(games_crank(f), 6),
                                                  'annee': int(games_year_pos(games_crank(f))) + 1}
                                                 for f in range(GB_N)],
                         'textes': texts()['games_banner']},
        'glyph_anatomy': {'images': GA_N, 'duree_s': GA_N / FPS, 'plan': '6.3 (incrustation, transparent)',
                          'rgba': True, 'boite': list(GA_BOX),
                          'segments': {'entree': [1, 10], 'sigma': [13, 25], 'heure': [35, 47], 'lettre_index': [57, 69],
                                       'notes': [67, 79], 'tenue': [80, GA_N - 9], 'sortie': [GA_N - 8, GA_N]},
                          'note': "Schéma marqué « exemple » (Σ, ΩΡ Δ, Κ) : la case 112 du modèle ne porte que « Σ Η », "
                                  "ni heure ni lettre (script.md note 1).",
                          'textes': texts()['glyph_anatomy']},
        'parapegma_line': {'images': PP_N, 'duree_s': PP_N / FPS, 'plan': '7.2 (surimpression, transparent)',
                           'rgba': True,
                           'segments': {'repere_xi': [1, 13], 'ecriture': [PP_W0 + 1, PP_W1 + 1],
                                        'mention_illustration': [PP_W1 + 3, PP_W1 + 15], 'tenue': [PP_W1 + 16, PP_N - 10],
                                        'sortie': [PP_N - 9, PP_N]},
                           'ancre_xi': list(PP_XI), 'ligne_de_base_y': PP_LINE_Y,
                           'calques_separes': {'parapegma_xi': 'repère Ξ seul, centré sur (960, 540) : décaler de '
                                                               '(x − 960, y − 540) pour le poser sur l\'échelle du '
                                                               'zodiaque, sous le Soleil (vers 17° de ΤΑΥΡΟΣ)',
                                               'parapegma_ligne': 'ligne + mention seules (sur la plaque du haut)'},
                           'note': "Surimpression illustrative (script.md note 3) : le modèle n'a ni lettres sur "
                                   "l'échelle ni texte de parapegme.",
                           'textes': texts()['parapegma_line']},
        'parapegma_xi': {'images': PP_N, 'identique_a': 'parapegma_line', 'ancre_xi': [W // 2, H // 2]},
        'parapegma_ligne': {'images': PP_N, 'identique_a': 'parapegma_line'},
        'end_card': {'images': EC_N, 'duree_s': EC_N / FPS, 'plan': '7.6 (plein écran, opaque, vignettage)',
                     'rgba': False,
                     'segments': {'etapes': [1, 15], 'question': [EC_Q0 + 1, EC_Q0 + 15],
                                  'credits': [EC_Q0 + 17, EC_Q0 + 31], 'tenue': [EC_Q0 + 32, EC_N]},
                     'fond_seul': 'end_card_fond.png (parchemin + vignettage, sans texte)',
                     'variante_transparente': "end_card_texte : mêmes textes en RGBA ; pour « la machine en fondu "
                                              "derrière » : fond_seul, puis la machine à ~20 % d'opacité, puis "
                                              "end_card_texte",
                     'note': "Caler l'image %d sur « Et vous, quelle date… » de la voix. Pas de sous-titres sur ce "
                             "carton (les crédits occupent le bas)." % (EC_Q0 + 1),
                     'textes': texts()['end_card']},
        'end_card_texte': {'images': EC_N, 'identique_a': 'end_card', 'rgba': True},
        'chapter_titles': {'images': CT_N, 'duree_s': CT_N / FPS, 'rgba': True,
                           'sequences': [f'chapter_title_{n}' for n in range(1, 8)],
                           'boite': [CT_X0, CT_YB - 104, 'largeur selon le titre', CT_YB],
                           'segments': {'entree': [1, 21], 'tenue': [22, CT_N - 11], 'sortie': [CT_N - 10, CT_N]},
                           'note': "En bas à gauche, au-dessus des sous-titres (bas de la carte à y = 876).",
                           'textes': texts()['chapter_titles']},
    }


# ----------------------------------------------------------------------------- index des séquences rendues
SHOTS = {   # nom -> (plan de script.md, rôle, boîte ou placement)
    'map': ('1.3', 'carte animée plein écran (remplace la 3D)', 'plein cadre'),
    'phases': ('3.4', 'incrustation à droite : vue du dessus Soleil-Terre-Lune + boule des phases', list(PH_BOX)),
    'metonic_cell': ('5.2', 'incrustation à droite : case de Méton agrandie « Phoinikaios… an 1 » (illustration)',
                     list(MC_BOX)),
    'games_banner': ('5.3', 'bandeau des 4 années d\'origine, curseur synchronisé sur la manivelle', list(GB_BOX)),
    'glyph_anatomy': ('6.3', 'incrustation à droite : anatomie d\'un signe, marquée « exemple »', list(GA_BOX)),
    'parapegma_line': ('7.2', 'repère Ξ + ligne du parapegme (version composée, repère en %s)' % (PP_XI,),
                       'ligne centrée, ligne de base y = %d' % PP_LINE_Y),
    'parapegma_xi': ('7.2', 'repère Ξ seul, centré sur (960, 540) : à translater sous le Soleil', 'ancre (960, 540)'),
    'parapegma_ligne': ('7.2', 'ligne « Ξ  La Pléiade se lève le matin » seule, à poser sur la plaque du haut',
                        'ligne de base y = %d' % PP_LINE_Y),
    'end_card': ('7.6', 'carton final opaque (parchemin + vignettage)', 'plein cadre'),
    'end_card_texte': ('7.6', 'textes du carton final en RGBA, sur end_card_fond.png et la machine en fondu',
                       'plein cadre'),
}
for _n in range(1, 8):
    SHOTS[f'chapter_title_{_n}'] = (f'{_n}.1', f'titre du chapitre {_n} en bas à gauche (0,2 s après le début du '
                                               f'premier plan du chapitre)', [CT_X0, CT_YB - 104, None, CT_YB])


def write_index():
    """build/out/explainer/inserts/index.json : une entrée par séquence rendue (dossier présent)"""
    seqs = []
    for name, (n, _, rgba, shadow, bg) in INSERTS.items():
        d = OUT / name
        if not d.is_dir():
            continue
        files = sorted(d.glob('[0-9][0-9][0-9][0-9].png'))
        with Image.open(files[0]) as im0:
            size, mode = list(im0.size), im0.mode
        shot, role, place = SHOTS[name]
        e = {'name': name, 'path': f'build/out/explainer/inserts/{name}', 'pattern': '%04d.png', 'first': 1,
             'frames': len(files), 'frames_expected': n, 'fps': FPS, 'duration_s': round(len(files) / FPS, 2),
             'size': size, 'mode': mode, 'transparent': bool(rgba), 'shadow_included': bool(shadow and rgba),
             'shot': shot, 'role': role, 'placement': place}
        if name.startswith('chapter_title_'):
            e['text'] = texts()['chapter_titles'][int(name[-1]) - 1]
            e['group'] = 'chapter_titles'
        mp4 = OUT / f'{name}_apercu.mp4'
        if mp4.exists():
            e['preview'] = f'build/out/explainer/inserts/{mp4.name}'
            e['preview_background'] = ('look2/%s_eevee.png' % bg) if (rgba and bg and bg != 'parchemin') else (
                'parchemin' if rgba else None)
        seqs.append(e)
    extra = []
    if (OUT / 'end_card_fond.png').exists():
        extra.append({'name': 'end_card_fond', 'path': 'build/out/explainer/inserts/end_card_fond.png', 'frames': 1,
                      'transparent': False, 'shot': '7.6', 'role': 'fond du carton final (parchemin + vignettage, '
                                                                        'sans texte), sous end_card_texte'})
    if (OUT / 'chapter_titles_apercu.mp4').exists():
        extra.append({'name': 'chapter_titles', 'preview': 'build/out/explainer/inserts/chapter_titles_apercu.mp4',
                      'sequences': [f'chapter_title_{k}' for k in range(1, 8)],
                      'role': 'les 7 titres de chapitre (aperçu à la suite)'})
    idx = {'generated_by': 'tools/explainer/inserts.py', 'fps': FPS, 'size': [W, H],
           'numbering': '%04d.png, première image 0001',
           'alpha': 'RGBA à alpha droit (non prémultiplié) ; ffmpeg : overlay=format=auto',
           'timing': 'build/out/explainer/inserts/timing.json (segments, manivelle image par image, textes)',
           'style': 'build/out/explainer/film/overlay_style.json (charte commune avec overlay.py et diagrams.py)',
           'typography': 'espace insécable (U+00A0) avant « : » et dans « », espace fine insécable (U+202F) avant '
                         '; ! ?, insécable entre nombre et unité',
           'sequences': seqs, 'extras': extra}
    (OUT / 'index.json').write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    return idx


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('names', nargs='*', default=list(INSERTS))
    ap.add_argument('--frames', help='liste d\'images (1-based) à rendre, pour tester')
    ap.add_argument('--out', help='dossier de sortie (tests)')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--no-preview', action='store_true')
    ap.add_argument('--check', action='store_true', help='vérifie seulement les textes')
    ap.add_argument('--index', action='store_true', help='réécrit seulement index.json (séquences déjà rendues)')
    args = ap.parse_args()
    errs = check_texts()
    if errs:
        print('\n'.join('ERREUR ' + e for e in errs))
        sys.exit(1)
    print('textes : OK (%d textes vérifiés)' % sum(len(v) for v in texts().values()))
    if args.check:
        return
    if args.index:
        idx = write_index()
        print(f'index : {len(idx["sequences"])} séquences -> {OUT / "index.json"}')
        return
    D.ensure_fonts()
    geo_rings()
    OUT.mkdir(parents=True, exist_ok=True)
    names = [n for a in args.names for n in ([f'chapter_title_{k}' for k in range(1, 8)] if a == 'chapter_titles'
                                              else [a])]
    for name in names:
        n = INSERTS[name][0]
        if args.frames:
            frames = [int(x) - 1 for x in args.frames.split(',')]
            outdir = Path(args.out or OUT / '_tests') / name
        else:
            frames = list(range(n))
            outdir = OUT / name
            if outdir.exists():
                shutil.rmtree(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        jobs = [(name, f, str(outdir)) for f in frames]
        if args.workers > 1 and len(jobs) > 4:
            with Pool(args.workers) as pool:
                for _ in pool.imap_unordered(_render, jobs, chunksize=4):
                    pass
        else:
            for j in jobs:
                _render(j)
        print(f'{name}: {len(frames)} images -> {outdir}')
        if not args.frames and not args.no_preview:
            mp4 = preview(name, outdir)
            if mp4:
                print(f'  aperçu {mp4}')
    if not args.frames:
        if 'end_card' in names:
            save_frame(end_bg(), OUT / 'end_card_fond.png', False, False)
        if any(n.startswith('chapter_title_') for n in names) and not args.no_preview:
            chapter_preview()
        (OUT / 'timing.json').write_text(json.dumps(timing(), ensure_ascii=False, indent=1), encoding='utf-8')
        idx = write_index()
        print(f'index : {len(idx["sequences"])} séquences -> {OUT / "index.json"}')


def end_bg():
    fr = Frame(bg=BG)
    fr.img(vignette_img(), 0, 0, W, H, z=0)
    return fr


if __name__ == '__main__':
    main()
