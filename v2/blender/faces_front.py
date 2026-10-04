"""Anticythère 2.0 — module faces : cadran principal avant (anneaux J2000 et tropique) et ses 10 aiguilles.

Longitude λ au angle de cadran φ = −λ (0° en haut, croissant dans le sens horaire vu de face). Une aiguille au repos
montre λ = 0 ; motion 'ephem:<clé>', scale −1 : elle tourne de −λ autour de +Z (phys +1, horaire).
"""
import math

import numpy as np

import faces_parts as FP
from faces_common import tag
from faces_mesh import MeshBuf, P, cyl_between, ring, rx, sphere

D = math.radians
# Limites UAI des constellations sur l'écliptique J2000 (approchées, degrés) ; Ophiuchus (247,7–266,3) non nommé.
CONSTELLATIONS = [("Poissons", 351.6, 28.7), ("Bélier", 28.7, 53.4), ("Taureau", 53.4, 90.1),
                  ("Gémeaux", 90.1, 118.0), ("Cancer", 118.0, 138.0), ("Lion", 138.0, 173.9),
                  ("Vierge", 173.9, 218.0), ("Balance", 218.0, 241.0), ("Scorpion", 241.0, 247.7),
                  ("Sagittaire", 266.3, 299.7), ("Capricorne", 299.7, 327.6), ("Verseau", 327.6, 351.6)]
BOUNDS = [351.6, 28.7, 53.4, 90.1, 118.0, 138.0, 173.9, 218.0, 241.0, 247.7, 266.3, 299.7, 327.6]
SIGNS = ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge", "Balance", "Scorpion", "Sagittaire",
         "Capricorne", "Verseau", "Poissons"]
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
          "novembre", "décembre"]
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
YEAR_REF = 2050  # année de gravure des mois (orbites figées en 2050)

# (nom, clé, matériau, rayon de la perle, matériau de la perle, source) du bas (près du cadran) vers le haut.
POINTERS = [("dragon", "node", "steel", None, None, "tube_node"),
            ("neptune", "lambda_geo_neptune", "steel", 98, "p_neptune", "tube_neptune"),
            ("uranus", "lambda_geo_uranus", "steel", 90, "p_uranus", "tube_uranus"),
            ("saturne", "lambda_geo_saturn", "steel", 82, "p_saturn", "tube_saturn"),
            ("jupiter", "lambda_geo_jupiter", "steel", 74, "p_jupiter", "tube_jupiter"),
            ("mars", "lambda_geo_mars", "steel", 66, "p_mars", "tube_mars"),
            ("venus", "lambda_geo_venus", "steel", 58, "p_venus", "tube_venus"),
            ("mercure", "lambda_geo_mercury", "steel", 50, "p_mercury", "tube_mercury"),
            ("lune", "lambda_moon", "silver", None, None, "tube_moon"),
            ("soleil", "lambda_sun", "gold", None, None, "axe_soleil")]
PHASE_R, PHASE_BALL, SUN_R, SUN_BALL = 30.0, 3.0, 112.0, 2.4
PHASE_POST = 0.4
# L'aiguille du Soleil passe au-dessus de la boule de phase (étage relevé, avec 0,25 mm de jeu).
_MOON_K = [p[0] for p in POINTERS].index("lune")
SUN_LEV = (FP.START + _MOON_K * FP.PITCH + FP.THICK + PHASE_POST + 2 * PHASE_BALL + 0.25 - FP.START) / FP.PITCH


def jd0(y, m, d):
    """Jour julien à 0 h (Meeus, calendrier grégorien)."""
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + 2 - a + a // 4 - 1524.5


def sun_trop(y, m, d):
    """Longitude tropique du Soleil (degrés, formule courte de Meeus, ±0,01°) à 0 h TT."""
    n = jd0(y, m, d) - 2451545.0
    L, g = 280.46646 + 0.9856474 * n, D(357.52911 + 0.98560028 * n)
    return (L + 1.914602 * math.sin(g) + 0.019993 * math.sin(2 * g)) % 360.0


