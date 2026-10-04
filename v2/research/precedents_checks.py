#!/usr/bin/env python3
"""Exact-fraction checks of the gear ratios and figures quoted in precedents.md.

Run with any Python 3 (standard library only), e.g.
  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 precedents_checks.py

Every check prints the quantity, the value claimed by the source and our value.
Labels [C1]..[C12] match the [C..] tags used in precedents.md.
"""
from fractions import Fraction as F

DAY = 86400


def hms(days):
    """Format a duration in days as 'Dd Hh Mm S.SSs'."""
    s = float(days) * DAY
    d, s = divmod(s, DAY)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(d)}d {int(h)}h {int(m)}m {s:.3f}s"


def header(tag, title):
    print(f"\n[{tag}] {title}")


# --- Schwilgue, Strasbourg (Lefort 1993) -----------------------------------
header("C1", "Strasbourg: exact sidereal ratio via an epicyclic train (celestial globe)")
year = F(31556928)                      # 365 d 5 h 48 min 48 s (Schwilgue's tropical year)
R = year / (year + DAY)                 # sidereal day / mean solar day
print("  R = 31556928/31643328 =", R, "| 13*47*269 =", 13 * 47 * 269)
b, B, c, C, d, D, e, E = 18, 270, 18, 269, 26, 100, 18, 94
turns = 1 + F(D, d) * F(e, E) * (F(B, b) * F(c, C) - 1)
print("  1 + (D/d)(e/E)((B/b)(c/C) - 1) =", turns, "| 1/R =", 1 / R, "| exact:", turns == 1 / R)
print("  i.e. 1/R = 1 + 450/(13*47*269):", 1 / R == 1 + F(450, 13 * 47 * 269))

header("C2", "Strasbourg: approximate sidereal ratio on the lunar train")
approx = F(271375, 272118)
train = F(334 * 65 * 300, 28 * 341 * 57)
print("  (334*65*300)/(28*341*57) =", train, "= 12 *", approx, ":", train == 12 * approx)
rel = (approx - R) / R
print(f"  relative error {float(rel):.3e} -> {float(rel) * 36525 * DAY:.2f} s per century "
      "(source: about 1 s in a little more than a century)")
print(f"  as sidereal angle: {float(rel) * 36525 * 360.9856:.4f} deg per century")

header("C3", "Strasbourg: lunar/solar inequality trains driven by a 1-day arbor")
lunar = [
    ("anomaly (anomalistic month)", F(70209, 2548), (27, 13, 18, 34)),
    ("evection", F(74090, 2329), (31, 19, 29, 11.453)),
    ("variation (synodic month)", F(51649, 1749), (29, 12, 44, 3)),
    ("annual equation (anomalistic year)", F(226461, 620), (365, 6, 13, 57)),
    ("nodes (draconic month)", F(49880, 1833), (27, 5, 5, 35.8)),
]
for name, ratio, (dd, hh, mm, ss) in lunar:
    target = dd + hh / 24 + mm / 1440 + ss / DAY
    err = (float(ratio) - target) * DAY
    print(f"  {name:36s} {str(ratio):>12s} = {hms(ratio)}  (target {dd}d {hh}h {mm}m {ss}s, err {err:+.3f} s)")

header("C4", "Strasbourg: precession wheel of 128 teeth, one turn in ~25,800 years")
for yrs in (25800, 25806):
    print(f"  teeth passed in 170 years at {yrs} y/turn: {128 * 170 / yrs:.3f} (source says 0.7)")

header("C5", "Strasbourg planetarium: worst period error 13 s on Jupiter (Lefort)")
jup = 374163250   # s, = 2*5^3*59*25367 (Lefort's table)
print("  2*5**3*59*25367 =", 2 * 5**3 * 59 * 25367, "| check:", 2 * 5**3 * 59 * 25367 == jup)
revs = 36525 * DAY / jup
print(f"  angle error after one century: {revs * 360 * 13 / jup:.2e} deg")

