"""Tests du module animate, à lancer dans Blender :
  $BL -b --factory-startup --python-exit-code 1 -P blender/test_animate.py
Objets factices : pilotes linéaires autour de ±Z, d'axes inclinés (avec et sans parent), clé « ephem:lambda_sun »
(ephem.py réel s'il fournit la clé, sinon un substitut), clés rapides (jup_io, gmst, mean_solar : sens et sous-images),
objets posés selon la convention de parts.py (spin_index : pilotage direct, phase comptée une fois), clé inconnue,
objet fixe, puis 1000 objets linéaires (chronométrés).
"""
import math
import random
import sys
import time
import types
import unittest
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import animate  # noqa: E402

TOL = 1e-6           # rad, exigence de la consigne
FRAMES = [1, 2, 57, 183, 300, 366]
START = (2026, 1, 1)


# ------------------------------------------------------------------ éphéméride : réelle ou substitut

def _stub_lambda_sun(j):
    """Longitude solaire approchée (Meeus, basse précision), ramenée dans [0, 2π[ pour éprouver le déroulage."""
    j = np.asarray(j, dtype=float)
    L = np.radians(280.46646 + 0.98564736 * j)
    M = np.radians(357.52911 + 0.98560028 * j)
    return np.mod(L + np.radians(1.914602) * np.sin(M) + np.radians(0.019993) * np.sin(2 * M), 2 * np.pi)


def _stub_lambda_moon(j):
    j = np.asarray(j, dtype=float)
    return np.mod(np.radians(218.3165 + 13.17639648 * j + 6.289 * np.sin(np.radians(134.963 + 13.0649930 * j))),
                  2 * np.pi)


def _make_stub():
    st = types.ModuleType("ephem")
    funcs = {"lambda_sun": _stub_lambda_sun, "lambda_moon": _stub_lambda_moon}
    st.KEYS = sorted(funcs)
    st.jd_from_date = animate._jd_gregorian
    st.jours_from_date = lambda y, m, d: animate._jd_gregorian(y, m, d) - 2451545.0
    st.values = lambda key, jours: funcs[key](jours)
    st.value = lambda key, jours: float(funcs[key](np.array([jours]))[0])
    st.IS_STUB = True
    return st


def load_ephem():
    """ephem.py réel s'il expose KEYS, value, values et la clé lambda_sun ; sinon substitut dans sys.modules."""
    try:
        real = animate.ephem_module()
        assert "lambda_sun" in real.KEYS
        real.values("lambda_sun", np.array([9496.5, 9497.5]))
        real.value("lambda_sun", 9496.5)
        return real, "ephem.py réel"
    except Exception as exc:  # absent, incomplet ou en cours d'écriture
        sys.modules["ephem"] = _make_stub()
        return sys.modules["ephem"], f"substitut ({type(exc).__name__}: {exc})"


EPHEM, EPHEM_ORIGIN = load_ephem()
print("[test_animate] éphéméride :", EPHEM_ORIGIN)


# ------------------------------------------------------------------ outils

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def mover(name, motion="linear", rate=0.0, phys=1, phase=0.0, axis=(0, 0, 1), loc=(0, 0, 0), **extra):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o["motion"], o["rate"], o["phys"], o["phase"], o["axis"] = motion, rate, phys, phase, list(axis)
    for k, v in extra.items():
        o[k] = v
    return o


def errors_at(objs, frame):
    return animate.angle_errors(objs, frame, bpy.context.scene)


def parts_spin_frame(axis, z_mode_for_minus_z=True):
    """Recopie de parts.spin_frame (convention de pose de parts.py) : ('Z', 0, 0, ±1) pour ±Z, sinon
    ('X', beta, gamma, 1) tels que Rz(gamma)·Ry(beta)·x̂ = axe. z_mode_for_minus_z=False : −Z posé en mode 'X'
    (beta = π/2), variante d'une version antérieure de parts.py, elle aussi acceptée par animate."""
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    if abs(a[0]) < 1e-9 and abs(a[1]) < 1e-9 and (a[2] > 0 or z_mode_for_minus_z):
        return "Z", 0.0, 0.0, (1 if a[2] > 0 else -1)
    beta = -math.asin(max(-1.0, min(1.0, float(a[2]))))
    gamma = math.atan2(float(a[1]), float(a[0])) if abs(a[2]) < 1.0 - 1e-9 else 0.0
    return "X", beta, gamma, 1


