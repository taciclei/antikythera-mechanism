"""Envelope-generated crown (contrate) teeth for a1 (vs b1) and q1 (vs b0).

Crown frame: s along the crown axis (a1: world x; q1: Moon-frame u), rho = distance from the crown axis,
phi measured from the direction toward the spur mid-plane (-z) toward +y (a1) / +v (q1).
Crown-frame point -> spur frame: (s, rho*sin(phi+alpha), z_axis - rho*cos(phi+alpha)), spur rotated by alpha*z_cr/z_sp.
A crown tooth is the set of points never inside the spur's teeth (thickened by `clearance` per flank) for any alpha.
Output: structured grid for tooth 0 (centred near pi/z_cr): rho columns j, s rows i from a per-column tip s_tip(rho_j)
to the root; at each node the allowed [phi_lo, phi_hi] shrunk by a flank margin. Every cell interior is verified.
"""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parent.parent)   # repository root
import json, math, sys
import numpy as np

AL = math.radians(30.0)
def inv(a): return np.tan(a) - a

class Pair:
    def __init__(s, z_sp, m, z_cr, z_axis, spur_z, clearance, j_sp, alpha_range_deg, n_phi=801, d_alpha_deg=0.05, keep_frac=0.45):
        s.z_sp, s.m, s.z_cr, s.z_axis, s.spur_z = z_sp, m, z_cr, z_axis, spur_z
        s.rp = m*z_sp/2; s.ra = s.rp + m; s.rf = s.rp - 1.25*m; s.rb = s.rp*math.cos(AL)
        s.clear, s.j = clearance, j_sp
        s.ratio = z_cr/z_sp; s.pitch_sp = 2*math.pi/z_sp; s.pitch_cr = 2*math.pi/z_cr
        s.phi_c = math.pi/z_cr
        s.phis = np.linspace(s.phi_c - keep_frac*s.pitch_cr, s.phi_c + keep_frac*s.pitch_cr, n_phi)
        s.alphas = np.radians(np.arange(-alpha_range_deg, alpha_range_deg + 1e-9, d_alpha_deg))
    def psi(s, r):
        return math.pi/(2*s.z_sp) + inv(AL) - inv(np.arccos(np.clip(s.rb/r, -1, 1))) - s.j/(4*s.rp) + s.clear/r
    def forbidden(s, sx, rho, phis=None):
        phis = s.phis if phis is None else phis
        forb = np.zeros(len(phis), dtype=bool)
        for a0 in range(0, len(s.alphas), 400):
            A = s.alphas[a0:a0+400][:, None]
            om = phis[None, :] + A
            y = rho*np.sin(om); zz = s.z_axis - rho*np.cos(om)
            inz = (zz >= s.spur_z[0] - 0.02) & (zz <= s.spur_z[1] + 0.02)
            th = A*s.ratio
            xb = sx*np.cos(th) + y*np.sin(th); yb = -sx*np.sin(th) + y*np.cos(th)
            r = np.hypot(xb, yb); ang = np.arctan2(yb, xb)
            d = ang - np.round(ang/s.pitch_sp)*s.pitch_sp
            psi = s.psi(np.clip(r, s.rf, s.ra))
            forb |= (inz & ((r < s.rf) | ((r <= s.ra) & (np.abs(d) <= psi)))).any(axis=0)
        return forb
    def interval(s, sx, rho):
        forb = s.forbidden(sx, rho); k = np.argmin(np.abs(s.phis - s.phi_c))
        if forb[k]: return None
        a = k
        while a > 0 and not forb[a-1]: a -= 1
        b = k
        while b < len(forb)-1 and not forb[b+1]: b += 1
        return s.phis[a], s.phis[b]

