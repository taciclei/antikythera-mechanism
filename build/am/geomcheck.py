"""Stage 'geometry': centre distances, modules, face overlaps, contact ratios, tip lands,
2D interference, collision pre-filter, a1 keep-out, follower sectors, cosmos checks."""
import json
import math
import os

import numpy as np

from . import OUT
from . import interference2d as X2
from . import involute as INV
from . import kinematics as K
from . import layout as LAY
from . import regions as REG

DEG = math.pi / 180.0


def mesh_checks(spec):
    rows, ok = [], True
    for m in spec.external_meshes:
        g1, g2 = spec.gears[m['driver']], spec.gears[m['driven']]
        a = math.dist(spec.axis_world(g1['body']), spec.axis_world(g2['body']))
        a_th = m['module'] * (g1['teeth'] + g2['teeth']) / 2
        zo = min(g1['z'][1], g2['z'][1]) - max(g1['z'][0], g2['z'][0])
        eps = INV.contact_ratio(g1['teeth'], g2['teeth'], m['module'])
        r = {'mesh': '%s~%s' % (m['driver'], m['driven']), 'carrier': m['carrier'],
             'module': m['module'], 'centre_distance': a, 'centre_theory': a_th,
             'cd_error': abs(a - a_th), 'cd_spec_error': abs(a - m['centre_distance']),
             'modules_equal': g1['module'] == g2['module'] == m['module'],
             'face_overlap': zo, 'face_overlap_spec': m['face_overlap'],
             'contact_ratio': eps, 'contact_ratio_spec': m['contact_ratio'],
             'min_teeth': min(g1['teeth'], g2['teeth'])}
        r['ok'] = (r['cd_error'] <= 1e-6 and r['cd_spec_error'] <= 1e-6 and r['modules_equal']
                   and zo >= 0.5 and abs(zo - m['face_overlap']) < 1e-9 and eps >= 1.2
                   and abs(eps - m['contact_ratio']) < 1e-3 and r['min_teeth'] >= 8)
        ok &= r['ok']
        rows.append(r)
    return ok, rows


def tip_lands(spec, j=0.03):
    rows, ok = [], True
    for g in spec['gears']:
        if g['kind'] == 'crown':
            continue
        nom = INV.Involute(g['teeth'], g['module'])
        thin = INV.Involute(g['teeth'], g['module'], j=j)
        r = {'gear': g['id'], 'z': g['teeth'], 'm': g['module'],
             'tip_land_nominal_over_m': nom.tip_land() / g['module'],
             'tip_land_thinned_mm': thin.tip_land(), 'fillet_over_m': thin.fillet_radius() / g['module'],
             'radii_match_spec': (abs(nom.r - g['pitch_radius']) < 1e-6 and abs(nom.ra - g['tip_radius']) < 1e-6
                                  and abs(nom.rf - g['root_radius']) < 1e-6)}
        r['ok'] = (r['tip_land_nominal_over_m'] >= 0.2 and r['tip_land_thinned_mm'] > 0
                   and r['radii_match_spec'] and g['teeth'] >= 8)
        ok &= r['ok']
        rows.append(r)
    return ok, rows


def a1_zone(spec, cat, pf):
    """Everything carried by b (except b1) inside z 4.6..33.73 must stay within r <= 63.6."""
    z0, z1 = spec.gears['a1']['z']
    rows, ok = [], True
    for p in cat.parts:
        if p['name'] == 'b1' or 'b' not in pf.chain(p['foot_body']) or p['foot_body'] == 'frame':
            continue
        if p['fz'][1] <= z0 or p['fz'][0] >= z1:
            continue
        R = pf.region(p, 'frame')
        rmax = R[4] if R[0] == 'ann' else REG.rmax_all(R, (0.0, 0.0))
        rows.append({'part': p['name'], 'r_max': round(rmax, 4)})
        ok &= rmax <= 63.6
    rows.sort(key=lambda r: -r['r_max'])
    return ok, rows


