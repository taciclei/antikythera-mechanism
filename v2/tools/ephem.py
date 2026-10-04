"""Éphémérides de l'Anticythère 2.0 (module « ephem », voir blender/CONTRACT.md).

Angles des sorties non linéaires de la machine en fonction de ``jours`` = jours depuis J2000.0
(2000-01-01 12:00 TT, sans ΔT : la même échelle sert de TT et de temps civil). Précision modeste,
1900-2100, sans réseau.

API partagée
------------
- ``KEYS`` : liste des clés ;
- ``value(key, jours)`` -> float ; ``values(key, jours_array)`` -> numpy.ndarray ;
- ``jd_from_date(y, m, d)`` (jour julien, calendrier grégorien proleptique, ``d`` peut être fractionnaire :
  ``jd_from_date(2000, 1, 1.5) == 2451545.0``) ; ``jours_from_date(y, m, d)`` = jd − 2451545,0.

Conventions
-----------
- Clés d'angle en radians, sens astronomique direct (longitudes croissantes), repère fixe écliptique et
  équinoxe moyens J2000.
- **Les angles sont continus (non repliés)** : une longitude passe de 2π à 2π + ε, pas à ε. Leur valeur
  modulo 2π est la position définie par le contrat. On peut donc les cuire directement en images clés.
  Les clés de calendrier sont cumulatives et en escalier (un cran par jour, par an, par lunaison…).
- ``eot`` en minutes (temps solaire vrai − temps solaire moyen) ; ``gamma`` sans dimension (r·sin F / r moyen).
- ``jup_nu`` = λ_Io − 2·λ_Europe (arbre « nu » de trains.json) : conjonctions Io-Europe à −ν.

Modèles et sources
------------------
- Planètes : éléments képlériens et taux séculaires de la table 1 de JPL « Approximate Positions of the
  Planets » (research/sources/jpl_approx_pos_2026-10-03.txt, 1800-2050, taux séculaires prolongés au-delà) ;
  barycentre Terre-Lune pris pour la Terre ; longitudes géométriques (sans temps de lumière ni aberration).
- Lune : Meeus, *Astronomical Algorithms*, ch. 47 (ELP-2000/82 tronquée, tables 47.A et 47.B complètes,
  ~10″), ramenée de l'équinoxe de la date au repère J2000 en retirant la précession générale p_A.
- Précession générale p_A : IAU 2006 (Capitaine et al. 2003), termes en T et T².
- Temps sidéral moyen : formule IAU 1982 sous la forme de Meeus (12.4).
- Équation du temps : longitude moyenne du Soleil (Meeus 28.2) moins ascension droite du Soleil vrai.
- Lunes galiléennes : longitudes moyennes de la théorie E5 (Lieske 1998, Meeus ch. 44), référées à B1950,
  décalées de la précession B1950 -> J2000 ; jovicentriques, géométriques.
- Calendrier : grégorien proleptique, exact.
"""
import math

import numpy as np

J2000 = 2451545.0
DEG = math.pi/180.0
TWO_PI = 2.0*math.pi
ARCSEC = DEG/3600.0
DAYS_PER_CY = 36525.0
EPS_DAY = 1e-6          # tolérance (jour) aux frontières de minuit pour les clés de calendrier


def _wrap(a):
    """Ramène un angle (radians) dans ]−π, π]."""
    return np.pi - np.mod(np.pi - a, TWO_PI)


def _T(jours):
    """Siècles juliens depuis J2000.0."""
    return np.asarray(jours, dtype=float)/DAYS_PER_CY


# ------------------------------------------------------------------ temps et calendrier grégorien

def jd_from_date(y, m, d):
    """Jour julien d'une date du calendrier grégorien proleptique (``d`` fractionnaire : 1.5 = 1er à midi)."""
    y, m = int(y), int(m)
    if m <= 2:
        y -= 1
        m += 12
    a = y//100
    b = 2 - a + a//4
    return math.floor(365.25*(y + 4716)) + math.floor(30.6001*(m + 1)) + float(d) + b - 1524.5


def jours_from_date(y, m, d):
    """Jours depuis J2000.0 (2000-01-01 12:00) d'une date grégorienne (``d`` fractionnaire possible)."""
    return jd_from_date(y, m, d) - J2000


