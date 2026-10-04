#!/usr/bin/env python3
"""Figures de l'étude (SVG autonomes) à partir de spec/architecture.json et de arch_layout.py.

Usage : python3 v2/tools/figures.py  →  study/fig_blocs.svg, fig_faces.svg, fig_couvercle.svg,
fig_etages.svg, fig_coupe.svg. Couleurs : currentColor pour l'encre ; les classes c-* (thème de la page)
ont une couleur de repli en attribut. Aucun <script> ni <style> dans les SVG.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import arch_layout as L  # noqa: E402

COL = {"time": "#2f5d8a", "planet": "#a8641c", "moon": "#5f6f86", "ecl": "#b23a2e", "jup": "#c27a12",
       "sun": "#c9961a", "bus": "#6b5aa6"}
FONT = 'font-family="Inter, Helvetica, Arial, sans-serif"'


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}" '
            f'{FONT} font-size="12" fill="currentColor">\n'
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>\n'
            + "\n".join(body) + "\n</svg>\n")


def box(x, y, w, h, lines, kind=None, bold_first=True, fs=12):
    c = COL.get(kind)
    cls = f' class="c-{kind}"' if kind else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{c or "none"}" fill-opacity="0.10" '
           f'stroke="{c or "currentColor"}"{cls} stroke-width="1.4"/>']
    ty = y + h / 2 - (len(lines) - 1) * (fs + 3) / 2 + fs / 3
    for i, t in enumerate(lines):
        wgt = ' font-weight="600"' if (i == 0 and bold_first) else ""
        out.append(f'<text x="{x + w / 2}" y="{ty + i * (fs + 3):.1f}" text-anchor="middle" font-size="{fs if i == 0 else fs - 1}"'
                   f'{wgt}>{esc(t)}</text>')
    return out


def arrow(x1, y1, x2, y2, label=None, lx=None, ly=None, anchor="middle"):
    out = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="currentColor" stroke-width="1.2" marker-end="url(#ah)"/>']
    if label:
        lx = (x1 + x2) / 2 if lx is None else lx
        ly = (y1 + y2) / 2 - 4 if ly is None else ly
        out.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="10.5" opacity="0.85">{esc(label)}</text>')
    return out


def poly(points, label=None, lx=0, ly=0, anchor="start"):
    pts = " ".join(f"{x},{y}" for x, y in points)
    out = [f'<polyline points="{pts}" fill="none" stroke="currentColor" stroke-width="1.2" marker-end="url(#ah)"/>']
    if label:
        out.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="10.5" opacity="0.85">{esc(label)}</text>')
    return out


def fig_blocs():
    b = []
    b += box(16, 262, 112, 52, ["Manivelle", "1 tour = 6 h"])
    b += box(168, 262, 124, 52, ["Arbre-jour J", "1 tour par jour"], "time")
    b += box(168, 420, 124, 52, ["Année Y", "1 tour par an"], "sun")
    b += arrow(128, 288, 166, 288, "24:96", ly=282)
    b += arrow(230, 314, 230, 418, "3 couples", lx=236, ly=372, anchor="start")
    cx, cw = 360, 268
    calc = [(14, "Calendrier grégorien", "croix de Malte · anneau 366 · cames 4/100/400", "time"),
            (76, "Temps", "sidéral · joint de Hooke · équation du temps", "time"),
            (138, "Boîte de Laplace", "Io · Europe · Ganymède · Callisto", "jup"),
            (200, "Lune : cascade à 5 étages", "+ coulisse d'éclipse sur le porte-nœuds", "moon"),
            (300, "UAK maîtresse de la Terre", "Soleil vrai", "sun"),
            (372, "7 tours planétaires", "train moyen → UAK → module vectoriel", "planet"),
            (460, "Précession", "depuis le train moyen de Neptune", "time"),
            (522, "Périgée, nœuds, Saros", "trains depuis Y", "moon")]
    for y, t1, t2, k in calc:
        b += box(cx, y, cw, 48, [t1, t2], k)
    # J vers les blocs de calcul (un tronc vertical)
    b += [f'<line x1="292" y1="280" x2="318" y2="280" stroke="currentColor" stroke-width="1.2"/>',
          f'<line x1="318" y1="38" x2="318" y2="280" stroke="currentColor" stroke-width="1.2"/>']
    for y in (38, 100, 162, 224):
        b += arrow(318, y, cx - 2, y)
    b += [f'<text x="322" y="252" font-size="10.5" opacity="0.85">goupille,</text>',
          f'<text x="322" y="265" font-size="10.5" opacity="0.85">tringles</text>']
    # Y vers les blocs (bus de l'année)
    b += [f'<line x1="292" y1="446" x2="334" y2="446" stroke="{COL["bus"]}" class="c-bus" stroke-width="2"/>',
          f'<line x1="334" y1="112" x2="334" y2="546" stroke="{COL["bus"]}" class="c-bus" stroke-width="2"/>']
    for y in (324, 396, 546):
        b += arrow(334, y, cx - 2, y)
    b += arrow(334, 112, cx - 2, 112)
    b += [f'<text x="296" y="438" font-size="10.5" class="c-bus" fill="{COL["bus"]}">bus Y</text>']
    b += arrow(cx + cw / 2, 420, cx + cw / 2, 458)
    b += [f'<text x="{cx + cw / 2 + 6}" y="{444}" font-size="10.5" opacity="0.85">Neptune moyen</text>']
    fx, fw = 744, 222
    faces = [(14, 176, "Face avant", "le ciel vu de la Terre",
              ["10 aiguilles sur l'écliptique", "zodiaque tropique", "horloge 24 h, équation du temps",
               "Jupiter et ses lunes"]),
             (214, 150, "Face arrière", "le temps",
              ["calendrier grégorien", "éclipses (γ, magnitude)", "Saros et Exeligmos"]),
             (388, 160, "Couvercle", "vu d'en haut",
              ["orrery des 8 planètes", "tellurion sidéral", "aiguille d'ombre"])]
    bus_x = [662, 686, 710]
    for (y, h, t, sub, items), bx in zip(faces, bus_x):
        b.append(f'<rect x="{fx}" y="{y}" width="{fw}" height="{h}" rx="8" fill="none" stroke="currentColor" stroke-width="1.6"/>')
        b.append(f'<text x="{fx + 12}" y="{y + 22}" font-weight="600" font-size="13">{esc(t)}</text>')
        b.append(f'<text x="{fx + 12}" y="{y + 38}" font-size="11" opacity="0.8">{esc(sub)}</text>')
        for i, it in enumerate(items):
            b.append(f'<text x="{fx + 16}" y="{y + 62 + i * 18}" font-size="11.5">· {esc(it)}</text>')
    # collecteurs : un par face ; chaque bloc s'y branche par un point
    feeds = {38: (0, 1, 0), 100: (1, 0, 1), 162: (1, 0, 0), 224: (1, 1, 1), 324: (1, 1, 1),
             396: (1, 0, 1), 484: (1, 0, 0), 546: (0, 1, 0)}
    tops = {0: 30, 1: 230, 2: 404}
    for k, bx in enumerate(bus_x):
        ys = [y for y, f in feeds.items() if f[k]]
        ylo, yhi = min(ys + [tops[k]]), max(ys + [tops[k]])
        b.append(f'<line x1="{bx}" y1="{ylo}" x2="{bx}" y2="{yhi}" stroke="currentColor" stroke-width="1.4"/>')
        b += arrow(bx, tops[k], fx - 2, tops[k])
    for y, f in feeds.items():
        last = max(bx for bx, on in zip(bus_x, f) if on)
        b.append(f'<line x1="{cx + cw}" y1="{y}" x2="{last}" y2="{y}" stroke="currentColor" stroke-width="1" opacity="0.7"/>')
        for bx, on in zip(bus_x, f):
            if on:
                b.append(f'<circle cx="{bx}" cy="{y}" r="3.2" fill="currentColor"/>')
    for bx, lab in zip(bus_x, ("avant", "arrière", "couvercle")):
        b.append(f'<text x="{bx}" y="{574}" text-anchor="middle" font-size="9.5" transform="rotate(-90 {bx} 574)" '
                 f'opacity="0.85"></text>')
    return svg(980, 590, b, "Circulation du mouvement : la manivelle mène l'arbre-jour J, qui mène l'année Y ; "
               "J et Y alimentent les blocs de calcul (calendrier, temps, Laplace, Lune, UAK, 7 tours, précession) "
               "qui mènent les trois faces.")


def write(name, txt):
    path = os.path.join(V2, "study", name)
    with open(path, "w") as f:
        f.write(txt)
    print("écrit", os.path.relpath(path, V2))


if __name__ == "__main__":
    import figures2
    write("fig_blocs.svg", fig_blocs())
    figures2.main(write)
