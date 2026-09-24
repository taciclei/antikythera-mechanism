"""Exact kinematics: Willis equations solved with fractions.Fraction, DOF, targets,
and the float64 angle laws theta(t) of every body (linear, pin-slot, follower, composite)."""
import math

import numpy as np
from fractions import Fraction

TWO_PI = 2.0 * math.pi
FIXED = ('frame',)
EXCLUDED = ('frame', 'a', 'q')   # not unknowns of the linear system


# ---------------------------------------------------------------- exact solver
def _equations(spec):
    """Rows as ({body: coeff}, rhs, label). frame has w = 0 and is dropped."""
    rows = []

    def add(coeffs, rhs, label):
        c = {}
        for b, v in coeffs:
            if b in FIXED:
                continue
            c[b] = c.get(b, 0) + Fraction(v)
        rows.append(({k: v for k, v in c.items() if v != 0}, Fraction(rhs), label))

    for m in spec.external_meshes:
        g1, g2 = spec.gears[m['driver']], spec.gears[m['driven']]
        z1, z2 = g1['teeth'], g2['teeth']
        C = m['carrier']
        # z1*(w1 - wC) + z2*(w2 - wC) = 0
        add([(g1['body'], z1), (g2['body'], z2), (C, -(z1 + z2))], 0,
            'willis %s~%s (%s)' % (m['driver'], m['driven'], C))
    for ps in spec.pin_slots:
        add([(spec.body_of(ps['slot_gear']), 1), (spec.body_of(ps['pin_gear']), -1)], 0,
            'pin-slot %s' % ps['id'])
    for f in spec.followers:
        add([(f['body'], 1), ('b', -1)], 0, 'follower %s' % f['id'])
    return rows


def _rref(matrix, ncols):
    """In-place exact Gauss-Jordan. matrix rows have ncols coefficients + 1 rhs.
    Returns (rank, pivot_cols)."""
    rank = 0
    pivots = []
    nrows = len(matrix)
    for col in range(ncols):
        piv = None
        for r in range(rank, nrows):
            if matrix[r][col] != 0:
                piv = r
                break
        if piv is None:
            continue
        matrix[rank], matrix[piv] = matrix[piv], matrix[rank]
        p = matrix[rank][col]
        matrix[rank] = [v / p for v in matrix[rank]]
        for r in range(nrows):
            if r != rank and matrix[r][col] != 0:
                f = matrix[r][col]
                matrix[r] = [a - f * b for a, b in zip(matrix[r], matrix[rank])]
        pivots.append(col)
        rank += 1
        if rank == nrows:
            break
    return rank, pivots


def solve(spec):
    """Solve all mean absolute rates. Returns a result dict."""
    unknowns = [b['id'] for b in spec['bodies'] if b['id'] not in EXCLUDED]
    idx = {b: i for i, b in enumerate(unknowns)}
    n = len(unknowns)
    eqs = _equations(spec)
    counts = {'willis': sum(1 for e in eqs if e[2].startswith('willis')),
              'pin_slot': sum(1 for e in eqs if e[2].startswith('pin-slot')),
              'follower': sum(1 for e in eqs if e[2].startswith('follower'))}

    def mat(rows):
        M = []
        for coeffs, rhs, _ in rows:
            r = [Fraction(0)] * (n + 1)
            for b, v in coeffs.items():
                r[idx[b]] += v
            r[n] = rhs
            M.append(r)
        return M

    H = mat(eqs)
    rank_h, _ = _rref(H, n)
    inconsistent_h = sum(1 for r in H if all(v == 0 for v in r[:n]) and r[n] != 0)
    # add the input: w_b = 1
    A = mat(eqs + [({'b': Fraction(1)}, Fraction(1), 'input b = 1')])
    rank_a, pivots = _rref(A, n)
    inconsistent = sum(1 for r in A if all(v == 0 for v in r[:n]) and r[n] != 0)
    rates = {}
    if rank_a == n and inconsistent == 0:
        for r_i, col in enumerate(pivots):
            rates[unknowns[col]] = A[r_i][n]
    rates['frame'] = Fraction(0)
    return {
        'unknowns': unknowns, 'n_unknowns': n, 'n_equations': len(eqs), 'counts': counts,
        'rank': rank_h, 'dof': n - rank_h, 'rank_with_input': rank_a,
        'inconsistent': inconsistent + inconsistent_h, 'rates': rates,
    }


