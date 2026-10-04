"""Anticythère 2.0 — module faces : caisse en chêne (parois de 6 mm), verre avant, porte arrière ouverte, manivelle.

Dimensions : architecture.json masse.box_mm (largeur × hauteur × profondeur) ; en z, la caisse va de la porte arrière
(BACK_DOOR_Z) au cadre avant (FRONT_COVER_Z). La manivelle prolonge la tringle `manivelle#r0` (entrée CRANK_IN, paroi
gauche) hors de la caisse ; son mouvement copie celui de la tringle (scene.json si présent, sinon arbre J).
"""
import math

import numpy as np

from faces_common import AL, scene_part, tag
from faces_mesh import MeshBuf, box, cyl_between, mat4, sphere

FRAME_W = 5.0     # largeur du cadre avant autour de la fenêtre (côtés)
FRAME_WY = 8.0    # largeur haut/bas
GLASS_T = 2.0
DOOR_OPEN_DEG = 100.0


def _solid(name, coll, mats, parts, kind="case", loc=(0.0, 0.0, 0.0), links=(), source="caisse"):
    buf = MeshBuf()
    for geom, key in parts:
        buf.add(geom, key)
    ob = buf.to_object(name, coll, mats, loc=loc)
    tag(ob, kind, source=source, links=list(links))
    return ob


def build_case(arch, colls, mats):
    coll, wl = colls["caisse"], AL.WALL
    W, H, _ = arch["masse"]["box_mm"]
    X, Y = W / 2.0, H / 2.0
    zb, zf = AL.BACK_DOOR_Z, AL.FRONT_COVER_Z
    z0, z1 = zb[1], zf[1]
    out = [_solid("CS_paroi_gauche", coll, mats, [(box(-X, -X + wl, -Y, Y, z0, z1), "oak")]),
           _solid("CS_paroi_droite", coll, mats, [(box(X - wl, X, -Y, Y, z0, z1), "oak")]),
           _solid("CS_dessus", coll, mats, [(box(-X + wl, X - wl, Y - wl, Y, z0, z1), "oak")],
                  links=["CS_paroi_gauche", "CS_paroi_droite", "CV_socle"]),
           _solid("CS_dessous", coll, mats, [(box(-X + wl, X - wl, -Y, -Y + wl, z0, z1), "oak")],
                  links=["CS_paroi_gauche", "CS_paroi_droite"])]
    xi, yi = X - wl, Y - wl
    xw, yw = xi - FRAME_W, yi - FRAME_WY
    zc0 = z1 - wl
    frame = [(box(-xi, xi, yw, yi, zc0, z1), "oak"), (box(-xi, xi, -yi, -yw, zc0, z1), "oak"),
             (box(-xi, -xw, -yw, yw, zc0, z1), "oak"), (box(xw, xi, -yw, yw, zc0, z1), "oak")]
    out.append(_solid("CS_cadre_avant", coll, mats, frame, links=["CS_paroi_gauche", "CS_paroi_droite",
                                                                  "CS_dessus", "CS_dessous"]))
    zg = zc0 + (wl - GLASS_T) / 2
    out.append(_solid("CS_verre", coll, mats, [(box(-xw + 0.1, xw - 0.1, -yw + 0.1, yw - 0.1, zg, zg + GLASS_T),
                                                "glass")], kind="glass"))
    # porte arrière : charnière verticale sur l'arête arrière droite (vue de face), ouverte de 100°
    dt = zb[1] - zb[0]
    door = [(box(-W, 0.0, -Y, Y, 0.0, dt), "oak"),
            ((sphere(4.0, 16, 8)[0] + [-W + 15.0, 0.0, -3.0], sphere(4.0, 16, 8)[1]), "dial")]
    d = _solid("CS_porte_arriere", coll, mats, door, loc=(X, 0.0, zb[0]), links=["CS_paroi_droite"])
    d.rotation_euler = (0.0, -math.radians(DOOR_OPEN_DEG), 0.0)
    d["open_angle_deg"] = DOOR_OPEN_DEG
    out.append(d)
    out.append(crank(arch, coll, mats, X))
    return out


def crank(arch, coll, mats, X):
    rod = next((it for it in arch["items"] if it["id"] == "manivelle#r0"), None)
    if rod is not None:
        zr = (rod["z"][0] + rod["z"][1]) / 2
        p = np.array([rod["p"][0], rod["p"][1], zr])
        q = np.array([rod["q"][0], rod["q"][1], zr])
    else:  # repli : entrée de la manivelle, axe horizontal
        p = np.array([AL.CRANK_IN[0], AL.CRANK_IN[1], 114.0])
        q = p + [1.0, 0.0, 0.0]
    u = (q - p) / np.linalg.norm(q - p)
    s = (p[0] - (-X - 14.0)) / u[0]   # moyeu à 14 mm de la paroi : le bras incliné ne la touche pas
    O = p - s * u
    wv = np.array([0.0, 1.0, 0.0]) - u[1] * u
    wv /= np.linalg.norm(wv)
    F = np.stack([u, wv, np.cross(u, wv)], 1)   # repère (axe, bras, travers)
    M = mat4(F)
    buf = MeshBuf()
    buf.add(cyl_between(np.zeros(3), s * u, 2.5, n=20), "steel")
    buf.add(box(-5.0, 0.0, -4.0, 40.0, -3.0, 3.0), "steel", M)          # bras (a le long de l'axe, b vers le haut)
    buf.add(cyl_between(F @ [-5.0, 0.0, 0.0], F @ [0.0, 0.0, 0.0], 5.0, n=24), "steel")  # moyeu
    buf.add(cyl_between(F @ [-5.0, 40.0, 0.0], F @ [-25.0, 40.0, 0.0], 3.5, n=20), "oak")  # poignée
    ob = buf.to_object("CS_manivelle", coll, mats, loc=tuple(O))
    part = scene_part("manivelle#r0") or {}
    tag(ob, "crank", motion="linear", rate=float(part.get("rate", 1.0)), phys=int(part.get("phys", 1)),
        phase=float(part.get("phase", 0.0)), axis=tuple(u), source="manivelle#r0",
        links=["CS_paroi_gauche", "manivelle#r0"], copy_motion_from="manivelle#r0")
    return ob


def build_plates(arch, colls, mats):
    """Platines-cadrans simples (aperçu autonome seulement : la v2 complète les tient de parts.py / scene.json)."""
    pl, out = AL.PLATE, []
    for nm, key in (("avant", "cadran avant"), ("arriere", "cadran arrière")):
        z0, z1 = arch["platines_z"][key]
        out.append(_solid(f"V2F_platine_{nm}", colls["caisse"], mats,
                          [(box(pl["x"][0], pl["x"][1], pl["y"][0], pl["y"][1], z0, z1), "dial")],
                          kind="plate", source=key))
        out[-1]["id"] = "cadran_" + nm  # même identifiant que la platine de parts.py (résolution des liens)
    return out
