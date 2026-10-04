"""Tests de la phase K2 (tours de Kepler côté Blender), à lancer dans Blender :
  $BL -b --factory-startup --python-exit-code 1 -P blender/test_kepler_build.py [-- --full] [--keep]
Une fausse tour (kepler_fake.py : manivelle à goupille, bras rainuré d'équant e = 1 mm, bague excentrique, manchon,
roue de prise 46 dents, anneau de loi LT) et un faux paquet motion.py/frame.py sont écrits dans un dossier
temporaire (tempfile). Rien n'est écrit dans v2/out ni dans v2/spec.
 1. inactif sans spec, chemins (arguments, environnement), spec explicite absente = erreur ;
 2. prepare_scene sur la vraie scene.json : blocs et roue de prise retirés, overrides appliqués, liens nettoyés ;
 3. géométrie : îlots qui se recouvrent (union), aire des pièces percées, alésage et rayon de tête de la roue ;
 4. construction complète par build_v2.main (--out, --kepler-spec, --kepler-tools) : objets, parents, propriétés ;
 5. animation : canaux évalués aux images 1, 2, 57, 183, 300, 366 contre motion_api à 1e-6 (mm, rad), matrix_world
    à 2e-5 mm (float32) ; roue menée θ = −θ_menante + phase ;
 6. contrôle (check.run_checks) : verdict OK, ≥ 48 états de grille + trajectoire, 0 recouvrement, couple engrené ;
 7. interférence volontaire (spec « sale ») : détectée sur la grille (pas à la première image), verdict ÉCHEC ;
 --full : build_v2.py et check.py en sous-processus (V2_KEPLER_SPEC, V2_KEPLER_TOOLS, V2_OUT ; check relit les
 chemins enregistrés dans la scène), propre (code 0) et sale (code 1).
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
for p in (HERE, os.path.join(HERE, 'lib')):
    if p not in sys.path:
        sys.path.insert(0, p)

import animate  # noqa: E402
import check_lib as CL  # noqa: E402
import kepler_build as KB  # noqa: E402
import kepler_fake as F  # noqa: E402
import kepler_geom as KG  # noqa: E402
from lib import meshing as MESHING  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FRAMES = (1, 2, 57, 183, 300, 366)
TMP = {}


def setUpModule():
    TMP['dir'] = tempfile.mkdtemp(prefix='v2_kepler_test_')
    TMP['env'] = {k: os.environ.pop(k) for k in ('V2_KEPLER_SPEC', 'V2_KEPLER_TOOLS', 'V2_OUT') if k in os.environ}
    for name, dirty in (('propre', False), ('sale', True)):
        TMP[name] = F.write(os.path.join(TMP['dir'], name), dirty)


def tearDownModule():
    os.environ.update(TMP['env'])
    if '--keep' in ARGS:
        print('dossier gardé :', TMP['dir'])
    else:
        shutil.rmtree(TMP['dir'], ignore_errors=True)


def build(name):
    """build_v2.main() dans ce processus, sortie dans le dossier temporaire ; renvoie build_report.json."""
    import build_v2
    spec, tools = TMP[name]
    out = os.path.join(TMP['dir'], name, 'out')
    old = sys.argv
    sys.argv = [old[0], '--', '--out', out, '--kepler-spec', spec, '--kepler-tools', tools]
    try:
        build_v2.main()
    finally:
        sys.argv = old
    with open(os.path.join(out, 'build_report.json')) as f:
        return json.load(f)


def run_check(*extra):
    import check
    return check.run_checks(check.parse_args(['check.py', '--', '--samples', '24'] + list(extra)))


def shoelace(p):
    p = np.asarray(p, float)
    return 0.5 * abs(float(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])))


class T1Inactif(unittest.TestCase):
    def test_paths_and_inactive(self):
        if os.path.exists(KB.DEFAULT_SPEC):
            self.skipTest('v2/spec/kepler.json existe : la chaîne réelle est active')
        self.assertIsNone(KB.activate(['blender']))
        x = KB.paths(['b', '--', '--kepler-spec', 'a.json', '--kepler-tools', 'd'])
        self.assertEqual((x['spec'], x['tools']), (os.path.abspath('a.json'), os.path.abspath('d')))
        os.environ['V2_KEPLER_SPEC'] = '/nulle/part/kepler.json'
        try:
            self.assertEqual(KB.paths(['b'])['spec'], '/nulle/part/kepler.json')
            with self.assertRaises(FileNotFoundError):
                KB.activate(['b'])
        finally:
            del os.environ['V2_KEPLER_SPEC']


class T2Scene(unittest.TestCase):
    def test_prepare_scene(self):
        with open(os.path.join(V2, 'spec', 'scene.json')) as f:
            parts = json.load(f)['parts']
        plist, info = KB.prepare_scene(parts, KB.load_spec(TMP['propre'][0]))
        idx = {p['id']: p for p in plist}
        self.assertEqual(info['replaced'], ['mod_mars', 'orr_mars#prise_axe', 'uak_mars'])
        self.assertEqual(len(plist), len(parts) - 3)
        self.assertIn('uak_venus', idx)
        self.assertEqual(idx['orr_mars#prise']['c'], [28.0, 93.0])
        self.assertEqual(idx['orr_mars#r0']['p'], [28.0, 93.0])
        self.assertEqual(idx['orr_mars#m0p~z']['c'], [28.0, 93.0])        # synth : suit sa source
        gone = set(info['replaced'])
        for p in plist:
            for k in ('links', 'meshes_with', 'engages'):
                self.assertFalse(gone & set(p.get(k) or []), p['id'])
        self.assertEqual(next(p for p in parts if p['id'] == 'orr_mars#prise')['c'], [28.0, 92.0])  # copie


class T3Geometrie(unittest.TestCase):
    def test_islands_and_areas(self):
        crank = next(p for p in F.spec()['towers']['mars']['parts'] if p['id'] == 'mars#manivelle')
        isl = [KG.shape_island(s) for s in crank['shapes']]
        self.assertTrue(KG.islands_overlap(isl))
        far = [KG.shape_island({'type': 'circle', 'c': [0, 0], 'r': 1}),
               KG.shape_island({'type': 'circle', 'c': [5, 0], 'r': 1})]
        self.assertFalse(KG.islands_overlap(far))
        me, info = KG.shapes_mesh('t_union', crank['shapes'], 2.0)
        rep = CL.check_mesh(me)
        self.assertTrue(info['union'] and rep['ok'], rep)
        ring = shoelace(F.circle_pts(6.5)) - shoelace(F.circle_pts(4.05))
        bar = 6.5 * 4.0 - shoelace(F.circle_pts(0.75, (10, 0), 32))
        lens = 2 * math.sqrt(6.5 ** 2 - 4) + 6.5 ** 2 * math.asin(2 / 6.5) - 5.0 * 4.0   # barre ∩ disque r 6,5
        self.assertAlmostEqual(rep['volume'] / 2.0, ring + bar - lens, delta=0.05)

    def test_pierced_arm_area(self):
        arm = next(p for p in F.spec()['towers']['mars']['parts'] if p['id'] == 'mars#bras')
        me, info = KG.shapes_mesh('t_bras', arm['shapes'], 2.4)
        sh = arm['shapes'][0]
        area = shoelace(sh['outer']) - sum(shoelace(h) for h in sh['holes'])
        rep = CL.check_mesh(me)
        self.assertTrue(rep['ok'], rep)
        self.assertEqual(MESHING.check_mesh(me)['shells'], 1)
        self.assertAlmostEqual(rep['volume'] / 2.4, area, delta=1e-3 * area)


class T4Propre(unittest.TestCase):
    """Construction, animation et contrôle de la fausse tour propre (un seul build, un seul contrôle)."""

    @classmethod
    def setUpClass(cls):
        cls.rep = build('propre')
        cls.api = KB.load_api(TMP['propre'][1])
        cls.kp = {p['id']: p for p in KB.kepler_parts(KB.load_spec(TMP['propre'][0]))}
        cls.chk = run_check()

    def test_1_objects(self):
        k = self.rep['kepler']
        self.assertEqual((k['parts'], k['failures'], k['unions']), (7, [], 1))
        self.assertEqual(self.rep['parts'], 412)
        for gone in ('uak_mars', 'mod_mars', 'orr_mars.prise_axe'):
            self.assertIsNone(bpy.data.objects.get(gone))
        self.assertIsNotNone(bpy.data.objects.get('uak_venus'))
        top = bpy.data.collections['V2_Kepler']
        self.assertEqual([c.name for c in top.children], ['V2_Kepler_mars'])
        root = bpy.data.objects['V2_K_mars']
        self.assertEqual(tuple(root['kepler_origin']), F.A)
        for pid in self.kp:
            o = bpy.data.objects[pid.replace('#', '.')]
            self.assertEqual((o.parent, o['part_id'], o['tower'], o['kepler']), (root, pid, 'mars', 1))
            self.assertTrue(CL.check_mesh(o.data)['ok'], pid)
            self.assertAlmostEqual(o.location[2], sum(self.kp[pid]['z']) / 2.0, places=4)
        bras, prise = bpy.data.objects['mars.bras'], bpy.data.objects['mars.prise']
        self.assertEqual(tuple(bras.matrix_world.translation[:2]), F.E)        # origine au pivot
        self.assertEqual(bpy.data.objects['mars.bague']['motion'], 'fixed')
        self.assertEqual((bras['motion'], bras['law'], bras['kind']), ('kepler', 'mars:equant', 'slotted_arm'))
        self.assertEqual(list(prise['meshes_with']), ['orr_mars.prise'])
        self.assertEqual(prise['teeth'], 46)
        self.assertAlmostEqual(prise['bore'], 5.65, places=9)
        self.assertEqual(prise.data.materials[0].name, 'V2_brass')
        self.assertEqual(bpy.data.objects['mars.goupille'].data.materials[0].name, 'V2_steel')
        V = np.array([v.co[:2] for v in prise.data.vertices])
        r = np.hypot(V[:, 0], V[:, 1])
        self.assertAlmostEqual(float(r.max()), 12.0, delta=2e-3)                  # tête : m (z/2 + 1)
        self.assertAlmostEqual(float(r.min()), 5.65, delta=1e-4)                  # alésage
        f = bpy.data.objects['orr_mars.prise']
        self.assertEqual((f['motion'], f['kepler_follow']), ('kepler', 'mars#prise'))
        self.assertEqual(tuple(round(v, 6) for v in f.location[:2]), (28.0, 93.0))   # override

    def test_2_animation(self):
        sc, worst = bpy.context.scene, {'loc': 0.0, 'rad': 0.0, 'world': 0.0}
        ox, oy = F.A
        for fr in FRAMES:
            sc.frame_set(fr)
            dg = bpy.context.evaluated_depsgraph_get()
            j = animate.jours_at_frame(fr)
            for pid, part in self.kp.items():
                o = bpy.data.objects[pid.replace('#', '.')].evaluated_get(dg)
                x, y, th = self.api.pose(part, self.api.state_from_jours('mars', j))
                worst['loc'] = max(worst['loc'], abs(o.location[0] - (x - ox)), abs(o.location[1] - (y - oy)))
                worst['rad'] = max(worst['rad'], abs(CL.wrap(o.rotation_euler[2] - th)))
                M = np.array(o.matrix_world)
                worst['world'] = max(worst['world'], math.hypot(M[0, 3] - x, M[1, 3] - y))
            f = bpy.data.objects['orr_mars.prise'].evaluated_get(dg)
            th = self.api.pose(self.kp['mars#prise'], self.api.state_from_jours('mars', j))[2]
            worst['rad'] = max(worst['rad'], abs(CL.wrap(f.rotation_euler[2] - (-th + f['follow_offset']))))
        print('\n[kepler] relecture des images clés : %s' % {k: '%.2e' % v for k, v in worst.items()})
        self.assertLessEqual(worst['loc'], 1e-6)
        self.assertLessEqual(worst['rad'], 1e-6)
        self.assertLessEqual(worst['world'], 2e-5)
        st = self.rep['animation']
        self.assertEqual(st['kepler'], 7)                       # 6 pièces mobiles + la roue menée
        self.assertLess(st['kepler_max_step_rad'], 0.1)

    def test_3_check(self):
        s, k = self.chk['summary'], self.chk['kepler']
        self.assertTrue(s['ok'], s['failures'])
        self.assertTrue(k['ok'], k['failures'])
        self.assertGreaterEqual(k['states']['grid'], 48)
        self.assertEqual(k['states']['total'], k['states']['grid'] + 12)
        self.assertEqual((k['meshes']['checked'], k['collisions_count']), (7, 0))
        self.assertEqual(k['pairs']['kepler_kepler'], 4)
        self.assertGreater(k['bvh_tests'], 0)
        self.assertLess(k['readback']['err_mm'], 1e-4)
        row = next(r for r in self.chk['pairs']['rows'] if {r['a'], r['b']} == {'mars.prise', 'orr_mars.prise'})
        self.assertEqual((row['samples'], row['overlapping_samples']), (24, 0))
        print('\n[kepler] contrôle propre : %s' % {x: s['counts'][x] for x in s['counts'] if x.startswith('kepler')})


class T5Sale(unittest.TestCase):
    """Intrus volontaires : le contrôle DOIT les trouver (grille de l'espace d'état) et échouer."""

    def test_detected(self):
        rep = build('sale')
        self.assertEqual(rep['kepler']['parts'], 9)
        chk = run_check('--quick')
        k, s = chk['kepler'], chk['summary']
        self.assertFalse(s['ok'])
        self.assertFalse(k['ok'])
        self.assertTrue(any('recouvrements Kepler' in x for x in s['failures']), s['failures'])
        pairs = {frozenset((c['a'], c['b'])): c for c in k['collisions']}
        for a, b in (('mars.intrus_LT', 'mars.bras'), ('mars.intrus_LT', 'mars.goupille'),
                     ('mars.intrus_tige', 'orr_mars.r0')):
            self.assertIn(frozenset((a, b)), pairs, (a, b))
        c = pairs[frozenset(('mars.intrus_LT', 'mars.bras'))]
        self.assertEqual(c['first_state']['kind'], 'grille')
        static = {frozenset((x['a'], x['b'])) for x in chk['static']['collisions']}
        self.assertNotIn(frozenset(('mars.intrus_LT', 'mars.bras')), static)   # invisible à la première image
        print('\n[kepler] intrus détectés : %s' % sorted('%s/%s (%d états)' % (c['a'], c['b'], c['states'])
                                                         for c in k['collisions']))


@unittest.skipUnless('--full' in ARGS, 'option --full')
class T6SousProcessus(unittest.TestCase):
    """Chaîne réelle en sous-processus : variables d'environnement, puis check.py sans option Kepler."""

    def run_chain(self, name):
        spec, tools = TMP[name]
        out = os.path.join(TMP['dir'], name, 'full')
        env = dict(os.environ, V2_KEPLER_SPEC=spec, V2_KEPLER_TOOLS=tools, V2_OUT=out)
        b = subprocess.run([bpy.app.binary_path, '-b', '--factory-startup', '--python-exit-code', '1', '-P',
                            os.path.join(HERE, 'build_v2.py')], env=env, capture_output=True, text=True)
        self.assertEqual(b.returncode, 0, b.stdout[-2000:] + b.stderr[-2000:])
        c = subprocess.run([bpy.app.binary_path, '-b', os.path.join(out, 'v2.blend'), '--python-exit-code', '1',
                            '-P', os.path.join(HERE, 'check.py'), '--', '--quick', '--out',
                            os.path.join(out, 'check.json')], capture_output=True, text=True)
        with open(os.path.join(out, 'check.json')) as f:
            return c.returncode, json.load(f)

    def test_full(self):
        code, rep = self.run_chain('propre')
        self.assertEqual(code, 0, rep['summary']['failures'])
        self.assertTrue(rep['kepler']['ok'])
        code, rep = self.run_chain('sale')
        self.assertEqual(code, 1)
        self.assertGreaterEqual(rep['kepler']['collisions_count'], 3)


if __name__ == '__main__':
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(
        sys.modules[__name__]))
    print('test_kepler_build : %s' % ('OK' if res.wasSuccessful() else 'ÉCHEC'))
    if not res.wasSuccessful():
        raise SystemExit(1)
