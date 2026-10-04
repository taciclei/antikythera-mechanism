"""Anticythère 2.0 — contrôles 3D d'une scène construite (voir CONTRACT.md, § 4).

Lancer :
  BL -b v2/out/v2.blend --python-exit-code 1 -P v2/blender/check.py -- --samples 24 [--quick]
  BL -b --factory-startup --python-exit-code 1 -P v2/blender/check.py -- --selftest [--quick]
Contrôles (rapport JSON dans v2/out/check.json, code de sortie 1 en cas d'échec) :
  (1) maillages : chaque roue/couronne/conique/arbre/platine est une variété fermée, cohérente, sans face dégénérée
      (aire nulle, ou épaisseur sous quelques ulp float32 des coordonnées : sommets alignés), de volume positif
      (tubes, tringles, axes et autres pièces : signalés seulement) ;
  (2) couples engrenés : pour chaque objet portant `meshes_with`, N instants répartis sur un tour de la roue la plus
      rapide du couple (au plus la durée de l'animation si une pièce est `ephem:`), arrondis au float32 comme les
      lit un pilote ; arbres BVH en repère monde des maillages évalués ; aucun couple de triangles sécants permis ;
      relecture des rotations `linear` (angle mesuré contre −2π·phys·|rate|·Δjours ; une pièce tournée par son
      pivot « V2_Pivot_<nom> » d'animate.py est relue aussi) ;
  (3) recouvrements statiques à la première image : couples dont les boîtes englobantes se coupent, ni déclarés
      (`links`, `meshes_with`, dans un sens ou dans l'autre) ni parents l'un de l'autre ; recouvrement BVH vide exigé,
      ainsi qu'aucune pièce entièrement noyée dans un solide fermé ; les couples avec un `block` sont signalés
      seulement ;
  (4) rapport : comptes, pires cas, durées. Une scène sans aucune pièce à contrôler (fichier .blend non chargé) ou
      sans contrôleur alors que des pièces bougent est un échec.
Les noms de `links`/`meshes_with` sont cherchés par nom d'objet, par ce nom avec « # » → « . » (parts.obj_name),
par `part_id`/`id`, puis par `source` unique ; un nom introuvable est un échec.
(5) tours de Kepler (kepler_check.py, CONTRACT.md § 8) : seulement si la scène contient des pièces Kepler
  (`kepler` = 1) ; maillages, relecture des images clés contre motion_api, recouvrements BVH sur une grille de
  l'espace d'état (L, LT) ; section « kepler » du rapport et verdict global. Sans pièce Kepler : rien de plus.
L'option --quick réduit le nombre d'instants et ne teste qu'un sous-ensemble aléatoire (graine fixe) des couples
statiques. L'option --selftest construit une petite scène synthétique (lib/check_selftest.py) et vérifie que les
contrôles attrapent les défauts volontaires et acceptent la scène corrigée. Le fichier .blend n'est jamais enregistré.
"""
import argparse
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
if os.path.join(HERE, 'lib') not in sys.path:
    sys.path.insert(0, os.path.join(HERE, 'lib'))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import check_lib as CL  # noqa: E402

CONTROLLER = 'V2_Controleur'
STRICT_KINDS = ('gear', 'crown', 'bevel', 'arbor', 'plate')     # maillage invalide = échec
GOLD = (math.sqrt(5.0) - 1.0) / 2.0


def log(*a):
    print('[v2-check]', *a, flush=True)


def parse_args(argv):
    argv = argv[argv.index('--') + 1:] if '--' in argv else []
    p = argparse.ArgumentParser(prog='check.py')
    p.add_argument('--samples', type=int, default=24, help='instants par couple engrené')
    p.add_argument('--quick', action='store_true', help='moins d\'instants, sous-ensemble des couples statiques')
    p.add_argument('--quick-pairs', type=int, default=200, help='couples statiques testés en mode --quick')
    p.add_argument('--readback-tol', type=float, default=0.05, help='écart toléré sur la relecture (rad)')
    p.add_argument('--all-meshes', action='store_true', help='inclure les maillages sans propriété kind')
    p.add_argument('--seed', type=int, default=20261004)
    p.add_argument('--selftest', action='store_true', help='scène synthétique et vérification des détections')
    p.add_argument('--out', default=None, help='chemin du rapport JSON')
    p.add_argument('--kepler-spec', default=None, help='spec Kepler (sinon V2_KEPLER_SPEC, la scène, le défaut)')
    p.add_argument('--kepler-tools', default=None, help='dossier de motion.py et frame.py')
    p.add_argument('--kepler-states', type=int, default=48, help='états (L, LT) de la grille, au moins')
    p.add_argument('--kepler-traj', type=int, default=12, help='instants de la trajectoire 2026 en plus')
    p.add_argument('--kepler-tol-mm', type=float, default=1e-4, help='relecture des positions Kepler (mm)')
    p.add_argument('--kepler-tol-rad', type=float, default=1e-5, help='relecture des angles Kepler (rad)')
    return p.parse_args(argv)


