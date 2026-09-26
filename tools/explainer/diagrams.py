#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schémas 2D animés du film « Le ciel dans une boîte » (build/out/explainer/script.md).

Séquences PNG 1920x1080, 25 i/s, dans build/out/explainer/diagrams/<nom>/%04d.png (numérotées à partir de 0001),
plus un aperçu MP4 par séquence (<nom>_apercu.mp4) et timing.json (plages d'images, manivelle image par image).

  retrograde        plan 4.3  Soleil, orbites de la Terre et de Mars, lignes de visée, boucle de Mars sur le zodiaque
  retrograde_split  plan 4.3  même schéma dans la moitié droite, moitié gauche transparente (RGBA) pour l'écran partagé
  eclipse           plan 6.5  orbite de la Lune inclinée, nœuds, nouvelle lune loin d'un nœud, éclipse de Soleil,
                              éclipse de Lune, aiguille du Dragon (hypothèse)
  pleiades_lever    plan 7.3  aube de mai à l'est, lever des Pléiades, barre de saison de Végèce qui se remplit
  pleiades_coucher  plan 7.4  aube d'automne à l'ouest, les Pléiades plongent dans une mer grise, Hésiode, mer fermée

Rétrogradation : la Terre et Mars sont sur des orbites circulaires (1 an ; 284/151 = 1,8808 an, rapport de la
reconstruction de Mars) calées sur la sortie de Mars de notre modèle (tools/explainer/engine.py, machine non calée) :
écart maximal 0,02° entre 2,08 et 2,54 ans de manivelle, stations aux mêmes instants (2,2135 et 2,4132).
Le schéma est donc synchrone de la machine si la manivelle suit la colonne « manivelle » de timing.json.
La latitude de Mars (inclinaison réelle 1,85°, nœud choisi pour dessiner une boucle) n'existe pas dans la machine :
elle ne sert qu'à ouvrir la boucle ; elle est à l'échelle des longitudes (pas d'exagération).

Étoiles des Pléiades : positions J2000 (Hipparcos) des neuf étoiles les plus brillantes, positions relatives exactes,
amas agrandi par rapport au paysage. Orientation de l'amas au lever et au coucher pour la latitude 36° N.

Usage (Python du venv ~/voxtral-tts, qui a matplotlib ; les polices OFL sont téléchargées dans build/cache/fonts) :
  ~/voxtral-tts/bin/python tools/explainer/diagrams.py                 # tout
  ~/voxtral-tts/bin/python tools/explainer/diagrams.py eclipse --frames 1,120,250 --out /tmp/x   # images tests
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.request
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import to_rgb, to_rgba  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle, Wedge  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build' / 'out' / 'explainer' / 'diagrams'
FONT_DIR = ROOT / 'build' / 'cache' / 'fonts'
W, H, FPS = 1920, 1080, 25
DPI = 100
PT = 72.0 / DPI                      # taille en points pour 1 px

# ----------------------------------------------------------------------------- palette (atelier en lumière du jour)
BG = '#F3EAD8'           # parchemin
PAPER = '#FBF5EA'
INK = '#2A2118'
MUTED = '#6B5B47'
RULE = '#E0CFAF'
RULE_STRONG = '#CDB48A'
BRONZE = '#9A6B2F'
GOLD = '#C8963E'
BRASS = '#EDD9AA'
HYP = '#62529A'          # « hypothèse » (même violet que la page web)
OK = '#2C7263'           # vert-de-gris : mer sûre
RISK = '#C8963E'         # or : mer incertaine
SHUT = '#4E5561'         # ardoise : mer fermée
EARTH = '#2F6DB0'
EARTH_NIGHT = '#1C3A63'


def lin2srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return tuple(np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055))


# couleurs de spec dials.front.planet_display (rgb linéaire -> sRGB)
SUN = lin2srgb([1.0, 0.72, 0.06])
MOON = lin2srgb([0.86, 0.88, 0.95])
MARS = lin2srgb([1.0, 0.08, 0.05])
MARS_INK = '#A8322A'     # même teinte, assez sombre pour du texte sur parchemin

# ----------------------------------------------------------------------------- polices (celles de la page web)
FONT_URLS = {
    'IBMPlexSans-Regular.ttf': 'https://github.com/IBM/plex/raw/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-Regular.ttf',
    'IBMPlexSans-Medium.ttf': 'https://github.com/IBM/plex/raw/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-Medium.ttf',
    'IBMPlexSans-SemiBold.ttf': 'https://github.com/IBM/plex/raw/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-SemiBold.ttf',
    'IBMPlexSans-Italic.ttf': 'https://github.com/IBM/plex/raw/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-Italic.ttf',
    'Marcellus-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/marcellus/Marcellus-Regular.ttf',
    'GentiumBookPlus-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/gentiumbookplus/GentiumBookPlus-Regular.ttf',
    'GentiumBookPlus-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/gentiumbookplus/GentiumBookPlus-Italic.ttf',
    'GentiumBookPlus-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/gentiumbookplus/GentiumBookPlus-Bold.ttf',
}
FONT_FALLBACK = {'sans': '/System/Library/Fonts/Avenir Next.ttc', 'serif': '/System/Library/Fonts/Palatino.ttc'}
FONTS = {'sans': 'IBMPlexSans-Regular.ttf', 'sansm': 'IBMPlexSans-Medium.ttf', 'sansb': 'IBMPlexSans-SemiBold.ttf',
         'sansi': 'IBMPlexSans-Italic.ttf',
         'display': 'Marcellus-Regular.ttf', 'greek': 'GentiumBookPlus-Bold.ttf', 'serif': 'GentiumBookPlus-Regular.ttf',
         'quote': 'GentiumBookPlus-Italic.ttf'}


def ensure_fonts():
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in FONT_URLS.items():
        p = FONT_DIR / name
        if p.exists() and p.stat().st_size > 10000:
            continue
        try:
            urllib.request.urlretrieve(url, p)
        except Exception as e:  # pragma: no cover
            print(f'  police {name} indisponible ({e}), police système utilisée', file=sys.stderr)


@lru_cache(maxsize=None)
def font_path(key):
    p = FONT_DIR / FONTS[key]
    if p.exists():
        return str(p)
    return FONT_FALLBACK['serif' if key in ('display', 'greek', 'serif', 'quote') else 'sans']


@lru_cache(maxsize=None)
def fp(key, px):
    return FontProperties(fname=font_path(key), size=px * PT)


# ----------------------------------------------------------------------------- temps et courbes
def clamp01(x):
    return min(1.0, max(0.0, x))


def smooth(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def ease(u):
    """cubique entrée-sortie"""
    u = clamp01(u)
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def ramp(f, a, b):
    """0 -> 1 lissé entre les images a et b"""
    return smooth((f - a) / float(b - a)) if b > a else float(f >= a)


def fade(f, a_in, b_in, a_out=None, b_out=None):
    v = ramp(f, a_in, b_in)
    if a_out is not None:
        v *= 1 - ramp(f, a_out, b_out)
    return v


def mix(c1, c2, u):
    a, b = np.array(to_rgba(c1)), np.array(to_rgba(c2))
    return tuple(a + (b - a) * clamp01(u))


# ----------------------------------------------------------------------------- dessin de base
class Frame:
    """Une image 1920x1080 en coordonnées pixels (y vers le bas)."""

    def __init__(self, bg=BG, transparent=False):
        self.fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        ax = self.ax
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)
        ax.set_autoscale_on(False)
        ax.axis('off')
        self.transparent = transparent
        if transparent:
            self.fig.patch.set_alpha(0)
            ax.patch.set_alpha(0)
        else:
            self.fig.patch.set_facecolor(bg)
            ax.add_patch(Rectangle((0, 0), W, H, color=bg, zorder=-100))

    def text(self, x, y, s, px, key='sans', color=INK, alpha=1.0, ha='left', va='baseline', z=50,
             halo=None, halo_w=6, rotation=0, lh=1.25, clip=None):
        if alpha <= 0.003 or not s:
            return None
        t = self.ax.text(x, y, s, fontproperties=fp(key, px), color=color, alpha=alpha, ha=ha, va=va,
                         zorder=z, rotation=rotation, linespacing=lh)
        if halo:
            t.set_path_effects([pe.withStroke(linewidth=halo_w, foreground=halo, alpha=alpha)])
        if clip is not None:
            t.set_clip_path(clip)
        return t

    def width(self, s, px, key='sans'):
        t = self.ax.text(0, 0, s, fontproperties=fp(key, px))
        bb = t.get_window_extent(renderer=self.fig.canvas.get_renderer())
        t.remove()
        return bb.width

    def rich(self, x, y, runs, alpha=1.0, ha='left', z=50, halo=None, halo_w=6):
        """runs = [(texte, police, px, couleur, dy)] sur une même ligne de base"""
        widths = [self.width(r[0], r[2], r[1]) for r in runs]
        total = sum(widths)
        x0 = x - (total if ha == 'right' else total / 2 if ha == 'center' else 0)
        for (s, key, px, col, dy), w_ in zip(runs, widths):
            self.text(x0, y + dy, s, px, key, col, alpha, z=z, halo=halo, halo_w=halo_w)
            x0 += w_
        return total

    def img(self, arr, x0, y0, x1, y1, z=0, alpha=1.0, clip=None):
        im = self.ax.imshow(arr, extent=(x0, x1, y1, y0), zorder=z, alpha=alpha, aspect='auto',
                            interpolation='bilinear', origin='upper')
        if clip is not None:
            im.set_clip_path(clip)
        return im

    def glow(self, x, y, r, color, alpha=1.0, z=1, power=2.0, clip=None):
        if alpha <= 0.003:
            return
        self.img(radial(color, power), x - r, y - r, x + r, y + r, z=z, alpha=alpha, clip=clip)

    def save(self, path, rgba=False):
        self.fig.canvas.draw()
        buf = np.asarray(self.fig.canvas.buffer_rgba())
        from PIL import Image
        im = Image.fromarray(buf.copy(), 'RGBA')
        if not rgba:
            im = im.convert('RGB')
        im.save(path, compress_level=4)
        plt.close(self.fig)


@lru_cache(maxsize=None)
def radial(color, power=2.0, n=256):
    y, x = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
    a = np.clip(1 - np.hypot(x, y), 0, 1) ** power
    img = np.zeros((n, n, 4))
    img[..., :3] = to_rgb(color)
    img[..., 3] = a
    return img


def vgradient(stops, n=512):
    """dégradé vertical : stops = [(position 0..1, couleur)] ; renvoie un tableau (n, 1, 4)"""
    pos = np.array([s[0] for s in stops])
    cols = np.array([to_rgba(s[1]) for s in stops])
    y = np.linspace(0, 1, n)
    out = np.stack([np.interp(y, pos, cols[:, k]) for k in range(4)], axis=-1)
    return out[:, None, :]


def hgradient(stops, n=512):
    return np.transpose(vgradient(stops, n), (1, 0, 2))


def star4(x, y, r, inner=0.38):
    """étoile à 4 branches (repère de parapegme)"""
    pts = []
    for k in range(8):
        a = math.pi / 2 + k * math.pi / 4
        rr = r if k % 2 == 0 else r * inner
        pts.append((x + rr * math.cos(a), y - rr * math.sin(a)))
    return pts


def arrow(fr, x0, y0, x1, y1, color, lw=3, alpha=1.0, head=16, z=40):
    if alpha <= 0.003:
        return
    ax = fr.ax
    ax.plot([x0, x1], [y0, y1], color=color, lw=lw, alpha=alpha, zorder=z, solid_capstyle='round')
    ang = math.atan2(y1 - y0, x1 - x0)
    pts = [(x1 + head * 0.35 * math.cos(ang), y1 + head * 0.35 * math.sin(ang)),
           (x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45)),
           (x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))]
    ax.add_patch(Polygon(pts, closed=True, color=color, alpha=alpha, zorder=z, lw=0))


