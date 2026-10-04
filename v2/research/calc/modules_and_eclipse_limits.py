"""Sizing of the per-planet 'vector modules' and eclipse-limit numbers for the dials."""
import json
import numpy as np
from geocentric import EL
P = np.pi/180
res = json.load(open('geocentric_results.json'))
dist = res['earth_planet_distance_AU']
plan = {'mercury': ('inner', 60, 'kes'), 'venus': ('inner', 70, 'eq'), 'mars': ('outer', 70, 'eqe'),
        'jupiter': ('outer', 50, 'eq'), 'saturn': ('outer', 50, 'eq'), 'uranus': ('outer', 50, 'eq'), 'neptune': ('outer', 50, 'eq')}
aE, eE = EL['earth'][0][0], EL['earth'][0][1]
mods = {}
for p, (nest, R, kmodel) in plan.items():
    a, e = EL[p][0][0], EL[p][0][1]
    dmin, dmax = dist[p]
    s = R/dmax
    m = {'nesting': nest, 'module_radius_mm': R, 'scale_mm_per_AU': round(s, 2), 'kepler_unit': kmodel,
         'planet_arm_mm': round(a*s, 2), 'sun_arm_mm': round(aE*s, 2),
         'planet_centre_offset_mm': round(a*e*s, 3), 'earth_centre_offset_mm': round(aE*eE*s, 3),
         'G_min_mm': round(dmin*s, 1), 'G_max_mm': round(dmax*s, 1),
         'follower_err_deg_for_0.02mm': round(np.degrees(0.02/(dmin*s)), 3)}
    if kmodel == 'eqe':
        m['epicyclet_mm'] = round(a*e*e/4*s, 3)
    if kmodel == 'kes':
        b = a*np.sqrt(1 - e*e)
        m['ellipse_arms_mm'] = [round((a + b)/2*s, 3), round((a - b)/2*s, 3)]
        m['ellipse_centre_offset_mm'] = round(a*e*s, 3)
    mods[p] = m
    print(p, m)
# eclipse limits (geocentric), Meeus ch.54 thresholds with mean u = 0.0059
u = 0.0059
lims = {}
for name, g in [('solar_any (|gamma| < 1.5433+u)', 1.5433 + u), ('solar_central (|gamma| < 0.9972)', 0.9972),
                ('lunar_penumbral (|gamma| < 1.5573+u)', 1.5573 + u), ('lunar_partial_umbral (|gamma| < 1.0128-u)', 1.0128 - u),
                ('lunar_total (|gamma| < 0.4678-u)', 0.4678 - u)]:
    row = {}
    for lab, par in (('apogee', 54.0/60), ('perigee', 61.4/60)):
        beta = np.degrees(np.arcsin(g*np.sin(par*P)/np.cos(5.3*P)))
        F = np.degrees(np.arcsin(np.sin(beta*P)/np.sin(5.0*P)))
        row[lab] = {'beta_deg': round(beta, 3), 'F_deg': round(F, 2)}
    lims[name] = row
    print(name, row)
syn, drac, anom = 29.530588853, 27.212220817, 27.554549878
saros = {'223_synodic_d': 223*syn, '242_draconic_d': 242*drac, '239_anomalistic_d': 239*anom,
         'node_shift_per_saros_deg': (242*drac - 223*syn)/drac*360,
         'anomaly_shift_per_saros_deg': (239*anom - 223*syn)/anom*360,
         'longitude_shift_per_saros_deg': -(223*syn % 1)*360,
         'exeligmos_extra_days': 3*223*syn - round(3*223*syn)}
print(saros)
json.dump({'modules': mods, 'eclipse_limits': lims, 'saros': saros}, open('modules_results.json', 'w'), indent=1)
