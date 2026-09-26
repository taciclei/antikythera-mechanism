"""Applique le calage « ciel réel » du moteur à une COPIE de am.blend (pour filmer de vraies dates).

  cp build/out/am.blend /tmp/am_cale.blend
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup /tmp/am_cale.blend --python-exit-code 1 \
      -P tools/explainer/apply_calibration_blend.py -- --t-ref 26.0 --save /tmp/am_cale_2026.blend

Après patch, AM_Controller["crank"] = c' est une manivelle LOCALE : la machine montre le temps t = t_ref + c'
(t = (JD − 2451545.0)/365.2422 ; t_ref = 26.0 -> 2025-12-31). Garder |c'| petit (< ~10 ans) : Blender lit la
variable de driver en float32, une grande manivelle perd de la précision (voir validate_blend.json).

Ce que fait le script : ajoute à chaque driver linéaire la constante engine.blender_offsets() (décalage temporel exact
de TOUS les engrenages + phases de calage des sorties), décale les curseurs des spirales, puis vérifie la copie contre
engine.calibrate() à plusieurs manivelles. Limite visuelle : les phases de calage tournent quelques sorties (b, e_table,
k, nœuds, goupilles planétaires, aiguilles arrière) par rapport à leurs pignons voisins ; en très gros plan sur ces
engrenages les dents ne sont plus exactement en prise. Ne modifie JAMAIS build/out/am.blend.
"""
import argparse
import math
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402


def lin_str(rate):
    """Même texte que build/am/expr.py : lin() (pour retrouver le préfixe exact des expressions)."""
    n, d = abs(rate.numerator), rate.denominator
    if rate == 0:
        return '0.0'
    arg = 'c' if (n, d) == (1, 1) else ('c*%d' % n if d == 1 else ('c/%d' % d if n == 1 else 'c*%d/%d' % (n, d)))
    return ('-2*pi*fmod(%s,1)' if rate > 0 else '2*pi*fmod(%s,1)') % arg


def plus(x):
    return ('+' + repr(float(x))) if x >= 0 else ('-' + repr(float(-x)))


def driver(obj, path):
    ad = obj.animation_data
    for fc in (ad.drivers if ad else []):
        if fc.data_path == path:
            return fc
    raise KeyError('%s.%s' % (obj.name, path))


def set_expr(fc, new):
    if len(new) > 255:
        raise ValueError('expression trop longue (%d) : %s' % (len(new), new))
    fc.driver.expression = new
    if fc.driver.expression != new:
        raise ValueError('expression tronquée : %s' % new)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--t-ref', type=float, default=26.0)
    ap.add_argument('--epoch-jd', type=float, default=E.JD_J2000, help='époque du calage (défaut J2000.0)')
    ap.add_argument('--save', help='chemin de sortie (.blend) ; jamais build/out/am.blend')
    a = ap.parse_args(argv)
    src = Path(bpy.data.filepath).resolve()
    if src == (E.ROOT / 'build' / 'out' / 'am.blend').resolve():
        sys.exit('refus : ouvrir une COPIE de am.blend, pas l\'original')
    if a.save and Path(a.save).resolve() == (E.ROOT / 'build' / 'out' / 'am.blend').resolve():
        sys.exit('refus : ne jamais écraser build/out/am.blend')
    m = E.calibrate(a.epoch_jd)
    off = E.blender_offsets(m, a.t_ref)
    ob = bpy.data.objects
    lin_b = lin_str(m.rel['b'])
    changed = []
    for bid, body in m.bodies.items():
        o = ob.get('B_' + bid)
        if o is None or bid in ('frame', 'moon') or bid in m.pin_slots:
            continue
        idx = 0 if bid in ('a', 'q') else 2
        fc = next(f for f in o.animation_data.drivers if f.data_path == 'rotation_euler' and f.array_index == idx)
        ex = fc.driver.expression
        if bid in off['corps']:                                  # corps linéaires (dont a) : expr == lin
            pre = lin_str(m.crank_rate) if bid == 'a' else lin_str(m.rel[bid])
            add = off['corps'][bid]
        elif bid == 'e_inner':
            pre, add = lin_str(m.rel['e_table']), off['corps']['e_table']
        else:                                                    # t_X, suiveurs, q : commencent par lin(b)
            pre, add = lin_b, off['corps']['b']
        if not ex.startswith(pre):
            raise ValueError('driver inattendu sur %s : %s' % (o.name, ex))
        set_expr(fc, pre + plus(add) + ex[len(pre):]); changed.append(o.name)
    for which, names in (('metonic', ('metonic_slider', 'metonic_slider_pin')), ('saros', ('saros_slider', 'saros_slider_pin'))):
        for name in names:
            fc = driver(ob[name], 'location')
            ex = fc.driver.expression
            if not ex.endswith('+1,1)'):
                raise ValueError('curseur inattendu : %s' % ex)
            set_expr(fc, ex[:-len('+1,1)')] + '+1+%r,1)' % off['curseurs'][which]); changed.append(name)
    ctl = ob['AM_Controller']
    if ctl.animation_data:
        ctl.animation_data.action = None
    ctl['calage'] = 'crank = t - %.6f ; t = (JD - 2451545.0)/365.2422 ; epoque %s' % (a.t_ref, m.calibration['epoch'])
    # vérification
    vl = bpy.context.view_layer
    worst = 0.0; worst_rho = 0.0
    centres = {'metonic': m.S['axes_world_xy']['N'], 'saros': m.S['axes_world_xy']['G']}
    for c in (0.0, 0.5, 1.25, -2.75, 3.0625, 7.9375, -9.5, 0.6131591796875):
        c = float(np.float32(c)); ctl['crank'] = c; ctl.update_tag(); vl.update()
        dg = bpy.context.evaluated_depsgraph_get()
        t = a.t_ref + c
        A = m.local(t); st = m.state(t)
        for bid in m.bodies:
            o = ob.get('B_' + bid)
            if o is None or bid == 'frame':
                continue
            oe = o.evaluated_get(dg)
            got = oe.rotation_euler[0] if bid in ('a', 'q') else oe.rotation_euler[2]
            worst = max(worst, abs((got - float(A[bid]) + math.pi) % (2 * math.pi) - math.pi))
        for which, name in (('metonic', 'metonic_slider'), ('saros', 'saros_slider')):
            p = np.array(ob[name].evaluated_get(dg).matrix_world.translation)[:2] - np.array(centres[which])
            worst_rho = max(worst_rho, abs(float(np.hypot(*p)) - float(st['rho'][which])))
    ctl['crank'] = 0.0
    ok = worst < 1e-4 and worst_rho < 1e-3
    print('APPLY_CALIBRATION %s : %d drivers modifiés, t_ref %.4f (%s), écart max %.2e rad, curseurs %.2e mm'
          % ('OK' if ok else 'FAIL', len(changed), a.t_ref, off['date_ref'], worst, worst_rho))
    if not ok:
        sys.exit(1)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.save).resolve()), copy=True, compress=True)
        print('enregistré :', a.save)


main()
