"""Tests du module d'éphémérides (v2/tools/ephem.py).

Références indépendantes :
- JPL Horizons (DE441) : éléments osculateurs héliocentriques des barycentres, écliptique J2000, 2000-2100 au pas
  de 10 j (research/sources/horizons/*.csv.gz) -> positions exactes (conversion propre au test, indépendante
  du module) -> longitudes géocentriques de référence ;
- canon NASA des éclipses 2001-2100 (Espenak & Meeus, research/calc/data) pour la Lune et γ ;
- Meeus, exemple 47.a ; formule basse précision de la Lune de l'Astronomical Almanac (toutes phases) ;
  extrêmes 2026 de l'équation du temps (research/constants.json) ;
- module datetime de Python (calendrier grégorien proleptique) pour le calendrier.
Lancer : $PY -m unittest discover -s tests -v (depuis v2/).
"""
import csv
import datetime
import gzip
import json
import math
import os
import sys
import unittest

import numpy as np

V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(V2, 'tools'))
import ephem as E  # noqa: E402

HORIZONS = os.path.join(V2, 'research', 'sources', 'horizons', 'horizons_%s_2000_2100.csv.gz')
ECLIPSES = os.path.join(V2, 'research', 'calc', 'data', 'nasa_%s_eclipses_2001_2100.csv')
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
API_KEYS = (['lambda_sun', 'lambda_moon', 'node', 'perigee', 'elong']
            + ['lambda_geo_' + p for p in E.PLANETS] + ['helio_' + p for p in E.PLANETS]
            + ['helio_earth', 'prec', 'gmst', 'mean_solar', 'jup_io', 'jup_europa', 'jup_ganymede',
               'jup_callisto', 'jup_nu', 'lunette', 'cal_ring', 'weekday', 'years', 'saros', 'exeligmos',
               'eot', 'gamma'])
# seuils : budget de l'architecture (géométrie + physique hors Kepler) plus une marge
LIMITS_DEG = {'mercury': 0.5, 'venus': 0.4, 'mars': 0.4, 'jupiter': 0.4, 'saturn': 0.4, 'uranus': 0.4,
              'neptune': 0.4, 'sun': 0.05, 'moon': 0.6}
REPORT = {}


def wrap_deg(a):
    return (np.asarray(a) + 180.0) % 360.0 - 180.0


def _rot(axis, ang):
    """Matrices de rotation (n, 3, 3) autour de l'axe 'x' ou 'z' (angles en radians, tableau)."""
    c, s, o, u = np.cos(ang), np.sin(ang), np.zeros_like(ang), np.ones_like(ang)
    if axis == 'z':
        m = [[c, -s, o], [s, c, o], [o, o, u]]
    else:
        m = [[u, o, o], [o, c, -s], [o, s, c]]
    return np.moveaxis(np.array(m), -1, 0)


def horizons_xyz(body):
    """(jours, x, y, z) héliocentriques J2000 (ua) depuis les éléments osculateurs de Horizons.

    Conversion indépendante du module testé : Kepler par point fixe (200 itérations), position dans le plan
    de l'orbite par l'anomalie vraie, puis R = Rz(Ω)·Rx(i)·Rz(ω)."""
    rows = [ln.split(',') for ln in gzip.open(HORIZONS % body, 'rt') if ln.strip() and not ln.startswith('#')]
    a = np.array([[float(v) for v in r[:7]] for r in rows])
    jd, ec, inc, om, w, ma, sma = a.T
    m = np.radians(ma)
    ecc = m.copy()
    for _ in range(200):
        ecc = m + ec*np.sin(ecc)
    nu = 2.0*np.arctan2(np.sqrt(1.0 + ec)*np.sin(ecc/2), np.sqrt(1.0 - ec)*np.cos(ecc/2))
    r = sma*(1.0 - ec*np.cos(ecc))
    p = np.stack([r*np.cos(nu), r*np.sin(nu), np.zeros_like(r)], axis=-1)
    rmat = _rot('z', np.radians(om)) @ _rot('x', np.radians(inc)) @ _rot('z', np.radians(w))
    x, y, z = np.einsum('nij,nj->ni', rmat, p).T
    return jd - E.J2000, x, y, z