def design(name, pair, s_tip_nom, s_root, band, n_rho=14, n_s=12, min_width=None, margin=0.01, ds=0.025):
    R = np.linspace(band[0], band[1], n_rho)
    # 1. deepest usable tip per column (width >= min_width + 2*margin)
    tips = []
    for rho in R:
        sx = s_tip_nom
        while True:
            iv = pair.interval(sx, rho)
            if iv is not None and (iv[1] - iv[0])*rho >= min_width + 2*margin: break
            sx += ds
            if sx > s_root: raise SystemExit(f"{name}: no tooth at rho {rho}")
        tips.append(sx)
    tips = np.array(tips)
    tips = np.maximum(tips, np.maximum(np.r_[tips[1:], tips[-1]], np.r_[tips[0], tips[:-1]]))   # conservative in between
    S = np.array([[t + (s_root - t)*i/(n_s-1) for t in tips] for i in range(n_s)])            # S[i, j]
    L = np.zeros_like(S); H = np.zeros_like(S)
    for i in range(n_s):
        for j in range(n_rho):
            lo, hi = pair.interval(S[i, j], R[j])
            L[i, j] = lo + margin/R[j]; H[i, j] = hi - margin/R[j]
    # 2. verify cell interiors (bilinear interpolation of s and phi bounds), shrink nodes until clean
    for it in range(8):
        bad = 0
        for i in range(n_s-1):
            for j in range(n_rho-1):
                for (u, v) in ((0.5, 0.5), (0.5, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 0.5), (0.25, 0.25), (0.75, 0.75), (0.25, 0.75), (0.75, 0.25)):
                    def bil(Mx): return (Mx[i, j]*(1-u)*(1-v) + Mx[i+1, j]*u*(1-v) + Mx[i, j+1]*(1-u)*v + Mx[i+1, j+1]*u*v)
                    sx, rho, lo, hi = bil(S), R[j]*(1-v) + R[j+1]*v, bil(L), bil(H)
                    f = pair.forbidden(sx, rho, np.linspace(lo, hi, 60))
                    if f.any():
                        bad += 1
                        for (a, b) in ((i, j), (i+1, j), (i, j+1), (i+1, j+1)):
                            L[a, b] += 0.004/R[b]; H[a, b] -= 0.004/R[b]
        if bad == 0: break
        print(f"  {name}: pass {it}: {bad} interior samples touched the spur; nodes shrunk")
    if bad: raise SystemExit(f"{name}: could not clean interior")
    w = (H - L)*R[None, :]
    print(f"{name}: tips s = {tips.min():.4f}..{tips.max():.4f} (nominal {s_tip_nom:.4f}), min width {w.min():.4f} mm, "
          f"phi {math.degrees(L.min()):.3f}..{math.degrees(H.max()):.3f} deg")
    return dict(tooth0_centre_rad=round(pair.phi_c, 9), rho_levels=[round(float(x), 6) for x in R],
                s_grid=[[round(float(x), 6) for x in row] for row in S],
                phi_lo_rad=[[round(float(x), 7) for x in row] for row in L], phi_hi_rad=[[round(float(x), 7) for x in row] for row in H],
                tip_s_min=round(float(tips.min()), 5), tip_s_max=round(float(tips.max()), 5))

if __name__ == '__main__':
    m1 = 0.5776; rp_a1 = m1*48/2; rp_b1 = m1*223/2
    a1 = design('a1', Pair(223, m1, 48, 5.30 + rp_a1, (3.95, 6.65), 0.04, 0.03, 32.0),
                s_tip_nom=rp_b1 - m1, s_root=rp_b1 + 1.25*m1 + 0.05, band=(rp_a1 - 0.6, rp_a1 + 0.7), min_width=0.2*m1)
    q1 = design('q1', Pair(20, 0.5, 20, 47.70 + 5.0, (47.20, 48.20), 0.04, 0.03, 70.0),
                s_tip_nom=5.0 - 0.5, s_root=5.0 + 1.25*0.5 + 0.05, band=(4.55, 5.45), min_width=0.2*0.5)
    out = sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/tools/crown_envelopes.json'
    json.dump({'a1': a1, 'q1': q1}, open(out, 'w'))
    print("written", out)
