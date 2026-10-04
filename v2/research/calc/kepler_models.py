"""Kepler-motion mechanisms vs exact Kepler: angle and position errors.

Models (all planar, angles from perihelion, distances in units of a):
  kepler  : exact (M = E - e sin E)
  ps(k)   : single pin-and-slot (Antikythera / Hipparchus simple eccentric), ratio k = offset/pin radius
  equant  : Ptolemy bisected eccentricity = two pin-and-slots in cascade (slot drives crank about C, crank pin drives slot about O)
  ward    : uniform rotation about the empty focus, point on the true ellipse (Seth Ward 1653)
"""
import numpy as np

def kepler(M, e):
    E = M.copy()
    for _ in range(60):
        E = E - (E - e*np.sin(E) - M) / (1 - e*np.cos(E))
    nu = 2*np.arctan2(np.sqrt(1+e)*np.sin(E/2), np.sqrt(1-e)*np.cos(E/2))
    r = 1 - e*np.cos(E)
    return nu, r

def ps_angle(M, k):
    return M + np.arctan2(k*np.sin(M), 1 - k*np.cos(M))

def ps_pos(M, k):
    """Pin on a circle of radius 1 about its axis; observer (slot axis) offset k toward perihelion."""
    x = np.cos(M) - k; y = np.sin(M)
    return np.arctan2(y, x), np.hypot(x, y)

def equant(M, e, c=None, q=None):
    """Circle radius 1 centred at C=(-c,0); equant point Q=(-q,0); focus O at origin. Default bisected c=e, q=2e."""
    c = e if c is None else c
    q = 2*e if q is None else q
    ux, uy = np.cos(M), np.sin(M)
    d = q - c                     # |Q - C| (Q further toward aphelion than C)
    # P = Q + t u, |P - C| = 1 ; Q - C = (-d, 0)
    b = -d*ux
    t = -b + np.sqrt(b*b - d*d + 1)
    x = -q + t*ux; y = t*uy
    return np.arctan2(y, x), np.hypot(x, y)

def ward(M, e):
    """Uniform angle M about the empty focus F2=(-2e,0); point on the true ellipse with focus O at origin."""
    # ellipse: |P| + |P - F2| = 2 ; P = F2 + s u
    ux, uy = np.cos(M), np.sin(M)
    # |F2 + s u| = 2 - s  ->  4e^2 - 4 e s ux + s^2 = 4 - 4 s + s^2  -> s (4 - 4 e ux) = 4 - 4 e^2
    s = (1 - e*e) / (1 - e*ux)
    x = -2*e + s*ux; y = s*uy
    return np.arctan2(y, x), np.hypot(x, y)

def wrap(a):
    return (a + np.pi) % (2*np.pi) - np.pi

def pos_err(th1, r1, th2, r2):
    return np.hypot(r1*np.cos(th1) - r2*np.cos(th2), r1*np.sin(th1) - r2*np.sin(th2))

def analyse(e, n=20000):
    M = np.linspace(0, 2*np.pi, n, endpoint=False)
    nu, r = kepler(M, e)
    out = {}
    # single pin-slot, k = 2e
    th = ps_angle(M, 2*e)
    out['ps_2e_angle_deg'] = np.degrees(np.max(np.abs(wrap(th - nu))))
    thp, rp = ps_pos(M, 2*e)
    out['ps_2e_pos_err_a'] = np.max(pos_err(thp, rp, nu, r))
    # single pin-slot, optimal k (minimax angle)
    ks = np.linspace(1.5*e, 2.1*e, 601)
    errs = [np.max(np.abs(wrap(ps_angle(M, k) - nu))) for k in ks]
    i = int(np.argmin(errs))
    out['ps_opt_k_over_e'] = ks[i]/e
    out['ps_opt_angle_deg'] = np.degrees(errs[i])
    # equant (bisected)
    th, rr = equant(M, e)
    out['eq_angle_deg'] = np.degrees(np.max(np.abs(wrap(th - nu))))
    out['eq_pos_err_a'] = np.max(pos_err(th, rr, nu, r))
    out['eq_radial_err_a'] = np.max(np.abs(rr - r))
    # equant angle on a fixed circle about the focus (angle unit + constant-length arm)
    out['const_r_pos_err_a'] = np.max(pos_err(th, np.ones_like(rr), nu, r))
    # Ward (empty focus, true ellipse)
    th, rr = ward(M, e)
    out['ward_angle_deg'] = np.degrees(np.max(np.abs(wrap(th - nu))))
    return out

def series_coeffs(fn, e, harmonics=4, n=4096):
    M = np.linspace(0, 2*np.pi, n, endpoint=False)
    nu, _ = kepler(M, e)
    d = wrap(fn(M) - nu)
    return [2*np.mean(d*np.sin(h*M)) for h in range(1, harmonics+1)]

if __name__ == '__main__':
    # leading error terms vs e (fit on small e)
    for name, fn in [('ps_2e', lambda M, e=None: None)]:
        pass
    for e in [0.01, 0.02, 0.05]:
        c_ps = series_coeffs(lambda M: ps_angle(M, 2*e), e)
        c_eq = series_coeffs(lambda M: equant(M, e)[0], e)
        c_wd = series_coeffs(lambda M: ward(M, e)[0], e)
        print(f"e={e}: PS err/e^2 harmonics", np.round(np.array(c_ps)/e**2, 4),
              "| EQ err/e^3", np.round(np.array(c_eq)/e**3, 4),
              "| WARD err/e^2", np.round(np.array(c_wd)/e**2, 4))
