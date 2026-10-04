"""Anticythère 2.0 — module faces : face arrière (suite) : Saros et Exeligmos, plaque « mode d'emploi »."""
import math

import faces_common as FC
import faces_parts as FP
from faces_back import S, _nums_at, _ticks_at, build_calendar, build_eclipses
from faces_mesh import MeshBuf, ring

EXE_OFF = (0.0, 14.0)     # centre du petit cadran de l'Exeligmos, relatif à l'axe du Saros
EXE_R = 9.0
INSTRUCTIONS = ("MODE D'EMPLOI\n\n"
                "Manivelle : {n:g} tours = 1 jour solaire moyen.\n"
                "Calendrier : la date est à l'index du haut ;\n"
                "le guichet montre le jour de la semaine.\n"
                "Éclipses : à la nouvelle ou à la pleine Lune,\n"
                "l'aiguille de la Lune près d'un nœud (☊ ☋)\n"
                "annonce une éclipse ; γ en rayons terrestres,\n"
                "secteur rouge : totale ou annulaire possible.\n"
                "Saros : 223 lunaisons ; l'Exeligmos ajoute\n"
                "8 h par Saros (+0 h, +8 h, +16 h).")


def build_saros(spec, colls, mats, z, r_axe=1.4):
    """Cadran du Saros ; l'aiguille prolonge l'arbre `saros#a2` (rayon r_axe) qui traverse la platine arrière."""
    coll, c, R = colls["arriere"], spec["c"], spec["R"]
    step = 2 * math.pi / 223
    buf = MeshBuf()
    buf.add(ring(FP.hole_for(1, [(0.0, r_axe)]), R, *FP.face_h(S)), "dial")
    FP.ticks(buf, [-(k + 0.5) * step for k in range(223)], R - 8.0, R - 1.5, 0.12, S)
    FP.ticks(buf, [-(k - 0.5) * step for k in range(0, 223, 10)], R - 10.0, R - 1.5, 0.3, S)
    FP.circle_line(buf, R - 8.0, 0.25, S)
    FP.circle_line(buf, R - 1.2, 0.3, S)
    FP.numbers_into(buf, [(str(k), 1.6, R - 11.5, -k * step) for k in range(0, 223, 20)], S)
    # petit cadran de l'Exeligmos : trois secteurs (+0 h, +8 h, +16 h)
    third = 2 * math.pi / 3
    _ticks_at(buf, EXE_OFF, [-(k + 0.5) * third for k in range(3)], 1.5, EXE_R, 0.3)
    h0, h1 = FP.eng_h(S)
    buf.add(ring(EXE_R - 0.15, EXE_R + 0.15, h0, h1, n=48), "engrave",
            [[1, 0, 0, EXE_OFF[0]], [0, 1, 0, EXE_OFF[1]], [0, 0, 1, 0], [0, 0, 0, 1]])
    _nums_at(buf, EXE_OFF, [(f"+{8 * k} h", 1.5, 5.6, -k * third) for k in range(3)])
    face = FP.fixed("AR_saros_cadran", buf, coll, mats, c, z, source="saros", links=["cadran_arriere", "saros#a2"])
    out = [face, FP.label_at("AR_saros_txt_titre", "Saros · 223 lunaisons", 2.2, coll, mats, face, (0.0, -15.0), S),
           FP.label_at("AR_saros_txt_exeligmos", "Exeligmos", 1.4, coll, mats, face, (0.0, 25.0), S)]
    out.append(FP.hand("AR_exeligmos_aiguille", coll, mats, (c[0] + EXE_OFF[0], c[1] + EXE_OFF[1]), z, S, 0, 1,
                       [(0.0, None, 7.5, 1.0, 0.4), (math.pi, None, 2.5, 1.0, 1.4)], "exeligmos",
                       base=FP.FACE_T, source="saros", links=["AR_saros_cadran"]))
    out.append(FP.hand("AR_saros_aiguille", coll, mats, c, z, S, 0, 1,
                       [(0.0, None, R - 2.0, 1.2, 0.4), (math.pi, None, 8.0, 1.2, 2.0)], "saros", lev=1,
                       rad=[(0.0, r_axe)], source="saros#a2",
                       links=["cadran_arriere", "saros#a2", "AR_saros_cadran"]))
    return out


def build_instructions(spec, colls, mats, z):
    coll, c, R = colls["arriere"], spec["c"], spec["R"]
    buf = MeshBuf()
    buf.add(ring(0.0, R, *FP.face_h(S)), "dial")
    FP.circle_line(buf, R - 1.5, 0.3, S)
    face = FP.fixed("AR_mode_emploi", buf, coll, mats, c, z, source="cadran_arriere", links=["cadran_arriere"])
    body = INSTRUCTIONS.format(n=FC.crank_rate())
    return [face, FP.label_at("AR_mode_emploi_txt", body, 1.5, coll, mats, face, (0.0, 0.0), S)]


def build_back(arch, colls, mats):
    ar = arch["faces"]["arriere"]
    z = float(arch["platines_z"]["cadran arrière"][0])
    return (build_calendar(ar["calendrier"], arch, colls, mats, z) + build_eclipses(ar["eclipses"], colls, mats, z)
            + build_saros(ar["saros"], colls, mats, z, FP.arch_r(arch, "saros#a2", 1.4))
            + build_instructions(ar["mode_emploi"], colls, mats, z))
