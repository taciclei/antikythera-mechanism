"""Anticythère 2.0 — modèle de scène : architecture.json + trains.json → spec/scene.json (CONTRACT.md § 3).

Python pur (json, fractions, math, numpy). Lancer : $PY tools/scene_model.py  (écrit v2/spec/scene.json).

Ce que fait ce module :
- une pièce de scène par item d'architecture.json (roue droite, couronne, conique, arbre, tube, tringle, bloc,
  axe de tour, divers), plus une platine par entrée de `platines_z` (contour 450 × 340, trous) et quelques
  pièces implicites (`synth`: true) : la conique d'en face d'un renvoi d'angle et le pignon couché qui mène une
  couronne d'arrivée ;
- taux exacts : pour chaque train placé, on part du taux de la SORTIE dans trains.json et on remonte la chaîne
  (`ordre_couples`, pignon fou d'étage, reprise 24 → fou → 24) ; chaque engrènement extérieur et chaque fou
  inversent le sens ; l'entrée recalculée doit valoir Y (ou J) à 1e-12 près, sinon SceneError ;
- sorties non linéaires : `motion` = « ephem:<clé> » (clés partagées de tools/ephem.py) ;
- entraxes exacts : les centres arrondis au µm d'architecture.json sont ajustés (pas de Newton de norme minimale)
  pour que chaque couple de roues droites tombe à m·(z1 + z2)/2 à 1e-9 près ;
- phases : règle de la v1 (build/am/involute.py, mesh_phase) — à jours = 0, une dent de la menée tombe dans un
  creux de la menante ; la dent 0 d'une roue est sur +X local ; même règle, au point de contact, pour les couples
  couronne / pignon couché et les coniques d'onglet (engage_phase, conventions de blender/parts.py) ;
- sens des renvois (architecture.json, « sens ») : chaque « con » garde le sens ; le pignon d'arrivée d'un renvoi
  de moyeu est placé du côté de la couronne qui le garde (place_arrival_pin) ;
- liens : la sémantique d'arch_geom.linked (même `group`, nom de base « axe_x ») est rendue explicite, et chaque roue
  enfilée sur un arbre, tube ou axe coaxial reçoit `arbor_r` (alésage de parts.py) ; le tube Y est creux (`r_in`).
"""
import json
import math
import os
import sys
from fractions import Fraction as F

import numpy as np

V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH_PATH = os.path.join(V2, "spec", "architecture.json")
TRAINS_PATH = os.path.join(V2, "spec", "trains.json")
OUT_PATH = os.path.join(V2, "spec", "scene.json")

TWO_PI = 2.0 * math.pi
BEVEL_M = 0.4            # module des couronnes, pignons couchés et coniques de renvoi (arch_layout.BEVEL_M)
CROWN_TEETH = 96         # couronne de moyeu ou d'arrivée
PIN_TEETH = 24           # pignon couché sur une tringle, conique d'onglet
SPUR_M = 0.5             # module des roues droites de renvoi (prises, carrousel, entrées Lune)
HUB_PIN_AT = BEVEL_M * CROWN_TEETH / 2 - 2.0   # 17,2 mm : centre du pignon couché sur la couronne
PIN_WIDTH = 10 * BEVEL_M  # 4 mm : largeur d'un pignon couché (parts.py : 10 m)
MITRE_R = BEVEL_M * PIN_TEETH / 2 + 2 * BEVEL_M  # 5,6 mm : encombrement d'une conique de 24
CROWN_R = BEVEL_M * CROWN_TEETH / 2 + 2 * BEVEL_M  # 20,0 mm : encombrement d'une couronne de 96
FACE_HUB = 1             # denture des couronnes de moyeu tournée vers +Z (pignon au-dessus)
FACE_ARRIVAL = -1        # denture des couronnes d'arrivée tournée vers −Z : même sens que le moyeu
PLATE_X = (-225.0, 225.0)  # contour des platines : 450 × 340 mm (arch_layout.PLATE)
PLATE_Y = (-170.0, 170.0)
HOLE_CLEAR = 0.3         # rayon d'un trou = rayon de la pièce + 0,3 mm
BORE_CLEAR = 0.05        # alésage d'un tube sur son arbre (parts.py : même jeu)
SNAP_TOL = 0.02          # deux points à moins de 0,02 mm sont le même axe (arrondis d'architecture.json)
LON_SCALE = -1.0         # rad par rad : phys = +1 → aiguille horaire vue de face
EOT_SCALE = -10.0 * TWO_PI / 1440.0  # rad par minute : 1 min de temps = 0,25° d'angle horaire, ×10 (couple 120:12)
PLANETS = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]

# Clés de l'éphéméride partagée (tools/ephem.py, KEYS) utilisées par la scène.
EPHEM_KEYS = (["lambda_sun", "lambda_moon", "node", "eot", "helio_earth"]
              + [f"lambda_geo_{p}" for p in PLANETS] + [f"helio_{p}" for p in PLANETS])
# Train des items → clé de `trains_places` (et arbre de sortie de trains.json).
TRAIN_ALIAS = {"ytrain": "Y", "prec": "precession_ring"}
HUB_ROUTES = ("lune_Y", "j_avant", "temps_J", "temps_Y", "manivelle")


class SceneError(Exception):
    """Incohérence du modèle (taux, sens, géométrie) : la génération s'arrête bruyamment."""


# ---------------------------------------------------------------------------------------------------------------
# Entraînements (taux exacts, sens)
# ---------------------------------------------------------------------------------------------------------------

def lin(absrate, phys, signed=None):
    """Entraînement à taux constant : |taux| exact (Fraction, tours/jour), sens physique, taux signé éventuel."""
    absrate = abs(F(absrate))
    phys = int(phys)
    if phys not in (1, -1):
        raise SceneError(f"sens physique invalide : {phys}")
    return {"motion": "linear", "abs": absrate, "phys": phys,
            "signed": F(signed) if signed is not None else phys * absrate}


def eph(key, phys, base=LON_SCALE, mean=None):
    """Entraînement non linéaire : angle = phys · base · ephem.value(clé, jours) + phase (scale = phys · base)."""
    if key not in EPHEM_KEYS:
        raise SceneError(f"clé d'éphéméride inconnue : {key}")
    return {"motion": "ephem:" + key, "phys": int(phys), "scale": phys * base,
            "mean": F(mean) if mean is not None else F(0)}


FIXED = {"motion": "fixed"}


def shaft_drive(S, sid):
    """Entraînement d'un arbre de trains.json (phys absent : sens du signe du taux)."""
    sh = S[sid]
    r = F(sh["rate_turns_per_day"])
    phys = sh.get("phys")
    if phys is None:
        phys = 1 if r >= 0 else -1
    d = lin(abs(r), phys, signed=r)
    d["ref"] = sid  # taux signé de trains.json (le signe peut différer de phys, ex. J : +1, phys −1)
    return d


def same_drive(a, b, tol=1e-12):
    """Deux entraînements linéaires égaux : taux exacts égaux (et à 1e-12 en flottant), même sens."""
    if a["motion"] != "linear" or b["motion"] != "linear":
        return a["motion"] == b["motion"] and a.get("phys") == b.get("phys")
    fa, fb = float(a["abs"]), float(b["abs"])
    return a["abs"] == b["abs"] and abs(fa - fb) <= tol * max(1.0, abs(fb)) and a["phys"] == b["phys"]


def set_drive(drives, pid, d, why=""):
    """Affecte un entraînement ; s'il existe déjà, il doit être identique (contrôle de cohérence). Entre deux
    entraînements égaux, celui d'un arbre de trains.json (« ref ») l'emporte : son taux signé est celui du fichier."""
    if pid in drives:
        if not same_drive(drives[pid], d):
            raise SceneError(f"{pid} : entraînement incohérent ({why}) : {fmt(drives[pid])} ≠ {fmt(d)}")
        if d.get("ref") and not drives[pid].get("ref"):
            drives[pid] = d
        return
    drives[pid] = d


def fmt(d):
    if d["motion"] == "linear":
        return f"{d['abs']} tr/j, phys {d['phys']:+d}"
    return d["motion"]


def crown_rule(phys, face, u, contact):
    """Sens d'un pignon couché (axe u) engrené sur la face d'une couronne d'axe Z, ou l'inverse.

    face = +1 : denture vers +Z (pignon au-dessus) ; contact = position du pignon moins centre de la couronne (xy).
    Roulement au contact : phys_pignon = phys_couronne · face · σ, σ = signe de u · contact (formule involutive).
    """
    s = u[0] * contact[0] + u[1] * contact[1]
    if abs(s) < 1e-9:
        raise SceneError("pignon couché tangent à sa couronne")
    return phys * face * (1 if s > 0 else -1)


# ---------------------------------------------------------------------------------------------------------------
# Trains placés : remontée de la sortie vers l'entrée
# ---------------------------------------------------------------------------------------------------------------

def arbor_of(w):
    """Arbre portant une roue de train (premier lien de l'item, cf. arch_place.train_items)."""
    return w["links"][0]