def nasa_eclipses(kind):
    """(jours TD au maximum, γ) du canon NASA."""
    out = []
    with open(ECLIPSES % kind) as fh:
        for r in csv.reader(fh):
            if r[0].startswith('#'):
                continue
            h, m, s = map(int, r[4].split(':'))
            day = int(r[3]) + (h + m/60 + s/3600)/24
            out.append((E.jours_from_date(int(r[1]), MONTHS.index(r[2]) + 1, day), float(r[10])))
    return np.array(out)


class TestApi(unittest.TestCase):
    def test_keys_and_shapes(self):
        self.assertEqual(set(API_KEYS) - set(E.KEYS), set())
        j = np.array([0.0, 1234.5, 9772.5])
        for k in E.KEYS:
            v = E.values(k, j)
            self.assertEqual(v.shape, j.shape, k)
            self.assertTrue(np.all(np.isfinite(v)), k)
            self.assertAlmostEqual(E.value(k, 1234.5), v[1], places=12, msg=k)
        with self.assertRaises(KeyError):
            E.value('pluton', 0.0)

    def test_julian_day(self):
        self.assertEqual(E.jd_from_date(2000, 1, 1.5), 2451545.0)
        self.assertAlmostEqual(E.jd_from_date(1957, 10, 4.81), 2436116.31, places=6)    # Meeus 7.a
        self.assertEqual(E.jours_from_date(2026, 1, 1), 9496.5)
        self.assertEqual(E.jd_from_date(1900, 1, 1), 2415020.5)

    def test_mean_rates_match_trains(self):
        """Sens et repère cohérents avec la machine : pente moyenne (moindres carrés, 1900-2100) de chaque clé
        = taux de l'arbre de spec/trains.json qui la réalise (une erreur de repère J2000/date se verrait à
        ~3e-6 près pour la Lune, ~4e-5 pour le Soleil). Seuils : périodiques résiduels et choix de denture."""
        from fractions import Fraction
        with open(os.path.join(V2, 'spec', 'trains.json')) as fh:
            rates = {s['id']: float(Fraction(s['rate_turns_per_day'])) for s in json.load(fh)['shafts']
                     if s.get('rate_turns_per_day') is not None}
        pairs = {'lambda_sun': ('sun_geo', 2e-6), 'helio_earth': ('orrery_earth', 2e-6),
                 'lambda_moon': ('moon_true', 1e-7), 'elong': ('moon_phase', 1e-7), 'node': ('moon_node', 2e-6),
                 'perigee': ('moon_perigee', 5e-6), 'prec': ('precession_ring', 1e-3), 'weekday': ('W', 1e-9),
                 'jup_io': ('io', 1e-8), 'jup_europa': ('europa', 1e-8), 'jup_ganymede': ('ganymede', 1e-8),
                 'jup_callisto': ('callisto', 1e-7), 'jup_nu': ('nu', 1e-6), 'cal_ring': ('cal_sum', 5e-5),
                 'saros': ('saros', 2e-6), 'exeligmos': ('exeligmos', 1e-2), 'lunette': ('jupiter_geo', 5e-4)}
        for p in E.PLANETS:
            tol = 2e-5 if p in ('mercury', 'venus', 'mars') else 2e-3
            pairs['lambda_geo_' + p] = (p + '_geo', tol)
            pairs['helio_' + p] = ('orrery_' + p, tol)
        j = np.arange(E.jours_from_date(1900, 1, 1), E.jours_from_date(2100, 1, 1), 0.37)
        for key, (shaft, tol) in pairs.items():
            slope = np.polyfit(j, E.values(key, j)/(2*math.pi), 1)[0]
            self.assertLess(abs(slope/rates[shaft] - 1.0), tol, f'{key} / {shaft}')

    def test_continuity(self):
        """Angles continus (aucun saut de 2π) au pas de 6 h sur 1900-2100."""
        j = np.arange(E.jours_from_date(1900, 1, 1), E.jours_from_date(2100, 12, 31), 0.25)
        for k in E.ANGLE_KEYS:
            if k in ('gmst', 'mean_solar'):
                continue                                         # plus d'un tour par jour : voir test_gmst
            step = np.abs(np.diff(E.values(k, j)))
            allowed = 2*math.pi/3 + 1e-9 if k == 'exeligmos' else 1.0   # exeligmos : un cran de 120° par saros
            self.assertLess(step.max(), allowed, k)