class TestPure(unittest.TestCase):
    def test_align_euler(self):
        for u in [(0, 1, 0), (1, 0, 0), (0, 0, -1), (0.3, -0.5, 0.8)]:
            n = math.sqrt(sum(c * c for c in u))
            u = tuple(c / n for c in u)
            ax, ay = animate.align_euler(u)
            rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
            ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
            z = rx @ ry @ np.array([0.0, 0.0, 1.0])
            self.assertLess(np.linalg.norm(z - np.array(u)), 1e-12)

    def test_unwrap_centered(self):
        a = np.mod(np.linspace(0, 40, 200), 2 * np.pi)
        u = animate.unwrap_centered(a)
        self.assertLess(np.max(np.abs(np.diff(u))), math.pi)
        self.assertLess(abs(u.max() + u.min()) / 2, math.pi + 1e-9)
        self.assertLess(np.max(np.abs(np.mod(u - a + math.pi, 2 * math.pi) - math.pi)), 1e-12)

    def test_formula(self):
        self.assertAlmostEqual(animate.linear_angle(1.0, -1, 0.5, 2.25), 2 * math.pi * 2.25 + 0.5, places=12)
        self.assertEqual(animate.linear_angle(-0.25, -1, 0.0, 1.0), animate.linear_angle(0.25, -1, 0.0, 1.0))
        self.assertEqual(animate.jours_from_date(2000, 1, 1), -0.5)

    def test_spin_axis(self):
        """Faire varier rotation_euler[i] (mode XYZ) = rotation autour de spin_axis(euler, i), à gauche."""
        rnd = random.Random(3)
        for _ in range(20):
            e = [rnd.uniform(-3, 3) for _ in range(3)]
            for i in range(3):
                d = 0.37
                e2 = list(e)
                e2[i] += d
                m0, m1 = Euler(e, "XYZ").to_matrix(), Euler(e2, "XYZ").to_matrix()
                want = Matrix.Rotation(d, 3, Vector(animate.spin_axis(e, i))) @ m0
                err = max(abs(want[r][c] - m1[r][c]) for r in range(3) for c in range(3))
                self.assertLess(err, 1e-5, (e, i))

    def test_continuous_values_fast_keys(self):
        """Clés rapides : le déroulage fin garde le vrai sens et le vrai nombre de tours entre deux clés."""
        j = 9496.5 + np.arange(0.0, 31.0)
        for key, turns_per_day in [("lambda_sun", 1 / 365.25), ("jup_io", 1 / 1.769137786),
                                   ("gmst", 1.0027379), ("mean_solar", 1.0)]:
            if key not in EPHEM.KEYS:
                continue
            v = animate.continuous_values(key, j)
            d = np.diff(v) / (2 * math.pi)
            self.assertTrue(np.all(np.abs(d - turns_per_day) < 0.01), (key, d[:3]))
            raw = np.asarray(EPHEM.values(key, j), float)
            self.assertLess(np.max(np.abs(np.mod(v - raw + math.pi, 2 * math.pi) - math.pi)), 1e-9)