def stage_list(wheels, tid):
    """Couples dans l'ordre réel : [(menante, menée, fou | None)] par indice d'étage."""
    st = {}
    for w in wheels:
        if w.get("role") in ("menante", "menee", "fou"):
            st.setdefault(w["stage"], {})[w["role"]] = w
    out = []
    for k in sorted(st):
        if "menante" not in st[k] or "menee" not in st[k]:
            raise SceneError(f"{tid} : étage {k} incomplet")
        out.append((st[k]["menante"], st[k]["menee"], st[k].get("fou")))
    return out


def expected_input(tid, place, arch, S):
    """Entraînement attendu à l'entrée d'un train : J (train J → Y), L de Neptune (précession), sinon la source du moyeu."""
    if tid == "ytrain":
        return "J", shaft_drive(S, "J")
    if tid == "prec":
        return "neptune_L", shaft_drive(S, "neptune_L")
    src = arch["moyeux"][place["hub"]]["src"]
    return src, shaft_drive(S, src)


def walk_train(tid, items, arch, S, drives, report):
    """Taux et sens de tous les arbres d'un train, de la sortie (trains.json) vers l'entrée ; contrôle de l'entrée."""
    key = TRAIN_ALIAS.get(tid, tid)
    place = arch["trains_places"][key]
    wheels = [it for it in items if it.get("train") == tid and it.get("wheel") == "train"]
    stages = stage_list(wheels, tid)
    order = place.get("ordre_couples")
    teeth = [[m["teeth"], n["teeth"]] for m, n, _ in stages]
    if order is not None and teeth != order:
        raise SceneError(f"{tid} : couples des items {teeth} ≠ ordre_couples {order}")
    idler_stage = place.get("idler_stage")
    fous = [k for k, (_, _, f) in enumerate(stages) if f is not None]
    if order is not None and fous != ([idler_stage] if idler_stage is not None else []):
        raise SceneError(f"{tid} : pignon fou aux étages {fous}, idler_stage = {idler_stage}")
    out = shaft_out = shaft_drive(S, key)
    if tid == "prec":
        # l'anneau tropique (179 dents intérieures) et son pignon de 15 sont dans le bloc du temps : on remonte
        # d'abord ces couples (un couple intérieur garde le sens ; les coniques de prec_bas le gardent aussi)
        rate, phys = out["abs"], out["phys"]
        for zd, zn, kind in reversed(S[key]["stages"][len(stages):]):
            rate, phys = rate * F(zn, zd), (phys if kind == "internal" else -phys)
        out = lin(rate, phys)
    set_drive(drives, arbor_of(stages[-1][1]), out, f"sortie de {tid}")
    for m, n, fou in reversed(stages):
        dn = drives[arbor_of(n)]
        rate = dn["abs"] * F(n["teeth"], m["teeth"])
        phys = -dn["phys"] * (-1 if fou is not None else 1)
        set_drive(drives, arbor_of(m), lin(rate, phys), f"{tid} {m['id']}")
        if fou is not None:
            set_drive(drives, arbor_of(fou), lin(rate * F(m["teeth"], fou["teeth"]), -phys), f"fou {fou['id']}")
    in_id = arbor_of(stages[0][0])
    wheel_arbor = {w["id"]: arbor_of(w) for w in wheels}
    rep = [w for w in wheels if w.get("role") in ("reprise", "reprise_fou")]
    if rep:
        d0 = drives[in_id]
        on_a0 = [w for w in rep if w["role"] == "reprise" and arbor_of(w) == in_id]
        fou = [w for w in rep if w["role"] == "reprise_fou"]
        on_ax = [w for w in rep if w["role"] == "reprise" and arbor_of(w) != in_id]
        if len(on_a0) != 1 or len(fou) != 1 or len(on_ax) != 1:
            raise SceneError(f"{tid} : reprise incomplète")
        on_a0, fou, on_ax = on_a0[0], fou[0], on_ax[0]
        if place.get("reprise") != ["fou", fou["teeth"]]:
            raise SceneError(f"{tid} : reprise {place.get('reprise')} ≠ fou de {fou['teeth']}")
        tube = arbor_of(on_ax) + "#tubeY"
        set_drive(drives, arbor_of(fou), lin(d0["abs"] * F(on_a0["teeth"], fou["teeth"]), -d0["phys"]), "fou de reprise")
        # 24 → fou → 24 : deux inversions, le tube Y de la tour garde le sens de l'arbre a0
        set_drive(drives, tube, lin(d0["abs"] * F(on_a0["teeth"], on_ax["teeth"]), d0["phys"]), "tube Y")
        wheel_arbor[on_ax["id"]] = tube
        in_id = tube
    src, exp = expected_input(tid, place, arch, S)
    got = drives[in_id]
    if not same_drive(got, exp):
        raise SceneError(f"ÉCHEC du contrôle d'entrée du train {tid} : {in_id} recalculé = {fmt(got)}, "
                         f"attendu {src} = {fmt(exp)}")
    set_drive(drives, in_id, exp, f"entrée de {tid}")  # contrôle passé : l'entrée porte le taux signé de {src}
    report[key] = {"train": tid, "input": in_id, "source": src, "output": arbor_of(stages[-1][1]),
                   "shaft_out": key, "rate_out": str(shaft_out["signed"]),
                   "phys_out": shaft_out["phys"]}
    return wheel_arbor


# ---------------------------------------------------------------------------------------------------------------
# Sortes de pièces
# ---------------------------------------------------------------------------------------------------------------

def unit2(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy)
    if n < 1e-9:
        raise SceneError(f"segment nul {p} → {q}")
    return (dx / n, dy / n)


def spur_teeth(r, m=SPUR_M):
    """Dents d'une roue droite de renvoi d'après son rayon d'encombrement r = m·z/2 + m."""
    z = (r - m) * 2 / m
    if abs(z - round(z)) > 1e-6:
        raise SceneError(f"rayon {r} : nombre de dents non entier ({z})")
    return int(round(z))


def wheel_spec(it, hubs):
    """(sorte, dents, module, engrènement, tringle porteuse | None) d'une roue de renvoi."""
    iid, r, route = it["id"], it["r"], it.get("route")
    if iid in hubs or iid.endswith("#bus#cour") or (route and abs(r - CROWN_R) < 1e-6):
        return "crown", CROWN_TEETH, BEVEL_M, "crown", None
    if "#bus#pin" in iid:
        return "gear", PIN_TEETH, BEVEL_M, "crown", iid.split("#pin")[0] + "#rod"
    if route and abs(r - MITRE_R) < 1e-6 and "#m" in iid:
        rod_id = f"{route}#r{iid.split('#m')[1][0]}"
        if any(lk in hubs for lk in it["links"]):  # pignon couché sur la couronne d'un moyeu
            return "gear", PIN_TEETH, BEVEL_M, "crown", rod_id
        return "bevel", PIN_TEETH, BEVEL_M, "bevel", rod_id
    if iid.endswith("#mitre"):  # conique d'onglet sur l'arbre du carrousel
        return "bevel", PIN_TEETH, BEVEL_M, "bevel", None
    return "gear", spur_teeth(r), SPUR_M, "external", None


def classify(it, hubs):
    """Sorte de pièce de scène d'un item d'architecture.json (et données de roue éventuelles)."""
    iid = it["id"]
    if it.get("block"):
        return {"kind": "block"}
    if it["kind"] == "rod":
        return {"kind": "rod"}
    if it.get("wheel") == "train":
        return {"kind": "gear", "teeth": it["teeth"], "m": it["m"], "mesh": it.get("mesh_kind", "external"),
                "rod": None}
    if it.get("wheel") == "renvoi":
        kind, z, m, mesh, rod_id = wheel_spec(it, hubs)
        return {"kind": kind, "teeth": z, "m": m, "mesh": mesh, "rod": rod_id}
    if iid.startswith("axe_"):
        if iid.endswith("#tubeY") or iid.endswith("#haut"):  # tube Y (Ø 8) : bas (reprise) et haut (au-dessus)
            return {"kind": "tube"}
        return {"kind": "arbor" if iid in ("axe_Y", "axe_J", "axe_soleil") else "axis"}
    if iid.endswith("#tenon"):
        return {"kind": "misc"}
    return {"kind": "arbor"}


def ephem_route(rid):
    """Clé d'éphéméride d'un renvoi non linéaire (None : renvoi linéaire ; 'fixed' : coulisse γ)."""
    if rid == "gamma":
        return "fixed"
    if rid.startswith("geo_"):
        return "lambda_geo_" + rid[4:]
    if rid.startswith("orr_"):
        nm = rid[4:]
        return "lambda_moon" if nm == "moon" else "helio_" + nm
    return {"moon_true": "lambda_moon", "node": "node", "lunette": "lambda_geo_jupiter", "vers_edt": "eot"}.get(rid)


def carousel_key(name):
    """(clé, arbre moyen de trains.json) d'un arbre du carrousel car_<nom>."""
    if name == "moon":
        return "lambda_moon", "moon_true"
    if name == "node":
        return "node", "moon_node"
    return "lambda_geo_" + name, name + "_geo"


# ---------------------------------------------------------------------------------------------------------------
# Entraînements des moyeux, tringles, renvois, carrousel, entrées de la Lune et axes
# ---------------------------------------------------------------------------------------------------------------

