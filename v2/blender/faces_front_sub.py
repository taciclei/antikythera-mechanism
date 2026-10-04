"""Anticythère 2.0 — module faces : petits cadrans avant (horloge 24 h, équation du temps, Jupiter, époque).

Même convention que le cadran principal : 0 en haut, valeurs croissantes dans le sens horaire vu de face.
"""
import math

import numpy as np

import faces_common as FC
import faces_parts as FP
from faces_mesh import MeshBuf, ring, sphere

D = math.radians
EOT_HALF = D(75.0)            # demi-angle du secteur de l'équation du temps
EOT_MAX = 16.5                # minutes au bord du secteur
EOT_SCALE = -EOT_HALF / EOT_MAX  # radians par minute (positif → horaire)
LINKS = ["cadran_avant"]
NU_SCALE = 1.0                # aiguille ν : montre la longitude −ν (ligne des conjonctions), sens rétrograde


def _face(buf, R, hole, key="ring"):
    h0, h1 = FP.face_h(+1)
    buf.add(ring(hole, R, h0, h1), key)
    FP.circle_line(buf, R - 0.8, 0.3, +1)


def build_clock(spec, coll, mats, z):
    c, R = spec["c"], spec["R"]
    buf = MeshBuf()
    _face(buf, R, FP.hole_for(2))
    FP.ticks(buf, [-2 * math.pi * h / 24 for h in range(24)], R - 5.0, R - 1.2, 0.5, +1)
    FP.ticks(buf, [-2 * math.pi * q / 96 for q in range(96) if q % 4], R - 3.0, R - 1.2, 0.2, +1)
    FP.numbers_into(buf, [(str(h), 2.8, R - 8.5, -2 * math.pi * h / 24) for h in range(24)], +1, upright=True)
    face = FP.fixed("AV_horloge_cadran", buf, coll, mats, c, z, source="horloge", links=LINKS)
    out = [face, FP.label_at("AV_horloge_txt_titre", "Horloge 24 h", 2.6, coll, mats, face, (0.0, -11.0), +1),
           FP.label_at("AV_horloge_txt_legende", "● temps moyen   ★ temps sidéral", 1.5, coll, mats, face,
                       (0.0, -15.5), +1)]
    sun = [(FP.bead(19.0, 0.0, +1, 0, rad=2.0), "gold")]
    out.append(FP.hand("AV_horloge_temps_moyen", coll, mats, c, z, +1, 0, 2,
                       [(0.0, None, 24.0, 1.8, 0.6), (math.pi, None, 6.0, 1.8, 2.4)], "mean_solar", mat="gold",
                       extras=sun, source="horloge", links=LINKS + ["AV_horloge_cadran"]))
    star = [(FP.arrow_head(0.0, 25.5, 31.0, 3.0, +1, 1), "silver")]
    out.append(FP.hand("AV_horloge_temps_sideral", coll, mats, c, z, +1, 1, 2,
                       [(0.0, None, 26.0, 1.4, 0.5), (math.pi, None, 7.0, 1.4, 2.2)], "gmst", mat="steel",
                       extras=star, source="horloge", links=LINKS + ["AV_horloge_cadran"]))
    return out


def build_eot(spec, coll, mats, z):
    c, R = spec["c"], spec["R"]
    buf = MeshBuf()
    _face(buf, R, FP.hole_for(1))
    for m in range(-16, 17):
        r0 = R - (8.0 if m % 5 == 0 else 6.0)
        FP.ticks(buf, [EOT_SCALE * m], r0, R - 2.5, 0.45 if m % 5 == 0 else 0.22, +1)
    FP.ticks(buf, [EOT_SCALE * EOT_MAX, -EOT_SCALE * EOT_MAX], R - 9.0, R - 2.0, 0.6, +1)
    FP.circle_line(buf, R - 2.3, 0.3, +1, a0=-EOT_HALF, a1=EOT_HALF)
    lab = [(("+" if m > 0 else "−" if m < 0 else "") + str(abs(m)), 2.2, R - 11.5, EOT_SCALE * m)
           for m in range(-15, 16, 5)]
    FP.numbers_into(buf, lab, +1, upright=True)
    face = FP.fixed("AV_edt_cadran", buf, coll, mats, c, z, source="edt", links=LINKS)
    out = [face, FP.label_at("AV_edt_txt_titre", "Équation du temps", 2.4, coll, mats, face, (0.0, -10.0), +1),
           FP.label_at("AV_edt_txt_legende", "minutes : temps vrai − temps moyen", 1.4, coll, mats, face,
                       (0.0, -14.5), +1)]
    out.append(FP.hand("AV_edt_aiguille", coll, mats, c, z, +1, 0, 1,
                       [(0.0, None, 29.0, 1.6, 0.4), (math.pi, None, 6.0, 1.6, 2.4)], "eot", mat="steel",
                       scale=EOT_SCALE, source="edt", links=LINKS + ["AV_edt_cadran"],
                       ephem_unit="minutes", sector_half_angle=EOT_HALF))
    return out