# ============================================================================= 1. RÉTROGRADATION (plan 4.3)
# Orbites circulaires calées sur la Mars de notre modèle (voir le docstring).
RETRO_T0, RETRO_T1 = 2.10, 2.52          # plage de manivelle du plan 4.2 / 4.3
MARS_A = 1.52                            # rayon de l'orbite de Mars (ua) : ajusté sur la machine
MARS_P = 284.0 / 151.0                   # période sidérale de Mars (ans) : 133 cycles synodiques en 284 ans
MARS_TH_REF = math.radians(292.1582)     # longitude héliocentrique de Mars à t = 2,31 (ajustée sur la machine)
MARS_I = math.radians(1.85)              # inclinaison réelle de l'orbite de Mars
MARS_U_OPP = math.radians(75.0)          # argument de latitude à l'opposition : choisi pour une boucle ouverte

RETRO_N = 200
RETRO_IN = 38                            # images 1-38 : mise en place (manivelle 2,10)
RETRO_SWEEP = 100                        # images 39-138 : manivelle 2,10 -> 2,52 (4 s, comme le plan 4.3)


def retro_crank(f):
    """manivelle (ans) à l'image f (0-based) : départ et arrivée doux (75 % linéaire + 25 % smoothstep)"""
    u = clamp01((f - RETRO_IN) / (RETRO_SWEEP - 1))
    return RETRO_T0 + (RETRO_T1 - RETRO_T0) * (0.75 * u + 0.25 * smooth(u))


def retro_state(t):
    t = np.asarray(t, float)
    thE = 2 * np.pi * t + np.pi                               # Terre = Soleil moyen de la machine + 180°
    thM = MARS_TH_REF + 2 * np.pi * (t - 2.31) / MARS_P
    xE, yE = np.cos(thE), np.sin(thE)
    xM, yM = MARS_A * np.cos(thM), MARS_A * np.sin(thM)
    dx, dy = xM - xE, yM - yE
    lam = np.arctan2(dy, dx)
    rho = np.hypot(dx, dy)
    th_node = MARS_TH_REF + 2 * np.pi * (RETRO_T_OPP - 2.31) / MARS_P - MARS_U_OPP
    zM = MARS_A * math.sin(MARS_I) * np.sin(thM - th_node)
    beta = np.arctan2(zM, rho)
    return dict(thE=thE, thM=thM, lam=lam, beta=beta, rho=rho)


def _opp_time():
    ts = np.linspace(2.2, 2.4, 20001)
    thE = 2 * np.pi * ts + np.pi
    thM = MARS_TH_REF + 2 * np.pi * (ts - 2.31) / MARS_P
    xE, yE = np.cos(thE), np.sin(thE)
    lam = np.arctan2(MARS_A * np.sin(thM) - yE, MARS_A * np.cos(thM) - xE)
    el = (lam - 2 * np.pi * ts) % (2 * np.pi)
    return float(ts[np.argmin(np.abs(el - np.pi))])


RETRO_T_OPP = _opp_time()


def _stations():
    ts = np.linspace(RETRO_T0, RETRO_T1, 42001)
    lam = np.unwrap(retro_state(ts)['lam'])
    d = np.diff(lam)
    idx = np.where(np.sign(d[1:]) != np.sign(d[:-1]))[0] + 1
    return [float(ts[i]) for i in idx]


RETRO_ST1, RETRO_ST2 = _stations()

RETRO_LAYOUTS = {
    'full': dict(x0=0, w=1920, sun=(960, 250), rE=205, ray_end=640, strip=(250, 712, 1670, 1040),
                 title_top=(70, 86), title_strip=(250, 694), periods=(70, 150), overtake=(1330, 395, 'left'),
                 retro_msg=(1670, 694, 'right'), rpx=1.0, loop_top=92),
    'split': dict(x0=960, w=960, sun=(1440, 222), rE=160, ray_end=515, strip=(1000, 655, 1880, 955),
                  title_top=(1000, 70), title_strip=(1000, 638), periods=(1880, 70), overtake=(1440, 580, 'center'),
                  retro_msg=(1440, 1028, 'center'), rpx=0.9, loop_top=92),
}


@lru_cache(maxsize=None)
def retro_track():
    ts = np.linspace(RETRO_T0, RETRO_T1, 1201)
    s = retro_state(ts)
    lam = np.degrees(np.unwrap(s['lam']))
    lam = lam - 360.0 * np.floor(lam.mean() / 360.0)          # longitudes dans [0, 360)
    return ts, lam, np.degrees(s['beta'])