def cosmos(spec, laws):
    out, ok = {}, True
    rings = {r['body']: r for r in spec.dials['front']['cosmos_rings']}
    fols = {f['body']: f for f in spec.followers}
    # elongations of the followers relative to the mean Sun
    for body, f in fols.items():
        x, y = f['epicycle_axis_xy_in_b']
        g0 = math.atan2(y, x)
        mk = rings[body]['marker_local_deg'] * DEG
        rel = abs(float(laws.rel[f['epicycle_body']]))
        T = 1.0 / rel
        ts = np.linspace(0, T, 200001)
        W = laws.world_z_vec(ts)
        el = np.remainder(-(W[body] + mk) + W['b'] + math.pi, 2 * math.pi) - math.pi
        lim = math.asin(f['pin_d'] / f['i'])
        r = {'max_abs_elongation_deg': float(np.abs(el).max() / DEG), 'limit_deg': lim / DEG,
             'marker_local_deg_is_minus_g0': abs(K.wrap(mk + g0)) < 1e-9}
        r['ok'] = (np.abs(el).max() <= lim + 1e-9 and np.abs(el).max() >= lim - 1e-6
                   and r['marker_local_deg_is_minus_g0'])
        out['elongation_' + f['id']] = r
        ok &= r['ok']
    # retrogradation of the superior planets at opposition
    for ps in spec.pin_slots:
        if ps['carrier'] != 'b':
            continue
        slot_body = spec.body_of(ps['slot_gear'])
        out_body = laws.out_of_slot and next(o for o, s in laws.out_of_slot.items() if s == slot_body)
        mk = rings[out_body]['marker_local_deg'] * DEG
        pin_body = spec.body_of(ps['pin_gear'])
        T = 1.0 / abs(float(laws.rel[pin_body]))
        ts = np.linspace(0, 2 * T, 400001)
        W = laws.world_z_vec(ts)
        lon = np.unwrap(-(W[out_body] + mk))
        eln = -(W[out_body] + mk) + W['b']
        v = np.gradient(lon, ts)
        res = []
        # centres of retrograde arcs: local minima of the longitude speed
        ks = np.where((v[1:-1] < 0) & (v[1:-1] <= v[:-2]) & (v[1:-1] <= v[2:]))[0] + 1
        for k in ks:
            res.append(float((eln[k] / DEG) % 360.0))
        dev = [abs(e - 180.0) for e in res]
        r = {'retrograde_centres_elongation_deg': [round(e, 4) for e in res],
             'max_dev_from_180_deg': max(dev) if dev else None,
             'marker_local_deg': rings[out_body]['marker_local_deg'],
             'marker_is_180_plus_beta': abs(K.wrap(mk - math.pi - ps['offset_dir_local_deg'] * DEG)) < 1e-9}
        r['ok'] = bool(res) and max(dev) <= 1.0 and r['marker_is_180_plus_beta']
        out['retrograde_' + ps['id']] = r
        ok &= r['ok']
    # solar apogee
    mk = rings['t_trueSun']['marker_local_deg'] * DEG
    ts = np.linspace(0, 1.0, 200001)
    lon = np.unwrap(-(laws.world_z_vec(ts)['t_trueSun'] + mk))
    v = np.gradient(lon, ts)
    k = int(np.argmin(v))
    if 0 < k < len(v) - 1:
        # parabolic refinement of the minimum
        y0, y1, y2 = v[k - 1], v[k], v[k + 1]
        den = y0 - 2 * y1 + y2
        dk = 0.5 * (y0 - y2) / den if den else 0.0
    else:
        dk = 0.0
    tk = ts[k] + dk * (ts[1] - ts[0])
    ap = ((-(laws.world_z(tk)['t_trueSun'] + mk)) / DEG) % 360.0
    r = {'apogee_longitude_deg': ap}
    r['ok'] = abs(ap - 65.5) <= 0.5
    out['solar_apogee'] = r
    ok &= r['ok']
    # lunar anomaly amplitude
    p = next(p for p in spec.pin_slots if p['id'] == 'lunar')
    ts = np.linspace(0, 4237 / 56165, 200001)
    Av = laws.local_vec(ts)
    d = np.remainder(Av['kp'] - Av['k'] + math.pi, 2 * math.pi) - math.pi
    amp = float(np.abs(d).max() / DEG)
    r = {'amplitude_deg': amp, 'asin_e_over_r_deg': math.degrees(math.asin(p['offset'] / p['pin_radius']))}
    r['ok'] = abs(amp - 6.58) < 0.01
    out['lunar_anomaly'] = r
    ok &= r['ok']
    # pins always inside their slots
    worst = 0.0
    rng = np.random.default_rng(20260924)
    for t in np.concatenate([rng.uniform(-76, 76, 400), np.linspace(0, 1, 200)]):
        A = laws.local(float(t))
        for ps in spec.pin_slots:
            pb, sb = spec.body_of(ps['pin_gear']), spec.body_of(ps['slot_gear'])
            b = ps['offset_dir_local_deg'] * DEG
            P = ps['pin_radius'] * np.array([math.cos(A[pb]), math.sin(A[pb])])
            S = ps['offset'] * np.array([math.cos(b), math.sin(b)])
            v = P - S
            ang = math.atan2(v[1], v[0])
            dist = float(np.linalg.norm(v))
            worst = max(worst, abs(K.wrap(ang - A[sb])))
            if not (ps['pin_radius'] - ps['offset'] - 1e-9 <= dist <= ps['pin_radius'] + ps['offset'] + 1e-9):
                worst = max(worst, 1.0)
        W = laws.world_z(float(t), A)
        for f in spec.followers:
            q = np.array(f['epicycle_axis_xy_in_b'])
            a = A[f['epicycle_body']] + f['pin_phase_deg'] * DEG
            P = q + f['pin_d'] * np.array([math.cos(a), math.sin(a)])
            ang = math.atan2(P[1], P[0])
            worst = max(worst, abs(K.wrap(ang - (W[f['body']] - W['b']))))
            dist = float(np.linalg.norm(P))
            if not (f['i'] - f['pin_d'] - 1e-9 <= dist <= f['i'] + f['pin_d'] + 1e-9):
                worst = max(worst, 1.0)
    out['pins_in_slots'] = {'max_angle_error_rad': worst, 'ok': worst < 1e-9}
    ok &= worst < 1e-9
    return ok, out


