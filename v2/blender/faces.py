"""Anticythère 2.0 — module faces : toutes les faces visibles de la machine (contrat § 4).

- Face avant (platine-cadran à z_cadran_avant) : cadran principal R 150 (anneau fixe J2000, anneau tropique mû par la
  précession), 10 aiguilles coaxiales (Soleil, Lune et boule de phase, Mercure à Neptune, Dragon), horloge 24 h,
  équation du temps, cadran de Jupiter et plaque d'époque.
- Face arrière (z 0..3, lue de dos) : calendrier (366 dates, guichet de la semaine, années), éclipses (Soleil, Lune,
  disque des nœuds gradué en γ), Saros et Exeligmos, plaque « mode d'emploi ».
- Couvercle : socle, 8 rainures d'orbites, bras des planètes étagés, tellurion (globe incliné, bras de la Lune,
  aiguille d'ombre).
- Caisse : chêne 6 mm, cadre et verre avant, porte arrière ouverte, manivelle sur la paroi gauche.

API : build_faces(arch, colls, mats) → liste des objets créés (maillages et textes). Les pièces mobiles portent les
propriétés motion, rate, phys, phase, axis, scale, kind, source, meshes_with, links (voir faces_common.tag).
Autonome : blender -b --factory-startup --python-exit-code 1 -P blender/faces.py -- [--plates] [--preview out.png]
"""
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy  # noqa: E402

import faces_back2 as FB  # noqa: E402
import faces_case as FK  # noqa: E402
import faces_common as FC  # noqa: E402
import faces_front as FF  # noqa: E402
import faces_front_sub as FS  # noqa: E402
import faces_lid as FL  # noqa: E402


def _parts_materials():
    """Matériaux de parts.py s'il est importable (sinon le jeu local de faces_common)."""
    try:
        import parts
        m = parts.materials()
        return m if isinstance(m, dict) else None
    except Exception:  # parts.py absent ou signature différente : jeu local
        return None


def build_faces(arch=None, colls=None, mats=None, with_plates=False):
    """Construit toutes les faces visibles. `arch` : architecture.json (lu si None) ; `colls` : dict de collections
    (voir faces_common.collections) ; `mats` : dict de matériaux (complété par le jeu local)."""
    arch = arch or FC.load_arch()
    colls = FC.collections(colls)
    mats = FC.materials(mats if mats is not None else _parts_materials())
    objs = []
    objs += FF.build_main(arch, colls, mats)
    objs += FS.build_subdials(arch, colls, mats)
    objs += FB.build_back(arch, colls, mats)
    objs += FL.build_lid(arch, colls, mats)
    objs += FK.build_case(arch, colls, mats)
    if with_plates:
        objs += FK.build_plates(arch, colls, mats)
    bpy.context.view_layer.update()  # matrices monde à jour pour les appelants
    return objs


def summary(objs):
    """Comptes par collection, par type et par mouvement."""
    by_coll = Counter(o.users_collection[0].name for o in objs)
    by_type = Counter(o.type for o in objs)
    motions = Counter(o.get("motion", "?") for o in objs if o.get("motion", "fixed") != "fixed")
    return {"total": len(objs), "collections": dict(by_coll), "types": dict(by_type),
            "mobiles": sum(motions.values()), "motions": dict(sorted(motions.items()))}


def set_units(scene):
    us = scene.unit_settings
    us.system, us.length_unit, us.scale_length = "METRIC", "MILLIMETERS", 0.001


def preview(path, res=(800, 620), hide=("CS_verre", "CS_cadre_avant")):
    """Aperçu Workbench orthographique de la face avant (basse résolution)."""
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new("V2F_camera_apercu")
    cam_data.type, cam_data.ortho_scale = "ORTHO", 490.0
    cam_data.clip_start, cam_data.clip_end = 1.0, 5000.0
    cam = bpy.data.objects.new("V2F_camera_apercu", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (0.0, 0.0, 1500.0)
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = str(path)
    hidden = [o for o in (bpy.data.objects.get(n) for n in hide) if o is not None]
    for o in hidden:
        o.hide_render = True
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cam_data)
    return str(path)


def main(argv=None):
    argv = argv if argv is not None else (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    set_units(bpy.context.scene)
    objs = build_faces(with_plates="--plates" in argv)
    print("FACES", summary(objs))
    if "--preview" in argv:
        print("APERCU", preview(argv[argv.index("--preview") + 1]))
    return objs


if __name__ == "__main__":
    main()
