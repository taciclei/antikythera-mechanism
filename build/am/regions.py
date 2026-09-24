"""Collision pre-filter (spec 5.8): conservative swept regions compared pairwise.
Region types (in some body frame F):
  ('ann', cx, cy, r1, r2, exact)  annulus; exact = it is the true shape (not a swept envelope)
  ('poly', islands)               static polygons (outer CCW + holes CW)
Levers of the followers are swept only over their sector relative to b."""
import math

import numpy as np

TWO_PI = 2.0 * math.pi


# ---------------------------------------------------------------- polygon primitives
def seg_dist(P, A, B):
    """Min distance from points P (N,2) to segments A->B (M,2). Returns (N,)."""
    P = np.asarray(P, float)
    AB = B - A
    L2 = np.einsum('ij,ij->i', AB, AB)
    L2[L2 == 0] = 1e-30
    out = np.full(len(P), np.inf)
    step = max(1, int(2e6 // max(len(A), 1)))
    for s in range(0, len(P), step):
        p = P[s:s + step, None, :]
        t = np.clip(np.einsum('nmk,mk->nm', p - A[None], AB) / L2[None], 0, 1)
        C = A[None] + t[..., None] * AB[None]
        out[s:s + step] = np.sqrt(((p - C) ** 2).sum(-1)).min(1)
    return out


def edges(loop):
    return loop, np.roll(loop, -1, axis=0)


def inside(P, loop):
    """Even-odd point in polygon, vectorised."""
    P = np.atleast_2d(P)
    x, y = P[:, 0][:, None], P[:, 1][:, None]
    A, B = edges(loop)
    xa, ya, xb, yb = A[:, 0][None], A[:, 1][None], B[:, 0][None], B[:, 1][None]
    cond = (ya > y) != (yb > y)
    with np.errstate(divide='ignore', invalid='ignore'):
        xi = xa + (y - ya) * (xb - xa) / (yb - ya)
    return ((cond & (x < xi)).sum(1) % 2) == 1


def segs_intersect(A1, B1, A2, B2):
    """Any proper intersection between segment sets 1 and 2."""
    def orient(a, b, c):
        return (b[..., 0] - a[..., 0]) * (c[..., 1] - a[..., 1]) - (b[..., 1] - a[..., 1]) * (c[..., 0] - a[..., 0])
    step = max(1, int(4e6 // max(len(A2), 1)))
    for s in range(0, len(A1), step):
        a1, b1 = A1[s:s + step, None], B1[s:s + step, None]
        o1 = orient(a1, b1, A2[None])
        o2 = orient(a1, b1, B2[None])
        o3 = orient(A2[None], B2[None], a1)
        o4 = orient(A2[None], B2[None], b1)
        if np.any((o1 * o2 < 0) & (o3 * o4 < 0)):
            return True
    return False


def bbox(loop):
    return loop.min(0), loop.max(0)


def poly_poly(P, Q):
    """Distance between two simple polygons (outer loops, filled). 0 if they overlap."""
    (p0, p1), (q0, q1) = bbox(P), bbox(Q)
    dx = max(q0[0] - p1[0], p0[0] - q1[0], 0.0)
    dy = max(q0[1] - p1[1], p0[1] - q1[1], 0.0)
    if math.hypot(dx, dy) > 0.6:
        return math.hypot(dx, dy)
    if inside(P[:1], Q)[0] or inside(Q[:1], P)[0]:
        return 0.0
    A1, B1 = edges(P)
    A2, B2 = edges(Q)
    if segs_intersect(A1, B1, A2, B2):
        return 0.0
    return float(min(seg_dist(P, A2, B2).min(), seg_dist(Q, A1, B1).min()))


def centroid(loop):
    return loop.mean(0)


def radial_range(reg, p):
    """(rmin, rmax, coax) of the region's material about point p."""
    p = np.asarray(p, float)
    if reg[0] == 'ann':
        _, cx, cy, r1, r2, exact = reg
        d = math.hypot(cx - p[0], cy - p[1])
        if d <= r1:
            return r1 - d, d + r2, (d < 1e-6 and exact)
        if d <= r2:
            return 0.0, d + r2, False
        return d - r2, d + r2, False
    rmin, rmax, coax = math.inf, 0.0, False
    for isl in reg[1]:
        outer = isl[0]
        rmax = max(rmax, float(np.sqrt(((outer - p) ** 2).sum(1)).max()))
        if inside(p[None], outer)[0]:
            hit = None
            for h in isl[1:]:
                if inside(p[None], h)[0]:
                    hit = h
                    break
            if hit is None:
                return 0.0, rmax_all(reg, p), False
            A, B = edges(hit)
            dm = float(seg_dist(p[None], A, B)[0])
            c = np.linalg.norm(centroid(hit) - p) < 1e-6
        else:
            A, B = edges(outer)
            dm = float(seg_dist(p[None], A, B)[0])
            c = False
        if dm < rmin:
            rmin, coax = dm, c
    return rmin, rmax, coax


def rmax_all(reg, p):
    return max(float(np.sqrt(((isl[0] - p) ** 2).sum(1)).max()) for isl in reg[1])


def interval_gap(a1, a2, b1, b2):
    if a2 < b1:
        return b1 - a2
    if b2 < a1:
        return a1 - b2
    return -min(a2 - b1, b2 - a1)


def gap(A, B):
    """Clearance between regions A and B (negative = overlap). Returns (gap, coaxial)."""
    if A[0] == 'poly' and B[0] == 'ann':
        A, B = B, A
    if A[0] == 'ann' and B[0] == 'ann':
        _, ax, ay, a1, a2, ea = A
        _, bx, by, b1, b2, eb = B
        d = math.hypot(ax - bx, ay - by)
        if d < 1e-9:
            return interval_gap(a1, a2, b1, b2), (ea and eb)
        if d >= a2 + b2:
            return d - a2 - b2, False
        if d + b2 <= a1:
            return a1 - d - b2, False
        if d + a2 <= b1:
            return b1 - d - a2, False
        return -(a2 + b2 - d), False
    if A[0] == 'ann':
        _, cx, cy, r1, r2, ex = A
        rmin, rmax, coax = radial_range(B, (cx, cy))
        return interval_gap(rmin, rmax, r1, r2), (coax and ex)
    best = math.inf
    for ia in A[1]:
        for ib in B[1]:
            best = min(best, island_dist(ia, ib))
    return best, False


def island_dist(ia, ib):
    """Distance between two islands (outer + holes); handles one island lying in a hole."""
    d = poly_poly(ia[0], ib[0])
    if d > 0:
        return d
    for P, Q in ((ia, ib), (ib, ia)):
        A1, B1 = edges(P[0])
        for h in Q[1:]:
            if inside(P[0][:1], h)[0]:
                A2, B2 = edges(h)
                if not segs_intersect(A1, B1, A2, B2):
                    return float(min(seg_dist(P[0], A2, B2).min(), seg_dist(h, A1, B1).min()))
    return 0.0


def region_bbox(R):
    if R[0] == 'ann':
        _, cx, cy, _, r2, _ = R
        return np.array([cx - r2, cy - r2]), np.array([cx + r2, cy + r2])
    pts = np.vstack([isl[0] for isl in R[1]])
    return pts.min(0), pts.max(0)


def bbox_gap(R1, R2):
    (a0, a1), (b0, b1) = region_bbox(R1), region_bbox(R2)
    dx = max(b0[0] - a1[0], a0[0] - b1[0], 0.0)
    dy = max(b0[1] - a1[1], a0[1] - b1[1], 0.0)
    return math.hypot(dx, dy)


def rotate_pts(P, a):
    c, s = math.cos(a), math.sin(a)
    return P @ np.array([[c, s], [-s, c]])


# ---------------------------------------------------------------- pre-filter
class Prefilter:
    def __init__(self, spec, cat):
        self.spec = spec
        self.cat = cat
        self.parts = cat.parts
        self.byname = cat.by_name()
        self.parent = {b['id']: b['parent'] for b in spec['bodies']}
        self.axis = {b['id']: tuple(b['axis_xy_in_parent'] or (0.0, 0.0)) for b in spec['bodies']}
        self.cache = {}
        self.intended = {}
        for a, b, why in cat.intended:
            self.intended[frozenset((a, b))] = why

    def chain(self, body):
        c = [body]
        while self.parent.get(c[-1]):
            c.append(self.parent[c[-1]])
        return c

    def foot_region(self, part):
        f = part['foot']
        if 'ann' in f:
            return ('ann',) + tuple(f['ann'])
        return ('poly', f['islands'])

    def sweep(self, reg, body):
        """Region of `reg` (in body frame) swept by the body's rotation, in the parent frame."""
        rmin, rmax, _ = radial_range(reg, (0.0, 0.0))
        exact = reg[0] == 'ann' and reg[5] and math.hypot(reg[1], reg[2]) < 1e-9
        ax, ay = self.axis[body]
        return ('ann', ax, ay, rmin, rmax, exact)

    def region(self, part, F):
        key = (part['name'], F)
        if key in self.cache:
            return self.cache[key]
        X = part['foot_body']
        reg = self.foot_region(part)
        while X != F:
            reg = self.sweep(reg, X)
            X = self.parent[X]
        self.cache[key] = reg
        return reg

    def common(self, a, b):
        ca = self.chain(a)
        cb = set(self.chain(b))
        return next(x for x in ca if x in cb)

    def lever_gap(self, lever, other):
        """Follower lever swept over its sector relative to b, vs a part carried by b."""
        a0, a1 = lever['extra']['lever']
        R = self.region(other, 'b')
        n = int(math.ceil((a1 - a0) / math.radians(0.02))) + 1
        alphas = np.linspace(a0, a1, n)
        margin = lever['extra']['r_max'] * (a1 - a0) / (n - 1)
        LR = ('poly', lever['foot']['islands'])
        if R[0] == 'ann':
            _, cx, cy, r1, r2, ex = R
            best, coax = math.inf, False
            # centre expressed in the lever frame for each sample angle
            c, s = np.cos(alphas), np.sin(alphas)
            px, py = c * cx + s * cy, -s * cx + c * cy
            # coarse pass: bbox of the lever polygon
            for x, y in zip(px, py):
                rmin, rmax, cx_ = radial_range(LR, (x, y))
                g = interval_gap(rmin, rmax, r1, r2)
                if g < best:
                    best, coax = g, cx_ and ex
            return best - margin, coax
        best = math.inf
        for a in alphas[::max(1, len(alphas) // 400)]:
            P = rotate_pts(lever['foot']['islands'][0][0], a)
            for isl in R[1]:
                best = min(best, poly_poly(P, isl[0]))
        return best - margin - lever['extra']['r_max'] * math.radians(0.02) * max(1, len(alphas) // 400), False

    def pair_gap(self, A, B):
        """(gap, coaxial, frame) for two parts of different bodies."""
        for L, O in ((A, B), (B, A)):
            if 'lever' in L['extra'] and 'b' in self.chain(O['foot_body']) and O['foot_body'] != 'frame':
                if O['foot_body'] == 'b' and self.foot_region(O)[0] == 'ann' and \
                        math.hypot(*self.foot_region(O)[1:3]) < 1e-9:
                    break      # coaxial tube of b: plain radial comparison in the frame
                g, c = self.lever_gap(L, O)
                return g, c, 'b-sector'
        F = self.common(A['foot_body'], B['foot_body'])
        RA, RB = self.region(A, F), self.region(B, F)
        bg = bbox_gap(RA, RB)
        if bg >= 0.6:
            return bg, False, F
        g, c = gap(RA, RB)
        return g, c, F

    def run(self, retain_gap=0.5, retain_dz=0.1):
        parts = [p for p in self.parts if p['kind'] != 'text']
        conflicts, intended, retained = [], [], []
        n_pairs = 0
        for i in range(len(parts)):
            A = parts[i]
            for j in range(i + 1, len(parts)):
                B = parts[j]
                if A['body'] == B['body']:
                    continue
                dz = max(B['fz'][0] - A['fz'][1], A['fz'][0] - B['fz'][1])
                if dz > retain_dz + 1e-9:
                    continue
                overlap_z = dz < -1e-9
                g, coax, F = self.pair_gap(A, B)
                n_pairs += overlap_z
                why = self.intended.get(frozenset((A['name'], B['name'])))
                need = 0.04 if coax else 0.15
                rec = {'a': A['name'], 'b': B['name'], 'gap': round(float(g), 5), 'coaxial': coax,
                       'frame': F, 'dz': round(float(dz), 5)}
                if why:
                    rec['why'] = why
                    intended.append(rec)
                elif overlap_z and g < need - 1e-9:
                    conflicts.append(rec)
                if g < retain_gap:
                    retained.append(rec)
        return {'n_pairs_z_overlap': n_pairs, 'conflicts': conflicts, 'intended': intended,
                'retained': retained}