# ---------------------------------------------------------------- temps
class Clock:
    """Fixe l'instant `jours` (depuis J2000.0). L'image courante (avec sous-image) suit `jours` pour les clés des
    sorties `ephem:` ; la propriété `jours` du contrôleur, dont l'animation est détachée (jamais enregistrée), est
    posée exactement pour les pilotes `linear`. La correspondance image ↔ jours est mesurée sur la scène.
    Les variables de pilote sont lues en float32 : chaque instant est arrondi au float32 le plus proche avant d'être
    posé (`now` = instant effectif), sinon la relecture verrait un écart de 2π·taux·ulp/2 (≈ 0,01 rad à 4 tours/j)."""

    def __init__(self, scene):
        self.sc = scene
        self.ctl = scene.objects.get(CONTROLLER) or next((o for o in scene.objects if 'jours' in o.keys()), None)
        self.f0 = scene.frame_start
        self.saved = None
        self.now = None
        f1 = scene.frame_end if scene.frame_end > self.f0 else self.f0 + 1
        if self.ctl is None:                    # pas de contrôleur : jours = images depuis la première
            self.fs, self.js = np.array([self.f0, self.f0 + 1.0]), np.array([0.0, 1.0])
        else:
            self.jours_orig = self.ctl.get('jours', 0.0)
            fc = self._jours_fcurve()
            if fc is not None:                  # table image → jours lue sur la courbe (toute interpolation)
                self.fs = np.arange(self.f0, f1 + 1, dtype=float)
                self.js = np.array([fc.evaluate(f) for f in self.fs])
            else:                               # pilote ou valeur fixe : mesure aux deux bouts
                self.fs = np.array([self.f0, f1], float)
                self.js = np.array([self._jours_at(self.f0), self._jours_at(f1)])
            if not np.all(np.diff(self.js) > 0):    # jours non animé : 1 image par jour (contrat)
                j = float(self.js[0])
                self.fs, self.js = np.array([self.f0, self.f0 + 1.0]), np.array([j, j + 1.0])
        self.j0 = float(self.js[0])
        self.slope = float((self.js[-1] - self.js[0]) / (self.fs[-1] - self.fs[0]))     # jours par image
        self.span = float(max(f1 - self.f0, 1) * self.slope)    # durée de l'animation (jours)
        if self.ctl is not None:
            ad = self.ctl.animation_data
            if ad is not None:
                muted = [fc for fc in ad.drivers if fc.data_path == '["jours"]' and not fc.mute]
                self.saved = (ad.action, getattr(ad, 'action_slot', None), muted, ad.use_nla)
                ad.action = None
                ad.use_nla = False                  # pistes NLA éventuelles : elles réécriraient `jours`
                for fc in muted:
                    fc.mute = True
        self.set(self.j0)

    def restore(self):
        """Rattache l'animation du contrôleur et revient à la première image."""
        if self.saved is not None:
            ad = self.ctl.animation_data
            action, slot, muted, use_nla = self.saved
            ad.action = action
            ad.use_nla = use_nla
            if slot is not None and getattr(ad, 'action_slot', None) != slot:
                try:
                    ad.action_slot = slot
                except (AttributeError, TypeError, RuntimeError):
                    pass
            for fc in muted:
                fc.mute = False
            self.saved = None
        if self.ctl is not None:
            self.ctl['jours'] = self.jours_orig      # valeur d'origine (l'animation rattachée la recalcule)
        self.sc.frame_set(self.f0)

    def _jours_at(self, f):
        self.sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        return float(self.ctl.evaluated_get(dg).get('jours', self.ctl.get('jours', 0.0)))

    def _jours_fcurve(self):
        ad = self.ctl.animation_data
        if ad is None or ad.action is None:
            return None
        try:
            from bpy_extras import anim_utils
            cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
            fcs = list(cb.fcurves) if cb is not None else []
        except (ImportError, AttributeError):
            fcs = list(getattr(ad.action, 'fcurves', []))
        return next((fc for fc in fcs if fc.data_path == '["jours"]'), None)

    def frame_of(self, jours):
        """Image (fractionnaire) où le contrôleur vaut `jours` ; extrapolation linéaire hors de l'animation."""
        if self.js[0] <= jours <= self.js[-1]:
            return float(np.interp(jours, self.js, self.fs))
        k = 0 if jours < self.js[0] else -1
        return float(self.fs[k] + (jours - self.js[k]) / self.slope)

    def set(self, jours):
        """Place la scène à `jours` arrondi au float32 (voir la classe) ; renvoie le graphe évalué."""
        jours = float(np.float32(jours))
        self.now = jours
        f = self.frame_of(jours)
        fi = math.floor(f)
        self.sc.frame_set(int(fi), subframe=float(f - fi))
        if self.ctl is not None:
            self.ctl['jours'] = float(jours)
            self.ctl.update_tag()
            bpy.context.view_layer.update()
        return bpy.context.evaluated_depsgraph_get()