def retro_frame(f, variant='full'):
    L = RETRO_LAYOUTS[variant]
    split = variant == 'split'
    fr = Frame(transparent=split)
    ax = fr.ax
    if split:   # panneau parchemin à droite, gauche transparente
        ax.add_patch(Rectangle((L['x0'], 0), L['w'], H, color=BG, zorder=-100))
        ax.add_patch(Rectangle((L['x0'], 0), 4, H, color=RULE_STRONG, zorder=-99))
    t = retro_crank(f)
    ts_all, lam_all, beta_all = retro_track()
    cx, cy = L['sun']
    rE = L['rE']
    rM = MARS_A * rE
    rot = -math.pi / 2 - (2 * np.pi * RETRO_T_OPP + np.pi)   # opposition vers le bas de l'image

    def scr(r, th):
        a = th + rot
        return cx + r * np.cos(a), cy - r * np.sin(a)

    a_orb = ramp(f, 0, 24)
    a_bod = ramp(f, 8, 26)
    a_strip = ramp(f, 14, 36)
    a_lbl = ramp(f, 18, 36)
    k = L['rpx']

    # --- titres
    fr.text(*L['title_top'], 'VUE DU DESSUS', 30, 'sansb', BRONZE, a_lbl)
    if split:
        fr.text(L['periods'][0], L['periods'][1], 'Terre : 1 tour en 1 an', 30, 'sans', MUTED, a_lbl, ha='right',
                halo=BG)
        fr.text(L['periods'][0], L['periods'][1] + 40, 'Mars : 1 tour en 1,88 an', 30, 'sans', MUTED, a_lbl,
                ha='right', halo=BG)
    else:
        fr.text(L['periods'][0], L['periods'][1], 'Terre : 1 tour en 1 an', 32, 'sans', MUTED, a_lbl)
        fr.text(L['periods'][0], L['periods'][1] + 44, 'Mars : 1 tour en 1,88 an', 32, 'sans', MUTED, a_lbl)

    # --- orbites (tracées progressivement)
    th = np.linspace(0, 2 * np.pi * a_orb, 400)
    if a_orb > 0:
        for r, col in ((rE, EARTH), (rM, MARS_INK)):
            x, y = scr(r, th + 2 * np.pi * RETRO_T_OPP + np.pi)     # départ au point d'opposition
            ax.plot(x, y, color=col, lw=2.2, alpha=0.38, zorder=5)

    # --- Soleil
    fr.glow(cx, cy, 120 * k, SUN, alpha=0.55 * a_bod, z=6)
    ax.add_patch(Circle((cx, cy), 34 * k, facecolor=SUN, edgecolor=GOLD, lw=2.5, alpha=a_bod, zorder=7))
    fr.text(cx, cy - 52 * k, 'Soleil', 32, 'sansm', BRONZE, a_lbl, ha='center', halo=BG)

    # --- état courant et traînées
    s = retro_state(t)
    xE, yE = scr(rE, s['thE'])
    xM, yM = scr(rM, s['thM'])
    past = ts_all <= t + 1e-9
    if past.sum() > 1:
        sp = retro_state(ts_all[past])
        ex, ey = scr(rE, sp['thE'])
        mx, my = scr(rM, sp['thM'])
        ax.plot(ex, ey, color=EARTH, lw=5, alpha=0.55, zorder=8, solid_capstyle='round')
        ax.plot(mx, my, color=MARS, lw=5, alpha=0.55, zorder=8, solid_capstyle='round')

    # --- lignes de visée fantômes (tous les 0,06 an) et ligne courante
    ghosts = [RETRO_T0 + 0.06 * i for i in range(8)]

    def ray(tt, alpha, lw, col=INK):
        st = retro_state(tt)
        x0, y0 = scr(rE, st['thE'])
        x1, y1 = scr(rM, st['thM'])
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        sext = (L['ray_end'] - y1) / uy if uy > 0.2 else 200
        x2, y2 = x1 + ux * sext, y1 + uy * sext
        ax.plot([x0, x1], [y0, y1], color=col, lw=lw, alpha=alpha, zorder=9, solid_capstyle='round')
        nseg = 24
        px = np.linspace(x1, x2, nseg + 1)
        py = np.linspace(y1, y2, nseg + 1)
        segs = [[(px[i], py[i]), (px[i + 1], py[i + 1])] for i in range(nseg)]
        al = alpha * np.linspace(1, 0, nseg) ** 1.2
        cols = [to_rgba(col, a) for a in al]
        ax.add_collection(LineCollection(segs, colors=cols, linewidths=lw, zorder=9, capstyle='round'))

    for g in ghosts:
        if g <= t + 1e-6 and f >= RETRO_IN:
            ray(g, 0.20, 1.8)
    if f >= RETRO_IN - 10:
        ray(t, 0.85 * ramp(f, RETRO_IN - 10, RETRO_IN), 3.2)

    # --- corps
    ax.add_patch(Circle((xE, yE), 15 * k, facecolor=EARTH, edgecolor=INK, lw=2, alpha=a_bod, zorder=12))
    ax.add_patch(Circle((xM, yM), 13 * k, facecolor=MARS, edgecolor=INK, lw=2, alpha=a_bod, zorder=12))
    # étiquettes des corps : côté extérieur de l'orbite de la Terre, côté intérieur pour Mars ? on les met à gauche/droite
    # étiquettes du côté opposé au mouvement (les flèches de vitesse partent vers la droite près de l'opposition)
    fr.text(xE - 24, yE - 20, 'Terre', 32, 'sansb', EARTH, a_lbl, ha='right', halo=BG)
    fr.text(xM - 24, yM + 12, 'Mars', 32, 'sansb', MARS_INK, a_lbl, ha='right', halo=BG)

    # --- « La Terre dépasse Mars » : flèches de vitesse (longueurs proportionnelles aux vitesses), avant l'opposition
    a_ov = ramp(t, RETRO_T_OPP - 0.05, RETRO_T_OPP - 0.02) if f >= RETRO_IN else 0.0
    if a_ov > 0:
        vE, vM = 2 * np.pi * 1.0 / 1.0, 2 * np.pi * MARS_A / MARS_P   # ua/an
        for (x, y, thb, v, col) in ((xE, yE, s['thE'], vE, EARTH), (xM, yM, s['thM'], vM, MARS_INK)):
            a = thb + rot + np.pi / 2
            ln = 15 * v * k
            arrow(fr, x + 20 * k * math.cos(a), y - 20 * k * math.sin(a),
                  x + (20 * k + ln) * math.cos(a), y - (20 * k + ln) * math.sin(a), col, lw=4, alpha=a_ov, head=18 * k,
                  z=13)
        ox, oy, oha = L['overtake']
        fr.text(ox, oy, 'La Terre dépasse Mars', 50 if split else 52, 'display', INK, a_ov, ha=oha, va='center',
                halo=BG, halo_w=8)

    # --- bande « Vue de la Terre » (zodiaque ; même échelle en longitude et en latitude)
    x0s, y0s, x1s, y1s = L['strip']
    if a_strip > 0:
        fr.text(*L['title_strip'], 'VUE DE LA TERRE : MARS SUR LE ZODIAQUE' if not split else 'VUE DE LA TERRE',
                30, 'sansb', BRONZE, a_strip)
        ax.add_patch(FancyBboxPatch((x0s, y0s), x1s - x0s, y1s - y0s, boxstyle='round,pad=0,rounding_size=14',
                                    facecolor=BRASS, edgecolor=RULE_STRONG, lw=2, alpha=a_strip, zorder=20))
        lam_min, lam_max = lam_all.min(), lam_all.max()
        lc = 0.5 * (lam_min + lam_max)
        span = (lam_max - lam_min) + 8.0
        kx = (x1s - x0s) / span
        b_top = beta_all.max()
        y_top = y0s + L['loop_top']

        def sx(l):
            return 0.5 * (x0s + x1s) + (l - lc) * kx

        def sy(b):
            return y_top + (b_top - b) * kx

        clip = FancyBboxPatch((x0s, y0s), x1s - x0s, y1s - y0s, boxstyle='round,pad=0,rounding_size=14',
                              transform=ax.transData, facecolor='none', edgecolor='none')
        ax.add_patch(clip)
        # étoiles de fond (pseudo-aléatoires, fixes)
        rng = np.random.default_rng(7)
        nst = 70 if split else 110
        sl = rng.uniform(lc - span / 2, lc + span / 2, nst)
        sb = rng.uniform(b_top - (y1s - y_top) / kx, b_top + (L['loop_top'] - 60) / kx, nst)
        ss = rng.uniform(0.6, 1.0, nst) ** 3
        sc = ax.scatter(sx(sl), sy(sb), s=(3 + 30 * ss), color=INK, alpha=0.28 * a_strip, zorder=21, lw=0)
        sc.set_clip_path(clip)
        # règle du zodiaque en haut de la bande : graduations (1°, 5°, limite de signe) et noms grecs de la machine
        ybase = y0s + 50
        segs, lws = [], []
        for d in range(int(math.floor(lc - span / 2)), int(math.ceil(lc + span / 2)) + 1):
            x = sx(d)
            if x < x0s + 8 or x > x1s - 8:
                continue
            ln = 50 if d % 30 == 0 else 16 if d % 5 == 0 else 8
            segs.append([(x, ybase), (x, ybase + ln)] if d % 30 else [(x, y0s + 2), (x, ybase + ln)])
            lws.append(3 if d % 30 == 0 else 1.5)
        ax.add_collection(LineCollection(segs, colors=[to_rgba(BRONZE, 0.8 * a_strip)] * len(segs), linewidths=lws,
                                         zorder=22))
        ax.plot([x0s + 8, x1s - 8], [ybase, ybase], color=BRONZE, lw=1.5, alpha=0.8 * a_strip, zorder=22)
        signs = [(270, 'ΑΙΓΟΚΕΡΩΣ', 'Capricorne'), (300, 'ΥΔΡΟΧΟΟΣ', 'Verseau')]
        xb_ = sx(300)       # limite ΑΙΓΟΚΕΡΩΣ | ΥΔΡΟΧΟΟΣ : les noms encadrent le trait
        for gr, frn, xx, hh in (('ΑΙΓΟΚΕΡΩΣ', 'Capricorne', xb_ - 16, 'right'), ('ΥΔΡΟΧΟΟΣ', 'Verseau', xb_ + 16, 'left')):
            fr.rich(xx, y0s + 38, [(gr, 'greek', 32, BRONZE, 0), ('  ' + frn, 'sans', 28, MUTED, 0)]
                    if not split else [(gr, 'greek', 30, BRONZE, 0)], alpha=a_strip, ha=hh, z=23)
        # trajet de Mars jusqu'à t ; la partie rétrograde est surlignée
        m = ts_all <= t + 1e-9
        if m.sum() > 1 and f >= RETRO_IN:
            ax.plot(sx(lam_all[m]), sy(beta_all[m]), color=MARS, lw=5, alpha=0.95, zorder=24, solid_capstyle='round')
            mr = m & (ts_all >= RETRO_ST1) & (ts_all <= RETRO_ST2)
            if mr.sum() > 1:
                ax.plot(sx(lam_all[mr]), sy(beta_all[mr]), color=MARS_INK, lw=7, alpha=0.95, zorder=24.5,
                        solid_capstyle='round')
        for g in ghosts:
            if g <= t + 1e-6 and f >= RETRO_IN:
                j = np.argmin(np.abs(ts_all - g))
                ax.add_patch(Circle((sx(lam_all[j]), sy(beta_all[j])), 5.5, facecolor=INK, alpha=0.5, zorder=25,
                                    lw=0))
        # pointe de flèche au milieu du recul (sens du mouvement)
        tm = 0.5 * (RETRO_ST1 + RETRO_ST2)
        a_ar = ramp(t, tm + 0.01, tm + 0.03) if f >= RETRO_IN else 0
        if a_ar > 0:
            j = np.argmin(np.abs(ts_all - tm))
            x_, y_ = sx(lam_all[j]), sy(beta_all[j])
            x2, y2 = sx(lam_all[j + 6]), sy(beta_all[j + 6])
            ang = math.atan2(y2 - y_, x2 - x_)
            hd = 26
            pts = [(x_ + hd * 0.6 * math.cos(ang), y_ + hd * 0.6 * math.sin(ang)),
                   (x_ - hd * math.cos(ang - 0.5), y_ - hd * math.sin(ang - 0.5)),
                   (x_ - hd * math.cos(ang + 0.5), y_ - hd * math.sin(ang + 0.5))]
            ax.add_patch(Polygon(pts, closed=True, color=MARS_INK, alpha=a_ar, zorder=25.5, lw=0))
        jn = np.argmin(np.abs(ts_all - t))
        mxs, mys = sx(lam_all[jn]), sy(beta_all[jn])
        ax.add_patch(Circle((mxs, mys), 13, facecolor=MARS, edgecolor=INK, lw=2, alpha=a_strip, zorder=26))
        # stations : étiquette sur le côté extérieur de la boucle
        for ts_, sgn in ((RETRO_ST1, 1), (RETRO_ST2, -1)):
            a_st = ramp(t, ts_ - 0.002, ts_ + 0.012) if f >= RETRO_IN else 0
            if a_st > 0:
                j = np.argmin(np.abs(ts_all - ts_))
                xs_, ys_ = sx(lam_all[j]), sy(beta_all[j])
                fr.text(xs_ + sgn * 26, ys_, 'Station', 32, 'sansm', INK, a_st, ha='left' if sgn > 0 else 'right',
                        va='center', z=27, halo=BRASS)
        # message rétrogradation
        a_rt = ramp(t, RETRO_ST1 + 0.01, RETRO_ST1 + 0.04) if f >= RETRO_IN else 0
        if a_rt > 0:
            rx, ry, rha = L['retro_msg']
            fr.rich(rx, ry, [('Mars recule : ', 'display', 50, MARS_INK, 0),
                             ('rétrogradation', 'display', 50, INK, 0)], alpha=a_rt, ha=rha, halo=BG, halo_w=8)
    return fr


