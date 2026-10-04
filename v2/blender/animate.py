"""Anticythère 2.0 — module animate : contrôleur de temps, pilotes « linear », images clés « ephem: ».

Contrat (v2/blender/CONTRACT.md § 2-3) :
- l'Empty « V2_Controleur » porte « jours » = jours depuis J2000.0, animé linéairement : image 1 = date de départ,
  1 image par jour (images 1 … days ; « jours » est clé jusqu'à l'image 1 + days, extrapolation linéaire) ;
- motion == 'linear'      → pilote Blender : angle = −2π · phys · |rate| · jours + phase, autour de « axis » ;
- motion == 'ephem:<clé>' → images clés cuites (une par step_days) : angle = scale · ephem.value(clé, jours) + phase,
  déroulé (pas de saut de 2π), interpolation LINEAR ;
- motion == 'fixed'       → rien.
Canal piloté (drive_channel), dans cet ordre :
1. convention de parts.py : objet en mode 'XYZ' portant « spin_index » (0 ou 2) dont la composante pilotée tourne
   déjà autour de ±« axis » (rotation_euler = (angle, beta, gamma) ou (0, 0, ±angle)) → on pilote directement
   rotation_euler[spin_index] (signe −1 autour de −axis) ; la phase posée au repos par parts.py est remplacée,
   jamais ajoutée (un pivot la compterait deux fois) ;
2. axe +Z : rotation_euler[2] (mode XYZ, donc autour du Z du parent) ; axe −Z : idem avec le signe opposé ;
3. autre axe (pose de repos = rotation identité, convention de faces) : un Empty pivot « V2_Pivot_<nom> » (mode
   ZYX, Z local aligné sur l'axe) devient le parent et l'on pilote son Z local.

Déroulage des clés « ephem: » : ephem.values est déroulé sur une grille fine (pas ≤ FINE_STEP), puis lu aux
instants des clés. Un déroulage sur les seules clés journalières replierait les clés rapides (Io, ~203°/j, tournerait
à l'envers entre deux images ; gmst et mean_solar seraient presque figés).

Précision : les variables de pilote et les images clés sont en float32. |rate| et la phase sont donc des constantes
littérales (double) dans l'expression, l'angle est ramené dans ]−2π, 2π[ par fmod, et « jours » vaut exactement
j0 + n aux images entières (j0 demi-entier, exact en float32) : erreur ≤ 3e-7 rad aux images entières. Aux
sous-images, « jours » est arrondi (~5e-4 j) mais de la même façon pour toutes les pièces (engrènements cohérents).
Les clés cuites sont centrées sur 0 : erreur ≈ |angle| · 6e-8 (≤ 4e-6 rad pour la Lune, ≤ 7e-5 rad pour gmst,
mean_solar et Io, qui font ~1 tour par jour sur 366 jours).
"""
import math
import sys
from pathlib import Path

CONTROLLER = "V2_Controleur"
PIVOT_PREFIX = "V2_Pivot_"
TWO_PI = 2.0 * math.pi
NON_ANGLE_KEYS = frozenset({"eot", "gamma"})  # valeurs non angulaires : ni déroulées ni recentrées
DEFAULT_SCALE = -1.0
FINE_STEP = 1.0 / 32.0  # jour : pas du déroulage (≤ 0,2 rad pour la clé la plus rapide, ~1 tour/jour)
_TOOLS = Path(__file__).resolve().parents[1] / "tools"


# ------------------------------------------------------------------ dates et éphémérides (sans bpy)

def ephem_module():
    """Importe v2/tools/ephem.py via sys.path (ImportError tant qu'il n'existe pas)."""
    if str(_TOOLS) not in sys.path:
        sys.path.insert(0, str(_TOOLS))
    import ephem  # module du projet (pas PyEphem)
    return ephem


def _jd_gregorian(y, m, d):
    """Jour julien à 0 h d'une date grégorienne (Meeus, ch. 7) ; secours si ephem.py est absent."""
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def jours_from_date(y, m, d):
    """Jours depuis J2000.0 (ephem.jours_from_date si disponible, sinon 0 h de la date)."""
    try:
        mod = ephem_module()
    except ImportError:
        return _jd_gregorian(y, m, d) - 2451545.0
    return float(mod.jours_from_date(y, m, d))


# ------------------------------------------------------------------ angles (fonctions pures)

