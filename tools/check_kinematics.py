"""Nonlinear kinematics check of spec/antikythera.json using the body-angle formulas exactly as specified."""
import json, math, sys
from fractions import Fraction as F
from pathlib import Path
import numpy as np
S = json.loads((Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'spec' / 'antikythera.json').read_text())
B = {b['id']: b for b in S['bodies']}; G = {g['id']: g for g in S['gears']}
PS = {p['id']: p for p in S['pin_slots']}; FO = {f['id']: f for f in S['followers']}
ERR = []; INFO = []
TAU = 2*math.pi
def rate(b, key='rate_rel_parent_mean'): return float(F(B[b][key]))
def angles(t):
    t = np.asarray(t, dtype=float); A = {}
    A['frame'] = 0*t; A['b'] = -TAU*t
    for bid, b in B.items():
        if b['kind'] in ('revolute',) and b['parent'] == 'frame' and bid not in ('moon',):
            A[bid] = -TAU*rate(bid)*t
    A['e_table'] = -TAU*rate('e_table')*t
    kl = -TAU*rate('k')*t
    p = PS['lunar']; be = math.radians(p['offset_dir_local_deg'])
    kpl = kl + np.arctan2(p['offset']*np.sin(kl - be), p['pin_radius'] - p['offset']*np.cos(kl - be))
    A['k_local'], A['kp_local'] = kl, kpl
    A['k'], A['kp'] = A['e_table'] + kl, A['e_table'] + kpl
    A['e_inner'] = A['e_table'] - kpl
    A['moon'] = -A['e_inner']
    A['q_rel'] = A['b'] - A['moon']
    for bid, b in B.items():
        if b['parent'] == 'b' and b['kind'] == 'revolute':
            A[bid + '_local'] = -TAU*rate(bid)*t; A[bid] = A['b'] + A[bid + '_local']
    for pid, slot_body, out in (('saturn', 'x_sa86s', 't_saturn'), ('jupiter', 'x_ju65s', 't_jupiter'), ('mars', 'x_ma80s', 't_mars')):
        p = PS[pid]; pin_body = G[p['pin_gear']]['body']; be = math.radians(p['offset_dir_local_deg'])
        th = A[pin_body + '_local']
        sl = th + np.arctan2(p['offset']*np.sin(th - be), p['pin_radius'] - p['offset']*np.cos(th - be))
        A[slot_body + '_local'] = sl; A[slot_body] = A['b'] + sl; A[out] = A['b'] - sl
    for f in S['followers']:
        g0 = math.atan2(f['epicycle_axis_xy_in_b'][1], f['epicycle_axis_xy_in_b'][0])
        lam = A[f['epicycle_body'] + '_local'] + math.radians(f['pin_phase_deg']) - g0
        A[f['body']] = A['b'] + g0 + np.arctan2(f['pin_d']*np.sin(lam), f['i'] + f['pin_d']*np.cos(lam))
    return A
rng = np.random.default_rng(20260924)
T = np.r_[0.0, rng.uniform(-50, 50, 400)]
A = angles(T)
# 1. Willis in angle form for every spur mesh
def gear_world(g): return A[G[g]['body']]
worst = 0
for m in S['meshes']:
    if m['type'] != 'external': continue
    c = {'frame': A['frame'], 'b': A['b'], 'e_table': A['e_table']}[m['carrier']]
    z1, z2 = G[m['driver']]['teeth'], G[m['driven']]['teeth']
    v = z1*(gear_world(m['driver']) - c) + z2*(gear_world(m['driven']) - c)
    dev = np.max(np.abs(v - v[0]))/z2
    worst = max(worst, dev)
    if dev > 1e-9: ERR.append(f"Willis angle relation broken on {m['driver']}~{m['driven']}: {dev:.3e} rad")
INFO.append(f"Willis (angles) on {sum(m['type']=='external' for m in S['meshes'])} meshes at 401 t: max deviation {worst:.2e} rad")
# 2. crowns
INFO.append("crown a1/b1: theta_b1 = (48/223)*theta_a by definition of the driver laws")
qdev = np.max(np.abs(A['q_rel'] - (A['b'] - A['moon'])))
INFO.append(f"crown b0/q1: q = theta_b - theta_moon (dev {qdev:.1e}); theta_q(0) = {A['q_rel'][0]:.7f} rad; mean rate check below")
t_lin = np.linspace(0, 19, 200001); AL = angles(t_lin)
qmean = (AL['q_rel'][-1] - AL['q_rel'][0])/(TAU*19)
if abs(qmean - 235/19) > 1e-3: ERR.append(f"q mean rate {qmean} != 235/19")
lin_dev = np.max(np.abs(AL['q_rel'] - TAU*235/19*t_lin - AL['q_rel'][0]))
INFO.append(f"q mean rate {qmean:.6f} (235/19 = {235/19:.6f}); a LINEAR q law would drift up to {math.degrees(lin_dev):.2f} deg (the lunar anomaly)")
# 3. pins stay in their slots
def rot(v, a): c, s = np.cos(a), np.sin(a); return np.stack([c*v[0] - s*v[1], s*v[0] + c*v[1]])
Kl = np.array(B['k']['axis_xy_in_parent']); Kpl = np.array(B['kp']['axis_xy_in_parent'])
for pid in ('lunar', 'saturn', 'jupiter', 'mars'):
    p = PS[pid]
    pb, sb = G[p['pin_gear']]['body'], G[p['slot_gear']]['body']
    if pid == 'lunar': Pax, Sax, th_p, th_s = Kl, Kpl, AL['k_local'], AL['kp_local']
    else: Pax, Sax, th_p, th_s = np.array(B[pb]['axis_xy_in_parent']), np.array(B[sb]['axis_xy_in_parent']), AL[pb + '_local'], AL[sb + '_local']
    pin = Pax[:, None] + p['pin_radius']*np.stack([np.cos(th_p), np.sin(th_p)])
    rel = pin - Sax[:, None]; dist = np.hypot(*rel); ang = np.arctan2(rel[1], rel[0])
    angerr = np.max(np.abs((ang - th_s + math.pi) % TAU - math.pi))
    lo, hi = p['pin_radius'] - p['offset'], p['pin_radius'] + p['offset']
    if dist.min() < lo - 1e-9 or dist.max() > hi + 1e-9 or angerr > 1e-9: ERR.append(f"pin {pid} leaves its slot (r {dist.min():.3f}..{dist.max():.3f}, ang err {angerr:.1e})")
    INFO.append(f"pin {pid}: radius in slot {dist.min():.3f}..{dist.max():.3f} (slot centreline {lo:.2f}..{hi:.2f}), angle error {angerr:.1e}")