def sectors(spec, cat, pf, pre):
    out = {}
    for p in cat.parts:
        if 'lever' in p['extra']:
            a0, a1 = p['extra']['lever']
            bad = [c for c in pre['conflicts'] if p['name'] in (c['a'], c['b'])]
            near = [c for c in pre['retained'] if p['name'] in (c['a'], c['b']) and c['frame'] == 'b-sector'
                    and 'why' not in c and c['dz'] < 0]
            out[p['name']] = {'sector_deg': [round(a0 / DEG, 3), round(a1 / DEG, 3)],
                              'z': p['z'], 'conflicts': bad, 'near_b_objects': near,
                              'ok': not bad and not near}
    return all(v['ok'] for v in out.values()), out


def run(spec, verbose=True, write=True):
    laws = K.Laws(spec)
    phases, comps = INV.compute_phases(spec, laws)
    rep, ok = {}, True
    ok1, rep['meshes'] = mesh_checks(spec)
    ok2, rep['tip_lands'] = tip_lands(spec)
    rep['phasing'] = {'components': len(comps), 'phased_gears': len(phases)}
    ok3 = len(comps) == 28 and len(phases) == 65
    inter = X2.check_all(spec, laws, phases)
    rep['interference2d'] = inter
    ok4 = all(r['ok'] for r in inter)
    cat = LAY.build(spec, laws, phases=phases)
    pf = REG.Prefilter(spec, cat)
    pre = pf.run()
    rep['prefilter'] = {'n_parts': len(cat.parts), 'n_pairs_z_overlap': pre['n_pairs_z_overlap'],
                        'n_conflicts': len(pre['conflicts']), 'conflicts': pre['conflicts'],
                        'n_intended': len(pre['intended']), 'intended': pre['intended'],
                        'n_retained': len(pre['retained'])}
    ok5 = not pre['conflicts']
    ok6, rep['a1_zone'] = a1_zone(spec, cat, pf)
    ok7, rep['sectors'] = sectors(spec, cat, pf, pre)
    ok8, rep['cosmos'] = cosmos(spec, laws)
    ok = ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7 and ok8
    rep['summary'] = {'meshes': ok1, 'tip_lands': ok2, 'phasing': ok3, 'interference2d': ok4,
                      'prefilter': ok5, 'a1_zone': ok6, 'sectors': ok7, 'cosmos': ok8, 'ok': ok}
    if write:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, 'prefilter_pairs.json'), 'w') as f:
            json.dump({'retained': pre['retained'], 'intended': pre['intended']}, f, indent=0,
                      default=float)
        with open(os.path.join(OUT, 'phases.json'), 'w') as f:
            json.dump(phases, f, indent=0)
    if verbose:
        s = rep['summary']
        print('[geometry] meshes: %d/%d ok (cd max err %.2e mm, eps min %.3f, face overlap min %.2f)' % (
            sum(r['ok'] for r in rep['meshes']), len(rep['meshes']),
            max(r['cd_error'] for r in rep['meshes']), min(r['contact_ratio'] for r in rep['meshes']),
            min(r['face_overlap'] for r in rep['meshes'])))
        print('[geometry] tip lands: nominal min %.3f m; thinned min %.4f mm -> %s' % (
            min(r['tip_land_nominal_over_m'] for r in rep['tip_lands']),
            min(r['tip_land_thinned_mm'] for r in rep['tip_lands']), s['tip_lands']))
        print('[geometry] phasing: %d components, %d gears -> %s' % (len(comps), len(phases), ok3))
        print('[geometry] 2D interference: %d/%d ok, min signed %.4f mm, backlash near [%.4f, %.4f] mm' % (
            sum(r['ok'] for r in inter), len(inter), min(r['min_signed'] for r in inter),
            min(r['backlash_near_min'] for r in inter), max(r['backlash_near_max'] for r in inter)))
        print('[geometry] pre-filter: %d parts, %d z-overlapping pairs, %d conflicts, %d intended, %d retained' % (
            len(cat.parts), pre['n_pairs_z_overlap'], len(pre['conflicts']), len(pre['intended']),
            len(pre['retained'])))
        for c in pre['conflicts']:
            print('   CONFLICT', c)
        print('[geometry] a1 keep-out: max r %.3f (limit 63.6) -> %s' % (
            rep['a1_zone'][0]['r_max'] if rep['a1_zone'] else 0, ok6))
        print('[geometry] follower sectors: %s' % {k: v['sector_deg'] for k, v in rep['sectors'].items()},
              '->', ok7)
        c = rep['cosmos']
        print('[geometry] cosmos: ' + '; '.join('%s %s' % (k, 'OK' if v['ok'] else 'FAIL') for k, v in c.items()))
        print('           apogee %.3f deg, lunar anomaly %.4f deg, elongations %s' % (
            c['solar_apogee']['apogee_longitude_deg'], c['lunar_anomaly']['amplitude_deg'],
            {k[11:]: round(v['max_abs_elongation_deg'], 4) for k, v in c.items() if k.startswith('elong')}))
        print('           retrograde centres dev from 180: %s' % {
            k[11:]: round(v['max_dev_from_180_deg'], 4) for k, v in c.items() if k.startswith('retro')})
    return ok, rep