def linear_angle(rate, phys, phase, jours):
    """Angle (rad) d'une pièce à taux constant : −2π · phys · |rate| · jours + phase (CONTRACT § 2)."""
    return -TWO_PI * phys * abs(rate) * jours + phase


def motion_props(obj):
    """Propriétés de mouvement d'un objet Blender (ou d'un dict), avec leurs valeurs par défaut."""
    g = obj.get
    axis = tuple(float(a) for a in g("axis", (0.0, 0.0, 1.0)))
    return {"motion": str(g("motion", "fixed")), "rate": float(g("rate", 0.0)),
            "phys": float(g("phys", 1.0)), "phase": float(g("phase", 0.0)),
            "scale": float(g("scale", DEFAULT_SCALE)), "axis": axis}


def ephem_key(motion):
    """Clé d'éphéméride de « ephem:<clé> », sinon None."""
    return motion[6:] if motion.startswith("ephem:") else None


def expected_angle_props(props, jours):
    """Angle attendu (rad, non ramené) autour de « axis » ; None pour une pièce fixe."""
    m = props["motion"]
    if m == "linear":
        return linear_angle(props["rate"], props["phys"], props["phase"], jours)
    key = ephem_key(m)
    if key is not None:
        return props["scale"] * float(ephem_module().value(key, jours)) + props["phase"]
    return None


def wrap_pi(x):
    """Ramène un angle (ou une différence d'angles) dans [−π, π[."""
    return (x + math.pi) % TWO_PI - math.pi


def angle_error(a, b):
    """Écart absolu entre deux angles, modulo 2π."""
    return abs(wrap_pi(a - b))


def align_euler(u):
    """(ax, ay) tels que Rx(ax)·Ry(ay)·ẑ = u : en mode 'ZYX' (R = Rx·Ry·Rz), le Z local du pivot suit u."""
    x, y, z = u
    return math.atan2(-y, z), math.asin(max(-1.0, min(1.0, x)))


def axis_mode(axis, tol=1e-9):
    """('z', +1) pour +Z, ('z', −1) pour −Z, sinon ('pivot', (ax, ay)) pour le pivot en mode ZYX."""
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0.0:
        raise ValueError("axe nul")
    x, y, z = x / n, y / n, z / n
    if abs(x) < tol and abs(y) < tol:
        return "z", (1 if z > 0 else -1)
    return "pivot", align_euler((x, y, z))


def spin_axis(euler, index):
    """Direction (repère du parent) de la rotation que produit rotation_euler[index] en mode 'XYZ'
    (R = Rz(c)·Ry(b)·Rx(a)) : index 0 → Rz·Ry·x̂, 1 → Rz·ŷ, 2 → ẑ. Ne dépend pas de la composante pilotée."""
    _a, b, c = (float(v) for v in euler)
    if index == 2:
        return 0.0, 0.0, 1.0
    if index == 1:
        return -math.sin(c), math.cos(c), 0.0
    if index == 0:
        return math.cos(c) * math.cos(b), math.sin(c) * math.cos(b), -math.sin(b)
    raise ValueError(f"spin_index {index!r}")


def linear_expression(rate, phys, phase, sign=1):
    """Expression simple du pilote (seule variable : j = jours) ; constantes en double, résultat ramené par fmod."""
    k = sign * (-TWO_PI * phys * abs(rate))
    p = sign * phase
    return f"fmod({k!r}*j+({p!r}),2*pi)"


def sample_jours(j0, days, step_days):
    """Instants d'échantillonnage (numpy) de j0 à j0 + days inclus, au pas step_days."""
    import numpy as np
    n = int(math.floor(days / step_days + 1e-9))
    jours = j0 + step_days * np.arange(n + 1, dtype=float)
    if jours[-1] < j0 + days - 1e-9:
        jours = np.append(jours, j0 + days)
    return jours


def unwrap_centered(angles):
    """Déroule une suite d'angles (sauts de 2π supprimés) puis la décale d'un multiple de 2π pour centrer son
    étendue sur 0 (les images clés sont en float32 : petites valeurs = meilleure précision)."""
    import numpy as np
    a = np.unwrap(np.asarray(angles, dtype=float))
    mid = 0.5 * (float(a.max()) + float(a.min()))
    return a - TWO_PI * round(mid / TWO_PI)