JUP_MOONS = [("io", "jup_io", 12.0, "gold"), ("europe", "jup_europa", 17.0, "light"),
             ("ganymede", "jup_ganymede", 23.0, "p_venus"), ("callisto", "jup_callisto", 29.0, "p_mercury")]


def build_jupiter(spec, coll, mats, z):
    c, R = spec["c"], spec["R"]
    n = len(JUP_MOONS) + 2
    buf = MeshBuf()
    _face(buf, R, FP.hole_for(n))
    FP.ticks(buf, [-D(a) for a in range(0, 360, 10)], R - 3.0, R - 1.2, 0.25, +1)
    FP.ticks(buf, [-D(a) for a in range(0, 360, 30)], R - 4.5, R - 1.2, 0.45, +1)
    face = FP.fixed("AV_jupiter_cadran", buf, coll, mats, c, z, source="laplace", links=LINKS)
    out = [face, FP.label_at("AV_jupiter_txt_titre", "Jupiter et ses lunes", 2.0, coll, mats, face, (0.0, -24.0), +1),
           FP.label_at("AV_jupiter_txt_legende", "Io · Europe · Ganymède · Callisto · ν · lunette", 1.2, coll,
                       mats, face, (0.0, -27.0), +1)]
    lk = LINKS + ["AV_jupiter_cadran", "laplace"]
    for k, (nom, key, L, mb) in enumerate(JUP_MOONS):
        out.append(FP.hand(f"AV_jupiter_{nom}", coll, mats, c, z, +1, k, n,
                           [(0.0, None, L, 1.0, 0.4), (math.pi, None, 4.0, 1.0, 1.6)], key, mat="steel",
                           extras=[(FP.bead(L - 0.5, 0.0, +1, k, rad=1.3), mb)], source="laplace", links=lk))
    # Ligne des conjonctions Io-Europe : elles tombent à la longitude −ν (ν = λ_Io − 2·λ_Europe, ephem.jupiter_nu) ;
    # l'aiguille est sur l'arbre ν renversé 1:1 (study/trains.md) : scale +1, un tour rétrograde en 486,8 j.
    out.append(FP.hand("AV_jupiter_nu", coll, mats, c, z, +1, n - 2, n,
                       [(0.0, None, 31.0, 0.6, 0.3), (math.pi, None, 31.0, 0.6, 0.3)], "jup_nu", mat="red",
                       scale=NU_SCALE, source="laplace", links=lk, shows="ligne des conjonctions Io-Europe (−ν)"))
    h0, h1 = FP.level(n - 1, +1)
    v, f = sphere(2.5, 24, 12)
    ball = [((v + np.array([0.0, 0.0, h1 + 2.5]), f), "p_jupiter")]
    out.append(FP.hand("AV_jupiter_lunette", coll, mats, c, z, +1, n - 1, n,
                       [(0.0, None, 32.0, 2.0, 2.0), (math.pi, None, 32.0, 2.0, 2.0)], "lunette", mat="silver",
                       extras=ball, source="lunette", links=lk))
    return out


EPOCH_TEXT = ("PLAQUE D'ÉPOQUE\n\nOrbites figées en 2050\nValable de 2000 à 2100\nRepère : écliptique J2000\n"
              "Mise à l'heure :\n1er janvier 2026, 0 h TT\nManivelle : {n:g} tours = 1 jour")


def build_epoch(spec, coll, mats, z):
    c, R = spec["c"], spec["R"]
    buf = MeshBuf()
    _face(buf, R, 0.0, key="dial")
    FP.circle_line(buf, R - 3.0, 0.3, +1)
    face = FP.fixed("AV_epoque_plaque", buf, coll, mats, c, z, source="cadran_avant", links=LINKS)
    body = EPOCH_TEXT.format(n=FC.crank_rate())
    return [face, FP.label_at("AV_epoque_txt", body, 2.2, coll, mats, face, (0.0, 0.0), +1)]


def build_subdials(arch, colls, mats):
    av, z, coll = arch["faces"]["avant"], float(arch["z_cadran_avant"]), colls["avant"]
    return (build_clock(av["horloge"], coll, mats, z) + build_eot(av["edt"], coll, mats, z)
            + build_jupiter(av["jupiter"], coll, mats, z) + build_epoch(av["epoque"], coll, mats, z))
