"""2D interference of every external mesh over one tooth pitch (spec 5.8)."""
import math

import numpy as np

from .involute import Involute
from .regions import seg_dist


def _place(loop, ang, c):
    ca, sa = math.cos(ang), math.sin(ang)
    return loop @ np.array([[ca, sa], [-sa, ca]]) + np.asarray(c)


def check_mesh(spec, laws, phases, mesh, j=0.03, n_pos=50, n_flank=24, scale=1.0):
    g1, g2 = spec.gears[mesh['driver']], spec.gears[mesh['driven']]
    z1, z2 = g1['teeth'], g2['teeth']
    m = g1['module'] * scale
    G1 = Involute(z1, g1['module'] * scale, j=j)
    G2 = Involute(z2, g2['module'] * scale, j=j)
    o1, o2 = G1.outline(0.0, n_flank), G2.outline(0.0, n_flank)
    C = mesh['carrier']
    W0 = laws.world_z(0.0)
    wc = W0[C] if C != 'frame' else 0.0
    t1 = W0[g1['body']] - wc + phases.get(mesh['driver'], 0.0)
    t2 = W0[g2['body']] - wc + phases.get(mesh['driven'], 0.0)
    c1 = np.array(spec.axis_world(g1['body'])) * scale
    c2 = np.array(spec.axis_world(g2['body'])) * scale
    a = float(np.linalg.norm(c2 - c1))
    u = (c2 - c1) / a
    P = c1 + u * G1.r
    min_signed, gaps_near, min_all = math.inf, [], math.inf
    for k in range(n_pos):
        d1 = 2 * math.pi / z1 * k / n_pos
        A = _place(o1, t1 + d1, c1)
        B = _place(o2, t2 - d1 * z1 / z2, c2)
        selA = np.linalg.norm(A - c2, axis=1) <= G2.ra + 0.2
        selB = np.linalg.norm(B - c1, axis=1) <= G1.ra + 0.2
        ia = np.where(selA)[0]
        ib = np.where(selB)[0]
        # segments adjacent to the selected vertices
        sa_ = np.unique(np.concatenate([ia, ia - 1]) % len(A))
        sb_ = np.unique(np.concatenate([ib, ib - 1]) % len(B))
        A0, A1 = A[sa_], A[(sa_ + 1) % len(A)]
        B0, B1 = B[sb_], B[(sb_ + 1) % len(B)]
        dB = seg_dist(B[ib], A0, A1)
        dA = seg_dist(A[ia], B0, B1)
        # analytic inside tests (points of one gear inside the other's material)
        rel_b = _place(B[ib] - c1, -(t1 + d1), (0, 0))
        rel_a = _place(A[ia] - c2, -(t2 - d1 * z1 / z2), (0, 0))
        in_b = G1.inside(rel_b)
        in_a = G2.inside(rel_a)
        sdB = np.where(in_b, -dB, dB)
        sdA = np.where(in_a, -dA, dA)
        min_signed = min(min_signed, float(sdB.min()), float(sdA.min()))
        min_all = min(min_all, float(min(dB.min(), dA.min())))
        nearB = np.linalg.norm(B[ib] - P, axis=1) <= 2 * m
        nearA = np.linalg.norm(A[ia] - P, axis=1) <= 2 * m
        cand = np.concatenate([dB[nearB], dA[nearA]])
        if len(cand):
            gaps_near.append(float(cand.min()))
    gmin = min(gaps_near) if gaps_near else math.nan
    gmax = max(gaps_near) if gaps_near else math.nan
    ok = min_signed >= 0 and 0.4 * j - 1e-9 <= gmin and gmax <= 3 * j + 1e-9
    return {'mesh': '%s~%s' % (mesh['driver'], mesh['driven']), 'min_signed': min_signed,
            'backlash_near_min': gmin, 'backlash_near_max': gmax, 'min_clearance': min_all,
            'positions': n_pos, 'j': j, 'ok': bool(ok)}


def check_all(spec, laws, phases, j=0.03, n_pos=50, n_flank=24, scale=1.0):
    return [check_mesh(spec, laws, phases, m, j, n_pos, n_flank, scale) for m in spec.external_meshes]
