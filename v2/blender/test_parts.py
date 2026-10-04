"""Tests de parts.py, à lancer dans Blender :
  $BL -b --factory-startup --python-exit-code 1 -P blender/test_parts.py [-- --arch]
Petite scène factice : couple engrené, couronne intérieure + pignon, tringles, platine percée, blocs, couronne de
champ + conique. Contrôles : maillages variétés (aucune arête non-variété, volume > 0), pas de recouvrement BVH du
couple engrené à sa phase (et recouvrement détecté à une phase fausse), propriétés, partage des maillages, temps.
`--arch` : construit en plus toutes les pièces de spec/architecture.json (essai de charge, sans contrôle BVH).
"""
import json
import math
import os
import sys
import time
import unittest

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts as P  # noqa: E402
from lib.involute import mesh_phase  # noqa: E402
from lib.meshing import check_mesh  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def internal_phase(phi1, beta, z1, z2):
    """Phase de la couronne intérieure (angle de sa DENT 0, comme toute roue) menée par un pignon intérieur
    (dent 0 en phi1) ; beta = direction centre de la couronne -> centre du pignon. Même sens de rotation. Le creux
    0 de la couronne (dent 0 de sa roue virtuelle) est en beta + (z1/z2)(phi1 − beta) ; sa dent 0 un demi-pas plus
    loin."""
    return beta + (z1 / z2) * (phi1 - beta) + math.pi / z2


