"""Eclipse predictor of the v2 mechanism, validated against NASA's Five Millennium Canon (2001-2100).

The mechanism quantities (all available as shafts or sliders in the proposed design):
  - true Moon longitude: recommended cascade (reduction, annual, evection, equant anomaly, variation)
  - Moon latitude: asin(sin i_eff * sin(F_true)), F_true = Moon - mean node (Scotch yoke on the draconic shaft)
  - true Sun: mean Sun + Earth equant; Sun declination from a Scotch yoke (sin d = sin eps sin lambda)
  - Moon distance (parallax) from the equant anomaly unit's pin radius
Syzygies are found on the MECHANISM's own elongation (what a user sees when the Sun and Moon pointers align).
"""
import csv, json
import numpy as np
from moon import args, meeus, pinslot, pinslot_doubled, sun_eoc, P
from kepler_models import equant, wrap

MON = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}

def jd(y, m, d, hh=0.0):
    if m <= 2: y -= 1; m += 12
    A = y//100; B = 2 - A + A//4
    return int(365.25*(y + 4716)) + int(30.6001*(m + 1)) + d + B - 1524.5 + hh/24

def mech_state(T, i_eff=5.0):
    Lp, D, M, Mp, F, Om = args(T)
    Ls = Lp - D; w = Lp - Mp
    k_an = 6.288774*P; k_ev = 1.274027*P; k_va = 0.658314*P; k_rd = 0.114332*P
    # recommended cascade: reduction -> annual (differential) -> evection -> anomaly (equant) -> variation
    th = pinslot_doubled(Lp, Om, -2*k_rd)
    th = th - (0.185116/1.9148)*sun_eoc(M)
    th = pinslot(th, 2*Ls - w, k_ev)
    x = th - w; a_an, r_an = equant(x, k_an/2); th = w + a_an
    th = pinslot_doubled(th, Ls, 2*k_va)
    lam_m = th
    beta = np.arcsin(np.sin(i_eff*P)*np.sin(lam_m - Om))
    lam_s = Ls + sun_eoc(M)                         # true Sun (mean equinox of date)
    par = 0.9507*P / r_an                           # Moon horizontal parallax from the anomaly unit's radius
    return lam_m, beta, lam_s, par

def find_syzygies(T0, T1, step_d=0.1, i_eff=5.0):
    T = np.arange(T0*36525, T1*36525, step_d)/36525
    lam_m, beta, lam_s, par = mech_state(T, i_eff)
    el = wrap(lam_m - lam_s)
    out = []
    for kind, target in (('new', 0.0), ('full', np.pi)):
        s = wrap(el - target)
        idx = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
        for i in idx:
            f = -s[i]/(s[i+1] - s[i])
            Tc = T[i] + f*(T[i+1] - T[i])
            out.append((kind, Tc))
    return out

def gmst_deg(T):
    d = T*36525
    return (280.46061837 + 360.98564736629*d + 0.000387933*T*T) % 360

