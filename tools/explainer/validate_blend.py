"""Valide tools/explainer/engine.py contre la scène Blender (drivers réels de am.blend).

Lancer sur une COPIE de build/out/am.blend (le fichier n'est jamais enregistré) :
  cp build/out/am.blend /tmp/am_copy.blend
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup /tmp/am_copy.blend \
      --python-exit-code 1 -P tools/explainer/validate_blend.py

Pour chaque valeur de AM_Controller["crank"] (>= 20 valeurs, dont de grands |t|), on lit dans Blender :
  * la rotation locale de TOUS les Empties B_* (driver) ;
  * les rotations MONDE (matrix_world) des aiguilles et marqueurs utilisés par les lectures : aiguille de date (B_b),
    aiguille de la Lune, aiguille du Dragon, les 6 sphères planétaires (centre de leur boîte englobante), boule de
    phase (axe de l'hémisphère argenté), aiguilles arrière (Méton, Saros, Jeux, Callippe, Exeligmos) ;
  * la position monde des curseurs des spirales (rayon depuis le centre du cadran),
et on compare avec engine.Machine().state(t). Critère : erreur angulaire max < 1e-4 rad.
Les valeurs de manivelle sont exactement représentables en float32 : Blender lit la variable de driver en float32,
une manivelle non représentable (ex. 2026.61) est d'abord arrondie (écart ~ taux × ulp(c)) — mesuré à part.
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402

OUT = E.OUT_DIR / 'validate_blend.json'
CRANKS = [0.0, 1.0, 0.5, 4.0, 19.0, 0.0078125, 3.25, 7.1875, 12.34375, -7.3125, -18.03125, 55.5, 88.0625,
          99.875, -100.0, 250.25, -1234.5625, 2026.6875, -2204.3125, 3000.125, -4712.5, 9999.75]
NON_EXACT = [2026.6131, -2204.4, 26.613137]      # pour mesurer l'effet float32 de la variable de driver


def wrap(x):
    return (x + math.pi) % (2 * math.pi) - math.pi


def main():
    m = E.Machine()
    ctl = bpy.data.objects['AM_Controller']
    if ctl.animation_data:                     # l'action de démonstration (crank 0 -> 4) ne doit pas écraser nos valeurs
        ctl.animation_data.action = None
    vl = bpy.context.view_layer
    ob = bpy.data.objects
    markers = {'t_mercury': 'marker_mercury', 't_venus': 'marker_venus', 't_mars': 'marker_mars',
               't_jupiter': 'marker_jupiter', 't_saturn': 'marker_saturn', 't_trueSun': 'marker_trueSun'}
    lonkey = {'t_mercury': 'mercure', 't_venus': 'venus', 't_mars': 'mars', 't_jupiter': 'jupiter',
              't_saturn': 'saturne', 't_trueSun': 'soleil_vrai'}
    back = {'metonic': 'B_n', 'saros': 'B_g', 'olympiad': 'B_o', 'callippic': 'B_cal', 'exeligmos': 'B_i'}
    centres = {'metonic': m.S['axes_world_xy']['N'], 'saros': m.S['axes_world_xy']['G']}
    # centre local de la boîte englobante de chaque marqueur (constante)
    bbc = {k: sum((Vector(c) for c in ob[n].bound_box), Vector()) / 8 for k, n in markers.items()}
    worst = {}; per_t = []; missing = []

    def upd(cat, err, t):
        err = abs(float(err))
        if err > worst.get(cat, (0, None))[0]:
            worst[cat] = (err, t)

    def evaluate(c):
        ctl['crank'] = float(c); ctl.update_tag(); vl.update()
        dg = bpy.context.evaluated_depsgraph_get()
        return dg

    for c in CRANKS:
        c = float(np.float32(c))
        dg = evaluate(c)
        st = m.state(c); A = st['local']; L = st['lon']
        row = {'crank': c}
        # (a) rotation locale de chaque corps
        wb = 0.0
        for bid in m.bodies:
            if bid == 'frame':
                continue
            o = ob.get('B_' + bid)
            if o is None:
                missing.append(bid); continue
            oe = o.evaluated_get(dg)
            got = oe.rotation_euler[0] if bid in ('a', 'q') else oe.rotation_euler[2]
            e = wrap(got - float(A[bid])); wb = max(wb, abs(e)); upd('corps_rotation_locale', e, c)
        row['corps_max_rad'] = wb
        mw = lambda name: np.array(ob[name].evaluated_get(dg).matrix_world)
        # (b) aiguilles avant (axe local +x)
        for name, key in (('B_b', 'soleil_moyen'), ('B_moon', 'lune'), ('B_t_nodes', 'noeud_ascendant')):
            M = mw(name); lam = -math.atan2(M[1, 0], M[0, 0])
            upd('aiguilles_avant_monde', wrap(lam - float(L[key])), c)
        # marqueurs planétaires : centre monde de la boîte englobante -> longitude
        for body, name in markers.items():
            o = ob[name].evaluated_get(dg)
            p = o.matrix_world @ bbc[body]
            lam = -math.atan2(p.y, p.x)
            upd('marqueurs_planetes_monde', wrap(lam - float(L[lonkey[body]])), c)
        # boule de phase : axe de l'hémisphère argenté (−z local de B_q), exprimé dans le repère de la Lune
        Mq = mw('B_q'); Mm = mw('B_moon')
        a_world = -Mq[:3, 2] / np.linalg.norm(Mq[:3, 2])
        a_moon = Mm[:3, :3].T @ a_world
        q_got = math.atan2(a_moon[1], -a_moon[2])
        upd('boule_de_phase', wrap(q_got - float(A['q'])), c)
        k_vis = (1 + a_world[2]) / 2                       # fraction argentée vue de face (+z)
        upd('fraction_eclairee_visible', k_vis - (1 - math.cos(float(L['phase']))) / 2, c)
        # (c) aiguilles arrière (axe local +y) : psi = atan2(−x, y)
        for which, name in back.items():
            M = mw(name); psi = math.atan2(-M[0, 1], M[1, 1])
            upd('aiguilles_arriere_monde', wrap(psi - float(st['psi'][which])), c)
        # curseurs des spirales : rayon et direction
        for which, name in (('metonic', 'metonic_slider'), ('saros', 'saros_slider')):
            o = ob[name].evaluated_get(dg)
            p = np.array(o.matrix_world.translation)[:2] - np.array(centres[which])
            rho = float(np.hypot(*p)); psi = math.atan2(-p[0], p[1])
            upd('curseurs_direction', wrap(psi - float(st['psi'][which])), c)
            upd('curseurs_rayon_table_mm', rho - float(st['rho'][which]), c)
            upd('curseurs_rayon_formule_exacte_mm', rho - float(st['rho_exact'][which]), c)
        per_t.append(row)
    # effet float32 d'une manivelle non représentable
    f32 = []
    for c in NON_EXACT:
        dg = evaluate(c)
        e64 = max(abs(wrap(ob['B_' + b].evaluated_get(dg).rotation_euler[2] - float(m.local(c)[b])))
                  for b in ('moon', 'k', 'e_table', 'b', 't_nodes'))
        c32 = float(np.float32(c))
        e32 = max(abs(wrap(ob['B_' + b].evaluated_get(dg).rotation_euler[2] - float(m.local(c32)[b])))
                  for b in ('moon', 'k', 'e_table', 'b', 't_nodes'))
        f32.append({'crank': c, 'float32': c32, 'err_moteur_en_float64_rad': e64, 'err_moteur_en_float32_rad': e32})
    ang = [k for k in worst if not k.endswith('_mm') and k != 'fraction_eclairee_visible']
    max_ang = max(worst[k][0] for k in ang)
    ok = max_ang < 1e-4 and not missing and worst['curseurs_rayon_table_mm'][0] < 1e-3
    rep = {'blend': bpy.data.filepath, 'moteur': 'tools/explainer/engine.py', 'n_valeurs_manivelle': len(CRANKS),
           'manivelles': [float(np.float32(c)) for c in CRANKS],
           'erreurs_max': {k: {'max': v[0], 'a_la_manivelle': v[1]} for k, v in worst.items()},
           'erreur_angulaire_max_rad': max_ang, 'critere_rad': 1e-4, 'corps_absents': sorted(set(missing)),
           'effet_float32_manivelle_non_representable': f32, 'par_valeur': per_t, 'ok': ok}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    for k, v in worst.items():
        print('  %-36s max %.2e  (manivelle %s)' % (k, v[0], v[1]))
    for r in f32:
        print('  float32 manivelle %s -> %s : moteur(c) %.1e rad, moteur(float32(c)) %.1e rad' %
              (r['crank'], r['float32'], r['err_moteur_en_float64_rad'], r['err_moteur_en_float32_rad']))
    print('VALIDATE_BLEND %s : %d manivelles, erreur angulaire max %.2e rad (critère 1e-4) -> %s' %
          ('OK' if ok else 'FAIL', len(CRANKS), max_ang, OUT))
    if not ok:
        sys.exit(1)


main()