class TestBlender(unittest.TestCase):
    def setUp(self):
        self.scene = reset()

    def test_controller_and_dates(self):
        st = animate.setup_animation(self.scene, START, days=366, fps=24)
        sc = self.scene
        self.assertEqual((sc.frame_start, sc.frame_end, sc.render.fps), (1, 366, 24))
        ctrl = bpy.data.objects[animate.CONTROLLER]
        j0 = animate.jours_from_date(*START)
        self.assertEqual(st["j0"], j0)
        for f in FRAMES + [367]:
            sc.frame_set(f)
            jv = ctrl.evaluated_get(bpy.context.evaluated_depsgraph_get())["jours"]
            self.assertEqual(jv, j0 + f - 1, f"image {f}")
        self.assertEqual(animate.set_frame_for_date(2026, 7, 1), 182.0)
        self.assertEqual(sc.frame_current, 182)
        self.assertEqual(animate.frame_for_date(2027, 1, 1), 366.0)
        self.assertEqual(animate.jours_at_frame(366), animate.jours_from_date(2027, 1, 1))

    def test_linear_z(self):
        objs = [mover("J", rate=1.0, phys=-1, phase=0.0),
                mover("gmst", rate=1.0027379097501048, phys=1, phase=1.234),
                mover("lent", rate=0.0123, phys=1, phase=-2.5),
                mover("prec", rate=-1.0625858265027432e-07, phys=-1, phase=0.1),
                mover("noeud", rate=-0.00014719999405916103, phys=-1, phase=3.0),
                mover("moinsZ", rate=0.37, phys=1, phase=0.4, axis=(0, 0, -1))]
        animate.setup_animation(self.scene, START)
        for o in objs:
            self.assertIs(o.parent, None)
            drv = o.animation_data.drivers[0].driver
            self.assertTrue(drv.is_simple_expression, drv.expression)
            self.assertTrue(drv.is_valid)
        for f in FRAMES:
            for name, e in errors_at(objs, f).items():
                self.assertLess(e, TOL, f"{name} image {f}")
        # le sens : phys = +1 tourne en horaire vu de face (angle autour de +Z décroissant)
        lent = bpy.data.objects["lent"]
        a1, a2 = animate.expected_angle(lent, 10), animate.expected_angle(lent, 11)
        self.assertLess(a2 - a1, 0.0)

    def _world_point_ok(self, o, rest_world, center, axis_world, frame):
        dg = bpy.context.evaluated_depsgraph_get()
        theta = animate.wrap_pi(animate.expected_angle(o, frame))  # mathutils est en float32 : angle ramené
        R = (Matrix.Translation(center) @ Matrix.Rotation(theta, 4, axis_world)
             @ Matrix.Translation(-center))
        for p in [Vector((10, 0, 0)), Vector((0, 7, 3)), Vector((-4, 2, -9))]:
            want = R @ rest_world @ p
            got = o.evaluated_get(dg).matrix_world @ p
            self.assertLess((want - got).length, 1e-4, f"{o.name} image {frame}")

    def test_linear_slanted(self):
        par = bpy.data.objects.new("porteur", None)
        self.scene.collection.objects.link(par)
        par.location = (5, 6, 7)
        par.rotation_euler = (0.2, -0.4, math.radians(30))
        u = Vector((0.3, -0.5, 0.8)).normalized()
        objs = [mover("incline", rate=0.8, phys=1, phase=0.3, axis=tuple(u), loc=(12, -3, 4)),
                mover("tringleY", rate=0.25, phys=-1, phase=-1.0, axis=(0, 1, 0), loc=(-20, 0, 15)),
                mover("axeX", rate=1.5, phys=1, phase=2.0, axis=(1, 0, 0), loc=(0, 30, 0)),
                mover("enfant", rate=0.05, phys=1, phase=0.0, axis=tuple(u), loc=(1, 2, 3))]
        objs[0].rotation_euler = (0.1, 0.2, 0.3)
        objs[3].parent = par
        self.scene.frame_set(1)
        rest = {o.name: o.matrix_world.copy() for o in objs}
        P = par.matrix_world.copy()
        st = animate.setup_animation(self.scene, START)
        self.assertEqual(st["pivots"], 4)
        for f in FRAMES:
            for name, e in errors_at(objs, f).items():
                self.assertLess(e, TOL, f"{name} image {f}")
            for o in objs:
                ax = Vector(o["axis"]).normalized()
                c = rest[o.name].translation.copy()
                if o.name == "enfant":
                    ax = (P.to_3x3() @ ax).normalized()
                self._world_point_ok(o, rest[o.name], c, ax, f)

    def test_parts_convention(self):
        """Objets posés comme parts.build_part : mode XYZ, rotation_euler = (phase, beta, gamma) (spin_index 0) ou
        (±phase sur Z, spin_index 2). Pilotage direct, sans pivot, et phase appliquée une seule fois."""
        u = Vector((0.3, -0.5, 0.8)).normalized()
        specs = [("tringle", tuple(u), 0.8, 1, 0.7, "linear"), ("tringleY", (0, 1, 0), 0.25, -1, -1.1, "linear"),
                 ("coniqueX", (1, 0, 0), 1.5, 1, 2.0, "linear"), ("moinsZ", (0, 0, -1), 0.37, 1, 0.4, "linear"),
                 ("moinsZ_X", (0, 0, -1), 0.21, -1, 1.4, "linear"), ("roueZ", (0, 0, 1), 0.0123, 1, -2.5, "linear"),
                 ("soleil_dos", (0, 0, -1), 0.0, 1, 0.9, "ephem:lambda_sun")]
        objs, rest, want = [], {}, {}
        for i, (name, axis, rate, phys, phase, motion) in enumerate(specs):
            mode, beta, gamma, sgn = parts_spin_frame(axis, z_mode_for_minus_z=not name.endswith("_X"))
            o = mover(name, motion=motion, rate=rate, phys=phys, phase=phase, axis=axis, loc=(3 * i, -2, 5))
            o.rotation_mode = "XYZ"
            o.rotation_euler = (0.0, 0.0, sgn * phase) if mode == "Z" else (phase, beta, gamma)
            o["spin"], o["spin_index"], o["spin_sign"] = mode, (2 if mode == "Z" else 0), sgn
            rest[name] = (Matrix.Translation(o.location)
                          @ Euler((0.0, beta, gamma), "XYZ").to_matrix().to_4x4())  # pose de phase nulle
            want[name] = (o, sgn, o["spin_index"])
            objs.append(o)
        st = animate.setup_animation(self.scene, START)
        self.assertEqual(st["pivots"], 0)
        for o in objs:
            self.assertIsNone(o.parent)
            self.assertEqual(animate.drive_channel(o, create=False), want[o.name])
        for f in FRAMES:
            for name, e in errors_at(objs, f).items():
                self.assertLess(e, TOL, f"{name} image {f}")
            for o in objs:
                self._world_point_ok(o, rest[o.name], rest[o.name].translation.copy(), Vector(o["axis"]), f)

    def test_ephem_fast_keys(self):
        """Clés rapides cuites au pas d'un jour : sens direct conservé entre deux clés (Io ne recule pas),
        exactes aux images entières (à la précision float32 près) et justes aux sous-images."""
        keys = [k for k in ("jup_io", "gmst", "mean_solar", "jup_europa") if k in EPHEM.KEYS]
        if not keys:
            self.skipTest("clés rapides absentes")
        objs = [mover(k, motion="ephem:" + k, scale=1.0, phase=0.2) for k in keys]
        animate.setup_animation(self.scene, START)
        for o in objs:
            fc = o.animation_data.action.fcurve_ensure_for_datablock(o, "rotation_euler", index=2)
            vals = np.array([k.co[1] for k in fc.keyframe_points], float)
            d = np.diff(vals)
            self.assertTrue(np.all(d > 0.5), f"{o.name} : pas min {d.min():.3f} rad")
            self.assertLess(abs(vals.max() + vals.min()) / 2, math.pi + 1e-3)
        bound = 2 * 1200 * 2.0 ** -24 + 1e-6  # |angle| centré ≤ ~1200 rad (gmst, mean_solar)
        for f in FRAMES:
            for name, e in errors_at(objs, f).items():
                self.assertLess(e, bound, f"{name} image {f}")
        for f in (1.5, 57.25, 200.75):
            for name, e in errors_at(objs, f).items():
                self.assertLess(e, 2e-3, f"{name} sous-image {f}")

    def test_ephem_lambda_sun(self):
        sun = mover("soleil", motion="ephem:lambda_sun", phase=0.3)
        sun2 = mover("soleil_incline", motion="ephem:lambda_sun", phase=-0.2, scale=1.0, axis=(0, 1, 1))
        fixe = mover("fixe", motion="fixed", loc=(1, 2, 3))
        fixe.rotation_euler = (0.1, 0.2, 0.3)
        st = animate.setup_animation(self.scene, START, days=366, step_days=1)
        self.assertEqual((st["ephem"], st["fixed"]), (2, 1))
        fc = sun.animation_data.action.fcurve_ensure_for_datablock(sun, "rotation_euler", index=2)
        self.assertEqual(len(fc.keyframe_points), 367)
        vals = np.array([k.co[1] for k in fc.keyframe_points])
        self.assertLess(np.max(np.abs(np.diff(vals))), math.pi)
        self.assertTrue(all(k.interpolation == "LINEAR" for k in fc.keyframe_points))
        for f in FRAMES:
            for name, e in errors_at([sun, sun2], f).items():
                self.assertLess(e, TOL, f"{name} image {f}")
        self.assertIsNone(fixe.animation_data)
        self.assertLess((Vector(fixe.rotation_euler) - Vector((0.1, 0.2, 0.3))).length, 1e-7)
        self.assertIsNone(animate.expected_angle(fixe, 10))

    def test_ephem_fast_key_unwrapped(self):
        if "lambda_moon" not in EPHEM.KEYS:
            self.skipTest("clé lambda_moon absente")
        moon = mover("lune", motion="ephem:lambda_moon", phase=0.0)
        animate.setup_animation(self.scene, START)
        fc = moon.animation_data.action.fcurve_ensure_for_datablock(moon, "rotation_euler", index=2)
        vals = np.array([k.co[1] for k in fc.keyframe_points])
        self.assertLess(np.max(np.abs(np.diff(vals))), math.pi)
        self.assertLess(abs(vals.max() + vals.min()) / 2, math.pi + 1e-6)
        # ~13 tours/an : |angle| ≤ ~45 rad en float32 → demi-ulp ≈ 2e-6 rad
        for f in FRAMES:
            self.assertLess(errors_at([moon], f)["lune"], 4e-6)

    def test_unknown_motion(self):
        """Clé d'éphéméride inconnue : ValueError explicite (strict), sinon objet ignoré sans animation."""
        bad = mover("inconnu", motion="ephem:pas_une_cle")
        with self.assertRaises(ValueError):
            animate.setup_animation(self.scene, START)
        st = animate.setup_animation(self.scene, START, strict=False)
        self.assertEqual(st["ignored"], ["inconnu"])
        self.assertIsNone(bad.animation_data)

    def test_idempotent(self):
        objs = [mover("a", rate=0.5, phys=1, phase=0.2), mover("b", rate=0.3, phys=-1, axis=(0, 1, 0)),
                mover("c", motion="ephem:lambda_sun")]
        animate.setup_animation(self.scene, START)
        n_obj = len(bpy.data.objects)
        animate.setup_animation(self.scene, START)
        self.assertEqual(len(bpy.data.objects), n_obj)
        self.assertEqual(len(objs[0].animation_data.drivers), 1)
        self.assertEqual(len(objs[0].animation_data.drivers[0].driver.variables), 1)
        for f in FRAMES:
            for name, e in errors_at(objs, f).items():
                self.assertLess(e, TOL, f"{name} image {f}")