# ============================================================================= 2. ÉCLIPSES (plan 6.5)
ECL_N = 250
ECL_EPS = math.radians(21)            # élévation de la caméra au-dessus du plan de l'orbite terrestre
ECL_E0 = (1160.0, 610.0)              # centre de la Terre à l'écran
ECL_A = 360.0                         # rayon dessiné de l'orbite de la Lune (px)
ECL_I = math.radians(15.0)            # inclinaison DESSINÉE (réelle : environ 5°), exagérée pour être visible
ECL_RP = 560.0                        # rayon du disque « plan de l'orbite de la Terre »
R_EARTH, R_MOON = 44.0, 20.0
UMBRA_E = 38.0                        # rayon de l'ombre de la Terre à la distance de la Lune
# phases (images, 0-based) : mise en place | nouvelle lune loin d'un nœud | quelques mois plus tard |
# éclipse de Soleil | vers la pleine lune, éclipse de Lune | aiguille du Dragon (tenue)
E_B, E_C, E_D, E_E, E_F = 34, 80, 102, 146, 184


def ecl_proj(p):
    p = np.asarray(p, float)
    X = ECL_E0[0] + p[..., 0]
    Y = ECL_E0[1] - (p[..., 1] * math.sin(ECL_EPS) + p[..., 2] * math.cos(ECL_EPS))
    return X, Y


def moon_pos(u, Om, a=ECL_A, inc=ECL_I):
    """position 3D de la Lune (x vers l'anti-Soleil, y en profondeur, z vers le nord de l'écliptique) ;
    u = argument de latitude (0 au nœud ascendant), Om = direction du nœud ascendant, sens direct vu du nord"""
    u = np.asarray(u, float)
    N = np.array([math.cos(Om), math.sin(Om), 0.0])
    zN = np.array([-math.sin(Om), math.cos(Om), 0.0])      # z × N
    Z = np.array([0.0, 0.0, 1.0])
    v = math.cos(inc) * zN + math.sin(inc) * Z
    return a * (np.cos(u)[..., None] * N + np.sin(u)[..., None] * v)


def ecl_timeline(f):
    """(Omega, u, visibilité de la Lune) à l'image f (0-based)"""
    if f < E_C:        # nœuds devant et derrière la Terre : la nouvelle lune passe au-dessus du Soleil
        Om = math.radians(90)
        u = math.radians(20 + 70 * ease((f - E_B) / 32.0)) if f >= E_B else math.radians(20)
        vis = ramp(f, 12, 26) * (1 - ramp(f, E_C - 2, E_C + 8))
    elif f < E_D:      # quelques mois plus tard : vue depuis la Terre, la ligne des nœuds a tourné par rapport au Soleil
        Om = math.radians(90 - 90 * ease((f - E_C) / (E_D - E_C - 2.0)))
        u = math.radians(140)
        vis = 0.0
    elif f < E_E:      # nouvelle lune sur un nœud
        Om = 0.0
        u = math.radians(140 + 40 * ease((f - E_D) / 24.0))
        vis = ramp(f, E_D, E_D + 10)
    else:              # demi-tour jusqu'à la pleine lune, sur l'autre nœud
        Om = 0.0
        u = math.radians(180 + 180 * ease((f - E_E) / (E_F - E_E - 2.0)))
        vis = 1.0
    return Om, u, vis


def _runs(mask):
    """plages contiguës [i0, i1] où mask est vrai"""
    out, i0 = [], None
    for i, m in enumerate(mask):
        if m and i0 is None:
            i0 = i
        if not m and i0 is not None:
            out.append((i0, i))
            i0 = None
    if i0 is not None:
        out.append((i0, len(mask) - 1))
    return out


