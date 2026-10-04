"""Anticythère 2.0 — module faces : chemins, matériaux, collections et propriétés communes.

Repère machine (contrat § 2) : X à droite vu de face, Y en haut, Z vers l'observateur de la face avant ; 1 unité = 1 mm.
Toutes les pièces mobiles portent les propriétés de l'API partagée : motion, rate, phys, phase, axis, scale, kind,
source, meshes_with, links. La rotation d'une pièce `ephem:<clé>` vaut `scale · valeur + phase` autour de `axis`,
exprimé dans le repère du parent (pose de repos = rotation identité, origine sur l'axe de rotation).
"""
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
for _p in (V2 / "tools", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import arch_layout as AL  # noqa: E402,F401  (constantes de conception de la v2, réexportées)

TAU = 2.0 * math.pi

# Clé d'éphéméride → arbre de trains.json qui la réalise (pour le taux moyen informatif `rate`).
KEY_SHAFT = {"lambda_sun": "sun_geo", "lambda_moon": "moon_true", "node": "moon_node", "perigee": "moon_perigee",
             "elong": "moon_phase", "prec": "precession_ring", "gmst": "gmst", "mean_solar": "J",
             "jup_io": "io", "jup_europa": "europa", "jup_ganymede": "ganymede", "jup_callisto": "callisto",
             "jup_nu": "nu", "lunette": "jupiter_geo", "cal_ring": "cal_sum", "weekday": "W", "saros": "saros",
             "exeligmos": "exeligmos", "eot": "eot_dial", "helio_earth": "orrery_earth"}
for _pl in ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"):
    KEY_SHAFT[f"lambda_geo_{_pl}"] = f"{_pl}_geo"
    KEY_SHAFT[f"helio_{_pl}"] = f"orrery_{_pl}"
EXTRA_RATE = {"years": 1.0 / (100 * 365.2425), "gamma": 0.0}

_RATES = None


def load_arch():
    with open(V2 / "spec" / "architecture.json", encoding="utf-8") as f:
        return json.load(f)


def key_rate(key):
    """Taux moyen (tours/jour, signé) de la valeur d'une clé d'éphéméride, d'après trains.json."""
    global _RATES
    if _RATES is None:
        with open(V2 / "spec" / "trains.json", encoding="utf-8") as f:
            tr = json.load(f)
        _RATES = {s["id"]: float(Fraction(s["rate_turns_per_day"])) for s in tr["shafts"]
                  if s.get("rate_turns_per_day") is not None}
    if key in EXTRA_RATE:
        return EXTRA_RATE[key]
    return _RATES.get(KEY_SHAFT.get(key, ""), 0.0)


def scene_part(pid):
    """Pièce de spec/scene.json (si le fichier existe déjà), sinon None."""
    p = V2 / "spec" / "scene.json"
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return next((q for q in json.load(f).get("parts", []) if q.get("id") == pid), None)
    except (OSError, ValueError):
        return None


def crank_rate():
    """Tours de manivelle par jour : taux de la tringle `manivelle#r0` (scene.json), sinon 4 (tringle de moyeu)."""
    part = scene_part("manivelle#r0")
    return abs(float(part["rate"])) if part and part.get("rate") else 4.0


# ---------------------------------------------------------------- propriétés
def tag(ob, kind, motion="fixed", key=None, scale=-1.0, axis=(0.0, 0.0, 1.0), phase=0.0, source="",
        links=(), meshes_with=(), rate=None, phys=None, **extra):
    """Pose les propriétés de l'API partagée. `key` → motion 'ephem:<key>'.
    phys = sens visible : +1 si la pièce tourne en moyenne dans le sens négatif autour de son axe
    (horaire vu de face pour l'axe +Z), −1 sinon ; pour une valeur oscillante, +1 par défaut."""
    if key is not None:
        motion = f"ephem:{key}"
        if rate is None:
            rate = key_rate(key)
        if phys is None:
            s = scale * rate
            phys = 1 if s <= 0 else -1
    ob["motion"] = motion
    ob["rate"] = float(rate or 0.0)
    ob["phys"] = int(phys if phys is not None else 1)
    ob["phase"] = float(phase)
    ob["axis"] = [float(a) for a in axis]
    ob["scale"] = float(scale)
    ob["kind"] = kind
    ob["source"] = source
    ob["meshes_with"] = list(meshes_with)
    ob["links"] = list(links)
    for k, v in extra.items():
        ob[k] = v
    return ob


# ---------------------------------------------------------------- matériaux
LOCAL_MATS = {  # clé : (couleur, métal, rugosité, alpha)
    "dial": ((0.80, 0.60, 0.30), 1.0, 0.35, 1.0), "ring": ((0.85, 0.83, 0.78), 1.0, 0.30, 1.0),
    "gold": ((1.00, 0.76, 0.33), 1.0, 0.25, 1.0), "silver": ((0.90, 0.90, 0.92), 1.0, 0.20, 1.0),
    "steel": ((0.10, 0.13, 0.25), 0.9, 0.30, 1.0), "engrave": ((0.04, 0.03, 0.02), 0.2, 0.60, 1.0),
    "dark": ((0.02, 0.02, 0.025), 0.0, 0.60, 1.0), "light": ((0.95, 0.93, 0.85), 0.0, 0.40, 1.0),
    "oak": ((0.45, 0.28, 0.13), 0.0, 0.60, 1.0), "glass": ((0.85, 0.92, 0.95), 0.0, 0.05, 0.12),
    "red": ((0.75, 0.08, 0.05), 0.0, 0.45, 1.0), "enamel": ((0.05, 0.08, 0.25), 0.0, 0.30, 1.0),
    "earth": ((0.10, 0.30, 0.75), 0.0, 0.50, 1.0), "p_mercury": ((0.55, 0.55, 0.55), 0.3, 0.5, 1.0),
    "p_venus": ((0.93, 0.85, 0.60), 0.0, 0.5, 1.0), "p_mars": ((0.80, 0.25, 0.10), 0.0, 0.5, 1.0),
    "p_jupiter": ((0.80, 0.62, 0.42), 0.0, 0.5, 1.0), "p_saturn": ((0.90, 0.80, 0.50), 0.0, 0.5, 1.0),
    "p_uranus": ((0.50, 0.85, 0.90), 0.0, 0.5, 1.0), "p_neptune": ((0.20, 0.35, 0.90), 0.0, 0.5, 1.0),
    "p_moon": ((0.85, 0.85, 0.80), 0.0, 0.6, 1.0),
}
ALIASES = {"dial": ("brass", "laiton", "bronze"), "gold": ("gold", "or"), "silver": ("silver", "argent"),
           "steel": ("steel", "acier"), "oak": ("wood", "oak", "bois"), "glass": ("glass", "verre"),
           "enamel": ("dial_dark",), "engrave": ("engraving", "gravure")}  # 'text' de parts.py (or) : peu lisible


def _make_mat(name, col, metal, rough, alpha):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (col[0], col[1], col[2], alpha)  # couleur d'affichage (Workbench)
    mat.metallic, mat.roughness = metal, rough
    nt = getattr(mat, "node_tree", None)
    pb = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None) if nt else None
    if pb is not None:
        pb.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
        pb.inputs["Metallic"].default_value = metal
        pb.inputs["Roughness"].default_value = rough
        if alpha < 1.0:
            pb.inputs["Alpha"].default_value = alpha
            if "Transmission Weight" in pb.inputs:
                pb.inputs["Transmission Weight"].default_value = 1.0
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "BLENDED"
    return mat