def center_turns(angles):
    """Décale une suite d'angles déjà continue d'un multiple de 2π pour centrer son étendue sur 0 (sans déroulage :
    deux clés successives peuvent légitimement différer de plus de π)."""
    import numpy as np
    a = np.asarray(angles, dtype=float)
    return a - TWO_PI * round(0.5 * (float(a.max()) + float(a.min())) / TWO_PI)


def continuous_values(key, jours, fine_step=FINE_STEP):
    """ephem.values(clé, jours) ; pour une clé angulaire, valeur brute déroulée sur une grille fine (chaque
    intervalle entre instants coupé en sous-pas ≤ fine_step) puis relue aux instants demandés : le nombre de tours
    entre deux clés est le vrai (pas le repli au plus court de np.unwrap sur la grille grossière)."""
    import numpy as np
    jours = np.asarray(jours, dtype=float)
    eph = ephem_module()
    if key in NON_ANGLE_KEYS or len(jours) < 2:
        return np.asarray(eph.values(key, jours), dtype=float)
    gaps = np.diff(jours)
    sub = max(1, int(math.ceil(float(gaps.max()) / fine_step - 1e-9)))
    fine = (jours[:-1, None] + gaps[:, None] * (np.arange(sub) / sub)[None, :]).ravel()
    fine = np.append(fine, jours[-1])
    return np.unwrap(np.asarray(eph.values(key, fine), dtype=float))[::sub]


def baked_angles(key, scale, phase, jours, cache=None):
    """Angles cuits pour une clé : scale · values(clé, jours) + phase, la valeur brute étant rendue continue
    (continuous_values) avant l'échelle, puis le tout centré d'un multiple de 2π si la clé est angulaire."""
    if cache is not None and key in cache:
        vals = cache[key]
    else:
        vals = continuous_values(key, jours)
        if cache is not None:
            cache[key] = vals
    ang = scale * vals + phase
    return ang if key in NON_ANGLE_KEYS else center_turns(ang)


# ------------------------------------------------------------------ Blender : courbes, contrôleur, pivots

def _linear_enum():
    import bpy
    return bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items["LINEAR"].value


def _fcurve(idb, path, index=0):
    """F-courbe (vidée) de idb pour path[index], créée dans l'action propre de idb si besoin."""
    import bpy
    ad = idb.animation_data or idb.animation_data_create()
    if ad.action is None:
        ad.action = bpy.data.actions.new("V2_Anim_" + idb.name)
    fc = ad.action.fcurve_ensure_for_datablock(idb, path, index=index)
    fc.keyframe_points.clear()
    return fc


def _set_keys(fc, frames, values, extrapolation="CONSTANT"):
    """Pose d'un coup des images clés LINEAR (frames, values)."""
    n = len(frames)
    co = [0.0] * (2 * n)
    co[0::2] = [float(f) for f in frames]
    co[1::2] = [float(v) for v in values]
    fc.keyframe_points.clear()
    fc.keyframe_points.add(n)
    fc.keyframe_points.foreach_set("co", co)
    fc.keyframe_points.foreach_set("interpolation", [_linear_enum()] * n)
    fc.extrapolation = extrapolation
    fc.update()


def ensure_controller(scene, j0, days, frame0=1):
    """Empty V2_Controleur : « jours » clé de (frame0, j0) à (frame0 + days, j0 + days), LINEAR."""
    import bpy
    ctrl = bpy.data.objects.get(CONTROLLER)
    if ctrl is None:
        ctrl = bpy.data.objects.new(CONTROLLER, None)
        ctrl.empty_display_type = "SPHERE"
        ctrl.empty_display_size = 10.0
    if scene not in ctrl.users_scene:
        scene.collection.objects.link(ctrl)
    ctrl["jours"] = float(j0)
    ctrl["j0"] = float(j0)
    ctrl["frame0"] = float(frame0)
    ctrl["jours_par_image"] = 1.0
    fc = _fcurve(ctrl, '["jours"]', 0)
    _set_keys(fc, [frame0, frame0 + days], [j0, j0 + days], extrapolation="LINEAR")
    return ctrl