def eclipse_frame(f):
    fr = Frame()
    ax = fr.ax
    Om, u, vis = ecl_timeline(f)
    ex, ey = ECL_E0
    a_in = ramp(f, 0, 14)
    a_orbit = ramp(f, 4, 26)
    a_nodes = ramp(f, 18, 30)

    # --- Soleil (hors champ à gauche) et sa lumière
    sx_, sy_ = 30.0, ey
    fr.glow(sx_, sy_, 330, SUN, alpha=0.55 * a_in, z=1)
    ax.add_patch(Circle((sx_, sy_), 150, facecolor=SUN, edgecolor=GOLD, lw=3, alpha=a_in, zorder=2))
    fr.text(95, ey + 205, 'Soleil', 36, 'sansm', BRONZE, a_in, ha='center')
    for dy in (-95, 0, 95):
        arrow(fr, 215, ey + dy, 355, ey + dy, GOLD, lw=3, alpha=0.7 * a_in, head=16, z=3)

    # --- plan de l'orbite de la Terre : moitié arrière sous la Terre, moitié avant par-dessus (translucide)
    pa = 0.55 * a_in
    ell_h = 2 * ECL_RP * math.sin(ECL_EPS)
    th = np.linspace(0, np.pi, 200)
    top = np.column_stack([ex + ECL_RP * np.cos(th), ey - 0.5 * ell_h * np.sin(th)])
    bot = np.column_stack([ex + ECL_RP * np.cos(th), ey + 0.5 * ell_h * np.sin(th)])
    ax.add_patch(Polygon(top, closed=True, facecolor='#E6D6B6', edgecolor='none', alpha=pa, zorder=4))
    ax.add_patch(Polygon(bot, closed=True, facecolor='#E6D6B6', edgecolor='none', alpha=pa, zorder=14))
    ax.add_patch(Ellipse((ex, ey), 2 * ECL_RP, ell_h, facecolor='none', edgecolor=RULE_STRONG, lw=2, alpha=a_in,
                         zorder=14))
    fr.text(ex + ECL_RP - 10, ey + 0.5 * ell_h + 50, 'plan de l\'orbite de la Terre', 30, 'sans', MUTED, a_in,
            ha='right', z=30)

    # --- ombre de la Terre (vers la droite, à l'opposé du Soleil)
    a_sh = ramp(f, 8, 26)
    if a_sh > 0:
        x_end = W + 10
        r_end = R_EARTH - (R_EARTH - UMBRA_E) * (x_end - ex) / ECL_A
        poly = [(ex, ey - R_EARTH), (x_end, ey - r_end), (x_end, ey + r_end), (ex, ey + R_EARTH)]
        cone = Polygon(poly, closed=True, facecolor='none', edgecolor='none')
        ax.add_patch(cone)
        fr.img(hgradient([(0, to_rgba(INK, 0.42)), (1, to_rgba(INK, 0.16))]), ex, ey - R_EARTH, x_end,
               ey + R_EARTH, z=15, alpha=a_sh, clip=cone)
        fr.text(1890, ey + R_EARTH + 40, 'ombre de la Terre', 30, 'sansm', INK, a_sh, ha='right', z=31, halo=BG,
                halo_w=6)

    # --- orbite de la Lune : sous le plan (tirets, voilée par le plan), au-dessus (trait plein)
    uu = np.linspace(0, 2 * np.pi, 721)
    P = moon_pos(uu, Om)
    X, Y = ecl_proj(P)
    draw_n = int(720 * a_orbit)
    if draw_n > 2:
        below = P[:draw_n + 1, 2] < 0
        for i0, i1 in _runs(below):
            ax.plot(X[i0:i1 + 1], Y[i0:i1 + 1], color=INK, lw=2.4, alpha=0.6, ls=(0, (7, 6)), zorder=3.5)
        for i0, i1 in _runs(~below):
            ax.plot(X[i0:i1 + 1], Y[i0:i1 + 1], color=INK, lw=3, alpha=0.9, zorder=16, solid_capstyle='round')
    a_orb_lbl = ramp(f, 20, 34) * (1 - ramp(f, E_C, E_C + 10))
    if a_orb_lbl > 0:
        fr.text(1250, 262, 'orbite de la Lune,\ninclinée d\'environ 5°\n(exagéré ici)', 32, 'sansm', INK,
                a_orb_lbl, ha='left', va='top', z=30, halo=BG, lh=1.2)
        j = np.argmin(np.abs(uu - math.radians(35)))
        ax.plot([1240, X[j] + 6], [300, Y[j] - 6], color=INK, lw=1.5, alpha=0.6 * a_orb_lbl, zorder=30)

    # --- nœuds ; ligne des nœuds qui devient l'aiguille du Dragon
    n1 = moon_pos(np.array([0.0]), Om)[0]          # nœud ascendant (tête de l'aiguille, convention du modèle)
    n2 = moon_pos(np.array([math.pi]), Om)[0]
    (x1, y1), (x2, y2) = ecl_proj(n1), ecl_proj(n2)
    a_dragon = ramp(f, E_F - 4, E_F + 10)
    line_col = mix(INK, BRONZE, a_dragon)
    ax.plot([x1, x2], [y1, y2], color=line_col, lw=2 + 6 * a_dragon, alpha=(0.55 + 0.4 * a_dragon) * a_nodes,
            ls=(0, (6, 6)) if a_dragon < 0.5 else '-', zorder=17, solid_capstyle='round')
    if a_dragon > 0:
        ax.add_patch(Circle((x1, y1), 15 * a_dragon, facecolor=GOLD, edgecolor=BRONZE, lw=2, zorder=18))
        ax.add_patch(Polygon([(x2 - 16, y2), (x2, y2 - 11), (x2 + 16, y2), (x2, y2 + 11)], closed=True,
                             facecolor=GOLD, edgecolor=BRONZE, lw=2, alpha=a_dragon, zorder=18))
        fr.text(ex, 960, 'l\'aiguille du Dragon montre les nœuds (hypothèse)', 46, 'sansm', HYP, a_dragon,
                ha='center', z=40, halo=BG, halo_w=8)
    for (x, y), dx_, ha in (((x1, y1), 22, 'left'), ((x2, y2), -22, 'right')):
        ax.add_patch(Polygon([(x - 11, y), (x, y - 11), (x + 11, y), (x, y + 11)], closed=True, facecolor=PAPER,
                             edgecolor=INK, lw=2.2, alpha=a_nodes, zorder=19))
        fr.text(x + dx_, y + 48, 'nœud', 36, 'sansb', INK, a_nodes, ha=ha, z=31, halo=BG, halo_w=7)

    # --- la Lune et son ombre (autour de la nouvelle lune)
    M = moon_pos(np.array([u]), Om)[0]
    mx, my = ecl_proj(M)
    align_new = clamp01((-M[0] / ECL_A - 0.86) / 0.14)
    a_msh = vis * align_new
    solar = 0.0
    if a_msh > 0.01:
        L_ = (-M[0]) - R_EARTH + 10           # le sommet de l'ombre atteint la surface de la Terre
        poly = [(mx, my - R_MOON), (mx + L_, my), (mx, my + R_MOON)]
        ax.add_patch(Polygon(poly, closed=True, facecolor=INK, edgecolor='none', alpha=0.45 * a_msh, zorder=11))
        if abs(my - ey) < R_EARTH - 6:
            solar = a_msh

    # --- Terre (jour à gauche, nuit à droite) ; tache d'ombre de la Lune pendant l'éclipse de Soleil
    ax.add_patch(Circle((ex, ey), R_EARTH, facecolor=EARTH_NIGHT, edgecolor='none', alpha=a_in, zorder=20))
    ax.add_patch(Wedge((ex, ey), R_EARTH, 90, 270, facecolor=EARTH, edgecolor='none', alpha=a_in, zorder=20.5))
    ax.add_patch(Circle((ex, ey), R_EARTH, facecolor='none', edgecolor=INK, lw=2.5, alpha=a_in, zorder=21))
    if solar > 0:
        ax.add_patch(Ellipse((ex - R_EARTH + 9, ey), 13, 22, facecolor='#111111', alpha=0.85 * solar, zorder=22))
    fr.text(ex - 6, ey + R_EARTH + 44, 'Terre', 36, 'sansb', EARTH, a_in, ha='center', z=31, halo=BG, halo_w=7)

    # --- Lune : phase vue de côté (moitié éclairée vers le Soleil) ; rousse et sombre dans l'ombre de la Terre
    in_umbra = 0.0
    if M[0] > 0:
        r_ax = math.hypot(M[1], M[2])
        r_u = R_EARTH - (R_EARTH - UMBRA_E) * M[0] / ECL_A
        in_umbra = clamp01((r_u + R_MOON - r_ax) / (2 * R_MOON))
    moon_day = mix(MOON, '#8C4A2A', in_umbra)
    moon_night = mix('#6F7380', '#5A2E1B', in_umbra)
    zmoon = 13 if M[2] < -6 else 23          # sous le plan : voilée par lui ; au nœud : devant tout
    if vis > 0.01:
        if in_umbra > 0:
            fr.glow(mx, my, 70, '#B5652F', alpha=0.45 * in_umbra * vis, z=zmoon - 0.5)
        ax.add_patch(Circle((mx, my), R_MOON, facecolor=moon_night, edgecolor='none', alpha=vis, zorder=zmoon))
        ax.add_patch(Wedge((mx, my), R_MOON, 90, 270, facecolor=moon_day, edgecolor='none', alpha=vis,
                           zorder=zmoon + 0.1))
        ax.add_patch(Circle((mx, my), R_MOON, facecolor='none', edgecolor=INK, lw=2, alpha=vis, zorder=zmoon + 0.2))
        fr.text(mx, my - R_MOON - 16, 'Lune', 34, 'sansb', INK, vis * ramp(f, 18, 30), ha='center', z=41, halo=BG,
                halo_w=7)

    # --- titres et sous-titres par phase (fondus enchaînés)
    def head(a, runs, sub):
        if a <= 0.003:
            return
        fr.rich(W / 2, 108, runs, alpha=a, ha='center', z=45)
        fr.text(W / 2, 170, sub, 36, 'sans', MUTED, a, ha='center', z=45)

    D = 'display'
    head(ramp(f, E_B + 6, E_B + 16) * (1 - ramp(f, E_C - 4, E_C + 2)),
         [('Nouvelle lune loin d\'un nœud : pas d\'éclipse', D, 62, INK, 0)],
         'l\'ombre de la Lune passe au-dessus de la Terre')
    head(ramp(f, E_C + 4, E_C + 10) * (1 - ramp(f, E_D - 2, E_D + 3)),
         [('Quelques mois plus tard…', D, 62, INK, 0)], 'un nœud se trouve maintenant face au Soleil')
    head(ramp(f, E_D + 12, E_D + 22) * (1 - ramp(f, E_E + 4, E_E + 10)),
         [('Nouvelle lune sur un nœud : ', D, 62, INK, 0), ('éclipse de Soleil', D, 62, BRONZE, 0)],
         'l\'ombre de la Lune touche la Terre')
    head(ramp(f, E_F - 10, E_F),
         [('Pleine lune sur un nœud : ', D, 62, INK, 0), ('éclipse de Lune', D, 62, '#8C4A2A', 0)],
         'la Lune passe dans l\'ombre de la Terre et s\'assombrit')
    return fr