def reveal():
    """Rend évaluables les objets masqués (objets ou collections `hide_viewport`, collections exclues de la couche
    de vue) : sinon le graphe de dépendances ne les évalue pas. Renvoie la liste d'annulation."""
    undo = []

    def walk(lc):
        if lc.exclude:
            undo.append((lc, 'exclude', True))
            lc.exclude = False
        for c in lc.children:
            walk(c)
    walk(bpy.context.view_layer.layer_collection)
    for item in list(bpy.data.collections) + list(bpy.context.scene.objects):
        if item.hide_viewport:
            undo.append((item, 'hide_viewport', True))
            item.hide_viewport = False
    bpy.context.view_layer.update()
    return undo


def unreveal(undo):
    for item, attr, value in reversed(undo):
        setattr(item, attr, value)


# ---------------------------------------------------------------- pièces
class Parts:
    """Objets maillés contrôlés, maillages évalués (repère local, mis en cache) et relations déclarées."""

    def __init__(self, all_meshes=False):
        obs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and (all_meshes or 'kind' in o.keys())]
        self.obs = sorted(obs, key=lambda o: o.name)
        self.by_name = {o.name: o for o in self.obs}
        self.non_mesh = sorted(o.name for o in bpy.context.scene.objects
                               if o.type != 'MESH' and str(o.get('kind', '')) in STRICT_KINDS)
        self.res = CL.Resolver(list(bpy.data.objects))
        self.load_seconds = 0.0
        self.local = {}
        self.tlist = {}
        self.mesh_rep = {}
        self.unresolved = []
        self.declared = {}
        for o in self.obs:
            s = set()
            for key in ('links', 'meshes_with'):
                for n in CL.as_list(o.get(key)):
                    t = self.res.get(n)
                    if t is None:
                        self.unresolved.append({'object': o.name, 'property': key, 'name': n})
                    else:
                        s.add(t.name)
            self.declared[o.name] = s

    @staticmethod
    def kind(o):
        return str(o.get('kind', 'misc'))

    def load(self, dg):
        """Maillages évalués de toutes les pièces, avec le rapport de validité."""
        t0 = time.time()
        for o in self.obs:
            V, T, rep = CL.evaluated_mesh_data(o, dg, with_check=True)
            self.local[o.name] = (V, T)
            self.tlist[o.name] = T.tolist()
            self.mesh_rep[o.name] = rep
        self.load_seconds = time.time() - t0

    def world(self, name, dg):
        V, T = self.local[name]
        return CL.to_world(V, CL.world_matrix(self.by_name[name], dg)), T

    def ancestors(self, o):
        s, p = set(), o.parent
        while p is not None:
            s.add(p.name)
            p = p.parent
        return s

    def moving_ancestor(self, o):
        """Vrai si un ancêtre bouge. Le pivot propre de l'objet (Empty « V2_Pivot_<nom> » d'animate.py, qui porte
        `v2_pivot_of` = nom) n'en est pas un : il tourne autour de l'axe de l'objet, la relecture reste valable."""
        p = o.parent
        if p is not None and str(p.get('v2_pivot_of', '')) == o.name:
            p = p.parent
        while p is not None:
            if str(p.get('motion', 'fixed')) != 'fixed' or (p.animation_data is not None):
                return True
            p = p.parent
        return False


