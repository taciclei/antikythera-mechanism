"""Anticythère 2.0 — module faces : face arrière, calendrier grégorien et cadran des éclipses.

Lue de dos (contrat § 2 et étude § 3.2) : les pièces tournent avec scale −1 autour de +Z, donc dans le sens
anti-horaire vu de dos (phys +1, horaire vu de face). Graduation de la valeur v : angle de cadran φ = −v pour une
aiguille ; pour un anneau ou un disque lu à un index fixe en haut, la case k est gravée à φ = +k·pas et vient en
haut quand l'anneau a tourné de −k·pas. Les textes sont retournés (rotation de π autour de Y) pour le lecteur de dos.
"""
import math

import numpy as np

import faces_parts as FP
from faces_mesh import MeshBuf, make_text, mat4, radial_bar, ring, text_M, texts_into
from faces_front import MONTHS

D = math.radians
S = -1                       # côté arrière
DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 366 cases, 29 février compris
WEEK = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]  # 0 = dimanche (Meeus)
GAMMA_K = 5.40               # γ ≈ 5,40 · sin F (rayons terrestres)


def _ticks_at(buf, o, phis, r0, r1, w, h=None):
    h0, h1 = h or FP.eng_h(S)
    for phi in phis:
        buf.add(radial_bar(phi, r0, r1, w, w, h0, h1), "engrave", mat4(None, (o[0], o[1], 0.0)))


def _nums_at(buf, o, items, h=None, upright=False):
    hh = FP.text_h(S) if h is None else h
    specs = []
    for s, size, r, phi in items:
        M = text_M(r, phi, hh, back=True, upright=upright)
        M[0, 3] += o[0]
        M[1, 3] += o[1]
        specs.append((s, size, M))
    texts_into(buf, specs, "engrave")


def build_calendar(spec, arch, colls, mats, z):
    coll, c, R = colls["arriere"], spec["c"], spec["R"]
    yrs = np.subtract(arch["blocs"]["annees"]["c"], c)
    wk = np.subtract(arch["blocs"]["semaine"]["c"], c)
    r_in, r0, r1, rb = R - 26.5, R - 25.0, R - 5.0, R - 3.5
    fh0, fh1 = FP.face_h(S)
    out = []
    # --- face fixe : disque intérieur, lunette extérieure et index du haut
    buf = MeshBuf()
    buf.add(ring(0.0, r_in, fh0, fh1), "dial")
    buf.add(ring(rb, R, fh0, fh1), "dial")
    buf.add(radial_bar(0.0, rb + 0.3, R - 0.5, 4.0, 4.0, *FP.span(FP.FACE_T, 2.4, S)), "dial")
    buf.add(FP.arrow_head(0.0, R - 0.5, r1 - 4.0, 4.0, S, 0), "dial")
    FP.circle_line(buf, r_in - 1.0, 0.3, S)
    yr_step = 2 * math.pi / 100
    _ticks_at(buf, yrs, [-y * yr_step for y in range(100)], 18.0, 21.0, 0.15)
    _ticks_at(buf, yrs, [-y * yr_step for y in range(0, 100, 10)], 16.0, 21.0, 0.35)
    _nums_at(buf, yrs, [(f"{y:02d}", 2.0, 13.0, -y * yr_step) for y in range(0, 100, 10)], upright=True)
    face = FP.fixed("AR_calendrier_cadran", buf, coll, mats, c, z, source="cal_anneau", links=["cadran_arriere"])
    out.append(face)
    for nm, body, size, xy in [("titre", "Calendrier grégorien", 4.0, (0.0, 64.0)),
                               ("annees", "années du siècle", 1.8, (yrs[0], yrs[1] + 23.5)),
                               ("semaine", "jour de la semaine", 1.8, (wk[0], wk[1] - 22.5))]:
        out.append(FP.label_at(f"AR_calendrier_txt_{nm}", body, size, coll, mats, face, tuple(xy), S))
    # --- anneau des 366 dates (tourne : index fixe en haut)
    step = 2 * math.pi / 366
    buf = MeshBuf()
    buf.add(ring(r0, r1, fh0, fh1), "ring")
    FP.ticks(buf, [(k + 0.5) * step for k in range(366)], r1 - 9.0, r1 - 0.5, 0.14, S)
    starts = np.cumsum([0] + DAYS[:-1])
    FP.ticks(buf, [(s - 0.5) * step for s in starts], r0 + 0.5, r1 - 0.5, 0.4, S)
    FP.circle_line(buf, r1 - 9.0, 0.25, S)
    nums = []
    for mi, nd in enumerate(DAYS):
        nums += [(str(d), 1.1, r1 - 4.5, (starts[mi] + d - 1) * step) for d in range(1, nd + 1)]
    FP.numbers_into(buf, nums, S)
    ring_ob = buf.to_object("AR_calendrier_anneau", coll, mats, loc=(c[0], c[1], z))
    FP.tag(ring_ob, "ring", key="cal_ring", scale=-1.0, source="cal_anneau", links=["cadran_arriere"],
           cells=366, index="haut")
    out.append(ring_ob)
    for mi, mname in enumerate(MONTHS):
        phi = (starts[mi] + DAYS[mi] / 2 - 0.5) * step
        out.append(FP.label(f"AR_calendrier_txt_mois_{mi:02d}", mname, 2.6, coll, mats, ring_ob, r0 + 5.0, phi, S))
    # --- aiguille des années
    out.append(FP.hand("AR_calendrier_annees", coll, mats, (c[0] + yrs[0], c[1] + yrs[1]), z, S, 0, 1,
                       [(0.0, None, 20.0, 1.2, 0.4), (math.pi, None, 5.0, 1.2, 2.0)], "years", base=FP.FACE_T,
                       source="annees", links=["AR_calendrier_cadran"]))
    out += week_window(coll, mats, (c[0] + wk[0], c[1] + wk[1]), z)
    return out


