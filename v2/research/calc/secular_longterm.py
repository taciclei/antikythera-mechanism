"""Long-term validity: error growth of frozen orbital shapes (e, varpi, I, Omega frozen at 2050) and
size of the long-period 'great inequality' terms (JPL Table 2a/2b, 3000 BC - 3000 AD)."""
import json
import numpy as np
from kepler_models import kepler, wrap
P = np.pi/180
T2 = {  # JPL Table 2a: a, e, I, L, varpi, Omega and rates per century
 'mercury': ([0.38709843, 0.20563661, 7.00559432, 252.25166724, 77.45771895, 48.33961819], [0.0, 0.00002123, -0.00590158, 149472.67486623, 0.15940013, -0.12214182]),
 'venus':   ([0.72332102, 0.00676399, 3.39777545, 181.97970850, 131.76755713, 76.67261496], [-0.00000026, -0.00005107, 0.00043494, 58517.81560260, 0.05679648, -0.27274174]),
 'earth':   ([1.00000018, 0.01673163, -0.00054346, 100.46691572, 102.93005885, -5.11260389], [-0.00000003, -0.00003661, -0.01337178, 35999.37306329, 0.31795260, -0.24123856]),
 'mars':    ([1.52371243, 0.09336511, 1.85181869, -4.56813164, -23.91744784, 49.71320984], [0.00000097, 0.00009149, -0.00724757, 19140.29934243, 0.45223625, -0.26852431]),
 'jupiter': ([5.20248019, 0.04853590, 1.29861416, 34.33479152, 14.27495244, 100.29282654], [-0.00002864, 0.00018026, -0.00322699, 3034.90371757, 0.18199196, 0.13024619]),
 'saturn':  ([9.54149883, 0.05550825, 2.49424102, 50.07571329, 92.86136063, 113.63998702], [-0.00003065, -0.00032044, 0.00451969, 1222.11494724, 0.54179478, -0.25015002]),
 'uranus':  ([19.18797948, 0.04685740, 0.77298127, 314.20276625, 172.43404441, 73.96250215], [-0.00020455, -0.00001550, -0.00180155, 428.49512595, 0.09266985, 0.05739699]),
 'neptune': ([30.06952752, 0.00895439, 1.77005520, 304.22289287, 46.68158724, 131.78635853], [0.00006447, 0.00000818, 0.00022400, 218.46515314, 0.01009938, -0.00606302]),
}
T2B = {'jupiter': (-0.00012452, 0.06064060, -0.35635438, 38.35125000), 'saturn': (0.00025899, -0.13434469, 0.87320147, 38.35125000),
       'uranus': (0.00058331, -0.97731848, 0.17689245, 7.67025000), 'neptune': (-0.00041348, 0.68346318, -0.10162547, 7.67025000)}
def pos(name, T, frozen_at=None, extra=True):
    e0, r = T2[name]
    el = [x + dx*T for x, dx in zip(e0, r)]
    if frozen_at is not None:
        el = [x + dx*frozen_at for x, dx in zip(e0, r)]; el[3] = e0[3] + r[3]*T
    a, e, I, L, w, O = el
    M = L - w
    if extra and name in T2B:
        b, c, s, f = T2B[name]; M = M + b*T*T + c*np.cos(f*T*P) + s*np.sin(f*T*P)
    nu, rr = kepler(wrap(M*P), e)
    u = (w - O)*P + nu; R = a*rr
    return (R*(np.cos(O*P)*np.cos(u) - np.sin(O*P)*np.sin(u)*np.cos(I*P)), R*(np.sin(O*P)*np.cos(u) + np.cos(O*P)*np.sin(u)*np.cos(I*P)))
out = {}
for half in (50, 100, 200, 500):
    T = np.arange(-half*365.25, half*365.25, 1.0)/36525 + 0.5
    xe, ye = pos('earth', T); xef, yef = pos('earth', T, 0.5)
    row = {}
    for p in ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']:
        x, y = pos(p, T, extra=False); xf, yf = pos(p, T, 0.5, extra=False)
        g = np.degrees(np.max(np.abs(wrap(np.arctan2(yf - yef, xf - xef) - np.arctan2(y - ye, x - xe)))))
        h = np.degrees(np.max(np.abs(wrap(np.arctan2(yf, xf) - np.arctan2(y, x)))))
        row[p] = (round(float(h), 3), round(float(g), 3))
    out[f'2050+-{half}yr'] = row
    print(f'frozen shapes, window 2050+-{half} yr (helio, geo max deg):', row)
gi = {}
T = np.arange(-30, 10, 0.01)
for p in T2B:
    b, c, s, f = T2B[p]
    gi[p] = {'amplitude_deg': float(np.hypot(c, s)), 'period_years': 36000/f/1.0*1}
print('long-period terms (added to M in Table 2b):', gi)
json.dump({'frozen_shape_error': out, 'great_inequality_terms': gi}, open('secular_results.json', 'w'), indent=1)
