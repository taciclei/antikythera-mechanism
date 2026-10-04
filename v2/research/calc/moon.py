"""Modern Moon mechanism: which inequalities, how to sum them, and the residual error.

Reference: Meeus, Astronomical Algorithms ch. 47 (truncated ELP-2000/82, ~10" in longitude), tables as
transcribed in github.com/soniakeys/meeus (MIT). Window 2000-2100, step 0.05 day.
All models share the reference mean arguments (L', D, M, M', F): gear-ratio errors are budgeted elsewhere.
"""
import json
import numpy as np
from kepler_models import equant, wrap

P = np.pi/180
TA = [  # D, M, M', F, sigma_l (1e-6 deg)
 (0,0,1,0,6288774),(2,0,-1,0,1274027),(2,0,0,0,658314),(0,0,2,0,213618),(0,1,0,0,-185116),(0,0,0,2,-114332),
 (2,0,-2,0,58793),(2,-1,-1,0,57066),(2,0,1,0,53322),(2,-1,0,0,45758),(0,1,-1,0,-40923),(1,0,0,0,-34720),
 (0,1,1,0,-30383),(2,0,0,-2,15327),(0,0,1,2,-12528),(0,0,1,-2,10980),(4,0,-1,0,10675),(0,0,3,0,10034),
 (4,0,-2,0,8548),(2,1,-1,0,-7888),(2,1,0,0,-6766),(1,0,-1,0,-5163),(1,1,0,0,4987),(2,-1,1,0,4036),
 (2,0,2,0,3994),(4,0,0,0,3861),(2,0,-3,0,3665),(0,1,-2,0,-2689),(2,0,-1,2,-2602),(2,-1,-2,0,2390),
 (1,0,1,0,-2348),(2,-2,0,0,2236),(0,1,2,0,-2120),(0,2,0,0,-2069),(2,-2,-1,0,2048),(2,0,1,-2,-1773),
 (2,0,0,2,-1595),(4,-1,-1,0,1215),(0,0,2,2,-1110),(3,0,-1,0,-892),(2,1,1,0,-810),(4,-1,-2,0,759),
 (0,2,-1,0,-713),(2,2,-1,0,-700),(2,1,-2,0,691),(2,-1,0,-2,596),(4,0,1,0,549),(0,0,4,0,537),
 (4,-1,0,0,520),(1,0,-2,0,-487),(2,1,0,-2,-399),(0,0,2,-2,-381),(1,1,1,0,351),(3,0,-2,0,-340),
 (4,0,-3,0,330),(2,-1,2,0,327),(0,2,1,0,-323),(1,1,-1,0,299),(2,0,3,0,294)]
TB = [  # D, M, M', F, sigma_b (1e-6 deg)
 (0,0,0,1,5128122),(0,0,1,1,280602),(0,0,1,-1,277693),(2,0,0,-1,173237),(2,0,-1,1,55413),(2,0,-1,-1,46271),
 (2,0,0,1,32573),(0,0,2,1,17198),(2,0,1,-1,9266),(0,0,2,-1,8822),(2,-1,0,-1,8216),(2,0,-2,-1,4324),
 (2,0,1,1,4200),(2,1,0,-1,-3359),(2,-1,-1,1,2463),(2,-1,0,1,2211),(2,-1,-1,-1,2065),(0,1,-1,-1,-1870),
 (4,0,-1,-1,1828),(0,1,0,1,-1794),(0,0,0,3,-1749),(0,1,-1,1,-1565),(1,0,0,1,-1491),(0,1,1,1,-1475),
 (0,1,1,-1,-1410),(0,1,0,-1,-1344),(1,0,0,-1,-1335),(0,0,3,1,1107),(4,0,0,-1,1021),(4,0,-1,1,833),
 (0,0,1,-3,777),(4,0,-2,1,671),(2,0,0,-3,607),(2,0,2,-1,596),(2,-1,1,-1,491),(2,0,-2,1,-451),
 (0,0,3,-1,439),(2,0,2,1,422),(2,0,-3,-1,421),(2,1,-1,1,-366),(2,1,0,1,-351),(4,0,0,1,331),
 (2,-1,1,1,315),(2,-2,0,-1,302),(0,0,1,3,-283),(2,1,1,-1,-229),(1,1,0,-1,223),(1,1,0,1,223),
 (0,1,-2,-1,-220),(2,1,-1,-1,-220),(1,0,1,1,-185),(2,-1,-2,-1,181),(0,1,2,1,-177),(4,0,-2,-1,176),
 (4,-1,-1,-1,166),(1,0,1,-1,-164),(4,0,1,-1,132),(1,0,-1,-1,-119),(4,-1,0,-1,115),(2,-2,0,1,107)]

