"""Heliocentric Kepler mechanisms -> geocentric ecliptic longitudes: error budget per planet.

Reference: JPL 'Approximate Positions of the Planets', Table 1 (Standish & Williams; 1800-2050 fit),
3D Kepler with secular rates. Mechanisms are PLANAR, with eccentricities and apsidal lines frozen at the
mid-epoch T_MID (eccentric pivots fixed in a frame that does not precess = J2000 frame), and use the SAME
mean longitudes as the reference (gear-ratio errors are budgeted separately).
Components: model (geometry of the mechanism), inclination (planar projection), secular (frozen e, varpi),
and the total. Window 2000-2100, 6-hour step.
"""
import json
import numpy as np
from kepler_models import kepler, equant, ps_angle, wrap

D2R = np.pi/180
EL = {  # a, e, I, L, varpi, Omega ; rates per Julian century (JPL Table 1)
 'mercury': ([0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593],
             [0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081]),
 'venus':   ([0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255],
             [0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418]),
 'earth':   ([1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0],
             [0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0]),
 'mars':    ([1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891],
             [0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343]),
 'jupiter': ([5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909],
             [-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106]),
 'saturn':  ([9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448],
             [-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794]),
 'uranus':  ([19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503],
             [-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589]),
 'neptune': ([30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574],
             [0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664]),
}
PLANETS = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']
# JPL nominal heliocentric-longitude error of these Kepler elements vs DE ephemeris, 1800-2050 (arcsec)
JPL_LON_ERR_ARCSEC = {'mercury': 15, 'venus': 20, 'earth': 20, 'mars': 40, 'jupiter': 400, 'saturn': 600, 'uranus': 50, 'neptune': 10}
T_MID = 0.5   # 2050.0

def elements(name, T, frozen):
    e0, r = EL[name]
    el = [x + dx*T for x, dx in zip(e0, r)]
    if frozen:   # keep the moving mean longitude, freeze a, e, I, varpi, Omega at T_MID
        el = [x + dx*T_MID for x, dx in zip(e0, r)]
        el[3] = e0[3] + r[3]*T
    return el

def rel_vec(name, T, model, frozen=True, planar=True):
    """Heliocentric position (x, y) in AU, ecliptic J2000."""
    a, e, I, L, w, O = elements(name, T, frozen)
    M = wrap((L - w)*D2R)
    if not planar:
        nu, rr = kepler(M, e)
        u = (w - O)*D2R + nu; r = a*rr; Ir, Or = I*D2R, O*D2R
        return (r*(np.cos(Or)*np.cos(u) - np.sin(Or)*np.sin(u)*np.cos(Ir)),
                r*(np.sin(Or)*np.cos(u) + np.cos(Or)*np.sin(u)*np.cos(Ir)))
    if model == 'kes':                       # exact Kepler (mechanical Kepler-equation solver)
        th, rr = kepler(M, e); z = rr*np.exp(1j*th)
    elif model == 'eq':                      # bisected equant = two pin-and-slots in cascade
        th, rr = equant(M, e); z = rr*np.exp(1j*th)
    elif model == 'eqe':                     # equant, crank shortened by e^2/4, epicyclet e^2/4 at absolute 3M
        th, rr = equant(M, e); z = rr*np.exp(1j*th)
        phiC = np.angle(z + e)
        z = z - (e*e/4)*np.exp(1j*phiC) + (e*e/4)*np.exp(3j*M)
    elif model == 'ps':                      # Antikythera pin-and-slot k=2e, arm of constant length
        z = np.exp(1j*ps_angle(M, 2*e))
    elif model == 'circle':
        z = np.exp(1j*M)
    else:
        raise ValueError(model)
    z = a*z*np.exp(1j*w*D2R)
    return z.real, z.imag

def lon(x, y):
    return np.arctan2(y, x)

def maxdeg(a):
    return float(np.degrees(np.max(np.abs(wrap(a)))))

def budget(T, model, earth_model='eq', earth_const=False):
    out = {}
    xE_ref, yE_ref = rel_vec('earth', T, None, frozen=False, planar=False)
    xE_3f, yE_3f = rel_vec('earth', T, None, frozen=True, planar=False)
    xE_pk, yE_pk = rel_vec('earth', T, 'kes', frozen=True)
    xE_m, yE_m = rel_vec('earth', T, earth_model, frozen=True)
    if earth_const:
        g = np.arctan2(yE_m, xE_m); xE_m, yE_m = np.cos(g), np.sin(g)
    for p in PLANETS:
        xr, yr = rel_vec(p, T, None, frozen=False, planar=False)     # reference
        x3, y3 = rel_vec(p, T, None, frozen=True, planar=False)      # frozen elements, 3D
        xk, yk = rel_vec(p, T, 'kes', frozen=True)                    # frozen, planar exact
        xm, ym = rel_vec(p, T, model, frozen=True)                    # mechanism
        geo = lambda x, y, xe, ye: lon(x - xe, y - ye)
        out[p] = {
            'helio_model': maxdeg(lon(xm, ym) - lon(xk, yk)),
            'geo_model': maxdeg(geo(xm, ym, xE_m, yE_m) - geo(xk, yk, xE_pk, yE_pk)),
            'geo_inclination': maxdeg(geo(xk, yk, xE_pk, yE_pk) - geo(x3, y3, xE_3f, yE_3f)),
            'geo_secular': maxdeg(geo(x3, y3, xE_3f, yE_3f) - geo(xr, yr, xE_ref, yE_ref)),
            'helio_total': maxdeg(lon(xm, ym) - lon(xr, yr)),
            'geo_total': maxdeg(geo(xm, ym, xE_m, yE_m) - geo(xr, yr, xE_ref, yE_ref)),
        }
    return out