def _ensure_pivot(obj, euler_xy):
    """Pivot Empty (mode ZYX, Z local = axe, origine = celle de obj) parent de obj ; matrice monde inchangée."""
    import bpy
    from mathutils import Matrix
    par = obj.parent
    if par is not None and par.get("v2_pivot_of") == obj.name:
        return par
    piv = bpy.data.objects.new(PIVOT_PREFIX + obj.name, None)
    piv.empty_display_type = "SINGLE_ARROW"
    piv.empty_display_size = 10.0
    for coll in obj.users_collection:
        coll.objects.link(piv)
    piv["v2_pivot_of"] = obj.name
    piv["axis"] = list(motion_props(obj)["axis"])
    old = obj.matrix_basis.copy()
    piv.parent = par
    piv.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
    piv.rotation_mode = "ZYX"
    piv.location = old.translation
    piv.rotation_euler = (euler_xy[0], euler_xy[1], 0.0)
    basis0 = piv.matrix_basis.copy()
    obj.parent = piv
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = basis0.inverted() @ old
    return piv


def _spin_index_channel(obj, axis, tol=1e-6):
    """(signe, index) si obj suit la convention de parts.py (mode 'XYZ', « spin_index » dont la rotation est
    colinéaire à axis), sinon None."""
    idx = obj.get("spin_index")
    if idx is None or obj.rotation_mode != "XYZ":
        return None
    try:
        idx = int(idx)
        d = spin_axis(obj.rotation_euler, idx)
    except (TypeError, ValueError):
        return None
    n = math.sqrt(sum(a * a for a in axis))
    dot = sum(a * b for a, b in zip(d, axis)) / n if n else 0.0
    return ((1 if dot > 0 else -1), idx) if abs(dot) > 1.0 - tol else None


def drive_channel(obj, create=True):
    """(objet piloté, signe, index de rotation_euler) : convention parts.py (obj, ±1, spin_index), sinon
    (obj, ±1, 2) pour ±Z, sinon (pivot, +1, 2) ; (None, 1, 2) si create=False et qu'aucun pivot n'existe."""
    axis = motion_props(obj)["axis"]
    direct = _spin_index_channel(obj, axis)
    if direct is not None:
        return obj, direct[0], direct[1]
    mode, info = axis_mode(axis)
    if mode == "z":
        if create and obj.rotation_mode != "XYZ":
            obj.rotation_mode = "XYZ"
        return obj, info, 2
    if create:
        return _ensure_pivot(obj, info), 1, 2
    par = obj.parent
    return (par, 1, 2) if par is not None and par.get("v2_pivot_of") == obj.name else (None, 1, 2)


def drive_target(obj, create=True):
    """(objet piloté, signe) — voir drive_channel pour l'index de rotation_euler."""
    tgt, sign, _idx = drive_channel(obj, create)
    return tgt, sign


def add_linear_driver(obj, ctrl):
    """Pilote simple : rotation = fmod(k·j + p, 2π), j = V2_Controleur["jours"]. Renvoie l'objet piloté."""
    p = motion_props(obj)
    tgt, sign, idx = drive_channel(obj)
    tgt.driver_remove("rotation_euler", idx)
    fc = tgt.driver_add("rotation_euler", idx)
    fc.keyframe_points.clear()  # pas de remappage : la valeur du pilote est appliquée telle quelle
    for mod in list(fc.modifiers):
        fc.modifiers.remove(mod)
    drv = fc.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = "j"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "OBJECT"
    var.targets[0].id = ctrl
    var.targets[0].data_path = '["jours"]'
    drv.expression = linear_expression(p["rate"], p["phys"], p["phase"], sign)
    return tgt


def bake_ephem(obj, j0, days, step_days=1, frame0=1, cache=None):
    """Images clés LINEAR (une par step_days) de scale · ephem.value(clé, jours) + phase, déroulées."""
    p = motion_props(obj)
    key = ephem_key(p["motion"])
    tgt, sign, idx = drive_channel(obj)
    tgt.driver_remove("rotation_euler", idx)
    jours = sample_jours(j0, days, step_days)
    ang = sign * baked_angles(key, p["scale"], p["phase"], jours, cache)
    fc = _fcurve(tgt, "rotation_euler", idx)
    _set_keys(fc, frame0 + (jours - j0), ang)
    return tgt


# ------------------------------------------------------------------ mise en place