def predict(kind, Tc, i_eff=5.0):
    lm, b, ls, par = mech_state(np.array([Tc]), i_eff)
    lm, b, ls, par = float(lm[0]), float(b[0]), float(ls[0]), float(par[0])
    eps = (23.439291 - 0.0130042*Tc)*P
    if kind == 'new':
        gamma = np.sin(b)*np.cos(5.3*P)/np.sin(par)
        dec = np.arcsin(np.sin(eps)*np.sin(ls)); ra = np.arctan2(np.cos(eps)*np.sin(ls), np.cos(ls))
    else:
        gamma = np.sin(b)*np.cos(5.3*P)/np.sin(par)
        la = ls + np.pi
        dec = np.arcsin(np.sin(eps)*np.sin(la)); ra = np.arctan2(np.cos(eps)*np.sin(la), np.cos(la))
    # sub-point (solar: sub-solar; lunar: sub-lunar ~ anti-solar) at the mechanism's syzygy instant, Delta T ignored
    lon_sub = np.degrees(wrap(ra - gmst_deg(Tc)*P))
    # simple 'where': latitude = declination + asin(gamma) along the projected ecliptic-north direction
    psi = np.arctan2(-np.sin(eps)*np.cos(ls if kind == 'new' else ls + np.pi), np.cos(eps))   # ecliptic-pole position angle (approx)
    x, y = gamma*np.sin(psi), gamma*np.cos(psi)
    if kind == 'new' and abs(gamma) < 1:
        z = np.sqrt(max(0.0, 1 - x*x - y*y))
        lat = np.degrees(np.arcsin(y*np.cos(dec) + z*np.sin(dec)))
        dH = np.degrees(np.arctan2(x, z*np.cos(dec) - y*np.sin(dec)))
        lon = np.degrees(wrap((lon_sub + dH)*P))
        lat_simple = np.degrees(dec) + np.degrees(np.arcsin(np.clip(gamma, -1, 1)))
    else:
        lat = np.degrees(dec) + (np.degrees(b) if kind == 'full' else 0); lon = lon_sub; lat_simple = lat
    return dict(gamma=gamma, beta_deg=np.degrees(b), lat=lat, lat_simple=lat_simple, lon=lon, lon_sub=lon_sub, par_deg=np.degrees(par))

def load(fn):
    rows = []
    for r in csv.reader(open(fn)):
        if r[0].startswith('#'): continue
        rows.append(r)
    return rows

def parse_ll(s):
    v = float(s[:-1]); return v if s[-1] in 'NE' else -v

