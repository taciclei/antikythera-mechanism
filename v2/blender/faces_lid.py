"""Anticythère 2.0 — module faces : couvercle, système solaire vu d'en haut (orrery) et tellurion.

Repère local du couvercle (u, v, h) : u = +X, v = −Z, h = +Y (vers le haut). Vu d'en haut (lecteur devant la machine),
le sens direct est anti-horaire et correspond à une rotation positive autour de +Y : λ = 0 vers +X, λ = 90° vers −Z.
Les bras tournent de +λ héliocentrique (scale +1, axe +Y, phys −1). Rainures : ellipses (Mercure, Mars) ou cercles
décentrés (autres) avec le Soleil au foyer ; les boules restent au rayon affiché a (le coulisseau radial n'est pas
animé ; `orbit_slot` = [a, e, ϖ] le permettrait).
"""
import json
import math

import numpy as np

import faces_parts as FP
from faces_common import AL, V2, tag
from faces_mesh import MeshBuf, bar, band, cyl_between, make_text, mat4, ring, sphere

L3 = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])  # (u, v, h) → (X, Y, Z)
ML = mat4(L3)
ORDER = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]
FR = {"mercury": "mercure", "venus": "venus", "earth": "terre", "mars": "mars", "jupiter": "jupiter",
      "saturn": "saturne", "uranus": "uranus", "neptune": "neptune"}
BALL = {"mercury": 1.8, "venus": 2.6, "mars": 2.2, "jupiter": 4.2, "saturn": 3.4, "uranus": 2.9, "neptune": 2.9}
ELLIPSES = ("mercury", "mars")
SOCLE_R, SOCLE_H, ARM_T, GAP = 122.0, 6.0, 1.0, 0.8
CARRIAGE_POST, GLOBE_GAP = 2.6, 0.2


def elements(p, year=2050.0):
    """(e, ϖ en radians) figés à l'année donnée (table 1 du JPL, taux séculaires)."""
    with open(V2 / "research" / "constants.json", encoding="utf-8") as f:
        c = json.load(f)["planets"][p]["jpl_table1_1800_2050"]
    T = (year - 2000.0) / 100.0
    e = c["elements"]["e"] + T * c["rates_per_century"]["e"]
    w = c["elements"]["varpi_deg"] + T * c["rates_per_century"]["varpi_deg"]
    return e, math.radians(w)


def orbit_points(a, e, w, ellipse, n=360):
    lam = np.linspace(0.0, 2 * math.pi, n, endpoint=False)
    if ellipse:
        r = a * (1 - e * e) / (1 + e * np.cos(lam - w))
        return np.c_[r * np.cos(lam), r * np.sin(lam)]
    return np.c_[a * np.cos(lam) - a * e * math.cos(w), a * np.sin(lam) - a * e * math.sin(w)]


def groove(pts, w, h0, h1):
    t = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    nrm = np.c_[t[:, 1], -t[:, 0]]
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    return band(pts - nrm * w / 2, pts + nrm * w / 2, h0, h1)


def lid_frame(arch):
    W, H, _ = arch["masse"]["box_mm"]
    zc = arch["faces"]["couvercle"].get("centre_xz", [0.0, None])[1]
    if zc is None:
        zc = (AL.BACK_DOOR_Z[0] + AL.FRONT_COVER_Z[1]) / 2
    return H / 2.0, float(zc)


def build_lid(arch, colls, mats):
    coll = colls["couvercle"]
    spec = arch["faces"]["couvercle"]
    y_top, zc = lid_frame(arch)
    ys = y_top + SOCLE_H
    origin = (0.0, ys, zc)
    out = []
    # --- socle et rainures
    buf = MeshBuf()
    buf.add(ring(0.0, SOCLE_R, -SOCLE_H, 0.0, n=180), "dial", ML)
    slots = {}
    for p in ORDER:
        a = float(spec["rayons"][p])
        e, w = elements(p)
        slots[p] = (a, e, w)
        buf.add(groove(orbit_points(a, e, w, p in ELLIPSES), 1.4, 0.0, FP.ENG), "engrave", ML)
    buf.add(ring(SOCLE_R - 2.3, SOCLE_R - 1.7, 0.0, FP.ENG, n=180), "engrave", ML)
    socle = buf.to_object("CV_socle", coll, mats, loc=origin)
    tag(socle, "socle", source="couvercle", links=["CS_dessus"])
    out.append(socle)
    out.append(make_text("CV_txt_titre", "Le système solaire vu d'en haut", 3.0, coll, mats["engrave"],
                         mat4(L3, L3 @ np.array([0.0, -116.5, 0.03])), parent=socle, source="couvercle"))
    # --- hauteurs étagées des bras (intérieur en bas)
    n = len(ORDER) + 1
    rad = FP.radii(n)
    tel = 1.0 + CARRIAGE_POST + GLOBE_GAP + 2 * spec["tellurion"]["globe_r"] + 1.2
    h, levels = 3.0, {}
    for p in ORDER:
        levels[p] = h
        top = h + ARM_T + (tel if p == "earth" else 2 * BALL[p])
        h = top + GAP
    # --- colonne fixe du Soleil
    buf = MeshBuf()
    buf.add(ring(0.0, rad[-1][1], 0.0, h, n=24), "steel", ML)
    buf.add((sphere(6.0, 32, 16)[0] + [0.0, 0.0, h + 6.0], sphere(6.0, 32, 16)[1]), "gold", ML)
    col = buf.to_object("CV_colonne_soleil", coll, mats, loc=origin)
    tag(col, "column", source="couvercle", links=["CV_socle"])
    out.append(col)
    # --- bras des planètes
    for i, p in enumerate(ORDER):
        a, e, w = slots[p]
        H = levels[p]
        ri, ro = rad[i]
        buf = MeshBuf()
        buf.add(ring(ri, ro, 0.0, H, n=32), "dial", ML)
        buf.add(ring(ri, ro + 1.2, H, H + ARM_T, n=32), "dial", ML)
        reach = a + 18.0 if p == "earth" else a
        buf.add(bar((ro + 0.9, 0.0), (reach, 0.0), 2.0, 1.4, H, H + ARM_T), "dial", ML)
        buf.add(bar((-ro - 0.9, 0.0), (-10.0, 0.0), 2.0, 3.0, H, H + ARM_T), "dial", ML)
        if p != "earth":
            v, f = sphere(BALL[p], 24, 12)
            buf.add((v + [a, 0.0, H + ARM_T + BALL[p]], f), "p_" + p, ML)
            if p == "saturn":
                buf.add(ring(BALL[p] + 1.0, BALL[p] + 3.0, -0.15, 0.15, n=48), "p_saturn",
                        mat4(L3, L3 @ np.array([a, 0.0, H + ARM_T + BALL[p]])))
        arm = buf.to_object(f"CV_bras_{FR[p]}", coll, mats, loc=origin)
        tag(arm, "orrery_arm", key=f"helio_{p}", scale=1.0, axis=(0.0, 1.0, 0.0), source=f"orr_{p}",
            links=["CV_socle", "CV_colonne_soleil"], orbit_slot=[a, e, w])
        out.append(arm)
        if p == "earth":
            out += tellurion(coll, mats, arm, a, H + ARM_T, spec["tellurion"])
    return out


