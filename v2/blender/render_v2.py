"""Anticythère 2.0 — rendus de la maquette (EEVEE) → v2/out/renders/*.png.

Lancer : BL -b v2/out/v2.blend --python-exit-code 1 -P v2/blender/render_v2.py -- [--quick] [--date 2026-10-04]
         [--only front,back,lid,front34,interior,floors]
Vues : face avant, face arrière (vue de dos), couvercle (vue de dessus), trois quarts, intérieur (caisse, cadrans et
platine P1 masqués), et un rendu par étage (E1…E5, pièces dont la cote z coupe l'étage).
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
for p in (HERE, os.path.join(V2, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
OUT = os.path.join(V2, "out", "renders")


def log(*a):
    print("[v2-rendu]", *a, flush=True)


def opts():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"quick": "--quick" in a, "date": "2026-10-04", "only": None, "anim": None, "step": 2, "res": None}
    for i, x in enumerate(a):
        if x == "--anim":
            o["anim"] = a[i + 1]
        if x == "--step":
            o["step"] = int(a[i + 1])
        if x == "--res":
            o["res"] = tuple(int(v) for v in a[i + 1].split("x"))
        if x == "--date":
            o["date"] = a[i + 1]
        if x == "--only":
            o["only"] = a[i + 1].split(",")
    return o


def look_at(ob, target, up=(0.0, 1.0, 0.0)):
    """Oriente l'objet vers la cible, +Y du monde en haut de l'image (base explicite)."""
    from mathutils import Matrix
    f = (Vector(target) - ob.location).normalized()
    r = f.cross(Vector(up)).normalized()
    u = r.cross(f)
    m = Matrix((r, u, -f)).transposed()
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = m.to_euler("XYZ")


def camera(name, loc, target=None, ortho=None, lens=50.0, rot=None):
    cam = bpy.data.cameras.get("CAM_" + name) or bpy.data.cameras.new("CAM_" + name)
    cam.clip_start, cam.clip_end = 1.0, 20000.0
    if ortho:
        cam.type, cam.ortho_scale = "ORTHO", ortho
    else:
        cam.type, cam.lens = "PERSP", lens
    ob = bpy.data.objects.get("CAM_" + name) or bpy.data.objects.new("CAM_" + name, cam)
    if ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    if rot is not None:
        ob.rotation_euler = rot
    else:
        look_at(ob, target)
    return ob


def lights_world():
    sc = bpy.context.scene
    for name, loc, energy, size in (("L_cle", (450, 350, 800), 4.0e6, 400.0), ("L_remplissage", (-600, 100, 500), 1.6e6, 600.0),
                                    ("L_arriere", (-200, 300, -700), 1.8e6, 600.0), ("L_dessus", (0, 900, 100), 1.5e6, 500.0)):
        ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = energy, size
        ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, ld)
        if ob.name not in sc.collection.objects:
            sc.collection.objects.link(ob)
        ob.location = loc
        look_at(ob, (0, 0, 120))
    w = bpy.data.worlds.get("V2_monde") or bpy.data.worlds.new("V2_monde")
    w.use_nodes = True
    bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg:
        bg.inputs["Color"].default_value = (0.86, 0.87, 0.86, 1.0)
        bg.inputs["Strength"].default_value = 0.6
    sc.world = w


def engine(quick):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = 16 if quick else 48
    except AttributeError:
        pass
    sc.render.resolution_x, sc.render.resolution_y = (960, 720) if quick else (1920, 1440)
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties[
        "view_transform"].enum_items] else "Standard"


def set_date(date):
    y, m, d = (int(x) for x in date.split("-"))
    try:
        import animate
        animate.set_frame_for_date(y, m, d)
        return
    except Exception as e:  # noqa: BLE001
        log("date non réglée :", e)


def visible(ob, show):
    ob.hide_render = not show
    ob.hide_viewport = not show


def zr(ob):
    """Cote z (mm) d'un objet : propriétés de la pièce si présentes, sinon boîte englobante."""
    if "z0" in ob and "z1" in ob:
        return float(ob["z0"]), float(ob["z1"])
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return min(p.z for p in pts), max(p.z for p in pts)


def shoot(name, cam, quick):
    sc = bpy.context.scene
    sc.camera = cam
    os.makedirs(OUT, exist_ok=True)
    sc.render.filepath = os.path.join(OUT, f"{name}{'_apercu' if quick else ''}.png")
    bpy.ops.render.render(write_still=True)
    log("écrit", sc.render.filepath)
    return sc.render.filepath


def main():
    o = opts()
    with open(os.path.join(V2, "spec", "architecture.json")) as f:
        arch = json.load(f)
    zf = arch["z_cadran_avant"]
    box = arch["masse"]["box_mm"]
    lights_world()
    engine(o["quick"])
    set_date(o["date"])
    objs = [ob for ob in bpy.data.objects if ob.type in ("MESH", "FONT", "CURVE")]
    cams = {
        "front": camera("front", (0, 0, zf + 900), rot=(0, 0, 0), ortho=box[0] * 1.08),
        "back": camera("back", (0, 0, -900), rot=(0, math.pi, 0), ortho=box[0] * 1.08),
        "lid": camera("lid", (0, 900, zf / 2), rot=(-math.pi / 2, 0, 0), ortho=box[0] * 1.08),
        "front34": camera("front34", (520, 380, zf + 620), target=(0, 0, zf / 2), lens=45.0),
        "interior": camera("interior", (420, 260, zf + 520), target=(0, -10, zf / 2), lens=40.0),
    }
    out = []
    if o["anim"]:
        sc = bpy.context.scene
        if o["res"]:
            sc.render.resolution_x, sc.render.resolution_y = o["res"]
        for ob in objs:
            visible(ob, ob.get("kind") != "glass")
        sc.camera = cams[o["anim"]]
        d = os.path.join(OUT, f"anim_{o['anim']}")
        os.makedirs(d, exist_ok=True)
        k = 0
        for f in range(sc.frame_start, sc.frame_end + 1, o["step"]):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(d, f"f_{k:04d}.png")
            bpy.ops.render.render(write_still=True)
            k += 1
        log("images d'animation :", k, "dans", d)
        return
    want = o["only"] or ["front", "back", "lid", "front34", "interior", "floors"]
    def coll(ob):
        return ob.users_collection[0].name if ob.users_collection else ""

    for name in ("front", "back", "lid", "front34"):
        if name in want:
            for ob in objs:
                visible(ob, ob.get("kind") != "glass")
            out.append(shoot(name, cams[name], o["quick"]))
    if "interior" in want:
        for ob in objs:
            z0, z1 = zr(ob)
            hide = (coll(ob) in ("V2_Caisse", "V2_Faces_Avant") or ob.get("kind") == "glass"
                    or (ob.get("kind") == "plate" and z0 > arch["etages"]["E3"]["z"][1]))
            visible(ob, not hide)
        out.append(shoot("interior", cams["interior"], o["quick"]))
    if "floors" in want:
        for fid, f in arch["etages"].items():
            a, b = f["z"]
            for ob in objs:
                z0, z1 = zr(ob)
                show = (not coll(ob).startswith(("V2_Caisse", "V2_Faces", "V2_Orrery")) and ob.get("kind") != "plate"
                        and z1 > a and z0 < b)
                visible(ob, show)
            out.append(shoot(f"etage_{fid}", cams["front"], o["quick"]))
        for ob in objs:
            visible(ob, True)
    with open(os.path.join(OUT, "renders.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