class TestTiming(unittest.TestCase):
    def test_1000_linear(self):
        scene = reset()
        rnd = random.Random(7)
        objs = []
        for i in range(1000):
            axis = (0, 0, 1) if i % 10 else (0, 1, 0)
            objs.append(mover(f"m{i:04d}", rate=rnd.uniform(1e-6, 1.1), phys=rnd.choice((-1, 1)),
                              phase=rnd.uniform(-math.pi, math.pi), axis=axis))
        t0 = time.perf_counter()
        st = animate.setup_animation(scene, START)
        t_setup = time.perf_counter() - t0
        t0 = time.perf_counter()
        for f in range(2, 52):
            scene.frame_set(f)
        t_frame = (time.perf_counter() - t0) / 50
        errs = errors_at(objs, 200)
        worst = max(errs.values())
        print(f"\n[timing] 1000 objets linéaires ({st['pivots']} pivots) : mise en place {t_setup:.3f} s, "
              f"frame_set {1000 * t_frame:.2f} ms/image, écart max {worst:.2e} rad")
        self.assertEqual(st["linear"], 1000)
        self.assertLess(worst, TOL)


if __name__ == "__main__":
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(
        sys.modules[__name__]))
    if not res.wasSuccessful():
        raise RuntimeError("test_animate : échecs")