# ---------------------------------------------------------------- (1) maillages
def check_meshes(parts):
    t0 = time.time()
    failed, reported, rows = [], [], []
    for o in parts.obs:
        r = parts.mesh_rep[o.name]
        k = parts.kind(o)
        rows.append((o.name, k, r))
        if not r['ok']:
            item = dict(r, name=o.name, kind=k)
            (failed if k in STRICT_KINDS else reported).append(item)
    strict = [x for x in rows if x[1] in STRICT_KINDS]
    sec = {'checked': len(rows), 'strict_checked': len(strict),
           'by_kind': {k: sum(1 for x in rows if x[1] == k) for k in sorted({x[1] for x in rows})},
           'failed': failed, 'reported_only': reported,
           'smallest_face_area': sorted(({'name': n, 'min_face_area': r['min_face_area']} for n, _k, r in strict),
                                        key=lambda d: d['min_face_area'])[:5],
           'thinnest_face': sorted(({'name': n, 'min_face_thickness': r['min_face_thickness'],
                                     'thin_tol_mm': r['thin_tol_mm']} for n, _k, r in strict),
                                   key=lambda d: d['min_face_thickness'] / max(d['thin_tol_mm'], 1e-30))[:5],
           'total_triangles': int(sum(len(parts.local[n][1]) for n, _k, _r in rows)),
           'non_mesh_with_kind': parts.non_mesh[:50],
           'seconds': round(time.time() - t0 + parts.load_seconds, 3)}
    sec['ok'] = not failed
    return sec


def mesh_faults(r):
    """Résumé des défauts d'un rapport check_mesh, pour les lignes d'échec."""
    names = (('non_manifold', 'arêtes non variétés'), ('non_contiguous', 'normales incohérentes'),
             ('boundary', 'arêtes de bord'), ('wire', 'arêtes isolées'), ('zero_area_faces', 'faces d\'aire nulle'),
             ('thin_faces', 'faces dégénérées'))
    out = ['%d %s' % (r[k], lab) for k, lab in names if r.get(k)]
    if r.get('volume', 0.0) <= 0:
        out.append('volume %.4g' % r.get('volume', 0.0))
    if not r.get('faces'):
        out.append('aucune face')
    return ', '.join(out)


# ---------------------------------------------------------------- (2) couples engrenés
def rate_of(o):
    """Taux absolu (tours/jour) d'une pièce `linear`, None pour les autres mouvements."""
    if str(o.get('motion', '')) != 'linear' or 'rate' not in o.keys():
        return None
    return abs(float(o['rate']))


def pair_period(oa, ob, span):
    """Durée échantillonnée d'un couple : un tour de la roue la plus rapide. Une pièce `ephem:` (images clés cuites
    sur l'animation seulement, figées au-delà) limite la durée à l'animation (`span` jours) ; elle donne son taux
    moyen `rate` s'il est connu. Sans aucun taux : `span`."""
    rates, ephem = [], False
    for o in (oa, ob):
        motion = str(o.get('motion', 'fixed'))
        ephem |= motion.startswith('ephem:') or motion == 'kepler'     # clés cuites sur l'animation seulement
        r = abs(float(o.get('rate', 0.0) or 0.0)) if motion != 'fixed' else 0.0
        if r > 0:
            rates.append(r)
    period = 1.0 / max(rates) if rates else span
    return min(period, span) if ephem else period


def mesh_pairs(parts):
    """Couples non ordonnés (a, b) déclarés par `meshes_with` ou `engages`, et partenaires ignorés (non maillés)."""
    pairs, seen, skipped = [], set(), []
    for o in parts.obs:
        # couples droits (`meshes_with`) et contacts de couronne et de coniques (`engages`, posé par parts.py)
        for n in CL.as_list(o.get('meshes_with')) + CL.as_list(o.get('engages')):
            t = parts.res.get(n)
            if t is None:
                continue                      # déjà compté dans parts.unresolved
            if t.name not in parts.by_name or t.name == o.name:
                skipped.append({'object': o.name, 'partner': t.name})
                continue
            key = tuple(sorted((o.name, t.name)))
            if key not in seen:
                seen.add(key)
                pairs.append(key)
    return pairs, skipped