def hub_rod_drive(src, hub_c, rod, pin_c):
    """Tringle de moyeu (96/24 : 4 fois la source) ; sens par la règle de la couronne de moyeu."""
    u = unit2(rod["p"], rod["q"])
    phys = crown_rule(src["phys"], FACE_HUB, u, (pin_c[0] - hub_c[0], pin_c[1] - hub_c[1]))
    return lin(4 * src["abs"], phys), u


def arrival_crown_drive(src, rod_d, u, crown_c, pin_c, face=FACE_ARRIVAL):
    """Couronne d'arrivée (24/96) : taux de la source ; sens par la règle de la couronne (face de sa denture)."""
    phys = crown_rule(rod_d["phys"], face, u, (pin_c[0] - crown_c[0], pin_c[1] - crown_c[1]))
    return lin(src["abs"], phys, signed=src["signed"] if phys == src["phys"] else None)


def mid(z):
    return 0.5 * (z[0] + z[1])


def crown_face(it, by_id, hubs):
    """Face de la denture d'une couronne : +1 (vers +Z, pignon au-dessus) pour un moyeu ; pour une couronne
    d'arrivée, −1 si son arbre monte au-dessus de la tringle (la couronne est au-dessus du pignon), sinon +1."""
    if it["id"] in hubs:
        return FACE_HUB
    if it["id"].endswith("#bus#cour"):
        return FACE_ARRIVAL
    if it.get("_face") is not None:  # déjà fixée par place_arrival_pin (avant de raccourcir l'arbre)
        return it["_face"]
    arb = [x for x in by_id.values() if x.get("route") == it.get("route") and x["kind"] == "cyl"
           and not x.get("wheel") and math.dist(x["c"], it["c"]) < 1e-6]
    if not arb:
        raise SceneError(f"{it['id']} : couronne d'arrivée sans arbre")
    return FACE_ARRIVAL if max(x["z"][1] for x in arb) > mid(it["z"]) + 1.0 else FACE_HUB


def place_arrival_pin(rod, crown, hub_end, hc, items, by_id, hubs):
    """Pignon couché qui mène la couronne d'arrivée d'un renvoi de moyeu, placé du côté de la couronne qui GARDE le
    sens de la source (architecture.json, « sens » : chaque « con » garde le sens, réglé par le côté d'engrènement).
    Règle de la couronne aux deux bouts : garder le sens ⇔ FACE_HUB · σ_moyeu · face · σ_arrivée = +1.
    Couronne tournée vers −Z (arbre qui monte, ex. j_avant) : pignon du côté du moyeu, rien ne bouge. Couronne
    tournée vers +Z (arbre venu d'en dessous : lune_Y, temps_J, temps_Y) : pignon au-delà du centre ; la tringle
    est prolongée jusqu'au bout du pignon (17,2 + 2 mm < 20 mm : dans l'encombrement réservé de la couronne) et
    l'arbre de la couronne arrêté 1 mm sous la tringle. Pose crown['_pin'], crown['_face'] ; renvoie un rapport."""
    face = crown_face(crown, by_id, hubs)
    cc = crown["c"]
    v = unit2(cc, hc)                                # du centre de la couronne vers le moyeu
    u = unit2(rod["p"], rod["q"])
    s_hub = 1 if hub_end == "p" else -1              # signe de u · (pignon du moyeu − centre du moyeu)
    s_arr = FACE_HUB * s_hub * face                  # signe voulu de u · (pignon d'arrivée − centre de la couronne)
    k = 1 if (u[0] * v[0] + u[1] * v[1]) * s_arr > 0 else -1   # +1 : côté du moyeu, −1 : au-delà du centre
    crown["_pin"] = [cc[0] + k * v[0] * HUB_PIN_AT, cc[1] + k * v[1] * HUB_PIN_AT]
    crown["_face"] = face
    if k > 0:
        return None
    reach = HUB_PIN_AT + PIN_WIDTH / 2
    cend = "q" if hub_end == "p" else "p"
    rod[cend] = [cc[0] - v[0] * reach, cc[1] - v[1] * reach]
    top = mid(crown["z"]) - rod["r"] - 1.0
    trimmed = {}
    for x in items:
        if (x.get("route") == crown.get("route") and x["kind"] == "cyl" and not x.get("wheel")
                and math.dist(x["c"], cc) < 1e-6 and x["z"][1] > top):
            if x["z"][0] >= top - 1.0:
                raise SceneError(f"{x['id']} : arbre trop court pour passer sous la tringle {rod['id']}")
            trimmed[x["id"]] = [x["z"][1], top]
            x["z"] = [x["z"][0], top]
    return {"tringle": rod["id"], "bout": cend, "pignon": [round(v_, 6) for v_ in crown["_pin"]],
            "arbres_raccourcis": trimmed}


def assign_drives(items, by_id, arch, S, drives, wheel_arbor):
    """Entraînement de chaque item (dict id → entraînement) ; les trains sont déjà remontés (walk_train)."""
    hubs = arch["moyeux"]
    P = arch["trains_places"]
    for hub, h in hubs.items():
        set_drive(drives, hub, shaft_drive(S, h["src"]), "couronne de moyeu")
    set_drive(drives, "axe_Y", shaft_drive(S, "Y"), "arbre Y")
    set_drive(drives, "axe_J", shaft_drive(S, "J"), "arbre J")
    renvois = {r["id"]: r for r in arch["renvois"]}
    out = {}
    for it in items:
        iid = it["id"]
        if "#bus#" in iid:
            tid = iid.split("#bus#")[0]
            hub = P[TRAIN_ALIAS.get(tid, tid)]["hub"]
            src = drives[hub]
            rod, pin0 = by_id[tid + "#bus#rod"], by_id[tid + "#bus#pin0"]
            rd, u = hub_rod_drive(src, hubs[hub]["c"], rod, pin0["c"])
            if iid.endswith("#cour"):
                d = arrival_crown_drive(src, rd, u, it["c"], by_id[tid + "#bus#pin1"]["c"])
                tgt = it["links"][1]
                tgt = tgt + "#tubeY" if tgt.startswith("axe_") else tgt
                if not same_drive(d, drives[tgt]):
                    raise SceneError(f"{iid} : la couronne d'arrivée ({fmt(d)}) ne mène pas {tgt} ({fmt(drives[tgt])})")
                out[iid] = d
            else:
                out[iid] = rd
        elif it.get("route"):
            out[iid] = route_drive(it, by_id, renvois, hubs, S, drives)
        elif iid.startswith("car_") or iid.startswith("tube_"):
            name = iid.split("#")[0].split("_", 1)[1]
            key, mean_shaft = carousel_key(name)
            out[iid] = eph(key, 1 if iid.startswith("tube_") else -1, mean=F(S[mean_shaft]["rate_turns_per_day"]))
        elif iid.startswith("lune_entree_"):
            pre = iid.split("#")[0]
            w1 = by_id[pre + "#w1"]
            d = drives[w1["links"][0]]
            if iid.endswith("#tenon"):
                out[iid] = FIXED
            elif iid.endswith("#fou"):
                out[iid] = lin(d["abs"] * F(spur_teeth(w1["r"]), spur_teeth(it["r"])), -d["phys"])
            else:
                out[iid] = d
        elif it.get("block"):
            out[iid] = FIXED
        elif iid == "axe_soleil":
            out[iid] = eph("lambda_sun", 1, mean=F(S["sun_geo"]["rate_turns_per_day"]))
        elif iid.startswith("axe_") and iid.endswith("#haut") and iid[:-5] + "#tubeY" in drives:
            # au-dessus des trains, la partie visible (Ø 8) est le tube Y (architecture.axis_items : « le tube Y
            # (Ø 8) au-dessus ») ; l'arbre L (Ø 4) est caché dedans ; la couronne de la tringle de moyeu y est calée
            out[iid] = drives[iid[:-5] + "#tubeY"]
        elif iid.startswith("axe_") and ("#haut" in iid or "#bas" in iid):
            out[iid] = drives[iid.split("#")[0]]
        elif iid in wheel_arbor:
            out[iid] = drives[wheel_arbor[iid]]
        elif iid in drives:
            out[iid] = drives[iid]
        else:
            raise SceneError(f"{iid} : aucun entraînement")
    return out


def route_drive(it, by_id, renvois, hubs, S, drives):
    """Entraînement d'une pièce de renvoi."""
    rid, iid = it["route"], it["id"]
    rv = renvois.get(rid, {})
    if rid in HUB_ROUTES:
        hub = rv["hub"]
        src = drives[hub]
        rod = by_id[f"{rid}#r0"]
        pin = next(x for x in by_id.values() if x.get("route") == rid and x.get("wheel") == "renvoi"
                   and hub in x["links"] and abs(x["r"] - MITRE_R) < 1e-6)
        rd, u = hub_rod_drive(src, hubs[hub]["c"], rod, pin["c"])
        crown = next((x for x in by_id.values() if x.get("route") == rid and x.get("wheel") == "renvoi"
                      and abs(x["r"] - CROWN_R) < 1e-6), None)
        if it["kind"] == "rod" or it is pin:
            return rd
        if crown is None:
            raise SceneError(f"{iid} : pièce inattendue dans le renvoi {rid}")
        d = arrival_crown_drive(src, rd, u, crown["c"], crown["_pin"], crown_face(crown, by_id, hubs))
        if d["phys"] != src["phys"]:  # architecture.json, « sens » : con → con garde le sens
            raise SceneError(f"{iid} : la couronne d'arrivée du renvoi {rid} ne garde pas le sens de {hub}")
        return d
    key = ephem_route(rid)
    if key == "fixed":
        return FIXED
    if key is not None:
        mean = F(S[rv["shaft"]]["rate_turns_per_day"]) if rv.get("shaft") in S else None
        if key == "eot":
            return eph(key, 1, base=EOT_SCALE, mean=mean)
        phys = 1
        if rv.get("car") or (rid.startswith("orr_") and "#prise_axe" not in iid):
            # couple extérieur final (64:64 du carrousel) ou prise extérieure de l'orrery (pour orr_moon, la prise
            # est dans le bloc Lune : son arbre z0 tourne déjà comme la roue de prise des planètes) ; ainsi toutes
            # les tringles de l'orrery tournent de +λ autour de +Y, comme les bras du couvercle (faces_lid)
            phys = -1
        return eph(key, phys, mean=mean)
    if rid in ("prec_avant", "prec_bas"):
        return drives["prec#a1"]
    return shaft_drive(S, rv["shaft"])


