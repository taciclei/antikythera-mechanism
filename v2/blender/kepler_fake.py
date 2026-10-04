"""Anticythère 2.0 — fausse tour de Kepler pour les tests de la phase K2 (sans bpy).

write(dossier, dirty=False) écrit dossier/kepler.json (1 tour, « mars », axe A = (5, 92) comme axe_mars) et
dossier/kepler_tools/{motion.py, frame.py} (API du contrat v2/tools/kepler/CONTRACT.md § 4, lois simples) :
- mars#manivelle (crank, loi L, sur axe_mars#haut) donnée en DEUX formes qui se recouvrent (moyeu + bras : union) ;
- mars#goupille (pin, Ø 1,5, à R = 10 de A) : (A + R·u(L), π/2 − L) ;
- mars#bague (plate_bush, fixe) : bague excentrique centrée en E = A + e·u(0), e = 1 mm, percée en A ;
- mars#bras (slotted_arm) : pivote en E, rainure (jeu 0,02) le long de +x local, θ = direction E → goupille
  (équant de petite excentricité) ; mars#manchon (tube) et mars#prise (gear 46 dents m 0,5, alésage 5,65) solidaires ;
- mars#anneau_T (oldham_disc, loi LT) autour de A, avec un ergot ;
- overrides : orr_mars#prise_axe retirée (remplacée par mars#prise), orr_mars#prise, orr_mars#r0 (bout p) et
  orr_mars#m0p déplacés de (0, +1) pour rester à 23 mm de E ; orr_mars#m0p~z (synth) suit.
dirty=True ajoute deux intrus non liés : mars#intrus_LT (bras de loi LT dans la couche du bras rainuré : touche le
bras et la goupille quand LT ≈ angle du bras) et mars#intrus_tige (bras de loi équant, z 209–211, long de 26 mm :
touche la tringle orr_mars#r0 et les coniques en (28, 93) quand il pointe vers +x).
"""
import json
import math
import os

A, E, R, ECC = (5.0, 92.0), (5.0, 93.0), 10.0, 1.0
L0_MARS, L0_EARTH = -4.55343205, 100.46457166            # degrés à J2000 (table 1 JPL)
RATE_MARS, RATE_EARTH = 2342453 / 1609217280, 589 / 215136  # tours par jour (trains.json : mars_L, Y)

MOTION_PY = '''"""Faux motion.py (test de la phase K2) : pose(part, state) -> (x, y, θ) en repère machine."""
import math

A, E, R = %r, %r, %r


def pose(part, state):
    law = part["motion"]["law"]
    L, LT = float(state["L"]), float(state["LT"])
    px, py = A[0] + R * math.sin(L), A[1] + R * math.cos(L)      # goupille : A + R·u(L)
    if law == "fixed":
        return tuple(part["motion"]["pivot"]) + (0.0,)
    if law == "mars:L":
        return A[0], A[1], math.pi / 2 - L
    if law == "mars:goupille":
        return px, py, math.pi / 2 - L
    if law == "mars:equant":
        return E[0], E[1], math.atan2(py - E[1], px - E[0])
    if law == "mars:LT":
        return A[0], A[1], math.pi / 2 - LT
    raise KeyError(law)
'''

FRAME_PY = '''"""Faux frame.py (test de la phase K2) : longitudes moyennes continues L(j) = L0 + 2π·taux·j."""
import math

L0 = {"mars": math.radians(%r), "earth": math.radians(%r)}
RATE = {"mars": %r, "earth": %r}


def state_from_jours(p, j):
    lt = L0["earth"] + 2 * math.pi * RATE["earth"] * j
    return {"L": L0[p] + 2 * math.pi * RATE[p] * j, "LT": lt}
'''


def circle_pts(r, c=(0.0, 0.0), n=96):
    return [[c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)] for k in range(n)]


def stadium_pts(x0, x1, hw, n=12):
    """Lumière le long de +x, de x0 à x1 (bouts ronds compris), demi-largeur hw (sens trigonométrique)."""
    a = [[x1 - hw + hw * math.cos(t), hw * math.sin(t)] for t in
         [-math.pi / 2 + math.pi * k / n for k in range(n + 1)]]
    b = [[x0 + hw + hw * math.cos(t), hw * math.sin(t)] for t in
         [math.pi / 2 + math.pi * k / n for k in range(n + 1)]]
    return a + b