# ============================================================================= 3. PLÉIADES (plans 7.3 et 7.4)
# neuf étoiles les plus brillantes (J2000) : (nom, AD en heures, déclinaison en degrés, magnitude V)
PLEIADES = [
    ('Alcyone', 3 + 47 / 60 + 29.08 / 3600, 24 + 6 / 60 + 18.5 / 3600, 2.87),
    ('Atlas', 3 + 49 / 60 + 9.74 / 3600, 24 + 3 / 60 + 12.3 / 3600, 3.62),
    ('Électre', 3 + 44 / 60 + 52.54 / 3600, 24 + 6 / 60 + 48.0 / 3600, 3.70),
    ('Maïa', 3 + 45 / 60 + 49.61 / 3600, 24 + 22 / 60 + 3.9 / 3600, 3.87),
    ('Mérope', 3 + 46 / 60 + 19.57 / 3600, 23 + 56 / 60 + 54.1 / 3600, 4.18),
    ('Taygète', 3 + 45 / 60 + 12.50 / 3600, 24 + 28 / 60 + 2.2 / 3600, 4.30),
    ('Pléioné', 3 + 49 / 60 + 11.22 / 3600, 24 + 8 / 60 + 12.2 / 3600, 5.05),
    ('Célaéno', 3 + 44 / 60 + 48.22 / 3600, 24 + 17 / 60 + 22.1 / 3600, 5.45),
    ('Astérope', 3 + 45 / 60 + 54.48 / 3600, 24 + 33 / 60 + 16.2 / 3600, 5.76),
]
LAT = math.radians(36.0)
PLE_SCALE = 175.0          # px par degré (amas agrandi par rapport au paysage)
PANEL = (60, 40, 1860, 690)
HORIZON = 540
# bande de l'année
BAND_X0, BAND_X1 = 170, 1750
BAND_Y0, BAND_Y1 = 850, 900
MONTHS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
MONTH_START = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]


def doy(month, day):
    return MONTH_START[month - 1] + day - 1


def bx(d):
    return BAND_X0 + (BAND_X1 - BAND_X0) * d / 365.0


def pleiades_offsets(setting=False):
    """décalages écran (px) des étoiles autour d'Alcyone, orientés comme au lever (est) ou au coucher (ouest)"""
    ra0 = math.radians(15 * PLEIADES[0][1])
    de0 = math.radians(PLEIADES[0][2])
    cosq = math.sin(LAT) / math.cos(de0)
    q = math.acos(cosq)                               # angle parallactique à l'horizon (≈ 50°)
    if not setting:     # face à l'est : nord en haut à gauche, trajectoire vers le haut à droite
        north = np.array([-math.sin(q), -math.cos(q)])
        east = np.array([-math.cos(q), math.sin(q)])
        path = np.array([math.cos(q), -math.sin(q)])
    else:               # face à l'ouest : nord en haut à droite, trajectoire vers le bas à droite
        north = np.array([math.sin(q), -math.cos(q)])
        east = np.array([-math.cos(q), -math.sin(q)])
        path = np.array([math.cos(q), math.sin(q)])
    out = []
    for name, ra, de, mag in PLEIADES:
        xi = math.degrees((math.radians(15 * ra) - ra0) * math.cos(de0))
        eta = de - PLEIADES[0][2]
        off = PLE_SCALE * (xi * east + eta * north)
        out.append((name, off, mag))
    return out, path


def draw_pleiades(fr, cx, cy, setting, alpha, clip, horizon=HORIZON, z=12):
    offs, _ = pleiades_offsets(setting)
    xs, ys, ss, al = [], [], [], []
    for name, off, mag in offs:
        x, y = cx + off[0], cy + off[1]
        ext = clamp01((horizon - 3 - y) / 34.0) ** 1.2          # extinction près de l'horizon
        a = alpha * ext
        if a <= 0.01:
            continue
        r = 9.5 * 10 ** (-0.17 * (mag - 2.87))
        fr.glow(x, y, r * 6.5, '#DDE8FF', alpha=0.6 * a, z=z, power=2.4, clip=clip)
        xs.append(x); ys.append(y); ss.append(r); al.append(a)
    for x, y, r, a in zip(xs, ys, ss, al):
        c = Circle((x, y), r, facecolor='#F7FAFF', edgecolor='none', alpha=a, zorder=z + 0.5)
        fr.ax.add_patch(c)
        c.set_clip_path(clip)


def panel_clip(fr):
    x0, y0, x1, y1 = PANEL
    p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle='round,pad=0,rounding_size=26', facecolor='none',
                       edgecolor='none', transform=fr.ax.transData)
    fr.ax.add_patch(p)
    return p


def panel_frame(fr, alpha):
    x0, y0, x1, y1 = PANEL
    fr.ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle='round,pad=0,rounding_size=26',
                                   facecolor='none', edgecolor=BRONZE, lw=3, alpha=alpha, zorder=60))


def sea(fr, clip, f, grey=False, alpha=1.0, glint_x=None):
    """mer en perspective : calme (traits longs, reflet de l'aube) ou grise et ventée (vagues courtes, moutons)"""
    x0, y0, x1, y1 = PANEL
    if grey:
        grad = vgradient([(0, '#646C75'), (0.25, '#4E565F'), (1, '#2F353C')])
    else:
        grad = vgradient([(0, '#5A6371'), (0.3, '#3E4957'), (1, '#27303B')])
    fr.img(grad, x0, HORIZON, x1, y1, z=20, alpha=alpha, clip=clip)
    ax = fr.ax
    rng = np.random.default_rng(3)
    rows = 11 if grey else 12
    segs, cols, lws = [], [], []
    foam = []
    for i in range(rows):
        v = (i + 1) / rows
        y = HORIZON + (y1 - HORIZON) * v ** 1.7 + 4
        if grey:
            amp, wl, nseg = 2 + 11 * v ** 1.4, 30 + 120 * v, int(9 + 9 * (1 - v))
            drift = f * 3.2 * (0.35 + v)
        else:
            amp, wl, nseg = 0.6 + 2.2 * v, 110 + 260 * v, int(5 + 5 * (1 - v))
            drift = f * 0.8 * (0.3 + v)
        phase = rng.uniform(0, 1000)
        for k in range(nseg):
            xc = (phase + k * (x1 - x0) / nseg + drift) % (x1 - x0 + 300) + x0 - 150
            ln = wl * rng.uniform(0.55, 1.15)
            xx = np.linspace(xc - ln / 2, xc + ln / 2, 14)
            yy = y - amp * np.sin(np.linspace(0, np.pi, 14)) + rng.uniform(-3, 3) * v
            segs.append(np.column_stack([xx, yy]))
            base = '#C3CCD4' if grey else '#8C9CAC'
            cols.append(to_rgba(base, alpha * ((0.22 + 0.42 * v) if grey else (0.18 + 0.30 * v))))
            lws.append((1.1 + 2.0 * v) if grey else (0.9 + 1.4 * v))
            if grey and rng.uniform() < 0.45:          # moutons d'écume qui naissent et s'effacent
                flick = math.sin(f * 0.22 + phase * 0.37 + k * 1.7)
                if flick > 0.2:
                    foam.append((xc + ln * rng.uniform(-0.1, 0.25), y - amp, 10 + 26 * v, 3 + 6 * v,
                                 alpha * min(1.0, (flick - 0.2) * 1.8) * (0.55 + 0.4 * v)))
    lc = LineCollection(segs, colors=cols, linewidths=lws, zorder=21, capstyle='round')
    ax.add_collection(lc)
    lc.set_clip_path(clip)
    for (x, y, w_, h_, a_) in foam:
        e = Ellipse((x, y), w_, h_, facecolor='#F2F4F6', alpha=a_, zorder=22, lw=0)
        ax.add_patch(e)
        e.set_clip_path(clip)
    if glint_x is not None and not grey:               # reflet de l'aube : courts traits clairs sous la lueur
        g_segs, g_cols = [], []
        for i in range(22):
            v = (i + 1) / 22
            y = HORIZON + (y1 - HORIZON) * v ** 1.6 + 3
            w_ = 30 + 120 * v * rng.uniform(0.5, 1.0)
            xc = glint_x + rng.uniform(-40, 40) * v + 6 * math.sin(f * 0.2 + i)
            g_segs.append([(xc - w_ / 2, y), (xc + w_ / 2, y)])
            g_cols.append(to_rgba('#F4CF98', alpha * (0.55 - 0.35 * v)))
        gl = LineCollection(g_segs, colors=g_cols, linewidths=2.2, zorder=22, capstyle='round')
        ax.add_collection(gl)
        gl.set_clip_path(clip)
    ax.plot([x0, x1], [HORIZON, HORIZON], color='#1F2630', lw=2, alpha=0.6 * alpha, zorder=23)[0].set_clip_path(clip)