# ---------------------------------------------------------------------------------------------------------------
# Couples de roues droites et ajustement exact des entraxes
# ---------------------------------------------------------------------------------------------------------------

def spur_pairs(items, by_id, hubs):
    """Couples de roues droites (ids triés) : partenaires des trains, prises de l'orrery, carrousel, entrées Lune."""
    pairs = set()
    for it in items:
        for q in it.get("partners", []):
            pairs.add(tuple(sorted((it["id"], q))))
        iid = it["id"]
        if iid.endswith("#prise_axe"):
            pairs.add(tuple(sorted((iid, iid[:-len("_axe")]))))
        if iid.startswith("car_") and iid.endswith("#roue"):
            pairs.add(tuple(sorted((iid, "tube_" + iid.split("#")[0][4:]))))
        if iid.startswith("lune_entree_") and iid.endswith("#fou"):
            pre = iid[:-len("#fou")]
            pairs.add(tuple(sorted((pre + "#w1", iid))))
            pairs.add(tuple(sorted((iid, pre + "#w2"))))
    for a, b in pairs:
        for x in (a, b):
            if x not in by_id or classify(by_id[x], hubs)["kind"] != "gear":
                raise SceneError(f"couple {a} / {b} : {x} n'est pas une roue droite")
    return sorted(pairs)


def teeth_m(it, hubs):
    c = classify(it, hubs)
    return c["teeth"], float(c["m"])


def centre_distance(z1, z2, m, mesh="external"):
    return m * (z2 - z1) / 2 if mesh == "internal" else m * (z1 + z2) / 2


def is_fixed_point(iid, hubs):
    """Points exacts par construction (axes de tour, moyeux, pile centrale, prises, sortie du Saros, axe M)."""
    return (iid.startswith("axe_") or iid in hubs or iid.startswith("tube_") or iid.endswith("#prise")
            or iid.endswith("#prise_axe") or iid == "saros#a2"
            or (iid.startswith("lune_entree_") and iid.endswith("#w2")))


def snap_centres(items, by_id, hubs, pairs):
    """Ajuste les centres (arrondis au µm) pour que chaque couple droit soit à l'entraxe exact (Newton de norme
    minimale, points fixes conservés). Modifie les items en place ; renvoie un rapport."""
    refs = []  # (item, clé, indice de nœud)
    nodes = []
    for it in items:
        for k in (("p", "q") if it["kind"] == "rod" else ("c",)):
            pt = it[k]
            n = next((i for i, nd in enumerate(nodes) if math.dist(nd["xy"], pt) < SNAP_TOL), None)
            if n is None:
                nodes.append({"xy": [float(pt[0]), float(pt[1])], "fixed": False, "ids": []})
                n = len(nodes) - 1
            nodes[n]["ids"].append(it["id"])
            if k == "c" and is_fixed_point(it["id"], hubs):
                if nodes[n]["fixed"] and math.dist(nodes[n]["xy"], pt) > 1e-9:
                    raise SceneError(f"deux points fixes différents confondus près de {pt}")
                nodes[n]["fixed"], nodes[n]["xy"] = True, [float(pt[0]), float(pt[1])]
            refs.append((it, k, n))
    node_of = {it["id"]: n for it, k, n in refs if k == "c"}
    cons = []
    for a, b in pairs:
        za, m = teeth_m(by_id[a], hubs)
        zb, mb = teeth_m(by_id[b], hubs)
        if abs(m - mb) > 1e-12:
            raise SceneError(f"{a} / {b} : modules différents ({m}, {mb})")
        cons.append((node_of[a], node_of[b], centre_distance(za, zb, m), a, b))
    free = sorted({n for i, j, *_ in cons for n in (i, j) if not nodes[n]["fixed"]})
    col = {n: 2 * k for k, n in enumerate(free)}
    X0 = {n: np.array(nodes[n]["xy"]) for n in range(len(nodes))}
    X = {n: X0[n].copy() for n in X0}
    for _ in range(60):
        f = np.array([np.linalg.norm(X[i] - X[j]) - d for i, j, d, *_ in cons])
        if np.max(np.abs(f)) < 1e-12:
            break
        J = np.zeros((len(cons), 2 * len(free)))
        for r, (i, j, d, *_) in enumerate(cons):
            g = (X[i] - X[j]) / np.linalg.norm(X[i] - X[j])
            if i in col:
                J[r, col[i]:col[i] + 2] = g
            if j in col:
                J[r, col[j]:col[j] + 2] = -g
        dx = np.linalg.lstsq(J, -f, rcond=None)[0]
        for n in free:
            X[n] = X[n] + dx[col[n]:col[n] + 2]
    worst = max(abs(np.linalg.norm(X[i] - X[j]) - d) for i, j, d, *_ in cons)
    if worst > 1e-9:
        bad = [(a, b) for i, j, d, a, b in cons if abs(np.linalg.norm(X[i] - X[j]) - d) > 1e-9]
        raise SceneError(f"entraxes non atteints (écart {worst:.3g} mm) : {bad[:5]}")
    moved = max((float(np.linalg.norm(X[n] - X0[n])) for n in free), default=0.0)
    if moved > 0.01:
        raise SceneError(f"ajustement des entraxes trop grand : {moved:.4f} mm")
    for it, k, n in refs:
        it[k] = [float(X[n][0]), float(X[n][1])]
    return {"couples": len(cons), "noeuds_libres": len(free), "deplacement_max_mm": round(moved, 6),
            "ecart_entraxe_max_mm": float(worst)}


def place_hub_pins(items, by_id, arch):
    """Pignons couchés des tringles de moyeu à exactement 17,2 mm des centres des couronnes (après ajustement) ;
    pignons d'arrivée des renvois de moyeu du côté qui garde le sens (place_arrival_pin). Renvoie le rapport des
    renvois modifiés."""
    hubs = arch["moyeux"]
    report = {}
    for it in items:
        iid = it["id"]
        if iid.endswith("#bus#rod"):
            tid = iid[:-len("#bus#rod")]
            hub = arch["trains_places"][TRAIN_ALIAS.get(tid, tid)]["hub"]
            hc, tc = hubs[hub]["c"], by_id[tid + "#bus#cour"]["c"]
            u = unit2(hc, tc)
            p0 = [hc[0] + u[0] * HUB_PIN_AT, hc[1] + u[1] * HUB_PIN_AT]
            p1 = [tc[0] - u[0] * HUB_PIN_AT, tc[1] - u[1] * HUB_PIN_AT]
            it["p"], it["q"] = p0, p1
            by_id[tid + "#bus#pin0"]["c"], by_id[tid + "#bus#pin1"]["c"] = list(p0), list(p1)
        elif it.get("route") in HUB_ROUTES and it["kind"] == "rod":
            hc = hubs[arch_renvoi(arch, it["route"])["hub"]]["c"]
            end = "p" if math.dist(it["p"], hc) < math.dist(it["q"], hc) else "q"
            other = it["q"] if end == "p" else it["p"]
            w = unit2(hc, other)
            pt = [hc[0] + w[0] * HUB_PIN_AT, hc[1] + w[1] * HUB_PIN_AT]
            it[end] = pt
            for x in items:
                if (x.get("route") == it["route"] and x.get("wheel") == "renvoi" and abs(x["r"] - MITRE_R) < 1e-6
                        and math.dist(x["c"], pt) < 0.05):
                    x["c"] = list(pt)
            crown = next((x for x in items if x.get("route") == it["route"] and x.get("wheel") == "renvoi"
                          and abs(x["r"] - CROWN_R) < 1e-6), None)
            if crown is not None:
                rep = place_arrival_pin(it, crown, end, hc, items, by_id, hubs)
                if rep:
                    report[it["route"]] = rep
    return report


def arch_renvoi(arch, rid):
    return next(r for r in arch["renvois"] if r["id"] == rid)


