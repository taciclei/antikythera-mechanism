import copy
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from am import spec as S, kinematics as K, involute as I, crown, spiral, outline, layout  # noqa: E402
from am import interference2d as X, regions as R, expr as E, geomcheck as G  # noqa: E402


class TestInvolute(unittest.TestCase):
    def test_tip_land_p2(self):
        g = I.Involute(12, 0.5)
        self.assertAlmostEqual(g.tip_land() / 0.5, 0.228, places=3)

    def test_outline(self):
        g = I.Involute(20, 0.5, j=0.03)
        o = g.outline(0.3)
        self.assertGreater(outline.signed_area(o), 0)
        d = np.linalg.norm(np.diff(np.vstack([o, o[:1]]), axis=0), axis=1)
        self.assertGreater(d.min(), 1e-9)
        # at least 24 points per flank
        self.assertGreaterEqual(len(o) / 20, 2 * 24)

    def test_contact_ratio(self):
        s = S.load()
        for m in s.external_meshes:
            g1, g2 = s.gears[m['driver']], s.gears[m['driven']]
            self.assertGreaterEqual(I.contact_ratio(g1['teeth'], g2['teeth'], m['module']), 1.2)


class TestCrownSpiral(unittest.TestCase):
    def test_crown_volumes(self):
        s = S.load()
        for w, vol in (('a1', 1.3913), ('q1', 0.8116)):
            V, T, z, nv = crown.crown_teeth(s, w)
            self.assertAlmostEqual(crown.mesh_volume(V[:nv], T[:len(T) // z]), vol, places=4)

    def test_spiral_continuity(self):
        for k in range(1, 10):
            a = spiral.rho(k * math.pi - 1e-9, 44, 5.2)
            b = spiral.rho(k * math.pi + 1e-9, 44, 5.2)
            self.assertAlmostEqual(float(a), float(b), places=6)

    def test_lookup(self):
        psi, rho = spiral.lookup(44, 5.2, 5, 250)
        self.assertGreaterEqual(len(psi), 1800)
        self.assertTrue(np.all(np.diff(rho) >= -1e-12))


class TestMeshes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = S.load()
        cls.L = K.Laws(cls.s)
        cls.ph, cls.comps = I.compute_phases(cls.s, cls.L)

    def test_components(self):
        self.assertEqual(len(self.comps), 28)

    def test_interference(self):
        for r in X.check_all(self.s, self.L, self.ph, n_pos=10):
            self.assertTrue(r['ok'], r)

    def test_bad_phase_detected(self):
        ph = dict(self.ph)
        ph['c1'] += math.pi / 38
        r = X.check_mesh(self.s, self.L, ph, self.s.external_meshes[0], n_pos=10)
        self.assertFalse(r['ok'])

    def test_axis_mutation_detected(self):
        d = copy.deepcopy(self.s.d)
        b = next(b for b in d['bodies'] if b['id'] == 'd')
        b['axis_xy_in_parent'][0] += 0.01
        ok, rows = G.mesh_checks(S.Spec(d))
        self.assertFalse(ok)

    def test_mesh_checks(self):
        ok, rows = G.mesh_checks(self.s)
        self.assertTrue(ok)


class TestPrefilterExpr(unittest.TestCase):
    def test_prefilter(self):
        s = S.load()
        L = K.Laws(s)
        cat = layout.build(s, L)
        res = R.Prefilter(s, cat).run()
        self.assertEqual(res['conflicts'], [])
        self.assertEqual(len(res['intended']), len(cat.intended))

    def test_zmutation_detected(self):
        s = S.load()
        d = copy.deepcopy(s.d)
        next(g for g in d['gears'] if g['id'] == 'nd64')['z'] = [12.3, 13.3]   # into L5
        s2 = S.Spec(d)
        L = K.Laws(s2)
        cat = layout.build(s2, L)
        res = R.Prefilter(s2, cat).run()
        self.assertTrue(res['conflicts'])

    def test_expr(self):
        ok, rep = E.check(S.load(), n=50)
        self.assertTrue(ok, rep['max_err'])


if __name__ == '__main__':
    unittest.main()