def eval_target(spec, rates, expr):
    if expr == 'a':      # crank: |w_b| * z_b1 / z_a1 (definition, crown mesh a1~b1)
        return abs(rates['b']) * Fraction(spec.gears['b1']['teeth'], spec.gears['a1']['teeth'])
    if expr == 'q@moon':  # |w_b - w_moon| * z_b0 / z_q1 (crown b0~q1 on the Moon carrier)
        return abs(rates['b'] - rates['moon']) * Fraction(spec.gears['b0']['teeth'],
                                                          spec.gears['q1']['teeth'])
    if '@' in expr:
        x, y = expr.split('@')
        return rates[x] - rates[y]
    if '-' in expr:
        x, y = expr.split('-')
        return rates[x] - rates[y]
    return rates[expr]


def check(spec):
    """Full exact check. Returns (ok, report dict)."""
    res = solve(spec)
    rates = res['rates']
    rate_errors = []
    for b in spec['bodies']:
        bid = b['id']
        if bid in EXCLUDED[1:]:
            continue
        exp = Fraction(b['rate_abs_mean'])
        got = rates.get(bid)
        if got != exp:
            rate_errors.append((bid, str(got), str(exp)))
        if b['rate_rel_parent_mean'] is not None and got is not None:
            rel = got - rates[b['parent']]
            if rel != Fraction(b['rate_rel_parent_mean']):
                rate_errors.append((bid + ' (rel)', str(rel), b['rate_rel_parent_mean']))
    targets = []
    for t in spec.targets:
        got = eval_target(spec, rates, t['expr']) if rates else None
        targets.append({'name': t['name'], 'expr': t['expr'], 'expected': t['value'],
                        'got': str(got), 'ok': got == Fraction(t['value'])})
    ok = (res['dof'] == 1 and res['rank'] == 44 and res['n_unknowns'] == 45
          and res['n_equations'] == 44 and res['inconsistent'] == 0 and not rate_errors
          and all(t['ok'] for t in targets) and len(targets) == 22)
    rep = dict(res)
    rep['rates'] = {k: str(v) for k, v in rates.items()}
    rep['rate_errors'] = rate_errors
    rep['targets'] = targets
    rep['ok'] = ok
    return ok, rep


# ---------------------------------------------------------------- angle laws (float64)
def lin_angle(rate, t):
    """-2*pi*rate*t reduced exactly modulo 2*pi (rate Fraction, t float). Result in (-2pi, 0]."""
    r = Fraction(rate) * Fraction(t)
    f = r - math.floor(r)
    return -TWO_PI * float(f)


def pin_slot_angle(th1, e, r, beta):
    return th1 + math.atan2(e * math.sin(th1 - beta), r - e * math.cos(th1 - beta))


def follower_rel(th_epi, i, d, g0, phase):
    lam = th_epi + phase - g0
    return g0 + math.atan2(d * math.sin(lam), i + d * math.cos(lam))