def expand_links(items):
    """Rend explicite la sémantique des liens d'architecture.json (tools/arch_geom.linked), car check.py ne lit que
    des noms exacts : (1) les pièces d'un même `group` (tour : axe L, tube Y, UAK, module) se touchent ;
    (2) un lien vers le nom de base « axe_x » vaut pour toutes les parties de cet axe (axe_x, axe_x#haut,
    axe_x#tubeY, axe_x#bas). Les liens ajoutés vont à la fin (links[0] reste l'arbre porteur). Renvoie leur nombre."""
    groups, axes = {}, {}
    for it in items:
        if it.get("group"):
            groups.setdefault(it["group"], []).append(it["id"])
        if it["id"].startswith("axe_"):
            axes.setdefault(it["id"].split("#")[0], []).append(it["id"])
    n = 0
    for it in items:
        old = [x for x in dict.fromkeys(it.get("links", [])) if x != it["id"]]
        new = list(old)
        for lk in old:
            new += sorted(axes.get(lk, []))
        new += sorted(groups.get(it.get("group"), []))
        new = [x for x in dict.fromkeys(new) if x != it["id"]]
        n += len(new) - len(old)
        it["links"] = new
    return n


def thread_supports(plist):
    """Roues d'axe Z enfilées sur un arbre, un tube ou un axe coaxial qui traverse leur couche : `arbor_r` = plus
    grand rayon de ces supports (parts.bore_radius : alésage = arbor_r + 0,05, même quand build_v2 n'a pas d'index),
    et le support est ajouté à `links` s'il n'y est pas (alésage sur arbre : contact légitime).
    Renvoie {roue: [supports ajoutés]}."""
    sup = [p for p in plist if p["kind"] in ("arbor", "tube", "axis", "misc") and "c" in p
           and p["axis"] == [0.0, 0.0, 1.0]]
    added = {}
    for p in plist:
        if p["kind"] not in ("gear", "crown", "bevel") or p["axis"] != [0.0, 0.0, 1.0] or p.get("mesh") == "internal":
            continue
        z0, z1 = p["z"]
        if p["kind"] == "bevel" and p.get("apex") is not None:  # corps de la conique : d'un seul côté du sommet
            a = mid(p["z"])
            z0, z1 = (a + BEVEL_SPAN[0], a + BEVEL_SPAN[1]) if p["apex"] < 0 else (a - BEVEL_SPAN[1], a - BEVEL_SPAN[0])
        here = sorted((s for s in sup if math.dist(s["c"], p["c"]) < 1e-6 and s["z"][0] < z1 - 1e-9
                       and s["z"][1] > z0 + 1e-9), key=lambda s: s["id"])
        if not here:
            continue
        p["arbor_r"] = max(s["r"] for s in here)
        new = [s["id"] for s in here if s["id"] not in p["links"] and p["id"] not in s["links"]]
        if new:
            p["links"] = p["links"] + new
            added[p["id"]] = new
    return added


# ---------------------------------------------------------------------------------------------------------------
# Pièces de scène : géométrie, mouvement, libellés
# ---------------------------------------------------------------------------------------------------------------

ROLE_FR = {"menante": "menante", "menee": "menée", "fou": "pignon fou", "reprise": "reprise du tube Y",
           "reprise_fou": "pignon fou de reprise"}
PITCH_PIN = BEVEL_M * PIN_TEETH / 2   # 4,8 mm : rayon primitif d'un pignon couché ou d'une conique de 24
TIP_PIN = PITCH_PIN + BEVEL_M         # 5,2 mm
BEVEL_SPAN = (2.0, TIP_PIN)           # étendue d'une conique d'onglet le long de son axe, depuis le sommet
# côté du corps d'une conique verticale ajoutée (« ~z ») : zr = sommet + BEVEL_SPAN (au-dessus) ou − (au-dessous)


def motion_fields(d):
    """Champs de mouvement de scene.json (CONTRACT § 2 ; ephem : angle = scale · value + phase, scale = phys · base)."""
    if d["motion"] == "linear":
        return {"motion": "linear", "rate": float(d["signed"]), "rate_exact": str(d["signed"]), "phys": d["phys"]}
    if d["motion"].startswith("ephem:"):
        return {"motion": d["motion"], "rate": float(d["mean"]), "rate_exact": str(d["mean"]), "phys": d["phys"],
                "scale": d["scale"]}
    return {"motion": "fixed", "rate": 0.0, "rate_exact": "0", "phys": 1}


def collection_of(iid, it):
    if it.get("block"):
        return "V2_Blocs"
    if iid.startswith("axe_"):
        return "V2_Tours"
    if it.get("route") or iid.startswith(("car_", "tube_", "lune_entree_")):
        return "V2_Renvois"
    return "V2_Trains"


def fr(x):
    """Nombre décimal à la française (virgule)."""
    return "" if x is None else f"{float(x):g}".replace(".", ",")


def label_of(it, cls, arch):
    """Libellé français d'une pièce."""
    iid, kind = it["id"], cls["kind"]
    if kind == "block":
        return arch["blocs"].get(iid, {}).get("role", "à dessiner")
    what = {"gear": f"roue de {cls.get('teeth')} dents (m {fr(cls.get('m'))})",
            "crown": f"couronne de {CROWN_TEETH} dents (m {fr(BEVEL_M)})",
            "bevel": f"conique de {PIN_TEETH} dents (m {fr(BEVEL_M)})", "rod": "tringle", "tube": "tube Y de la tour",
            "axis": "axe de tour", "arbor": "arbre", "misc": "tenon fixe du pignon fou"}[kind]
    if cls.get("rod") and kind == "gear":
        what = f"pignon couché de {PIN_TEETH} dents (m {fr(BEVEL_M)})"
    if it.get("train"):
        tid = it["train"]
        key = TRAIN_ALIAS.get(tid, tid)
        if kind == "gear":
            return f"train {key} : {what}, {ROLE_FR.get(it.get('role'), it.get('role'))}"
        return f"train {key} : arbre {it.get('arbor')}"
    if "#bus#" in iid:
        tid = iid.split("#bus#")[0]
        return f"tringle de moyeu vers le train {TRAIN_ALIAS.get(tid, tid)} : {what}"
    if iid in arch["moyeux"]:
        h = arch["moyeux"][iid]
        return f"moyeu {iid} (arbre {h['src']}) : {what}"
    if it.get("route"):
        return f"renvoi {it['route']} : {what}"
    if iid.startswith("car_"):
        return f"carrousel ({iid.split('#')[0][4:]}) : {what}"
    if iid.startswith("tube_"):
        return f"tube de la pile ({iid[5:]}) : {what}"
    if iid.startswith("lune_entree_"):
        return f"entrée du bloc Lune ({iid.split('#')[0][12:]}) : {what}"
    names = {"axe_Y": "arbre Y (année)", "axe_J": "arbre-jour J", "axe_soleil": "arbre du Soleil vrai (pile centrale)"}
    if iid in names:
        return names[iid]
    if iid.startswith("axe_"):
        p = iid.split("#")[0][4:]
        suffix = {"haut": "tube Y (Ø 8) autour de l'arbre L, jusqu'au module vectoriel",
                  "bas": "arbre L prolongé vers la précession",
                  "tubeY": "tube Y (reprise)"}.get(iid.split("#")[1] if "#" in iid else "", "arbre L (longitude moyenne)")
        return f"tour {p} : {suffix}"
    return what


def base_part(it, cls, d, arch):
    """Pièce de scène d'un item : géométrie brute de l'item (centres ajustés), mouvement, liens."""
    iid = it["id"]
    p = {"id": iid, "kind": cls["kind"], "source": iid, "collection": collection_of(iid, it),
         "label": label_of(it, cls, arch)}
    if it["kind"] == "rod":
        u = unit2(it["p"], it["q"])
        p.update(p=list(it["p"]), q=list(it["q"]), z=list(it["z"]), r=it["r"], axis=[u[0], u[1], 0.0])
    else:
        p.update(c=list(it["c"]), z=list(it["z"]), r=it["r"], axis=[0.0, 0.0, 1.0])
        if "r_in" in it:
            p["r_in"] = it["r_in"]
    if "teeth" in cls:
        p.update(teeth=int(cls["teeth"]), m=float(cls["m"]), mesh=cls["mesh"])
        if cls["kind"] == "gear" and not cls.get("rod"):
            p["width"] = round(p["z"][1] - p["z"][0], 6)
    if it.get("block"):
        p["contenu"] = arch["blocs"].get(iid, {}).get("contenu", [])
    p["links"] = [x for x in dict.fromkeys(it.get("links", [])) if x != iid]
    p["meshes_with"] = []
    p["engages"] = []
    p.update(motion_fields(d))
    p["phase"] = 0.0
    return p