def fake_scene():
    """Scène factice (repère machine, mm)."""
    m, z1, z2 = 0.5, 20, 60
    b = math.radians(30.0)
    a = m * (z1 + z2) / 2.0
    c2 = [a * math.cos(b), a * math.sin(b)]
    ph1 = 0.1
    ph2 = mesh_phase(ph1, b, z1, z2)
    rc = [80.0, 0.0]
    bi = math.radians(-50.0)
    ai = m * (z2 - z1) / 2.0
    pc = [rc[0] + ai * math.cos(bi), rc[1] + ai * math.sin(bi)]
    phr = internal_phase(0.2, bi, z1, z2)
    base = {'motion': 'linear', 'rate': 0.01, 'phys': 1, 'collection': 'V2_Trains', 'source': 'test'}
    S = [
        dict(base, id='tst#w1', kind='gear', c=[0.0, 0.0], z=[131.0, 134.0], teeth=z1, m=m, mesh='external',
             phase=ph1, meshes_with=['tst#w2'], links=['tst#a1', 'tst#w2']),
        dict(base, id='tst#w2', kind='gear', c=c2, z=[131.0, 134.0], teeth=z2, m=m, mesh='external', phys=-1,
             phase=ph2, meshes_with=['tst#w1'], links=['tst#w1']),
        dict(base, id='tst#a1', kind='arbor', c=[0.0, 0.0], z=[125.0, 155.0], r=2.0, phase=ph1, links=['tst#w1']),
        dict(base, id='tst#ring', kind='gear', c=rc, z=[131.0, 134.0], teeth=z2, m=m, mesh='internal', phase=phr,
             meshes_with=['tst#pin']),
        dict(base, id='tst#pin', kind='gear', c=pc, z=[131.0, 134.0], teeth=z1, m=m, mesh='external', phase=0.2,
             meshes_with=['tst#ring']),
        dict(base, id='tst#w3', kind='gear', c=[0.0, -60.0], z=[131.0, 134.0], teeth=z1, m=m, phase=0.7),
        dict(base, id='tst#r1', kind='rod', p=[0.0, 50.0], q=[60.0, 80.0], z=[204.0, 219.0], r=1.5),
        dict(base, id='tst#r2', kind='rod', p=[100.0, 70.0], q=[100.0, 10.0], z=[204.0, 219.0], r=1.5),
        {'id': 'P4', 'kind': 'plate', 'x': [-50.0, 150.0], 'y': [-90.0, 100.0], 'z': [123.0, 125.0],
         'motion': 'fixed', 'collection': 'V2_Platines',
         'holes': [{'c': [0.0, 0.0], 'r': 2.3}, [c2[0], c2[1], 2.3], [80.0, 0.0, 6.0], [83.0, 0.0, 6.0],
                   {'c': [400.0, 0.0], 'r': 3.0}, [[20.0, -80.0], [30.0, -80.0], [30.0, -70.0], [20.0, -70.0]]]},
        {'id': 'lune', 'kind': 'block', 'c': [40.0, -40.0], 'r': 15.0, 'z': [48.0, 97.0], 'motion': 'fixed',
         'label': 'à dessiner', 'collection': 'V2_Blocs'},
        {'id': 'cal_anneau', 'kind': 'block', 'c': [-112.0, 15.0], 'r': 30.0, 'r_in': 24.0, 'z': [3.0, 9.0],
         'motion': 'fixed', 'collection': 'V2_Blocs'},
        dict(base, id='Y4a', kind='crown', c=[200.0, 0.0], z=[155.0, 170.0], teeth=96, m=0.4,
             meshes_with=['bus#pin0'], links=['axe_Y']),
        dict(base, id='axe_Y', kind='axis', c=[200.0, 0.0], z=[100.0, 200.0], r=4.0),
        dict(base, id='bus#pin0', kind='gear', mesh='crown', c=[217.2, 0.0], z=[155.0, 170.0], teeth=24, m=0.4,
             axis=[1.0, 0.0, 0.0], rod='bus#rod', phase=math.pi / 24, meshes_with=['Y4a'], links=['Y4a']),
        dict(base, id='bus#rod', kind='rod', p=[217.2, 0.0], q=[260.0, 0.0], z=[155.0, 170.0], r=1.5),
        dict(base, id='bus#m1q', kind='bevel', c=[260.0, 0.0], z=[155.0, 170.0], axis=[1.0, 0.0, 0.0],
             rod='bus#rod', phase=math.pi / 24, meshes_with=['car#mitre']),
        dict(base, id='car#mitre', kind='bevel', c=[260.0, 0.0], z=[155.0, 170.0], axis=[0.0, 0.0, 1.0],
             links=['car#a'], meshes_with=['bus#m1q']),
        dict(base, id='car#a', kind='arbor', c=[260.0, 0.0], z=[162.5, 230.0], r=2.0),
        dict(base, id='tube_moon', kind='tube', c=[-60.0, 40.0], z=[100.0, 140.0], r=4.0, r_in=2.05),
        dict(base, id='misc1', kind='misc', c=[-60.0, -40.0], z=[100.0, 110.0], r=3.0),
        dict(base, id='tst#wneg', kind='gear', c=[0.0, -120.0], z=[131.0, 134.0], teeth=z1, m=m, phase=0.3,
             axis=[0.0, 0.0, -1.0]),
    ]
    return S


def world_tris(obj):
    """Triangles de l'objet dans le repère monde (pour BVHTree)."""
    me = obj.data
    me.calc_loop_triangles()
    mw = obj.matrix_world
    V = [mw @ v.co for v in me.vertices]
    T = [tuple(t.vertices) for t in me.loop_triangles]
    return V, T


def overlap(o1, o2):
    bpy.context.view_layer.update()
    t1 = BVHTree.FromPolygons(*world_tris(o1))
    t2 = BVHTree.FromPolygons(*world_tris(o2))
    return len(t1.overlap(t2))


class PartsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        P.reset_cache()
        t0 = time.perf_counter()
        cls.mats = P.materials()
        cls.t_mat = time.perf_counter() - t0
        cls.scene = fake_scene()
        cls.index = {p['id']: p for p in cls.scene}
        cls.colls = {}
        cls.objs, cls.times = {}, {}
        for p in cls.scene:
            t = time.perf_counter()
            cls.objs[p['id']] = P.build_part(p, cls.colls, cls.mats, cls.index)
            cls.times[p['id']] = time.perf_counter() - t
        bpy.context.view_layer.update()

    def test_materials(self):
        for k in ('brass', 'bronze', 'steel', 'glass', 'oak', 'block_translucent', 'dial_dark', 'text'):
            self.assertIn(k, self.mats)
        pb = P._principled(self.mats['block_translucent'])
        self.assertAlmostEqual(pb.inputs['Alpha'].default_value, 0.25, places=6)
        self.assertIs(P.materials()['brass'], self.mats['brass'])        # pas de doublon

    def test_manifold(self):
        for pid, o in self.objs.items():
            r = check_mesh(o.data)
            print('  %-12s %-6s %6d sommets %5d faces  coques %3d  volume %10.2f mm3  %.3f s' % (
                pid, o['kind'], r['verts'], r['faces'], r['shells'], r['volume'], self.times[pid]))
            self.assertTrue(r['ok'], (pid, r))
            if o['kind'] in ('gear', 'crown', 'bevel', 'rod', 'arbor'):
                self.assertEqual(r['shells'], 1, pid)

    def test_meshing_pair_no_overlap(self):
        w1, w2 = self.objs['tst#w1'], self.objs['tst#w2']
        self.assertEqual(overlap(w1, w2), 0)
        ring, pin = self.objs['tst#ring'], self.objs['tst#pin']
        self.assertEqual(overlap(ring, pin), 0)
        # contrôle du contrôle : une demi-dent de décalage doit faire chevaucher les dentures
        for o, z in ((w2, 60), (ring, 60)):
            o.rotation_euler.z += math.pi / z
            n = overlap(w1 if o is w2 else pin, o)
            o.rotation_euler.z -= math.pi / z
            self.assertGreater(n, 0, o.name)

    def test_rotation_keeps_mesh_clean(self):
        """La phase est dans la rotation de l'objet, pas dans le maillage : même maillage pour w1 et w3."""
        w1, w3 = self.objs['tst#w1'], self.objs['tst#w3']
        self.assertIs(w1.data, w3.data)
        self.assertAlmostEqual(w1.rotation_euler.z, 0.1)
        self.assertAlmostEqual(w3.rotation_euler.z, 0.7)
        self.assertEqual(w1.rotation_mode, 'XYZ')
        self.assertAlmostEqual(w1['bore'], 2.05)                    # arbre lié r 2 + 0,05
        self.assertEqual(self.objs['tst#w2']['n_windows'], 5)       # rayon primitif 15 > 12 : fenêtres

    def test_props_and_names(self):
        o = self.objs['tst#w1']
        self.assertEqual(o.name, 'tst.w1')
        self.assertEqual(o['motion'], 'linear')
        self.assertEqual(list(o['meshes_with']), ['tst.w2'])
        self.assertEqual(P.prop_list(o, 'links'), ['tst.a1', 'tst.w2'])
        self.assertEqual(o['spin'], 'Z')
        self.assertEqual(list(o['axis']), [0.0, 0.0, 1.0])
        self.assertEqual(o.users_collection[0].name, 'V2_Trains')
        self.assertIn('V2_Platines', self.colls)

    def test_rods(self):
        for pid in ('tst#r1', 'tst#r2'):
            p = self.index[pid]
            o = self.objs[pid]
            L = math.dist(p['p'], p['q'])
            zm = sum(p['z']) / 2
            ends = sorted([tuple(o.matrix_world @ Vector((s * L / 2, 0, 0))) for s in (-1, 1)])
            exp = sorted([(p['p'][0], p['p'][1], zm), (p['q'][0], p['q'][1], zm)])
            np.testing.assert_allclose(ends, exp, atol=1e-4)
            self.assertEqual(o['spin'], 'X')
        self.assertEqual(list(self.objs['tst#r2']['axis']), [0.0, 1.0, 0.0])   # tringle verticale : +Y

    def test_plate(self):
        o = self.objs['P4']
        self.assertIn('fusionnés', o['warnings'])
        self.assertIn('hors du contour', o['warnings'])
        r = check_mesh(o.data)
        area = 200 * 190 - (4 - math.pi) * 16 - 2 * math.pi * 2.3 ** 2 - 100     # coins r 4, 2 trous, carré
        merged = (3.0 + 6.0 + 6.0) / 2
        area -= math.pi * merged ** 2
        self.assertAlmostEqual(r['volume'] / 2.0, area, delta=0.005 * area)

    def test_blocks(self):
        o = self.objs['lune']
        lab = [c for c in o.children if c.type == 'FONT']
        self.assertEqual(len(lab), 1)
        self.assertIn('à dessiner', lab[0].data.body)
        mat = o.material_slots[0].material
        self.assertEqual(mat.name, 'V2_block_translucent')

    def test_crown_bevel(self):
        cr, pn = self.objs['Y4a'], self.objs['bus#pin0']
        self.assertAlmostEqual(cr['bore'], 4.05)                     # axe lié r 4
        self.assertAlmostEqual(pn['bore'], 1.55)                     # tringle porteuse r 1,5
        self.assertEqual(pn['spin'], 'X')
        self.assertAlmostEqual(pn.dimensions.x, 4.0, places=4)       # pignon couché : largeur 10 m
        b1, b2 = self.objs['bus#m1q'], self.objs['car#mitre']
        self.assertEqual((b1['apex'], b2['apex']), (1, -1))          # corps vers la tringle / le long de l'arbre
        self.assertAlmostEqual(b1['bore'], 1.55)
        self.assertAlmostEqual(b2['bore'], 2.05)
        self.assertEqual(b2['spin'], 'Z')

    def test_crown_and_mitre_mesh(self):
        """Couronne + pignon couché, et paire d'onglet au concours des axes : aucun recouvrement en roulant
        (rapports 96:24 et 1:1, un pas de la roue lente), recouvrement à une demi-dent de décalage."""
        cr, pn = self.objs['Y4a'], self.objs['bus#pin0']
        b1, b2 = self.objs['bus#m1q'], self.objs['car#mitre']
        for (a, b, pitch) in ((cr, pn, 2 * math.pi / 96), (b2, b1, 2 * math.pi / 24)):
            a0, b0 = a.rotation_euler.copy(), b.rotation_euler.copy()
            ia, ib = a['spin_index'], b['spin_index']
            mid, ph, k = P.engage_phase(self.index[a['part_id']], self.index[b['part_id']], self.index)
            self.assertEqual(mid, b['part_id'])
            self.assertAlmostEqual(ph, b0[ib] % (2 * math.pi / 24), places=6)   # rotation en float32
            n = []
            for s in range(7):                                       # sens imposé par la formule : dφ = k·dθ
                d = s / 6 * pitch
                a.rotation_euler[ia] = a0[ia] + d
                b.rotation_euler[ib] = b0[ib] + k * d
                n.append(overlap(a, b))
            a.rotation_euler, b.rotation_euler = a0, b0
            self.assertEqual(sum(n), 0, (a.name, b.name, n))
            b.rotation_euler[ib] += math.pi / (24 if b is pn or b is b1 else 96)
            self.assertGreater(overlap(a, b), 0, (a.name, b.name))
            b.rotation_euler = b0

    def test_zz_timing(self):
        print('\nmatériaux : %.3f s' % self.t_mat)
        print(P.stats_text())
        t = time.perf_counter()
        o = P.build_part({'id': 'big#w', 'kind': 'gear', 'c': [0, 0], 'z': [0, 3], 'teeth': 189, 'm': 0.5},
                         None, self.mats)
        dt = time.perf_counter() - t
        t = time.perf_counter()
        P.build_part({'id': 'big#w2', 'kind': 'gear', 'c': [0, 0], 'z': [10, 13], 'teeth': 189, 'm': 0.5},
                     None, self.mats)
        dt2 = time.perf_counter() - t
        print('roue 189 dents : %.3f s (%d sommets) ; doublon lié : %.4f s' % (dt, len(o.data.vertices), dt2))
        self.assertLess(dt2, 0.05)
        self.assertTrue(check_mesh(o.data)['ok'])


    def test_axis_minus_z_and_default_collection(self):
        o = self.objs['tst#wneg']
        self.assertEqual((o['spin'], o['spin_sign']), ('Z', -1))
        self.assertAlmostEqual(o.rotation_euler.z, -0.3)               # rotation de 0,3 autour de −Z
        self.assertIs(o.data, self.objs['tst#w1'].data)                # même maillage le long de +Z
        coll = bpy.data.collections.new('T_defaut')
        x = P.build_part({'id': 'sans#coll', 'kind': 'arbor', 'c': [0, 0], 'z': [0, 5], 'r': 2.0},
                         {'_default': coll}, self.mats)
        self.assertEqual(x.users_collection[0].name, 'T_defaut')

    def test_zzz_cache_after_reset(self):
        """Après une réinitialisation du fichier (sans reset_cache), un maillage homonyme n'est pas réutilisé."""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mats = P.materials()
        g = {'kind': 'gear', 'c': [0, 0], 'z': [0, 3], 'teeth': 20, 'm': 0.5}
        a = P.build_part(dict(g, id='k#a', bore=3.05), None, mats)       # même nom de maillage, autre alésage
        b = P.build_part(dict(g, id='k#b'), None, mats)                  # clé de tst#w1 (alésage 2,05)
        self.assertIsNot(a.data, b.data)
        self.assertAlmostEqual(a['bore'], 3.05)
        self.assertAlmostEqual(b['bore'], 2.05)
        self.assertTrue(check_mesh(b.data)['ok'])