def materials(mats=None):
    """Jeu de matériaux du module : ceux fournis (`mats`, p. ex. parts.materials()) quand la clé ou un alias
    existe, sinon un petit jeu local préfixé V2F_."""
    mats = dict(mats or {})
    out = {}
    for k, (col, metal, rough, alpha) in LOCAL_MATS.items():
        got = mats.get(k) or next((mats[a] for a in ALIASES.get(k, ()) if a in mats), None)
        out[k] = got if isinstance(got, bpy.types.Material) else _make_mat("V2F_" + k, col, metal, rough, alpha)
    return out


# ---------------------------------------------------------------- collections
COLL_NAMES = {"avant": "V2_Faces_Avant", "arriere": "V2_Faces_Arriere", "couvercle": "V2_Couvercle",
              "caisse": "V2_Caisse"}
COLL_ALIASES = {"couvercle": ("V2_Orrery",), "caisse": ("V2_Caisse",)}


def _child(root, name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in root.children and c.name not in bpy.context.scene.collection.children:
        root.children.link(c)
    return c


def collections(colls=None):
    """Collections du module (copie : le dict de l'appelant n'est pas modifié). `colls` peut fournir 'avant',
    'arriere', 'couvercle', 'caisse', ou les collections de build_v2 : 'V2_Faces' (parente des faces avant et
    arrière), 'V2_Orrery' (couvercle), 'V2_Caisse' ; les manquantes sont créées sous 'V2_Faces'."""
    src = dict(colls or {})
    root = src.get("faces") or src.get("V2_Faces")
    if root is None:
        root = bpy.data.collections.get("V2_Faces") or bpy.data.collections.new("V2_Faces")
        if root.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(root)
    out = {"faces": root}
    for k, name in COLL_NAMES.items():
        got = src.get(k) or next((src[a] for a in COLL_ALIASES.get(k, ()) if src.get(a) is not None), None)
        out[k] = got if got is not None else _child(root, name)
    return out