def instants(j0, period, n):
    """n instants sur un tour : pas régulier plus un décalage au nombre d'or (évite de retomber toujours sur la même
    phase de dent quand le nombre de dents est multiple de n)."""
    return [j0 + period * (k + (k * GOLD) % 1.0) / n for k in range(n)]


def radial_filter_gap(Wa, Wb, tb, center_b, axis_b, reach=2.0):
    """Jeu approché entre A et B : sommets de A à moins de (rayon de B + reach) de l'axe de B, puis BVH de B."""
    def radial(W):
        d = W - center_b
        return np.linalg.norm(d - np.outer(d @ axis_b, axis_b), axis=1)
    rmax = float(radial(Wb).max()) if len(Wb) else 0.0
    lo_b, hi_b = CL.aabb(Wb)
    sel = radial(Wa) <= rmax + reach
    return CL.min_gap(Wa[sel], tb, lo_b, hi_b, reach=reach)


def check_pairs(parts, clock, n, tol):
    t0 = time.time()
    pairs, skipped = mesh_pairs(parts)
    rows, frozen = [], []
    rb = {'err_rad': 0.0, 'objects': 0}
    rb_objs = set()
    for a, b in pairs:
        oa, ob = parts.by_name[a], parts.by_name[b]
        period = pair_period(oa, ob, clock.span)
        js = instants(clock.j0, period, n)
        hits, gap, ref = [], math.inf, {}
        moved, expect = {a: 0.0, b: 0.0}, {a: 0.0, b: 0.0}
        for j in js:
            dg = clock.set(j)
            j = clock.now                     # instant effectif (float32), celui que lisent les pilotes
            geo = {}
            for name in (a, b):
                o = parts.by_name[name]
                M = CL.world_matrix(o, dg)
                V, T = parts.local[name]
                W = CL.to_world(V, M)
                geo[name] = (W, T, CL.bvh(W, parts.tlist[name]), M)
                if rate_of(o) is None or parts.moving_ancestor(o):
                    continue
                rb_objs.add(name)
                R = CL.rot3(M)
                R0, jr = ref.setdefault(name, (R, j))
                meas = CL.signed_rotation(R0, R, CL.as_vec(o.get('axis')))
                exp = CL.wrap(-2.0 * math.pi * float(o.get('phys', 1)) * rate_of(o) * (j - jr))
                err = abs(CL.wrap(meas - exp))
                moved[name] = max(moved[name], abs(meas))
                expect[name] = max(expect[name], abs(exp))
                if err > rb['err_rad']:
                    rb.update(err_rad=err, object=name, jours=j, measured=meas, expected=exp)
            Wa, Ta, ta, Ma = geo[a]
            Wb, Tb, tb, Mb = geo[b]
            cnt, pt = CL.overlap_info(ta, tb, Wa, Ta)
            if cnt:
                hits.append({'jours': round(j, 6), 'tri_pairs': cnt, 'point': pt})
            else:
                ax_a, ax_b = CL.as_vec(oa.get('axis')), CL.as_vec(ob.get('axis'))
                gap = min(gap, radial_filter_gap(Wa, Wb, tb, Mb[:3, 3], ax_b),
                          radial_filter_gap(Wb, Wa, ta, Ma[:3, 3], ax_a))
        for name in (a, b):
            if expect[name] > 1e-3 and moved[name] < 1e-7:
                frozen.append(name)
        rows.append({'a': a, 'b': b, 'kinds': [parts.kind(oa), parts.kind(ob)], 'period_days': period,
                     'samples': len(js), 'overlapping_samples': len(hits),
                     'tri_pairs_max': max((h['tri_pairs'] for h in hits), default=0),
                     'hits': hits[:5], 'min_gap_mm': None if math.isinf(gap) else round(gap, 5)})
    bad = [r for r in rows if r['overlapping_samples']]
    rb['objects'] = len(rb_objs)
    rb['ok'] = rb['err_rad'] <= tol
    rb['tol_rad'] = tol
    clean = [r for r in rows if not r['overlapping_samples'] and r['min_gap_mm'] is not None]
    sec = {'pairs': len(rows), 'samples_per_pair': n, 'overlapping_pairs': len(bad),
           'worst': sorted(bad, key=lambda r: -r['tri_pairs_max'])[:10],
           'tightest_clean': [{'a': r['a'], 'b': r['b'], 'min_gap_mm': r['min_gap_mm']}
                              for r in sorted(clean, key=lambda r: r['min_gap_mm'])[:10]],
           'unresolved_names': parts.unresolved, 'skipped_partners': skipped,
           'frozen': sorted(set(frozen)), 'readback': rb, 'rows': rows,
           'seconds': round(time.time() - t0, 3)}
    sec['ok'] = not bad and not parts.unresolved and not frozen and rb['ok']
    return sec


