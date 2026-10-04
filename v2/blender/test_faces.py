"""Tests du module faces, à lancer dans Blender :
  BL -b --factory-startup --python-exit-code 1 -P v2/blender/test_faces.py [-- --with-parts]
--with-parts construit aussi les pièces de spec/scene.json (parts.py) pour vérifier les recouvrements avec elles.
Écrit l'aperçu Workbench de la face avant dans v2/out/preview_faces.png (pose au 1er janvier 2026 si ephem.py existe).
"""
import math
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import faces  # noqa: E402
import faces_common as FC  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WITH_PARTS = "--with-parts" in ARGS
PREVIEW = FC.V2 / "out" / "preview_faces.png"
PLANETS = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]
API_KEYS = (["lambda_sun", "lambda_moon", "node", "perigee", "elong", "prec", "gmst", "mean_solar", "jup_io",
             "jup_europa", "jup_ganymede", "jup_callisto", "jup_nu", "lunette", "cal_ring", "weekday", "years",
             "saros", "exeligmos", "eot", "gamma", "helio_earth"]
            + [f"lambda_geo_{p}" for p in PLANETS] + [f"helio_{p}" for p in PLANETS])
REQUIRED = set(API_KEYS) - {"perigee", "gamma"}
PROPS = ("motion", "rate", "phys", "phase", "axis", "scale", "kind", "source", "meshes_with", "links")


def resolver():
    """Même règle que check.py : nom, nom avec '#' → '.', part_id ou id, puis source unique."""
    obs = list(bpy.data.objects)
    by = {o.name: o for o in obs}
    for o in obs:
        for k in ("part_id", "id"):
            if k in o.keys():
                by.setdefault(str(o[k]), o)
    src = {}
    for o in obs:
        if "source" in o.keys():
            src.setdefault(str(o["source"]), []).append(o)
    return lambda n: by.get(n) or by.get(n.replace("#", ".")) or (src.get(n, [None, None])[0]
                                                                  if len(src.get(n, [])) == 1 else None)


def moving(objs):
    return [o for o in objs if str(o.get("motion", "fixed")) != "fixed"]


def pose(objs, value_of):
    """Pose chaque pièce mobile : angle = scale · valeur + phase (ephem) ou angle linéaire, autour de axis."""
    for o in moving(objs):
        m = str(o["motion"])
        ang = (o["scale"] * value_of(m[6:]) + o["phase"]) if m.startswith("ephem:") else value_of("linear")
        o.rotation_mode = "AXIS_ANGLE"
        o.rotation_axis_angle = (ang, *o["axis"])
    bpy.context.view_layer.update()


def world_mesh(o):
    me = o.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(o.matrix_world)
    W = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    return W, [tuple(p.vertices) for p in me.polygons]


def overlaps(meshes, res, mine=None):
    """Couples (a, b) en recouvrement BVH, hors liens déclarés et parenté (au moins un objet de `mine`)."""
    data = {o.name: world_mesh(o) for o in meshes}
    box = {n: (W.min(0), W.max(0)) for n, (W, _) in data.items()}
    decl = {o.name: {getattr(res(str(x)), "name", None) for k in ("links", "meshes_with") for x in
                     (o.get(k).to_list() if hasattr(o.get(k), "to_list") else list(o.get(k) or []))}
            for o in meshes}

    def anc(o):
        s, p = set(), o.parent
        while p is not None:
            s.add(p.name)
            p = p.parent
        return s
    ancs = {o.name: anc(o) for o in meshes}
    trees, bad, names = {}, [], sorted(data)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            (la, ha), (lb, hb) = box[a], box[b]
            if np.any(la > hb) or np.any(lb > ha):
                continue
            if b in decl[a] or a in decl[b] or a in ancs[b] or b in ancs[a]:
                continue
            if mine is not None and a not in mine and b not in mine:
                continue
            for n in (a, b):
                if n not in trees:
                    trees[n] = BVHTree.FromPolygons(data[n][0].tolist(), data[n][1])
            if trees[a].overlap(trees[b]):
                bad.append((a, b))
    return bad


class FacesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        faces.set_units(bpy.context.scene)
        mats = None
        if WITH_PARTS:
            import json
            import parts
            mats = parts.materials()
            colls = {}
            for p in json.loads((FC.V2 / "spec" / "scene.json").read_text())["parts"]:
                name = p.get("collection") or "V2_Divers"
                if name not in colls:
                    colls[name] = bpy.data.collections.new(name)
                    bpy.context.scene.collection.children.link(colls[name])
                parts.build_part(p, {**colls, "_default": colls[name]}, mats)
        cls.objs = faces.build_faces(mats=mats, with_plates=not WITH_PARTS)
        bpy.context.view_layer.update()
        cls.summary = faces.summary(cls.objs)
        print("\nFACES", cls.summary)

    def test_1_counts(self):
        s = self.summary
        self.assertGreater(s["total"], 100)
        for c in ("V2_Faces_Avant", "V2_Faces_Arriere", "V2_Couvercle", "V2_Caisse"):
            self.assertGreater(s["collections"].get(c, 0), 0, c)
        self.assertGreaterEqual(s["mobiles"], 40)
        print("objets créés :", s["total"], "| mobiles :", s["mobiles"], "| types :", s["types"])

    def test_2_properties(self):
        for o in moving(self.objs):
            for k in PROPS:
                self.assertIn(k, o.keys(), f"{o.name} : {k}")
            ax = np.array(o["axis"], float)
            self.assertAlmostEqual(float(np.linalg.norm(ax)), 1.0, places=6, msg=o.name)
            self.assertIn(o["phys"], (1, -1), o.name)
            m = str(o["motion"])
            self.assertTrue(m == "linear" or (m.startswith("ephem:") and m[6:] in API_KEYS), f"{o.name} : {m}")
            self.assertEqual(tuple(o.rotation_euler), (0.0, 0.0, 0.0), f"{o.name} : pose de repos non nulle")

    def test_3_keys(self):
        used = {str(o["motion"])[6:] for o in moving(self.objs) if str(o["motion"]).startswith("ephem:")}
        self.assertFalse(REQUIRED - used, f"clés manquantes : {sorted(REQUIRED - used)}")
        lon = [o for o in moving(self.objs) if o.name.startswith("AV_aiguille_")]
        self.assertEqual(len(lon), 10)
        self.assertTrue(all(o["scale"] == -1.0 and o["phys"] == 1 or o["motion"] == "ephem:node" for o in lon))
        try:  # animate.setup_animation (strict) refuse une clé absente d'ephem.KEYS
            import ephem
            self.assertFalse(used - set(ephem.KEYS), f"clés inconnues d'ephem.py : {sorted(used - set(ephem.KEYS))}")
        except ImportError:
            pass
        print("clés utilisées :", len(used), sorted(used))

    def test_4_manifold(self):
        import bmesh
        bad = []
        for o in self.objs:
            if o.type == "MESH":
                bm = bmesh.new()
                bm.from_mesh(o.data)
                n = sum(1 for e in bm.edges if not e.is_manifold)
                bm.free()
                if n:
                    bad.append((o.name, n))
        self.assertFalse(bad, f"maillages non fermés : {bad[:5]}")

    def test_5_texts(self):
        bodies = " ".join(o.data.body for o in self.objs if o.type == "FONT")
        for w in ("Bélier", "Gémeaux", "janvier", "décembre", "Équation du temps", "Calendrier grégorien",
                  "Éclipses", "Saros", "MODE D'EMPLOI", "Le système solaire", "Horloge 24 h"):
            self.assertIn(w, bodies)
        for o in self.objs:
            if o.type != "FONT":
                continue
            M = np.array(o.matrix_world)[:3, :3]
            self.assertGreater(np.linalg.det(M), 0, f"{o.name} : texte en miroir")
            nz = M[:, 2] / np.linalg.norm(M[:, 2])
            coll = o.users_collection[0].name
            if coll == "V2_Faces_Avant":
                self.assertGreater(nz[2], 0.99, o.name)
            elif coll == "V2_Faces_Arriere":
                self.assertLess(nz[2], -0.99, f"{o.name} : non lisible de dos")
                if o.name.endswith("_titre"):
                    self.assertLess(M[0, 0], 0, f"{o.name} : sens de lecture de dos")

    def test_6_ranges(self):
        z_front = float(FC.load_arch()["z_cadran_avant"])
        for o in self.objs:
            if o.type != "MESH":
                continue
            W, _ = world_mesh(o)
            coll = o.users_collection[0].name
            if coll == "V2_Faces_Avant":
                self.assertGreaterEqual(W[:, 2].min(), z_front - 1e-6, o.name)
                self.assertLess(W[:, 2].max(), z_front + 22.0, o.name)
            elif coll == "V2_Faces_Arriere":
                self.assertGreater(W[:, 2].min(), -20.0, o.name)
                self.assertLessEqual(W[:, 2].max(), 1e-6, o.name)
            elif coll == "V2_Couvercle":
                self.assertGreaterEqual(W[:, 1].min(), 180.0 - 1e-6, o.name)

    def test_7_links_resolve(self):
        res = resolver()
        missing = sorted({(o.name, str(n)) for o in self.objs for k in ("links", "meshes_with")
                          for n in (o.get(k).to_list() if hasattr(o.get(k), "to_list") else list(o.get(k) or []))
                          if res(str(n)) is None})
        if WITH_PARTS:
            self.assertFalse(missing, f"noms non résolus : {missing[:8]}")
        else:
            self.assertFalse([m for m in missing if not m[1] in ("pile", "lune", "laplace", "saros#a2",
                                                                 "manivelle#r0")], missing)

    def test_8_no_overlap(self):
        res = resolver()
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and "kind" in o.keys()]
        rng = random.Random(7)
        mine = {o.name for o in self.objs}
        for i in range(6):
            pose(self.objs, lambda k: rng.uniform(-16.5, 16.5) if k == "eot" else rng.uniform(0, 2 * math.pi))
            bad = overlaps(meshes, res, mine)
            self.assertFalse(bad, f"pose {i} : recouvrements {bad[:6]}")
        print("recouvrements : aucun sur 6 poses aléatoires,", len(meshes), "maillages")

    def test_9_preview(self):
        try:
            import ephem
        except ImportError as e:  # ephem.py absent : pose aléatoire (une clé manquante, elle, est une erreur)
            print("aperçu en pose aléatoire :", repr(e))
        else:
            j = ephem.jours_from_date(2026, 1, 1)
            pose(self.objs, lambda k: float(ephem.value(k, j)) if k != "linear" else 0.0)
            print("aperçu posé au 2026-01-01 (ephem.py)")
        PREVIEW.unlink(missing_ok=True)
        path = faces.preview(PREVIEW)
        self.assertTrue(Path(path).exists() and Path(path).stat().st_size > 1000)
        print("APERCU", path)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def dial_phi(ob, local=(0.0, 1.0, 0.0)):
    """Angle de cadran (0 en haut, + anti-horaire vu de face) de la direction locale `local` de ob, en monde."""
    d = np.array(ob.matrix_world)[:3, :3] @ np.asarray(local, float)
    return math.atan2(-d[0], d[1])