def refine_wheel(p, it, cls, by_id, hubs):
    """Données de forme des roues de renvoi. Comme dans architecture.json (et parts.py), z = la couche : son milieu
    est la hauteur de l'axe des tringles. Couronne : `face` (+1 : denture vers +Z, pignon au-dessus), `pitch_z`.
    Pignon couché : axe de sa tringle (`rod`). Conique d'onglet : c = sommet (bout de tringle), `apex` = côté du
    sommet le long de l'axe par rapport au corps (+1 : sommet côté +axe, corps vers −axe), `apex_point`."""
    iid, kind = it["id"], cls["kind"]
    apex = mid(it["z"])
    if kind == "crown":
        face = crown_face(it, by_id, hubs)
        p.update(face=face, pitch_z=apex - face * PITCH_PIN)
    elif cls.get("rod"):
        rod = by_id[cls["rod"]]
        u = unit2(rod["p"], rod["q"])
        p.update(axis=[u[0], u[1], 0.0], rod=cls["rod"])
        if kind == "gear":  # pignon couché, centré sur l'axe de la tringle
            p["width"] = PIN_WIDTH
        else:  # conique couchée : sommet au bout de la tringle, corps vers l'intérieur de la tringle
            sigma = 1 if math.dist(it["c"], rod["p"]) < math.dist(it["c"], rod["q"]) else -1
            p.update(apex=-sigma, apex_point=[it["c"][0], it["c"][1], apex], end=("p" if sigma > 0 else "q"),
                     width=BEVEL_SPAN[1] - BEVEL_SPAN[0], pitch_angle_deg=45.0)
    elif kind == "bevel":  # conique d'onglet sur l'arbre du carrousel : corps au-dessus du sommet
        p.update(apex=-1, apex_point=[it["c"][0], it["c"][1], apex], width=BEVEL_SPAN[1] - BEVEL_SPAN[0],
                 pitch_angle_deg=45.0)
    elif iid.endswith("#prise") or iid.endswith("#prise_axe"):
        p["z"] = [it["z"][0], it["z"][0] + 3.0]  # plan de prise au bas de la couche, sous les tringles
        p["width"] = 3.0
    return p


# ---------------------------------------------------------------------------------------------------------------
# Pièces implicites, contacts couronne/conique, phases
# ---------------------------------------------------------------------------------------------------------------

def copy_motion(src):
    return {k: src[k] for k in ("motion", "rate", "rate_exact", "phys", "scale") if k in src}


def synth_part(sid, src_id, coll, label, c, z, axis, kind, motion, links, engages, **extra):
    p = {"id": sid, "kind": kind, "source": src_id, "synth": True, "collection": coll, "label": label,
         "c": [float(c[0]), float(c[1])], "z": [float(z[0]), float(z[1])], "r": MITRE_R, "axis": list(axis),
         "teeth": PIN_TEETH, "m": BEVEL_M, "mesh": "crown" if kind == "gear" else "bevel",
         "links": list(dict.fromkeys(links)), "meshes_with": [], "engages": list(engages)}
    p.update(motion)
    p["phase"] = 0.0
    p.update(extra)
    return p


def add_synth(parts, items, by_id):
    """Pignons couchés d'arrivée (« ~pin ») et coniques d'en face des renvois d'angle (« ~z »)."""
    new = []
    for rid in HUB_ROUTES:
        crown = next((x for x in items if x.get("route") == rid and x.get("wheel") == "renvoi"
                      and abs(x["r"] - CROWN_R) < 1e-6), None)
        if crown is None:
            continue
        rod = parts[f"{rid}#r0"]
        sid = crown["id"] + "~pin"
        new.append(synth_part(sid, crown["id"], rod["collection"],
                              f"renvoi {rid} : pignon couché de {PIN_TEETH} dents (m {fr(BEVEL_M)}) de la couronne d'arrivée",
                              crown["_pin"], rod["z"], rod["axis"], "gear",
                              copy_motion(rod), [rod["id"], crown["id"]] + parts[crown["id"]]["links"], [crown["id"]],
                              width=PIN_WIDTH, rod=rod["id"]))
        parts[crown["id"]]["engages"].append(sid)
    loose = []
    for p in [q for q in parts.values() if q["kind"] == "bevel" and "rod" in q]:
        end, apex = p["apex_point"][:2], p["apex_point"][2]
        sigma = 1 if p["end"] == "p" else -1
        mates = [q for q in parts.values() if q["kind"] == "bevel" and "rod" not in q
                 and math.dist(q["apex_point"][:2], end) < 1e-6 and abs(q["apex_point"][2] - apex) < 1e-6]
        if not mates:
            # un arbre vertical distinct de chaque côté du sommet reçoit sa conique (ex. lunette#z0 au-dessus de
            # geo_jupiter#z0, deux coniques sur la même conique couchée) ; on regarde d'abord le côté qui garde
            # le sens (h = −σ ; onglet : phys_tringle = −phys_z · σ · h) ; un arbre placé du mauvais côté donne
            # une conique dont le sens est refusé plus bas (échec bruyant, pas d'omission silencieuse)
            used = set()
            for h in (-sigma, sigma):
                zr = [apex + BEVEL_SPAN[0], apex + BEVEL_SPAN[1]] if h > 0 else [apex - BEVEL_SPAN[1], apex - BEVEL_SPAN[0]]
                sup = sorted([x for x in items if x["kind"] == "cyl" and not x.get("block") and x["id"] != p["id"]
                              and x["id"] not in used and math.dist(x["c"], end) < 1e-6
                              and (not x.get("wheel") or x["id"].endswith("#prise"))
                              and x["z"][0] <= zr[0] + 1e-6 and x["z"][1] >= zr[1] - 1e-6],
                             key=lambda x: (bool(x.get("wheel")), x["id"]))
                if not sup:
                    continue
                sp = parts[sup[0]["id"]]
                used.add(sp["id"])
                q = synth_part(p["id"] + ("~z" if h == -sigma else "~z2"), p["id"], p["collection"],
                               f"{p['label'].split(' : ')[0]} : conique de {PIN_TEETH} dents (m {fr(BEVEL_M)}) sur "
                               f"l'arbre {sp['id']}", end, p["z"], [0.0, 0.0, 1.0], "bevel", copy_motion(sp),
                               [p["id"], sp["id"], p["rod"]] + p["links"], [p["id"]], apex=-h,
                               apex_point=[end[0], end[1], apex], width=BEVEL_SPAN[1] - BEVEL_SPAN[0],
                               pitch_angle_deg=45.0, support=sp["id"])
                new.append(q)
                mates.append(q)
            if not mates:
                loose.append(p["id"])  # partenaire hors de la scène (cadran de faces.py ou bloc non dessiné)
                continue
        for q in mates:
            hq = -q["apex"]  # côté du corps de la conique verticale (+1 : au-dessus du sommet)
            if p["phys"] != -q["phys"] * sigma * hq:
                raise SceneError(f"{p['id']} / {q['id']} : sens incompatible au renvoi d'angle")
            if q["motion"] != p["motion"] or q["rate_exact"] != p["rate_exact"]:
                raise SceneError(f"{p['id']} / {q['id']} : coniques d'onglet à des vitesses différentes")
            p["engages"].append(q["id"])
            if p["id"] not in q["engages"]:
                q["engages"].append(p["id"])
    for q in new:
        parts[q["id"]] = q
    return [q["id"] for q in new], sorted(loose)


def crown_engagements(parts, items, by_id, arch):
    """Contacts couronne / pignon couché (moyeux, tringles de moyeu, renvois de moyeu), vérifiés (taux 24/96, sens)."""
    hubs = arch["moyeux"]
    pairs = []
    for it in items:
        iid = it["id"]
        if iid.endswith("#bus#pin0"):
            tid = iid[:-len("#bus#pin0")]
            pairs.append((arch["trains_places"][TRAIN_ALIAS.get(tid, tid)]["hub"], iid))
        elif iid.endswith("#bus#pin1"):
            pairs.append((iid[:-len("#bus#pin1")] + "#bus#cour", iid))
        elif it.get("route") in HUB_ROUTES and parts[iid]["kind"] == "gear":
            pairs.append((arch_renvoi(arch, it["route"])["hub"], iid))
    pairs += [(p["source"], p["id"]) for p in parts.values() if p.get("synth") and p["id"].endswith("~pin")]
    for cr, pin in pairs:
        C, Pn = parts[cr], parts[pin]
        u = Pn["axis"]
        expect = crown_rule(C["phys"], C["face"], u, (Pn["c"][0] - C["c"][0], Pn["c"][1] - C["c"][1]))
        if Pn["phys"] != expect:
            raise SceneError(f"{cr} / {pin} : sens du pignon couché {Pn['phys']} ≠ {expect}")
        if abs(F(Pn["rate_exact"])) * PIN_TEETH != abs(F(C["rate_exact"])) * CROWN_TEETH:
            raise SceneError(f"{cr} / {pin} : rapport 96/24 non respecté")
        if abs(math.dist(Pn["c"], C["c"]) - HUB_PIN_AT) > 1e-9:
            raise SceneError(f"{cr} / {pin} : pignon à {math.dist(Pn['c'], C['c'])} mm du centre (≠ 17,2)")
        for a, b in ((cr, pin), (pin, cr)):
            if b not in parts[a]["engages"]:
                parts[a]["engages"].append(b)
    return len(pairs)


def mesh_phase(phi1, beta12, z1, z2):
    """Règle de la v1 (build/am/involute.py, mesh_phase) : angle de la dent 0 de la roue 2 qui s'intercale dans la
    roue 1 (dent 0 à phi1) ; beta12 = direction du centre 1 vers le centre 2."""
    return beta12 + math.pi + math.pi / z2 - (z1 / z2) * (phi1 - beta12)