if __name__ == '__main__':
    base = 'data/'
    se = load(base + 'nasa_solar_eclipses_2001_2100.csv')
    le = load(base + 'nasa_lunar_eclipses_2001_2100.csv')
    T0 = (jd(2001, 1, 1) - 2451545)/36525; T1 = (jd(2101, 1, 1) - 2451545)/36525
    syz = find_syzygies(T0, T1)
    print('mechanism syzygies found:', len(syz))
    ref = []
    for r in se:
        hh, mm, ss = map(int, r[4].split(':'))
        Tn = (jd(int(r[1]), MON[r[2]], int(r[3]), hh + mm/60 + ss/3600) - 2451545)/36525
        ref.append(('new', Tn, float(r[10]), float(r[11]), r[8], parse_ll(r[12]), parse_ll(r[13]) if len(r) > 13 else None))
    for r in le:
        hh, mm, ss = map(int, r[4].split(':'))
        Tn = (jd(int(r[1]), MON[r[2]], int(r[3]), hh + mm/60 + ss/3600) - 2451545)/36525
        ref.append(('full', Tn, float(r[10]), float(r[12]), r[8], parse_ll(r[16]), parse_ll(r[17])))
    # match each NASA eclipse to the nearest mechanism syzygy of the same kind
    res = {'new': [], 'full': []}
    syz_by = {'new': np.array([t for k, t in syz if k == 'new']), 'full': np.array([t for k, t in syz if k == 'full'])}
    for kind, Tn, g, mag, typ, lat, lon in ref:
        arr = syz_by[kind]; j = int(np.argmin(np.abs(arr - Tn))); Tm = arr[j]
        p = predict(kind, Tm)
        res[kind].append(dict(T=Tn, dt_h=(Tm - Tn)*36525*24, gamma_ref=g, gamma_mech=p['gamma'], mag_ref=mag, type=typ,
                              lat_ref=lat, lon_ref=lon, lat=p['lat'], lat_simple=p['lat_simple'], lon=p['lon']))
    summary = {}
    for kind in ('new', 'full'):
        R = res[kind]
        dt = np.array([r['dt_h'] for r in R]); dg = np.array([r['gamma_mech'] - r['gamma_ref'] for r in R])
        summary[kind] = {'n': len(R), 'time_err_h_max': float(np.abs(dt).max()), 'time_err_h_rms': float(np.sqrt(np.mean(dt*dt))),
                         'gamma_err_max': float(np.abs(dg).max()), 'gamma_err_rms': float(np.sqrt(np.mean(dg*dg)))}
    # magnitudes from gamma (Meeus ch.54 linear formulas, mean u = 0.0059 for lack of a u mechanism)
    u = 0.0059
    L = res['full']
    um_pred = np.array([(1.0128 - u - abs(r['gamma_mech']))/0.5450 for r in L])
    um_ref = np.array([r['mag_ref'] for r in L])
    summary['full']['umbral_mag_err_rms'] = float(np.sqrt(np.mean((um_pred - um_ref)**2)))
    summary['full']['umbral_mag_err_max'] = float(np.abs(um_pred - um_ref).max())
    # solar 'where' for central eclipses (|gamma| < 0.9)
    S = [r for r in res['new'] if abs(r['gamma_ref']) < 0.9 and r['lon_ref'] is not None]
    dlat = np.array([r['lat'] - r['lat_ref'] for r in S]); dlat_s = np.array([r['lat_simple'] - r['lat_ref'] for r in S])
    dlon = np.array([np.degrees(wrap((r['lon'] - r['lon_ref'])*P)) for r in S])
    summary['new']['central_n'] = len(S)
    summary['new']['where_lat_err_deg_rms'] = float(np.sqrt(np.mean(dlat**2))); summary['new']['where_lat_err_deg_max'] = float(np.abs(dlat).max())
    summary['new']['where_lat_simple_err_deg_rms'] = float(np.sqrt(np.mean(dlat_s**2))); summary['new']['where_lat_simple_err_deg_max'] = float(np.abs(dlat_s).max())
    summary['new']['where_lon_err_deg_rms'] = float(np.sqrt(np.mean(dlon**2))); summary['new']['where_lon_err_deg_max'] = float(np.abs(dlon).max())
    summary['new']['hemisphere_correct_fraction'] = float(np.mean([np.sign(r['lat']) == np.sign(r['lat_ref']) for r in S]))
    F = [r for r in res['full'] if r['lon_ref'] is not None]
    dlatF = np.array([r['lat'] - r['lat_ref'] for r in F]); dlonF = np.array([np.degrees(wrap((r['lon'] - r['lon_ref'])*P)) for r in F])
    summary['full']['zenith_lat_err_deg_rms'] = float(np.sqrt(np.mean(dlatF**2))); summary['full']['zenith_lon_err_deg_rms'] = float(np.sqrt(np.mean(dlonF**2)))
    summary['full']['zenith_lon_err_deg_max'] = float(np.abs(dlonF).max())
    # detection test: classify every mechanism syzygy by gamma thresholds, compare with the NASA lists
    det = {}
    nasa_new = np.array([t for k, t, *_ in ref if k == 'new']); nasa_full = np.array([t for k, t, *_ in ref if k == 'full'])
    for kind, arr, lim in (('new', nasa_new, 1.5433 + u), ('full', nasa_full, 1.5573 + u)):
        hits = miss = false = 0; border = []
        for Tm in syz_by[kind]:
            g = predict(kind, Tm)['gamma']
            pred = abs(g) < lim
            real = np.any(np.abs(arr - Tm) < 0.6/36525*1)  # within ~0.6 day
            real = np.any(np.abs(arr - Tm)*36525 < 0.6)
            if pred and real: hits += 1
            elif real and not pred: miss += 1; border.append(round(float(g), 3))
            elif pred and not real: false += 1; border.append(round(float(g), 3))
        det[kind] = dict(hits=hits, missed=miss, false_alarms=false, gamma_of_errors=border)
    summary['detection'] = det
    print(json.dumps(summary, indent=1))
    json.dump(summary, open('eclipses_results.json', 'w'), indent=1)