# ---------------------------------------------------------------- (3) recouvrements statiques
def closed_solid(rep):
    return rep['non_manifold'] == 0 and rep['boundary'] == 0 and rep['wire'] == 0 and rep['volume'] > 0


def check_static(parts, clock, quick, quick_pairs, seed):
    t0 = time.time()
    dg = clock.set(clock.j0)
    names = [o.name for o in parts.obs if len(parts.local[o.name][1])]
    W, T, lo, hi = {}, {}, [], []
    for nm in names:
        W[nm], T[nm] = parts.world(nm, dg)
        a, b = CL.aabb(W[nm])
        lo.append(a)
        hi.append(b)
    cand = CL.aabb_pairs(np.array(lo), np.array(hi)) if names else []
    excluded = {'declared': 0, 'parent': 0}
    anc = {nm: parts.ancestors(parts.by_name[nm]) for nm in names}
    todo = []
    for i, j in cand:
        a, b = names[i], names[j]
        if b in parts.declared[a] or a in parts.declared[b]:
            excluded['declared'] += 1
        elif a in anc[b] or b in anc[a]:
            excluded['parent'] += 1
        else:
            todo.append((i, j))
    eligible = len(todo)
    if quick and len(todo) > quick_pairs:
        todo = sorted(random.Random(seed).sample(todo, quick_pairs))
    trees = {}

    def tree(nm):
        if nm not in trees:
            trees[nm] = CL.bvh(W[nm], parts.tlist[nm])
        return trees[nm]

    collisions, blocks = [], []
    contained_tests = 0
    for i, j in todo:
        a, b = names[i], names[j]
        cnt, pt = CL.overlap_info(tree(a), tree(b), W[a], T[a])
        typ, inner = ('surface', None) if cnt else (None, None)
        if not cnt:          # pièce entièrement noyée dans un solide fermé ?
            for x, y, ix, iy in ((a, b, i, j), (b, a, j, i)):
                if CL.aabb_inside(lo[ix], hi[ix], lo[iy], hi[iy]) and closed_solid(parts.mesh_rep[y]):
                    contained_tests += 1
                    if CL.point_inside(tree(y), W[x][0]):
                        typ, inner, pt = 'contained', x, [round(float(v), 4) for v in W[x][0]]
                        break
        if typ is None:
            continue
        ka, kb = parts.kind(parts.by_name[a]), parts.kind(parts.by_name[b])
        item = {'a': a, 'b': b, 'kinds': [ka, kb], 'type': typ, 'tri_pairs': cnt, 'point': pt}
        if inner:
            item['inside'] = inner
        (blocks if 'block' in (ka, kb) else collisions).append(item)
    collisions.sort(key=lambda d: -d['tri_pairs'])
    sec = {'objects': len(names), 'bbox_pairs': len(cand), 'excluded': excluded, 'eligible_pairs': eligible,
           'tested_pairs': len(todo), 'sampled': bool(quick and eligible > len(todo)),
           'containment_tests': contained_tests, 'bvh_built': len(trees),
           'collisions_count': len(collisions), 'collisions': collisions[:200],
           'block_contacts_count': len(blocks), 'block_contacts': blocks[:200],
           'worst': collisions[:10], 'jours': clock.j0, 'seconds': round(time.time() - t0, 3)}
    sec['ok'] = not collisions
    return sec


