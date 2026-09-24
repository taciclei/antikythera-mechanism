"""Independent validation of spec/antikythera.json (reads ONLY the JSON; shares no code with make_spec.py).

1. Global exact linear solve (Fraction Gauss-Jordan) of all mean rates from meshes / pin-slots / followers:
   rank, degrees of freedom, consistency, and equality with every body's declared rate and every target.
2. Geometry: mesh centre distances vs modules, equal modules, face overlap, contact ratio, undercut.
3. Collision screening of gears, arbors, tubes, pillars, pins, followers and plates (circles/annuli per layer,
   swept annuli between frames, radial intervals on the central axis, follower swing sectors, a1 keep-out).
"""
import json, math, sys
from fractions import Fraction as F
from pathlib import Path

S = json.loads((Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'spec' / 'antikythera.json').read_text())
ERR, INFO = [], []
def err(m): ERR.append(m)
G = {g['id']: g for g in S['gears']}
B = {b['id']: b for b in S['bodies']}
AX = S['axes_world_xy']; E = tuple(AX['E'])
def fr(s): return None if s is None else F(s)

# ---------------- 1. global linear solve ----------------
moving = [b for b in B if B[b]['kind'] != 'fixed' and b not in ('a', 'q')]
idx = {b: i for i, b in enumerate(moving)}
n = len(moving)
rows = []
def w(body):  # returns coefficient vector for body rate
    v = [F(0)]*(n+1)
    if body in idx: v[idx[body]] = F(1)
    return v
def lin(*terms):  # terms: (coef, body)
    v = [F(0)]*(n+1)
    for c, b in terms:
        if b in idx: v[idx[b]] += c
    return v
for m in S['meshes']:
    if m['type'] == 'crown': continue
    g1, g2, c = m['driver'], m['driven'], m['carrier']
    b1, b2 = G[g1]['body'], G[g2]['body']
    z1, z2 = G[g1]['teeth'], G[g2]['teeth']
    rows.append(lin((F(z1), b1), (F(z2), b2), (-F(z1 + z2), c)))           # z1(w1-wc) + z2(w2-wc) = 0
for ps in S['pin_slots']:
    rows.append(lin((F(1), G[ps['slot_gear']]['body']), (F(-1), G[ps['pin_gear']]['body'])))
for fo in S['followers']:
    rows.append(lin((F(1), fo['body']), (F(-1), 'b')))
inp = [F(0)]*(n+1); inp[idx['b']] = F(1); inp[n] = F(1)                  # input: b = +1
A = [r[:] for r in rows]
def rank_of(mat):
    M = [r[:] for r in mat]; rk = 0; col = 0; rows_ = len(M)
    for col in range(n):
        piv = next((r for r in range(rk, rows_) if M[r][col] != 0), None)
        if piv is None: continue
        M[rk], M[piv] = M[piv], M[rk]
        pv = M[rk][col]; M[rk] = [x/pv for x in M[rk]]
        for r in range(rows_):
            if r != rk and M[r][col] != 0:
                f = M[r][col]; M[r] = [a - f*b for a, b in zip(M[r], M[rk])]
        rk += 1
    return rk, M
rk, _ = rank_of(A)
dof = n - rk
INFO.append(f"linear system: {n} moving bodies, {len(rows)} constraints, rank {rk}, DOF {dof}, redundant {len(rows) - rk}")
if dof != 1: err(f"DOF must be 1, got {dof}")
rk2, R = rank_of(A + [inp])
if rk2 != n: err(f"system with input not fully determined (rank {rk2} of {n})")
for r in R:
    if all(x == 0 for x in r[:n]) and r[n] != 0: err("inconsistent constraints (mechanism would jam)")
sol = {}
for r in R:
    nz = [i for i in range(n) if r[i] != 0]
    if len(nz) == 1: sol[moving[nz[0]]] = r[n]/r[nz[0]]
sol['frame'] = F(0)
for b in moving:
    if b not in sol: err(f"rate of {b} undetermined"); continue
    decl = fr(B[b]['rate_abs_mean'])
    if decl != sol[b]: err(f"declared rate of {b} = {decl} but solve gives {sol[b]}")
def tv(expr):
    if expr == 'a': return F(223, 48)
    if expr == 'q@moon': return abs(sol['b'] - sol['moon'])
    if expr == 'moon-t_nodes': return sol['moon'] - sol['t_nodes']
    if '@' in expr: x, c = expr.split('@'); return sol[x] - sol[c]
    return sol[expr]
for t in S['targets']:
    if tv(t['expr']) != F(t['value']): err(f"target {t['name']}: {tv(t['expr'])} != {t['value']}")