def horner(T, *c):
    return sum(ci*T**i for i, ci in enumerate(c))

def args(T):
    Lp = horner(T, 218.3164477, 481267.88123421, -.0015786, 1/538841, -1/65194000)*P
    D = horner(T, 297.8501921, 445267.1114034, -.0018819, 1/545868, -1/113065000)*P
    M = horner(T, 357.5291092, 35999.0502909, -.0001535, 1/24490000)*P
    Mp = horner(T, 134.9633964, 477198.8675055, .0087414, 1/69699, -1/14712000)*P
    F = horner(T, 93.272095, 483202.0175233, -.0036539, -1/3526000, 1/863310000)*P
    Om = horner(T, 125.0445479, -1934.1362891, .0020754, 1/467441, -1/60616000)*P
    return Lp, D, M, Mp, F, Om

def meeus(T):
    Lp, D, M, Mp, F, Om = args(T)
    E = 1 - .002516*T - .0000074*T*T
    A1 = (119.75 + 131.849*T)*P; A2 = (53.09 + 479264.29*T)*P; A3 = (313.45 + 481266.484*T)*P
    sl = 3958*np.sin(A1) + 1962*np.sin(Lp - F) + 318*np.sin(A2)
    for d, m, mp, f, c in TA:
        sl = sl + c*np.sin(d*D + m*M + mp*Mp + f*F)*E**abs(m)
    sb = -2235*np.sin(Lp) + 382*np.sin(A3) + 175*np.sin(A1 - F) + 175*np.sin(A1 + F) + 127*np.sin(Lp - Mp) - 115*np.sin(Lp + Mp)
    for d, m, mp, f, c in TB:
        sb = sb + c*np.sin(d*D + m*M + mp*Mp + f*F)*E**abs(m)
    return Lp + sl*1e-6*P, sb*1e-6*P

def pinslot(theta, beta, k):
    """Antikythera pin-and-slot on a carrier at angle beta: output longitude."""
    x = theta - beta
    return theta + np.arctan2(k*np.sin(x), 1 - k*np.cos(x))

def pinslot_doubled(theta, beta, k):
    """Stage working on 2(theta-beta): gear 2:1 up, pin-and-slot, 1:2 down (for 2D and 2F terms)."""
    x = 2*(theta - beta)
    return theta + 0.5*np.arctan2(k*np.sin(x), 1 - k*np.cos(x))

def sun_eoc(M):
    """Equation of centre of the Sun from the Earth's equant unit (rad)."""
    e = 0.01670
    th, _ = equant(M, e)
    return wrap(th - M)

def models(T):
    Lp, D, M, Mp, F, Om = args(T)
    Ls = Lp - D                      # mean Sun
    w = Lp - Mp                      # mean perigee
    k_an = 6.288774*P; k_ev = 1.274027*P; k_va = 0.658314*P; k_rd = 0.114332*P
    out = {}
    out['mean_only'] = Lp
    out['antikythera_pinslot_anomaly'] = pinslot(Lp, w, k_an)
    # equant anomaly (two pin-slots in cascade): e = k/2, second harmonic e^2 instead of 5/4 e^2
    th, _ = equant(Mp, k_an/2); out['equant_anomaly'] = w + th
    # parallel summation of pure sines (Scotch yokes + Kelvin-type summation / differential stack)
    order = sorted(TA, key=lambda r: -abs(r[4]))
    acc = Lp.copy()
    for n, (d, m, mp, f, c) in enumerate(order, 1):
        acc = acc + c*1e-6*P*np.sin(d*D + m*M + mp*Mp + f*F)
        if n in (1, 2, 3, 4, 5, 6, 8, 10, 13, 20, 30, 59):
            out[f'parallel_sines_{n}'] = acc.copy()
    # realistic cascade of Antikythera-type stages (each stage reads the previous stage's output)
    def cascade(order_):
        th = Lp.copy()
        for st in order_:
            if st == 'anomaly':
                th = pinslot(th, w, k_an)
            elif st == 'anomaly_eq':    # equant anomaly unit (slot-driven pin-and-slot + follower at the focus)
                z, _ = equant(th - w, k_an/2); th = w + z
            elif st == 'anomaly_eqe':   # equant-based anomaly unit (second harmonic correct)
                xx = th - w; z, _ = equant(xx, k_an/2); z = np.exp(1j*z)  # angle only
                th = w + np.angle(z) + (k_an/2)**2/4*np.sin(2*xx)  # + small correction epicyclet-equivalent
            elif st == 'evection':
                th = pinslot(th, 2*Ls - w, k_ev)
            elif st == 'variation':
                th = pinslot_doubled(th, Ls, 2*k_va)
            elif st == 'reduction':     # -0.114 sin 2F: doubled stage on the node carrier, offset reversed
                th = pinslot_doubled(th, Om, -2*k_rd)
            elif st == 'annual':        # differential: -0.0967 x (Sun's equation of centre)
                th = th - (0.185116/1.9148)*sun_eoc(M)
        return th
    out['cascade_A(an,ev,va,ann)'] = cascade(['anomaly', 'evection', 'variation', 'annual'])
    out['cascade_B(ev,va,ann,an)'] = cascade(['evection', 'variation', 'annual', 'anomaly'])
    out['cascade_C(an,ev,va,ann,red)'] = cascade(['anomaly', 'evection', 'variation', 'annual', 'reduction'])
    out['cascade_D(anEQE,ev,va,ann,red)'] = cascade(['anomaly_eqe', 'evection', 'variation', 'annual', 'reduction'])
    out['RECOMMENDED cascade(red,ann,ev,anEQ,va)'] = cascade(['reduction', 'annual', 'evection', 'anomaly_eq', 'variation'])
    return out