# --- Huygens 1682 ------------------------------------------------------------
header("C6", "Huygens planetarium (1682): drift of his tooth ratios against modern periods")
sid_year = 365.256363
modern = {"Mercury": 87.9691, "Venus": 224.701, "Mars": 686.980, "Jupiter": 4332.589, "Saturn": 10759.22}
huygens = {"Mercury": F(204, 847), "Venus": F(32, 52), "Mars": F(158, 84),
           "Jupiter": F(166, 14), "Saturn": F(206, 7)}
for p, r in huygens.items():
    true = modern[p] / sid_year
    drift = 100 / float(r) * 360 - 100 / true * 360
    print(f"  {p:8s} ratio {str(r):>8s} = {float(r):.6f} y (modern {true:.6f}) drift {drift:+7.2f} deg/century")
print("  Saturn convergent: 77708431/2640858 =", f"{77708431 / 2640858:.6f}", "-> 206/7 =", f"{206 / 7:.6f}")

# --- Dondi 1364 --------------------------------------------------------------
header("C7", "Dondi, Mercury dial: 63/20 x 12 signs per year")
s = F(63, 20) * 12
print("  =", s, "signs =", int(s), "signs", float((s - int(s)) * 30), "deg (source: 37 signs 24 deg)")

# --- Sidereal-time ratios compared -------------------------------------------
header("C8", "Sidereal ratio accuracy, expressed as star-dial drift per century")
ideal = 365.2422 / 366.2422
cases = {
    "Patek Calibre 89 (0.9972677)": 0.9972677,
    "Schwilgue approx 271375/272118": float(F(271375, 272118)),
    "Wallingford (1 part in 3 million)": ideal * (1 + 1 / 3e6),
}
for name, val in cases.items():
    rel = (val - ideal) / ideal
    print(f"  {name:34s} rel {rel:+.2e} -> {rel * 36525 * 360.9856:+8.3f} deg/century")

# --- Precession ---------------------------------------------------------------
header("C9", "Precession periods used by the clocks vs the current value")
modern_prec = 25771.57534   # years (Wikipedia, Axial precession, IAU 2006 rate 5028.796195"/cy)
for name, yrs in [("Strasbourg", 25806), ("Jens Olsen", 25753), ("Soernes", 25800)]:
    d = (360 / yrs - 360 / modern_prec) * 100
    print(f"  {name:11s} {yrs} y -> rate error {d:+.4f} deg/century")
print(f"  25800 y in mean solar days: {25800 * 365.2422:,.0f} (Soernes quotes a 1:9,500,000 train)")

# --- Galilean moons ----------------------------------------------------------
header("C10", "Galilean moons: Laplace relation vs a pure 1:2:4 gear")
P = {"Io": 1.769138, "Europa": 3.551181, "Ganymede": 7.154553, "Callisto": 16.689017}  # NASA NSSDC
n = {k: 360 / v for k, v in P.items()}
print("  n_Io - 3 n_Eu + 2 n_Ga =", f"{n['Io'] - 3 * n['Europa'] + 2 * n['Ganymede']:+.2e}", "deg/day")
print(f"  P_Eu/P_Io = {P['Europa'] / P['Io']:.6f}, P_Ga/P_Eu = {P['Ganymede'] / P['Europa']:.6f}")
print(f"  pure 1:2:4 from Io: Europa drifts {(n['Io'] / 2 - n['Europa']) * 365.25:+.1f} deg/yr, "
      f"Ganymede {(n['Io'] / 4 - n['Ganymede']) * 365.25:+.1f} deg/yr")

header("C11", "Galilean moons: light-time effect seen from Earth (Roemer 1676)")
lt_au = 499.005 / DAY
print(f"  Io moves {n['Io'] * lt_au:.2f} deg per AU of light time; Earth-Jupiter distance swings ~2 AU "
      f"-> {2 * n['Io'] * lt_au:.2f} deg peak to peak")

# --- Secular calendar -------------------------------------------------------
header("C12", "Andersen secular calendar: 48-month cam, 50-tooth secular wheel stepped every 8 years")
print("  50 teeth x 8 years =", 50 * 8, "years per turn")
greg = F(365 * 400 + 97, 400)
print("  Gregorian mean year =", greg, "=", float(greg), "days; tropical 365.24219 -> drift",
      f"{(float(greg) - 365.24219) * 100 * 24 * 60:.1f} min per century")

# --- Kepler mechanisms (not a precedent: a quantitative reading of them) -----
import math