INFO.append(f"targets checked: {len(S['targets'])}")

# ---------------- 2. mesh geometry ----------------
alpha = math.radians(S['tooth']['pressure_angle_deg']); ha = S['tooth']['addendum_coeff']
def world_axis(g):
    b = B[G[g]['body']]
    if b['parent'] == 'e_table': return (E[0] + b['axis_xy_in_parent'][0], E[1] + b['axis_xy_in_parent'][1])
    return tuple(b['axis_xy_in_parent']) if b['axis_xy_in_parent'] else (0.0, 0.0)
def d2(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
for m in S['meshes']:
    if m['type'] == 'crown': continue
    g1, g2 = G[m['driver']], G[m['driven']]
    if abs(g1['module'] - g2['module']) > 1e-9: err(f"module mismatch {g1['id']}~{g2['id']}")
    a = g1['module']*(g1['teeth'] + g2['teeth'])/2
    d = d2(world_axis(g1['id']), world_axis(g2['id']))
    if abs(d - a) > 1e-6: err(f"centre distance {g1['id']}~{g2['id']}: {d:.5f} vs {a:.5f}")
    zo = min(g1['z'][1], g2['z'][1]) - max(g1['z'][0], g2['z'][0])
    if zo < 0.5: err(f"face overlap {g1['id']}~{g2['id']} {zo:.2f}")
    r1, r2 = g1['pitch_radius'], g2['pitch_radius']; m_ = g1['module']
    eps = (math.sqrt((r1+ha*m_)**2-(r1*math.cos(alpha))**2) + math.sqrt((r2+ha*m_)**2-(r2*math.cos(alpha))**2) - a*math.sin(alpha))/(math.pi*m_*math.cos(alpha))
    if eps < 1.2: err(f"contact ratio {g1['id']}~{g2['id']} {eps:.3f}")
zmin = 2*ha/math.sin(alpha)**2
if min(g['teeth'] for g in S['gears']) < zmin - 1e-9: err("undercut")
used = [g['module'] for g in S['gears']]
INFO.append(f"meshes checked: {sum(1 for m in S['meshes'] if m['type'] != 'crown')}, modules {min(used):.4f}..{max(used):.4f}")

# ---------------- 3. collision screening ----------------
def group(body):
    if body == 'b' or B[body]['parent'] == 'b': return 'b'
    if body == 'e_table' or B[body]['parent'] == 'e_table': return 'e_table'
    if body == 'moon' or B[body]['parent'] == 'moon': return 'moon'
    return 'frame'
CENTRE = {'b': (0.0, 0.0), 'e_table': E, 'moon': (0.0, 0.0)}
def body_axis_world(bid):
    b = B[bid]
    if b['axis_xy_in_parent'] is None: return (0.0, 0.0)
    if b['parent'] == 'e_table': return (E[0] + b['axis_xy_in_parent'][0], E[1] + b['axis_xy_in_parent'][1])
    return tuple(b['axis_xy_in_parent'])
OBJ = []
def add(name, body, c, rin, rout, z0, z1, tags=(), sweep_about=None):
    OBJ.append(dict(name=name, body=body, grp=group(body), c=tuple(c), rin=rin, rout=rout, z0=z0, z1=z1, tags=set(tags), sweep_about=sweep_about))
for t in S['tubes']:
    add(t['id'], t['body'], (0, 0), t['r_in'], t['r_out'], t['z'][0], t['z'][1], tags={'tube'})
for g in S['gears']:
    if g['kind'] == 'crown': continue
    add(g['id'], g['body'], world_axis(g['id']), g['bore_radius'], g['tip_radius'], g['z'][0], g['z'][1], tags={'gear'})
for it in S['shafts']['items']:
    if 'r' not in it: continue
    add(it['id'], it['owner'], body_axis_world(it['axis_body']), it.get('r_in', 0.0), it['r'], it['z'][0], it['z'][1], tags={'shaft'})
# pins: annulus band swept about the owner's axis (the owner turns relative to its carrier)
for p in S['shafts']['pins']:
    own = p['owner']
    if 'local_xy' in p: d = math.hypot(*p['local_xy'])
    else: d = next(f['pin_d'] for f in S['followers'] if f['epicycle_body'] == own)
    add(p['id'], own, body_axis_world(own), max(d - p['r'], 0), d + p['r'], p['z'][0], p['z'][1], tags={'pin'}, sweep_about='own')
for s_ in S['structure']:
    if s_['id'] in ('short_pillars', 'long_pillars'):
        hw = math.hypot(*s_['section'])/2
        for k, (r, ang) in enumerate(s_['polar']):
            add(f"{s_['id']}_{k}", 'b', (r*math.cos(math.radians(ang)), r*math.sin(math.radians(ang))), 0.0, hw, s_['z'][0], s_['z'][1], tags={'pillar'})
LEV = {'mercury_follower': ('t_mercury', 52.0), 'venus_follower': ('t_venus', 49.5), 'true_sun_follower': ('t_trueSun', 43.5)}
TUBE_OF = {t['body']: t for t in S['tubes']}
for s_ in S['structure']:
    if s_['id'] in LEV:
        body, reach = LEV[s_['id']]
        add(s_['id'], body, (0, 0), TUBE_OF[body]['r_in'], reach, s_['z'][0], s_['z'][1], tags={'follower'})
    if s_['id'] in ('mercury_disk', 'venus_disk'):
        add(s_['id'], s_['body'], body_axis_world(s_['body']), 1.4, s_['radius'], s_['z'][0], s_['z'][1], tags={'disk'})
for ring in S['dials']['front']['cosmos_rings']:
    add(f"ring_{ring['body']}", ring['body'], (0, 0), TUBE_OF[ring['body']]['r_in'], ring['radii'][1], ring['z'][0], ring['z'][1], tags={'ring'})
    # marker sphere resting on the ring front face (swept circle about the centre)
    rr = 1.6 if ring['body'] == 't_trueSun' else 1.2
    add(f"marker_{ring['body']}", ring['body'], (0, 0), ring['marker_r'] - rr, ring['marker_r'] + rr, ring['z'][1], ring['z'][1] + 2*rr, tags={'marker'})
dp = S['dials']['front']['date_pointer']; add('date_pointer', 'b', (0, 0), 7.0, dp['length'], dp['z'][0], dp['z'][1])
dh = S['dials']['front']['dragon_hand']; add('dragon_hand', 't_nodes', (0, 0), 2.1, dh['half_length'], dh['z'][0], dh['z'][1])
mp = S['dials']['front']['moon_pointer']; add('moon_arm', 'moon', (0, 0), 1.2, mp['length'], mp['arm_z'][0], mp['arm_z'][1])
q1c = S['crowns']['q1']; rq = q1c['disc']['r_out']
add('q1_crown', 'q', (0, 0), 4.5, math.hypot(q1c['disc']['u'][1], rq), q1c['axis_z'] - rq, q1c['axis_z'] + rq, tags={'crown'})
a1c = S['crowns']['a1']
if a1c['axis_z'] + a1c['disc']['r_out'] > 34.15 - 0.05 and a1c['disc']['x'][0] < 65.0 + 0.15: err("a1 crown disc reaches the CP")
add('main_plate', 'frame', (0, 0), 2.3, 999, -2.0, 0.0, tags={'plate'})
add('back_plate', 'frame', (0, 0), 0.0, 999, -16.5, -15.0, tags={'plate'})
add('front_plate', 'frame', (0, 0), 7.8, 999, 40.0, 41.5, tags={'plate'})
add('sub_plate', 'frame', (0, 0), 7.8, 60.0, 37.45, 38.65, tags={'plate'})
add('fx56_spacer', 'frame', (0, 0), 7.8, 12.0, 37.30, 37.45)
add('cp_plate', 'b', (0, 0), 7.5, 65.0, 34.15, 36.15, tags={'plate'})
add('b1_web', 'b', (0, 0), 3.2, 53.0, 3.95, 7.85, tags={'plate'})
add('d_plate_zone', 'b', (0, 0), 0, 0, 0, 0)  # placeholder (D-plate shape checked by geometry review)
OBJ = [o for o in OBJ if o['rout'] > 0]

MESH = {frozenset((m['driver'], m['driven'])) for m in S['meshes']} | {frozenset(('q1_crown', 'b0'))}
SLOT_OF = {p['id']: p['slot_in'] for p in S['shafts']['pins']}
LEVER_BODY = {'mercury_follower': 't_mercury', 'venus_follower': 't_venus', 'true_sun_follower': 't_trueSun'}
def intended(o1, o2):
    a, b = o1['name'], o2['name']
    if o1['body'] == o2['body']: return True
    if frozenset((a, b)) in MESH: return True
    for x, y in ((a, b), (b, a)):
        if x in SLOT_OF and SLOT_OF[x] == y: return True
    if ('plate' in o1['tags'] and o2['tags'] & {'shaft', 'tube', 'pin'}) or ('plate' in o2['tags'] and o1['tags'] & {'shaft', 'tube', 'pin'}):
        return True   # clearance holes
    return False

def swept(o):
    """(centre, lo, hi): region swept relative to the frame. Objects rigid with a rotating carrier sweep an annulus about
    the carrier centre; objects on their own rotating axis inside a carrier (pins) are first expanded about that axis."""
    c, lo, hi = o['c'], o['rin'], o['rout']
    cc = CENTRE.get(o['grp'])
    if o['grp'] == 'frame' or cc is None:
        return c, lo, hi
    r = math.hypot(c[0]-cc[0], c[1]-cc[1])
    if r < 1e-9: return cc, lo, hi
    return cc, max(r - hi, 0.0), r + hi
SECT = {}
for fo in S['followers']:
    c = B[fo['epicycle_body']]['axis_xy_in_parent']; g0 = math.degrees(math.atan2(c[1], c[0])); half = math.degrees(math.asin(fo['pin_d']/fo['i']))
    SECT[{'mercury': 'mercury_follower', 'venus': 'venus_follower', 'trueSun': 'true_sun_follower'}[fo['id']]] = (g0 - half, g0 + half)
def in_sector(o, sec, half_w=1.5):
    ang = math.degrees(math.atan2(o['c'][1], o['c'][0])); r = max(math.hypot(*o['c']), 1e-6)
    marg = math.degrees(math.asin(min(1.0, (o['rout'] + half_w)/r))) if r > o['rout'] + half_w else 180
    lo, hi = sec[0] - marg, sec[1] + marg
    return ((ang - lo) % 360) <= (hi - lo)
CLEAR, BEARING = 0.15, 0.04
bad = []
for i in range(len(OBJ)):
    for j in range(i+1, len(OBJ)):
        o1, o2 = OBJ[i], OBJ[j]
        zo = min(o1['z1'], o2['z1']) - max(o1['z0'], o2['z0'])
        if zo < 0.0 or (zo == 0.0): continue          # touching faces only allowed between different bodies if no area overlap; z-disjoint here
        if intended(o1, o2): continue
        lev = o1 if o1['name'] in SECT else (o2 if o2['name'] in SECT else None)
        if lev is not None:
            oth = o2 if lev is o1 else o1
            if oth['grp'] == 'b' and math.hypot(*oth['c']) > 1e-9:
                if math.hypot(*oth['c']) - oth['rout'] >= lev['rout'] + CLEAR or not in_sector(oth, SECT[lev['name']]): continue
                bad.append(f"{o1['name']} / {o2['name']}: inside swing sector"); continue
        c1, lo1, hi1 = swept(o1); c2, lo2, hi2 = swept(o2)
        same_rigid = o1['grp'] == o2['grp'] and o1['grp'] != 'frame'
        if same_rigid:   # both rigid in the same rotating carrier: compare actual positions
            c1, lo1, hi1 = o1['c'], o1['rin'], o1['rout']; c2, lo2, hi2 = o2['c'], o2['rin'], o2['rout']
        dd = math.hypot(c1[0]-c2[0], c1[1]-c2[1])
        if dd < 1e-9:
            gap = max(lo2 - hi1, lo1 - hi2); need = BEARING
        else:
            gap = dd - hi1 - hi2; need = CLEAR
            if lo1 > 0 and dd + hi2 <= lo1: gap, need = lo1 - (dd + hi2), CLEAR
            if lo2 > 0 and dd + hi1 <= lo2: gap, need = lo2 - (dd + hi1), CLEAR
        if gap < need: bad.append(f"{o1['name']} / {o2['name']}: gap {gap:.3f} < {need} z[{max(o1['z0'], o2['z0']):.2f},{min(o1['z1'], o2['z1']):.2f}]")
for b_ in bad: err("collision screen: " + b_)
a1 = S['crowns']['a1']; kz0, kz1 = 4.60, 33.73
for o in OBJ:
    if o['grp'] != 'b' or o['z1'] <= kz0 or o['z0'] >= kz1 or o['name'] in ('b1', 'b1_web'): continue
    if 'pillar' in o['tags']:
        s_ = next(x for x in S['structure'] if o['name'].startswith(x['id']))
        reach = math.hypot(math.hypot(*o['c']) + min(s_['section'])/2, max(s_['section'])/2)
    else:
        reach = math.hypot(*o['c']) + o['rout']
    if reach > 63.6: err(f"a1 keep-out: {o['name']} reaches {reach:.2f}")
INFO.append(f"collision screen: {len(OBJ)} objects, {len(OBJ)*(len(OBJ)-1)//2} pairs")
print("\n".join(INFO))
if ERR:
    print(f"\nFAILED ({len(ERR)}):"); [print("  -", e) for e in ERR]; sys.exit(1)
print("VALID: all independent checks passed")