def _day_number(jours):
    """Numéro du jour julien civil (entier, change à minuit) ; tolérance EPS_DAY avant minuit."""
    return np.floor(np.asarray(jours, dtype=float) + J2000 + 0.5 + EPS_DAY).astype(np.int64)


def civil_date(jours):
    """Date civile grégorienne (année, mois, jour) de chaque instant, en tableaux d'entiers.

    Algorithme de Fliegel et Van Flandern (valable pour tout numéro de jour julien positif)."""
    j = _day_number(jours)
    f = j + 1401 + (((4*j + 274277)//146097)*3)//4 - 38
    e = 4*f + 3
    g = (e % 1461)//4
    h = 5*g + 2
    day = (h % 153)//5 + 1
    month = ((h//153 + 2) % 12) + 1
    year = e//1461 - 4716 + (12 + 2 - month)//12
    return year, month, day


def is_leap(y):
    """Année bissextile grégorienne (fonctionne sur des tableaux)."""
    y = np.asarray(y)
    return (y % 4 == 0) & ((y % 100 != 0) | (y % 400 == 0))


# rang du premier jour de chaque mois sur l'anneau de 366 cases (disposition d'une année bissextile)
_MONTH_START_366 = np.array([0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], dtype=np.int64)


def day_index_366(jours):
    """Rang du jour sur l'anneau des dates de 366 cases : 1er janvier = 0, 29 février = 59, 1er mars = 60,
    31 décembre = 365. Les années communes sautent la case 59 (28 février -> 1er mars : deux crans)."""
    year, month, day = civil_date(jours)
    return year, _MONTH_START_366[month - 1] + day - 1


def weekday(jours):
    """Jour de la semaine : 0 = dimanche, 1 = lundi, …, 6 = samedi."""
    return (_day_number(jours) + 1) % 7


# ------------------------------------------------------------------ précession générale (IAU 2006)

P_A_ARCSEC = (5028.796195, 1.1054348)      # ″/siècle, ″/siècle² (Capitaine et al. 2003)


def p_A(jours):
    """Précession générale en longitude accumulée depuis J2000 (radians)."""
    T = _T(jours)
    return (P_A_ARCSEC[0]*T + P_A_ARCSEC[1]*T*T)*ARCSEC


# ------------------------------------------------------------------ planètes : JPL, table 1 (1800-2050)

# a (ua), e, I (°), L (°), varpi (°), Omega (°) ; puis les taux par siècle julien
_JPL_T1 = {
    'mercury': ((0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
                (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081)),
    'venus': ((0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
              (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418)),
    'earth': ((1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
              (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0)),
    'mars': ((1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
             (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343)),
    'jupiter': ((5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
                (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106)),
    'saturn': ((9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
               (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794)),
    'uranus': ((19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503),
               (-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589)),
    'neptune': ((30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574),
                (0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664)),
}
PLANETS = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']


def kepler_E(M, e, iterations=8):
    """Anomalie excentrique (Newton) pour M (radians) et e < 1 ; vectorisé."""
    M = np.asarray(M, dtype=float)
    E = M + e*np.sin(M)
    for _ in range(iterations):
        E = E - (E - e*np.sin(E) - M)/(1.0 - e*np.cos(E))
    return E


def orbit_xyz(a, e, inc, node, argp, M):
    """Position héliocentrique écliptique (ua) depuis des éléments (angles en radians), vectorisé."""
    E = kepler_E(M, e)
    xp = a*(np.cos(E) - e)
    yp = a*np.sqrt(1.0 - e*e)*np.sin(E)
    co, so, cn, sn = np.cos(argp), np.sin(argp), np.cos(node), np.sin(node)
    ci, si = np.cos(inc), np.sin(inc)
    x = (co*cn - so*sn*ci)*xp + (-so*cn - co*sn*ci)*yp
    y = (co*sn + so*cn*ci)*xp + (-so*sn + co*cn*ci)*yp
    z = (so*si)*xp + (co*si)*yp
    return x, y, z


def _planet(name, jours):
    """(x, y, z) héliocentriques J2000 (ua) et longitude moyenne continue L (rad) d'une planète."""
    el, rate = _JPL_T1[name]
    T = _T(jours)
    a, e, inc, L, varpi, node = (el[k] + rate[k]*T for k in range(6))
    inc, L, varpi, node = inc*DEG, L*DEG, varpi*DEG, node*DEG
    x, y, z = orbit_xyz(a, e, inc, node, varpi - node, _wrap(L - varpi))
    return x, y, z, L


def helio_longitude(name, jours):
    """Longitude héliocentrique écliptique J2000 (rad, continue) ; 'earth' = barycentre Terre-Lune."""
    x, y, z, L = _planet(name, jours)
    return L + _wrap(np.arctan2(y, x) - L)


def sun_longitude(jours):
    """Longitude géométrique géocentrique du Soleil, J2000 (rad, continue)."""
    return helio_longitude('earth', jours) + np.pi


def geo_longitude(name, jours):
    """Longitude géocentrique écliptique J2000 d'une planète (rad, continue).

    Le dépliage s'appuie sur une référence continue : le Soleil pour Mercure et Vénus (élongation bornée),
    la longitude héliocentrique pour les planètes extérieures (écart < 90°)."""
    x, y, z, L = _planet(name, jours)
    xe, ye, ze, Le = _planet('earth', jours)
    lam = np.arctan2(y - ye, x - xe)
    if name in ('mercury', 'venus'):
        ref = Le + _wrap(np.arctan2(ye, xe) - Le) + np.pi
    else:
        ref = L + _wrap(np.arctan2(y, x) - L)
    return ref + _wrap(lam - ref)


# ------------------------------------------------------------------ Lune : Meeus ch. 47 (ELP-2000/82 tronquée)

# Table 47.A : D, M, M', F, Σl (1e-6 °), Σr (1e-3 km)
_MOON_LR = np.array([
    (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111), (2, 0, 0, 0, 658314, -2955968),
    (0, 0, 2, 0, 213618, -569925), (0, 1, 0, 0, -185116, 48888), (0, 0, 0, 2, -114332, -3149),
    (2, 0, -2, 0, 58793, 246158), (2, -1, -1, 0, 57066, -152138), (2, 0, 1, 0, 53322, -170733),
    (2, -1, 0, 0, 45758, -204586), (0, 1, -1, 0, -40923, -129620), (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755), (2, 0, 0, -2, 15327, 10321), (0, 0, 1, 2, -12528, 0),
    (0, 0, 1, -2, 10980, 79661), (4, 0, -1, 0, 10675, -34782), (0, 0, 3, 0, 10034, -23210),
    (4, 0, -2, 0, 8548, -21636), (2, 1, -1, 0, -7888, 24208), (2, 1, 0, 0, -6766, 30824),
    (1, 0, -1, 0, -5163, -8379), (1, 1, 0, 0, 4987, -16675), (2, -1, 1, 0, 4036, -12831),
    (2, 0, 2, 0, 3994, -10445), (4, 0, 0, 0, 3861, -11650), (2, 0, -3, 0, 3665, 14403),
    (0, 1, -2, 0, -2689, -7003), (2, 0, -1, 2, -2602, 0), (2, -1, -2, 0, 2390, 10056),
    (1, 0, 1, 0, -2348, 6322), (2, -2, 0, 0, 2236, -9884), (0, 1, 2, 0, -2120, 5751),
    (0, 2, 0, 0, -2069, 0), (2, -2, -1, 0, 2048, -4950), (2, 0, 1, -2, -1773, 4130),
    (2, 0, 0, 2, -1595, 0), (4, -1, -1, 0, 1215, -3958), (0, 0, 2, 2, -1110, 0),
    (3, 0, -1, 0, -892, 3258), (2, 1, 1, 0, -810, 2616), (4, -1, -2, 0, 759, -1897),
    (0, 2, -1, 0, -713, -2117), (2, 2, -1, 0, -700, 2354), (2, 1, -2, 0, 691, 0),
    (2, -1, 0, -2, 596, 0), (4, 0, 1, 0, 549, -1423), (0, 0, 4, 0, 537, -1117),
    (4, -1, 0, 0, 520, -1571), (1, 0, -2, 0, -487, -1739), (2, 1, 0, -2, -399, 0),
    (0, 0, 2, -2, -381, -4421), (1, 1, 1, 0, 351, 0), (3, 0, -2, 0, -340, 0),
    (4, 0, -3, 0, 330, 0), (2, -1, 2, 0, 327, 0), (0, 2, 1, 0, -323, 1165),
    (1, 1, -1, 0, 299, 0), (2, 0, 3, 0, 294, 0), (2, 0, -1, -2, 0, 8752)], dtype=float)

# Table 47.B : D, M, M', F, Σb (1e-6 °)
_MOON_B = np.array([
    (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693), (2, 0, 0, -1, 173237),
    (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271), (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198),
    (2, 0, 1, -1, 9266), (0, 0, 2, -1, 8822), (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324),
    (2, 0, 1, 1, 4200), (2, 1, 0, -1, -3359), (2, -1, -1, 1, 2463), (2, -1, 0, 1, 2211),
    (2, -1, -1, -1, 2065), (0, 1, -1, -1, -1870), (4, 0, -1, -1, 1828), (0, 1, 0, 1, -1794),
    (0, 0, 0, 3, -1749), (0, 1, -1, 1, -1565), (1, 0, 0, 1, -1491), (0, 1, 1, 1, -1475),
    (0, 1, 1, -1, -1410), (0, 1, 0, -1, -1344), (1, 0, 0, -1, -1335), (0, 0, 3, 1, 1107),
    (4, 0, 0, -1, 1021), (4, 0, -1, 1, 833), (0, 0, 1, -3, 777), (4, 0, -2, 1, 671),
    (2, 0, 0, -3, 607), (2, 0, 2, -1, 596), (2, -1, 1, -1, 491), (2, 0, -2, 1, -451),
    (0, 0, 3, -1, 439), (2, 0, 2, 1, 422), (2, 0, -3, -1, 421), (2, 1, -1, 1, -366),
    (2, 1, 0, 1, -351), (4, 0, 0, 1, 331), (2, -1, 1, 1, 315), (2, -2, 0, -1, 302),
    (0, 0, 1, 3, -283), (2, 1, 1, -1, -229), (1, 1, 0, -1, 223), (1, 1, 0, 1, 223),
    (0, 1, -2, -1, -220), (2, 1, -1, -1, -220), (1, 0, 1, 1, -185), (2, -1, -2, -1, 181),
    (0, 1, 2, 1, -177), (4, 0, -2, -1, 176), (4, -1, -1, -1, 166), (1, 0, 1, -1, -164),
    (4, 0, 1, -1, 132), (1, 0, -1, -1, -119), (4, -1, 0, -1, 115), (2, -2, 0, 1, 107)], dtype=float)

MOON_MEAN_DISTANCE_KM = 385000.56


def _poly(T, *c):
    """Polynôme de Horner en T (coefficients croissants)."""
    out = np.zeros_like(T)
    for ck in reversed(c):
        out = out*T + ck
    return out


def moon_arguments(jours):
    """Arguments moyens de Meeus 47 (radians, équinoxe de la date, continus) : L', D, M, M', F, Ω."""
    T = _T(jours)
    Lp = _poly(T, 218.3164477, 481267.88123421, -0.0015786, 1/538841, -1/65194000)
    D = _poly(T, 297.8501921, 445267.1114034, -0.0018819, 1/545868, -1/113065000)
    M = _poly(T, 357.5291092, 35999.0502909, -0.0001536, 1/24490000)
    Mp = _poly(T, 134.9633964, 477198.8675055, 0.0087414, 1/69699, -1/14712000)
    F = _poly(T, 93.2720950, 483202.0175233, -0.0036539, -1/3526000, 1/863310000)
    Om = _poly(T, 125.0445479, -1934.1362891, 0.0020754, 1/467441, -1/60616000)
    return tuple(v*DEG for v in (Lp, D, M, Mp, F, Om))


def moon_of_date(jours):
    """Lune géocentrique, équinoxe moyen de la date : (λ rad continue, β rad, distance km)."""
    T = _T(jours)
    Lp, D, M, Mp, F, Om = moon_arguments(jours)
    E = 1.0 - 0.002516*T - 0.0000074*T*T
    A1 = (119.75 + 131.849*T)*DEG
    A2 = (53.09 + 479264.290*T)*DEG
    A3 = (313.45 + 481266.484*T)*DEG
    sl = 3958*np.sin(A1) + 1962*np.sin(Lp - F) + 318*np.sin(A2)
    sr = np.zeros_like(T)
    for d, m, mp, f, cl, cr in _MOON_LR:
        arg = d*D + m*M + mp*Mp + f*F
        ef = E**abs(m)
        if cl:
            sl = sl + cl*ef*np.sin(arg)
        if cr:
            sr = sr + cr*ef*np.cos(arg)
    sb = (-2235*np.sin(Lp) + 382*np.sin(A3) + 175*np.sin(A1 - F) + 175*np.sin(A1 + F)
          + 127*np.sin(Lp - Mp) - 115*np.sin(Lp + Mp))
    for d, m, mp, f, cb in _MOON_B:
        sb = sb + cb*E**abs(m)*np.sin(d*D + m*M + mp*Mp + f*F)
    return Lp + sl*1e-6*DEG, sb*1e-6*DEG, MOON_MEAN_DISTANCE_KM + sr*1e-3


def moon_longitude(jours):
    """Longitude géocentrique vraie de la Lune, repère J2000 (rad, continue)."""
    return moon_of_date(jours)[0] - p_A(jours)


def moon_node(jours):
    """Longitude du nœud ascendant moyen de la Lune, repère J2000 (rad, continue, décroissante)."""
    return moon_arguments(jours)[5] - p_A(jours)


def moon_perigee(jours):
    """Longitude du périgée moyen de la Lune (L' − M'), repère J2000 (rad, continue)."""
    Lp, D, M, Mp, F, Om = moon_arguments(jours)
    return Lp - Mp - p_A(jours)


def moon_gamma(jours):
    """Course de la coulisse d'éclipse : r·sin(λ vraie − Ω moyen) / r moyen (sans dimension)."""
    lam, beta, r = moon_of_date(jours)
    return r*np.sin(lam - moon_arguments(jours)[5])/MOON_MEAN_DISTANCE_KM


# ------------------------------------------------------------------ Terre : temps sidéral, équation du temps

GMST_TURNS_PER_DAY = 360.98564736629/360.0      # 1,00273790935… tour par jour solaire moyen


def gmst(jours):
    """Temps sidéral moyen de Greenwich en angle (rad, continu) : IAU 1982 (Meeus 12.4), jours pris en UT."""
    d = np.asarray(jours, dtype=float)
    T = d/DAYS_PER_CY
    deg = 280.46061837 + 360.98564736629*d + 0.000387933*T*T - T*T*T/38710000.0
    return deg*DEG


def obliquity(jours):
    """Obliquité moyenne de l'écliptique (rad), IAU 2006 au premier ordre."""
    T = _T(jours)
    return (84381.406 - 46.836769*T)*ARCSEC


def equation_of_time(jours):
    """Équation du temps (minutes) = temps solaire vrai − temps solaire moyen.

    E = L0 − 0,0057183° − α : L0 longitude moyenne du Soleil (Meeus 28.2, équinoxe de la date), α ascension
    droite du Soleil vrai (longitude J2000 + p_A, aberration −20,5″, obliquité moyenne) ; nutation omise."""
    tau = _T(jours)/10.0
    L0 = _poly(tau, 280.4664567, 360007.6982779, 0.03032028, 1/49931, -1/15300, -1/2000000)*DEG
    lam = sun_longitude(jours) + p_A(jours) - 20.4898*ARCSEC
    eps = obliquity(jours)
    alpha = np.arctan2(np.cos(eps)*np.sin(lam), np.cos(lam))
    E = _wrap(L0 - 0.0057183*DEG - alpha)
    return np.degrees(E)*4.0


# ------------------------------------------------------------------ lunes galiléennes (E5, Meeus ch. 44)

# longitudes moyennes l_i = l0 + n·t, t = JD − 2443000,5 (°, °/j), référées à l'équinoxe B1950
_GALILEAN = {'io': (106.07719, 203.488955790), 'europa': (175.73161, 101.374724735),
             'ganymede': (120.55883, 50.317609207), 'callisto': (84.44459, 21.571071177)}
_E5_EPOCH = 2443000.5
_B1950_TO_J2000 = 1.3966626*0.5 + 0.0003088*0.25     # précession B1950 -> J2000 (°), Meeus 44


def galilean_longitude(moon, jours):
    """Longitude jovicentrique moyenne d'un satellite galiléen, repère J2000 (rad, continue, géométrique)."""
    l0, n = _GALILEAN[moon]
    t = np.asarray(jours, dtype=float) + (J2000 - _E5_EPOCH)
    return (l0 + _B1950_TO_J2000 + n*t)*DEG


def jupiter_nu(jours):
    """ν = λ_Io − 2·λ_Europe (rad, continu, +0,7395 °/j), comme l'arbre « nu » de spec/trains.json
    (« ν = n_Io − 2n_Eu, ligne des conjonctions à −ν ») : les conjonctions Io-Europe tombent à la longitude −ν.
    Par la relation de Laplace (λ_Io − 3λ_Eu + 2λ_Ga = π), λ_Europe − 2·λ_Ganymède = ν − π : les conjonctions
    Europe-Ganymède tombent à π − ν."""
    return galilean_longitude('io', jours) - 2.0*galilean_longitude('europa', jours)


# ------------------------------------------------------------------ clés de calendrier (cumulatives, en escalier)

def _cal_ring(jours):
    year, idx = day_index_366(jours)
    return TWO_PI*(366*(year - 2000) + idx)/366.0


def _weekday(jours):
    # 2451539 = numéro du jour julien d'un dimanche (1999-12-26) : 0 mod 2π le dimanche
    return TWO_PI*(_day_number(jours) - 2451539)/7.0


def _years(jours):
    return TWO_PI*civil_date(jours)[0]/100.0


def lunation_index(jours):
    """Numéro de lunaison k (entier) : 0 à partir de la nouvelle Lune vraie du 2000-01-06 (k de Meeus),
    incrémenté à chaque nouvelle Lune vraie (élongation multiple de 2π)."""
    return np.floor(elongation(jours)/TWO_PI).astype(np.int64)


def elongation(jours):
    """Élongation de la Lune (λ Lune − λ Soleil), rad, continue et croissante."""
    return moon_longitude(jours) - sun_longitude(jours)


def _saros(jours):
    return TWO_PI*lunation_index(jours)/223.0


def _exeligmos(jours):
    return TWO_PI*np.floor_divide(lunation_index(jours), 223)/3.0


# ------------------------------------------------------------------ table des clés

def _geo(name):
    return lambda j: geo_longitude(name, j)


def _helio(name):
    return lambda j: helio_longitude(name, j)


def _gal(name):
    return lambda j: galilean_longitude(name, j)


_FUNCS = {
    'lambda_sun': sun_longitude,
    'lambda_moon': moon_longitude,
    'node': moon_node,
    'perigee': moon_perigee,
    'elong': elongation,
}
_FUNCS.update({'lambda_geo_' + p: _geo(p) for p in PLANETS})
_FUNCS.update({'helio_' + p: _helio(p) for p in PLANETS})
_FUNCS.update({
    'helio_earth': _helio('earth'),
    'prec': lambda j: -p_A(j),
    'gmst': gmst,
    'mean_solar': lambda j: TWO_PI*(np.asarray(j, dtype=float) + 0.5),
    'jup_io': _gal('io'), 'jup_europa': _gal('europa'), 'jup_ganymede': _gal('ganymede'),
    'jup_callisto': _gal('callisto'), 'jup_nu': jupiter_nu,
    'lunette': lambda j: geo_longitude('jupiter', j) + np.pi/2,
    'cal_ring': _cal_ring,
    'weekday': _weekday,
    'years': _years,
    'saros': _saros,
    'exeligmos': _exeligmos,
    'eot': equation_of_time,
    'gamma': moon_gamma,
})

KEYS = list(_FUNCS)
ANGLE_KEYS = [k for k in KEYS if k not in ('eot', 'gamma')]
UNITS = {k: ('min' if k == 'eot' else '1' if k == 'gamma' else 'rad') for k in KEYS}


def values(key, jours_array):
    """Valeurs de la clé ``key`` pour un tableau de ``jours`` depuis J2000.0 (numpy.ndarray de float)."""
    if key not in _FUNCS:
        raise KeyError(f"clé d'éphéméride inconnue : {key!r} (voir ephem.KEYS)")
    j = np.asarray(jours_array, dtype=float)
    return np.asarray(_FUNCS[key](j), dtype=float).reshape(j.shape)


def value(key, jours):
    """Valeur de la clé ``key`` à l'instant ``jours`` (float)."""
    return float(values(key, np.array([float(jours)]))[0])


if __name__ == '__main__':
    j = jours_from_date(2026, 10, 4)
    print(f"2026-10-04 0 h : jours = {j}")
    for k in KEYS:
        v = value(k, j)
        txt = f"{round(math.degrees(v), 6) % 360:10.4f} °" if UNITS[k] == 'rad' else f"{v:10.4f} {UNITS[k]}"
        print(f"  {k:20s} {txt}")