def season_band(fr, f, fills, labels_alpha=1.0, inbar=False):
    """bande de l'année. fills = liste de (jour début, jour fin, couleur, progression 0..1, hachures ?)"""
    ax = fr.ax
    a = labels_alpha
    ax.add_patch(FancyBboxPatch((BAND_X0, BAND_Y0), BAND_X1 - BAND_X0, BAND_Y1 - BAND_Y0,
                                boxstyle='round,pad=0,rounding_size=10', facecolor=PAPER, edgecolor=RULE_STRONG, lw=2,
                                alpha=a, zorder=30))
    for d0, d1, col, prog, lbl in fills:
        if prog <= 0:
            continue
        dd = d0 + (d1 - d0) * prog
        ax.add_patch(Rectangle((bx(d0), BAND_Y0 + 3), bx(dd) - bx(d0), BAND_Y1 - BAND_Y0 - 6, facecolor=col,
                               edgecolor='none', alpha=0.92 * a, zorder=31))
        if inbar and lbl and (d1 - d0) * prog > 0.8 * (d1 - d0):
            fr.text(0.5 * (bx(d0) + bx(d1)), 0.5 * (BAND_Y0 + BAND_Y1) + 1, lbl, 28, 'sansb', PAPER,
                    a * ramp(prog, 0.8, 1.0), ha='center', va='center', z=33)
    # mois
    segs = []
    for m in range(13):
        x = bx(MONTH_START[m])
        segs.append([(x, BAND_Y0), (x, BAND_Y1 + 10)])
    ax.add_collection(LineCollection(segs, colors=[to_rgba(RULE_STRONG, a)], linewidths=1.5, zorder=32))
    for m in range(12):
        fr.text(0.5 * (bx(MONTH_START[m]) + bx(MONTH_START[m + 1])), BAND_Y1 + 36, MONTHS[m], 28, 'sans', MUTED, a,
                ha='center', z=33)


def date_mark(fr, d, text, alpha, color=INK, below=True, ha='center', star=True, dx=0):
    if alpha <= 0.003:
        return
    x = bx(d)
    y = BAND_Y1 + 58 if below else BAND_Y0 - 16
    if star:
        fr.ax.add_patch(Polygon(star4(x, BAND_Y1 + 62, 14), closed=True, facecolor=GOLD, edgecolor=BRONZE, lw=1.5,
                                alpha=alpha, zorder=34))
        fr.ax.plot([x, x], [BAND_Y0 - 4, BAND_Y1 + 48], color=BRONZE, lw=2, alpha=alpha, zorder=34)
    if text:
        fr.text(x + dx, BAND_Y1 + 118 if below else y, text, 30, 'sansm', color, alpha, ha=ha, z=34)


def sky(fr, clip, stops, alpha=1.0):
    x0, y0, x1, y1 = PANEL
    fr.img(vgradient(stops), x0, y0, x1, HORIZON + 2, z=2, alpha=alpha, clip=clip)


# ---- 7.3 : lever héliaque en mai (est), la mer s'ouvre (Végèce)
PL_N = 150


def pleiades_lever_frame(f):
    fr = Frame()
    ax = fr.ax
    a_in = ramp(f, 0, 18)
    clip = panel_clip(fr)
    dawn = ramp(f, 0, PL_N - 10)
    top = mix('#1B2340', '#2E3B64', dawn)
    mid = mix('#394465', '#6F7AA0', dawn)
    low = mix('#8E7A80', '#E4B58C', dawn)
    hor = mix('#C08D6E', '#F3C98E', dawn)
    sky(fr, clip, [(0, top), (0.45, mid), (0.82, low), (1, hor)], alpha=a_in)
    gx = 640
    fr.glow(gx, HORIZON + 30, 520, '#F6C98A', alpha=(0.35 + 0.5 * dawn) * a_in, z=3, power=1.6, clip=clip)
    # Pléiades : montent le long d'une trajectoire à ~50° de l'horizon
    offs, path = pleiades_offsets(False)
    u_ = clamp01(f / 110.0)
    s = 0.6 * u_ + 0.4 * (1 - (1 - u_) ** 2)                   # mouvement diurne presque uniforme, arrêt doux
    d0, d1 = -80.0, 230.0                                       # distance le long de la trajectoire (px)
    dist = d0 + (d1 - d0) * s
    cx = 560 + path[0] * dist
    cy = HORIZON + 40 + path[1] * dist
    star_a = a_in * (1 - 0.35 * ramp(f, 100, PL_N))            # le jour pâlit les étoiles
    draw_pleiades(fr, cx, cy, False, star_a, clip)
    a_lbl = ramp(f, 40, 56)
    if a_lbl > 0:
        lx, ly = cx + 150, cy - 70
        fr.text(lx, ly, 'Pléiades', 40, 'sansb', PAPER, a_lbl, ha='left', z=40)
        ax.plot([cx + 60, lx - 8], [cy - 40, ly - 12], color=PAPER, lw=1.8, alpha=0.8 * a_lbl, zorder=40)
    sea(fr, clip, f, grey=False, alpha=a_in, glint_x=gx)
    fr.glow(gx, HORIZON + 20, 260, '#F6C98A', alpha=0.22 * dawn * a_in, z=24, power=2, clip=clip)
    fr.text(gx, HORIZON + 50, 'EST', 30, 'sansb', PAPER, 0.85 * a_in, ha='center', z=40)
    panel_frame(fr, a_in)
    # titre sur le ciel
    a_t = ramp(f, 12, 28)
    fr.text(110, 130, 'Aube de mai : les Pléiades se lèvent', 58, 'display', PAPER, a_t, z=45)
    fr.text(110, 196, 'à l\'est, avant le Soleil', 58, 'display', PAPER, a_t, z=45)
    # bande de saison
    a_b = ramp(f, 30, 48)
    fr.rich(BAND_X0, 762, [('Saison de navigation selon Végèce ', 'sansb', 36, INK, 0),
                           ('(IV', 'sans', 36, MUTED, 0), ('e', 'sans', 22, MUTED, -14), ('-V', 'sans', 36, MUTED, 0),
                           ('e', 'sans', 22, MUTED, -14), (' s. apr. J.-C.)', 'sans', 36, MUTED, 0)], alpha=a_b)
    d_open, d_close = doy(5, 27), doy(9, 14)
    prog = ease((f - 62) / 48.0)
    season_band(fr, f, [(d_open, d_close, OK, prog, 'mer sûre')], labels_alpha=a_b)
    date_mark(fr, d_open, 'lever des Pléiades', ramp(f, 52, 64), ha='center')
    a_s = ramp(f, 66, 80)
    fr.text(0.5 * (bx(d_open) + bx(d_close)), BAND_Y0 - 20, 'Mer sûre : 27 mai–14 sept.', 38, 'sansb', OK, a_s,
            ha='center', z=36)
    # Pachon : le mois égyptien qui précède l'ouverture (« Pachone decurso »)
    a_p = ramp(f, 84, 98)
    if a_p > 0:
        xa, xb = bx(doy(4, 26)), bx(d_open)
        yb = BAND_Y0 - 12
        ax.plot([xa, xa, xb, xb], [yb + 8, yb, yb, yb + 8], color=BRONZE, lw=2.5, alpha=a_p, zorder=36)
        fr.rich(xa - 12, BAND_Y0 - 20, [('ΠΑΧΩΝ', 'greek', 38, BRONZE, 0), (' : mois cité par Végèce', 'sansm', 34,
                                                                          BRONZE, 0)], alpha=a_p, ha='right')
    fr.rich(BAND_X1, 1062, [('Végèce, ', 'sans', 28, MUTED, 0), ('Epitoma rei militaris', 'sansi', 28, MUTED, 0),
                            (' IV, 39', 'sans', 28, MUTED, 0)], alpha=a_b, ha='right', z=36)
    return fr


# ---- 7.4 : coucher des Pléiades à l'aube en automne (ouest), Hésiode ; la mer se ferme
PC_N = 225