def compression(T):
    """Sighting arm pivoted on the orrery's Earth when orbit radii are NOT in true ratio (circular orbits)."""
    schemes = {
        'equal_spacing_20mm': {'mercury': 30, 'venus': 50, 'earth': 70, 'mars': 90, 'jupiter': 110, 'saturn': 130, 'uranus': 150, 'neptune': 170},
        'sqrt': {p: 60*np.sqrt(EL[p][0][0]) for p in ['earth'] + PLANETS},
        'log': {p: 70 + 40*np.log(EL[p][0][0]) for p in ['earth'] + PLANETS},
    }
    out = {}
    LE = (EL['earth'][0][3] + EL['earth'][1][3]*T)*D2R
    for name, R in schemes.items():
        out[name] = {'earth_r_mm': round(float(R['earth']), 1)}
        for p in PLANETS:
            Lp = (EL[p][0][3] + EL[p][1][3]*T)*D2R
            ap = EL[p][0][0]
            true = lon(ap*np.cos(Lp) - np.cos(LE), ap*np.sin(Lp) - np.sin(LE))
            comp = lon(R[p]*np.cos(Lp) - R['earth']*np.cos(LE), R[p]*np.sin(Lp) - R['earth']*np.sin(LE))
            out[name][p] = {'r_mm': round(float(R[p]), 1), 'max_err_deg': round(maxdeg(comp - true), 2)}
    return out

def distances(T):
    xE, yE = rel_vec('earth', T, None, frozen=False, planar=False)
    out = {}
    for p in PLANETS:
        x, y = rel_vec(p, T, None, frozen=False, planar=False)
        d = np.hypot(x - xE, y - yE)
        out[p] = (float(d.min()), float(d.max()))
    return out

def geo_minus_helio(T):
    out = {}
    xE, yE = rel_vec('earth', T, None, frozen=False, planar=False)
    for p in PLANETS:
        x, y = rel_vec(p, T, None, frozen=False, planar=False)
        out[p] = maxdeg(lon(x - xE, y - yE) - lon(x, y))
    return out

if __name__ == '__main__':
    T = np.arange(0, 100*365.25, 0.25)/36525.0
    res = {}
    for label, model, em, ec in [('circle', 'circle', 'circle', False), ('ps', 'ps', 'ps', False),
                                 ('eq', 'eq', 'eq', False), ('eqe', 'eqe', 'eqe', False), ('kes', 'kes', 'kes', False),
                                 ('eqe_earth_const_radius', 'eqe', 'eqe', True)]:
        res[label] = budget(T, model, em, ec)
        print(f"\n== {label}: helio_model / geo_model / geo_incl / geo_secular / helio_total / GEO_TOTAL (deg)")
        for p, d in res[label].items():
            print(f"  {p:8s} {d['helio_model']:7.3f} {d['geo_model']:7.3f} {d['geo_inclination']:7.3f} {d['geo_secular']:7.3f} {d['helio_total']:7.3f} {d['geo_total']:7.3f}")
    comp = compression(T)
    print('\ncompressed orrery + sighting arm (max geocentric error, deg):')
    for s, d in comp.items():
        print(' ', s, {k: v for k, v in d.items()})
    dist = distances(T); gmh = geo_minus_helio(T)
    print('\nEarth-planet distance min/max (AU):', {p: (round(a, 3), round(b, 3)) for p, (a, b) in dist.items()})
    print('max |geo - helio| (deg):', {p: round(v, 2) for p, v in gmh.items()})
    # mechanical tolerance: follower angle error = delta / |G|min ; module scale s chosen so that Delta_max*s = R_mod
    tol = {}
    for R_mod in (40.0, 60.0):
        for delta in (0.02, 0.05):
            tol[f'R{int(R_mod)}_d{delta}'] = {p: round(float(np.degrees(delta/(dist[p][0]*R_mod/dist[p][1]))), 3) for p in PLANETS}
    print('follower angle error from pin/slot position error delta (deg), module radius R:', tol)
    json.dump({'budget': res, 'compression': comp, 'earth_planet_distance_AU': dist, 'geo_minus_helio_max_deg': gmh,
               'tolerance_follower_deg': tol, 'jpl_table1_lon_err_arcsec_1800_2050': JPL_LON_ERR_ARCSEC},
              open('geocentric_results.json', 'w'), indent=1)
