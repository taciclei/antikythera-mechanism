import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from am import spec as S, kinematics as K, involute as I, layout, threemf  # noqa: E402
from am import interference2d as X  # noqa: E402


class TestPrint(unittest.TestCase):
    def test_profiles_2d(self):
        s = S.load()
        L = K.Laws(s)
        ph, _ = I.compute_phases(s, L)
        for prof, pp in layout.print_profiles(s):
            for r in X.check_all(s, L, ph, j=pp['backlash_mm'], n_pos=8, scale=pp['scale']):
                self.assertTrue(r['ok'], (prof.name, r))

    def test_profile_holes(self):
        s = S.load()
        L = K.Laws(s)
        for prof, pp in layout.print_profiles(s):
            cat = layout.build(s, L, prof)
            for gid, info in cat.gear_info.items():
                g = s.gears[gid]
                if g['kind'] == 'spur':
                    sup = g['bore_radius'] - (0.05 if g['mount'].startswith('rides_on') else 0.0)
                    self.assertAlmostEqual(info['bore'] * prof.s, sup * prof.s + pp['bore_clearance_mm'], places=9)

    def test_threemf_roundtrip(self):
        V = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float)
        T = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
                      [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 't.3mf')
            threemf.write(p, [('cube', V, T), ('cube2', V * 2, T)])
            back, n = threemf.read(p)
            self.assertEqual(n, 2)
            self.assertTrue(all(threemf.closed(t) for _, _, t in back))
            self.assertTrue(np.allclose(back[1][1], V * 2))
        self.assertFalse(threemf.closed(T[:-1]))


if __name__ == '__main__':
    unittest.main()