def tellurion(coll, mats, arm, a, h_arm, spec):
    """Chariot contre-tournant (orientation fixe), globe incliné (temps sidéral), bras de la Lune, aiguille d'ombre."""
    eps = math.radians(spec["inclinaison_deg"])
    gr, br = float(spec["globe_r"]), float(spec["bras_lune"])
    pole = np.array([0.0, math.cos(eps), -math.sin(eps)])  # pôle nord céleste : λ = 90°, β = 90° − ε
    out = []
    buf = MeshBuf()
    buf.add(ring(0.0, 3.5, 0.0, 1.0, n=32), "dial", ML)
    buf.add(ring(0.0, 0.9, 1.0, CARRIAGE_POST, n=16), "steel", ML)
    car = buf.to_object("CV_tellurion_chariot", coll, mats, loc=tuple(L3 @ [a, 0.0, h_arm]), parent=arm)
    tag(car, "carriage", key="helio_earth", scale=-1.0, axis=(0.0, 1.0, 0.0), source="tellurion",
        links=[arm.name], axis_frame="parent")
    out.append(car)
    hc = CARRIAGE_POST + GLOBE_GAP + gr
    R = np.stack([[1.0, 0.0, 0.0], [0.0, -math.sin(eps), -math.cos(eps)], pole], 1)
    v, f = sphere(gr, 36, 18)
    keys = ["light" if np.mean(v[list(fc), 2]) > 0.85 * gr else "earth" for fc in f]
    buf = MeshBuf().add((v, f), keys, mat4(R))
    buf.add(cyl_between(-(gr + 0.8) * pole, (gr + 0.8) * pole, 0.4, n=12), "steel")
    buf.add((sphere(0.8, 12, 6)[0] + [gr, 0.0, 0.0], sphere(0.8, 12, 6)[1]), "gold")
    glob = buf.to_object("CV_globe_terre", coll, mats, loc=(0.0, hc, 0.0), parent=car)
    tag(glob, "globe", key="gmst", scale=1.0, axis=tuple(pole), source="tellurion", links=[car.name],
        axis_frame="parent", meridien="Greenwich vers +X (point d'or) à gmst = 0")
    out.append(glob)
    buf = MeshBuf()
    buf.add(ring(0.96, 2.0, 1.2, 2.0, n=24), "silver", ML)
    buf.add(bar((1.8, 0.0), (br, 0.0), 1.2, 0.8, 1.2, 2.0), "silver", ML)
    buf.add(cyl_between(L3 @ [br, 0.0, 2.0], L3 @ [br, 0.0, hc - 1.2], 0.45, n=12), "silver")
    buf.add((sphere(1.2, 16, 8)[0] + L3 @ [br, 0.0, hc], sphere(1.2, 16, 8)[1]), "p_moon")
    moon = buf.to_object("CV_bras_lune", coll, mats, parent=car)
    tag(moon, "moon_arm", key="lambda_moon", scale=1.0, axis=(0.0, 1.0, 0.0), source="orr_moon",
        links=[car.name], axis_frame="parent")
    out.append(moon)
    hn = h_arm + hc + 2.4
    buf = MeshBuf()
    buf.add(bar((a + gr + 0.6, 0.0), (a + 18.0, 0.0), 0.8, 0.4, hn - 0.3, hn + 0.3), "dark", ML)
    buf.add(cyl_between(L3 @ [a + 17.5, 0.0, h_arm], L3 @ [a + 17.5, 0.0, hn], 0.5, n=12), "dark")
    nd = buf.to_object("CV_aiguille_ombre", coll, mats, parent=arm)
    tag(nd, "shadow_needle", source="gamma", links=[arm.name], follows=arm.name)
    out.append(nd)
    return out