# ---------------------------------------------------------------- (4) rapport
def run_checks(opts):
    """Lance les trois contrôles sur la scène courante et renvoie le rapport (dict)."""
    t0 = time.time()
    n = max(2, min(opts.samples, 6)) if opts.quick else max(1, opts.samples)
    hidden = reveal()
    clock = Clock(bpy.context.scene)
    try:
        parts = Parts(opts.all_meshes)
        parts.load(clock.set(clock.j0))
        rep = {'meta': {'blend': bpy.data.filepath or '(non enregistré)', 'blender': bpy.app.version_string,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'), 'quick': bool(opts.quick), 'samples': n,
                        'controller': clock.ctl.name if clock.ctl else None, 'frame_start': clock.f0,
                        'jours_start': clock.j0, 'days_per_frame': clock.slope, 'objects': len(parts.obs)}}
        rep['meshes'] = check_meshes(parts)
        rep['pairs'] = check_pairs(parts, clock, n, opts.readback_tol)
        rep['static'] = check_static(parts, clock, opts.quick, opts.quick_pairs, opts.seed)
        if any(int(o.get('kepler', 0) or 0) for o in parts.obs):      # tours de Kepler : section (5)
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import kepler_check
            rep['kepler'] = kepler_check.check_kepler(parts, clock, opts)
        rep['meta']['revealed'] = len(hidden)
    finally:
        clock.restore()
        unreveal(hidden)
    m, p, s = rep['meshes'], rep['pairs'], rep['static']
    fails = []
    if not m['checked']:
        fails.append('aucune pièce à contrôler (aucun objet maillé portant « kind ») : '
                     'le fichier .blend est-il chargé ?')
    animated = sum(1 for o in bpy.context.scene.objects if str(o.get('motion', 'fixed')) != 'fixed')
    if rep['meta']['controller'] is None and animated:
        fails.append('contrôleur %s absent alors que %d objets sont mobiles' % (CONTROLLER, animated))
    if m['failed']:
        fails.append('maillages invalides : %d (%s)' % (
            len(m['failed']), ', '.join('%s [%s]' % (x['name'], mesh_faults(x)) for x in m['failed'][:5])))
    if p['overlapping_pairs']:
        fails.append('couples engrenés en recouvrement : %d (%s)' % (
            p['overlapping_pairs'], ', '.join('%s~%s' % (r['a'], r['b']) for r in p['worst'][:5])))
    if p['unresolved_names']:
        fails.append('noms non résolus dans links/meshes_with : %d' % len(p['unresolved_names']))
    if p['frozen']:
        fails.append('pièces figées (pilotes non évalués ?) : %s' % ', '.join(p['frozen'][:5]))
    if not p['readback']['ok']:
        fails.append('relecture des rotations : écart %.4g rad > %.4g' % (p['readback']['err_rad'], opts.readback_tol))
    if s['collisions_count']:
        fails.append('recouvrements statiques : %d (%s)' % (
            s['collisions_count'], ', '.join('%s/%s' % (c['a'], c['b']) for c in s['worst'][:5])))
    if 'kepler' in rep:
        fails += rep['kepler']['failures']
    rep['summary'] = {'ok': not fails, 'failures': fails,
                      'counts': {'meshes_checked': m['checked'], 'meshes_failed': len(m['failed']),
                                 'mesh_pairs': p['pairs'], 'pair_samples': p['pairs'] * n,
                                 'overlapping_pairs': p['overlapping_pairs'], 'static_tested': s['tested_pairs'],
                                 'static_collisions': s['collisions_count'],
                                 'block_contacts': s['block_contacts_count']},
                      'seconds': {'meshes': m['seconds'], 'pairs': p['seconds'], 'static': s['seconds'],
                                  'total': round(time.time() - t0, 3)}}
    if 'kepler' in rep:
        k = rep['kepler']
        rep['summary']['counts'].update(kepler_parts=k['parts'], kepler_states=k['states']['total'],
                                        kepler_pairs=k['pairs']['kepler_kepler'] + k['pairs']['kepler_scene'],
                                        kepler_bvh_tests=k['bvh_tests'], kepler_collisions=k['collisions_count'])
        rep['summary']['seconds']['kepler'] = k['seconds']
    return rep


def sanitize(x):
    """Rapport JSON strict : flottants non finis → None, types numpy → types Python."""
    if isinstance(x, dict):
        return {str(k): sanitize(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [sanitize(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(x) else None
    return x


def main():
    opts = parse_args(sys.argv)
    if opts.selftest:
        import check_selftest as ST
        report = ST.run(opts, run_checks)
        ok = report['ok']
        out = opts.out or os.path.join(V2, 'out', 'check_selftest.json')
    else:
        report = run_checks(opts)
        ok = report['summary']['ok']
        out = opts.out or os.path.join(V2, 'out', 'check.json')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w') as f:
        json.dump(sanitize(report), f, indent=1, default=str, allow_nan=False)
    summ = report.get('summary', {})
    log('rapport :', out)
    for line in summ.get('failures', report.get('failures', [])):
        log('  échec :', line)
    log('résultat :', 'OK' if ok else 'ÉCHEC')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