def assign_phases(parts):
    """Phases des roues droites engrenées (forêt de couples ; racine de chaque composante : phase 0)."""
    done = {}
    for pid in sorted(k for k, p in parts.items() if p["meshes_with"]):
        if pid in done:
            continue
        done[pid] = 0.0
        stack = [pid]
        while stack:
            g = stack.pop()
            for o in sorted(parts[g]["meshes_with"]):
                if o in done:
                    continue
                a, b = parts[g], parts[o]
                beta = math.atan2(b["c"][1] - a["c"][1], b["c"][0] - a["c"][0])
                ph = mesh_phase(done[g], beta, a["teeth"], b["teeth"])
                pitch = TWO_PI / b["teeth"]
                done[o] = ph - pitch * math.floor(ph / pitch)
                stack.append(o)
    for pid, ph in done.items():
        parts[pid]["phase"] = round(ph, 12)
    return len(done)


def wrap_to(x, period):
    return x - period * math.floor(x / period)


def lying(p):
    return abs(p["axis"][2]) < 0.5


def engage_phase(known, other, phi):
    """Phase de `other` qui fait tomber une de ses dents dans un creux de `known` (phase phi) à jours = 0.

    Conventions de parts.py : dent 0 sur +X de construction ; couronne : dents centrées sur k·2π/96 (le retournement
    face −1 garde cet ensemble) ; pièce couchée d'axe u : angle compté de e1 = ẑ × u vers +Z (rotation directe
    autour de u). Couronne C (face f, phase φ_C) / pignon P au rayon R = 17,2, azimut α, σ = signe de u·(P − C),
    i = 96/24 ; contact sous le pignon si f = +1 (angle −f·π/2) :  φ_P = −f·π/2 + π/24 + f·σ·i·(φ_C − α) [2π/24].
    Conique couchée B (apex a_B) / conique d'axe Z (apex a_Z), sommet commun : contact sur la génératrice
    −a_B·u − a_Z·ẑ, donc à l'angle −a_Z·π/2 sur B et à l'azimut α_Z de −a_B·u sur Z :
    φ_B = −a_Z·π/2 + π/24 − a_Z·a_B·(φ_Z − α_Z) [2π/24]. Les inverses s'en déduisent (i = 1 pour les coniques)."""
    if "crown" in (known["kind"], other["kind"]):
        C, P = (known, other) if known["kind"] == "crown" else (other, known)
        d = (P["c"][0] - C["c"][0], P["c"][1] - C["c"][1])
        alpha = math.atan2(d[1], d[0])
        s = 1 if P["axis"][0] * d[0] + P["axis"][1] * d[1] > 0 else -1
        f, i = C["face"], C["teeth"] // P["teeth"]
        pp = TWO_PI / P["teeth"]
        base = -f * math.pi / 2 + pp / 2
        if known is C:
            return wrap_to(base + f * s * i * (phi - alpha), pp)
        return wrap_to(alpha + f * s * (phi - base) / i, TWO_PI / C["teeth"])
    B, Z = (known, other) if lying(known) else (other, known)
    if lying(Z) or not lying(B) or B["teeth"] != Z["teeth"]:
        raise SceneError(f"{known['id']} / {other['id']} : couple de coniques non pris en charge")
    aB, aZ, u = B["apex"], Z["apex"], B["axis"]
    alpha = math.atan2(-aB * u[1], -aB * u[0])
    pz = TWO_PI / B["teeth"]
    base = -aZ * math.pi / 2 + pz / 2
    if known is Z:
        return wrap_to(base - aZ * aB * (phi - alpha), pz)
    return wrap_to(alpha - aZ * aB * (phi - base), pz)


def assign_engage_phases(parts):
    """Phases des contacts « engages » (couronne / pignon couché, coniques d'onglet) : forêt parcourue depuis des
    racines de phase 0 (couronnes et coniques d'axe Z d'abord, ordre des identifiants) ; un cycle incohérent lève
    SceneError. Renvoie le nombre de pièces phasées."""
    done = {}
    nodes = sorted((pid for pid, p in parts.items() if p.get("engages")),
                   key=lambda pid: (lying(parts[pid]), pid))
    for root in nodes:
        if root in done:
            continue
        done[root] = 0.0
        stack = [root]
        while stack:
            g = stack.pop()
            for o in sorted(parts[g]["engages"]):
                ph = engage_phase(parts[g], parts[o], done[g])
                if o in done:
                    per = TWO_PI / parts[o]["teeth"]
                    if abs(wrap_to(ph - done[o] + per / 2, per) - per / 2) > 1e-9:
                        raise SceneError(f"{g} / {o} : phases de contact incohérentes (cycle)")
                    continue
                done[o] = ph
                stack.append(o)
    for pid, ph in done.items():
        parts[pid]["phase"] = round(ph, 12)
    return len(done)


# ---------------------------------------------------------------------------------------------------------------
# Platines, contrôles d'ensemble, assemblage
# ---------------------------------------------------------------------------------------------------------------

PLATE_IDS = {"P1": "platine_P1", "P2": "platine_P2", "P3": "platine_P3", "P4": "platine_P4",
             "cadran avant": "cadran_avant", "cadran arrière": "cadran_arriere"}


def plate_parts(arch, parts):
    """Une platine par entrée de platines_z : contour 450 × 340, trous des arbres, tubes et axes qui la traversent
    (through) ou qui s'y appuient (pivot), rayon de la pièce + 0,3 mm ; trous coaxiaux fusionnés (plus grand rayon)."""
    out = []
    for name, (z0, z1) in arch["platines_z"].items():
        holes = []
        for p in parts:
            if p["kind"] not in ("arbor", "tube", "axis") or "c" not in p or p["axis"] != [0.0, 0.0, 1.0]:
                continue
            a, b = p["z"]
            if a > z1 + 1e-9 or b < z0 - 1e-9:
                continue
            through = a < z1 - 1e-9 and b > z0 + 1e-9
            h = next((x for x in holes if math.dist(x["c"], p["c"]) < 1e-6), None)
            if h is None:
                holes.append({"c": list(p["c"]), "r": round(p["r"] + HOLE_CLEAR, 6), "ids": [p["id"]],
                              "through": through})
            else:
                h["r"] = max(h["r"], round(p["r"] + HOLE_CLEAR, 6))
                h["ids"].append(p["id"])
                h["through"] = h["through"] or through
        for h in holes:
            if not (PLATE_X[0] < h["c"][0] - h["r"] and h["c"][0] + h["r"] < PLATE_X[1]
                    and PLATE_Y[0] < h["c"][1] - h["r"] and h["c"][1] + h["r"] < PLATE_Y[1]):
                raise SceneError(f"{name} : trou hors du contour en {h['c']}")
        holes.sort(key=lambda h: (h["c"][0], h["c"][1]))
        x0, x1 = PLATE_X
        y0, y1 = PLATE_Y
        out.append({"id": PLATE_IDS[name], "kind": "plate", "source": f"platines_z/{name}", "collection": "V2_Platines",
                    "label": f"platine {name}" if name.startswith("P") else name, "c": [0.0, 0.0], "z": [z0, z1],
                    "size": [x1 - x0, y1 - y0], "outline": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], "holes": holes,
                    "axis": [0.0, 0.0, 1.0], "links": sorted({i for h in holes for i in h["ids"]}), "meshes_with": [],
                    "engages": [], "motion": "fixed", "rate": 0.0, "rate_exact": "0", "phys": 1, "phase": 0.0})
    return out


def check_spur_kinematics(parts, pairs):
    """Chaque couple droit : vitesses dans le rapport inverse des dents, sens opposés (engrènement extérieur)."""
    for a, b in pairs:
        A, B = parts[a], parts[b]
        if A["motion"] != B["motion"]:
            raise SceneError(f"{a} / {b} : mouvements différents ({A['motion']}, {B['motion']})")
        if A["phys"] != -B["phys"]:
            raise SceneError(f"{a} / {b} : même sens pour un engrènement extérieur")
        if A["motion"] == "linear":
            if abs(F(A["rate_exact"])) * A["teeth"] != abs(F(B["rate_exact"])) * B["teeth"]:
                raise SceneError(f"{a} / {b} : vitesses hors du rapport des dents")
        elif A["motion"].startswith("ephem:") and (A["teeth"] != B["teeth"] or A["scale"] != -B["scale"]):
            raise SceneError(f"{a} / {b} : couple non linéaire autre que 1:1")


def jd_gregorian(y, m, d):
    """Jour julien (0 h) d'une date grégorienne (Meeus)."""
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + 2 - a + a // 4 - 1524.5


def rnd(p):
    """Arrondi des coordonnées à 1e-10 mm et des axes à 1e-12 (fichier stable ; entraxes exacts à 1e-9)."""
    for k in ("c", "p", "q", "z", "apex_point", "axis"):
        if k in p:
            p[k] = [round(float(v), 12 if k == "axis" else 10) + 0.0 for v in p[k]]
    for k in ("r", "r_in", "arbor_r", "width", "pitch_z"):
        if k in p:
            p[k] = round(float(p[k]), 9) + 0.0
    for h in p.get("holes", []):
        h["c"] = [round(float(v), 10) + 0.0 for v in h["c"]]
    return p