# JPL "Approximate Positions of the Planets", Table 1 (1800-2050), J2000 values: a (au), e
ELEM = {
    "Mercury": (0.38709927, 0.20563593), "Venus": (0.72333566, 0.00677672),
    "Earth": (1.00000261, 0.01671123), "Mars": (1.52371034, 0.09339410),
    "Jupiter": (5.20288700, 0.04838624), "Saturn": (9.53667594, 0.05386179),
    "Uranus": (19.18916464, 0.04725744), "Neptune": (30.06992276, 0.00859048),
}
N = 720


def kepler(a, e, M):
    """True anomaly and radius of the Kepler ellipse (Sun at focus, perihelion on +x)."""
    E = M
    for _ in range(50):
        E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
    return nu, a * (1 - e * math.cos(E))


def pin_slot(e, M):
    """Antikythera-style pin-and-slot with offset k = 2e: follower angle."""
    k = 2 * e
    return math.atan2(math.sin(M), math.cos(M) - k)


def equant(a, e, M):
    """Ptolemaic equant: deferent centre at -ae, equant at -2ae, uniform angle M about the equant."""
    qx, cx = -2 * a * e, -a * e
    ux, uy = math.cos(M), math.sin(M)
    dqc = qx - cx
    t = -ux * dqc + math.sqrt((ux * dqc) ** 2 - dqc ** 2 + a * a)
    px, py = qx + t * ux, t * uy
    return math.atan2(py, px), math.hypot(px, py)


def wrap(x):
    return (x + math.pi) % (2 * math.pi) - math.pi


header("C13", "Equation of centre: pin-and-slot (k = 2e) and equant vs exact Kepler, max |error| in deg")
for p, (a, e) in ELEM.items():
    err_ps = err_eq = 0.0
    for i in range(N):
        M = 2 * math.pi * i / N
        nu, _ = kepler(a, e, M)
        err_ps = max(err_ps, abs(wrap(pin_slot(e, M) - nu)))
        err_eq = max(err_eq, abs(wrap(equant(a, e, M)[0] - nu)))
    print(f"  {p:8s} e={e:.4f}  pin-and-slot {math.degrees(err_ps):6.3f}  (3/4 e^2 = "
          f"{math.degrees(0.75 * e * e):6.3f})   equant {math.degrees(err_eq):6.3f}")
ae = 0.0549
print(f"  Moon (e = {ae}): pin-and-slot 3/4 e^2 = {math.degrees(0.75 * ae * ae):.3f} deg")

header("C14", "Geocentric longitude error from the orrery geometry (2-D, inclinations ignored), max deg")
print("  case A: exact Kepler angles but circular radius r = a for Earth and planet")
print("  case B: equant model (angle and radius) for Earth and planet")
NG = 360


def track(a, e, model):
    out = []
    for i in range(NG):
        M = 2 * math.pi * i / NG
        nu, r = kepler(a, e, M)
        if model == "circ":
            r = a
        elif model == "equant":
            nu, r = equant(a, e, M)
        out.append((r * math.cos(nu), r * math.sin(nu)))
    return out


aE, eE = ELEM["Earth"]
earth = {m: track(aE, eE, m) for m in ("kepler", "circ", "equant")}
for p, (a, e) in ELEM.items():
    if p == "Earth":
        continue
    # perihelion directions differ between planets; use a 37 deg offset as a generic case
    rot = math.radians(37)
    pl = {m: [(x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot))
              for x, y in track(a, e, m)] for m in ("kepler", "circ", "equant")}
    worst = {"circ": 0.0, "equant": 0.0}
    for i in range(NG):
        for j in range(0, NG, 2):
            ex, ey = earth["kepler"][j]
            px, py = pl["kepler"][i]
            ref = math.atan2(py - ey, px - ex)
            for m in worst:
                ex2, ey2 = earth[m][j]
                px2, py2 = pl[m][i]
                worst[m] = max(worst[m], abs(wrap(math.atan2(py2 - ey2, px2 - ex2) - ref)))
    print(f"  {p:8s} A (circular radius) {math.degrees(worst['circ']):6.2f}   "
          f"B (equant) {math.degrees(worst['equant']):6.3f}")