def hub_bar(r, x_end, hw, n=72):
    """Contour de l'union d'un disque de rayon r (centre 0) et d'une barre [0, x_end] × [−hw, hw]."""
    a0 = math.asin(hw / r)
    arc = [[r * math.cos(t), r * math.sin(t)] for t in [a0 + (2 * math.pi - 2 * a0) * k / n for k in range(n + 1)]]
    return arc + [[x_end, -hw], [x_end, hw]]


def rect(x0, x1, hw):
    return [[x0, -hw], [x1, -hw], [x1, hw], [x0, hw]]


def part(pid, kind, z, law, pv, shapes, links, **extra):
    d = {'id': 'mars#' + pid, 'tower': 'mars', 'kind': kind, 'z': list(z), 'shapes': shapes,
         'motion': {'law': law, 'pivot': list(pv)}, 'links': links, 'label': pid.replace('_', ' ')}
    d.update(extra)
    return d


def poly(outer, holes=()):
    return {'type': 'polygon', 'outer': outer, 'holes': [h for h in holes]}


def spec(dirty=False):
    pin_at = (A[0] + R, A[1])
    ps = [
        part('manivelle', 'crank', (188.0, 190.0), 'mars:L', A,
             [poly(circle_pts(6.5), [circle_pts(4.05)]), poly(rect(5.0, 11.5, 2.0), [circle_pts(0.75, (R, 0.0), 32)])],
             ['axe_mars#haut', 'mars#goupille']),
        part('goupille', 'pin', (188.0, 193.6), 'mars:goupille', pin_at, [{'type': 'circle', 'c': [0, 0], 'r': 0.75}],
             ['mars#manivelle', 'mars#bras']),
        part('bague', 'plate_bush', (190.4, 207.0), 'fixed', E,
             [poly(circle_pts(5.6), [circle_pts(4.05, (0.0, A[1] - E[1]))])],
             ['axe_mars#haut', 'mars#bras', 'mars#manchon', 'mars#prise']),
        part('bras', 'slotted_arm', (190.6, 193.0), 'mars:equant', E,
             [poly(hub_bar(8.0, 14.5, 2.5), [circle_pts(5.65), stadium_pts(7.75, 12.25, 0.77)])],
             ['mars#bague', 'mars#goupille', 'mars#manchon']),
        part('manchon', 'tube', (193.4, 203.6), 'mars:equant', E, [poly(circle_pts(7.0), [circle_pts(5.65)])],
             ['mars#bague', 'mars#bras', 'mars#prise']),
        part('prise', 'gear', (204.0, 207.0), 'mars:equant', E, [poly(circle_pts(12.0), [circle_pts(5.65)])],
             ['mars#bague', 'mars#manchon', 'orr_mars#prise'],
             gear={'teeth': 46, 'm': 0.5, 'mesh_with': ['orr_mars#prise']}),
        part('anneau_T', 'oldham_disc', (195.0, 197.0), 'mars:LT', A,
             [poly(hub_bar(12.0, 13.5, 1.0), [circle_pts(8.6)])], []),
    ]
    if dirty:
        ps.append(part('intrus_LT', 'arm', (191.0, 192.5), 'mars:LT', A, [poly(rect(9.5, 15.5, 1.0))], []))
        ps.append(part('intrus_tige', 'arm', (209.0, 211.0), 'mars:equant', E, [poly(rect(6.0, 26.0, 1.0))], []))
    ov = [{'id': 'orr_mars#prise_axe', 'remove': True, 'replaced_by': 'mars#prise'},
          {'id': 'orr_mars#prise', 'c': [28.0, 93.0]}, {'id': 'orr_mars#r0', 'p': [28.0, 93.0]},
          {'id': 'orr_mars#m0p', 'c': [28.0, 93.0]}]
    return {'meta': {'title': 'fausse tour de Kepler (test K2)', 'dirty': dirty},
            'towers': {'mars': {'parts': ps, 'overrides': ov, 'params': {'R': R, 'e': ECC}}}}


def write(folder, dirty=False):
    """Écrit la spec et le faux paquet ; renvoie (chemin de kepler.json, dossier des outils)."""
    tools = os.path.join(folder, 'kepler_tools')
    os.makedirs(tools, exist_ok=True)
    with open(os.path.join(tools, 'motion.py'), 'w') as f:
        f.write(MOTION_PY % (A, E, R))
    with open(os.path.join(tools, 'frame.py'), 'w') as f:
        f.write(FRAME_PY % (L0_MARS, L0_EARTH, RATE_MARS, RATE_EARTH))
    path = os.path.join(folder, 'kepler.json')
    with open(path, 'w') as f:
        json.dump(spec(dirty), f, indent=1)
    return path, tools