class EngageTest(unittest.TestCase):
    """Conventions de phase des contacts hors roues droites (engage_phase) à des azimuts quelconques, faces et
    sommets dans tous les sens, et autres règles de construction (alésage, tube creux, conique d'axe −Z, étiquette)."""

    @classmethod
    def setUpClass(cls):
        cls.mats = P.materials()
        base = {'motion': 'linear', 'rate': 0.01, 'phys': 1, 'collection': 'V2_Essais'}
        S = []
        for i, f in enumerate((1, -1)):                              # deux couronnes : dents vers +Z, vers −Z
            cc = [600.0 + 120.0 * i, 0.0]
            S.append(dict(base, id='E#cr%d' % i, kind='crown', c=cc, z=[155.0, 170.0], face=f, phase=0.05 + i,
                          links=[]))
            for j, (gd, s) in enumerate(((31.8, 1), (100.0, -1), (217.0, 1))):
                g = math.radians(gd)
                u = [s * math.cos(g), s * math.sin(g), 0.0]
                S.append(dict(base, id='E#p%d%d' % (i, j), kind='gear', mesh='crown', teeth=24, m=0.4, width=4.0,
                              c=[cc[0] + 17.2 * math.cos(g), cc[1] + 17.2 * math.sin(g)], z=[155.0, 170.0],
                              axis=u, phase=0.0))
        for i, (aV, aL) in enumerate(((-1, 1), (1, -1), (1, 1), (-1, -1))):  # onglets : 4 combinaisons de sommets
            g = math.radians(137.0)
            c = [600.0 + 60.0 * i, 200.0]
            S.append(dict(base, id='E#v%d' % i, kind='bevel', c=c, z=[204.0, 219.0], axis=[0, 0, 1], apex=aV,
                          phase=0.3))
            S.append(dict(base, id='E#l%d' % i, kind='bevel', c=c, z=[204.0, 219.0],
                          axis=[math.cos(g), math.sin(g), 0.0], apex=aL, phase=0.0))
        cls.I = {p['id']: p for p in S}
        cls.pairs = [('E#cr%d' % i, 'E#p%d%d' % (i, j)) for i in range(2) for j in range(3)]
        cls.pairs += [('E#v%d' % i, 'E#l%d' % i) for i in range(4)]
        for a, b in cls.pairs:
            mid, ph, k = P.engage_phase(cls.I[a], cls.I[b])
            cls.I[mid]['phase'] = ph
        cls.O = {pid: P.build_part(p, {}, cls.mats, cls.I) for pid, p in cls.I.items()}

    def test_engage_any_azimuth(self):
        """Phase de la formule : aucun recouvrement au repos ni en roulant (dφ = k·dθ) ; demi-pas : recouvrement."""
        for a, b in self.pairs:
            oa, ob = self.O[a], self.O[b]
            _, _, k = P.engage_phase(self.I[a], self.I[b])
            ia, ib = oa['spin_index'], ob['spin_index']
            a0, b0 = oa.rotation_euler[ia], ob.rotation_euler[ib]
            pitch = 2 * math.pi / (96 if self.I[a]['kind'] == 'crown' else 24)
            n = []
            for s in range(6):
                oa.rotation_euler[ia] = a0 + s / 5 * pitch
                ob.rotation_euler[ib] = b0 + k * s / 5 * pitch
                n.append(overlap(oa, ob))
            oa.rotation_euler[ia] = a0
            ob.rotation_euler[ib] = b0 + math.pi / 24
            n_bad = overlap(oa, ob)
            ob.rotation_euler[ib] = b0
            self.assertEqual(sum(n), 0, (a, b, n))
            self.assertGreater(n_bad, 0, (a, b))

    def test_bores_and_hollow_tube(self):
        """Un tube coaxial non lié qui traverse la roue impose l'alésage ; un tube sans r_in est creux."""
        I = {
            'T#tube': {'id': 'T#tube', 'kind': 'tube', 'c': [800.0, -200.0], 'z': [131.0, 155.0], 'r': 4.0},
            'T#axe': {'id': 'T#axe', 'kind': 'axis', 'c': [800.0, -200.0], 'z': [125.0, 155.0], 'r': 2.0},
            'T#w0': {'id': 'T#w0', 'kind': 'gear', 'c': [800.0, -200.0], 'z': [131.0, 134.0], 'teeth': 24,
                     'm': 0.5, 'links': ['T#axe']},
            'T#cour': {'id': 'T#cour', 'kind': 'crown', 'c': [800.0, -200.0], 'z': [140.0, 155.0], 'links': []},
        }
        O = {k: P.build_part(p, {}, self.mats, I) for k, p in I.items()}
        self.assertAlmostEqual(O['T#w0']['bore'], 4.05)
        self.assertAlmostEqual(O['T#cour']['bore'], 4.05)
        self.assertAlmostEqual(O['T#tube']['r_in'], 2.05)
        self.assertTrue(check_mesh(O['T#tube'].data)['ok'])
        for a, b in (('T#tube', 'T#axe'), ('T#w0', 'T#tube'), ('T#cour', 'T#tube'), ('T#w0', 'T#axe')):
            self.assertEqual(overlap(O[a], O[b]), 0, (a, b))
        solo = P.build_part({'id': 'T#seul', 'kind': 'tube', 'c': [0, 0], 'z': [0, 5], 'r': 4.0}, {}, self.mats)
        self.assertAlmostEqual(solo['r_in'], 2.05)                     # sans index : arbre par défaut

    def test_scene_index_fallback(self):
        """Sans `index`, une pièce identique à celle de spec/scene.json trouve ses supports dans ce fichier."""
        si = P.scene_index()
        if not si:
            self.skipTest('spec/scene.json absent')
        for p in si.values():
            sup = [o['r'] for o in P.coaxial_supports(p, si)] if p['kind'] == 'gear' else []
            if sup and max(sup) > P.ARBOR_R + 1e-6 and p.get('mesh') == 'external':
                o = P.build_part(p, {}, self.mats)
                self.assertAlmostEqual(o['bore'], max(sup) + P.BORE_CLEAR, places=6)
                q = dict(p, id=p['id'] + '_copie')                     # pièce hors scène : pas d'index implicite
                self.assertAlmostEqual(P.build_part(q, {}, self.mats)['bore'], P.ARBOR_R + P.BORE_CLEAR)
                return
        self.skipTest('aucune roue sur un support épais dans scene.json')

    def test_bevel_minus_z(self):
        """`apex` est rapporté à l'axe : axe −Z et apex +1 = sommet en bas, corps vers +Z (comme axe +Z, apex −1)."""
        q = {'kind': 'bevel', 'c': [900.0, 0.0], 'z': [10.0, 20.0]}
        o1 = P.build_part(dict(q, id='M#a', axis=[0, 0, -1], apex=1), {}, self.mats)
        o2 = P.build_part(dict(q, id='M#b', axis=[0, 0, 1], apex=-1), {}, self.mats)
        self.assertIs(o1.data, o2.data)
        self.assertEqual(o1['apex'], 1)
        self.assertGreater(min(v.co.z for v in o1.data.vertices), -1e-6)

    def test_label_fits(self):
        """Une longue étiquette tient dans l'empreinte du bloc (disque et anneau)."""
        long = 'cascade lunaire à 5 étages, coulisse, différentiel, ' * 4
        for pid, r, r_in in (('L#disque', 50.0, None), ('L#anneau', 96.0, 84.0), ('L#petit', 8.0, None)):
            o = P.build_part({'id': pid, 'kind': 'block', 'c': [0.0, 900.0], 'z': [0.0, 10.0], 'r': r,
                              'r_in': r_in, 'label': long, 'motion': 'fixed'}, {}, self.mats)
            lab = [c for c in o.children if c.type == 'FONT'][0]
            bpy.context.view_layer.update()
            W, H = lab['label_box']
            self.assertTrue(lab.data.body.startswith(pid), pid)
            self.assertLessEqual(lab.dimensions.x, W * 1.02, pid)
            self.assertLessEqual(lab.dimensions.y, H * 1.02 + 0.5 * lab.data.size, pid)
            self.assertNotIn('part_id', lab.keys())


