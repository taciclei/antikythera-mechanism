#!/usr/bin/env python3
"""Anticythere 2.0 -- gear trains: design, exact verification, spec and study.

Every rotating part of the machine is a *shaft*. Its mean rate (turns per mean solar day, an exact Fraction) follows
from the master day shaft J (1 turn per day) through four kinds of links:
  * gear trains: 1 to 3 compound pairs, teeth in [10, 220]. They are found here by an exhaustive search of
    factorable fractions and cross-checked against the continued-fraction (Stern-Brocot) best approximations;
  * differentials: exact linear combinations, realised by bevel differentials (carrier = (s1 + s2)/2) plus exact
    gain pairs (40:20 = 2, 80:20 = 4, ...);
  * steppers: the Geneva crosses of the Gregorian calendar, whose mean rates are exact;
  * nonlinear units (Kepler units, vector modules, lunar cascade, Hooke joint, phase ball): their MEAN rate is an
    exact linear combination of their inputs (one turn out per turn in).

Every rate is therefore an exact rational multiple of the day-shaft rate. The script compares it with the modern
target (v2/research/constants.json), asserts the error budgets and writes:
  v2/spec/trains.json   machine-readable spec (exact fractions as "p/q" strings, tooth counts, signs, errors)
  v2/study/trains.md    readable study in French, one table per subsystem

Usage (Blender's Python; numpy is only needed for the design search):
  BPY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
  $BPY v2/tools/trains.py            # design + verify + write the JSON and the Markdown
  $BPY v2/tools/trains.py --check    # re-verify v2/spec/trains.json from its tooth counts alone (no search)
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent            # v2/tools
V2 = HERE.parent
CONST_PATH = V2 / 'research' / 'constants.json'
OUT_JSON = V2 / 'spec' / 'trains.json'
OUT_MD = V2 / 'study' / 'trains.md'

ZMIN, ZMAX = 10, 220                               # allowed tooth counts (rule of the project)
CAPS = (60, 80, 100, 120, 150, 180, 220)           # wheel-size ladder: the smallest cap that meets the budget wins
MARGIN = Fraction(1, 2)                            # a train is accepted when its error <= MARGIN * allocation
MODULE_DEFAULT = Fraction(1, 2)                    # mm
MODULE_MIN = Fraction(2, 5)                        # 0.4 mm (project rule)
DAYS_PER_CY = 36525                                # Julian century (days)
DEG_PER_TURN = 360


def fr(x) -> Fraction:
    """Exact Fraction of a JSON value: the decimal string as printed, never the binary float."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    return Fraction(str(x))


def fstr(x: Fraction) -> str:
    x = Fraction(x)
    return f"{x.numerator}/{x.denominator}" if x.denominator != 1 else str(x.numerator)


def deg_cy(rate_turns_per_day: Fraction) -> Fraction:
    return rate_turns_per_day * DEG_PER_TURN * DAYS_PER_CY


def per_day(deg_per_cy: Fraction) -> Fraction:
    return deg_per_cy / (DEG_PER_TURN * DAYS_PER_CY)


# =====================================================================================================================
# 1. Targets (modern rates, exact decimals taken from constants.json)
# =====================================================================================================================

def poly_window_mean(c: dict) -> Fraction:
    """Mean rate (deg per century) over T in [0, 1] (2000-2100) of c0 + c1 T + c2 T^2 + c3 T^3 + c4 T^4."""
    return fr(c['c1_deg_per_cy']) + fr(c['c2']) + fr(c['c3']) + fr(c['c4'])


