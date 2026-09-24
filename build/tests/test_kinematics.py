import math
import os
import random
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from am import spec as S, kinematics as K  # noqa: E402


class TestSpec(unittest.TestCase):
    def test_fingerprint(self):
        s = S.load()
        rep = S.fingerprint_report(s.d)
        self.assertTrue(rep['ok'], rep['sha256'])
        self.assertTrue(all(rep['sections'].values()))

    def test_structure(self):
        self.assertEqual(S.validate(S.load().d), [])

    def test_counts(self):
        s = S.load()
        self.assertEqual(len(s.gears), 69)
        self.assertEqual(len(s.bodies), 48)
        self.assertEqual(len(s.external_meshes), 37)
        self.assertEqual(len(s.crown_meshes), 2)


class TestKinematics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = S.load()
        cls.ok, cls.rep = K.check(cls.s)
        cls.L = K.Laws(cls.s)

    def test_dof(self):
        self.assertEqual(self.rep['n_unknowns'], 45)
        self.assertEqual(self.rep['n_equations'], 44)
        self.assertEqual(self.rep['counts'], {'willis': 37, 'pin_slot': 4, 'follower': 3})
        self.assertEqual(self.rep['rank'], 44)
        self.assertEqual(self.rep['dof'], 1)
        self.assertEqual(self.rep['inconsistent'], 0)

    def test_rates(self):
        self.assertEqual(self.rep['rate_errors'], [])

    def test_targets(self):
        self.assertEqual(len(self.rep['targets']), 22)
        for t in self.rep['targets']:
            self.assertTrue(t['ok'], t)
        self.assertTrue(self.ok)

    def test_mutation_detected(self):
        """Changing one tooth count must break the solver checks."""
        import copy
        d = copy.deepcopy(self.s.d)
        next(g for g in d['gears'] if g['id'] == 'e5')['teeth'] = 51
        ok, rep = K.check(S.Spec(d))
        self.assertFalse(ok)

    def test_willis_on_angles(self):
        """Every external mesh satisfies Willis on the actual (nonlinear) angles."""
        s, L = self.s, self.L
        rnd = random.Random(1)
        for _ in range(40):
            t = rnd.uniform(-50, 50)
            A = L.local(t)
            W = L.world_z(t, A)
            for m in s.external_meshes:
                g1, g2 = s.gears[m['driver']], s.gears[m['driven']]
                C = m['carrier']
                wc = W.get(C, 0.0)
                d1 = W.get(g1['body'], 0.0) - wc
                d2 = W.get(g2['body'], 0.0) - wc
                # z1*d1 + z2*d2 = const (0 at t=0 for these laws) modulo 2*pi*z (tooth period)
                v = g1['teeth'] * d1 + g2['teeth'] * d2
                A0 = L.local(0.0)
                W0 = L.world_z(0.0, A0)
                v0 = (g1['teeth'] * (W0.get(g1['body'], 0.0) - W0.get(C, 0.0))
                      + g2['teeth'] * (W0.get(g2['body'], 0.0) - W0.get(C, 0.0)))
                err = abs(K.wrap(v - v0))
                self.assertLess(err, 1e-9 * max(g1['teeth'], g2['teeth']) * 10, (m, t, err))

    def test_q_initial(self):
        self.assertAlmostEqual(self.L.local(0.0)['q'], -0.0773916, places=6)

    def test_mean_rates_numeric(self):
        """Nonlinear bodies: mean rate over many cycles equals the exact mean."""
        rates = {k: Fraction(v) for k, v in self.rep['rates'].items()}
        bodies = ('kp', 'e_inner', 'moon', 't_mars', 't_mercury', 't_trueSun', 'x_sa86s')
        T, n = 19.0, 6000
        prev, acc = None, dict.fromkeys(bodies, 0.0)
        for j in range(n + 1):
            W = self.L.world_z(T * j / n)
            if prev is not None:
                for b in bodies:
                    acc[b] += K.wrap(W[b] - prev[b])
            prev = W
        for b in bodies:
            mean = -acc[b] / (2 * math.pi * T)
            self.assertAlmostEqual(mean, float(rates[b]), delta=0.02, msg=b)


if __name__ == '__main__':
    unittest.main()