class TestPlanets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.j, cls.xe, cls.ye, cls.ze = horizons_xyz('earth')

    def test_sun(self):
        ref = np.degrees(np.arctan2(-self.ye, -self.xe))
        err = np.abs(wrap_deg(np.degrees(E.values('lambda_sun', self.j)) - ref)).max()
        REPORT['sun'] = err
        self.assertLess(err, LIMITS_DEG['sun'])
        err_h = np.abs(wrap_deg(np.degrees(E.values('helio_earth', self.j))
                                - np.degrees(np.arctan2(self.ye, self.xe)))).max()
        self.assertLess(err_h, LIMITS_DEG['sun'])

    def test_planets_geocentric_and_heliocentric(self):
        for p in E.PLANETS:
            with self.subTest(planet=p):
                j, x, y, z = horizons_xyz(p)
                np.testing.assert_allclose(j, self.j)
                ref = np.degrees(np.arctan2(y - self.ye, x - self.xe))
                err = np.abs(wrap_deg(np.degrees(E.values('lambda_geo_' + p, j)) - ref))
                err_h = np.abs(wrap_deg(np.degrees(E.values('helio_' + p, j)) - np.degrees(np.arctan2(y, x))))
                REPORT[p] = err.max()
                REPORT[p + ' (<= 2050)'] = err[j <= E.jours_from_date(2050, 1, 1)].max()
                REPORT['helio_' + p] = err_h.max()
                self.assertLess(err.max(), LIMITS_DEG[p])
                self.assertLess(err_h.max(), LIMITS_DEG[p])

    def test_lunette(self):
        j = np.linspace(0, 36525, 50)
        np.testing.assert_allclose(E.values('lunette', j), E.values('lambda_geo_jupiter', j) + np.pi/2)


class TestMoon(unittest.TestCase):
    def test_meeus_example_47a(self):
        j = np.array([2448724.5 - E.J2000])                     # 1992-04-12 0 h TD
        lam, beta, r = E.moon_of_date(j)
        self.assertAlmostEqual(math.degrees(lam[0]) % 360, 133.162655, places=5)
        self.assertAlmostEqual(math.degrees(beta[0]), -3.229126, places=5)
        self.assertAlmostEqual(r[0], 368409.7, delta=0.1)

    def test_against_nasa_eclipses(self):
        """Au maximum d'une éclipse, la Lune est au plus près du Soleil (ou de l'ombre) : la composante de
        l'écart le long de la trace relative, x + y·ẏ/ẋ, mesure l'erreur en longitude de la Lune."""
        for kind, target in (('solar', 0.0), ('lunar', math.pi)):
            j = nasa_eclipses(kind)[:, 0]

            def xy(jj):
                beta = E.moon_of_date(jj)[1]
                dl = E._wrap(E.values('lambda_moon', jj) - E.values('lambda_sun', jj) - target)
                return dl*np.cos(beta), beta
            h = 0.01
            x, y = xy(j)
            (x1, y1), (x0, y0) = xy(j + h), xy(j - h)
            res = np.degrees(x + y*(y1 - y0)/(x1 - x0))
            REPORT['moon ' + kind] = np.abs(res).max()
            self.assertGreater(len(j), 200)
            self.assertLess(np.abs(res).max(), LIMITS_DEG['moon'])

    def test_all_phases_against_almanac(self):
        """Toutes phases (quadratures et octants compris, où la variation culmine), 2000-2100 au pas de 0,1 j :
        écart à la formule basse précision de l'Astronomical Almanac (théorie de Brown, ~0,3° ; équinoxe de
        la date), théorie indépendante de la série de Meeus."""
        j = np.arange(0.0, 36525.0, 0.1)
        T = j/36525.0
        terms = ((6.29, 135.0, 477198.87), (-1.27, 259.3, -413335.36), (0.66, 235.7, 890534.22),
                 (0.21, 269.9, 954397.74), (-0.19, 357.5, 35999.05), (-0.11, 186.5, 966404.03))
        lam = 218.32 + 481267.881*T + sum(a*np.sin(np.radians(c0 + c1*T)) for a, c0, c1 in terms)
        # repère J2000 de la clé → équinoxe de la date : + p_A (IAU 2006)
        pa = (5028.796195*T + 1.1054348*T*T)/3600.0
        err = np.abs(wrap_deg(np.degrees(E.values('lambda_moon', j)) + pa - lam))
        REPORT['moon vs almanac (all phases)'] = err.max()
        self.assertLess(err.max(), 0.45)
        self.assertLess(float(np.sqrt(np.mean(err**2))), 0.15)

    def test_gamma_against_nasa(self):
        """γ (rayons terrestres) ≈ K · (r sin F / r moyen), K ≈ sin i · cos 5,3° · r moyen / R⊕ ≈ 5,3."""
        for kind in ('solar', 'lunar'):
            a = nasa_eclipses(kind)
            g = E.values('gamma', a[:, 0])
            k = float(np.sum(g*a[:, 1])/np.sum(g*g))
            err = np.abs(k*g - a[:, 1]).max()
            REPORT['gamma ' + kind] = err
            self.assertTrue(5.2 < k < 5.4, k)
            self.assertLess(err, 0.05)
            big = np.abs(a[:, 1]) > 0.05
            np.testing.assert_array_equal(np.sign(g[big]), np.sign(a[big, 1]))

    def test_node_perigee_elong(self):
        j = np.array([0.0, 36525.0])
        pa = (5028.796195 + 1.1054348)/3600                     # p_A sur un siècle (°)
        node = np.degrees(np.diff(E.values('node', j)))[0]
        self.assertAlmostEqual(node, -1934.1362891 + 0.0020754 - pa, delta=1e-4)
        per = np.degrees(np.diff(E.values('perigee', j)))[0]    # L' − M' (termes en T et T²)
        self.assertAlmostEqual(per, 481267.88123421 - 477198.8675055 - 0.0015786 - 0.0087414 - pa, delta=1e-4)
        j = np.linspace(-36525, 36525, 1001)
        np.testing.assert_allclose(E.values('elong', j), E.values('lambda_moon', j) - E.values('lambda_sun', j))
        self.assertTrue(np.all(np.diff(E.values('elong', np.arange(0, 3000, 0.1))) > 0))