def arch_parts():
    """Pièces approchées depuis architecture.json (en attendant scene.json) : roues, couronnes de moyeu (r 20),
    coniques (r 5,6), tringles, arbres, blocs."""
    A = json.load(open(os.path.join(HERE, '..', 'spec', 'architecture.json')))
    out = []
    for it in A['items']:
        p = {'id': it['id'], 'z': it['z'], 'links': it.get('links', []), 'r': it['r'], 'motion': 'fixed'}
        if it['kind'] == 'rod':
            p.update(kind='rod', p=it['p'], q=it['q'])
        elif it.get('block'):
            p.update(kind='block', c=it['c'], r_in=it.get('r_in'))
        elif it.get('teeth'):
            p.update(kind='gear', c=it['c'], teeth=it['teeth'], m=it['m'], mesh=it.get('mesh_kind', 'external'))
        elif it.get('wheel') == 'renvoi' and abs(it['r'] - 20.0) < 1e-9:
            p.update(kind='crown', c=it['c'])
        elif it.get('wheel') == 'renvoi' and abs(it['r'] - 5.6) < 1e-9:
            p.update(kind='bevel', c=it['c'])
        else:
            p.update(kind='arbor' if it['r'] <= 4.0 else 'misc', c=it['c'])
        out.append(p)
    return out


def run_arch():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    P.reset_cache()
    mats = P.materials()
    parts = arch_parts()
    index = {p['id']: p for p in parts}
    t = time.perf_counter()
    bad = []
    for p in parts:
        o = P.build_part(p, {}, mats, index)
        r = check_mesh(o.data)
        if not r['ok']:
            bad.append((p['id'], r))
    print('\narchitecture.json : %d pièces en %.2f s, %d maillages non conformes' % (
        len(parts), time.perf_counter() - t, len(bad)))
    print(P.stats_text())
    for b in bad[:10]:
        print('  NON CONFORME', b)
    return not bad


if __name__ == '__main__':
    t0 = time.perf_counter()
    res = unittest.main(argv=['test_parts'], exit=False, verbosity=2).result
    ok = res.wasSuccessful()
    if '--arch' in ARGS:
        ok = run_arch() and ok
    print('test_parts : %s en %.2f s' % ('OK' if ok else 'ÉCHEC', time.perf_counter() - t0))
    if not ok:
        raise SystemExit(1)