def top_phi(ob):
    """Angle de cadran, dans le repère local de ob, de la direction monde « en haut » (index fixe du haut)."""
    loc = np.array(ob.matrix_world)[:3, :3].T @ np.array([0.0, 1.0, 0.0])
    return math.atan2(-loc[0], loc[1]) % (2 * math.pi)


class ReadingsTest(unittest.TestCase):
    """Lectures en repère monde après animate.setup_animation (pivots, parents, images clés), comparées à ephem."""
    TOL = 1e-4

    @classmethod
    def setUpClass(cls):
        try:
            import animate
            import ephem
        except ImportError as e:
            raise unittest.SkipTest(f"animate.py ou ephem.py absent : {e!r}")
        cls.an, cls.eph = animate, ephem
        bpy.ops.wm.read_factory_settings(use_empty=True)
        faces.set_units(bpy.context.scene)
        arch = FC.load_arch()
        faces.build_faces(arch, with_plates=True)
        cls.arch = arch
        cls.stats = animate.setup_animation(bpy.context.scene)  # 2026-01-01 → 2027-01-01
        cls.O = bpy.data.objects

    def goto(self, j):
        f = self.an.frame_for_jours(j)
        bpy.context.scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        bpy.context.view_layer.update()

    def test_pile_from_architecture(self):
        """Pile centrale : arbre du Soleil = axe_soleil (r 2,0), tube du Dragon à blocs.pile.r (Ø 18,4 mm)."""
        import faces_parts as FP
        z = float(self.arch["z_cadran_avant"])
        for name, want in (("AV_aiguille_soleil", FP.arch_r(self.arch, "axe_soleil", 2.0)),
                           ("AV_aiguille_dragon", float(self.arch["blocs"]["pile"]["r"]))):
            W, _ = world_mesh(self.O[name])
            near = W[(W[:, 2] < z + 1.0)]  # tube seul, sous le premier étage d'aiguilles
            self.assertAlmostEqual(float(np.hypot(near[:, 0], near[:, 1]).max()), want, places=4, msg=name)

    def test_readings_at_dates(self):
        e, O = self.eph, self.O
        import faces_front_sub as FS
        for date in [(2026, 1, 1), (2026, 3, 1), (2026, 7, 14), (2026, 11, 3)]:
            j = e.jours_from_date(*date)
            self.goto(j)
            v = {k: float(e.value(k, j)) for k in e.KEYS}
            for nm, key in [("AV_aiguille_soleil", "lambda_sun"), ("AV_aiguille_lune", "lambda_moon"),
                            ("AV_aiguille_mars", "lambda_geo_mars"), ("AV_aiguille_dragon", "node"),
                            ("AV_horloge_temps_moyen", "mean_solar"), ("AV_horloge_temps_sideral", "gmst"),
                            ("AV_jupiter_io", "jup_io"), ("AR_eclipses_noeuds", "node")]:
                self.assertLess(abs(wrap(dial_phi(O[nm]) + v[key])), self.TOL, f"{date} {nm}")
            # anneau tropique : 0° Bélier à la longitude J2000 −p (prec = −p)
            self.assertLess(abs(wrap(dial_phi(O["AV_anneau_tropique"]) + v["prec"])), self.TOL, date)
            self.assertLess(abs(wrap(dial_phi(O["AV_edt_aiguille"]) - FS.EOT_SCALE * v["eot"])), self.TOL, date)
            self.assertLess(abs(wrap(dial_phi(O["AR_calendrier_annees"]) + v["years"])), self.TOL, date)
            # boule de phase : moitié claire (−Z local au repos) vers l'observateur à la pleine Lune, vers le Soleil
            light = np.array(O["AV_boule_phase"].matrix_world)[:3, :3] @ np.array([0.0, 0.0, -1.0])
            self.assertAlmostEqual(light[2], -math.cos(v["elong"]), places=4, msg=date)
            moon, sun = (np.array(O[n].matrix_world)[:3, :3] @ [0.0, 1.0, 0.0]
                         for n in ("AV_aiguille_lune", "AV_aiguille_soleil"))
            tang = sun[:2] - moon[:2] * float(np.dot(sun[:2], moon[:2]))
            if np.linalg.norm(tang) > 1e-3:
                self.assertGreater(float(np.dot(light[:2], tang)), 0.0, f"{date} : clair à l'opposé du Soleil")
            # calendrier (lu de dos à l'index du haut) et guichet de la semaine
            _, idx = e.day_index_366(j)
            self.assertEqual(round(top_phi(O["AR_calendrier_anneau"]) / (2 * math.pi / 366)) % 366, int(idx), date)
            self.assertEqual(round(top_phi(O["AR_semaine_disque"]) / (2 * math.pi / 7)) % 7, int(e.weekday(j)), date)
            # tellurion : chariot d'orientation fixe, bras de la Terre, méridien de Greenwich, bras de la Lune
            R = np.array(O["CV_tellurion_chariot"].matrix_world)[:3, :3]
            self.assertLess(float(np.abs(R - np.eye(3)).max()), 1e-5, date)
            for nm, key in (("CV_bras_terre", "helio_earth"), ("CV_bras_lune", "lambda_moon")):
                d = np.array(O[nm].matrix_world)[:3, :3] @ [1.0, 0.0, 0.0]
                self.assertLess(abs(wrap(math.atan2(-d[2], d[0]) - v[key])), self.TOL, f"{date} {nm}")
            g = np.array(O["CV_globe_terre"].matrix_world)[:3, :3] @ [1.0, 0.0, 0.0]
            eps = math.radians(self.arch["faces"]["couvercle"]["tellurion"]["inclinaison_deg"])
            ra = math.atan2(-g[2] * math.cos(eps) - g[1] * math.sin(eps), g[0])  # écliptique → équateur
            self.assertLess(abs(wrap(ra - v["gmst"])), self.TOL, f"{date} globe")

    def test_nu_line_at_conjunction(self):
        """À une conjonction Io-Europe (λ_Io = λ_Europe), la ligne ν passe par les aiguilles d'Io et d'Europe."""
        e, O = self.eph, self.O
        j0 = e.jours_from_date(2026, 2, 1)
        js = j0 + np.arange(0.0, 5.0, 0.01)
        s = np.sin(e.values("jup_io", js) - e.values("jup_europa", js))
        c = np.cos(e.values("jup_io", js) - e.values("jup_europa", js))
        i = next(i for i in range(len(js) - 1) if s[i] < 0 <= s[i + 1] and c[i] > 0)
        a, b = js[i], js[i + 1]
        for _ in range(40):
            m = (a + b) / 2
            a, b = (m, b) if math.sin(e.value("jup_io", m) - e.value("jup_europa", m)) < 0 else (a, m)
        self.goto(a)
        io, nu = dial_phi(O["AV_jupiter_io"]), dial_phi(O["AV_jupiter_nu"])
        self.assertLess(abs(wrap(dial_phi(O["AV_jupiter_europe"]) - io)), 1e-3)
        self.assertLess(abs(wrap(2 * (nu - io))) / 2, 1e-3, "la ligne ν ne passe pas par la conjonction")
        self.assertEqual(O["AV_jupiter_nu"]["phys"], -1, "ligne des conjonctions : sens rétrograde")


if __name__ == "__main__":
    r = unittest.main(argv=["test_faces"], exit=False, verbosity=2).result
    if not r.wasSuccessful():  # --python-exit-code 1 : une exception donne le code de sortie 1
        raise RuntimeError(f"test_faces : {len(r.failures)} échecs, {len(r.errors)} erreurs")