def latitude_models(T, lam_mech):
    Lp, D, M, Mp, F, Om = args(T)
    i = 5.145*P
    out = {}
    out['5.128 sin F_mean'] = 5.128122*P*np.sin(F)
    Ftrue = lam_mech - Om
    out['asin(sin i sin F_true) i=5.145'] = np.arcsin(np.sin(i)*np.sin(Ftrue))
    out['+ 0.173 sin(2D-F)'] = out['asin(sin i sin F_true) i=5.145'] + 0.173237*P*np.sin(2*D - F)
    syz = (np.abs(wrap(D)) < 2*P) | (np.abs(np.abs(wrap(D)) - np.pi) < 2*P)
    out['_syzygy_mask'] = syz
    out['asin(sin 5.0 sin F_true) [eclipse scale]'] = np.arcsin(np.sin(5.0*P)*np.sin(Ftrue))
    return out

if __name__ == '__main__':
    res = {}
    chunks = []
    T_all = np.arange(0, 100*365.25, 0.05)/36525.0
    stats = {}
    for Tc in np.array_split(T_all, 20):
        lam, beta = meeus(Tc)
        ms = models(Tc)
        for k, v in ms.items():
            d = np.degrees(wrap(v - lam))
            s = stats.setdefault(k, [0.0, 0.0, 0])
            s[0] = max(s[0], float(np.max(np.abs(d)))); s[1] += float(np.sum(d*d)); s[2] += d.size
        lat = latitude_models(Tc, ms['RECOMMENDED cascade(red,ann,ev,anEQ,va)'])
        syz = lat.pop('_syzygy_mask')
        for k, v in list(lat.items()):
            lat['@syzygy ' + k] = (v, syz)
        for k, v in lat.items():
            if isinstance(v, tuple):
                d = np.degrees(v[0][v[1]] - beta[v[1]])
            else:
                d = np.degrees(v - beta)
            s = stats.setdefault('LAT ' + k, [0.0, 0.0, 0])
            s[0] = max(s[0], float(np.max(np.abs(d)))); s[1] += float(np.sum(d*d)); s[2] += d.size
    print('Moon longitude/latitude error vs Meeus ch.47, 2000-2100 (deg): max | rms')
    for k, (mx, ss, n) in stats.items():
        res[k] = {'max_deg': round(mx, 4), 'rms_deg': round((ss/n)**0.5, 4)}
        print(f"  {k:40s} {mx:8.4f} {(ss/n)**0.5:8.4f}")
    # periods of the arguments (days)
    rates = {'M_prime (anomalistic month)': 477198.8675055, '2D-M_prime (evection)': 2*445267.1114034 - 477198.8675055,
             '2D (variation)': 2*445267.1114034, 'M (anomalistic year)': 35999.0502909, '2F (reduction)': 2*483202.0175233,
             'D (synodic month)': 445267.1114034, 'F (draconic month)': 483202.0175233,
             'evection carrier 2Ls - varpi (deg/yr)': None}
    per = {}
    for k, r in rates.items():
        if r: per[k] = round(36525*360/r, 5)
    n_ls = 445267.1114034 - 0, None
    # carrier rates in revolutions per year (Julian)
    Ls_rate = 481267.88123421 - 445267.1114034      # deg / century
    w_rate = 481267.88123421 - 477198.8675055
    per['carrier_evection_rev_per_year'] = round((2*Ls_rate - w_rate)/36000, 6)
    per['carrier_perigee_rev_per_year'] = round(w_rate/36000, 6)
    per['carrier_node_rev_per_year'] = round(-1934.1362891/36000, 6)
    print('periods/rates:', per)
    json.dump({'moon_errors': res, 'periods_days_and_rates': per}, open('moon_results.json', 'w'), indent=1)