def pleiades_coucher_frame(f):
    fr = Frame()
    ax = fr.ax
    a_in = ramp(f, 0, 18)
    clip = panel_clip(fr)
    # ciel d'ouest à l'aube : ombre de la Terre (bleu sombre) sous la « ceinture de Vénus » rosée
    dawn = ramp(f, 0, PC_N)
    sky(fr, clip, [(0, mix('#343F52', '#46526A', dawn)), (0.55, mix('#5F6A7E', '#7C879A', dawn)),
                   (0.76, mix('#9D8E98', '#C3A3A5', dawn)), (0.88, mix('#5E6879', '#6E788A', dawn)),
                   (1, mix('#48515F', '#56606E', dawn))], alpha=a_in)
    # nuages et traînées de vent
    rng = np.random.default_rng(11)
    for i in range(7):
        x = (rng.uniform(0, 1900) + f * rng.uniform(2.5, 4.5)) % 2200 - 150
        y = rng.uniform(90, 360)
        fr.glow(x, y, rng.uniform(140, 260), '#8A93A0', alpha=0.35 * a_in, z=4, power=1.4, clip=clip)
    for i in range(16):
        x = (rng.uniform(0, 2000) + f * rng.uniform(7, 11)) % 2300 - 200
        y = rng.uniform(80, HORIZON - 40)
        ln = rng.uniform(80, 200)
        l_ = ax.plot([x, x + ln], [y, y + ln * 0.08], color='#D5DBE2', lw=1.6, alpha=0.22 * a_in, zorder=5)[0]
        l_.set_clip_path(clip)
    # Pléiades : descendent vers la droite et plongent dans la mer
    offs, path = pleiades_offsets(True)
    u_ = clamp01((f - 6) / 150.0)
    s = 0.85 * u_ + 0.15 * smooth(u_)                           # mouvement diurne presque uniforme
    d0, d1 = -330.0, 90.0
    dist = d0 + (d1 - d0) * s
    cx = 1210 + path[0] * dist
    cy = HORIZON + path[1] * dist
    draw_pleiades(fr, cx, cy, True, a_in, clip)
    a_lbl = ramp(f, 22, 38) * (1 - ramp(f, 104, 120))          # l'étiquette s'efface quand l'amas plonge
    if a_lbl > 0:
        lx, ly = cx + 170, cy - 60
        fr.text(lx, ly, 'Pléiades', 40, 'sansb', PAPER, a_lbl, ha='left', z=40)
        ax.plot([cx + 70, lx - 8], [cy - 30, ly - 12], color=PAPER, lw=1.8, alpha=0.8 * a_lbl, zorder=40)
    sea(fr, clip, f, grey=True, alpha=a_in)
    fr.text(1210, HORIZON + 50, 'OUEST', 30, 'sansb', PAPER, 0.85 * a_in, ha='center', z=40)
    panel_frame(fr, a_in)
    # Hésiode (trad. Leconte de Lisle, faits.md 5.5), puis la conclusion
    a_q = ramp(f, 14, 32) * (1 - ramp(f, 150, 164))
    fr.text(110, 128, '« … crains le temps où les Plèiades […]', 50, 'quote', PAPER, a_q, z=45)
    fr.text(110, 190, 'tombent dans la noire mer. »', 50, 'quote', PAPER, a_q, z=45)
    fr.rich(112, 246, [('Hésiode, ', 'sans', 30, '#E4E1DA', 0), ('Les Travaux et les Jours', 'sansi', 30, '#E4E1DA', 0),
                       (' (trad. Leconte de Lisle)', 'sans', 30, '#E4E1DA', 0)], alpha=a_q, z=45)
    a_c = ramp(f, 162, 180)
    fr.text(110, 140, 'Pas où aller : quand partir', 66, 'display', PAPER, a_c, z=45)
    fr.text(112, 206, 'Pas un instrument de navigation : un calendrier du ciel', 38, 'sansm', '#EDEAE3', a_c, z=45)
    # bande de saison
    a_b = ramp(f, 0, 16)
    fr.rich(BAND_X0, 762, [('Saison de navigation selon Végèce ', 'sansb', 36, INK, 0),
                           ('(IV', 'sans', 36, MUTED, 0), ('e', 'sans', 22, MUTED, -14), ('-V', 'sans', 36, MUTED, 0),
                           ('e', 'sans', 22, MUTED, -14), (' s. apr. J.-C.)', 'sans', 36, MUTED, 0)], alpha=a_b)
    d_open, d_close, d_shut, d_reopen = doy(5, 27), doy(9, 14), doy(11, 11), doy(3, 10)
    p_unc = ease((f - 58) / 34.0)
    p_shut1 = ease((f - 96) / 22.0)
    p_shut2 = ease((f - 116) / 22.0)
    season_band(fr, f, [(d_open, d_close, OK, 1.0, 'mer sûre'),
                        (d_close, d_shut, RISK, p_unc, 'incertaine'),
                        (d_shut, 365, SHUT, p_shut1, 'fermée'),
                        (0, d_reopen, SHUT, p_shut2, 'fermée')], labels_alpha=a_b, inbar=True)
    date_mark(fr, d_open, 'lever des Pléiades', a_b)
    # coucher des Pléiades : fin oct.–début nov. (Hésiode)
    a_h = ramp(f, 64, 80)
    if a_h > 0:
        xa, xb = bx(doy(10, 20)), bx(doy(11, 10))
        fr.ax.add_patch(Rectangle((xa, BAND_Y0 - 12), xb - xa, 8, facecolor=BRONZE, alpha=0.9 * a_h, zorder=36))
        date_mark(fr, doy(11, 1), 'coucher des Pléiades', a_h)
        fr.text(BAND_X1, BAND_Y0 - 30, 'Fin oct.–début nov. : quitter la mer', 38, 'sansb', BRONZE, a_h, ha='right',
                z=36)
    a_v = ramp(f, 110, 126)
    fr.text(BAND_X0, BAND_Y0 - 30, 'Végèce : mer fermée du 11 nov. au 10 mars', 38, 'sansb', SHUT, a_v, z=36)
    fr.rich(BAND_X1, 1062, [('Végèce, ', 'sans', 28, MUTED, 0), ('Epitoma rei militaris', 'sansi', 28, MUTED, 0),
                            (' IV, 39', 'sans', 28, MUTED, 0)], alpha=a_b, ha='right', z=36)
    return fr


# ============================================================================= orchestration
DIAGRAMS = {
    'retrograde': (RETRO_N, lambda f: retro_frame(f, 'full'), False),
    'retrograde_split': (RETRO_N, lambda f: retro_frame(f, 'split'), True),
    'eclipse': (ECL_N, eclipse_frame, False),
    'pleiades_lever': (PL_N, pleiades_lever_frame, False),
    'pleiades_coucher': (PC_N, pleiades_coucher_frame, False),
}


def _render(job):
    name, f, outdir = job
    n, fn, rgba = DIAGRAMS[name]
    fr = fn(f)
    fr.save(Path(outdir) / f'{f + 1:04d}.png', rgba=rgba)
    return f


def ffmpeg_exe():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def preview(name, outdir):
    exe = ffmpeg_exe()
    if not exe:
        return None
    mp4 = OUT / f'{name}_apercu.mp4'
    cmd = [exe, '-y', '-loglevel', 'error', '-framerate', str(FPS), '-start_number', '1', '-i',
           str(outdir / '%04d.png')]
    if DIAGRAMS[name][2]:   # RGBA : aplatir sur gris sombre pour l'aperçu
        cmd += ['-filter_complex', f'color=c=0x3a3a3a:s={W}x{H}:r={FPS}[bg];[bg][0:v]overlay=shortest=1,format=yuv420p']
    else:
        cmd += ['-pix_fmt', 'yuv420p']
    cmd += ['-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-movflags', '+faststart', str(mp4)]
    subprocess.run(cmd, check=True)
    return mp4


def timing():
    retro = [{'image': f + 1, 'manivelle': round(retro_crank(f), 5)} for f in range(RETRO_N)]
    return {
        'fps': FPS, 'taille': [W, H], 'numerotation': '%04d.png, première image 0001',
        'retrograde': {
            'images': RETRO_N, 'duree_s': RETRO_N / FPS, 'plan': '4.3 (écran partagé)',
            'segments': {'mise_en_place': [1, RETRO_IN], 'balayage_manivelle': [RETRO_IN + 1, RETRO_IN + RETRO_SWEEP],
                         'tenue': [RETRO_IN + RETRO_SWEEP + 1, RETRO_N]},
            'manivelle_debut_fin': [RETRO_T0, RETRO_T1],
            'stations_manivelle': [round(RETRO_ST1, 4), round(RETRO_ST2, 4)],
            'opposition_manivelle': round(RETRO_T_OPP, 4),
            'note': ('Pour le plan 4.3 (4 s), utiliser les images %d-%d et poser AM_Controller["crank"] = colonne '
                     '« manivelle » image par image : le schéma et la machine s\'arrêtent et reculent ensemble.'
                     % (RETRO_IN + 1, RETRO_IN + RETRO_SWEEP)),
            'manivelle_par_image': retro,
        },
        'retrograde_split': {'identique_a': 'retrograde', 'alpha': 'moitié gauche transparente (RGBA)'},
        'eclipse': {
            'images': ECL_N, 'duree_s': ECL_N / FPS, 'plan': '6.5 (plein écran)',
            'segments': {'mise_en_place': [1, E_B], 'nouvelle_lune_loin_du_noeud': [E_B + 1, E_C],
                         'quelques_mois_plus_tard': [E_C + 1, E_D], 'eclipse_de_soleil': [E_D + 1, E_E],
                         'eclipse_de_lune': [E_E + 1, E_F], 'aiguille_du_dragon_tenue': [E_F + 1, ECL_N]},
            'note': ('Le plan 6.5 dure 6,5 s avec un retour sur la machine : la fin (éclipse de Lune + Dragon, '
                     'images %d-%d) suffit si le plan est court.' % (E_E + 1, ECL_N)),
        },
        'pleiades_lever': {'images': PL_N, 'duree_s': PL_N / FPS, 'plan': '7.3 (plein écran, puis retour sur '
                           'l\'anneau égyptien)', 'segments': {'tout_est_lisible_a_partir_de': 100}},
        'pleiades_coucher': {'images': PC_N, 'duree_s': PC_N / FPS, 'plan': '7.4 (incrustation, puis retour sur la '
                             'machine)', 'segments': {'hesiode': [15, 164], 'mer_fermee': [97, PC_N],
                                                      'conclusion': [163, PC_N]}},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('names', nargs='*', default=list(DIAGRAMS))
    ap.add_argument('--frames', help='liste d\'images (1-based) à rendre, pour tester')
    ap.add_argument('--out', help='dossier de sortie (tests)')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--no-preview', action='store_true')
    args = ap.parse_args()
    ensure_fonts()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        n = DIAGRAMS[name][0]
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
        (OUT / 'timing.json').write_text(json.dumps(timing(), ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