def week_window(coll, mats, o, z):
    """Disque des 7 jours sous un cache percé d'un guichet en haut."""
    step = 2 * math.pi / 7
    buf = MeshBuf()
    buf.add(ring(0.0, 17.0, *FP.level(0, S)), "light")
    buf.add(ring(0.0, 1.5, *FP.span(FP.FACE_T, FP.START, S)), "steel")
    top = -(FP.START + FP.THICK)
    for k in range(7):
        buf.add(radial_bar((k + 0.5) * step, 6.0, 16.5, 0.3, 0.3, top - FP.ENG, top), "engrave")
    disc = buf.to_object("AR_semaine_disque", coll, mats, loc=(o[0], o[1], z))
    FP.tag(disc, "disc", key="weekday", scale=-1.0, source="semaine", links=["AR_calendrier_cadran"],
           weekday_zero="dimanche")
    out = [disc]
    for k, nom in enumerate(WEEK):
        M = text_M(11.5, k * step, top - 0.03, back=True)
        out.append(make_text(f"AR_semaine_txt_{k}", nom, 1.9, coll, mats["engrave"], M, parent=disc,
                             source="semaine"))
    buf = MeshBuf()
    lv = FP.level(1, S)
    buf.add(ring(6.0, 21.0, *lv, a0=D(24), a1=D(336)), "dial")
    buf.add(ring(0.0, 6.0, *lv), "dial")
    buf.add(ring(19.6, 21.0, *FP.span(FP.FACE_T, FP.START + FP.PITCH + FP.THICK, S)), "dial")
    out.append(FP.fixed("AR_semaine_guichet", buf, coll, mats, o, z, source="semaine",
                        links=["AR_calendrier_cadran"]))
    return out