for f in S['followers']:
    ax = np.array(f['epicycle_axis_xy_in_b']); axw = rot(ax[:, None]*np.ones_like(t_lin), AL['b'])
    psi = AL[f['epicycle_body']] + math.radians(f['pin_phase_deg'])
    P = axw + f['pin_d']*np.stack([np.cos(psi), np.sin(psi)])
    r = np.hypot(*P); ang = np.arctan2(P[1], P[0])
    angerr = np.max(np.abs((ang - AL[f['body']] + math.pi) % TAU - math.pi))
    if angerr > 1e-9 or r.min() < f["i"] - f["pin_d"] - 1e-7 or r.max() > f["i"] + f["pin_d"] + 1e-7: ERR.append(f"follower {f['id']} misses its pin")
    INFO.append(f"follower {f['id']}: pin radius {r.min():.3f}..{r.max():.3f}, lever angle error {angerr:.1e}")
# 4. displays
MK = {r['body']: math.radians(r['marker_local_deg']) for r in S['dials']['front']['cosmos_rings']}
lam_sun = -AL['b']
def lon(body): return -(AL[body] + MK[body])
def wrapd(x): return (np.degrees(x) + 180) % 360 - 180
for f in S['followers']:
    el = wrapd(lon(f['body']) - lam_sun); amp = math.degrees(math.asin(f['pin_d']/f['i']))
    if np.max(np.abs(el)) > amp + 1e-6: ERR.append(f"{f['id']} elongation {np.max(np.abs(el)):.2f} > {amp:.2f}")
    INFO.append(f"{f['id']}: elongation from mean Sun within +-{np.max(np.abs(el)):.3f} deg (max allowed {amp:.3f})")
tl = np.unwrap(lon('t_trueSun')); v = np.gradient(tl, t_lin); k = np.argmin(v[1000:21000]) + 1000
apo = (math.degrees(tl[k]) % 360)
INFO.append(f"true Sun apogee (slowest motion) at longitude {apo:.2f} deg")
if abs(apo - 65.5) > 0.5: ERR.append(f"solar apogee at {apo:.2f}, expected 65.5")
for body, name in (('t_mars', 'Mars'), ('t_jupiter', 'Jupiter'), ('t_saturn', 'Saturn')):
    tt = np.linspace(0, 60, 600001); AA = angles(tt)
    L_ = np.unwrap(-(AA[body] + MK[body])); vv = np.gradient(L_, tt); ls = -AA['b']
    mins = [i for i in range(1, len(vv)-1) if vv[i] < vv[i-1] and vv[i] <= vv[i+1] and vv[i] < 0]
    els = [wrapd(L_[i] - ls[i]) for i in mins]
    worst_el = max(abs(abs(e) - 180) for e in els) if els else 999
    INFO.append(f"{name}: {len(mins)} retrogrades in 60 yr, elongation at mid-retrograde within {worst_el:.3f} deg of 180")
    if worst_el > 1.0: ERR.append(f"{name} retrograde not at opposition ({worst_el:.2f} deg off)")
anom = wrapd(AL["moon"] + TAU*254/19*t_lin); anom = (anom.max() - anom.min())/2*np.ones(1)
INFO.append(f"lunar anomaly amplitude {np.max(np.abs(anom)):.3f} deg (asin(1.1/9.6) = {math.degrees(math.asin(1.1/9.6)):.3f})")
# 5. spiral psi from c equals unwrapped pointer rotation modulo the spiral length
for c in rng.uniform(-50, 50, 200):
    th_n = -TAU*float(F(B['n']['rate_abs_mean']))*c; th_g = -TAU*float(F(B['g']['rate_abs_mean']))*c
    pm = 10*math.pi*(((c/19) % 1 + 1) % 1); ps = 8*math.pi*(((c*235/4237) % 1 + 1) % 1)
    if abs(((th_n - pm) + 5*math.pi) % (10*math.pi) - 5*math.pi) > 1e-9 or abs(((th_g - ps) + 4*math.pi) % (8*math.pi) - 4*math.pi) > 1e-9:
        ERR.append("spiral psi formula mismatch"); break
INFO.append("spiral psi_mod formulas match the n/g rotations modulo 5 and 4 turns")
print("\n".join(INFO))
if ERR: print(f"\nFAILED ({len(ERR)}):"); [print("  -", e) for e in ERR]; sys.exit(1)
print("KINEMATICS OK")