def load_targets(C: dict) -> dict:
    T = {}
    E = C['earth']
    pr = E['precession']
    # general precession p_A (IAU 2006), mean over 2000-2100: 5028.796195'' + 1.1054348'' (T^2 term) per century
    pA_deg_cy = (fr(pr['pA_arcsec_per_cy_IAU2006']) + fr(pr['pA_T2_arcsec_per_cy2'])) / 3600
    T['_pA_deg_cy'] = pA_deg_cy
    T['_tropical_year_days'] = fr(E['years_days']['tropical_mean_laskar']['value'])

    def add(key, deg_per_cy_, source, name_fr, uncert=None, note=None):
        T[key] = {'turns_per_day': per_day(deg_per_cy_), 'deg_per_cy': deg_per_cy_, 'source': source,
                  'name_fr': name_fr, 'uncert_deg_cy': uncert, 'note': note}

    P = C['planets']
    for p in ('earth', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune'):
        mm = P[p]['mean_motion']
        key = 'Y' if p == 'earth' else f'{p}_L'
        add(key, fr(mm['deg_per_century_sidereal']),
            'DE441 (JPL Horizons) ajusté 2000–2100, repère J2000 (constants.json, planets.%s.mean_motion)' % p,
            P[p]['name_fr'], fr(mm['rate_uncertainty_deg_per_century']))
    # Moon (Meeus ch. 47, equinox of date) -> J2000 frame by removing p_A; mean over 2000-2100 (T^2..T^4 included)
    mo = C['moon']['mean_arguments_meeus47_deg']
    L_trop, D_, Om_trop, pe_trop = (poly_window_mean(mo[k]) for k in ('L_prime', 'D', 'Omega', 'perigee'))
    src = 'Meeus ch. 47 (ELP-2000/82), moyenne 2000–2100, moins p_A (IAU 2006) pour le repère J2000'
    add('moon_L', L_trop - pA_deg_cy, src, 'Lune : longitude moyenne')
    add('moon_perigee', pe_trop - pA_deg_cy, src, 'Lune : périgée moyen ϖ')
    add('moon_node', Om_trop - pA_deg_cy, src, 'Lune : nœud ascendant moyen Ω')
    add('moon_D', D_, 'Meeus ch. 47, moyenne 2000–2100 (D ne dépend pas du repère)', 'Lune : élongation moyenne D')
    add('moon_F', poly_window_mean(mo['F']), 'Meeus ch. 47, moyenne 2000–2100', 'Lune : argument de latitude F')
    add('moon_Mp', poly_window_mean(mo['M_prime']), 'Meeus ch. 47, moyenne 2000–2100', 'Lune : anomalie moyenne M′')
    add('evection_carrier', 2 * T['Y']['deg_per_cy'] - T['moon_perigee']['deg_per_cy'],
        '2·(Terre, DE441) − ϖ (Meeus), repère J2000', 'Porte-satellite de l’évection 2λ☉ − ϖ')
    add('precession_ring', -pA_deg_cy, 'p_A IAU 2006 (Capitaine et al. 2003), moyenne 2000–2100',
        'Anneau du zodiaque tropique (précession, sens rétrograde)')
    add('saros', D_ / 223, '223 lunaisons moyennes (D de Meeus, moyenne 2000–2100)', 'Saros')
    add('exeligmos', D_ / 669, '669 lunaisons moyennes', 'Exeligmos (3 Saros)')
    # Galilean moons: Lieske E5 mean motions (deg/day, fixed equinox = sidereal)
    G = C['galilean']['moons']
    n = {k: fr(G[k]['mean_motion_deg_per_day_E5']) for k in ('io', 'europa', 'ganymede', 'callisto')}
    e5 = 'Lieske E5 (Meeus ch. 44), repère fixe'
    for k, nm in (('io', 'Io'), ('europa', 'Europe'), ('ganymede', 'Ganymède'), ('callisto', 'Callisto')):
        add(k, n[k] * DAYS_PER_CY, e5, nm)
    nu = (n['io'] - n['europa'] - 2 * n['ganymede']) / 2   # = n_Io - 2 n_Eu = n_Eu - 2 n_Ga (to 5e-10 deg/day)
    add('nu', nu * DAYS_PER_CY, e5 + ' : ν = n_Io − 2n_Eu = n_Eu − 2n_Ga (moyenne des deux)',
        'Arbre ν (la ligne des conjonctions tourne à −ν)')
    T['_galilean_n_deg_day'] = n
    # sidereal time: GMST rate per UT1 day (IERS 2010) -- the machine realises 1 + Y + p_A
    T['gmst'] = {'turns_per_day': fr(E['rotation']['gmst_ratio_sidereal_per_solar']),
                 'source': 'IERS 2010 (rapport temps sidéral moyen / temps solaire moyen)', 'name_fr': 'Temps sidéral (TSMG)'}
    T['stellar'] = {'turns_per_day': fr(E['rotation']['era_turns_per_ut1_day']),
                    'source': 'IERS 2010 (angle de rotation de la Terre, ERA)', 'name_fr': 'Rotation stellaire (ERA)'}
    # Mars perihelion (optional apsidal plate): Simon 1994 secular rate in the J2000 frame
    add('mars_apsides', fr(P['mars']['simon1994_secular_J2000']['varpi_rate_deg_per_cy']),
        'Simon et al. 1994, ϖ de Mars, repère J2000', 'Ligne des apsides de Mars (option)')
    # elements for the geocentric amplification bound
    T['_elements'] = {p: (fr(P[p]['jpl_table1_1800_2050']['elements']['a_au']), fr(P[p]['jpl_table1_1800_2050']['elements']['e']))
                      for p in ('mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune')}
    return T


# =====================================================================================================================
# 2. Rational approximation: continued fractions / Stern-Brocot, and the exhaustive search of factorable fractions
# =====================================================================================================================

def cf_terms(x: Fraction, nmax: int = 60) -> list[int]:
    terms = []
    for _ in range(nmax):
        a = x.numerator // x.denominator
        terms.append(a)
        rest = x - a
        if rest == 0:
            break
        x = 1 / rest
    return terms


def convergents(x: Fraction, qmax: int):
    """Convergents h/k of x (continued fraction) with k <= qmax."""
    h2, h1, k2, k1 = 0, 1, 1, 0
    out = []
    for a in cf_terms(x, 200):
        h, k = a * h1 + h2, a * k1 + k2
        if k > qmax:
            break
        out.append(Fraction(h, k))
        h2, h1, k2, k1 = h1, h, k1, k
    return out


def best_rational(x: Fraction, qmax: int) -> Fraction:
    """Best rational approximation of x with denominator <= qmax (convergents + largest admissible semiconvergents:
    every best approximation of the first kind is one of them -- the Stern-Brocot descent towards x)."""
    h2, h1, k2, k1 = 0, 1, 1, 0
    cands = []
    for a in cf_terms(x, 200):
        if k1 > 0:
            j = min(a, (qmax - k2) // k1)
            if j >= 1:
                cands.append(Fraction(h2 + j * h1, k2 + j * k1))
        h, k = a * h1 + h2, a * k1 + k2
        if k > qmax:
            break
        cands.append(Fraction(h, k))
        h2, h1, k2, k1 = h1, h, k1, k
    return min(cands, key=lambda c: abs(c - x))


_PROD: dict = {}


def products(k: int, cap: int):
    """Sorted distinct products of k integers in [ZMIN, cap], plus a membership table."""
    import numpy as np
    key = (k, cap)
    if key not in _PROD:
        z = np.arange(ZMIN, cap + 1, dtype=np.int64)
        v = z.copy()
        for _ in range(k - 1):
            v = np.unique((v[:, None] * z[None, :]).ravel())
        table = np.zeros(int(v.max()) + 1, dtype=bool)
        table[v] = True
        _PROD[key] = (v, table)
    return _PROD[key]


def search(r: float, k: int, cap: int, top: int = 60) -> list[tuple[float, int, int]]:
    """Best fractions N/D close to r, N and D both products of k integers in [ZMIN, cap]. Sorted by relative error."""
    import numpy as np
    v, table = products(k, cap)
    Q = v.astype(np.float64)
    found = {}
    for rounding in (np.floor, np.ceil):
        N = rounding(r * Q).astype(np.int64)
        idx = np.nonzero((N >= ZMIN ** k) & (N < table.size))[0]
        idx = idx[table[N[idx]]]
        if idx.size == 0:
            continue
        err = np.abs(N[idx] / Q[idx] - r) / r
        for i in idx[np.argsort(err, kind='stable')[:top]]:
            n_, d_ = int(N[i]), int(v[i])
            g = math.gcd(n_, d_)
            red = (n_ // g, d_ // g)
            e = abs(n_ / d_ - r) / r
            if red not in found or (n_, d_) < found[red][1:]:
                found[red] = (e, n_, d_)
    return sorted(found.values())[:top]


def factorizations(n: int, k: int, cap: int, lo: int = ZMIN) -> list[tuple[int, ...]]:
    """All non-increasing k-tuples of integers in [lo, cap] whose product is n."""
    if k == 1:
        return [(n,)] if lo <= n <= cap else []
    out = []
    f = min(cap, n // lo ** (k - 1))
    while f >= lo and f ** k >= n:
        if n % f == 0:
            for t in factorizations(n // f, k - 1, f, lo):
                out.append((f,) + t)
        f -= 1
    return out


def assign_stages(N: int, D: int, k: int, cap: int, last_driven_min: int | None = None):
    """Pair k drivers (product N) with k driven wheels (product D): minimise the largest single-stage ratio, then the
    total ratio spread, then the largest wheel. If last_driven_min is set, one driven wheel must be >= it (a ring
    gear) and is put in the last stage."""
    best = None
    for dr in factorizations(N, k, cap):
        for dn in factorizations(D, k, cap):
            for perm in sorted(set(itertools.permutations(dn))):
                st = list(zip(dr, perm))
                if last_driven_min is not None:
                    ring = [s for s in st if s[1] >= last_driven_min]
                    if not ring:
                        continue
                    ring_stage = max(ring, key=lambda s: s[1])
                    st.remove(ring_stage)
                    st = sorted(st, key=lambda s: -s[0] / s[1]) + [ring_stage]
                else:
                    st = sorted(st, key=lambda s: -s[0] / s[1])
                logs = [abs(math.log(a / b)) for a, b in st]
                cost = (round(max(logs), 9), round(sum(logs), 9), max(max(s) for s in st), st)
                if best is None or cost < best[0]:
                    best = (cost, st)
    return None if best is None else [list(s) for s in best[1]]


def design_train(r_needed: Fraction, alloc_rel: Fraction, kmax: int = 3, last_driven_min: int | None = None):
    """Smallest number of pairs, then smallest wheels (cap ladder), then smallest error, such that the relative error
    is <= MARGIN * alloc_rel. Returns (choice, alternatives) where alternatives = best train per k at cap 220."""
    r_abs = abs(r_needed)
    rf = float(r_abs)

    def best_at(k, cap):
        for _, N, D in search(rf, k, cap):
            st = assign_stages(N, D, k, cap, last_driven_min)
            if st is not None:
                return (abs(Fraction(N, D) - r_abs) / r_abs, N, D, st, cap)
        return None

    alternatives, choice = {}, None
    for k in range(1, kmax + 1):
        if choice is None:                    # climb the wheel-size ladder until the budget is met
            for cap in CAPS:
                if last_driven_min is not None and cap < last_driven_min:
                    continue
                got = best_at(k, cap)
                if got is not None and got[0] <= alloc_rel * MARGIN:
                    choice = (k,) + got
                    break
        got = best_at(k, CAPS[-1])            # best train with this many pairs, for the study tables
        if got is not None:
            alternatives[k] = got
    if choice is None:   # budget not met: take the best k = kmax train and flag it
        k = max(alternatives)
        choice = (k,) + alternatives[k]
    return choice, alternatives


def factorable(f: Fraction, kmax: int = 3, cap: int = ZMAX):
    """Smallest k (and multiplier m) such that f = (p m)/(q m) with p m, q m products of k teeth in [ZMIN, cap]."""
    import numpy as np
    p, q = f.numerator, f.denominator
    for k in range(1, kmax + 1):
        v, table = products(k, cap)
        M = (table.size - 1) // max(p, q)
        if M < 1:
            continue
        m = np.arange(1, M + 1, dtype=np.int64)
        ok = table[p * m] & table[q * m]
        if ok.any():
            return k, int(m[int(np.argmax(ok))])
    return None


# =====================================================================================================================
# 3. The machine: shafts and their exact mean rates
# =====================================================================================================================

def stages_ratio(stages) -> Fraction:
    num = math.prod(s[0] for s in stages)
    den = math.prod(s[1] for s in stages)
    return Fraction(num, den)


def n_reversals(sh: dict) -> int:
    """External meshes reverse the sense; internal meshes (ring gears) and 1:1 bevel transfers are counted apart."""
    ext = sum(1 for s in sh['stages'] if (s[2] if len(s) > 2 else 'external') == 'external')
    return ext + (1 if sh.get('idler') else 0)


def compute_rates(shafts: list[dict]) -> dict:
    """Exact mean rates (turns per mean solar day) of every shaft, in definition order."""
    R = {}
    for sh in shafts:
        k = sh['kind']
        if k == 'input':
            R[sh['id']] = fr(sh['rate'])
        elif k == 'train':
            R[sh['id']] = sh['sign'] * stages_ratio(sh['stages']) * R[sh['src']]
        elif k in ('diff', 'unit'):
            R[sh['id']] = sum((fr(t['coeff']) * R[t['shaft']] for t in sh['terms']), Fraction(0))
        elif k == 'stepper':
            R[sh['id']] = fr(sh['mean_steps_per_day']) / sh['steps_per_turn'] * (R[sh['src']] if sh.get('src') else 1)
        else:
            raise ValueError(k)
    return R


def check_diff_realisation(sh: dict) -> None:
    """A bevel differential gives carrier = (s1 + s2)/2 ; side gear i is fed through a gain g_i (exact pair, sign),
    the carrier then goes through post pairs. Declared coefficient = 1/2 * g_i * post."""
    rz = sh.get('realisation')
    if not rz:
        return
    post = stages_ratio(rz['post_pairs']) if rz.get('post_pairs') else Fraction(1)
    for t, side in zip(sh['terms'], rz['sides']):
        g = (stages_ratio([side['pair']]) if side.get('pair') else Fraction(1)) * side['sign']
        assert Fraction(1, 2) * g * post == fr(t['coeff']), (sh['id'], t, side)


# =====================================================================================================================
# 4. Design of the whole machine
# =====================================================================================================================

PLANETS = ('mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune')
PLANET_FR = {'mercury': 'Mercure', 'venus': 'Vénus', 'mars': 'Mars', 'jupiter': 'Jupiter', 'saturn': 'Saturne',
             'uranus': 'Uranus', 'neptune': 'Neptune', 'earth': 'Terre'}
KEPLER_UNIT = {'mercury': 'résolveur de Kepler (RK) + ellipse à deux bras', 'venus': 'équant bissecté',
               'earth': 'équant bissecté', 'mars': 'équant + épicyclet (EQE)', 'jupiter': 'équant bissecté',
               'saturn': 'équant bissecté', 'uranus': 'équant bissecté', 'neptune': 'équant bissecté'}

# Allocations: the gear error allowed for each designed train (degrees of mean longitude per century).
ALLOC = {
    'Y': Fraction(1, 1000),          # the Earth feeds every geocentric planet (x 3.6 near Venus) and D = L - Y
    'planet': Fraction(2, 100),      # x 3.7 amplification for Mars at opposition -> <= 0.074 deg geocentric
    'moon_L': Fraction(1, 100),      # eclipses: 0.01 deg/cy on D = 1.2 min of time per century
    'moon_perigee': Fraction(2, 100),
    'moon_node': Fraction(1, 100),
    'ganymede': Fraction(2, 1000), 'nu': Fraction(2, 1000), 'callisto': Fraction(1, 100),
}
ALLOC_REL = {'precession_ring': Fraction(1, 10 ** 4), 'saros': Fraction(1, 10 ** 6), 'gmst_direct': Fraction(1, 10 ** 9)}


def new_shaft(id_, kind, subsystem, name_fr, **kw) -> dict:
    sh = {'id': id_, 'kind': kind, 'subsystem': subsystem, 'name_fr': name_fr}
    sh.update(kw)
    return sh


def train(id_, src, stages, sign, subsystem, name_fr, **kw):
    st = [list(s) + (['external'] if len(s) == 2 else []) for s in stages]
    return new_shaft(id_, 'train', subsystem, name_fr, src=src, stages=st, sign=sign, **kw)


def diff(id_, terms, subsystem, name_fr, realisation=None, **kw):
    return new_shaft(id_, 'diff', subsystem, name_fr,
                     terms=[{'shaft': s, 'coeff': fstr(fr(c))} for s, c in terms], realisation=realisation, **kw)


def unit(id_, terms, subsystem, name_fr, device, **kw):
    return new_shaft(id_, 'unit', subsystem, name_fr, device=device,
                     terms=[{'shaft': s, 'coeff': fstr(fr(c))} for s, c in terms], **kw)


def side(sign=1, pair=None):
    return {'sign': sign, 'pair': pair}


def designed(id_, sources, target_key, T, R, subsystem, name_fr, alloc_deg=None, alloc_rel=None,
             last_driven_min=None, ring_mesh=None, longitude=True, **kw):
    """Design a train for target T[target_key] from the best of the candidate source shafts."""
    tgt = T[target_key]['turns_per_day']
    best = None
    for src in sources:
        r_needed = tgt / R[src]
        a_rel = alloc_rel if alloc_rel is not None else alloc_deg / abs(deg_cy(tgt))
        choice, alts = design_train(r_needed, a_rel, last_driven_min=last_driven_min)
        k, err, N, D, st, cap = choice
        key = (k, cap, err)
        if best is None or key < best[0]:
            best = (key, src, choice, alts, r_needed, a_rel)
    _, src, (k, err, N, D, st, cap), alts, r_needed, a_rel = best
    sign = 1 if r_needed > 0 else -1
    stages = [list(s) + ['external'] for s in st]
    if ring_mesh:
        stages[-1][2] = ring_mesh
    sh = train(id_, src, stages, sign, subsystem, name_fr, target=target_key, longitude=longitude,
               design={'cap': cap, 'pairs': k, 'rel_err_train': float(err), 'alloc_rel': float(a_rel),
                       'alloc_deg_cy': float(alloc_deg) if alloc_deg is not None else None,
                       'r_needed': float(r_needed), 'sources_tried': list(sources),
                       'alternatives': {str(kk): {'cap': v[4], 'stages': v[3], 'ratio': fstr(Fraction(v[1], v[2])),
                                                  'rel_err': float(v[0])} for kk, v in sorted(alts.items())}},
               **kw)
    return sh


def build(C: dict) -> tuple[list[dict], dict]:
    T = load_targets(C)
    S: list[dict] = []
    R: dict = {}

    def put(sh):
        S.append(sh)
        R.update(compute_rates([sh]) if sh['kind'] == 'input' else {})
        if sh['kind'] != 'input':
            R[sh['id']] = compute_rates_one(sh, R)
        return sh

    # ---- time base ------------------------------------------------------------------------------------------------
    put(new_shaft('J', 'input', 'time', 'Arbre-jour J (manivelle ; 1 tour par jour solaire moyen)', rate='1',
                  note='Base de temps de toute la machine. Les jours sont des jours solaires moyens (UT1) ; les '
                       'éphémérides sont en TT : ΔT (~69 s en 2026) n’est pas modélisé.'))
    put(train('W', 'J', [(10, 70)], 1, 'time', 'Roue de la semaine (1 tour en 7 jours)', exact=True))
    # ---- Earth / Sun: the main wheel of the year (sidereal, J2000 frame) -------------------------------------------
    put(designed('Y', ['J'], 'Y', T, R, 'sun', 'Roue de l’année Y : longitude moyenne de la Terre, repère J2000 '
                 '(Soleil moyen = Y + 180°)', alloc_deg=ALLOC['Y']))
    # ---- planets: mean heliocentric longitudes (J2000 frame) from the year wheel ------------------------------------
    for p in PLANETS:
        put(designed(f'{p}_L', ['Y'], f'{p}_L', T, R, 'planets',
                     f'{PLANET_FR[p]} : longitude moyenne héliocentrique (repère J2000)', alloc_deg=ALLOC['planet']))
    # ---- Moon ------------------------------------------------------------------------------------------------------
    put(designed('moon_L', ['J', 'Y'], 'moon_L', T, R, 'moon', 'Lune : longitude moyenne (repère J2000)',
                 alloc_deg=ALLOC['moon_L']))
    put(designed('moon_perigee', ['Y'], 'moon_perigee', T, R, 'moon',
                 'Lune : porte-satellite du périgée ϖ (étage d’anomalie)', alloc_deg=ALLOC['moon_perigee']))
    put(designed('moon_node', ['Y'], 'moon_node', T, R, 'moon',
                 'Lune : porte-nœuds Ω (aiguille du Dragon, étage de réduction, coulisse d’éclipse)',
                 alloc_deg=ALLOC['moon_node']))
    put(diff('evection_carrier', [('Y', 2), ('moon_perigee', -1)], 'moon',
             'Lune : porte-satellite de l’évection 2λ☉ − ϖ (différentiel, sans nouveau rapport approché)',
             realisation={'type': 'bevel', 'sides': [side(1, [80, 20]), side(-1, [40, 20])], 'post_pairs': []},
             target='evection_carrier', longitude=True))
    # ---- precession: the tropical zodiac ring, driven from a slow planetary arbor ----------------------------------
    put(designed('precession_ring', ['neptune_L', 'uranus_L', 'saturn_L', 'moon_node'], 'precession_ring', T, R,
                 'time', 'Anneau du zodiaque tropique (précession ; 1 tour rétrograde en ~25 766 ans)',
                 alloc_rel=ALLOC_REL['precession_ring'], last_driven_min=150, ring_mesh='internal'))
    # ---- sidereal time and equation of time -------------------------------------------------------------------------
    put(diff('sun_trop', [('Y', 1), ('precession_ring', -1)], 'time',
             'Soleil moyen tropique X = Y + p (différentiel)',
             realisation={'type': 'bevel', 'sides': [side(1, [40, 20]), side(-1, [40, 20])], 'post_pairs': []}))
    put(diff('stellar', [('J', 1), ('Y', 1)], 'time',
             'Rotation stellaire S = J + Y (différentiel ; mène le globe-tellurion)',
             realisation={'type': 'bevel', 'sides': [side(1, [40, 20]), side(1, [40, 20])], 'post_pairs': []},
             target='stellar'))
    put(diff('gmst', [('J', 1), ('sun_trop', 1)], 'time',
             'Temps sidéral moyen (TSMG) = J + X (différentiel)',
             realisation={'type': 'bevel', 'sides': [side(1, [40, 20]), side(1, [40, 20])], 'post_pairs': []},
             target='gmst'))
    put(unit('earth_true', [('Y', 1)], 'sun', 'Terre vraie λ (sortie de l’unité de Kepler de la Terre)',
             'unité de Kepler (équant bissecté) : un tour par tour'))
    put(diff('lambda_trop', [('earth_true', 1), ('precession_ring', -1)], 'time',
             'Soleil vrai tropique λ + p (entrée du joint de Hooke)',
             realisation={'type': 'bevel', 'sides': [side(1, [40, 20]), side(-1, [40, 20])], 'post_pairs': []}))
    put(unit('alpha_sun', [('lambda_trop', 1)], 'time', 'Ascension droite vraie du Soleil α (sortie du joint de Hooke)',
             'joint de Hooke plié à ε = 23,44° : tan α = cos ε · tan λ, un tour par tour'))
    put(diff('eot', [('sun_trop', 1), ('alpha_sun', -1)], 'time',
             'Équation du temps EdT = X − α (différentiel ; vitesse moyenne nulle)',
             realisation={'type': 'bevel', 'sides': [side(1, [40, 20]), side(-1, [40, 20])], 'post_pairs': []}))
    put(train('eot_dial', 'eot', [(120, 12)], 1, 'time', 'Aiguille de l’équation du temps (agrandissement ×10)',
              exact=True))
    put(train('tellurion', 'stellar', [(40, 40, 'chain')], 1, 'time',
              'Globe-tellurion de l’orrery (chaîne 1:1 le long du bras de la Terre : angle absolu = S)', exact=True))
    # ---- Gregorian calendar ------------------------------------------------------------------------------------------
    # 303 common years per 400 = 146 097 days: the skip cross makes 303 steps per 146 097 days on average
    put(new_shaft('cal_cross_main', 'stepper', 'calendar', 'Croix de Malte principale (6 fentes ; 1 pas par jour)',
                  src='J', steps_per_turn=6, mean_steps_per_day='1',
                  note='une goupille sur l’arbre-jour : 1/6 de tour par jour, verrouillage positif'))
    put(new_shaft('cal_cross_skip', 'stepper', 'calendar',
                  'Croix de saut (6 fentes ; 1 pas la nuit du 28 février des années communes)',
                  src=None, steps_per_turn=6, mean_steps_per_day='303/146097',
                  note='goupille escamotable, engagée par la logique C4 ∨ (C100 ∧ C400)'))
    put(diff('cal_sum', [('cal_cross_main', Fraction(1, 61)), ('cal_cross_skip', Fraction(1, 61))], 'calendar',
             'Anneau des dates (366 positions) = (croix principale + croix de saut)/61',
             realisation={'type': 'bevel', 'sides': [side(1), side(1)], 'post_pairs': [[20, 61], [20, 200]]},
             note='différentiel puis 20:61 et 20:200 (l’anneau porte 200 dents intérieures)'))
    put(train('cal_prog4', 'cal_sum', [(15, 60)], 1, 'calendar', 'Roue-programme de 4 ans (came C4)', exact=True))
    put(train('cal_prog100', 'cal_prog4', [(12, 60), (12, 60)], 1, 'calendar', 'Roue-programme de 100 ans (came C100)',
              exact=True))
    put(train('cal_prog400', 'cal_prog100', [(15, 60)], 1, 'calendar', 'Roue-programme de 400 ans (came C400)',
              exact=True))
    # ---- planets: units, modules, orrery, special arms ---------------------------------------------------------------
    for p in PLANETS:
        put(unit(f'{p}_true', [(f'{p}_L', 1)], 'planets', f'{PLANET_FR[p]} vraie (sortie de l’unité de Kepler)',
                 KEPLER_UNIT[p] + ' : un tour par tour'))
    for p in PLANETS:
        inner = p in ('mercury', 'venus')
        put(unit(f'{p}_geo', [('Y', 1)] if inner else [(f'{p}_L', 1)], 'planets',
                 f'{PLANET_FR[p]} : aiguille géocentrique (module vectoriel)',
                 'module vectoriel (suiveur) : en moyenne ' + ('le Soleil (planète intérieure)' if inner else
                                                              'la planète (planète extérieure)')))
    put(unit('sun_geo', [('earth_true', 1)], 'sun', 'Soleil vrai : aiguille géocentrique (= Terre vraie + 180°)',
             'renvoi 1:1'))
    for p in ('earth',) + PLANETS:
        src = 'earth_true' if p == 'earth' else f'{p}_true'
        put(train(f'orrery_{p}', src, [(40, 40, 'bevel')], 1, 'orrery',
                  f'Orrery : tube de {PLANET_FR[p]} (renvoi d’angle 1:1 vers le couvercle)', exact=True))
    put(train('mars_epicyclet', 'mars_L', [(60, 20)], 1, 'planets',
              'Mars : épicyclet correcteur (angle absolu 3L − 2ϖ, ϖ figé : couple 3:1)', exact=True))
    put(unit('mercury_E', [('mercury_L', 1)], 'planets', 'Mercure : arbre de l’anomalie excentrique E (résolveur)',
             'boucle M = E − e sin E : un tour par tour'))
    put(train('mercury_counter_arm', 'mercury_E', [(40, 40, 'bevel')], -1, 'planets',
              'Mercure : bras (a − b)/2 à l’angle ϖ − E (inverseur conique coaxial 1:1)', exact=True,
              note='inverseur conique coaxial = différentiel à porte-satellite fixe : sortie = −E (+ 2ϖ, ϖ figé)'))
    # ---- Moon units ---------------------------------------------------------------------------------------------------
    put(diff('annual_eq', [('earth_true', Fraction(3, 31)), ('Y', Fraction(-3, 31))], 'moon',
             'Lune : moteur de l’équation annuelle (3/31)(λ☉ vrai − λ☉ moyen) (vitesse moyenne nulle)',
             realisation={'type': 'bevel', 'sides': [side(1), side(-1)], 'post_pairs': [[30, 155]]},
             note='amplitude visée 0,185116/1,914602 = 0,096686 ; 3/31 = 0,096774 (écart 0,09 % de 0,185° = 0,0002°)'))
    put(unit('moon_true', [('moon_L', 1)], 'moon', 'Lune vraie : aiguille (sortie de la cascade à 5 étages)',
             'cascade réduction → équation annuelle → évection → anomalie (équant) → variation : un tour par tour'))
    put(unit('moon_phase', [('moon_true', 1), ('sun_geo', -1)], 'moon',
             'Boule de phase (rotation relative à l’aiguille de la Lune = Lune vraie − Soleil vrai)',
             'couronne 1:1 (48:48) menée par le tube du Soleil vrai'))
    # ---- eclipses -----------------------------------------------------------------------------------------------------
    put(designed('saros', ['J', 'Y', 'moon_L'], 'saros', T, R, 'eclipses', 'Aiguille du Saros (1 tour = 223 lunaisons)',
                 alloc_rel=ALLOC_REL['saros'], longitude=False))
    put(train('exeligmos', 'saros', [(20, 60)], 1, 'eclipses', 'Aiguille de l’Exeligmos (1 tour = 3 Saros)', exact=True,
              target='exeligmos'))
    # ---- Galilean moons: the Laplace box ------------------------------------------------------------------------------
    put(designed('ganymede', ['J'], 'ganymede', T, R, 'galilean', 'Ganymède (train direct)', alloc_deg=ALLOC['ganymede']))
    put(designed('nu', ['J'], 'nu', T, R, 'galilean', 'Arbre ν = n_Io − 2n_Eu (ligne des conjonctions à −ν)',
                 alloc_deg=ALLOC['nu'], longitude=False))
    put(diff('europa', [('ganymede', 2), ('nu', 1)], 'galilean', 'Europe = 2·Ganymède + ν (différentiel)',
             realisation={'type': 'bevel', 'sides': [side(1, [80, 20]), side(1, [40, 20])], 'post_pairs': []},
             target='europa', longitude=True))
    put(diff('io', [('europa', 2), ('nu', 1)], 'galilean', 'Io = 2·Europe + ν (différentiel)',
             realisation={'type': 'bevel', 'sides': [side(1, [80, 20]), side(1, [40, 20])], 'post_pairs': []},
             target='io', longitude=True))
    put(designed('callisto', ['J'], 'callisto', T, R, 'galilean', 'Callisto (train direct, hors résonance)',
                 alloc_deg=ALLOC['callisto']))
    # ---- options and variants (not in the baseline machine) -----------------------------------------------------------
    put(designed('gmst_direct', ['J'], 'gmst', T, R, 'options',
                 'Variante : temps sidéral par un train direct depuis J (au lieu du différentiel)',
                 alloc_rel=ALLOC_REL['gmst_direct'], longitude=False, optional=True))
    put(diff('synodic', [('moon_L', 1), ('Y', -1)], 'options',
             'Variante : arbre synodique moyen D = L − Y (différentiel)',
             realisation={'type': 'bevel', 'sides': [side(1, [40, 20]), side(-1, [40, 20])], 'post_pairs': []},
             target='moon_D', optional=True))
    put(train('saros_223', 'synodic', [(20, 223), (10, 200)], 1, 'options',
              'Variante : Saros exact avec une roue de 223 dents (hommage à b1)', exact=True, optional=True,
              target='saros', exception='223 dents > 220 : nombre premier, exigé par le Saros exact (comme b1 de 223 '
                                        'dents dans la machine antique)'))
    put(designed('mars_apsides', ['precession_ring'], 'mars_apsides', T, R, 'options',
                 'Option : plateau d’apsides de Mars (1 tour en ~81 000 ans)', alloc_rel=Fraction(1, 100),
                 optional=True))
    return S, T


def compute_rates_one(sh: dict, R: dict) -> Fraction:
    tmp = dict(R)
    k = sh['kind']
    if k == 'train':
        return sh['sign'] * stages_ratio(sh['stages']) * tmp[sh['src']]
    if k in ('diff', 'unit'):
        return sum((fr(t['coeff']) * tmp[t['shaft']] for t in sh['terms']), Fraction(0))
    if k == 'stepper':
        return fr(sh['mean_steps_per_day']) / sh['steps_per_turn'] * (tmp[sh['src']] if sh.get('src') else 1)
    raise ValueError(k)


# =====================================================================================================================
# 5. Physical senses (idlers), modules, wheel sizes
# =====================================================================================================================

def finalize(S: list[dict], T: dict) -> dict:
    """Exact rates, then physical senses: phys = sense of rotation seen from the front (+1 = clockwise = prograde,
    as on the v1 front dial). Longitude shafts must turn prograde when their rate is positive. J's sense is chosen
    so that the year wheel Y needs no idler; trains that would come out the wrong way get one idler (20 teeth).
    Then modules and pitch sizes."""
    R = compute_rates(S)
    by = {s['id']: s for s in S}
    # senses
    for sh in S:
        sh['rate_sign'] = 1 if R[sh['id']] > 0 else (-1 if R[sh['id']] < 0 else 0)
    rev_Y = n_reversals(by['Y'])
    by['J']['phys'] = (-1) ** rev_Y
    for sh in S:
        if sh['kind'] == 'input':
            continue
        need = sh['rate_sign'] if sh.get('longitude') else None
        if sh['kind'] == 'train' and sh['stages'][0][2] in ('external', 'internal'):
            src_phys = by[sh['src']].get('phys')
            if src_phys is None:
                sh['phys'] = None
                continue
            phys = src_phys * (-1) ** n_reversals(sh)
            if need is not None and phys != need and not sh.get('idler'):
                sh['idler'] = 20
                phys = -phys
            sh['phys'] = phys
            if need is not None:
                assert phys == need, sh['id']
        elif sh['kind'] in ('unit',) and len(sh['terms']) == 1:
            sh['phys'] = by[sh['terms'][0]['shaft']].get('phys')
        elif sh['kind'] == 'diff' and need is not None:
            sh['phys'] = need                    # the input senses are set by the realisation (idlers as needed)
        else:
            sh['phys'] = None
    # modules and sizes
    for sh in S:
        if sh['kind'] != 'train':
            continue
        mods, info = [], []
        for z1, z2, mesh in sh['stages']:
            m = MODULE_DEFAULT
            if mesh == 'internal':
                m = Fraction(4, 5) if sh['id'] == 'precession_ring' else Fraction(9, 10)
            mods.append(fstr(m))
            cd = m * (z2 - z1) / 2 if mesh == 'internal' else m * (z1 + z2) / 2
            info.append({'pitch_d_mm': [float(m * z1), float(m * z2)], 'centre_distance_mm': float(cd)})
        sh['modules_mm'] = mods
        sh['geometry'] = info
    if 'cal_sum' in by:
        by['cal_sum']['realisation']['post_modules_mm'] = ['1/2', '9/10']
    return R


# =====================================================================================================================
# 6. Gregorian calendar: exact simulation of the cams
# =====================================================================================================================

def gregorian_check(y_from=1582, y_to=6000, epoch=2000, read_pos=58, positions=366):
    """Ring of 366 positions (1 turn per civil year), program wheels 1:4, 1:100, 1:400 of the ring (exact pairs),
    cams centred on the reading instant (ring at 28 Feb, position 58). Skip 29 Feb iff C4 or (C100 and C400)."""
    rho = Fraction(read_pos, positions)

    def in_arc(a, lo, hi):           # a, lo, hi in turns; arc from lo to hi (mod 1)
        a, lo, hi = a % 1, lo % 1, hi % 1
        return lo <= a <= hi if lo <= hi else (a >= lo or a <= hi)

    def margin(a, lo, hi):
        a = a % 1
        d = min((a - lo) % 1, (hi - a) % 1)
        return d

    arcs = {
        'C4': ((1 + rho) / 4 - Fraction(1, 8), (3 + rho) / 4 + Fraction(1, 8)),
        'C100': (rho / 100 - Fraction(1, 200), rho / 100 + Fraction(1, 200)),
        'C400': ((1 + rho / 100) / 4 - Fraction(1, 8), (3 + rho / 100) / 4 + Fraction(1, 8)),
    }
    errors, min_margin = [], {'C4': Fraction(1), 'C100': Fraction(1), 'C400': Fraction(1)}
    for Y in range(y_from, y_to + 1):
        n = Y - epoch
        ring = n + rho
        a = {'C4': ring / 4, 'C100': ring / 100, 'C400': ring / 400}
        st = {c: in_arc(a[c], *arcs[c]) for c in arcs}
        skip = st['C4'] or (st['C100'] and st['C400'])
        leap = Y % 4 == 0 and (Y % 100 != 0 or Y % 400 == 0)
        if skip == leap:
            errors.append(Y)
        # margins: distance of the reading angle to the nearest cam edge (on the side it is read)
        for c in ('C4', 'C100'):
            lo, hi = arcs[c]
            d = margin(a[c], lo, hi) if st[c] else margin(a[c], hi, lo)
            min_margin[c] = min(min_margin[c], d)
        if n % 100 == 0:
            lo, hi = arcs['C400']
            d = margin(a['C400'], lo, hi) if st['C400'] else margin(a['C400'], hi, lo)
            min_margin['C400'] = min(min_margin['C400'], d)
    return {'years': [y_from, y_to], 'errors': errors,
            'min_margin_deg': {c: float(v * 360) for c, v in min_margin.items()},
            'arcs_turns': {c: [fstr(lo % 1), fstr(hi % 1)] for c, (lo, hi) in arcs.items()},
            'reading_position': read_pos, 'positions': positions}


def gregorian_daywise(y_from=1600, y_to=2400, epoch=2000, read_pos=58, positions=366):
    """Day-by-day run of the mechanism: the ring advances 1 position per day (main cross) and 1 more on the night of
    28 Feb when the cams, read at the ring's ACTUAL angle (exact fraction of turns), say "skip". The date engraved under
    the ring index must equal the real (proleptic Gregorian) date every day; the week wheel (1/7 turn per day) must
    show the real weekday."""
    import datetime as dt
    rho = Fraction(read_pos, positions)
    arcs = {'C4': ((1 + rho) / 4 - Fraction(1, 8), (3 + rho) / 4 + Fraction(1, 8)),
            'C100': (rho / 100 - Fraction(1, 200), rho / 100 + Fraction(1, 200)),
            'C400': ((1 + rho / 100) / 4 - Fraction(1, 8), (3 + rho / 100) / 4 + Fraction(1, 8))}

    def in_arc(a, lo, hi):
        a, lo, hi = a % 1, lo % 1, hi % 1
        return lo <= a <= hi if lo <= hi else (a >= lo or a <= hi)

    month_len = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ring_dates = [(m + 1, d + 1) for m in range(12) for d in range(month_len[m])]
    assert len(ring_dates) == positions and ring_dates[read_pos] == (2, 28)
    day = dt.date(y_from, 1, 1)
    end = dt.date(y_to, 1, 1)
    steps = (y_from - epoch) * positions          # ring steps since 1 Jan of the epoch (1 turn = 366 steps)
    n_days = (day - dt.date(epoch, 1, 1)).days    # day count since the epoch (week wheel)
    wrong_dates, wrong_weekdays, days = 0, 0, 0
    while day < end:
        if ring_dates[steps % positions] != (day.month, day.day):
            wrong_dates += 1
        if (5 + n_days) % 7 != day.weekday():     # 1 Jan 2000 was a Saturday (weekday() = 5)
            wrong_weekdays += 1
        step = 1
        if steps % positions == read_pos:
            ring = Fraction(steps, positions)
            c4 = in_arc(ring / 4, *arcs['C4'])
            c100 = in_arc(ring / 100, *arcs['C100'])
            c400 = in_arc(ring / 400, *arcs['C400'])
            if c4 or (c100 and c400):
                step = 2                          # the skip cross adds one position: 28 Feb -> 1 Mar
        steps += step
        n_days += 1
        days += 1
        day += dt.timedelta(days=1)
    return {'years': [y_from, y_to], 'days': days, 'wrong_dates': wrong_dates, 'wrong_weekdays': wrong_weekdays}


# =====================================================================================================================
# 7. Evaluation, budgets, Lean candidates
# =====================================================================================================================

def evaluate(S: list[dict], T: dict, R: dict) -> dict:
    ty = T['_tropical_year_days']
    out = {}
    for sh in S:
        key = sh.get('target')
        if not key or key not in T:
            continue
        tg = T[key]['turns_per_day']
        m = R[sh['id']]
        rel = (m - tg) / tg
        ev = {'target': key, 'machine_turns_per_day': fstr(m), 'target_turns_per_day': fstr(tg),
              'rel_err': float(rel), 'ppm': float(rel * 10 ** 6),
              'machine_turns_per_tropical_year': float(m * ty), 'target_turns_per_tropical_year': float(tg * ty)}
        if m != 0:
            ev['machine_period_days'] = float(1 / abs(m))
            ev['target_period_days'] = float(1 / abs(tg))
            ev['period_diff_s'] = float((1 / abs(m) - 1 / abs(tg)) * 86400)
        if key in ('gmst', 'stellar'):
            ev['err_s_per_century'] = float((m - tg) * 86400 * DAYS_PER_CY)
        else:
            d = deg_cy(m - tg)
            ev['deg_per_century'] = float(d)
            ev['years_to_1deg'] = float(100 / abs(d)) if d != 0 else None
        out[sh['id']] = ev
    # derived lunar arguments
    for name, a, b, key in (('D', 'moon_L', 'Y', 'moon_D'), ('F', 'moon_L', 'moon_node', 'moon_F'),
                            ('Mp', 'moon_L', 'moon_perigee', 'moon_Mp')):
        m = R[a] - R[b]
        tg = T[key]['turns_per_day']
        out[f'moon_{name}'] = {'target': key, 'machine_turns_per_day': fstr(m), 'target_turns_per_day': fstr(tg),
                               'rel_err': float((m - tg) / tg), 'ppm': float((m - tg) / tg * 10 ** 6),
                               'deg_per_century': float(deg_cy(m - tg)),
                               'machine_period_days': float(1 / abs(m)), 'target_period_days': float(1 / abs(tg)),
                               'period_diff_s': float((1 / abs(m) - 1 / abs(tg)) * 86400),
                               'machine_turns_per_tropical_year': float(m * ty),
                               'target_turns_per_tropical_year': float(tg * ty),
                               'years_to_1deg': float(100 / abs(deg_cy(m - tg))) if m != tg else None,
                               'expr': f'ω {a} − ω {b}'}
    # tropical (zodiac) readings: pointer - ring
    out['_zodiac_note'] = ('Lecture tropique = aiguille (repère J2000) − anneau ; l’erreur tropique vaut l’erreur de '
                           'l’aiguille + l’erreur de l’anneau (%.2e °/siècle).' % abs(out['precession_ring']['deg_per_century']))
    return out


def geocentric_bounds(T: dict, ev: dict) -> dict:
    """Worst-case geocentric drift per century due to the gear errors only: |dp| r_p/Delta_min + |dE| r_E/Delta_min."""
    el = T['_elements']
    aE, eE = (float(x) for x in el['earth'])
    dE = abs(ev['Y']['deg_per_century'])
    res = {}
    for p in PLANETS:
        a, e = (float(x) for x in el[p])
        dp = abs(ev[f'{p}_L']['deg_per_century'])
        if p in ('mercury', 'venus'):
            dmin = aE * (1 - eE) - a * (1 + e)
            Ap, AE = a * (1 + e) / dmin, aE * (1 - eE) / dmin
        else:
            dmin = a * (1 - e) - aE * (1 + eE)
            Ap, AE = a * (1 - e) / dmin, aE * (1 + eE) / dmin
        res[p] = {'delta_min_au': dmin, 'amp_planet': Ap, 'amp_earth': AE, 'bound_deg_per_century': Ap * dp + AE * dE}
    return res


def budgets(S, T, R, ev, geo, greg) -> list[dict]:
    """All asserted budgets. Each entry: name, value, limit, kind, ok."""
    A = []

    def add(name, value, limit, kind='<=', note=''):
        ok = (abs(value) <= limit) if kind == '<=' else (value == limit)
        A.append({'name': name, 'value': value, 'limit': limit, 'kind': kind, 'ok': bool(ok), 'note': note})

    def frn(x):
        return f'{float(x):g}'.replace('.', ',')

    # task budgets
    def nm(k):
        return SHORT.get(k, PLANET_FR.get(k, k))

    for k in ('Y',) + tuple(f'{p}_L' for p in PLANETS):
        add(f'tâche : {nm(k)} < 1°/siècle', ev[k]['deg_per_century'], 1.0)
    for k in ('moon_L', 'moon_D', 'moon_F', 'moon_Mp', 'moon_node', 'moon_perigee'):
        add(f'tâche : {nm(k)} < 2°/siècle', ev[k]['deg_per_century'], 2.0)
    prec_period_err = ev['precession_ring']['rel_err']
    add('tâche : période de précession à 0,5 % près', prec_period_err, 0.005)
    # internal (tighter) budgets
    for k in ('Y', 'mars_L', 'venus_L'):
        add(f'étude des mécanismes : {nm(k)} ≤ 0,1°/siècle', ev[k]['deg_per_century'], 0.1)
    for k, a in (('Y', ALLOC['Y']),) + tuple((f'{p}_L', ALLOC['planet']) for p in PLANETS) + \
            (('moon_L', ALLOC['moon_L']), ('moon_perigee', ALLOC['moon_perigee']), ('moon_node', ALLOC['moon_node']),
             ('ganymede', ALLOC['ganymede']), ('nu', ALLOC['nu']), ('callisto', ALLOC['callisto'])):
        add(f'allocation : {nm(k)} ≤ {frn(a)}°/siècle', ev[k]['deg_per_century'], float(a))
    for p in PLANETS:
        add(f'géocentrique (engrenages seuls) : {nm(p)} ≤ 0,1°/siècle', geo[p]['bound_deg_per_century'], 0.1)
    for k, n_ in (('io', 'Io'), ('europa', 'Europe')):
        add(f'lunes galiléennes : {n_} ≤ 0,02°/siècle', ev[k]['deg_per_century'], 0.02)
    add('temps sidéral ≤ 1 s/siècle', ev['gmst']['err_s_per_century'], 1.0)
    add('Saros ≤ 10⁻⁶ relatif', ev['saros']['rel_err'], 1e-6)
    add('Mercure ≤ 0,05°/siècle', ev['mercury_L']['deg_per_century'], 0.05)
    # exact identities
    add('identité : Io − 3·Europe + 2·Ganymède = 0', float(R['io'] - 3 * R['europa'] + 2 * R['ganymede']), 0.0, '==')
    add('identité : évection = 2Y − ϖ', float(R['evection_carrier'] - (2 * R['Y'] - R['moon_perigee'])), 0.0, '==')
    pr = -R['precession_ring']
    add('identité : TSMG = J + Y + p', float(R['gmst'] - (R['J'] + R['Y'] + pr)), 0.0, '==')
    add('identité : vitesse moyenne de l’EdT = 0', float(R['eot']), 0.0, '==')
    add('identité : vitesse moyenne de l’équation annuelle = 0', float(R['annual_eq']), 0.0, '==')
    add('exact : semaine = 1/7 tour par jour', float(R['W'] - Fraction(1, 7)), 0.0, '==')
    add('exact : 146 097 jours = 20 871 semaines', float(Fraction(146097, 7) - 20871), 0.0, '==')
    add('exact : anneau des dates = 400/146 097 tour par jour (1 tour par année civile)',
        float(R['cal_sum'] - Fraction(400, 146097)), 0.0, '==')
    add('exact : roues-programmes 1/4, 1/100, 1/400 de l’anneau',
        float(max(abs(R['cal_prog4'] - R['cal_sum'] / 4), abs(R['cal_prog100'] - R['cal_sum'] / 100),
                  abs(R['cal_prog400'] - R['cal_sum'] / 400))), 0.0, '==')
    for p in PLANETS:
        want = R['Y'] if p in ('mercury', 'venus') else R[f'{p}_L']
        add(f'exact : vitesse moyenne de l’aiguille géocentrique ({nm(p)})', float(R[f'{p}_geo'] - want), 0.0, '==')
    add('exact : Exeligmos = Saros/3', float(R['exeligmos'] - R['saros'] / 3), 0.0, '==')
    add('grégorien : années fausses 1582–6000', len(greg['errors']), 0, '==')
    dw = greg['daywise']
    add(f"grégorien jour par jour {dw['years'][0]}–{dw['years'][1]} ({dw['days']:,} jours) : dates fausses".replace(',', ' '),
        dw['wrong_dates'], 0, '==')
    add(f"semaine jour par jour {dw['years'][0]}–{dw['years'][1]} : jours faux", dw['wrong_weekdays'], 0, '==')
    # tooth counts, modules
    bad = []
    for sh in S:
        if sh['kind'] == 'train':
            for z1, z2, _ in sh['stages']:
                if not (ZMIN <= z1 <= ZMAX and ZMIN <= z2 <= ZMAX) and not sh.get('exception'):
                    bad.append((sh['id'], z1, z2))
            for m in sh.get('modules_mm', []):
                assert fr(m) >= MODULE_MIN, (sh['id'], m)
        rz = sh.get('realisation') or {}
        for pair in [s['pair'] for s in rz.get('sides', []) if s.get('pair')] + rz.get('post_pairs', []):
            if not (ZMIN <= pair[0] <= ZMAX and ZMIN <= pair[1] <= ZMAX):
                bad.append((sh['id'], *pair))
    add('dentures hors [10, 220] sans exception déclarée', len(bad), 0, '==')
    return A


def lean_candidates(S, T, R, ev) -> list[dict]:
    L = []
    for sh in S:
        if sh['kind'] == 'train':
            L.append({'kind': 'ratio', 'shaft': sh['id'],
                      'statement': f"ω {sh['id']} = ({'-' if sh['sign'] < 0 else ''}{'·'.join(str(s[0]) for s in sh['stages'])}"
                                   f" / {'·'.join(str(s[1]) for s in sh['stages'])}) · ω {sh['src']}",
                      'rate_vs_J': fstr(R[sh['id']])})
        elif sh['kind'] in ('diff', 'unit'):
            L.append({'kind': 'identity' if sh['kind'] == 'diff' else 'mean_rate', 'shaft': sh['id'],
                      'statement': f"ω {sh['id']} = " + ' + '.join(f"({t['coeff']})·ω {t['shaft']}" for t in sh['terms']),
                      'rate_vs_J': fstr(R[sh['id']])})
    for k, e in ev.items():
        if k.startswith('_') or 'deg_per_century' not in e:
            continue
        lim = 10.0 ** (math.floor(math.log10(max(abs(e['deg_per_century']), 1e-12))) + 1)
        lhs = f"({e['expr']})" if e.get('expr') else f'ω {k}'
        L.append({'kind': 'bound', 'shaft': k,
                  'statement': f"|{lhs} − cible| · 360 · 36525 < {lim:g}  (cible = {e['target_turns_per_day']} tr/j, "
                               f"décimale exacte de constants.json)"})
    L += [
        {'kind': 'identity', 'shaft': 'io', 'statement': 'ω io − 3 ω europa + 2 ω ganymede = 0 (Laplace, exact par construction)'},
        {'kind': 'identity', 'shaft': 'eot', 'statement': 'vitesse moyenne de l’équation du temps = 0'},
        {'kind': 'identity', 'shaft': 'gmst', 'statement': 'ω gmst = ω J + ω Y − ω precession_ring'},
        {'kind': 'decide', 'shaft': 'calendar', 'statement': 'pour tout n : saute(n) ↔ ¬ bissextile(2000 + n) '
                                                              '(400 cas par decide + périodicité de 400 ans des trois cames)'},
        {'kind': 'decide', 'shaft': 'W', 'statement': '146097 = 7 · 20871'},
    ]
    return L


# =====================================================================================================================
# 8. Writers: JSON spec and French study
# =====================================================================================================================

def to_json(S, T, R, ev, geo, greg, A, L, meta) -> dict:
    shafts = []
    for sh in S:
        d = {k: v for k, v in sh.items() if k not in ('rate_sign',)}
        d['rate_turns_per_day'] = fstr(R[sh['id']])
        d['rate_turns_per_tropical_year'] = float(R[sh['id']] * T['_tropical_year_days'])
        if sh['kind'] == 'train':
            d['ratio'] = fstr(sh['sign'] * stages_ratio(sh['stages']))
            d['n_reversals'] = n_reversals(sh)
        shafts.append(d)
    targets = {}
    for k, v in T.items():
        if k.startswith('_'):
            continue
        targets[k] = {'turns_per_day': fstr(v['turns_per_day']), 'turns_per_day_float': float(v['turns_per_day']),
                      'turns_per_tropical_year': float(v['turns_per_day'] * T['_tropical_year_days']),
                      'source': v['source'], 'name_fr': v['name_fr']}
        if 'deg_per_cy' in v:
            targets[k]['deg_per_century'] = float(v['deg_per_cy'])
        if v.get('uncert_deg_cy') is not None:
            targets[k]['rate_uncertainty_deg_per_century'] = float(v['uncert_deg_cy'])
    return {
        'meta': meta,
        'conventions': {
            'time_base': 'J = arbre-jour, 1 tour par jour solaire moyen (entrée). Toutes les vitesses sont des fractions '
                         'exactes de tours par jour ; « tr/an » = × année tropique moyenne (%s j).' % float(T['_tropical_year_days']),
            'frame': 'Repère fixe J2000 (étoiles, caisse) pour tous les trains ; le zodiaque tropique est un anneau qui '
                     'tourne à −p_A. Lecture tropique = aiguille − anneau.',
            'sign': 'Signe des vitesses : + = sens direct (longitudes croissantes). phys = sens vu de face '
                    '(+1 = horaire, le sens direct du cadran avant, comme la v1). Pignon fou (idler) ajouté quand un '
                    'train sortirait dans le mauvais sens.',
            'stages': '[menante, menée, engrènement] ; rapport = Π menantes / Π menées × signe',
            'differential': 'différentiel conique : porte-satellite = (s1 + s2)/2 ; chaque côté reçoit un gain exact '
                            '(couple 40:20 = 2, 80:20 = 4, signe par pignon fou) ; post_pairs après le porte-satellite.',
            'unit': 'unité non linéaire (Kepler, module vectoriel, cascade lunaire, joint de Hooke) : un tour de sortie '
                    'par tour d’entrée, donc vitesse moyenne = combinaison linéaire exacte des entrées.',
            'error': 'erreur relative = (machine − cible)/cible ; °/siècle = (machine − cible) × 360 × 36 525 ; '
                     'période de l’approximation = 1/|vitesse machine| (jours).',
            'teeth': '[%d, %d] dents ; module ≥ %s mm (0,5 mm par défaut ; anneaux à denture intérieure 0,8–0,9 mm).'
                     % (ZMIN, ZMAX, float(MODULE_MIN)),
            'selection': 'pour chaque train conçu : le plus petit nombre de couples, puis la plus petite roue (échelle '
                         '%s dents), puis la plus petite erreur, avec erreur ≤ %s × allocation.' % (list(CAPS), float(MARGIN)),
        },
        'allocations_deg_per_century': {k: float(v) for k, v in ALLOC.items()},
        'allocations_relative': {k: float(v) for k, v in ALLOC_REL.items()},
        'targets': targets,
        'shafts': shafts,
        'evaluation': ev,
        'geocentric_bounds': geo,
        'gregorian_simulation': greg,
        'budgets': A,
        'lean_candidates': L,
        'shared_arbors': {k: [{'train': i, 'first_driver_teeth': z} for i, z in v] for k, v in shared_arbors(S).items()},
        'inventory': inventory(S),
    }


def fnum(x, nd=3, sign=False):
    """French number: decimal comma, thousands grouped by spaces (as in the other v2 documents)."""
    if x is None:
        return '—'
    s = f"{float(x):+,.{nd}f}" if sign else f"{float(x):,.{nd}f}"
    return s.replace(',', ' ').replace('.', ',').replace('-', '−')


def fint(n: int) -> str:
    return f'{n:,}'.replace(',', ' ')


SUP = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')


def fsci(x, nd=2):
    if x is None:
        return '—'
    x = float(x)
    if x == 0:
        return '0'
    e = int(math.floor(math.log10(abs(x))))
    m = x / 10 ** e
    if round(abs(m), nd) >= 10:
        m /= 10
        e += 1
    s = f"{m:.{nd}f}".replace('.', ',').replace('-', '−')
    return s if e == 0 else f"{s}·10{str(e).translate(SUP)}"


def fdeg(x):
    """deg/century, readable."""
    if x is None:
        return '—'
    ax = abs(float(x))
    if ax == 0:
        return '0'
    if ax >= 0.01:
        return fnum(x, 3, sign=True)
    return fsci(x, 1) if x < 0 else '+' + fsci(x, 1)


def teeth_str(sh):
    st = sh['stages']
    s = ' · '.join(f"{a}:{b}" + (' (int.)' if m == 'internal' else '') for a, b, m in st)
    if sh.get('idler'):
        s += f" + pignon fou {sh['idler']}"
    return s


def period_str(days):
    if days is None:
        return '—'
    if days < 2:
        return fnum(days, 6) + ' j'
    if days < 1000:
        return fnum(days, 5) + ' j'
    yrs = days / 365.2421896698
    return f"{fnum(days, 2)} j ({fnum(yrs, 3)} a)"


SHORT = {'W': 'semaine', 'Y': 'roue de l’année Y', 'mercury_L': 'Mercure', 'venus_L': 'Vénus', 'mars_L': 'Mars',
         'jupiter_L': 'Jupiter', 'saturn_L': 'Saturne', 'uranus_L': 'Uranus', 'neptune_L': 'Neptune',
         'moon_L': 'Lune L', 'moon_perigee': 'périgée ϖ', 'moon_node': 'nœuds Ω', 'precession_ring': 'anneau du zodiaque',
         'saros': 'Saros', 'exeligmos': 'Exeligmos', 'ganymede': 'Ganymède', 'nu': 'ν', 'callisto': 'Callisto',
         'eot_dial': 'aiguille de l’EdT', 'tellurion': 'globe-tellurion', 'cal_prog4': 'programme 4 ans',
         'cal_prog100': 'programme 100 ans', 'cal_prog400': 'programme 400 ans', 'mars_epicyclet': 'épicyclet de Mars',
         'mercury_counter_arm': 'bras inverse de Mercure', 'moon_D': 'Lune D', 'moon_F': 'Lune F',
         'moon_Mp': 'Lune M′', 'gmst_direct': 'TSMG direct (variante)', 'mars_apsides': 'apsides de Mars (option)',
         'cal_sum': 'anneau des dates', 'annual_eq': 'équation annuelle (gain 3/31)', 'gmst': 'temps sidéral',
         'sun_trop': 'Soleil moyen tropique', 'stellar': 'rotation stellaire', 'europa': 'Europe', 'io': 'Io',
         'evection_carrier': 'porte-satellite de l’évection', 'eot': 'EdT'}
SRC_PHRASE = {'Y': 'la roue de l’année Y', 'J': 'l’arbre-jour J', 'moon_L': 'l’arbre de la Lune'}


def flim(x):
    if isinstance(x, int):
        return str(x)
    if x != 0 and abs(x) < 1e-3:
        return fsci(x, 0)
    return f'{x:g}'.replace('.', ',')


def dt_str(s):
    if s is None:
        return '—'
    if abs(s) >= 86400:
        return fnum(s / 86400, 3, True) + ' j'
    if abs(s) >= 600:
        return fnum(s / 60, 1, True) + ' min'
    return fnum(s, 3, True) + ' s'


def fval(x):
    if isinstance(x, int):
        return str(x)
    if x == 0:
        return '0'
    if abs(x) < 1e-3:
        return fsci(x, 2)
    return fnum(x, 4)


def diagram(S) -> list[str]:
    """Text tree of the baseline gear trains, grouped by source shaft and number of pairs (from the actual design)."""
    by_id = {s['id']: s for s in S}
    order, groups = [], {}
    for sh in S:
        if sh['kind'] != 'train' or sh.get('optional') or sh['subsystem'] == 'orrery':
            continue
        if sh['stages'][0][2] in ('bevel', 'chain'):
            continue
        src = sh['src']
        if src not in groups:
            order.append(src)
            groups[src] = {}
        k = len(sh['stages'])
        groups[src].setdefault((k, bool(sh.get('design'))), []).append(sh['id'])
    name = {'J': 'J  (manivelle, 1 tour par jour)', 'Y': 'Y  (roue de l’année, repère J2000)',
            'neptune_L': 'Neptune', 'saros': 'Saros', 'eot': 'EdT', 'cal_sum': 'anneau des dates',
            'cal_prog4': 'programme 4 ans', 'cal_prog100': 'programme 100 ans', 'mars_L': 'Mars'}
    out = []
    exact_lines = []
    for src in list(order):
        if all(not des for (k, des) in groups[src]) and src != 'J':
            for (k, des), ids in groups[src].items():
                for i in ids:
                    exact_lines.append(f"{name.get(src, SHORT.get(src, src))} → {SHORT.get(i, i)} ({teeth_str(by_id[i])})")
            order.remove(src)
    for src in order:
        out.append(name.get(src, SHORT.get(src, src)))
        items = sorted(groups[src].items(), key=lambda kv: (not kv[0][1], kv[0][0]))
        extra = ['croix de Malte (1/6 par jour) + croix de saut → Σ → 20:61 · 20:200 → anneau des dates'] if src == 'J' else []
        lines = []
        for (k, des), ids in items:
            lab = ', '.join(SHORT.get(i, i) for i in ids)
            lines.append(f"{k} couple{'s' if k > 1 else ''}{' (approché)' if des else ' (exact)'} → {lab}")
        lines += extra
        for i, l in enumerate(lines):
            out.append((' └─ ' if i == len(lines) - 1 else ' ├─ ') + l)
    out.append('rapports entiers (exacts) :')
    out += ['  ' + l for l in exact_lines]
    out.append('différentiels (exacts) : évection 2Y − ϖ · X = Y + p · S = J + Y · TSMG = J + X · λ + p · EdT = X − α')
    out.append('                         équation annuelle · anneau des dates · Europe = 2Ga + ν · Io = 2Eu + ν')
    return out


def shared_arbors(S) -> dict:
    """First driving wheel of every baseline spur train, grouped by source arbor (only arbors driving >= 2 trains)."""
    out = {}
    for sh in S:
        if sh['kind'] == 'train' and not sh.get('optional') and sh['stages'][0][2] in ('external', 'internal'):
            out.setdefault(sh['src'], []).append((sh['id'], sh['stages'][0][0]))
    return {k: v for k, v in out.items() if len(v) >= 2}


def inventory(S) -> dict:
    base = [s for s in S if not s.get('optional')]
    inv = {'designed_pairs': 0, 'designed_wheels': 0, 'exact_pairs': 0, 'exact_wheels': 0, 'idlers': 0,
           'differentials': 0, 'diff_wheels': 0, 'steppers': 0}
    sizes = []
    for sh in base:
        if sh['kind'] == 'train':
            n = len(sh['stages'])
            if sh.get('design'):
                inv['designed_pairs'] += n
                inv['designed_wheels'] += 2 * n
            else:
                inv['exact_pairs'] += n
                inv['exact_wheels'] += 2 * n
            if sh.get('idler'):
                inv['idlers'] += 1
            for (z1, z2, mesh), g, m in zip(sh['stages'], sh.get('geometry', []), sh.get('modules_mm', [])):
                sizes.append((g['pitch_d_mm'][1], sh['id'], z2, m, mesh))
                sizes.append((g['pitch_d_mm'][0], sh['id'], z1, m, mesh))
        elif sh['kind'] == 'diff' and sh.get('realisation'):
            rz = sh['realisation']
            for (z1, z2), m in zip(rz.get('post_pairs', []), rz.get('post_modules_mm', ['1/2'] * 9)):
                mm = float(fr(m))
                sizes.append((mm * z2, sh['id'], z2, m, 'internal' if z2 >= 150 and sh['id'] == 'cal_sum' else 'external'))
            inv['differentials'] += 1
            inv['diff_wheels'] += 4 + 2 * sum(1 for s in rz['sides'] if s.get('pair')) + 2 * len(rz.get('post_pairs', []))
        elif sh['kind'] == 'stepper':
            inv['steppers'] += 1
    # 1:1 transfers not modelled as shafts (estimate): 7 modules x (planet arm 2 + Earth arm 2 + chain 3),
    # 8 geocentric pointers x 2, lunar cascade relative pairs 6 x 2, phase crown 2, Jovian dial 4 x 2
    inv['transfer_wheels_estimate'] = 7 * 7 + 8 * 2 + 6 * 2 + 2 + 4 * 2
    inv['total_estimate'] = (inv['designed_wheels'] + inv['exact_wheels'] + inv['idlers'] + inv['diff_wheels'] +
                             2 * inv['steppers'] + inv['transfer_wheels_estimate'])
    sizes.sort(reverse=True)
    seen, top = set(), []
    for d, sid, z, m, mesh in sizes:
        if (sid, z) in seen:
            continue
        seen.add((sid, z))
        top.append({'pitch_d_mm': d, 'shaft': sid, 'teeth': z, 'module_mm': m, 'mesh': mesh})
        if len(top) >= 8:
            break
    inv['largest_wheels'] = top
    return inv


def write_md(S, T, R, ev, geo, greg, A, L, path: Path):
    by = {s['id']: s for s in S}
    ty = float(T['_tropical_year_days'])
    lines = []
    w = lines.append

    def row(*c):
        w('| ' + ' | '.join(str(x) for x in c) + ' |')

    def train_row(sid, label=None):
        sh = by[sid]
        e = ev.get(sid, {})
        ratio = sh['sign'] * stages_ratio(sh['stages'])
        row(label or sh['name_fr'], SHORT.get(sh['src'], sh['src']) if sh['src'] != 'J' else 'J',
            fnum(e.get('target_turns_per_tropical_year'), 9) if e else '—',
            f"`{fstr(ratio)}`", teeth_str(sh), fsci(e.get('ppm'), 2) if e else 'exact',
            fdeg(e.get('deg_per_century')) if e else 'exact', period_str(e.get('machine_period_days')) if e else '—')

    def header():
        row('Sortie', 'Source', 'Cible (tours par année tropique)', 'Rapport du train (fraction)',
            'Dents (menante:menée)', 'Erreur (ppm)', 'Erreur (°/siècle)', 'Période réalisée')
        row(*['---'] * 8)

    inv = inventory(S)
    designed = [s for s in S if s.get('design') and not s.get('optional')]
    allok = all(a['ok'] for a in A)
    worst = sorted(((abs(ev[s['id']]['deg_per_century']), s['id']) for s in designed
                    if 'deg_per_century' in ev.get(s['id'], {}) and s['id'] not in ('saros', 'precession_ring')),
                   reverse=True)[:3]
    from_Y = [SHORT[s['id']] for s in designed if s['src'] == 'Y']
    from_J = [SHORT[s['id']] for s in designed if s['src'] == 'J' and s['id'] != 'Y']

    w('# Anticythère 2.0 — Les trains d’engrenages')
    w('')
    w('*Généré par `v2/tools/trains.py` (ne pas éditer à la main). Données : `v2/spec/trains.json`. Constantes : '
      '`v2/research/constants.json`. Tous les rapports sont des fractions exactes, recalculées avec `fractions.Fraction` '
      'à chaque exécution ; `trains.py --check` les revérifie à partir des seuls nombres de dents.*')
    w('')
    w('## 0. L’essentiel')
    w('')
    w('- **Une seule entrée** : l’arbre-jour J, 1 tour par jour solaire moyen. Le calendrier grégorien compte des '
      'jours ; il n’est exact que si la machine compte des jours, car 146 097 = 3³·7·773, et 773 est premier et '
      'dépasse 220 dents.')
    w(f"- **La roue de l’année Y** (longitude moyenne de la Terre, repère fixe J2000) est menée par J en "
      f"{len(by['Y']['stages'])} couples. De Y partent : {', '.join(from_Y)}, comme les trains de b1 dans la machine "
      f"antique. De J partent directement : {', '.join(from_J)}. L’anneau du zodiaque (précession) part de "
      f"{SHORT[by['precession_ring']['src']]}.")
    w(f"- **{len(designed)} trains approchés**, choisis par recherche exhaustive : {inv['designed_pairs']} couples. "
      f"Il faut aussi {inv['exact_pairs']} couples de rapport exact (semaine, calendrier, renvois, Exeligmos…), "
      f"{inv['idlers']} pignons fous pour le sens et {inv['differentials']} différentiels. Toutes les dentures "
      f"sont dans [10, 220] ; la machine de base n’a aucune exception. La variante « Saros à 223 dents » en serait "
      f"une, en hommage à b1.")
    w('- **Tout le reste est exact par construction** :')
    w('  - les différentiels : évection 2λ☉ − ϖ, temps sidéral, équation du temps, Laplace ;')
    w('  - les roues de rapport entier : semaine, calendrier, Exeligmos, épicyclet de Mars ;')
    w('  - les unités non linéaires, qui font un tour par tour : Kepler, modules géocentriques, cascade lunaire, '
      'joint de Hooke.')
    worst_txt = ', '.join(SHORT[i] + ' ' + fdeg(ev[i]['deg_per_century']) + '°/siècle' for _, i in worst)
    w(f"- **Bilan** : {'les' if allok else 'PAS toutes les'} {len(A)} vérifications passent. Les plus grosses "
      f"erreurs d’engrenage sont : {worst_txt}.")
    w('  - C’est 100 à 1 000 fois sous les objectifs de la tâche (1°/siècle pour les planètes, 2°/siècle pour la '
      'Lune).')
    w('  - C’est aussi sous l’incertitude des moyens mouvements eux-mêmes (0,005 à 0,05°/siècle).')
    w('  - **Les engrenages ne limitent nulle part la précision** ; la géométrie et la physique la limitent.')
    w('')
    w('| Grandeur | Objectif de la tâche | Erreur d’engrenage (°/siècle) | Marge |')
    w('|---|---|---|---|')
    for k, lab in (('Y', 'Soleil / Terre'),) + tuple((f'{p}_L', PLANET_FR[p]) for p in PLANETS):
        d = ev[k]['deg_per_century']
        w(f"| {lab} | < 1°/siècle | {fdeg(d)} | ×{fnum(1 / abs(d), 0)} |")
    for k, lab in (('moon_L', 'Lune, longitude moyenne L'), ('moon_D', 'Lune, élongation D = L − Y'),
                   ('moon_F', 'Lune, argument de latitude F = L − Ω'), ('moon_Mp', 'Lune, anomalie M′ = L − ϖ')):
        d = ev[k]['deg_per_century']
        w(f"| {lab} | < 2°/siècle | {fdeg(d)} | ×{fnum(2 / abs(d), 0)} |")
    pe = ev['precession_ring']
    w(f"| Précession (période) | à 0,5 % près | écart de {fsci(abs(pe['rel_err']) * 100, 1)} % | "
      f"×{fsci(0.005 / abs(pe['rel_err']), 1)} |")
    w('')
    w('---')
    w('')
    w('## 1. Conventions et méthode')
    w('')
    w('- **Unités.** Les vitesses sont en tours par jour solaire moyen, en fractions exactes. Les « tours par année '
      f'tropique » s’obtiennent en multipliant par l’année tropique moyenne ({fnum(ty, 10)} j, Laskar). L’erreur en '
      '°/siècle de longitude moyenne vaut (machine − cible) × 360 × 36 525. La **période réalisée** est celle que '
      'produit la machine (1/vitesse) : c’est « la période de l’approximation ».')
    w('- **Repère.**')
    w('  - Tous les trains tournent dans le repère **fixe J2000**, celui des étoiles et de la caisse ; les pivots '
      'excentriques de Kepler sont fixés à la caisse.')
    w('  - Le **zodiaque tropique** est un anneau qui tourne lentement à rebours (précession).')
    w('  - Une aiguille se lit donc en longitude tropique sur cet anneau, et en longitude J2000 sur la couronne fixe '
      'des constellations.')
    w('- **Cibles.**')
    w('  - Planètes et Terre : moyens mouvements DE441 ajustés sur 2000–2100 (`constants.json`).')
    w('  - Lune : polynômes de Meeus, ch. 47 (ELP-2000/82), pente moyenne sur 2000–2100, moins p_A.')
    w('  - Précession : p_A IAU 2006, pente moyenne 2000–2100 (5 029,90″/siècle).')
    w('  - Lunes galiléennes : théorie E5 de Lieske. Temps sidéral : IERS 2010.')
    w('- **Signes et sens.**')
    w('  - Une vitesse positive est directe (longitudes croissantes). Vu de face, le sens direct est horaire, comme '
      'sur le cadran avant de la v1.')
    w('  - Chaque couple extérieur inverse le sens ; un anneau à denture intérieure ne l’inverse pas.')
    w(f"  - Le sens de J est choisi pour que Y tourne dans le sens direct sans pignon fou : J tourne "
      f"{'à rebours (antihoraire vu de face)' if by['J']['phys'] < 0 else 'dans le sens horaire'}.")
    w('  - Un pignon fou de 20 dents est ajouté à tout train qui sortirait à l’envers.')
    w('- **Choix d’un train.**')
    w('  - Pour chaque sortie, la recherche exhaustive parcourt toutes les fractions N/D où N et D sont des produits '
      'de k nombres de dents compris entre 10 et la taille maximale, avec k = 1, 2 ou 3.')
    w(f"  - On retient d’abord le plus petit k, puis la plus petite taille maximale de roue (échelle "
      f"{', '.join(str(c) for c in CAPS)} dents), puis la plus petite erreur, à condition que l’erreur ne dépasse "
      f"pas la moitié de l’allocation.")
    w('  - Les couples sont ensuite appariés pour équilibrer les rapports par étage.')
    w('  - Le rapport visé tient compte de l’erreur réelle de l’arbre source : les erreurs ne s’accumulent pas le '
      'long d’une chaîne.')
    w('- **Allocations** (erreur d’engrenage admise, en °/siècle) :')
    w('  - Terre : 0,001. Elle se reporte sur toutes les planètes vues de la Terre et sur D = L − Y.')
    w('  - Planètes : 0,02. Mars, amplifiée ×3,7 à l’opposition, reste ainsi sous 0,1° géocentrique.')
    w('  - Lune : 0,01 pour L, 0,02 pour ϖ, 0,01 pour Ω.')
    w('  - Ganymède et ν : 0,002 chacun, car Io = 4·Ganymède + 3ν. Callisto : 0,01.')
    w('  - Précession : 10⁻⁴ en relatif. Saros : 10⁻⁷ en relatif.')
    w('- **Modules.** 0,5 mm par défaut : une roue de 220 dents fait 110 mm. Les deux anneaux à denture intérieure '
      'ont le diamètre du cadran avant : zodiaque 0,8 mm, dates 0,9 mm. Tous les modules sont ≥ 0,4 mm.')
    w('')
    w('**Arbre des trains de la machine de base** (généré depuis la conception) :')
    w('')
    w('```')
    lines.extend(diagram(S))
    w('```')
    w('')
    w('---')
    w('')
    # ---- 2
    w('## 2. Base de temps et manivelle')
    w('')
    header()
    train_row('W', 'Semaine (1 tour en 7 jours)')
    w('')
    w('- **Heure.** L’aiguille des heures solaires moyennes (cadran de 24 h) est l’arbre J lui-même : rapport 1, exact.')
    w('- **Manivelle.** Trois positions sont possibles, toutes sur des arbres existants et sans rapport nouveau :')
    w('  - sur **J** : 1 tour = 1 jour ;')
    w('  - sur la **roue de la semaine W** : 1 tour = 7 jours exactement ; J tourne alors 7 fois, le couple 10:70 '
      'étant mené à l’envers ;')
    w(f"  - sur la **roue de l’année Y** : 1 tour = 1 année sidérale ; J tourne alors 365,26 fois. C’est un "
      f"multiplicateur de 365 à travers {len(by['Y']['stages'])} couples : possible mais dur (§ 14).")
    w('- **Jours solaires et temps des éphémérides.** J compte des jours solaires moyens (UT1), alors que les '
      'vitesses cibles sont en jours de 86 400 s SI (TT). L’écart ΔT vaut environ 69 s en 2026 et dérive d’environ '
      '1 min par siècle ; il décale la Lune d’environ 0,01°. Il est négligé ; un réglage manuel reste possible.')
    w('')
    # ---- 3
    w('## 3. Calendrier grégorien (règle 4/100/400)')
    w('')
    w('| Organe | Rapport exact | Réalisation | Vitesse moyenne |')
    w('|---|---|---|---|')
    w('| Croix de Malte principale (6 fentes) | 1/6 de tour par jour | une goupille sur J | 1/6 tr/j |')
    w('| Croix de saut (6 fentes) | 1/6 de tour la nuit du 28 février des années communes | goupille escamotable, '
      'commandée par les cames | 303/(6 · 146 097) tr/j |')
    w('| Anneau des dates (366 positions, mois gravés) | (principale + saut)/61 | différentiel conique (½), puis '
      '20:61 et 20:200 (denture intérieure) | 400/146 097 tr/j, soit 1 tour par année civile |')
    for sid, lab in (('cal_prog4', 'Roue-programme de 4 ans (came C4)'),
                     ('cal_prog100', 'Roue-programme de 100 ans (came C100)'),
                     ('cal_prog400', 'Roue-programme de 400 ans (came C400)')):
        sh = by[sid]
        w(f"| {lab} | {fstr(stages_ratio(sh['stages']))} de la précédente | {teeth_str(sh)} | {fstr(R[sid])} tr/j |")
    w('')
    w('**Comment la règle 4/100/400 est appliquée.**')
    w('')
    w('1. L’anneau avance d’une position par jour. Une année commune doit pourtant parcourir ses 366 positions en '
      '365 jours.')
    w('2. La nuit du 28 février d’une année commune, la croix de saut ajoute une position : l’anneau passe directement '
      'du 28 février au 1ᵉʳ mars.')
    w('3. L’anneau fait donc **exactement un tour par année civile**, quelle qu’elle soit. Les roues-programmes, '
      'menées par l’anneau, font exactement un tour en 4, 100 et 400 ans.')
    w('4. On saute le 29 février si **C4 ∨ (C100 ∧ C400)**. Les cames sont lues quand l’anneau est sur le '
      f"28 février (position {greg['reading_position']} sur 366) :")
    w(f"   - **C4**, sur la roue de 4 ans, est levée pendant les trois années non multiples de 4 : un secteur de 270° "
      f"dont les bords sont à mi-chemin des lectures. Marge minimale : {fnum(greg['min_margin_deg']['C4'], 1)}°.")
    w(f"   - **C100**, sur la roue de 100 ans, n’est levée que l’année séculaire : un secteur de 3,6°. Marge "
      f"{fnum(greg['min_margin_deg']['C100'], 2)}°, soit ± ½ an.")
    w(f"   - **C400**, sur la roue de 400 ans, est levée pour les trois siècles non multiples de 400 : un secteur de "
      f"270°. Marge {fnum(greg['min_margin_deg']['C400'], 1)}°.")
    w('')
    dw = greg['daywise']
    w('**Vérifications exactes** (en fractions) :')
    w(f"- logique des cames, année par année : **{len(greg['errors'])} année fausse** de {greg['years'][0]} à "
      f"{greg['years'][1]} ;")
    w(f"- mécanisme simulé jour par jour de {dw['years'][0]} à {dw['years'][1]} ({fint(dw['days'])} jours) : croix de Malte, "
      f"saut décidé par les cames à l’angle réel de l’anneau, date lue sous l’index comparée à la vraie date. "
      f"**{dw['wrong_dates']} date fausse**, et **{dw['wrong_weekdays']} jour de la semaine faux** ;")
    w('- les trois roues reviennent à leur position après 400 ans : vérifier 400 années consécutives suffit donc pour '
      'toutes les années.')
    w('')
    w('- **Jour de la semaine** : 1/7, exact. 146 097 jours font 20 871 semaines : la semaine ne dépend pas de la '
      'règle grégorienne.')
    w('- **Dérive civile** : 365,2425 j − 365,24219 j = 0,031 j par siècle, soit un jour en ~3 200 ans. Elle vient de '
      'la règle grégorienne elle-même, pas de la machine.')
    w('')
    # ---- 4
    w('## 4. Soleil et Terre : la roue de l’année')
    w('')
    header()
    train_row('Y', 'Y : Terre (longitude moyenne, J2000)')
    w('')
    e = ev['Y']
    w(f"- Année sidérale réalisée : {fnum(e['machine_period_days'], 9)} j ; cible {fnum(e['target_period_days'], 9)} j "
      f"(écart {dt_str(e['period_diff_s'])}).")
    w('- Le **Soleil moyen** est Y + 180°, sur le même arbre.')
    w('- Le **Soleil vrai** sort de l’unité de Kepler de la Terre (équant bissecté), qui fait un tour par tour.')
    w('- Le Soleil tropique, lu sur le zodiaque, vaut Y + p ; il est formé par différentiel (§ 8).')
    w('')
    # ---- 5
    w('## 5. Planètes')
    w('')
    w('### 5.1 Longitudes moyennes héliocentriques (repère J2000), depuis la roue de l’année')
    w('')
    header()
    for p in PLANETS:
        train_row(f'{p}_L', PLANET_FR[p])
    w('')
    w('| Planète | Unité de Kepler | Période sidérale réalisée | Cible (DE441) | Écart | Incertitude du taux cible |')
    w('|---|---|---|---|---|---|')
    for p in PLANETS:
        e = ev[f'{p}_L']
        unc = T[f'{p}_L'].get('uncert_deg_cy')
        w(f"| {PLANET_FR[p]} | {KEPLER_UNIT[p]} | {period_str(e['machine_period_days'])} | "
          f"{period_str(e['target_period_days'])} | {dt_str(e['period_diff_s'])} | ±{fnum(unc, 3)}°/siècle |")
    w('')
    w('Pour les planètes lentes, l’écart de période paraît grand en jours, mais il ne compte qu’en degrés par siècle : '
      'Neptune ne fait que 0,6 tour par siècle.')
    w('')
    w('### 5.2 Ce qu’il faut de plus pour la face avant (géocentrique) et l’orrery : des rapports exacts')
    w('')
    w('| Organe | Rapport | Réalisation | Rôle |')
    w('|---|---|---|---|')
    w('| Unité de Kepler (une par planète, Terre comprise) | 1 tour par tour | équant : goupille et rainure menée par la '
      'rainure ; Mercure : résolveur M = E − e sin E | angle autour du centre φ_C (modules) et anomalie vraie (orrery) |')
    w('| Bras planète d’un module vectoriel | 1:1 | renvoi depuis l’unité de Kepler | vecteur Soleil→planète à l’échelle s |')
    w('| Bras Terre des 7 modules | 1:1 (×7) | un arbre « φ_C Terre + 180° » et 7 roues égales | vecteur Terre→Soleil |')
    w('| Bras 2 d’un module (chaîne le long du bras 1) | 1:1 | roue sur tube, pignon fou, roue égale | conserve l’angle '
      'absolu |')
    w(f"| Épicyclet de Mars | 3 | {teeth_str(by['mars_epicyclet'])} | angle 3L − 2ϖ (ϖ figé dans la caisse) |")
    w(f"| Bras (a − b)/2 de Mercure | −1 | inverseur conique coaxial {teeth_str(by['mercury_counter_arm'])} | "
      f"ellipse exacte à deux bras |")
    w('| Tubes de l’orrery (8) | 1:1 | renvoi d’angle conique ou roue de champ vers le couvercle | longitudes '
      'héliocentriques vraies |')
    w('| Aiguilles géocentriques (7 + Soleil) | 1:1 | suiveur du module, renvoi coaxial vers la face avant | '
      'longitudes géocentriques |')
    w('')
    w('La vitesse moyenne de chaque aiguille géocentrique est exacte, et vérifiée : c’est celle de la planète pour '
      'Mars à Neptune, celle du Soleil (Y) pour Mercure et Vénus. Les boucles de rétrogradation sont des oscillations '
      'autour de ce mouvement moyen.')
    w('')
    w('### 5.3 Ce que les erreurs d’engrenage deviennent vues de la Terre')
    w('')
    w('Une erreur δ sur la longitude héliocentrique déplace la planète de r·δ. Vue de la Terre, cela fait au plus '
      'r·δ/Δ_min. Borne par siècle, engrenages seuls (planète et Terre) :')
    w('')
    w('| Planète | Δ_min (ua) | Amplification planète | Amplification Terre | Borne géocentrique (°/siècle) |')
    w('|---|---|---|---|---|')
    for p in PLANETS:
        g = geo[p]
        w(f"| {PLANET_FR[p]} | {fnum(g['delta_min_au'], 3)} | ×{fnum(g['amp_planet'], 2)} | ×{fnum(g['amp_earth'], 2)} | "
          f"{fdeg(g['bound_deg_per_century'])} |")
    w('')
    w('Ces bornes sont 10 à 100 fois plus petites que les erreurs de géométrie de l’étude des mécanismes (0,02 à '
      '0,26°, dues surtout à l’inclinaison et à la dérive séculaire des orbites).')
    w('')
    # ---- 6
    w('## 6. La Lune')
    w('')
    w('### 6.1 Les trois trains approchés')
    w('')
    header()
    train_row('moon_L', 'Lune : longitude moyenne L')
    train_row('moon_perigee', 'Périgée ϖ (porte-satellite de l’anomalie)')
    train_row('moon_node', 'Nœud Ω (porte-nœuds, sens rétrograde)')
    w('')
    w('### 6.2 Les arguments, tous obtenus sans nouveau rapport')
    w('')
    w('| Argument | Formé par | Vitesse réalisée (tours par année tropique) | Cible | Erreur (°/siècle) | Période réalisée |')
    w('|---|---|---|---|---|---|')
    for k, lab, how in (('moon_D', 'Élongation D (lunaison)', 'L − Y'), ('moon_F', 'Argument de latitude F', 'L − Ω'),
                        ('moon_Mp', 'Anomalie M′', 'L − ϖ'),
                        ('evection_carrier', 'Porte-satellite de l’évection', '2Y − ϖ (différentiel)')):
        e = ev[k]
        w(f"| {lab} | {how} | {fnum(e['machine_turns_per_tropical_year'], 9)} | "
          f"{fnum(e['target_turns_per_tropical_year'], 9)} | {fdeg(e['deg_per_century'])} | "
          f"{period_str(e['machine_period_days'])} |")
    w('')
    eD = ev['moon_D']['deg_per_century']
    w(f"- Les engrenages décalent l’heure des syzygies, donc des éclipses, de {fnum(abs(eD) / 12.1907 * 24 * 60, 2)} min "
      f"par siècle.")
    w('- La comparaison de D avec Meeus contient aussi un petit désaccord des cibles entre elles : la Terre de DE441 '
      'et le Soleil de Meeus diffèrent d’environ 0,001°/siècle.')
    w('')
    w('### 6.3 Les étages de la cascade (rapports exacts sur les porte-satellites)')
    w('')
    w('| Étage (ordre de la cascade) | Porte-satellite | Rapports relatifs au porte-satellite | Terme produit |')
    w('|---|---|---|---|')
    w('| 1. Réduction à l’écliptique | Ω (porte-nœuds) | montée 2:1 (60:30), goupille et rainure, descente 1:2 (30:60) '
      '| −0,114° sin 2F |')
    w('| 2. Équation annuelle | — (différentiel) | gain 3/31 = ½ × 30:155 sur (λ☉ vrai − λ☉ moyen), retranché de la '
      'longitude de la Lune | −0,185° sin M |')
    w('| 3. Évection | 2λ☉ − ϖ (différentiel ; gains 80:20 et 40:20) | 1:1 | 1,274° sin(2D − M′) |')
    w('| 4. Anomalie (équant) | ϖ (périgée) | 1:1 | 6,289° sin M′ (+ 0,173° sin 2M′) |')
    w('| 5. Variation | Y (Soleil moyen) | montée 2:1 (60:30), goupille et rainure, descente 1:2 (30:60) | 0,658° sin 2D |')
    w('| Boule de phase | aiguille de la Lune | couronne 1:1 (48:48) menée par le tube du Soleil vrai | phase vraie |')
    w('')
    w('Vitesses moyennes, exactes :')
    w('- la Lune vraie tourne en moyenne comme L ;')
    w('- la boule de phase tourne comme L − Y (la lunaison) ;')
    w('- le moteur de l’équation annuelle a une vitesse moyenne nulle.')
    w('')
    w('Le gain de l’équation annuelle vise 0,185116/1,914602 = 0,096686 ; 3/31 = 0,096774, soit 0,09 % de 0,185°, '
      'environ 0,0002°.')
    w('')
    # ---- 7
    w('## 7. Éclipses')
    w('')
    header()
    train_row('saros', 'Saros (1 tour = 223 lunaisons)')
    train_row('exeligmos', 'Exeligmos (1 tour = 3 Saros)')
    w('')
    w('- La prédiction des éclipses n’utilise **aucun rapport de plus**. La coulisse écossaise est portée par le '
      'porte-nœuds Ω et menée par la goupille de l’unité d’anomalie : elle donne γ ∝ r·sin F (étude des mécanismes, '
      '§ 5).')
    w('- Les aiguilles du Saros et de l’Exeligmos sont des compteurs de retour.')
    e = ev['saros']
    w(f"- Saros réalisé : {period_str(e['machine_period_days'])}, pour une cible de "
      f"{period_str(e['target_period_days'])} (écart {dt_str(e['period_diff_s'])}). Il part de "
      f"{SRC_PHRASE.get(by['saros']['src'], by['saros']['src'])}, en {len(by['saros']['stages'])} couples. "
      f"Depuis J, il faudrait trois couples (réduction de 1:6 585, proche de la limite 22³ = 10 648) ; depuis Y, "
      f"le rapport n’est que 1:18.")
    es = ev['saros_223']
    w('- **Variante exacte** (option) :')
    w('  - un arbre synodique D = L − Y (différentiel), puis 20:223 et 10:200 ;')
    w('  - le rapport vaut alors exactement 1/223 de la lunaison de la machine ;')
    w('  - la roue de 223 dents sort de la règle des 220 dents. L’exception se justifie : 223 est premier, comme pour '
      'b1 dans la machine antique ;')
    w(f"  - écart à la cible : {fsci(es['ppm'], 2)} ppm, celui de D.")
    w('')
    # ---- 8
    w('## 8. Temps sidéral, équation du temps, précession')
    w('')
    header()
    train_row('precession_ring', 'Anneau du zodiaque tropique (précession)')
    train_row('eot_dial', 'Aiguille de l’EdT (×10)')
    train_row('tellurion', 'Globe-tellurion (chaîne 1:1)')
    w('')
    e = ev['precession_ring']
    w(f"- **Précession.** Période réalisée : {fnum(e['machine_period_days'] / ty, 1)} années tropiques, pour une cible "
      f"de {fnum(e['target_period_days'] / ty, 1)} ans. La cible est la pente moyenne de p_A sur 2000–2100 ; avec le "
      f"seul terme linéaire, on aurait {fnum(1296000 / 50.28796195, 1)} ans. Écart relatif : {fsci(e['rel_err'], 1)}.")
    w(f"  - Le train part de l’arbre de **{SHORT[by['precession_ring']['src']]}**. Deux couples suffisent ainsi, "
      f"au lieu de quatre depuis Y, car 25 766 > 22³ = 10 648.")
    w('  - Le dernier couple attaque la denture intérieure de l’anneau lui-même.')
    w('')
    w('| Différentiel | Relation exacte (vitesses) | Gains des côtés | Rôle |')
    w('|---|---|---|---|')
    for sid, role in (('sun_trop', 'Soleil moyen tropique (EdT, temps sidéral)'),
                      ('stellar', 'globe-tellurion de l’orrery'), ('gmst', 'aiguille du temps sidéral'),
                      ('lambda_trop', 'entrée du joint de Hooke'), ('eot', 'équation du temps'),
                      ('evection_carrier', 'porte-satellite de l’évection'), ('annual_eq', 'équation annuelle de la Lune'),
                      ('cal_sum', 'anneau des dates'), ('europa', 'Europe'), ('io', 'Io')):
        sh = by[sid]
        rel = ' + '.join(f"({t['coeff']})·{t['shaft']}" for t in sh['terms']).replace('(-', '(−')
        rz = sh.get('realisation') or {}
        gains = ', '.join((('−' if s['sign'] < 0 else '') + (f"{s['pair'][0]}:{s['pair'][1]}" if s.get('pair') else 'direct'))
                          for s in rz.get('sides', []))
        if rz.get('post_pairs'):
            gains += ' ; puis ' + ' · '.join(f"{a}:{b}" for a, b in rz['post_pairs'])
        w(f"| {sh['name_fr']} | {sid} = {rel} | {gains} | {role} |")
    w('')
    w('Un différentiel conique donne ½(s₁ + s₂) sur son porte-satellite. Un gain 40:20 (×2) sur chaque côté donne '
      'donc s₁ + s₂, et un gain 80:20 (×4) donne 2s₁. Le signe « − » est obtenu par un pignon fou.')
    w('')
    e = ev['gmst']
    gm = T['gmst']['turns_per_day']
    p_lin = per_day(fr(5028.796195) / 3600)
    comp_Y = (R['Y'] - T['Y']['turns_per_day']) * 86400 * DAYS_PER_CY
    comp_p = (-R['precession_ring'] - p_lin) * 86400 * DAYS_PER_CY
    comp_t = (1 + T['Y']['turns_per_day'] + p_lin - gm) * 86400 * DAYS_PER_CY
    w(f"- **Temps sidéral.** TSMG = J + Y + p : c’est une identité exacte. Vitesse réalisée : "
      f"{fnum(float(R['gmst']), 13)} tr/j ; IERS : {fnum(float(gm), 13)} tr/j. Écart : "
      f"{fnum(e['err_s_per_century'], 3, True)} s de temps sidéral par siècle, qui se décompose ainsi :")
    w(f"  - {fnum(float(comp_Y), 3, True)} s : erreur du train de Y ;")
    w(f"  - {fnum(float(comp_p), 3, True)} s : la pente moyenne de p_A sur 2000–2100, au lieu de sa valeur J2000 ;")
    w(f"  - {fnum(float(comp_t), 3, True)} s : écart entre l’année DE441 et l’année implicite de la formule IERS.")
    eg = ev['gmst_direct']
    w(f"- *Variante* : un train direct depuis J, {teeth_str(by['gmst_direct'])}. Il donne "
      f"{fnum(eg['err_s_per_century'], 3, True)} s par siècle sans différentiel. Mais il n’est plus lié au Soleil de la "
      f"machine : l’écart avec l’aiguille du Soleil dériverait. On retient le différentiel, la solution de Schwilgué à "
      f"Strasbourg.")
    es = ev['stellar']
    w(f"- **Globe-tellurion.** S = J + Y. L’écart à l’ERA de l’IERS vaut {fnum(es['err_s_per_century'], 2, True)} s "
      f"par siècle, soit environ p_A(1 − cos ε) ≈ 417″ par siècle. Ce n’est pas une erreur d’engrenage : le globe a "
      f"un axe fixe, alors que l’ERA est mesuré autour de l’axe réel, qui précesse. C’est invisible sur un globe.")
    w('- **Équation du temps.** EdT = X − α, où α sort du joint de Hooke. Le joint fait un tour par tour : la vitesse '
      'moyenne de l’EdT est donc **exactement nulle**, et l’aiguille ne dérive jamais. Un couple 120:12 l’agrandit ×10.')
    ea = ev['mars_apsides']
    w(f"- *Option* : un plateau d’apsides de Mars, mené par l’anneau de précession par le couple "
      f"{teeth_str(by['mars_apsides'])}. Période {fnum(ea['machine_period_days'] / ty, 0)} ans, pour une cible de "
      f"{fnum(ea['target_period_days'] / ty, 0)} ans. Il supprimerait la plus grande part de la dérive séculaire de "
      f"Mars (0,33° à ±100 ans).")
    w('')
    # ---- 9
    w('## 9. Les lunes galiléennes (jovicentriques, repère fixe)')
    w('')
    header()
    for sid, lab in (('ganymede', 'Ganymède'), ('nu', 'ν (ligne des conjonctions à −ν)'), ('callisto', 'Callisto')):
        train_row(sid, lab)
    w('')
    w('| Lune | Formée par | Période sidérale réalisée | Cible (E5) | Erreur (°/siècle) | Période relative au bras de '
      'Jupiter de l’orrery |')
    w('|---|---|---|---|---|---|')
    for sid, lab, how in (('io', 'Io', '2·Europe + ν'), ('europa', 'Europe', '2·Ganymède + ν'),
                          ('ganymede', 'Ganymède', 'train'), ('callisto', 'Callisto', 'train')):
        e = ev[sid]
        relj = 1 / (R[sid] - R['jupiter_L'])
        w(f"| {lab} | {how} | {fnum(e['machine_period_days'], 7)} j | {fnum(e['target_period_days'], 7)} j | "
          f"{fdeg(e['deg_per_century'])} | {fnum(float(relj), 7)} j |")
    w('')
    w('- La relation de Laplace n_Io − 3n_Eu + 2n_Ga = 0 est **exacte par construction**, quels que soient les '
      'rapports des deux trains : (4Ga + 3ν) − 3(2Ga + ν) + 2Ga = 0.')
    w('- Les doubleurs des différentiels (80:20 et 40:20) sont exacts.')
    w('- La « ligne des conjonctions » se montre par une aiguille sur l’arbre ν renversé (1:1). Elle fait un tour '
      'rétrograde en 486,8 jours.')
    w('- Ces vitesses sont jovicentriques et sidérales, pour un cadran jovien fixe. Sur le bras de Jupiter de '
      'l’orrery, il faudrait retrancher la vitesse de Jupiter (dernière colonne). Ce serait exact avec une seconde '
      'boîte de Laplace au bout du bras ; cette option n’est pas retenue.')
    w('')
    # ---- 10
    w('## 10. Bilan d’erreur complet')
    w('')
    w('| Sortie | Erreur (ppm) | Erreur (°/siècle) | Années pour 1° | Allocation (°/siècle) | Commentaire |')
    w('|---|---|---|---|---|---|')
    comments = {'Y': 'se reporte sur toutes les planètes vues de la Terre', 'moon_D': 'L − Y', 'moon_F': 'L − Ω',
                'moon_Mp': 'L − ϖ', 'io': '4·Ganymède + 3ν', 'europa': '2·Ganymède + ν',
                'evection_carrier': '2Y − ϖ', 'saros': 'compteur', 'precession_ring': 'erreur relative de la période'}
    for s in designed:
        if s.get('idler'):
            comments[s['id']] = (comments.get(s['id'], '') + ' ; pignon fou').strip(' ;')
    alloc_of = {'Y': ALLOC['Y'], 'moon_L': ALLOC['moon_L'], 'moon_perigee': ALLOC['moon_perigee'],
                'moon_node': ALLOC['moon_node'], 'ganymede': ALLOC['ganymede'], 'nu': ALLOC['nu'],
                'callisto': ALLOC['callisto']}
    for p in PLANETS:
        alloc_of[f'{p}_L'] = ALLOC['planet']
    order = ['Y'] + [f'{p}_L' for p in PLANETS] + ['moon_L', 'moon_perigee', 'moon_node', 'moon_D', 'moon_F', 'moon_Mp',
                                                    'evection_carrier', 'ganymede', 'nu', 'europa', 'io', 'callisto',
                                                    'saros', 'precession_ring']
    for k in order:
        e = ev[k]
        a = alloc_of.get(k)
        y1 = e.get('years_to_1deg')
        nm = SHORT.get(k) or T[e['target']]['name_fr']
        w(f"| {nm} | {fsci(e['ppm'], 2)} | {fdeg(e['deg_per_century'])} | {fsci(y1, 1) if y1 else '∞'} | "
          f"{fnum(a, 3) if a is not None else '—'} | {comments.get(k, '')} |")
    w(f"| Temps sidéral (TSMG) | {fsci(ev['gmst']['ppm'], 2)} | {fnum(ev['gmst']['err_s_per_century'], 3, True)} s/siècle | — | "
      f"1 s/siècle | identité J + Y + p |")
    w('')
    w('**Pour comparaison**, d’après l’étude des mécanismes et les constantes :')
    w('- la géométrie seule laisse 0,02 à 0,26° géocentriques sur 2000–2100 ;')
    w('- la Lune à 5 étages laisse 0,26° au maximum ;')
    w('- les perturbations hors Kepler valent 0,11° (Jupiter) et 0,17° (Saturne) ;')
    w('- les moyens mouvements cibles sont eux-mêmes incertains de 0,005 à 0,05°/siècle.')
    w('')
    w('**Les engrenages ne sont nulle part le facteur limitant.**')
    w('')
    w(f"### Vérifications ({sum(a['ok'] for a in A)}/{len(A)} réussies)")
    w('')
    w('| Vérification | Valeur | Limite | État |')
    w('|---|---|---|---|')
    for a in A:
        lim = ('= ' + flim(a['limit'])) if a['kind'] == '==' else ('≤ ' + flim(a['limit']))
        w(f"| {a['name']} | {fval(a['value'])} | {lim} | {'✅' if a['ok'] else '❌'} |")
    w('')
    # ---- 11 inventory
    w('## 11. Inventaire et encombrement')
    w('')
    w('| Poste | Nombre |')
    w('|---|---|')
    w(f"| Couples des trains approchés | {inv['designed_pairs']} ({inv['designed_wheels']} roues) |")
    w(f"| Couples de rapport exact modélisés (semaine, calendrier, renvois, Exeligmos…) | {inv['exact_pairs']} "
      f"({inv['exact_wheels']} roues) |")
    w(f"| Pignons fous de sens | {inv['idlers']} |")
    w(f"| Différentiels coniques, avec leurs couples de gain | {inv['differentials']} ({inv['diff_wheels']} roues) |")
    w(f"| Croix de Malte et leurs plateaux à goupille | {inv['steppers']} ({2 * inv['steppers']} pièces) |")
    w(f"| Renvois 1:1 non modélisés comme arbres : modules, aiguilles, cascade lunaire, cadran jovien (estimation) | "
      f"~{inv['transfer_wheels_estimate']} roues |")
    w(f"| **Total estimé des roues dentées** | **~{inv['total_estimate']}** |")
    w('')
    w('**Arbres partagés.** Chaque arbre source porte les premières roues menantes de plusieurs trains. Deux roues '
      'menantes de même denture et de même module peuvent n’en faire qu’une, qui engrène avec plusieurs roues '
      'disposées autour d’elle, comme b1 dans la machine antique :')
    w('')
    w('| Arbre source | Premières roues menantes (dents → train) | Roues communes possibles |')
    w('|---|---|---|')
    for src, lst in shared_arbors(S).items():
        drv = ', '.join(f"{z} → {SHORT.get(i, i)}" for i, z in lst)
        cnt = {}
        for i, z in lst:
            cnt.setdefault(z, []).append(SHORT.get(i, i))
        common = ' ; '.join(f"{z} dents : {', '.join(v)}" for z, v in cnt.items() if len(v) > 1) or '—'
        w(f"| {SHORT.get(src, src) if src != 'J' else 'arbre-jour J'} | {drv} | {common} |")
    w('')
    w('Plus grandes roues :')
    w('')
    w('| Arbre | Dents | Module (mm) | Diamètre primitif (mm) | Engrènement |')
    w('|---|---|---|---|---|')
    for t in inv['largest_wheels']:
        w(f"| {SHORT.get(t['shaft'], t['shaft'])} | {t['teeth']} | {fnum(float(fr(t['module_mm'])), 2)} | "
          f"{fnum(t['pitch_d_mm'], 1)} | {'denture intérieure' if t['mesh'] == 'internal' else 'extérieur'} |")
    w('')
    w('Ordre de grandeur :')
    w('- les roues ordinaires font au plus ~95 mm ;')
    w('- les deux anneaux du cadran avant font 143 et 180 mm.')
    w('')
    w('C’est le format de la v1 (plaque de 176 × 300 mm), avec plus d’étages. L’implantation (plans, entraxes, '
      'empilement des tubes coaxiaux) reste à faire.')
    w('')
    # ---- 12 CF
    w('## 12. Fractions continues : la meilleure fraction n’est pas toujours taillable')
    w('')
    w('Pour chaque train conçu, le tableau donne :')
    w('- le rapport visé r et ses premiers quotients partiels ;')
    w('- la première réduite (convergente) qui tient l’allocation, et si elle se taille en 1 à 3 couples de '
      '[10, 220] ;')
    w('- la fraction retenue p/q.')
    w('')
    w('La dernière colonne divise l’erreur de la fraction retenue par celle de la meilleure fraction de dénominateur '
      '≤ q (descente de Stern–Brocot). ×1 signifie que la fraction retenue est elle-même une meilleure approximation.')
    w('')
    w('| Train | Rapport visé r | Fraction continue de r | 1ʳᵉ réduite dans l’allocation | Taillable ? | Fraction retenue | Erreur / meilleure erreur (dén. ≤ q) |')
    w('|---|---|---|---|---|---|---|')
    for sh in S:
        cf = sh.get('cf')
        if not cf:
            continue
        w(f"| {SHORT.get(sh['id'], sh['id'])} | {fnum(cf['r'], 10)} | [{'; '.join(str(a) for a in cf['terms'][:8])}"
          f"{'; …' if len(cf['terms']) > 8 else ''}] | {cf['first_ok_convergent'] or '—'} | "
          f"{cf['first_ok_factorable'] or '—'} | `{cf['chosen']}` | ×{fnum(cf['quality'], 2)} |")
    w('')
    w('**Combien de couples faut-il ?** Erreur du meilleur train à 1, 2 et 3 couples (roues jusqu’à 220 dents), en '
      '°/siècle. En gras : le train retenu, avec la taille maximale de ses roues.')
    w('')
    w('| Train | 1 couple | 2 couples | 3 couples | Allocation |')
    w('|---|---|---|---|---|')
    for sh in S:
        d = sh.get('design')
        if not d or sh['id'] in ('gmst_direct',):
            continue
        tg = abs(float(deg_cy(T[sh['target']]['turns_per_day'])))
        cells = []
        for k in ('1', '2', '3'):
            alt = d['alternatives'].get(k)
            if int(k) == d['pairs']:
                cells.append(f"**{fsci(d['rel_err_train'] * tg, 1)}** (roues ≤ {d['cap']}) ; à 220 : "
                             f"{fsci(alt['rel_err'] * tg, 1)}")
            else:
                cells.append(fsci(alt['rel_err'] * tg, 1) if alt else 'impossible')
        al = d['alloc_deg_cy'] if d.get('alloc_deg_cy') is not None else d['alloc_rel'] * tg
        w(f"| {SHORT.get(sh['id'], sh['id'])} | {' | '.join(cells)} | {fsci(al, 0)} |")
    w('')
    w('« impossible » : le rapport sort de l’intervalle qu’un seul couple de 10 à 220 dents peut donner (1:22 à 22:1). '
      'Le retenu n’est pas toujours le plus précis : c’est le plus petit nombre de couples qui tient la moitié de '
      'l’allocation, avec les plus petites roues.')
    w('')
    w('Comment lire ce tableau :')
    w('- Les réduites successives sont les fractions de Huygens (1682). À dénominateur donné, elles sont les '
      'meilleures possibles.')
    w('- Mais leurs facteurs premiers dépassent souvent 220 : un nombre premier de 223 ou plus ne se taille pas.')
    w('- La recherche exhaustive trouve des rapports moins « optimaux » au sens de Stern–Brocot, mais taillables, et '
      'encore bien plus précis que nécessaire.')
    w('')
    # ---- 13 Lean
    w('## 13. Candidats aux preuves Lean 4')
    w('')
    w('**Tous les rapports sont candidats**, car ce sont des fractions exactes. La méthode de la v1 s’applique : '
      '`Kinematics.lean` et `Targets.lean` y sont générés depuis la spec. Il y a quatre familles d’énoncés :')
    w('')
    w('1. **Rapports de trains**, un énoncé par arbre : ω_sortie = ± Π menantes / Π menées · ω_source. On en déduit '
      'la vitesse par rapport à J par `norm_num`. Exemple : ' +
      f"`{next(l['statement'] for l in L if l['shaft'] == 'Y')}`, soit ω Y = {fstr(R['Y'])} · ω J.")
    w('2. **Bornes d’erreur** : |ω − cible| · 360 · 36 525 < borne. La cible est la décimale exacte de '
      '`constants.json` ; la preuve est un `norm_num` sur des rationnels.')
    w('3. **Identités exactes par construction** :')
    w('   - Laplace : Io − 3·Europe + 2·Ganymède = 0 ;')
    w('   - évection = 2Y − ϖ ; TSMG = J + Y + p ;')
    w('   - vitesse moyenne nulle de l’EdT et de l’équation annuelle ;')
    w('   - Exeligmos = Saros/3 ; anneau des dates = 400/146 097 tr/j ;')
    w('   - vitesse moyenne des aiguilles géocentriques = celle de la planète ou du Soleil.')
    w('4. **Logique grégorienne** : `decide` sur les 400 cas, plus la périodicité de 400 ans des trois cames ; '
      'et 146 097 = 7 · 20 871.')
    w('')
    w(f"`trains.json` → `lean_candidates` en contient {len(L)} : {sum(1 for l in L if l['kind'] == 'ratio')} rapports, "
      f"{sum(1 for l in L if l['kind'] in ('identity', 'mean_rate'))} identités et vitesses moyennes, "
      f"{sum(1 for l in L if l['kind'] == 'bound')} bornes, {sum(1 for l in L if l['kind'] == 'decide')} énoncés "
      f"décidables.")
    w('')
    w('Vitesses exactes des arbres approchés par rapport à J (tours par jour) :')
    w('')
    w('| Arbre | Vitesse exacte (tr/j) | Cible (°/siècle ; fraction exacte dans `trains.json`) | Machine (°/siècle) |')
    w('|---|---|---|---|')
    for s in designed:
        e = ev.get(s['id'], {})
        tgd = deg_cy(fr(e['target_turns_per_day']))
        w(f"| {SHORT.get(s['id'], s['id'])} | `{fstr(R[s['id']])}` | {fnum(float(tgd), 6)} | "
          f"{fnum(float(deg_cy(R[s['id']])), 6)} |")
    w('')
    # ---- 14 open
    w('## 14. Questions ouvertes')
    w('')
    sar = by['saros']
    oq = [
        '**Manivelle rapide.** Une manivelle sur Y (1 tour = 1 an) entraîne J à ×365 à travers trois couples, ainsi '
        'que les croix de Malte et la boîte de Laplace (Io : 206 tours par tour de manivelle). C’est cinématiquement '
        'exact, mais le couple et l’usure sont à étudier. Alternatives : la manivelle sur W seulement (1 tour = 1 '
        'semaine), ou un débrayage du calendrier et des lunes galiléennes en marche rapide, qu’il faudrait alors '
        'recaler.',
        f"**Saros : 223 dents ou pas ?** La machine de base suit la règle des 220 dents : {len(sar['stages'])} couples "
        f"depuis {SRC_PHRASE.get(sar['src'], sar['src'])}, à {fsci(abs(ev['saros']['rel_err']), 1)} près. La variante "
        f"exacte demande une roue de 223 dents et un différentiel de plus (arbre synodique) ; elle rend hommage à b1.",
        '**Fenêtre des cibles.** Toutes les cibles sont des pentes moyennes sur 2000–2100. L’écart entre jeux '
        'd’éléments va jusqu’à 0,46°/siècle (Saturne, selon la fenêtre), soit 50 à 1 000 fois les erreurs '
        'd’engrenage. Changer de fenêtre change donc les cibles, pas la conclusion ; il faudrait seulement relancer '
        'la recherche (quelques secondes).',
        '**Modules et place.** Les modules (0,5 mm ; anneaux 0,8–0,9 mm) et les entraxes sont indicatifs. Les roues '
        'de 10 dents demandent un déport de denture ou un angle de pression de 25 à 30°, comme dans la v1.',
        '**Sens des différentiels.** Les relations sont écrites en vitesses signées. Le sens physique de chaque entrée '
        '(et donc les pignons fous éventuels) se fixera à l’implantation.',
        '**Plateau d’apsides de Mars.** L’option est chiffrée (§ 8). La machine de base garde le réglage séculaire à '
        'la main.',
        '**Lunes galiléennes sur l’orrery.** La machine de base les montre sur un cadran jovien fixe. Les montrer '
        'autour de la Jupiter du couvercle demanderait une seconde boîte de Laplace au bout du bras.',
    ]
    for q in oq:
        w(f'- {q}')
    w('')
    w('## 15. Reproduire')
    w('')
    w('```')
    w('BPY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13')
    w('$BPY ~/antikythera/v2/tools/trains.py           # recherche, vérification et écriture (quelques secondes)')
    w('$BPY ~/antikythera/v2/tools/trains.py --check   # revérifie spec/trains.json à partir des seules dentures')
    w('```')
    w('')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


# =====================================================================================================================
# 9. Continued-fraction report per designed train
# =====================================================================================================================

def cf_report(sh: dict, T: dict, R: dict) -> dict:
    tgt = T[sh['target']]['turns_per_day']
    r = abs(tgt / R[sh['src']])
    chosen = stages_ratio(sh['stages'])
    alloc_rel = Fraction(sh['design']['alloc_rel']).limit_denominator(10 ** 15)
    terms = cf_terms(r, 40)
    first_ok, first_fact = None, None
    for c in convergents(r, 10 ** 12):
        if abs(c - r) / r <= alloc_rel * MARGIN:
            first_ok = fstr(c)
            f = factorable(c)
            first_fact = (f"oui ({f[0]} couple{'s' if f[0] > 1 else ''}, ×{f[1]})" if f else
                          'non (facteur premier > 220 ou trop grand)')
            break
    best = best_rational(r, chosen.denominator)
    q = abs(chosen - r) / max(abs(best - r), Fraction(1, 10 ** 40))
    return {'r': float(r), 'terms': terms[:20], 'first_ok_convergent': first_ok, 'first_ok_factorable': first_fact,
            'chosen': fstr(chosen), 'best_same_den': fstr(best), 'quality': float(q)}


# =====================================================================================================================
# 10. Main
# =====================================================================================================================

def run_checks(S, T):
    for sh in S:
        if sh['kind'] == 'diff':
            check_diff_realisation(sh)
    R = finalize(S, T)
    ev = evaluate(S, T, R)
    geo = geocentric_bounds(T, ev)
    greg = gregorian_check()
    greg['daywise'] = gregorian_daywise()
    A = budgets(S, T, R, ev, geo, greg)
    return R, ev, geo, greg, A


def main():
    C = json.loads(CONST_PATH.read_text(encoding='utf-8'))
    if '--check' in sys.argv:
        spec = json.loads(OUT_JSON.read_text(encoding='utf-8'))
        T = load_targets(C)
        S = [dict(s) for s in spec['shafts']]
        stored = {s['id']: s['rate_turns_per_day'] for s in spec['shafts']}
        R, ev, geo, greg, A = run_checks(S, T)
        for k, v in stored.items():
            assert fstr(R[k]) == v, (k, fstr(R[k]), v)
        for a in A:
            print(('OK   ' if a['ok'] else 'FAIL ') + a['name'], a['value'])
        bad = [a for a in A if not a['ok']]
        print(f"{len(A) - len(bad)}/{len(A)} vérifications réussies ; vitesses recalculées identiques à la spec "
              f"({len(stored)} arbres).")
        sys.exit(1 if bad else 0)
    S, T = build(C)
    R, ev, geo, greg, A = run_checks(S, T)
    for sh in S:
        if sh.get('design'):
            sh['cf'] = cf_report(sh, T, R)
    L = lean_candidates(S, T, R, ev)
    meta = {'title': 'Anticythère 2.0 — trains d’engrenages (fractions exactes)', 'generated_by': 'v2/tools/trains.py',
            'constants': 'v2/research/constants.json', 'date': '2026-10-03', 'n_shafts': len(S),
            'all_budgets_ok': all(a['ok'] for a in A)}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(to_json(S, T, R, ev, geo, greg, A, L, meta), ensure_ascii=False, indent=1) + '\n',
                        encoding='utf-8')
    write_md(S, T, R, ev, geo, greg, A, L, OUT_MD)
    for sh in S:
        if sh.get('design'):
            e = ev.get(sh['id'], {})
            print(f"{sh['id']:16s} from {sh['src']:10s} {teeth_str(sh):40s} "
                  f"err {e.get('deg_per_century', e.get('err_s_per_century', 0)):+.2e} rel {e.get('rel_err', 0):+.2e}")
    bad = [a for a in A if not a['ok']]
    for a in bad:
        print('FAIL', a['name'], a['value'], a['limit'])
    print(f"{len(A) - len(bad)}/{len(A)} checks OK -> {OUT_JSON} , {OUT_MD}")
    assert not bad, 'error budget not met'


if __name__ == '__main__':
    main()
