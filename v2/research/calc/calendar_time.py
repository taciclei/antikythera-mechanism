"""Calendar & time subsystem checks: Gregorian program wheels, sidereal time, equation of time (Hooke joint),
precession train, and Galilean-moon trains (Laplace-exact architecture)."""
import json
import numpy as np
from gear_search import best_trains
from kepler_models import equant, kepler, wrap

P = np.pi/180
out = {}

# ---------------------------------------------------------------- 1. Gregorian leap-year logic by program wheels
def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

READ = 59/366          # the Feb-28 -> Mar-1 step happens at ring position 58->59 (of 366)
def cams(Y, Y0=2000):
    """Continuous wheels geared from the 366-step year ring (1 rev / calendar year), epoch Jan 1 Y0."""
    years = (Y - Y0) + READ
    w4 = (years/4) % 1.0            # 1:4
    w100 = (years/100) % 1.0        # 1:25 after w4
    w400 = (years/400) % 1.0        # 1:4 after w100
    # cam sectors centred on the reading instants (edges half-way between readings)
    def raised(w, period, which):   # 'which' = set of residues (years mod period) for which the cam is raised
        k = np.floor(w*period + 0.5 - READ) % period   # nearest year index
        margin = abs(((w*period - READ + 0.5) % 1.0) - 0.5)/period*360   # degrees from the sector centre
        return (k in which), margin
    c4, m4 = raised(w4, 4, {1, 2, 3})
    c100, m100 = raised(w100, 100, {0})
    c400, m400 = raised(w400, 400, {100, 200, 300})
    # 400-yr wheel: only distinguishes the 4 centuries -> sector of 90 deg; use the coarse reading
    k400 = int(np.floor((w400*4 + 0.5 - READ/100))) % 4
    c400 = k400 in (1, 2, 3)
    skip = c4 or (c100 and c400)
    return (not skip), m4, m100
bad = [y for y in range(1582, 6001) if cams(y)[0] != is_leap(y)]
out['gregorian'] = {'years_checked': '1582-6000', 'errors': bad,
                    'cam_margins_deg': {'w4 (1 rev/4 yr), sector 90 deg': 45.0, 'w100 (1 rev/100 yr), sector 3.6 deg': 1.8,
                                        'w400 (1 rev/400 yr), sector 90 deg': 45.0},
                    'ratios': {'ring->w4': '1:4 (e.g. 15:60)', 'w4->w100': '1:25 (e.g. 12:60 x 12:60)', 'w100->w400': '1:4 (15:60)'},
                    'drift_vs_tropical_year_days_per_century': (365.2425 - 365.24219)*100}
print('Gregorian cams: errors over 1582-6000 ->', bad[:10])

# ---------------------------------------------------------------- 2. sidereal time = hour hand + mean Sun
trop = 365.242190; gmst_rate = 1.002737909350795
out['sidereal'] = {'rate_from_differential': 1 + 1/trop, 'iau_gmst_rate': gmst_rate,
                   'diff_seconds_per_century': (1 + 1/trop - gmst_rate)*86400*36525}

# ---------------------------------------------------------------- 3. equation of time with a Hooke joint
T = np.arange(0, 100*365.25, 0.25)/36525
L0 = (280.46646 + 36000.76983*T + 0.0003032*T*T)*P
Ms = (357.52911 + 35999.05029*T - 0.0001537*T*T)*P
e = 0.016708634 - 0.000042037*T
C = ((1.914602 - 0.004817*T - 0.000014*T*T)*np.sin(Ms) + (0.019993 - 0.000101*T)*np.sin(2*Ms) + 0.000289*np.sin(3*Ms))*P
lam = L0 + C
eps = (23.0 + 26/60 + 21.448/3600 - 46.8150/3600*T)*P
def eot_min(L, la, ep):
    a = np.arctan2(np.cos(ep)*np.sin(la), np.cos(la))
    return np.degrees(wrap(L - a))*4
ref = eot_min(L0, lam, eps)
p_rate = 5028.796195/3600*P      # general precession per century
# mechanism (a): Earth equant fixed in the J2000 frame (eccentric pivot fixed), Hooke joint fed with lambda + precession
w_j2000 = (102.93768193 + 180)*P; e_mid = 0.01671123 - 0.00004392*0.5
Lsid = L0 - p_rate*T                                         # mean Sun in the fixed frame
th, _ = equant(wrap(Lsid - w_j2000), e_mid)
lam_a = w_j2000 + th + p_rate*T                               # back to equinox of date via the differential
eps_mid = (23.0 + 26/60 + 21.448/3600 - 46.8150/3600*0.5)*P
mech_a = eot_min(L0, lam_a, eps_mid)
mech_b = eot_min(L0 - p_rate*T, lam_a - p_rate*T, eps_mid)   # same, but WITHOUT the precession input
# classical cam: EoT profile cut for 2050 and turned by the mean Sun (tropical) -> perihelion drift not followed
Tm = 0.5
L0m = L0; Mm = L0 - (282.9373 + 1.7195*Tm)*P                    # cam keeps perihelion of 2050
cam = eot_min(L0, L0 + equant(wrap(Mm), e_mid)[0] - wrap(Mm), eps_mid)
out['equation_of_time'] = {
    'amplitude_ref_min': [float(ref.min()), float(ref.max())],
    'hooke_with_precession_input_max_err_s': float(np.max(np.abs(mech_a - ref))*60),
    'hooke_without_precession_input_max_err_s': float(np.max(np.abs(mech_b - ref))*60),
    'fixed_cam_2050_max_err_s': float(np.max(np.abs(cam - ref))*60),
}
print('EoT:', out['equation_of_time'])

# ---------------------------------------------------------------- 4. precession train
prec_years = 360*3600/(5028.796195/100)
out['precession'] = {'period_tropical_years': prec_years,
                     'from_year_shaft_4_pairs': best_trains(1/prec_years, 4, top=3),
                     'from_year_shaft_3_pairs_plus_worm_1_100': best_trains(100/prec_years, 3, top=3)}
print('precession period', prec_years, out['precession']['from_year_shaft_4_pairs'][0])

# ---------------------------------------------------------------- 5. Galilean moons (E5 mean motions, deg/day)
n = {'io': 203.48895579, 'europa': 101.374724735, 'ganymede': 50.317609207, 'callisto': 21.571071177}
nu = n['io'] - 2*n['europa']
out['galilean'] = {'mean_motions_deg_per_day': n,
                   'laplace_check_deg_per_day': n['io'] - 3*n['europa'] + 2*n['ganymede'],
                   'nu_deg_per_day': nu, 'nu_check': n['europa'] - 2*n['ganymede'], 'nu_period_days': 360/nu,
                   'periods_days': {k: 360/v for k, v in n.items()}}
trains = {}
for name, rate in [('ganymede', n['ganymede']/360), ('nu', nu/360), ('callisto', n['callisto']/360)]:
    trains[name] = {k: best_trains(rate, k, top=2) for k in (2, 3)}
out['galilean']['trains_from_day_shaft'] = trains
for name, d in trains.items():
    for k, lst in d.items():
        if not lst: print(f"  {name:9s} {k} pairs: none"); continue
        b = lst[0]
        print(f"  {name:9s} {k} pairs: {b['drivers']}/{b['driven']} rel_err={b['rel_err']:.2e}")
json.dump(out, open('calendar_time_results.json', 'w'), indent=1, default=float)