class TestEarthTime(unittest.TestCase):
    def test_gmst(self):
        self.assertAlmostEqual(math.degrees(E.value('gmst', 0.0)), 280.46061837, places=9)
        for j0 in (-36525.0, 0.0, 9772.5, 36525.0):
            rate = (E.value('gmst', j0 + 1.0) - E.value('gmst', j0))/(2*math.pi)
            self.assertAlmostEqual(rate, 1.00273790935, delta=1e-10)
        # Meeus 12.a : 1987-04-10 0 h UT -> 13 h 10 min 46,3668 s
        g = math.degrees(E.value('gmst', E.jours_from_date(1987, 4, 10))) % 360
        self.assertAlmostEqual(g, (13 + 10/60 + 46.3668/3600)*15, delta=1e-5)

    def test_mean_solar(self):
        for d in ((2026, 10, 4), (1900, 3, 1), (2099, 12, 31)):
            v = E.value('mean_solar', E.jours_from_date(*d)) % (2*math.pi)
            self.assertAlmostEqual(min(v, 2*math.pi - v), 0.0, places=9)
        v = E.value('mean_solar', E.jours_from_date(2026, 10, 4.75)) % (2*math.pi)
        self.assertAlmostEqual(v, 1.5*math.pi, places=9)

    def test_precession(self):
        self.assertEqual(E.value('prec', 0.0), 0.0)
        p = math.degrees(E.value('prec', 36525.0))*3600
        self.assertAlmostEqual(p, -(5028.796195 + 1.1054348), places=6)

    def test_equation_of_time(self):
        j = np.arange(E.jours_from_date(1900, 1, 1), E.jours_from_date(2101, 1, 1), 0.5)
        eot = E.values('eot', j)
        REPORT['eot range (min)'] = (round(float(eot.min()), 3), round(float(eot.max()), 3))
        self.assertGreaterEqual(eot.min(), -15.0)
        self.assertLessEqual(eot.max(), 17.0)
        with open(os.path.join(V2, 'research', 'constants.json')) as fh:
            ext = json.load(fh)['earth']['equation_of_time']['extremes_2026']
        j26 = np.arange(E.jours_from_date(2026, 1, 1), E.jours_from_date(2027, 1, 1), 1/24)
        e26 = E.values('eot', j26)
        self.assertAlmostEqual(e26.min(), ext['min_minutes'], delta=0.05)
        self.assertAlmostEqual(e26.max(), ext['max_minutes'], delta=0.05)
        for key, fn in (('min_date', np.argmin), ('max_date', np.argmax)):
            y, m, d = E.civil_date(j26[fn(e26)])
            self.assertEqual('%04d-%02d-%02d' % (y, m, d), ext[key])