def setup_animation(scene_bpy, start=(2026, 1, 1), days=366, fps=24, step_days=1, strict=True):
    """Contrôleur + pilotes « linear » + images clés « ephem: » pour tous les objets de la scène portant « motion ».

    Plage : images 1 … days (366 images = 2026-01-01 → 2027-01-01, CONTRACT § 2) ; « jours » et les images clés
    couvrent [j0, j0 + days]. Idempotent (pivots réutilisés, pilotes et clés remplacés). Renvoie des statistiques.
    """
    import time
    t0 = time.perf_counter()
    j0 = jours_from_date(*start)
    scene_bpy.render.fps = int(fps)
    scene_bpy.render.fps_base = 1.0
    scene_bpy.frame_start = 1
    scene_bpy.frame_end = int(days)
    ctrl = ensure_controller(scene_bpy, j0, days, frame0=1)
    objs = [o for o in scene_bpy.objects if "motion" in o and o.name != CONTROLLER]
    stats = {"j0": j0, "linear": 0, "ephem": 0, "fixed": 0, "pivots": 0, "ignored": []}
    cache, known = {}, None
    for o in objs:
        m = str(o["motion"])
        if m.startswith("ephem:") and known is None:
            known = set(ephem_module().KEYS)
        if m == "linear":
            tgt = add_linear_driver(o, ctrl)
            stats["linear"] += 1
        elif m.startswith("ephem:") and ephem_key(m) in known:
            tgt = bake_ephem(o, j0, days, step_days, frame0=1, cache=cache)
            stats["ephem"] += 1
        elif m == "fixed":
            stats["fixed"] += 1
            continue
        else:
            if strict:
                raise ValueError(f"{o.name} : motion inconnu {m!r} (clés d'éphéméride : ephem.KEYS)")
            stats["ignored"].append(o.name)
            continue
        stats["pivots"] += int(tgt is not o)
    scene_bpy.frame_set(1)
    stats["seconds"] = time.perf_counter() - t0
    return stats


# ------------------------------------------------------------------ temps ↔ images, contrôles

def controller():
    """L'Empty V2_Controleur (KeyError s'il n'existe pas)."""
    import bpy
    return bpy.data.objects[CONTROLLER]


def jours_at_frame(frame):
    """Jours depuis J2000.0 à l'image frame (calcul en double)."""
    c = controller()
    return c["j0"] + (frame - c["frame0"]) * c["jours_par_image"]


def frame_for_jours(jours):
    c = controller()
    return c["frame0"] + (jours - c["j0"]) / c["jours_par_image"]


def frame_for_date(y, m, d):
    return frame_for_jours(jours_from_date(y, m, d))


def set_frame_for_date(y, m, d, scene=None):
    """Place la scène à la date (sous-image si besoin) ; renvoie l'image (float)."""
    import bpy
    scene = scene or bpy.context.scene
    f = frame_for_date(y, m, d)
    fi = math.floor(f)
    scene.frame_set(int(fi), subframe=f - fi)
    return f


def expected_angle(obj, frame):
    """Angle attendu (rad, non ramené) de obj autour de son « axis » à l'image frame ; None si fixe.
    Pour « ephem: », c'est la formule exacte (les images clés en sont l'interpolation linéaire au pas step_days)."""
    return expected_angle_props(motion_props(obj), jours_at_frame(frame))


def measured_angle(obj, depsgraph=None):
    """Angle évalué (rad, tel que stocké) de obj autour de son « axis » ; None si rien n'est piloté."""
    tgt, sign, idx = drive_channel(obj, create=False)
    if tgt is None:
        return None
    ev = tgt.evaluated_get(depsgraph) if depsgraph is not None else tgt
    return sign * ev.rotation_euler[idx]


def angle_errors(objs, frame, scene=None):
    """{nom: écart modulo 2π} entre angle évalué et angle attendu à l'image frame (pièces mobiles)."""
    import bpy
    scene = scene or bpy.context.scene
    fi = math.floor(frame)
    scene.frame_set(int(fi), subframe=frame - fi)
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for o in objs:
        exp = expected_angle(o, frame)
        got = measured_angle(o, dg)
        if exp is not None and got is not None:
            out[o.name] = angle_error(got, exp)
    return out


def main():
    """blender -b <fichier> --python-exit-code 1 -P blender/animate.py -- [--start 2026-01-01] [--days 366]
    [--fps 24] [--step 1] [--save out/x.blend]"""
    import argparse
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="animate.py")
    ap.add_argument("--start", default="2026-01-01")
    ap.add_argument("--days", type=int, default=366)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--step", type=float, default=1.0)
    ap.add_argument("--save", default=None)
    a = ap.parse_args(argv)
    y, m, d = (int(s) for s in a.start.split("-"))
    stats = setup_animation(bpy.context.scene, (y, m, d), a.days, a.fps, a.step)
    print("[animate]", stats)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.save).resolve()))


if __name__ == "__main__":
    main()