class Laws:
    """Angle laws of every body, built from the spec (constants read as float64)."""

    def __init__(self, spec):
        self.spec = spec
        self.rel = {b['id']: (Fraction(b['rate_rel_parent_mean'])
                              if b['rate_rel_parent_mean'] is not None else None)
                    for b in spec['bodies']}
        self.crank_rate = Fraction(spec.gears['b1']['teeth'], spec.gears['a1']['teeth'])
        self.ps = {}   # slot body -> (pin body, e, r, beta, carrier)
        for p in spec.pin_slots:
            self.ps[spec.body_of(p['slot_gear'])] = (
                spec.body_of(p['pin_gear']), p['offset'], p['pin_radius'],
                math.radians(p['offset_dir_local_deg']), p['carrier'])
        self.fol = {}
        for f in spec.followers:
            x, y = f['epicycle_axis_xy_in_b']
            self.fol[f['body']] = (f['epicycle_body'], f['i'], f['pin_d'], math.atan2(y, x),
                                   math.radians(f['pin_phase_deg']))
        # outputs driven through a slot gear on carrier b (equal tooth counts, see meshes)
        self.out_of_slot = {}
        for m in spec.external_meshes:
            b1, b2 = spec.body_of(m['driver']), spec.body_of(m['driven'])
            if b1 in self.ps and m['carrier'] == 'b':
                self.out_of_slot[b2] = b1
        self.linear = [b['id'] for b in spec['bodies']
                       if b['kind'] == 'revolute' and b['id'] not in ('b',)] + ['b']

    def local(self, t):
        """Angles relative to each body's Blender parent (rad). 'a' about +x, 'q' about the
        Moon's local +x; all others about +z."""
        A = {'frame': 0.0}
        for b in self.spec['bodies']:
            bid = b['id']
            if b['kind'] == 'revolute':
                A[bid] = lin_angle(self.rel[bid], t)
        A['a'] = lin_angle(self.crank_rate, t)
        for s, (p, e, r, beta, _) in self.ps.items():
            A[s] = pin_slot_angle(A[p], e, r, beta)
        # e_inner (world) = theta_e_table - theta_kp   (k2~e6, 50:50, carrier e_table)
        A['e_inner'] = A['e_table'] - A['kp']
        # moon (world) = -theta_e_inner                  (e1~b3, 32:32, carrier frame)
        A['moon'] = -A['e_inner']
        for out, slot in self.out_of_slot.items():
            A[out] = A['b'] - A[slot]
        for fb, (epi, i, d, g0, ph) in self.fol.items():
            A[fb] = A['b'] + follower_rel(A[epi], i, d, g0, ph)
        # q about the Moon's radial axis: theta_b - theta_moon (world z-angles)
        A['q'] = A['b'] - A['moon']
        return A

    def local_vec(self, ts):
        """Vectorised float64 version of local() for an array of times (analysis only)."""
        ts = np.asarray(ts, float)

        def lin(rate):
            return -TWO_PI * np.mod(float(rate) * ts, 1.0)
        A = {'frame': np.zeros_like(ts)}
        for b in self.spec['bodies']:
            if b['kind'] == 'revolute':
                A[b['id']] = lin(self.rel[b['id']])
        A['a'] = lin(self.crank_rate)
        for s, (p, e, r, beta, _) in self.ps.items():
            A[s] = A[p] + np.arctan2(e * np.sin(A[p] - beta), r - e * np.cos(A[p] - beta))
        A['e_inner'] = A['e_table'] - A['kp']
        A['moon'] = -A['e_inner']
        for out, slot in self.out_of_slot.items():
            A[out] = A['b'] - A[slot]
        for fb, (epi, i, d, g0, ph) in self.fol.items():
            lam = A[epi] + ph - g0
            A[fb] = A['b'] + g0 + np.arctan2(d * np.sin(lam), i + d * np.cos(lam))
        A['q'] = A['b'] - A['moon']
        return A

    def world_z_vec(self, ts):
        A = self.local_vec(ts)
        W = {}
        for b in self.spec['bodies']:
            bid = b['id']
            if bid in ('a', 'q'):
                continue
            p = b['parent']
            W[bid] = A[bid] + (A[p] if p not in (None, 'frame') else 0.0)
        return W

    def world_z(self, t, A=None):
        """World z-angles of all z-axis bodies (children of b / e_table include the carrier)."""
        A = A or self.local(t)
        W = {}
        for b in self.spec['bodies']:
            bid = b['id']
            if bid in ('a', 'q'):
                continue
            p = b['parent']
            W[bid] = A[bid] + (A[p] if p not in (None, 'frame') else 0.0)
        return W


def wrap(a):
    """Wrap to (-pi, pi]."""
    return math.remainder(a, TWO_PI)