class TestCalendar(unittest.TestCase):
    STEP = 2*math.pi/366

    def ring(self, y, m, d):
        return E.value('cal_ring', E.jours_from_date(y, m, d + 0.5))

    def test_weekday_2026_10_04_is_sunday(self):
        v = E.value('weekday', E.jours_from_date(2026, 10, 4.5))
        self.assertEqual(round(v/(2*math.pi/7)) % 7, 0)
        self.assertEqual(int(E.weekday(E.jours_from_date(2026, 10, 4.5))), 0)

    def test_civil_date_and_weekday_exact_1900_2100(self):
        d0 = datetime.date(1900, 1, 1)
        n = (datetime.date(2100, 12, 31) - d0).days + 1
        j = E.jours_from_date(1900, 1, 1) + np.arange(n)            # minuit pile : début du jour
        y, m, d = E.civil_date(j)
        wd = E.weekday(j)
        dates = [d0 + datetime.timedelta(days=int(k)) for k in range(n)]
        self.assertEqual(list(y), [t.year for t in dates])
        self.assertEqual(list(m), [t.month for t in dates])
        self.assertEqual(list(d), [t.day for t in dates])
        self.assertEqual(list(wd), [t.isoweekday() % 7 for t in dates])
        steps = np.round(np.diff(E.values('weekday', j))/(2*math.pi/7))
        self.assertTrue(np.all(steps == 1))

    def test_cal_ring_february(self):
        for y in range(1900, 2101):
            # du 28 février au lendemain (1er mars ou 29 février) : 2 crans (commune) ou 1 (bissextile)
            feb28 = E.jours_from_date(y, 2, 28.5)
            jump = (E.value('cal_ring', feb28 + 1.0) - E.value('cal_ring', feb28))/self.STEP
            self.assertAlmostEqual(jump, 1.0 if E.is_leap(y) else 2.0, places=9, msg=y)
            self.assertAlmostEqual((self.ring(y, 3, 1) - self.ring(y, 2, 28))/self.STEP, 2.0, places=9)
            self.assertAlmostEqual((self.ring(y + 1, 1, 1) - self.ring(y, 12, 31))/self.STEP, 1.0, places=9)
        self.assertAlmostEqual(self.ring(2026, 1, 1) % (2*math.pi), 0.0, places=9)
        self.assertAlmostEqual(self.ring(2026, 12, 31) % (2*math.pi), 365*self.STEP, places=9)
        self.assertEqual([bool(E.is_leap(y)) for y in (1900, 2000, 2024, 2026, 2100)],
                         [False, True, True, False, False])

    def test_years(self):
        for y in (1900, 1999, 2026, 2100):
            v = E.value('years', E.jours_from_date(y, 6, 1)) % (2*math.pi)
            self.assertAlmostEqual(v, 2*math.pi*(y % 100)/100, places=9)

    def test_saros_exeligmos(self):
        # nouvelle Lune du 2000-01-06 vers 18 h 14 : k passe de −1 à 0
        self.assertEqual(int(E.lunation_index(E.jours_from_date(2000, 1, 6.5))), -1)
        self.assertEqual(int(E.lunation_index(E.jours_from_date(2000, 1, 7.0))), 0)
        j = np.arange(0.0, 40000.0, 0.5)
        k = E.lunation_index(j)
        self.assertTrue(set(np.diff(k)) <= {0, 1})
        np.testing.assert_allclose(E.values('saros', j) % (2*np.pi), 2*np.pi*(k % 223)/223, atol=1e-9)
        np.testing.assert_allclose(E.values('exeligmos', j) % (2*np.pi), 2*np.pi*((k//223) % 3)/3, atol=1e-9)
        self.assertLessEqual(abs((k[-1] - k[0]) - 40000.0/29.530589), 1.0)


class TestGalilean(unittest.TestCase):
    def test_laplace_and_nu(self):
        """ν = λ_Io − 2λ_Eu (arbre « nu » de trains.json) ; conjonctions Io-Europe à −ν, Europe-Ganymède à π − ν."""
        j = np.linspace(-36525, 36525, 101)
        io, eu, ga = (E.values('jup_' + n, j) for n in ('io', 'europa', 'ganymede'))
        nu = E.values('jup_nu', j)
        lap = io - 3*eu + 2*ga
        self.assertLess(np.abs(np.degrees(E._wrap(lap - math.pi))).max(), 1e-3)
        np.testing.assert_allclose(nu, io - 2*eu)
        self.assertLess(np.abs(E._wrap(eu - 2*ga - nu + math.pi)).max(), 1e-4)
        # conjonctions repérées par balayage (pas 0,01 j, interpolation linéaire) : la longitude commune vaut
        # −ν pour Io-Europe et π − ν pour Europe-Ganymède
        jj = np.arange(0.0, 400.0, 0.01)
        for ka, kb, off in (('jup_io', 'jup_europa', 0.0), ('jup_europa', 'jup_ganymede', math.pi)):
            sep = E._wrap(E.values(ka, jj) - E.values(kb, jj))
            idx = np.nonzero((sep[:-1] < 0) & (sep[1:] >= 0))[0]
            tc = jj[idx] - sep[idx]*0.01/(sep[idx + 1] - sep[idx])
            self.assertGreater(len(tc), 50)
            dev = E._wrap(E.values(kb, tc) - (off - E.values('jup_nu', tc)))
            self.assertLess(np.abs(np.degrees(dev)).max(), 0.01, ka + '/' + kb)

    def test_rates_match_constants(self):
        with open(os.path.join(V2, 'research', 'constants.json')) as fh:
            moons = json.load(fh)['galilean']['moons']
        for n in ('io', 'europa', 'ganymede', 'callisto'):
            rate = (E.value('jup_' + n, 1000.0) - E.value('jup_' + n, 0.0))/(2*math.pi*1000.0)
            self.assertAlmostEqual(rate, moons[n]['turns_per_day_sidereal'], delta=1e-12)
        nu = (E.value('jup_nu', 1000.0) - E.value('jup_nu', 0.0))/1000.0
        self.assertAlmostEqual(math.degrees(nu), 0.739506321, delta=1e-8)

    def test_meeus_example_44(self):
        """1992-12-16 0 h UT (JDE 2448972,50068) : X vus de la Terre (rayons joviens, + vers l'ouest),
        Meeus ex. 44.b : −3,45 ; +7,44 ; +1,20 ; +7,07. L'écart restant vient des termes périodiques de E5
        absents des longitudes moyennes ; seuil par lune = a·sin(amplitude de ces termes) + arrondi 0,01
        (Io ~0,5°, Europe ~1,06°, Ganymède ~0,3°, Callisto ~0,84°, plafonné à 0,3). Sans le décalage
        B1950 -> J2000, Ganymède (0,19) et Callisto (0,54) sortiraient des seuils."""
        j = 2448972.50068 - E.J2000
        xj, yj, zj, _ = E._planet('jupiter', j)
        xe, ye, ze, _ = E._planet('earth', j)
        tau = 0.0057755183*math.sqrt((xj - xe)**2 + (yj - ye)**2 + (zj - ze)**2)   # temps de lumière (j)
        lam_j = E.value('lunette', j) - math.pi/2
        for n, a, x_ref, tol in (('io', 5.9057, -3.45, 0.06), ('europa', 9.3966, 7.44, 0.19),
                                 ('ganymede', 14.9883, 1.20, 0.09), ('callisto', 26.3627, 7.07, 0.3)):
            x = -a*math.sin(E.value('jup_' + n, j - tau) - lam_j)
            REPORT['X ' + n + ' (R_J)'] = abs(x - x_ref)
            self.assertLess(abs(x - x_ref), tol, n)


def tearDownModule():
    if REPORT:
        print('\n[ephem] erreurs maximales mesurées (°, sauf mention) :', file=sys.stderr)
        for k, v in REPORT.items():
            print(f'  {k:28s} {v if isinstance(v, tuple) else round(float(v), 4)}', file=sys.stderr)


if __name__ == '__main__':
    unittest.main()