def build(arch=None, trains=None):
    """Construit le dictionnaire de scene.json (lève SceneError à la moindre incohérence)."""
    import copy
    if arch is None:
        with open(ARCH_PATH) as f:
            arch = json.load(f)
    if trains is None:
        with open(TRAINS_PATH) as f:
            trains = json.load(f)
    S = {s["id"]: s for s in trains["shafts"]}
    items = copy.deepcopy(arch["items"])
    by_id = {it["id"]: it for it in items}
    if len(by_id) != len(items):
        raise SceneError("identifiants d'items en double")
    hubs = arch["moyeux"]
    n_links = expand_links(items)
    drives, report, wheel_arbor = {}, {}, {}
    tids = sorted({it["train"] for it in items if it.get("train")}, key=lambda t: (t == "prec", t))
    for tid in tids:
        wheel_arbor.update(walk_train(tid, items, arch, S, drives, report))
    missing = set(arch["trains_places"]) - set(report)
    if missing:
        raise SceneError(f"trains placés sans pièces : {sorted(missing)}")
    pairs = spur_pairs(items, by_id, hubs)
    snap = snap_centres(items, by_id, hubs, pairs)
    arrivals = place_hub_pins(items, by_id, arch)
    dmap = assign_drives(items, by_id, arch, S, drives, wheel_arbor)
    parts = {}
    for it in items:
        cls = classify(it, hubs)
        p = base_part(it, cls, dmap[it["id"]], arch)
        if cls["kind"] in ("gear", "crown", "bevel") and it.get("wheel") == "renvoi":
            refine_wheel(p, it, cls, by_id, hubs)
        parts[it["id"]] = p
    for pid, p in parts.items():  # le tube Y (bas) entoure l'arbre L : vrai tube, alésage = rayon de l'arbre + jeu
        if pid.endswith("#tubeY") and pid[:-len("#tubeY")] in parts:
            p["r_in"] = parts[pid[:-len("#tubeY")]]["r"] + BORE_CLEAR
    for a, b in pairs:
        parts[a]["meshes_with"].append(b)
        parts[b]["meshes_with"].append(a)
    for p in parts.values():
        p["meshes_with"] = sorted(set(p["meshes_with"]))
    check_spur_kinematics(parts, pairs)
    synth, loose = add_synth(parts, items, by_id)
    n_crown = crown_engagements(parts, items, by_id, arch)
    n_phase = assign_phases(parts)
    if any(p["meshes_with"] and p.get("engages") for p in parts.values()):
        raise SceneError("une pièce à la fois dans un couple droit et dans un contact de couronne ou de conique")
    n_phase_e = assign_engage_phases(parts)
    plist = list(parts.values())
    threaded = thread_supports(plist)
    plist += plate_parts(arch, plist)
    known = {p["id"] for p in plist}
    dropped = {}
    for p in plist:  # noms d'architecture.json sans pièce (ex. « y_arbre ») : retirés des liens, signalés
        bad = [x for x in p["links"] if x not in known]
        if bad:
            dropped[p["id"]] = bad
            p["links"] = [x for x in p["links"] if x in known]
    for p in plist:
        p["engages"] = sorted(set(p["engages"]))
        rnd(p)
    kinds = {}
    for p in plist:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    j0 = 2451545.0
    start = jd_gregorian(2026, 1, 1)
    meta = {
        "title": "Anticythère 2.0 — modèle de scène (pièces, taux exacts, sens, phases)",
        "generated_by": "v2/tools/scene_model.py", "contract": "v2/blender/CONTRACT.md § 3",
        "inputs": ["v2/spec/architecture.json", "v2/spec/trains.json"], "historique": False,
        "conventions": CONVENTIONS,
        "counts": {"parts": len(plist), "items": len(items), "synth": len(synth), "kinds": dict(sorted(kinds.items())),
                   "spur_pairs": len(pairs), "crown_contacts": n_crown, "phased_wheels": n_phase,
                   "phased_engaged_parts": n_phase_e},
        "trains": dict(sorted(report.items())), "ajustement_entraxes": snap, "liens_ignores": dropped,
        "liens_ajoutes": {"groupes_et_axes_de_tour": n_links, "supports_coaxiaux": threaded},
        "renvois_cote_eloigne": arrivals, "coniques_sans_partenaire_dans_la_scene": loose,
        "ephem_keys": sorted({p["motion"][6:] for p in plist if p["motion"].startswith("ephem:")}),
    }
    controller = {"name": "V2_Controleur", "j0": "J2000.0", "j0_jd": j0, "start_date": "2026-01-01",
                  "start_jd": start, "start_jours": start - j0, "end_date": "2027-01-01", "frames": 366, "fps": 24,
                  "step_days": 1}
    return {"meta": meta, "controller": controller, "parts": plist}


CONVENTIONS = {
    "repere": "mm ; X à droite, Y en haut, Z vers l'observateur (face avant) ; repère d'architecture.json",
    "linear": "angle = −2π · phys · |rate| · jours + phase (rad) autour de axis ; rate signé en tours/jour, "
              "rate_exact = fraction exacte ; sur un arbre de trains.json le signe est celui de trains.json "
              "(+ = sens direct), ailleurs rate = phys · |rate|",
    "ephem": "angle = scale · ephem.value(clé, jours) + phase, scale = phys · base ; base = −1 rad/rad pour les "
             "angles (phys = +1 : sens horaire vu de face) ; rate = vitesse moyenne de l'arbre (information)",
    "eot": "renvoi vers_edt : base = −10 · 2π/1440 rad par minute d'équation du temps (1 min = 0,25° d'angle "
           "horaire, ×10 par le couple 120:12 du bloc du temps) : +16,5 min → 41,25° en sens horaire ; le cadran lit ×10",
    "phase": "angle de la dent 0 (sur +X local ; pièce couchée : depuis ẑ × axe vers +Z) à jours = 0 ; couples "
             "droits : règle mesh_phase de la v1 (une dent de la menée dans un creux de la menante) ; contacts "
             "couronne/pignon couché et coniques d'onglet : même règle au point de contact (scene_model.engage_phase)",
    "rod": "axe = direction p → q ; phys et angle autour de cet axe ; pignons et coniques couchés : axe de leur tringle",
    "crown": "96 dents m 0,4 ; z = la couche (son milieu = axe des pignons couchés) ; face = sens de la denture "
             "(+1 vers +Z : pignon au-dessus) ; pitch_z = plan primitif ; pignon couché de 24 centré à 17,2 mm de l'axe",
    "bevel": "conique d'onglet 24 dents m 0,4 (45°) : c et milieu de z = sommet commun du couple (apex_point) ; "
             "apex = côté du sommet le long de l'axe (+1 : sommet côté +axe, corps vers −axe) ; le côté du corps est "
             "choisi pour garder le sens (chaîne « con ») ; un arbre de chaque côté du sommet reçoit sa conique "
             "(« ~z » côté qui garde le sens, « ~z2 » en face) ; pignon couché : z = la couche, largeur 10 m",
    "arrivee": "renvoi de moyeu (lune_Y, j_avant, temps_J, temps_Y) : le pignon couché d'arrivée est du côté de la "
               "couronne qui garde le sens de la source (architecture.json, sens) ; s'il passe au-delà du centre, la "
               "tringle est prolongée jusqu'à lui et l'arbre de la couronne arrêté 1 mm sous la tringle "
               "(meta.renvois_cote_eloigne)",
    "links": "liens des items, plus la sémantique d'arch_geom.linked : pièces d'un même group (tour) et toutes les "
             "parties d'un axe de tour pour un lien vers son nom de base ; plus le support coaxial d'une roue "
             "enfilée ; arbor_r = rayon de ce support (alésage = arbor_r + 0,05 dans parts.py)",
    "tour": "axe_<p> = arbre L (Ø 4) ; axe_<p>#tubeY et axe_<p>#haut = tube Y (Ø 8, kind tube, taux de Y) qui porte "
            "la reprise et la couronne de la tringle de moyeu ; axe_<p>#bas = arbre L prolongé",
    "meshes_with": "couples de roues droites, à l'entraxe exact m·(z1 + z2)/2 (contrôle BVH) ; engages : contacts "
                   "couronne/pignon couché et coniques (vérifiés ici : rapport 96/24, sens par roulement, phases)",
    "synth": "pièces implicites de l'architecture : « ~z » / « ~z2 » conique d'un arbre vertical à un renvoi "
             "d'angle, « ~pin » pignon couché qui mène une couronne d'arrivée",
    "plate": "outline 450 × 340 centré ; holes : arbres, tubes et axes qui traversent (through) ou s'appuient "
             "(pivot) sur la platine, rayon de la pièce + 0,3 mm",
    "block": "enveloppe translucide « à dessiner » ; motion fixed ; label = rôle du bloc",
}


def dumps(scene):
    return json.dumps(scene, ensure_ascii=False, indent=1) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        scene = build()
    except SceneError as e:
        print(f"scene_model : ÉCHEC — {e}", file=sys.stderr)
        return 1
    text = dumps(scene)
    if "--check" in argv:
        with open(OUT_PATH) as f:
            same = f.read() == text
        print("scene.json à jour" if same else "scene.json PÉRIMÉ")
        return 0 if same else 1
    with open(OUT_PATH, "w") as f:
        f.write(text)
    c = scene["meta"]["counts"]
    print(f"écrit {os.path.relpath(OUT_PATH, V2)} : {c['parts']} pièces {c['kinds']}, {c['spur_pairs']} couples "
          f"droits, {c['crown_contacts']} contacts de couronne, {c['synth']} pièces implicites")
    return 0


if __name__ == "__main__":
    sys.exit(main())
