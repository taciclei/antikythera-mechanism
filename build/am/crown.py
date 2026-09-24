"""Crown (contrate) teeth of a1 and q1 built from the pre-computed envelope grids of the spec."""
import math

import numpy as np

TWO_PI = 2.0 * math.pi


def tooth_grid(env, shrink=0.0):
    s = np.array(env['s_grid'], float)
    rho = np.array(env['rho_levels'], float)
    lo = np.array(env['phi_lo_rad'], float)
    hi = np.array(env['phi_hi_rad'], float)
    if shrink:
        lo = lo + shrink / rho[None, :]
        hi = hi - shrink / rho[None, :]
    return s, rho, lo, hi


def tooth_faces(I, J):
    """Quad faces (index tuples) of one tooth; L(i,j) = i*J + j, H(i,j) = I*J + i*J + j.
    I, J = number of rows/columns."""
    L = lambda i, j: i * J + j  # noqa: E731
    H = lambda i, j: I * J + i * J + j  # noqa: E731
    q = []
    for i in range(I - 1):
        for j in range(J - 1):
            q.append((L(i, j), L(i, j + 1), L(i + 1, j + 1), L(i + 1, j)))
            q.append((H(i, j), H(i + 1, j), H(i + 1, j + 1), H(i, j + 1)))
    for i in range(I - 1):
        q.append((L(i, 0), L(i + 1, 0), H(i + 1, 0), H(i, 0)))
        q.append((L(i, J - 1), H(i, J - 1), H(i + 1, J - 1), L(i + 1, J - 1)))
    for j in range(J - 1):
        q.append((L(0, j), H(0, j), H(0, j + 1), L(0, j + 1)))
        q.append((L(I - 1, j), L(I - 1, j + 1), H(I - 1, j + 1), H(I - 1, j)))
    return q


def crown_teeth(spec, which, shrink=0.0, scale=1.0):
    """All teeth of crown `which` ('a1' or 'q1') in the crown frame (s, y, z - axis_z).
    Returns (verts (N,3), tris (M,3), n_shells, verts_per_tooth)."""
    c = spec.crowns[which]
    env = c['envelope']
    s, rho, lo, hi = tooth_grid(env, shrink / scale if scale else shrink)
    I, J = s.shape
    z = c['teeth']
    quads = tooth_faces(I, J)
    tris1 = []
    for a, b, cc, d in quads:
        tris1.append((a, b, cc))
        tris1.append((a, cc, d))
    tris1 = np.array(tris1, np.int64)
    nv = 2 * I * J
    V, T = [], []
    for k in range(z):
        dk = k * TWO_PI / z
        pts = []
        for phi in (lo + dk, hi + dk):
            x = s
            y = rho[None, :] * np.sin(phi)
            zz = -rho[None, :] * np.cos(phi)
            pts.append(np.stack([x, y, zz], axis=-1).reshape(-1, 3))
        V.append(np.vstack(pts) * scale)
        T.append(tris1 + k * nv)
    return np.vstack(V), np.vstack(T), z, nv


def mesh_volume(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    return float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0)