def build_eclipses(spec, colls, mats, z):
    coll, c, R = colls["arriere"], spec["c"], spec["R"]
    n = 3
    buf = MeshBuf()
    buf.add(ring(FP.hole_for(n), R, *FP.face_h(S)), "dial")
    for d in range(360):
        r0 = R - (6.5 if d % 10 == 0 else 5.0 if d % 5 == 0 else 3.5)
        FP.ticks(buf, [-D(d)], r0, R - 0.8, 0.35 if d % 5 == 0 else 0.15, S)
    FP.circle_line(buf, R - 7.0, 0.3, S)
    FP.numbers_into(buf, [(f"{d}°", 2.2, R - 10.0, -D(d)) for d in range(0, 360, 30)], S)
    face = FP.fixed("AR_eclipses_cadran", buf, coll, mats, c, z, source="lune", links=["cadran_arriere"])
    out = [face, FP.label_at("AR_eclipses_txt_titre", "Éclipses", 4.0, coll, mats, face, (0.0, -80.0), S),
           FP.label_at("AR_eclipses_txt_legende", "Lune près d'un nœud à la syzygie : éclipse", 1.8, coll, mats,
                       face, (0.0, -86.0), S)]
    out += node_disc(coll, mats, c, z, n)
    lk = ["cadran_arriere", "lune", "AR_eclipses_cadran"]
    out.append(FP.hand("AR_eclipses_lune", coll, mats, c, z, S, 1, n,
                       [(0.0, None, 100.0, 1.6, 0.4), (math.pi, None, 14.0, 1.6, 2.6)], "lambda_moon", mat="silver",
                       extras=[(FP.bead(84.0, 0.0, S, 1, rad=3.0), "p_moon")], source="lune", links=lk))
    out.append(FP.hand("AR_eclipses_soleil", coll, mats, c, z, S, 2, n,
                       [(0.0, None, 103.0, 2.0, 0.5), (math.pi, None, 14.0, 2.0, 3.0)], "lambda_sun", mat="gold",
                       extras=[(FP.bead(90.0, 0.0, S, 2, rad=3.5), "gold")], source="lune", links=lk))
    return out


def node_disc(coll, mats, c, z, n, R=72.0):
    """Disque des nœuds (tourne avec Ω) gravé de la ligne des nœuds, de γ et des secteurs d'éclipse."""
    h0, h1 = FP.level(0, S)
    e0, e1 = h0 - FP.ENG, h0
    ri, ro = FP.radii(n)[0]
    disc = [(ring(ro + 1.0, R, h0, h1), "ring"),
            (radial_bar(0.0, 10.0, R - 1.0, 0.5, 0.5, e0, e1), "engrave"),
            (radial_bar(math.pi, 10.0, R - 1.0, 0.5, 0.5, e0, e1), "engrave")]
    specs = []
    for node, sgn in ((0.0, 1), (math.pi, -1)):
        for g in (0.5, 1.0, 1.5):
            F = math.asin(g / GAMMA_K)
            for s in (1, -1):
                phi = -(node + s * F)
                disc.append((radial_bar(phi, R - 16.0, R - 1.0, 0.3, 0.3, e0, e1), "engrave"))
                lab = ("+" if sgn * s > 0 else "−") + f"{g:g}".replace(".", ",")
                specs.append((lab, 1.6, text_M(R - 19.0, phi, h0 - 0.03, back=True)))
        f1, f2 = math.asin(1.0 / GAMMA_K), math.asin(1.55 / GAMMA_K)
        arcs = [((-f1, f1), "red"), ((f1, f2), "gold"), ((-f2, -f1), "gold")]  # centrale / partielle
        for (a, b), key in arcs:
            disc.append((ring(R - 5.0, R - 1.5, e0, e1, a0=-node - b, a1=-node - a), key))
        specs.append(("☊" if sgn > 0 else "☋", 4.0, text_M(R - 30.0, -node, h0 - 0.03, back=True)))
    ob = FP.hand("AR_eclipses_noeuds", coll, mats, c, z, S, 0, n, [], "node", mat="ring", extras=disc,
                 source="node", links=["cadran_arriere", "lune", "AR_eclipses_cadran"],
                 gamma_scale=f"γ ≈ {GAMMA_K} sin F")
    buf = MeshBuf()
    texts_into(buf, specs, "engrave")
    txt = buf.to_object("AR_eclipses_noeuds_gravure", coll, mats, parent=ob)
    FP.tag(txt, "text", source="node", links=[ob.name])
    return [ob, txt]
