"""Back-dial two-centre spirals (Anastasiou et al. 2014), grooves, cell marks and psi->rho table.
Back view (u, v) = (-x, y); psi clockwise seen from the back from +v; world dir = (-sin, cos)."""
import math

import numpy as np

from .involute import dedupe
from .outline import ccw, cw

TWO_PI = 2.0 * math.pi


def rho(psi, r_start, pitch):
    psi = np.asarray(psi, float)
    k = np.floor(psi / TWO_PI)
    phi = psi - TWO_PI * k
    Rk = r_start + k * pitch
    d = pitch / 2
    second = d * np.cos(phi) + np.sqrt((Rk + d) ** 2 - d * d * np.sin(phi) ** 2)
    return np.where(phi < math.pi, Rk, second)


def arc_centre(psi, pitch):
    """Centre (u, v) of the circular arc the spiral follows at psi."""
    phi = np.mod(psi, TWO_PI)
    return np.where(phi[..., None] < math.pi, np.array([0.0, 0.0]), np.array([0.0, pitch / 2]))


def point_uv(psi, r_start, pitch):
    psi = np.asarray(psi, float)
    r = rho(psi, r_start, pitch)
    return np.stack([r * np.sin(psi), r * np.cos(psi)], axis=-1)


def uv_to_xy(p, centre):
    p = np.asarray(p, float)
    return np.stack([centre[0] - p[..., 0], centre[1] + p[..., 1]], axis=-1)


def dial(spec, which):
    d = spec.dials['back'][which]
    c = spec['axes_world_xy'][d['centre']]
    return d, (float(c[0]), float(c[1]))


def groove_loop(centre, r_start, pitch, turns, hw, step=math.radians(0.5)):
    """Groove (spiral offset by +-hw, round ends of radius hw) as a CW world-xy loop."""
    end = turns * TWO_PI
    n = int(math.ceil(end / step))
    psi = np.linspace(0.0, end, n + 1)
    # nudge exact multiples of pi so the arc-centre choice is unambiguous
    S = point_uv(psi, r_start, pitch)
    C = arc_centre(psi - 1e-12 * (psi > 0), pitch)
    nrm = S - C
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    outer = S + hw * nrm
    inner = S - hw * nrm

    def cap(Sp, a_pt, b_pt, towards):
        a0 = math.atan2(a_pt[1] - Sp[1], a_pt[0] - Sp[0])
        a1 = math.atan2(b_pt[1] - Sp[1], b_pt[0] - Sp[0])
        at = math.atan2(towards[1], towards[0])
        # choose the direction (ccw or cw) whose sweep passes through `at`
        dccw = (a1 - a0) % TWO_PI
        if (at - a0) % TWO_PI <= dccw:
            angs = a0 + np.linspace(0, dccw, 13)
        else:
            angs = a0 - np.linspace(0, TWO_PI - dccw, 13)
        return np.stack([Sp[0] + hw * np.cos(angs), Sp[1] + hw * np.sin(angs)], axis=1)[1:-1]

    t_end = S[-1] - S[-2]
    t_start = S[0] - S[1]
    pts = np.vstack([outer, cap(S[-1], outer[-1], inner[-1], t_end), inner[::-1],
                     cap(S[0], inner[0], outer[0], t_start)])
    return cw(dedupe(uv_to_xy(pts, centre)))


def spiral_band_loop(centre, r_start, pitch, turns, hw, step=math.radians(0.5)):
    """Same as the groove but CCW (swept region of the slider pin, used by the pre-filter)."""
    return ccw(groove_loop(centre, r_start, pitch, turns, hw, step))


def cell_marks(centre, r_start, pitch, turns, cells, groove_hw, width=0.3, margin=0.3, r_max=71.0):
    """Radial marks at the cell boundaries between successive turns (world xy CCW loops)."""
    out = []
    end = turns * TWO_PI
    for jj in range(cells + 1):
        psi = end * jj / cells
        ra = float(rho(psi, r_start, pitch)) + groove_hw + margin
        if psi + TWO_PI <= end + 1e-9:
            rb = float(rho(psi + TWO_PI, r_start, pitch)) - groove_hw - margin
        else:
            rb = r_max
        rb = min(rb, r_max)
        if rb - ra < 0.5:
            continue
        d = np.array([-math.sin(psi), math.cos(psi)])
        p = np.array([math.cos(psi), math.sin(psi)])
        c = np.array(centre)
        q = np.array([c + ra * d - width / 2 * p, c + ra * d + width / 2 * p,
                      c + rb * d + width / 2 * p, c + rb * d - width / 2 * p])
        out.append(ccw(q))
    return out


def lookup(r_start, pitch, turns, per_pi):
    """Table psi -> rho with keys at every pi/per_pi (breakpoints at multiples of pi are keys)."""
    n = int(turns * 2 * per_pi)
    psi = np.linspace(0.0, turns * TWO_PI, n + 1)
    return psi, rho(psi, r_start, pitch)