def build_main(arch, colls, mats):
    coll, z = colls["avant"], float(arch["z_cadran_avant"])
    spec = arch["faces"]["avant"]["principal"]
    c = spec["c"]
    (_, f0, f1), (_, t0, t1) = spec["anneaux"]
    n = len(POINTERS)
    rad = FP.pile_radii(arch, n)  # pile Ø 18,4 mm d'architecture.json (axe_soleil r 2,0 au centre)
    h0, h1 = FP.face_h(+1)
    out = []
    # --- face fixe : anneau des constellations J2000 et disque central
    buf = MeshBuf()
    buf.add(ring(f0, f1, h0, h1), "dial")
    buf.add(ring(FP.hole_for(n, rad), t0 - 2.0, h0, h1), "enamel")  # disque central : ciel émaillé
    for dd in range(360):
        r0 = f1 - (7.0 if dd % 10 == 0 else 5.5 if dd % 5 == 0 else 3.5)
        FP.ticks(buf, [-D(dd)], r0, f1 - 0.6, 0.3 if dd % 5 else 0.45, +1)
    FP.ticks(buf, [-D(b) for b in BOUNDS], f0 + 0.4, f1 - 7.4, 0.4, +1)
    for r in (f0 + 0.6, f1 - 7.2, f1 - 0.4):
        FP.circle_line(buf, r, 0.3, +1)
    for r in (t0 - 3.0, 40.0):
        FP.circle_line(buf, r, 0.3, +1, key="gold")
    FP.numbers_into(buf, [(str(dd), 1.5, f1 - 8.6, -D(dd)) for dd in range(0, 360, 10)], +1)
    dial = FP.fixed("AV_cadran_principal", buf, coll, mats, c, z, source="cadran_avant", links=["cadran_avant"])
    out.append(dial)
    for i, (name, a, b) in enumerate(CONSTELLATIONS):
        mid = a + ((b - a) % 360.0) / 2
        out.append(FP.label(f"AV_txt_constellation_{i:02d}", name, 2.0 if name == "Scorpion" else 2.6,
                            coll, mats, dial, f0 + 2.6, -D(mid), +1))
    out.append(FP.label_at("AV_txt_titre", "Le ciel vu de la Terre", 4.0, coll, mats, dial, (0.0, -86.0), +1,
                           key="gold"))
    out.append(FP.label_at("AV_txt_sous_titre", "longitudes J2000 · anneau tropique mû par la précession", 2.0,
                           coll, mats, dial, (0.0, -93.0), +1, key="gold"))
    # --- anneau tropique (zodiaque et mois grégoriens), tourne avec la précession
    buf = MeshBuf()
    buf.add(ring(t0, t1, h0, h1), "ring")
    FP.ticks(buf, [-D(30 * i) for i in range(12)], t1 - 8.0, t1 - 0.4, 0.4, +1)
    FP.circle_line(buf, t1 - 8.0, 0.3, +1)
    FP.circle_line(buf, t0 + 0.6, 0.3, +1)
    doy = 0
    for mi, nd in enumerate(MONTH_DAYS):
        for d in range(1, nd + 1):
            lam = sun_trop(YEAR_REF, mi + 1, d)
            if d == 1:
                FP.ticks(buf, [-D(lam)], t0 + 0.6, t1 - 8.0, 0.4, +1)
            else:
                r0 = t1 - (11.5 if d % 5 == 0 else 10.0)
                FP.ticks(buf, [-D(lam)], r0, t1 - 8.0, 0.18, +1)
            doy += 1
    ring_ob = buf.to_object("AV_anneau_tropique", coll, mats, loc=(c[0], c[1], z))
    tag(ring_ob, "ring", key="prec", scale=-1.0, source="prec_avant", links=["cadran_avant"])
    out.append(ring_ob)
    for i, s in enumerate(SIGNS):
        out.append(FP.label(f"AV_txt_signe_{i:02d}", s, 2.8, coll, mats, ring_ob, t1 - 4.0, -D(30 * i + 15), +1))
    for mi, mname in enumerate(MONTHS):
        lam = sun_trop(YEAR_REF, mi + 1, 16)
        out.append(FP.label(f"AV_txt_mois_{mi:02d}", mname, 2.4, coll, mats, ring_ob, t0 + 4.6, -D(lam), +1))
    out += build_pointers(coll, mats, c, z, n, rad)
    return out


def build_pointers(coll, mats, c, z, n, rad=None):
    out = []
    for k, (nom, key, mat, rb, mb, src) in enumerate(POINTERS):
        extras, arms = [], [(0.0, None, 146.0, 2.0, 0.5), (math.pi, None, 18.0, 2.0, 3.2)]
        lev = SUN_LEV if nom == "soleil" else k
        h0, h1 = FP.level(lev, +1)
        if nom == "dragon":
            arms = [(0.0, None, 124.0, 2.4, 1.2), (math.pi, None, 124.0, 2.4, 1.2)]
            extras.append((FP.arrow_head(0.0, 121.0, 131.0, 6.0, +1, k), mat))
            x, y = P(126.0, math.pi)
            v, f = ring(1.4, 2.6, h0, h1, n=24)
            extras.append(((v + np.array([x, y, 0.0]), f), mat))
        elif nom == "soleil":
            arms = [(0.0, None, 146.0, 2.4, 0.6), (math.pi, None, 18.0, 2.4, 3.6)]
            v, f = sphere(SUN_BALL, 24, 12)
            x, y = P(SUN_R, 0.0)
            extras.append(((v + np.array([x, y, (h0 + h1) / 2]), f), "gold"))
        elif nom == "lune":
            x, y = P(PHASE_R, 0.0)
            extras.append((cyl_between((x, y, h1 - 0.1), (x, y, h1 + PHASE_POST), 0.7), mat))
        if rb is not None:
            extras.append((FP.bead(rb, 0.0, +1, k), mb))
        ob = FP.hand(f"AV_aiguille_{nom}", coll, mats, c, z, +1, k, n, arms, key, mat=mat, extras=extras,
                     lev=lev, rad=rad, source=src,
                     links=["cadran_avant", "pile", "axe_soleil", "AV_cadran_principal"])
        out.append(ob)
        if nom == "lune":
            out.append(phase_ball(coll, mats, ob, h1))
    return out


def phase_ball(coll, mats, moon, h1):
    """Boule de phase : moitié sombre (face +Z au repos = nouvelle Lune), moitié claire ; tourne de +élongation
    autour de l'axe de l'aiguille (+Y local) : la partie claire se tourne vers le Soleil."""
    v, f = sphere(PHASE_BALL, 24, 12)
    v = v @ rx(-math.pi / 2).T
    keys = ["dark" if np.mean(v[list(face), 2]) > 0 else "light" for face in f]
    buf = MeshBuf().add((v, f), keys)
    x, y = P(PHASE_R, 0.0)
    ob = buf.to_object("AV_boule_phase", coll, mats, loc=(x, y, h1 + PHASE_POST + PHASE_BALL), parent=moon)
    tag(ob, "phase_ball", key="elong", scale=1.0, axis=(0.0, 1.0, 0.0), source="tube_moon",
        links=[moon.name], axis_frame="parent")
    return ob
