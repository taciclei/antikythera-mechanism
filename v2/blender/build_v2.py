"""Anticythère 2.0 — assemblage de la maquette 3D → v2/out/v2.blend (voir CONTRACT.md).

Lancer : BL -b --factory-startup --python-exit-code 1 -P v2/blender/build_v2.py [-- --no-anim] [--out DIR]
         [--kepler-spec F --kepler-tools D]
Étapes : scène et unités, collections, matériaux, pièces de scene.json (parts.py), faces (faces.py),
animation (animate.py), rapport v2/out/build_report.json (dossier : --out, sinon V2_OUT, sinon v2/out).
Tours de Kepler (kepler_build.py, CONTRACT.md § 8) : seulement si v2/spec/kepler.json existe (ou --kepler-spec,
V2_KEPLER_SPEC) ; les blocs remplacés ne sont plus construits, les overrides sont appliqués, les pièces sont
construites et animées (motion « kepler ») et le rapport gagne une clé « kepler ». Sans spec : rien ne change.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
for p in (HERE, os.path.join(V2, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy  # noqa: E402

OUT = os.path.join(V2, "out")
COLLS = ["V2_Platines", "V2_Tours", "V2_Trains", "V2_Renvois", "V2_Blocs", "V2_Faces", "V2_Orrery", "V2_Caisse",
         "V2_Divers"]


def log(*a):
    print("[v2]", *a, flush=True)


def args():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    us = sc.unit_settings
    us.system, us.length_unit, us.scale_length = "METRIC", "MILLIMETERS", 0.001
    sc.name = "Anticythere_2"
    return sc


def collections(sc):
    out = {}
    for name in COLLS:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
        out[name] = c
    return out


def out_dir(opts):
    """Dossier de sortie : --out DIR, sinon V2_OUT, sinon v2/out."""
    if "--out" in opts and opts.index("--out") + 1 < len(opts):
        return os.path.abspath(opts[opts.index("--out") + 1])
    return os.path.abspath(os.environ.get("V2_OUT") or OUT)


def main():
    t0 = time.time()
    opts = args()
    out = out_dir(opts)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(V2, "spec", "scene.json")) as f:
        scene = json.load(f)
    with open(os.path.join(V2, "spec", "architecture.json")) as f:
        arch = json.load(f)
    sc = reset_scene()
    colls = collections(sc)
    import parts
    import kepler_build
    kep = kepler_build.activate()          # None tant que la spec Kepler n'existe pas
    plist, kscene = scene["parts"], None
    if kep is not None:
        plist, kscene = kepler_build.prepare_scene(plist, kep["spec"])
        log(f"Kepler : {kep['spec_path']} ; blocs remplacés {kscene['replaced']}, "
            f"overrides {len(kscene['overrides_applied'])}")
    mats = parts.materials()
    n, kinds, fails = 0, {}, []
    index = {p["id"]: p for p in plist}
    for p in plist:
        try:
            parts.build_part(p, colls, mats, index=index)
            n += 1
            kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
        except Exception as e:  # noqa: BLE001
            fails.append((p["id"], repr(e)))
    log(f"pièces : {n} ({kinds}), échecs : {len(fails)}, {time.time() - t0:.1f} s")
    krep = None
    if kep is not None:
        _kobs, krep = kepler_build.build_kepler(kep["spec"], colls, mats, kep["api"], scene_index=index)
        kepler_build.remember(sc, kep)
        fails += [("kepler:" + i, e) for i, e in krep["failures"]]
        log(f"Kepler : {krep['parts']} pièces {krep['towers']}, menées {len(krep['followers'])}, "
            f"échecs {len(krep['failures'])}, {time.time() - t0:.1f} s")
    import faces
    fobs = faces.build_faces(arch, colls, mats)
    log(f"faces : {len(fobs)} objets, {time.time() - t0:.1f} s")
    anim = None
    if "--no-anim" not in opts:
        import animate
        anim = animate.setup_animation(sc, kepler=kep)
        log(f"animation prête, {time.time() - t0:.1f} s")
    path = os.path.join(out, "v2.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    rep = {"parts": n, "kinds": kinds, "failures": fails, "faces": len(fobs), "objects": len(bpy.data.objects),
           "animation": anim if isinstance(anim, (dict, list, str, int, float)) else bool(anim),
           "seconds": round(time.time() - t0, 1), "blend": path}
    if kep is not None:
        rep["kepler"] = dict(krep, scene=kscene, spec=kep["spec_path"], tools=kep["tools_path"])
    with open(os.path.join(out, "build_report.json"), "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    log("écrit", path)
    if fails:
        for fid, e in fails[:20]:
            log("ÉCHEC", fid, e)
        sys.exit(1)


if __name__ == "__main__":
    main()
