#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Moteur astronomique de l'explainer « Comment lire la machine d'Anticythère ».

Pur Python 3 + numpy (utiliser le Python de Blender : .../Resources/5.2/python/bin/python3.13).
Ne lit QUE spec/antikythera.json. Il reproduit les lois angulaires des drivers de
build/out/am.blend (validé contre Blender par tools/explainer/validate_blend.py), puis :
  * read(t)          : lectures humaines en français (zodiaque, calendrier, Lune, planètes, cadrans) ;
  * glyph_table(...) : glyphes d'éclipse Σ/Η CALCULÉS PAR NOTRE MODÈLE (et le modèle EYM de Freeth 2014) ;
  * calibrate(...)   : calage des PHASES sur le ciel réel (éléments moyens de Meeus), rapports inchangés ;
  * machine_events() : nouvelles/pleines lunes, éclipses prédites, années des Jeux, rétrogradations ;
  * exports JSON pour la page web (portage JavaScript).

Honnêteté : les trains planétaires, le Soleil vrai et l'aiguille du Dragon sont HYPOTHÉTIQUES
(Freeth et al. 2021) ; les glyphes produits ici sont calculés par notre modèle, sauf la table EYM
(Freeth 2014, PLoS ONE 9(7):e103275) ; la machine n'était PAS un instrument de navigation.

CLI (voir --help) :  --selftest | read | events | glyphs | report | export | all
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / 'spec' / 'antikythera.json'
OUT_DIR = ROOT / 'build' / 'out' / 'explainer'
TAU = 2.0 * math.pi
YEAR_DAYS = 365.2422            # 1 année du modèle (1 tour de b1) = 1 année tropique, en jours
JD_J2000 = 2451545.0            # 2000-01-01 12:00 TT
DAYS_PER_CENTURY = 36525.0
SYNODIC_REAL = 29.530588853     # jours (Meeus, lunaison moyenne à J2000)
EYU_DEG = 360.0 / 446.0         # Freeth 2014 : 1 « Eclipse Year unit » = 1/446 de l'année des éclipses

# ----------------------------------------------------------------------------- libellés (FR)
ZODIAC_FR = ['Bélier', 'Taureau', 'Gémeaux', 'Cancer', 'Lion', 'Vierge', 'Balance',
             'Scorpion', 'Sagittaire', 'Capricorne', 'Verseau', 'Poissons']
EGYPT_MONTHS_FR = ['Thot', 'Phaophi', 'Athyr', 'Choiak', 'Tybi', 'Méchir', 'Phaménoth',
                   'Pharmouthi', 'Pachôn', 'Payni', 'Épiphi', 'Mésorê', 'jours épagomènes']
GAMES_FR = {'ΙΣΘΜΙΑ': 'Jeux isthmiques (Corinthe)', 'ΟΛΥΜΠΙΑ': 'Jeux olympiques (Olympie)',
            'ΝΕΜΕΑ': 'Jeux néméens (Némée)', 'ΠΥΘΙΑ': 'Jeux pythiques (Delphes)',
            'ΝΑΑ': 'Naa (Dodone)', 'ΑΛΙΕΙΑ': 'Halieia (Rhodes)'}


def games_fr(label):
    """Nom français d'un secteur du cadran des Jeux : deux fêtes par année (« ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ »), séparées par
    une espace dans la spec (Freeth et al. 2008 SI ; Iversen 2017)."""
    return ' et '.join(GAMES_FR.get(w, w) for w in label.split())


# les quatre paires historiques (spec dials.back.subsidiary[olympiad].labels) : clés prêtes pour la page web
GAMES_FR.update({p: games_fr(p) for p in ('ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ', 'ΝΕΜΕΑ ΝΑΑ', 'ΙΣΘΜΙΑ ΠΥΘΙΑ', 'ΝΕΜΕΑ ΑΛΙΕΙΑ')})


def olympia_index(labels):
    """Indice du secteur qui porte ΟΛΥΜΠΙΑ (année 1 de l'olympiade)."""
    return next(k for k, lab in enumerate(labels) if 'ΟΛΥΜΠΙΑ' in lab.split())
PLANETS = [('t_mercury', 'mercure', 'Mercure'), ('t_venus', 'venus', 'Vénus'),
           ('t_mars', 'mars', 'Mars'), ('t_jupiter', 'jupiter', 'Jupiter'),
           ('t_saturn', 'saturne', 'Saturne')]
GLYPH_LUNAR, GLYPH_SOLAR = 'Σ', 'Η'     # ΣΕΛΗΝΗ (Lune), ΗΛΙΟΣ (Soleil), comme sur le cadran
HYPO = 'HYPOTHÉTIQUE (Freeth et al. 2021)'

# Éléments moyens rapportés à l'équinoxe moyen de la date (Meeus, Astronomical Algorithms, 2e éd.) ;
# T = siècles juliens depuis J2000.0 (TT). Degrés.
MEEUS = {
    'sun_L0': (280.46646, 36000.76983, 0.0003032),                              # éq. 25.2
    'sun_M': (357.52911, 35999.05029, -0.0001537),                              # éq. 25.3
    'moon_L': (218.3164477, 481267.88123421, -0.0015786, 1 / 538841, -1 / 65194000),   # éq. 47.1
    'moon_D': (297.8501921, 445267.1114034, -0.0018819, 1 / 545868, -1 / 113065000),   # éq. 47.2
    'moon_M': (134.9633964, 477198.8675055, 0.0087414, 1 / 69699, -1 / 14712000),      # éq. 47.4
    'moon_F': (93.2720950, 483202.0175233, -0.0036539, -1 / 3526000, 1 / 863310000),   # éq. 47.5
    'moon_Omega': (125.0445479, -1934.1362891, 0.0020754, 1 / 467441, -1 / 60616000),  # éq. 47.7
    'mercury': (252.250906, 149474.0722491, 0.00030350, 0.000000018),          # table 31.A (L)
    'venus': (181.979801, 58519.2130302, 0.00031014, 0.000000015),
    'earth': (100.466457, 36000.7698278, 0.00030322, 0.000000020),
    'mars': (355.433000, 19141.6964471, 0.00031052, 0.000000016),
    'jupiter': (34.351519, 3036.3027748, 0.00022330, 0.000000037),
    'saturn': (50.077444, 1223.5110686, 0.00051908, -0.000000030),
}

# Repères historiques utilisés pour caler les cadrans arrière (sources dans README.md).
ANCHORS = {
    'saros_FM1': {'date': (-204, 5, 12, 12.0), 'calendar': 'julian',
                  'source': 'Freeth 2014, PLoS ONE 9(7):e103275 : « FM1 at -204 May-12 » (205 av. J.-C.)'},
    'callippic': {'date': (-329, 6, 28, 12.0), 'calendar': 'julian',
                  'source': 'Début du 1er cycle de Callippe : solstice d\'été de 330 av. J.-C. '
                            '(28 juin julien), Evans 1998 p. 186-187'},
    'olympiad': {'first_year': -775,
                 'source': '1re Olympiade : été 776 av. J.-C. (année astronomique -775) ; Jeux en été'},
    'nabonassar_jd': {'jd': 1448638.0,
                      'source': 'Ère de Nabonassar : 1 Thot = mercredi 26 février 747 av. J.-C. (julien), '
                                'JD 1448638 (calcul Meeus ch. 7)'},
}

# Éclipses réelles 2026-2028 : NASA/GSFC (F. Espenak), SEdecade2021.html et LEdecade2021.html,
# instant du maximum en TD (≈ TT).
NASA_ECLIPSES_2026_2028 = [
    ('solaire', '2026-02-17T12:13:05', 'annulaire', 121), ('lunaire', '2026-03-03T11:34:52', 'totale', 133),
    ('solaire', '2026-08-12T17:47:05', 'totale', 126), ('lunaire', '2026-08-28T04:14:04', 'partielle', 138),
    ('solaire', '2027-02-06T16:00:47', 'annulaire', 131), ('lunaire', '2027-02-20T23:14:06', 'pénombrale', 143),
    ('lunaire', '2027-07-18T16:04:09', 'pénombrale', 110), ('solaire', '2027-08-02T10:07:49', 'totale', 136),
    ('lunaire', '2027-08-17T07:14:59', 'pénombrale', 148), ('lunaire', '2028-01-12T04:14:13', 'partielle', 115),
    ('solaire', '2028-01-26T15:08:58', 'annulaire', 141), ('lunaire', '2028-07-06T18:20:57', 'partielle', 120),
    ('solaire', '2028-07-22T02:56:39', 'totale', 146), ('lunaire', '2028-12-31T16:53:15', 'totale', 125),
]
NASA_SOURCES = ['https://eclipse.gsfc.nasa.gov/SEdecade/SEdecade2021.html',
                'https://eclipse.gsfc.nasa.gov/LEdecade/LEdecade2021.html']


# ============================================================================= petits outils
def wrap2pi(x):
    """Angle ramené dans [0, 2π)."""
    return np.mod(x, TAU)


def wrappi(x):
    """Angle ramené dans [-π, π)."""
    return np.mod(np.asarray(x, float) + math.pi, TAU) - math.pi


def deg(x):
    return float(np.degrees(x))


def frac_str(f: Fraction):
    return '%d/%d' % (f.numerator, f.denominator) if f.denominator != 1 else str(f.numerator)


def fmt_angle(d):
    """12.345 -> 12°21′"""
    d = d % 360.0
    a = int(math.floor(d)); m = int(round((d - a) * 60))
    if m == 60:
        a, m = a + 1, 0
    return '%d°%02d′' % (a, m)


# ============================================================================= temps et calendriers
def jd_from_date(y, m, d, hour=0.0, calendar='auto'):
    """Jour julien (Meeus ch. 7). Années astronomiques (0 = 1 av. J.-C.). calendar: auto|julian|gregorian
    (auto = grégorien à partir du 15 octobre 1582)."""
    if calendar == 'auto':
        calendar = 'gregorian' if (y, m, d) >= (1582, 10, 15) else 'julian'
    Y, M = (y - 1, m + 12) if m <= 2 else (y, m)
    B = 0
    if calendar == 'gregorian':
        A = math.floor(Y / 100); B = 2 - A + math.floor(A / 4)
    return math.floor(365.25 * (Y + 4716)) + math.floor(30.6001 * (M + 1)) + d + hour / 24.0 + B - 1524.5


def date_from_jd(jd):
    """(année, mois, jour, heure décimale, calendrier) ; julien avant le 15/10/1582."""
    Z = math.floor(jd + 0.5); F = jd + 0.5 - Z
    if Z < 2299161:
        A, cal = Z, 'julian'
    else:
        al = math.floor((Z - 1867216.25) / 36524.25); A = Z + 1 + al - math.floor(al / 4); cal = 'gregorian'
    B = A + 1524; C = math.floor((B - 122.1) / 365.25); D = math.floor(365.25 * C)
    E = math.floor((B - D) / 30.6001)
    day = B - D - math.floor(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715
    d = int(math.floor(day)); hour = (day - d) * 24.0
    return int(year), int(month), d, hour, cal


def parse_date(s):
    """'2026-08-12', '2026-08-12T17:47', '-204-05-12' (année astronomique) -> JD (TT)."""
    s = s.strip()
    neg = s.startswith('-')
    if neg:
        s = s[1:]
    datepart, _, timepart = s.replace(' ', 'T').partition('T')
    y, m, d = (int(v) for v in datepart.split('-'))
    y = -y if neg else y
    h = 0.0
    if timepart:
        parts = [float(v) for v in timepart.split(':')]
        h = parts[0] + (parts[1] / 60 if len(parts) > 1 else 0) + (parts[2] / 3600 if len(parts) > 2 else 0)
    return jd_from_date(y, m, d, h)


def format_jd(jd, with_time=True):
    jdm = math.floor(jd * 1440.0 + 0.5) / 1440.0 + 1e-7          # arrondi à la minute
    y, m, d, h, cal = date_from_jd(jdm)
    hh = int(h); mm = int((h - hh) * 60.0)
    ys = '%04d' % y if y >= 0 else '-%04d' % (-y)
    s = '%s-%02d-%02d' % (ys, m, d)
    if with_time:
        s += ' %02d:%02d TT' % (hh, mm)
    if cal == 'julian':
        s += ' (julien)'
    if y <= 0:
        s += ' [%d av. J.-C.]' % (1 - y)
    return s


def t_from_jd(jd):
    """Temps de la manivelle (années du modèle) : t = (JD - 2451545.0) / 365.2422."""
    return (np.asarray(jd, float) - JD_J2000) / YEAR_DAYS


def jd_from_t(t):
    return JD_J2000 + np.asarray(t, float) * YEAR_DAYS


def t_from_date(s):
    return float(t_from_jd(parse_date(s)))


def egyptian_date(jd):
    """Date civile égyptienne (année vague de 365 j) comptée depuis l'ère de Nabonassar."""
    n = math.floor(jd + 0.5) - ANCHORS['nabonassar_jd']['jd']       # jours écoulés depuis 1 Thot an 1
    year = int(n // 365) + 1; doy = int(n % 365)
    mi = min(doy // 30, 12)
    return {'annee_nabonassar': year, 'jour_de_l_annee': doy + 1, 'mois_index': mi,
            'mois_fr': EGYPT_MONTHS_FR[mi], 'jour': doy - 30 * mi + 1}


# ============================================================================= ciel réel moyen
def _poly(c, T):
    return sum(ci * T ** i for i, ci in enumerate(c))


def mean_elements(jd):
    """Éléments moyens réels (degrés, non réduits) à la date JD (TT), équinoxe moyen de la date."""
    T = (jd - JD_J2000) / DAYS_PER_CENTURY
    e = {k: _poly(c, T) for k, c in MEEUS.items()}
    e['sun_apogee'] = e['sun_L0'] - e['sun_M'] + 180.0
    e['moon_perigee'] = e['moon_L'] - e['moon_M']
    return e


def mean_rates_deg_per_century():
    return {k: c[1] for k, c in MEEUS.items()}


def lunations_real(jd):
    """Nombre (réel, continu) de lunaisons moyennes depuis J2000 via l'élongation moyenne D de Meeus."""
    return mean_elements(jd)['moon_D'] / 360.0


def mean_new_moon_near(jd):
    """JD de la nouvelle lune moyenne (D ≡ 0) la plus proche de jd."""
    target = 360.0 * round(mean_elements(jd)['moon_D'] / 360.0)
    x = jd
    for _ in range(4):
        x -= (mean_elements(x)['moon_D'] - target) / (MEEUS['moon_D'][1] / DAYS_PER_CENTURY)
    return x


def ecliptic_limits():
    """Limites écliptiques (distance de la Lune au nœud à la syzygie) calculées à partir de la géométrie
    moyenne Terre-Lune-Soleil (ombre agrandie de 2 % à la Danjon/Meeus, inclinaison moyenne 5.145°)."""
    inc = math.radians(5.145)
    k = 0.2725                      # rayon lunaire / rayon terrestre
    cases = {  # (parallaxe lunaire, demi-diamètre solaire, parallaxe solaire) en degrés
        'moyenne': (0.95072, 959.63 / 3600, 8.794 / 3600),
        'min': (0.8986, 959.63 / 1.01671 / 3600, 8.794 / 1.01671 / 3600),     # Lune à l'apogée
        'max': (1.0254, 959.63 / 0.98329 / 3600, 8.794 / 0.98329 / 3600),     # Lune au périgée
    }
    out = {}
    for name, (pm, ss, ps) in cases.items():
        sm = k * pm
        beta_u = 1.02 * (pm - ss + ps) + sm            # ombre + rayon lunaire
        beta_p = 1.02 * (pm + ss + ps) + sm            # pénombre + rayon lunaire
        beta_s = pm - ps + ss + sm                     # éclipse de Soleil visible quelque part
        f = lambda b: math.degrees(math.asin(math.sin(math.radians(b)) / math.sin(inc)))
        out[name] = {'lunaire_ombre': round(f(beta_u), 2), 'lunaire_penombre': round(f(beta_p), 2),
                     'solaire': round(f(beta_s), 2)}
    return out


LIMITS = {
    'solar_deg': 17.0,
    'lunar_deg': round(ecliptic_limits()['moyenne']['lunaire_ombre'], 1),
    'doc': ("Éclipse de Soleil possible si, à la nouvelle lune de la machine, l'aiguille de la Lune est à "
            "moins de 17.0° d'un nœud (aiguille du Dragon) : milieu de la fourchette 15.39°-18.59° donnée par "
            "F. Espenak (NASA, « Periodicity of Solar Eclipses » §1.1 : « within about 17° of a node »). "
            "Éclipse de Lune (partielle ou totale, par l'ombre) possible si, à la pleine lune, la Lune est à "
            "moins de L° d'un nœud, L calculé par ecliptic_limits() à partir de la géométrie moyenne "
            "(ombre = 1.02 × (π_Lune − s_Soleil + π_Soleil), + rayon lunaire, inclinaison 5.145°) ; "
            "fourchette apogée-périgée donnée dans glyphs.json. Les éclipses pénombrales (≈ 17°) ne sont pas "
            "comptées par cette règle."),
}
FREETH_RULE = {
    'lunar_eyu': 20, 'solar_north_eyu': 20, 'solar_south_eyu': 7,
    'doc': ("Règle EYM de Freeth 2014 (PLoS ONE 9(7):e103275) : glyphe lunaire si la pleine lune est à ≤ 20 EYu "
            "du « point nodal », glyphe solaire si la nouvelle lune est à ≤ 20 EYu au NORD du nœud ou ≤ 7 EYu au "
            "SUD (visibilité depuis la Grèce), pas de 2e prédiction lunaire le mois suivant ; 1 EYu = 360°/446 "
            "= 0.807° de distance Soleil-nœud. Appliquée ici aux positions de NOTRE machine."),
}


# ============================================================================= ciel réel (référence)
# Éléments képlériens approchés de JPL (E. M. Standish), table 1 « 1800 AD - 2050 AD », écliptique et équinoxe
# moyens J2000 : https://ssd.jpl.nasa.gov/planets/approx_pos.html  (a [au], e, I, L, long.peri, long.node) + taux/siècle.
JPL_1800_2050 = {
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
}


def _helio_j2000(name, T):
    el0, rt = JPL_1800_2050[name]
    a, e, I, L, wb, Om = (x + y * T for x, y in zip(el0, rt))
    M = math.radians((L - wb + 180) % 360 - 180); w = math.radians(wb - Om)
    I, Om = math.radians(I), math.radians(Om)
    Ecc = M + e * math.sin(M)
    for _ in range(12):
        Ecc -= (Ecc - e * math.sin(Ecc) - M) / (1 - e * math.cos(Ecc))
    xp, yp = a * (math.cos(Ecc) - e), a * math.sqrt(1 - e * e) * math.sin(Ecc)
    cw, sw, cO, sO, cI, sI = math.cos(w), math.sin(w), math.cos(Om), math.sin(Om), math.cos(I), math.sin(I)
    return np.array([(cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp,
                     (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp,
                     (sw * sI) * xp + (cw * sI) * yp])


def real_sky(jd):
    """Longitudes géocentriques réelles approchées (degrés, équinoxe de la date) : Soleil (Meeus ch. 25, ~0.01°),
    Lune (6 principaux termes de Meeus ch. 47, ~0.3°), nœud moyen, planètes (JPL table 1, 1800-2050, ~0.1° ;
    positions géométriques). Référence de comparaison seulement."""
    T = (jd - JD_J2000) / DAYS_PER_CENTURY
    el = mean_elements(jd)
    Ms = math.radians(el['sun_M'])
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Ms) + (0.019993 - 0.000101 * T) * math.sin(2 * Ms)
         + 0.000289 * math.sin(3 * Ms))
    out = {'soleil': (el['sun_L0'] + C) % 360.0}
    D, Mp, F = (math.radians(el[k]) for k in ('moon_D', 'moon_M', 'moon_F'))
    E_ = 1 - 0.002516 * T
    dl = (6.288774 * math.sin(Mp) + 1.274027 * math.sin(2 * D - Mp) + 0.658314 * math.sin(2 * D)
          + 0.213618 * math.sin(2 * Mp) - 0.185116 * E_ * math.sin(Ms) - 0.114332 * math.sin(2 * F))
    out['lune'] = (el['moon_L'] + dl) % 360.0
    out['noeud'] = el['moon_Omega'] % 360.0
    prec = 1.396971 * T + 0.0003086 * T * T          # précession générale en longitude (J2000 -> date)
    earth = _helio_j2000('earth', T)
    for name, key in (('mercury', 'mercure'), ('venus', 'venus'), ('mars', 'mars'), ('jupiter', 'jupiter'),
                      ('saturn', 'saturne')):
        v = _helio_j2000(name, T) - earth
        out[key] = (math.degrees(math.atan2(v[1], v[0])) + prec) % 360.0
    return out


def compare_sky(m, date_from='2026-01-01', date_to='2028-12-31', step_days=1.0):
    """Écarts machine calée − ciel réel (degrés) jour par jour : max, moyenne absolue ; et dates de début de
    rétrogradation réelles vs machine."""
    jds = np.arange(parse_date(date_from), parse_date(date_to) + 1e-9, step_days)
    keys = {'soleil_vrai': 'soleil', 'soleil_moyen': 'soleil', 'lune': 'lune', 'noeud_ascendant': 'noeud',
            'mercure': 'mercure', 'venus': 'venus', 'mars': 'mars', 'jupiter': 'jupiter', 'saturne': 'saturne'}
    Lm = m.longitudes(t_from_jd(jds))
    real = [real_sky(j) for j in jds]
    stats = {}
    for mk, rk in keys.items():
        err = np.array([((math.degrees(float(Lm[mk][i])) - real[i][rk] + 180) % 360) - 180 for i in range(len(jds))])
        stats[mk] = {'ecart_max_deg': round(float(np.max(np.abs(err))), 3),
                     'ecart_moyen_abs_deg': round(float(np.mean(np.abs(err))), 3),
                     'ecart_moyen_deg': round(float(np.mean(err)), 3)}
    stations = {}
    for key in ('mercure', 'venus', 'mars', 'jupiter', 'saturne'):
        r = np.unwrap(np.radians([x[key] for x in real]))
        v = np.gradient(r)
        idx = [i for i in range(1, len(v)) if v[i - 1] > 0 >= v[i]]
        stations[key] = [format_jd(float(jds[i]), with_time=False) for i in idx]
    return {'periode': [date_from, date_to], 'pas_jours': step_days, 'ecarts': stats,
            'debuts_de_retrogradation_reels': stations,
            'reference': 'Soleil Meeus ch. 25 ; Lune 6 termes de Meeus ch. 47 ; planètes JPL approx_pos table 1 '
                         '(https://ssd.jpl.nasa.gov/planets/approx_pos.html) + précession ; précision ~0.01° / 0.3° / 0.1°'}


# ============================================================================= la machine
class Machine:
    """Angles de tous les corps exactement comme les drivers Blender (build/am/expr.py), éventuellement
    décalés par des PHASES constantes (calage sur le ciel réel ; phases nulles = am.blend tel quel)."""

    def __init__(self, spec_path=SPEC_PATH, phases=None, calibration=None):
        self.spec_path = Path(spec_path)
        raw = self.spec_path.read_bytes()
        self.spec_sha256 = hashlib.sha256(raw).hexdigest()
        S = self.S = json.loads(raw)
        self.bodies = {b['id']: b for b in S['bodies']}
        self.gears = {g['id']: g for g in S['gears']}
        self.rel = {k: Fraction(b['rate_rel_parent_mean']) for k, b in self.bodies.items()
                    if b['rate_rel_parent_mean'] is not None}
        self.rate_abs = {k: Fraction(b['rate_abs_mean']) for k, b in self.bodies.items()
                         if b['rate_abs_mean'] is not None}
        self.revolute = [k for k, b in self.bodies.items() if b['kind'] == 'revolute']
        self.crank_rate = Fraction(self.gears['b1']['teeth'], self.gears['a1']['teeth'])   # 223/48
        body_of = lambda g: self.gears[g]['body']
        self.pin_slots = {}      # corps à rainure -> paramètres
        for p in S['pin_slots']:
            self.pin_slots[body_of(p['slot_gear'])] = {
                'id': p['id'], 'pin': body_of(p['pin_gear']), 'e': p['offset'], 'r': p['pin_radius'],
                'beta': math.radians(p['offset_dir_local_deg']), 'carrier': p['carrier']}
        self.out_of_slot = {}    # sortie planétaire -> corps à rainure (engrenages égaux sur b)
        for m in S['meshes']:
            if m['type'] == 'external' and m['carrier'] == 'b' and body_of(m['driver']) in self.pin_slots:
                self.out_of_slot[body_of(m['driven'])] = body_of(m['driver'])
        self.followers = {}
        for f in S['followers']:
            x, y = f['epicycle_axis_xy_in_b']
            self.followers[f['body']] = {'id': f['id'], 'epi': f['epicycle_body'], 'i': f['i'], 'd': f['pin_d'],
                                         'g0': math.atan2(y, x), 'ph': math.radians(f['pin_phase_deg'])}
        self.marker = {r['body']: math.radians(r['marker_local_deg']) for r in S['dials']['front']['cosmos_rings']}
        fr, bk = S['dials']['front'], S['dials']['back']
        self.zodiac = fr['zodiac_ring']['labels']
        self.cal_ring = fr['calendar_ring']
        self.spirals = {}
        for which in ('metonic', 'saros'):
            d = bk[which]
            body = d['pointer_body']
            q = -self.rel[body] / d['turns']          # tours de spirale complète par an
            n = int(d['turns'] * 2 * 250)             # table psi -> rho du driver (clé tous les π/250)
            psi = np.linspace(0.0, d['turns'] * TAU, n + 1)
            self.spirals[which] = {'body': body, 'turns': d['turns'], 'cells': d['cells'],
                                   'r_start': d['r_start'], 'pitch': d['pitch'], 'q': q,
                                   'table_psi': psi, 'table_rho': self.rho_exact(psi, d['r_start'], d['pitch'])}
        self.subsidiary = {s['id']: s for s in bk['subsidiary']}
        self.phases = dict(phases or {})
        self.calibration = calibration
        self._engraved = None

    # ------------------------------------------------------------------ lois élémentaires
    def lin(self, body, t):
        """Angle local linéaire, exactement l'expression du driver : ∓2π·fmod(c·n/d, 1), + phase."""
        r = self.rel[body]
        ph = self.phases.get(body, 0.0)
        t = np.asarray(t, float)
        if r == 0:
            return np.zeros_like(t) + ph
        n, d = abs(r.numerator), r.denominator
        x = np.fmod(t * n / d, 1.0)
        return (-TAU if r > 0 else TAU) * x + ph

    @staticmethod
    def pin_slot(th, e, r, beta):
        return th + np.arctan2(e * np.sin(th - beta), r - e * np.cos(th - beta))

    @staticmethod
    def rho_exact(psi, r_start, pitch):
        """Spirale à deux centres (Anastasiou et al. 2014), rayon du curseur (mm)."""
        psi = np.asarray(psi, float)
        k = np.floor(psi / TAU); phi = psi - TAU * k
        Rk = r_start + k * pitch; dl = pitch / 2
        second = dl * np.cos(phi) + np.sqrt((Rk + dl) ** 2 - dl * dl * np.sin(phi) ** 2)
        return np.where(phi < math.pi, Rk, second)

    def psi_spiral(self, which, t):
        """Position de l'aiguille sur la spirale (0 .. tours·2π), comme le driver du curseur :
        turns·2π·fmod(fmod(c·q, 1) + 1, 1) (+ phase psi0 de calage, stockée sous la clé du corps)."""
        sp = self.spirals[which]
        q = sp['q']; t = np.asarray(t, float)
        n, d = q.numerator, q.denominator
        u = np.fmod(np.fmod(t * n / d, 1.0) + 1.0, 1.0)
        psi0 = self.phases.get(sp['body'], 0.0)
        if psi0:
            u = np.mod(u + psi0 / (sp['turns'] * TAU), 1.0)
        return sp['turns'] * TAU * u

    # ------------------------------------------------------------------ état complet
    def local(self, t):
        """Angles locaux (rad) de TOUS les corps, relatifs à leur parent Blender ('a' autour de +x,
        'q' autour de l'axe radial de la Lune, les autres autour de +z) — mêmes formules que les drivers."""
        t = np.asarray(t, float)
        A = {'frame': np.zeros_like(t)}
        for b in self.revolute:
            A[b] = self.lin(b, t)
        r = self.crank_rate
        A['a'] = -TAU * np.fmod(t * r.numerator / r.denominator, 1.0) + self.phases.get('a', 0.0)
        for s, p in self.pin_slots.items():
            A[s] = self.pin_slot(A[p['pin']], p['e'], p['r'], p['beta'])
        A['e_inner'] = A['e_table'] - A['kp']          # k2~e6 (50:50) sur e_table
        A['moon'] = -A['e_inner']                       # e1~b3 (32:32) sur le bâti
        for out, slot in self.out_of_slot.items():
            A[out] = A['b'] - A[slot]
        for fb, f in self.followers.items():
            lam = A[f['epi']] + f['ph'] - f['g0']
            A[fb] = A['b'] + f['g0'] + np.arctan2(f['d'] * np.sin(lam), f['i'] + f['d'] * np.cos(lam))
        A['q'] = A['b'] - A['moon']                     # couronne b0~q1 : phase = θ_b − θ_Lune
        return A

    def world(self, t, A=None):
        """Angles monde (autour de +z) des corps d'axe z : enfants de b / e_table incluent le porteur."""
        A = self.local(t) if A is None else A
        W = {}
        for k, b in self.bodies.items():
            if k in ('a', 'q'):
                continue
            p = b['parent']
            W[k] = A[k] + (A[p] if p not in (None, 'frame') else 0.0)
        return W

    def state(self, t):
        """Tout ce que montre la machine au temps t (années de manivelle) : angles locaux et monde,
        positions des aiguilles arrière (psi, sens horaire vu de l'arrière depuis 12 h) et rayons des curseurs."""
        A = self.local(t); W = self.world(t, A)
        psi = {w: self.psi_spiral(w, t) for w in self.spirals}
        rho = {w: np.interp(psi[w], self.spirals[w]['table_psi'], self.spirals[w]['table_rho']) for w in self.spirals}
        rho_exact = {w: self.rho_exact(psi[w], self.spirals[w]['r_start'], self.spirals[w]['pitch']) for w in self.spirals}
        for s in self.subsidiary.values():
            psi[s['id']] = wrap2pi(W[s['pointer_body']])
        return {'t': t, 'local': A, 'world': W, 'psi': psi, 'rho': rho, 'rho_exact': rho_exact,
                'lon': self.longitudes(t, A, W)}

    def longitudes(self, t, A=None, W=None):
        """Longitudes écliptiques affichées (rad, [0, 2π)) ; la longitude croît dans le sens horaire vu de face."""
        A = self.local(t) if A is None else A
        W = self.world(t, A) if W is None else W
        L = {'soleil_moyen': wrap2pi(-W['b']),                            # aiguille de date (b, +x local)
             'soleil_vrai': wrap2pi(-(W['t_trueSun'] + self.marker['t_trueSun'])),
             'lune': wrap2pi(-W['moon']),                                  # aiguille de la Lune
             'noeud_ascendant': wrap2pi(-W['t_nodes']),                    # tête (+x) de l'aiguille du Dragon
             'phase': wrap2pi(A['q'])}                                     # élongation / Soleil moyen
        for body, key, _ in PLANETS:
            L[key] = wrap2pi(-(W[body] + self.marker[body]))
        return L

    # ------------------------------------------------------------------ fonctions légères (Soleil/Lune/nœud)
    def sun_moon_node(self, t):
        t = np.asarray(t, float)
        b = self.lin('b', t); et = self.lin('e_table', t); k = self.lin('k', t)
        p = self.pin_slots['kp']
        kp = self.pin_slot(k, p['e'], p['r'], p['beta'])
        moon = -(et - kp)
        return {'sun': wrap2pi(-b), 'moon': wrap2pi(-moon), 'node': wrap2pi(-self.lin('t_nodes', t)),
                'q': wrap2pi(b - moon), 'moon_mean': wrap2pi(et - k)}

    def rate(self, key, t, h=1e-5):
        """Vitesse de la longitude affichée (rad/an) par différence centrée."""
        a = self.longitudes(np.asarray(t, float) + h)[key]; b = self.longitudes(np.asarray(t, float) - h)[key]
        return wrappi(a - b) / (2 * h)

    # ------------------------------------------------------------------ syzygies
    def syzygy(self, t_guess, target):
        """Instant où l'élongation Lune − Soleil moyen affichée (angle de la boule de phase q) vaut target
        (0 = nouvelle lune, π = pleine lune), le plus proche de t_guess (Newton)."""
        t = np.array(t_guess, float, copy=True)
        h = 1e-6
        for _ in range(10):
            g = wrappi(self.sun_moon_node(t)['q'] - target)
            r = wrappi(self.sun_moon_node(t + h)['q'] - self.sun_moon_node(t - h)['q']) / (2 * h)
            t = t - g / r
        return t

    @property
    def month(self):
        """Mois synodique moyen du modèle (années) : 19/235."""
        return 1.0 / float(self.rate_abs['moon'] - self.rate_abs['b'])

    def mean_conjunction_near(self, t):
        e = self.sun_moon_node(t)
        el = wrappi(e['moon_mean'] - e['sun'])
        return np.asarray(t, float) - el / TAU * self.month

    def syzygies(self, t0, t1):
        """Toutes les nouvelles (0) et pleines (π) lunes de la machine dans [t0, t1] -> liste triée."""
        T = self.month
        m0 = float(self.mean_conjunction_near(t0)) - T
        k = np.arange(0, int((t1 - m0) / T) + 3)
        m = m0 + k * T
        nm = self.syzygy(m, 0.0); fm = self.syzygy(m + T / 2, math.pi)
        ev = [(float(x), 'NM') for x in nm] + [(float(x), 'FM') for x in fm]
        return sorted(e for e in ev if t0 <= e[0] <= t1)

    def node_distance(self, t, kind):
        """Distance (degrés) de l'aiguille de la Lune au nœud le plus proche, et latitude N/S (Lune au nord
        si 0 < λ_Lune − Ω_asc < 180°)."""
        e = self.sun_moon_node(t)
        F = wrap2pi(e['moon'] - e['node'])
        dist = np.degrees(np.minimum(np.abs(wrappi(F)), np.abs(wrappi(F - math.pi))))
        return dist, np.sin(F) > 0

    # ------------------------------------------------------------------ cadrans
    def saros_cell(self, t):
        psi = self.psi_spiral('saros', t)
        return np.minimum((psi / (8 * math.pi) * 223).astype(int), 222) + 1

    def saros_convention(self):
        return 'freeth2014' if self.calibration else 'model'

    def saros_cycle_start_before(self, t):
        psi = float(self.psi_spiral('saros', t))
        return float(t) - psi / (8 * math.pi) * float(1 / self.spirals['saros']['q'])

    def engraved_table(self):
        """Table de glyphes « gravée » sur le cadran de Saros de CETTE machine : calculée par le modèle pour le
        cycle de Saros qui contient l'époque (t = 0 non calé ; époque de calage sinon), règle LIMITS."""
        if self._engraved is None:
            t0 = self.calibration['t_epoch'] if self.calibration else 0.0
            self._engraved = glyph_table(self, self.saros_cycle_start_before(t0 + 1e-9), rule='limits')
        return self._engraved

    # ------------------------------------------------------------------ lectures humaines
    def read(self, t, ring_offset_days=None):
        """Lecture complète en français au temps t (scalaire)."""
        t = float(t)
        st = self.state(t); L = {k: float(v) for k, v in st['lon'].items()}
        out = {'t_manivelle_ans': t, 'mode': 'calé sur le ciel réel' if self.calibration else
               'modèle (époque non calée, manivelle 0 = tout à zéro)'}
        if self.calibration:
            jd = float(jd_from_t(t))
            out['jd_tt'] = jd; out['date'] = format_jd(jd)
        # Soleil
        out['soleil'] = {'moyen (aiguille de date)': zodiac_read(self.zodiac, deg(L['soleil_moyen'])),
                         'vrai (sphère dorée)': dict(zodiac_read(self.zodiac, deg(L['soleil_vrai'])), statut=HYPO)}
        # Calendrier égyptien sous l'aiguille de date
        ndays = self.cal_ring['day_divisions']
        pos = deg(L['soleil_moyen']) / 360.0 * ndays
        cal = {'anneau_fixe': egypt_ring_read(pos)}
        if self.calibration:
            eg = egyptian_date(out['jd_tt'])
            off = (eg['jour_de_l_annee'] - 0.5 - pos) % 365
            cal['anneau_regle'] = dict(egypt_ring_read((pos + off) % 365), decalage_anneau_jours=round(off, 2),
                                       note="anneau tourné à la main pour suivre l'année vague égyptienne "
                                            "(1 jour tous les 4 ans environ)")
        elif ring_offset_days is not None:
            cal['anneau_regle'] = egypt_ring_read((pos + ring_offset_days) % 365)
        out['calendrier_egyptien'] = cal
        # Lune
        D = deg(L['phase']); month_days = self.month * YEAR_DAYS
        out['lune'] = dict(zodiac_read(self.zodiac, deg(L['lune'])), elongation_deg=round(D, 3),
                           phase=phase_name(D), fraction_eclairee=round((1 - math.cos(math.radians(D))) / 2, 4),
                           age_jours=round(D / 360 * month_days, 2), croissante=D < 180)
        # Planètes
        pl = {}
        for body, key, name in PLANETS:
            v = float(self.rate(key, t)) / TAU * 360 / YEAR_DAYS
            pl[name] = dict(zodiac_read(self.zodiac, deg(L[key])), vitesse_deg_par_jour=round(v, 4),
                            retrograde=v < 0, statut=HYPO)
        out['planetes'] = pl
        # Dragon
        dist, north = self.node_distance(t, 'NM')
        out['aiguille_du_dragon'] = {'noeud_ascendant': zodiac_read(self.zodiac, deg(L['noeud_ascendant'])),
                                     'noeud_descendant': zodiac_read(self.zodiac, deg(L['noeud_ascendant']) + 180),
                                     'lune_distance_au_noeud_deg': round(float(dist), 3),
                                     'lune_au_nord_de_l_ecliptique': bool(north), 'statut': HYPO}
        # Cadrans arrière
        out.update(self.read_back(t, st))
        return out

    def read_back(self, t, st=None):
        st = self.state(t) if st is None else st
        o = {}
        psi = float(st['psi']['metonic'])
        cell = min(int(psi / (10 * math.pi) * 235), 234)
        year = (19 * cell) // 235
        first = -(-235 * year // 19)
        o['metonique'] = {'case': cell + 1, 'spire': int(psi // TAU) + 1, 'annee_du_cycle': year + 1,
                          'mois_dans_l_annee': cell - first + 1, 'rayon_curseur_mm': round(float(st['rho']['metonic']), 4),
                          'note': "année = année solaire du modèle où le mois commence (convention moyenne, pas le "
                                  "schéma d'intercalation historique)"}
        if self.calibration:
            o['metonique']['cycle_numero'] = self._cycle_number('metonic', t)
        pc = float(st['psi']['callippic'])
        o['callippique'] = {'secteur': int(pc // (math.pi / 2)) + 1,
                            'note': 'chaque secteur = un cycle de Méton de 19 ans (76 ans en tout)'}
        og = self.subsidiary['olympiad']
        k = self.olympiad_sector(t)
        name = og['labels'][k]
        o['jeux'] = {'secteur': k + 1, 'inscription': name, 'nom_fr': games_fr(name),
                     'annee_de_l_olympiade': self.olympiad_year_index(k)}
        if self.calibration:
            o['jeux']['olympiade_numero'] = self.olympiad_number(t)
        ps = float(st['psi']['saros'])
        cell = min(int(ps / (8 * math.pi) * 223), 222) + 1
        tab = self.engraved_table()
        g = tab['cells'][cell - 1]
        o['saros'] = {'case': cell, 'spire': int(ps // TAU) + 1, 'glyphe': g['glyph'] or None,
                      'rayon_curseur_mm': round(float(st['rho']['saros']), 4),
                      'glyphe_note': ('Σ = éclipse de Lune possible à la pleine lune de ce mois, Η = éclipse de '
                                      'Soleil possible à la nouvelle lune ' +
                                      ('qui termine ce mois (mois commençant au 1er croissant, Freeth 2014)'
                                       if self.saros_convention() == 'freeth2014' else 'qui ouvre ce mois') +
                                      ' ; glyphes CALCULÉS PAR NOTRE MODÈLE (règle des limites écliptiques)')}
        if self.calibration:
            o['saros']['cycle_numero'] = self._cycle_number('saros', t)
        ex = self.subsidiary['exeligmos']
        kx = int(float(st['psi']['exeligmos']) // (TAU / 3))
        o['exeligmos'] = {'secteur': kx + 1, 'inscription': ex['labels'][kx], 'heures_a_ajouter': 8 * kx}
        return o

    def olympiad_sector(self, t):
        """Secteur (0..3) du cadran des Jeux sous l'aiguille ; secteur k = [tilt + k·90°, tilt + (k+1)·90°) en psi."""
        og = self.subsidiary['olympiad']
        psi = self.lin(og['pointer_body'], t)                  # corps enfant du bâti : angle monde = angle local
        k = np.mod(psi - math.radians(og.get('sector_tilt_deg', 0.0)), TAU) // (TAU / og['sectors'])
        return k.astype(int) if np.ndim(k) else int(k)

    def olympiad_direction(self):
        """+1 si l'aiguille des Jeux va dans le sens des secteurs croissants (psi croissant), −1 sinon."""
        return 1 if self.rel[self.subsidiary['olympiad']['pointer_body']] < 0 else -1

    def olympiad_year_index(self, k):
        og = self.subsidiary['olympiad']
        kO = olympia_index(og['labels'])
        return ((k - kO) * self.olympiad_direction()) % og['sectors'] + 1

    def olympiad_number(self, t):
        c = self.calibration
        return int(math.floor((float(t) - c['olympiad']['t_start']) / 4.0)) + c['olympiad']['number_at_start']

    def _cycle_number(self, which, t):
        c = self.calibration['cycles'][which]
        sp = self.spirals[which]
        u = float(t) * float(sp['q']) + self.phases[sp['body']] / (sp['turns'] * TAU)
        return int(math.floor(u)) + c['offset']


# ============================================================================= lectures (aides)
def zodiac_read(labels, lon_deg):
    lon = lon_deg % 360.0
    k = int(lon // 30) % 12
    return {'longitude_deg': round(lon, 4), 'signe_grec': labels[k], 'signe_fr': ZODIAC_FR[k],
            'degre_dans_le_signe': round(lon - 30 * k, 3),
            'texte': '%s dans %s (%s)' % (fmt_angle(lon - 30 * k), labels[k], ZODIAC_FR[k])}


def egypt_ring_read(pos_days):
    doy = int(math.floor(pos_days)) % 365
    mi = min(doy // 30, 12)
    greek = ['ΘΩΥΘ', 'ΦΑΩΦΙ', 'ΑΘΥΡ', 'ΧΟΙΑΚ', 'ΤΥΒΙ', 'ΜΕΧΙΡ', 'ΦΑΜΕΝΩΘ', 'ΦΑΡΜΟΥΘΙ', 'ΠΑΧΩΝ', 'ΠΑΥΝΙ',
             'ΕΠΙΦΙ', 'ΜΕΣΟΡΗ', 'ΕΠΑΓΟΜΕΝΑΙ']
    day = doy - 30 * mi + 1
    return {'jour_de_l_annee': doy + 1, 'mois_grec': greek[mi], 'mois_fr': EGYPT_MONTHS_FR[mi], 'jour': day,
            'texte': ('%d %s (%s)' % (day, EGYPT_MONTHS_FR[mi], greek[mi])) if mi < 12 else
                     ('%de jour épagomène (%s)' % (day, greek[mi]))}


def phase_name(D):
    """Nom de la phase d'après l'élongation D (degrés) : phases principales à ±7.5° (≈ ±0.6 jour)."""
    D %= 360.0
    for c, n in ((0, 'nouvelle lune'), (90, 'premier quartier'), (180, 'pleine lune'), (270, 'dernier quartier'),
                 (360, 'nouvelle lune')):
        if abs(D - c) <= 7.5:
            return n
    if D < 90:
        return 'premier croissant'
    if D < 180:
        return 'gibbeuse croissante'
    if D < 270:
        return 'gibbeuse décroissante'
    return 'dernier croissant'


# ============================================================================= glyphes d'éclipse
def glyph_table(machine: Machine, t_cycle_start, rule='limits', convention=None, limits=None):
    """Glyphes des 223 cases d'un cycle de Saros qui commence à t_cycle_start (aiguille en début de case 1).

    convention 'model'      : cases bornées par les conjonctions moyennes (machine non calée) ; Η = nouvelle
                              lune qui OUVRE la case, Σ = pleine lune du milieu.
    convention 'freeth2014' : cases commençant au 1er croissant (NM moyenne + 2/38 mois, Freeth 2014) ; Σ = pleine
                              lune du milieu, Η = nouvelle lune qui TERMINE la case.
    rule 'limits'     : limites écliptiques LIMITS ; rule 'freeth2014' : seuils EYM transposés en degrés."""
    convention = convention or machine.saros_convention()
    lim = dict(LIMITS if limits is None else limits)
    T = machine.month
    n = np.arange(-1, 223)
    start = t_cycle_start + n * T
    if convention == 'model':
        m = start; nm_t = m
    else:
        m = start - 2.0 / 38.0 * T; nm_t = m + T
    t_nm = machine.syzygy(nm_t, 0.0); t_fm = machine.syzygy(m + T / 2, math.pi)
    dn, north = machine.node_distance(t_nm, 'NM'); df, _ = machine.node_distance(t_fm, 'FM')
    if rule == 'limits':
        lunar = df <= lim['lunar_deg']; solar = dn <= lim['solar_deg']
    elif rule == 'freeth2014':
        e = EYU_DEG
        lunar_raw = df <= FREETH_RULE['lunar_eyu'] * e
        lunar = lunar_raw.copy()
        for i in range(1, len(lunar)):            # règle des mois consécutifs
            if lunar[i] and lunar[i - 1]:
                lunar[i] = False
        solar = np.where(north, dn <= FREETH_RULE['solar_north_eyu'] * e, dn <= FREETH_RULE['solar_south_eyu'] * e)
    else:
        raise ValueError(rule)
    cells = []
    for i in range(1, 224):
        g = (GLYPH_LUNAR if lunar[i] else '') + (' ' if lunar[i] and solar[i] else '') + (GLYPH_SOLAR if solar[i] else '')
        cells.append({'case': i, 'glyph': g, 'lunaire': bool(lunar[i]), 'solaire': bool(solar[i]),
                      't_pleine_lune': round(float(t_fm[i]), 8), 't_nouvelle_lune': round(float(t_nm[i]), 8),
                      'dist_noeud_pleine_lune_deg': round(float(df[i]), 3),
                      'dist_noeud_nouvelle_lune_deg': round(float(dn[i]), 3),
                      'lune_au_nord_a_la_nouvelle_lune': bool(north[i])})
    return {'t_debut_cycle': float(t_cycle_start), 'convention': convention, 'regle': rule,
            'limites_deg': {'solaire': lim['solar_deg'], 'lunaire': lim['lunar_deg']} if rule == 'limits' else
            {'lunaire': 20 * EYU_DEG, 'solaire_nord': 20 * EYU_DEG, 'solaire_sud': 7 * EYU_DEG},
            'cells': cells, 'stats': glyph_stats(cells, convention)}


def freeth2014_eym():
    """Modèle « Eclipse Year Model » de Freeth 2014 (reconstruction du cadran historique) : mois de 38 EYu,
    année des éclipses de 446 EYu, pleine lune n à 38(n−1)+17, nouvelle lune n à 38(n−1)+36 (mod 446),
    points nodaux à 66 (descendant) et 289 (ascendant) EYu ; limites 20 / 20 (nord) / 7 (sud) EYu ;
    pas de 2e glyphe lunaire le mois suivant."""
    NP = ((66, 'D'), (289, 'A'))

    def nearest(p):
        best = None
        for c, kind in NP:
            d = ((p - c + 223) % 446) - 223
            if best is None or abs(d) < abs(best[0]):
                best = (d, kind)
        return best
    cells = []; prev = False
    for n in range(1, 224):
        fm = (38 * (n - 1) + 17) % 446; nm = (38 * (n - 1) + 36) % 446
        dF, _ = nearest(fm); dN, kind = nearest(nm)
        lunar = abs(dF) <= 20 and not prev
        prev = lunar
        north = dN < 0 if kind == 'D' else dN > 0
        solar = abs(dN) <= (20 if north else 7)
        g = (GLYPH_LUNAR if lunar else '') + (' ' if lunar and solar else '') + (GLYPH_SOLAR if solar else '')
        cells.append({'case': n, 'glyph': g, 'lunaire': lunar, 'solaire': solar,
                      'pleine_lune_eyu_du_point_nodal': dF, 'nouvelle_lune_eyu_du_point_nodal': dN})
    return {'source': 'Freeth 2014, PLoS ONE 9(7):e103275, « Eclipse Year Model »', 'convention': 'freeth2014',
            'cells': cells, 'stats': glyph_stats(cells, 'freeth2014')}


def glyph_stats(cells, convention):
    lunar = [c['case'] for c in cells if c['lunaire']]
    solar = [c['case'] for c in cells if c['solaire']]
    both = [c['case'] for c in cells if c['lunaire'] and c['solaire']]

    def gaps(v):
        return [(b - a) % 223 or 223 for a, b in zip(v, v[1:] + v[:1])] if v else []

    def groups(g):
        """Tailles des groupes séparés par des intervalles de 5 mois (motif babylonien 8-7-8-7-8)."""
        if not g or 5 not in g:
            return []
        i0 = g.index(5); rot = g[i0 + 1:] + g[:i0 + 1]
        out, run = [], 1
        for x in rot:
            if x == 5:
                out.append(run); run = 1
            else:
                run += 1 if x == 6 else 0
        return out
    gl, gs = gaps(lunar), gaps(solar)
    hist = lambda g: {str(k): g.count(k) for k in sorted(set(g))}
    return {'cases_avec_glyphe': len(set(lunar) | set(solar)), 'lunaires': len(lunar), 'solaires': len(solar),
            'cases_avec_les_deux': len(both), 'ecarts_lunaires_mois': hist(gl), 'ecarts_solaires_mois': hist(gs),
            'groupes_lunaires': groups(gl), 'groupes_solaires': groups(gs)}


def cyclic_equal(a, b):
    a, b = list(a), list(b)
    return len(a) == len(b) and any(a == b[i:] + b[:i] for i in range(len(b)))


def compare_tables(a, b):
    """Compare deux tables sur l'axe des lunaisons (Σ à la pleine lune k, Η à la nouvelle lune qui ouvre la
    lunaison k) ; renvoie le meilleur décalage cyclique et les accords."""
    def events(tab):
        L = np.zeros(223, bool); S = np.zeros(223, bool)
        for c in tab['cells']:
            k = c['case'] - 1
            L[k] = c['lunaire']
            if c['solaire']:
                S[(k + 1) % 223 if tab['convention'] == 'freeth2014' else k] = True
        return L, S
    La, Sa = events(a); Lb, Sb = events(b)
    best = None
    for s in range(223):
        Lr, Sr = np.roll(Lb, -s), np.roll(Sb, -s)
        agree = int(np.sum(La == Lr) + np.sum(Sa == Sr))
        common = int(np.sum(La & Lr) + np.sum(Sa & Sr))
        if best is None or (agree, common) > (best['accords_sur_446'], best['glyphes_communs']):
            best = {'decalage_lunaisons': s, 'accords_sur_446': agree, 'glyphes_communs': common,
                    'lunaires_communs': int(np.sum(La & Lr)), 'solaires_communs': int(np.sum(Sa & Sr))}
    s = best['decalage_lunaisons']
    best['sans_decalage'] = {'accords_sur_446': int(np.sum(La == Lb) + np.sum(Sa == Sb)),
                             'glyphes_communs': int(np.sum(La & Lb) + np.sum(Sa & Sb))}
    best['total_a'] = int(La.sum() + Sa.sum()); best['total_b'] = int(Lb.sum() + Sb.sum())
    return best


# ============================================================================= calage sur le ciel réel
def calibrate(epoch_jd=JD_J2000, spec_path=SPEC_PATH):
    """Machine dont les PHASES (angles à t = 0) sont choisies pour qu'à l'époque epoch_jd ses mouvements
    moyens coïncident avec les éléments moyens réels (Meeus). Les RAPPORTS d'engrenages ne changent pas :
    la machine dérive ensuite lentement (voir drift_report). Cadrans arrière calés sur des repères historiques
    (ANCHORS) en comptant les lunaisons réelles."""
    base = Machine(spec_path)
    tE = float(t_from_jd(epoch_jd))
    el = mean_elements(epoch_jd)
    r = math.radians
    lin0 = lambda body, t=tE: float(base.lin(body, t))
    wrap = lambda x: float(x % TAU)
    ph = {}
    L0 = r(el['sun_L0'])
    ph['b'] = wrap(-L0 - lin0('b'))                                      # Soleil moyen (b, aiguille de date)
    ts = base.followers['t_trueSun']
    ph['x_su56'] = wrap(ts['g0'] - ts['ph'] - ph['b'] - r(el['sun_apogee']) - lin0('x_su56'))   # apogée solaire
    beta = base.pin_slots['kp']['beta']
    xE = beta - r(el['moon_M'])                                          # anomalie lunaire (k, local)
    ph['k'] = wrap(xE - lin0('k'))
    ph['e_table'] = wrap(r(el['moon_L']) + xE - lin0('e_table'))         # longitude moyenne de la Lune
    ph['t_nodes'] = wrap(-r(el['moon_Omega']) - lin0('t_nodes'))         # nœud ascendant
    for body, key in (('t_mars', 'mars'), ('t_jupiter', 'jupiter'), ('t_saturn', 'saturn')):
        pin = base.pin_slots[base.out_of_slot[body]]['pin']
        ph[pin] = wrap(r(el[key]) - L0 + base.marker[body] - lin0(pin))
    for body, key in (('t_mercury', 'mercury'), ('t_venus', 'venus')):
        f = base.followers[body]
        ph[f['epi']] = wrap(L0 - r(el[key]) - f['ph'] + f['g0'] - lin0(f['epi']))
    # --- cadrans arrière : comptage des lunaisons réelles depuis les repères historiques
    fc = 2.0 / 38.0                                   # cases commençant au 1er croissant (Freeth 2014)
    a = ANCHORS['saros_FM1']['date']
    nm_saros = mean_new_moon_near(jd_from_date(*a[:3], a[3], 'julian') - SYNODIC_REAL / 2)
    a = ANCHORS['callippic']['date']
    nm_meton = mean_new_moon_near(jd_from_date(*a[:3], a[3], 'julian'))
    Ns = lunations_real(epoch_jd) - lunations_real(nm_saros) - fc
    Nm = lunations_real(epoch_jd) - lunations_real(nm_meton) - fc
    cycles = {}
    for which, N, cells in (('saros', Ns, 223), ('metonic', Nm, 235)):
        sp = base.spirals[which]; q = float(sp['q'])
        u = N / cells
        u0 = (u - tE * q) % 1.0
        ph[sp['body']] = u0 * sp['turns'] * TAU
        cycles[which] = {'offset': int(math.floor(u)) - int(math.floor(tE * q + u0)) + 1,   # 1 = premier cycle
                         'lunaisons_depuis_repere': N + fc}
    ph['i'] = wrap(TAU * ((Ns / 669.0) % 1.0) - lin0('i'))                 # Exeligmos : 3 Saros
    ph['cal'] = wrap(TAU * ((Nm / 940.0) % 1.0) - lin0('cal'))             # Callippe : 4 × 235 mois
    # --- Jeux : entrée dans ΟΛΥΜΠΙΑ au solstice d'été moyen des années ≡ 1 (mod 4) (776 av. J.-C. = −775)
    og = base.subsidiary['olympiad']
    y = date_from_jd(epoch_jd)[0]
    y_star = y - ((y - ANCHORS['olympiad']['first_year']) % 4)
    t_sol = float(t_from_jd(jd_from_date(y_star, 6, 21, 12.0)))
    lam_b = lambda t: -(lin0('b', t) + ph['b'])
    for _ in range(3):
        t_sol -= float(wrappi(lam_b(t_sol) - math.pi / 2)) / TAU
    kO = olympia_index(og['labels'])
    step = TAU / og['sectors']; tilt = r(og.get('sector_tilt_deg', 0.0))
    direction = base.olympiad_direction()
    boundary = tilt + step * (kO if direction > 0 else kO + 1) + (1e-9 if direction > 0 else -1e-9)
    ph['o'] = wrap(boundary - lin0('o', t_sol))
    cal = {'epoch_jd': epoch_jd, 'epoch': format_jd(epoch_jd), 't_epoch': tE,
           'mean_elements_deg': {k: v % 360.0 for k, v in el.items()},
           'anchors': {'saros_nouvelle_lune_moyenne': format_jd(nm_saros), 'saros_jd': nm_saros,
                       'metonique_nouvelle_lune_moyenne': format_jd(nm_meton), 'metonique_jd': nm_meton,
                       'debut_des_cases': 'nouvelle lune moyenne + 2/38 de mois (1er croissant, Freeth 2014)',
                       'sources': {k: v['source'] for k, v in ANCHORS.items()}},
           'cycles': cycles,
           'olympiad': {'t_start': t_sol, 'year_start': y_star, 'number_at_start': (y_star - ANCHORS['olympiad']['first_year']) // 4 + 1,
                        'convention': "l'aiguille entre dans ΟΛΥΜΠΙΑ au solstice d'été moyen (Soleil moyen à 90°) "
                                      "des années olympiques antiques (≡ 776 av. J.-C. mod 4)"}}
    return Machine(spec_path, phases=ph, calibration=cal)


def blender_offsets(m: Machine, t_ref=0.0):
    """Constantes à ajouter aux drivers de am.blend pour qu'une manivelle LOCALE c' = t − t_ref (petite, donc précise
    en float32) montre la machine m au temps t : décalage temporel exact de TOUS les corps linéaires (les engrenages
    restent en prise) + phases de calage des sorties. Renvoie {'corps': {id: rad}, 'curseurs': {spirale: u0 ∈ [0,1)}}."""
    base = Machine(m.spec_path)
    t_ref = float(t_ref)
    off = {b: float((base.lin(b, t_ref) + m.phases.get(b, 0.0)) % TAU) for b in m.revolute}
    r = m.crank_rate
    off['a'] = float((-TAU * math.fmod(t_ref * r.numerator / r.denominator, 1.0)) % TAU)
    cur = {}
    for which, sp in m.spirals.items():
        q = sp['q']
        u = math.fmod(math.fmod(t_ref * q.numerator / q.denominator, 1.0) + 1.0, 1.0)
        cur[which] = float((u + m.phases.get(sp['body'], 0.0) / (sp['turns'] * TAU)) % 1.0)
    return {'t_ref': t_ref, 'jd_ref': float(jd_from_t(t_ref)), 'date_ref': format_jd(float(jd_from_t(t_ref))),
            'corps': off, 'curseurs': cur}


_MACHINES = {}


def get_machine(calibrated=False):
    """Machine partagée : non calée (= am.blend) ou calée sur J2000.0."""
    if calibrated not in _MACHINES:
        _MACHINES[calibrated] = calibrate() if calibrated else Machine()
    return _MACHINES[calibrated]


def state(t, calibrated=False):
    """Angles de tous les corps au temps de manivelle t (non calé = exactement les drivers de am.blend)."""
    return get_machine(calibrated).state(t)


def read(t, calibrated=False):
    """Lecture en français au temps de manivelle t."""
    return get_machine(calibrated).read(t)


def read_date(date):
    """Lecture en français de la machine calée à une date ('2026-08-12T17:47', '-204-05-12', ou JD)."""
    jd = parse_date(date) if isinstance(date, str) else float(date)
    return get_machine(True).read(float(t_from_jd(jd)))


def drift_report(m: Machine):
    """Écart (°/siècle julien) entre les mouvements moyens des rapports anciens et les valeurs modernes (Meeus)."""
    k = 360.0 * DAYS_PER_CENTURY / YEAR_DAYS          # (tours/an du modèle) -> °/siècle julien
    R = mean_rates_deg_per_century()
    ra = {b: float(v) for b, v in m.rate_abs.items()}
    moon = ra['moon'] * k; node = ra['t_nodes'] * k; sun = ra['b'] * k     # λ croît avec le taux (horaire vu de face)
    apse = -ra['e_table'] * k                          # e_table tourne en sens direct : longitude du périgée
    rows = {
        'soleil_moyen': (sun, R['sun_L0'], 'b = 1 tour/an'),
        'apogee_solaire': (0.0, R['sun_L0'] - R['sun_M'], 'su56 fixe (apogée fixe)'),
        'lune_longitude_moyenne': (moon, R['moon_L'], 'moon = 254/19 tour/an'),
        'lune_elongation_D': (moon - sun, R['moon_D'], '235/19 lunaisons/an (Méton)'),
        'lune_anomalie_moyenne': (moon - apse, R['moon_M'], 'k/e_table = 56165/4237'),
        'perigee_lunaire': (apse, R['moon_L'] - R['moon_M'], 'e_table = 477/4237 tour/an'),
        'noeud_lunaire': (node, R['moon_Omega'], 't_nodes = −5/93 tour/an'),
        'argument_de_latitude_F': (moon - node, R['moon_F'], 'Lune − nœud'),
    }
    for body, key, epi in (('t_mercury', 'mercury', 'x_me20'), ('t_venus', 'venus', 'x_r1')):
        rows[key] = (ra[epi] * k, R[key], 'épicycle %s = %s tour/an (longitude héliocentrique)' % (epi, frac_str(m.rate_abs[epi])))
    for body, key in (('t_mars', 'mars'), ('t_jupiter', 'jupiter'), ('t_saturn', 'saturn')):
        rows[key] = (ra[body] * k, R[key], '%s = %s tour/an' % (body, frac_str(m.rate_abs[body])))
    out = {}
    for name, (mod, real, note) in rows.items():
        d = mod - real
        out[name] = {'modele_deg_par_siecle': round(mod, 6), 'reel_deg_par_siecle': round(real, 6),
                     'derive_deg_par_siecle': round(d, 4), 'rapport': note}
    D = out['lune_elongation_D']['derive_deg_par_siecle']
    out['_resume'] = {
        'mois_synodique_modele_jours': round(m.month * YEAR_DAYS, 6), 'mois_synodique_reel_jours': SYNODIC_REAL,
        'phases_de_la_lune_avance_jours_par_siecle': round(D / (MEEUS['moon_D'][1] / DAYS_PER_CENTURY), 3),
        'eclipses_F_derive_deg_par_siecle': out['argument_de_latitude_F']['derive_deg_par_siecle'],
    }
    return out


# ============================================================================= événements
def machine_events(date_from, date_to, rule='limits', machine=None):
    """Événements affichés par la machine calée (J2000 par défaut) entre deux dates (chaînes ISO ou JD) :
    nouvelles/pleines lunes, éclipses prédites (aiguille du Dragon ET glyphe du cadran de Saros),
    changements de secteur des Jeux, débuts (et fins) de rétrogradation."""
    m = machine if machine is not None else get_machine(True)
    jd0 = parse_date(date_from) if isinstance(date_from, str) else float(date_from)
    jd1 = parse_date(date_to) if isinstance(date_to, str) else float(date_to)
    t0, t1 = float(t_from_jd(jd0)), float(t_from_jd(jd1))
    ev = []
    tab = m.engraved_table()
    conv = tab['convention']
    lim = LIMITS
    prev_lunar = False
    for ts, kind in m.syzygies(t0, t1):
        dist, north = m.node_distance(ts, kind)
        dist = float(dist); north = bool(north)
        name = 'nouvelle lune' if kind == 'NM' else 'pleine lune'
        e = {'type': name, 't': ts, 'jd': float(jd_from_t(ts)), 'date': format_jd(float(jd_from_t(ts))),
             'distance_noeud_deg': round(dist, 3)}
        ev.append(e)
        psi = float(m.psi_spiral('saros', ts)) / (8 * math.pi) * 223
        if conv == 'model' and kind == 'NM':
            cell = int(math.floor(psi + 0.5)) % 223 + 1
        else:
            cell = min(int(psi), 222) + 1
        g = tab['cells'][cell - 1]
        if rule == 'limits':
            dragon = dist <= (lim['solar_deg'] if kind == 'NM' else lim['lunar_deg'])
        else:
            if kind == 'NM':
                dragon = dist <= (20 if north else 7) * EYU_DEG
            else:
                dragon = dist <= 20 * EYU_DEG and not prev_lunar
                prev_lunar = dragon
        dial = g['solaire'] if kind == 'NM' else g['lunaire']
        if dragon or dial:
            ev.append({'type': 'éclipse de Soleil' if kind == 'NM' else 'éclipse de Lune', 't': ts,
                       'jd': e['jd'], 'date': e['date'], 'distance_noeud_deg': round(dist, 3),
                       'lune_au_nord': north, 'case_saros': cell, 'glyphe_case': g['glyph'],
                       'predite_par_aiguille_du_dragon': bool(dragon), 'predite_par_cadran_saros': bool(dial)})
    # Jeux : entrées de secteur
    og = m.subsidiary['olympiad']
    grid = np.arange(t0, t1 + 1 / 365, 1 / 365.0)
    sec = m.olympiad_sector(grid)
    for i in np.nonzero(sec[1:] != sec[:-1])[0]:
        a, b = grid[i], grid[i + 1]
        for _ in range(40):
            c = 0.5 * (a + b)
            if m.olympiad_sector(np.array([c]))[0] == sec[i]:
                a = c
            else:
                b = c
        k = int(sec[i + 1]); name = og['labels'][k]
        e = {'type': 'Jeux : nouveau secteur', 't': b, 'jd': float(jd_from_t(b)), 'date': format_jd(float(jd_from_t(b))),
             'inscription': name, 'nom_fr': games_fr(name), 'annee_de_l_olympiade': m.olympiad_year_index(k)}
        if m.calibration:
            e['olympiade_numero'] = m.olympiad_number(b + 1e-6)
        ev.append(e)
    # Rétrogradations
    grid = np.arange(t0 - 2 / 365, t1 + 2 / 365, 1 / 365.0)
    for body, key, name in PLANETS:
        v = m.rate(key, grid)
        for i in np.nonzero(np.sign(v[1:]) != np.sign(v[:-1]))[0]:
            a, b = grid[i], grid[i + 1]
            sa = np.sign(v[i])
            for _ in range(45):
                c = 0.5 * (a + b)
                if np.sign(m.rate(key, np.array([c]))[0]) == sa:
                    a = c
                else:
                    b = c
            if not (t0 <= b <= t1):
                continue
            lon = float(m.longitudes(np.array([b]))[key][0])
            ev.append({'type': 'début de rétrogradation' if sa > 0 else 'fin de rétrogradation', 'planete': name,
                       't': b, 'jd': float(jd_from_t(b)), 'date': format_jd(float(jd_from_t(b))),
                       'position': zodiac_read(m.zodiac, math.degrees(lon))['texte'], 'statut': HYPO})
    ev.sort(key=lambda e: e['t'])
    return ev


def compare_with_nasa(m: Machine, rule='limits'):
    """Éclipses prédites par la machine calée (2026-2028) face aux éclipses réelles de la NASA."""
    ev = [e for e in machine_events('2025-12-01', '2029-01-31', rule=rule, machine=m) if e['type'].startswith('éclipse')]
    rows = []; used = set()
    for kind, iso, typ, saros in NASA_ECLIPSES_2026_2028:
        jd = parse_date(iso)
        want = 'éclipse de Soleil' if kind == 'solaire' else 'éclipse de Lune'
        cands = [(abs(e['jd'] - jd), i, e) for i, e in enumerate(ev) if e['type'] == want]
        best = min(cands, default=None)
        row = {'reelle': '%s %s %s (Saros %d)' % (iso.replace('T', ' '), kind, typ, saros), 'jd_reel': jd}
        if best and best[0] < 5:
            _, i, e = best; used.add(i)
            row.update({'machine': e['date'], 'ecart_heures': round((e['jd'] - jd) * 24, 2),
                        'distance_noeud_machine_deg': e['distance_noeud_deg'],
                        'aiguille_du_dragon': e['predite_par_aiguille_du_dragon'],
                        'cadran_saros': e['predite_par_cadran_saros'], 'case_saros': e['case_saros']})
        else:
            ts = m.syzygies(float(t_from_jd(jd)) - 0.05, float(t_from_jd(jd)) + 0.05)
            ts = [x for x in ts if x[1] == ('NM' if kind == 'solaire' else 'FM')]
            if ts:
                tt = ts[0][0]; dist, _ = m.node_distance(tt, ts[0][1])
                row.update({'machine': 'NON PRÉDITE', 'syzygie_machine': format_jd(float(jd_from_t(tt))),
                            'ecart_heures': round((float(jd_from_t(tt)) - jd) * 24, 2),
                            'distance_noeud_machine_deg': round(float(dist), 3)})
            else:
                row['machine'] = 'NON PRÉDITE'
        rows.append(row)
    false_pos = [{'machine': e['date'], 'type': e['type'], 'distance_noeud_deg': e['distance_noeud_deg'],
                  'aiguille_du_dragon': e['predite_par_aiguille_du_dragon'], 'cadran_saros': e['predite_par_cadran_saros']}
                 for i, e in enumerate(ev) if i not in used and parse_date('2026-01-01') <= e['jd'] < parse_date('2029-01-01')]
    return {'regle': rule, 'eclipses': rows, 'predictions_sans_eclipse_reelle': false_pos, 'sources': NASA_SOURCES}


def olympiad_check(m: Machine):
    out = {}
    for label, iso in (('Jeux de Los Angeles (14-30 juillet 2028)', '2028-07-21'), ('été 2029', '2029-08-01'),
                       ('été 2025', '2025-08-01'), ('Tokyo 2020 tenus en 2021', '2021-08-01'),
                       ('Athènes 1896', '1896-04-10'), ('1re Olympiade, été 776 av. J.-C.', '-775-08-01'),
                       ('Olympiade de 332 av. J.-C.', '-331-08-01')):
        r = m.read(t_from_date(iso))['jeux']
        out[label] = {'date': iso, 'secteur': r['inscription'], 'annee_de_l_olympiade': r['annee_de_l_olympiade'],
                      'olympiade_numero': r.get('olympiade_numero')}
    out['explication'] = (
        "Le cycle antique commence à l'été 776 av. J.-C. (année astronomique −775) ; comme il n'y a pas d'année 0, "
        "les années olympiques antiques prolongées sont celles ≡ 1 (mod 4) : 1 apr. J.-C., …, 2021, 2025, 2029. "
        "Les Jeux modernes (depuis 1896) tombent les années divisibles par 4 : ils sont décalés d'un an. Calée sur "
        "le cycle antique, l'aiguille montre donc ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ à l'été 2025 et 2029, et ΝΕΜΕΑ ΑΛΙΕΙΑ (4e année de "
        "l'olympiade) pendant les Jeux de Los Angeles 2028. Clin d'œil : les Jeux de Tokyo 2020, reportés à l'été 2021, "
        "sont tombés une année « olympique » antique.")
    return out


# ============================================================================= exports
def glyphs_payload():
    m0 = Machine()
    tabs = {'limits': glyph_table(m0, 0.0, 'limits'), 'freeth2014': glyph_table(m0, 0.0, 'freeth2014')}
    eym = freeth2014_eym()
    mc = calibrate()
    tc = mc.saros_cycle_start_before(mc.calibration['t_epoch'])
    cal_tabs = {r: glyph_table(mc, tc, r) for r in ('limits', 'freeth2014')}
    jd_fm1 = jd_from_date(-204, 5, 12, 12.0, 'julian')
    ma = calibrate(jd_fm1)
    ta = ma.saros_cycle_start_before(ma.calibration['t_epoch'] + 0.5 * ma.month)
    anc_tabs = {r: glyph_table(ma, ta, r) for r in ('limits', 'freeth2014')}
    hist = {'source': 'Freeth 2014, PLoS ONE 9(7):e103275 (texte : « There are 51 glyphs, with 38 predictions of lunar '
                      'eclipses and 28 predictions of solar eclipses » ; motif lunaire 8-7-8-7-8 babylonien)',
            'cases_avec_glyphe': 51, 'lunaires': 38, 'solaires': 28}
    comp = {
        'modele_limites_vs_EYM': compare_tables(eym, tabs['limits']),
        'modele_regle_freeth_vs_EYM': compare_tables(eym, tabs['freeth2014']),
        'machine_calee_205avJC_regle_freeth_vs_EYM': compare_tables(eym, anc_tabs['freeth2014']),
        'machine_calee_205avJC_limites_vs_EYM': compare_tables(eym, anc_tabs['limits']),
    }
    return {
        'titre': "Glyphes d'éclipse du cadran de Saros",
        'avertissement': "Tables CALCULÉES PAR NOTRE MODÈLE (positions Soleil moyen / Lune / aiguille du Dragon de la "
                         "machine) sauf 'historique_EYM_Freeth2014', reconstruction publiée du cadran antique.",
        'spec_sha256': m0.spec_sha256,
        'limites': dict(LIMITS, geometrie=ecliptic_limits()), 'regle_freeth2014': FREETH_RULE,
        'historique_publie': hist,
        'historique_EYM_Freeth2014': eym,
        'modele_epoque_t0': tabs,
        'machine_calee_J2000_cycle_contenant_J2000': dict(cal_tabs, epoque=mc.calibration['epoch']),
        'machine_calee_205avJC_cycle_de_FM1': dict(anc_tabs, epoque=ma.calibration['epoch'],
                                                  note="machine calée sur les éléments moyens du 12 mai 205 av. J.-C. "
                                                       "(FM1 de Freeth 2014), cadran de Saros commençant au 1er croissant "
                                                       "précédant FM1"),
        'comparaisons': comp,
    }


def export_payload(glyphs=None):
    m0 = Machine(); mc = calibrate()
    glyphs = glyphs or glyphs_payload()
    S = m0.S
    bodies = {}
    for k, b in m0.bodies.items():
        bodies[k] = {'parent': b['parent'], 'axis': b['axis'], 'kind': b['kind'],
                     'rate_rel_parent': [m0.rel[k].numerator, m0.rel[k].denominator] if k in m0.rel else None,
                     'rate_abs': [m0.rate_abs[k].numerator, m0.rate_abs[k].denominator] if k in m0.rate_abs else None}
    sp = {w: {'pointer_body': s['body'], 'turns': s['turns'], 'cells': s['cells'], 'r_start': s['r_start'],
              'pitch': s['pitch'], 'q_turns_per_year': [s['q'].numerator, s['q'].denominator],
              'lookup': 'clés linéaires tous les π/250 de 0 à turns·2π (comme la F-curve du driver)'}
          for w, s in m0.spirals.items()}
    tests = []
    for t in (0.0, 1.0, 3.3, -7.25, 26.73, -2204.4):
        for name, m in (('modele', m0), ('cale_J2000', mc)):
            st = m.state(t)
            tests.append({'machine': name, 't': t,
                          'local_rad': {k: float(v) for k, v in st['local'].items()},
                          'psi_rad': {k: float(v) for k, v in st['psi'].items()},
                          'rho_mm': {k: float(v) for k, v in st['rho'].items()},
                          'lon_deg': {k: deg(v) for k, v in st['lon'].items()},
                          'lecture': m.read(t)})
    return {
        'titre': "Moteur de la machine d'Anticythère — export pour le portage JavaScript",
        'genere_par': 'tools/explainer/engine.py', 'date': _dt.date.today().isoformat(),
        'spec_sha256': m0.spec_sha256,
        'temps': {'annee_du_modele_jours': YEAR_DAYS, 'jd_t0_cale': JD_J2000,
                  't': 't = (JD_TT − 2451545.0) / 365.2422 (années de manivelle ; t = 0 = J2000.0 dans le mode calé)'},
        'formules': {
            'lin': "angle local = s·2π·fmod(t·n/d, 1) + phase, avec rate_rel_parent = ±n/d et s = −1 si le taux est "
                   "positif (horaire vu de face), +1 sinon ; fmod garde le signe de t (comme en C)",
            'a': 'rotation autour de +x = −2π·fmod(t·223/48, 1)',
            'pin_slot': 'slot = p + atan2(e·sin(p − beta), r − e·cos(p − beta)) avec p = angle local du corps à goupille',
            'lune': 'e_inner = e_table − kp ; moon = −e_inner ; q = b − moon (boule de phase, autour de l\'axe radial)',
            'sorties_planetes_superieures': 'θ(t_X) = θ_b − slot',
            'suiveurs': 'θ_F = θ_b + g0 + atan2(d·sin(lam), i + d·cos(lam)), lam = θ(épicycle, local) + pin_phase − g0',
            'monde': 'θ_monde = θ_local + θ_local(parent) si parent ∈ {b, e_table}',
            'longitudes': 'λ = −(θ_monde + marker_local) (croît dans le sens horaire vu de face, 0 = début du Bélier '
                          'sur +x) ; Lune = −θ(moon) ; Soleil moyen = −θ(b) ; nœud ascendant = −θ(t_nodes) ; '
                          'phase = q mod 2π (0 = nouvelle lune)',
            'spirales': 'psi = turns·2π·frac(t·q + psi0/(turns·2π)), psi0 = phase du corps pointeur ; case = '
                        'floor(psi/(turns·2π)·cells) + 1 ; rayon = spirale à deux centres (rho_exact) ou table linéaire',
            'cadrans_secondaires': "psi = θ_monde mod 2π (horaire vu de l'arrière depuis 12 h) ; secteur = "
                                   "floor(((psi − tilt) mod 2π)/(2π/secteurs))",
            'calendrier': 'jour (0..364) = floor(λ_Soleil_moyen/360·365 + décalage_anneau) ; mois = jour // 30',
        },
        'rapport_manivelle': [m0.crank_rate.numerator, m0.crank_rate.denominator],
        'corps': bodies,
        'goupilles_rainures': {s: dict(p) for s, p in m0.pin_slots.items()},
        'sorties_de_rainure': m0.out_of_slot,
        'suiveurs': m0.followers,
        'marqueurs_rad': m0.marker,
        'spirales': sp,
        'cadrans_secondaires': m0.subsidiary,
        'libelles': {'zodiaque_grec': m0.zodiac, 'zodiaque_fr': ZODIAC_FR,
                     'mois_egyptiens_grec': S['dials']['front']['calendar_ring']['month_labels'],
                     'mois_egyptiens_fr': EGYPT_MONTHS_FR, 'jeux_fr': GAMES_FR,
                     'planetes': {b: n for b, _, n in PLANETS}},
        'phases': {'modele': {}, 'cale_J2000': mc.phases,
                   'note': "phase = constante ajoutée à l'angle local linéaire du corps ; pour n et g (spirales) c'est "
                           "psi0 ∈ [0, tours·2π) : rotation = lin + psi0, curseur = tours·2π·frac(t·q + psi0/(tours·2π))"},
        'blender_film_2026': blender_offsets(mc, 26.0),
        'calage_J2000': mc.calibration,
        'derive': drift_report(m0),
        'limites_ecliptiques': dict(LIMITS, geometrie=ecliptic_limits()), 'regle_freeth2014': FREETH_RULE,
        'glyphes': {
            'modele_t0_limites': [c['glyph'] for c in glyphs['modele_epoque_t0']['limits']['cells']],
            'cale_J2000_limites': [c['glyph'] for c in glyphs['machine_calee_J2000_cycle_contenant_J2000']['limits']['cells']],
            'cale_J2000_t_debut_cycle': glyphs['machine_calee_J2000_cycle_contenant_J2000']['limits']['t_debut_cycle'],
            'historique_EYM_Freeth2014': [c['glyph'] for c in glyphs['historique_EYM_Freeth2014']['cells']],
            'convention': "modèle : Η = nouvelle lune qui ouvre la case ; calé (Freeth 2014) : cases au 1er croissant, "
                          "Η = nouvelle lune qui termine la case, Σ = pleine lune du milieu",
        },
        'ancres': ANCHORS,
        'vecteurs_de_test': tests,
    }


def report_payload():
    m0 = Machine(); mc = calibrate()
    sky = compare_sky(mc)
    ev = machine_events('2026-01-01', '2028-12-31', machine=mc)
    sky['debuts_de_retrogradation_machine'] = {
        key: [e['date'].split(' ')[0] for e in ev if e['type'] == 'début de rétrogradation' and e['planete'] == name]
        for _, key, name in PLANETS}
    return {'derive_par_siecle': drift_report(m0), 'machine_vs_ciel_2026_2028': sky,
            'eclipses_2026_2028_regle_limites': compare_with_nasa(mc, 'limits'),
            'eclipses_2026_2028_regle_freeth2014': compare_with_nasa(mc, 'freeth2014'),
            'jeux_olympiques': olympiad_check(mc),
            'calage': mc.calibration}


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, Fraction):
        return frac_str(o)
    raise TypeError(type(o))


def write_json(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=_json_default))
    return path


# ============================================================================= auto-test
def selftest(verbose=True):
    ok = []

    def check(name, cond, info=''):
        ok.append((name, bool(cond), info))
        if verbose:
            print('%-4s %s %s' % ('OK' if cond else 'FAIL', name, info))

    m = Machine()
    rng = np.random.default_rng(20260925)
    T = np.r_[0.0, 1e-3, 19.0, -50.0, rng.uniform(-60, 60, 300)]
    # 1. taux absolus = relatif + parent
    bad = [k for k, b in m.bodies.items() if k in m.rel and b['parent'] not in (None,) and k in m.rate_abs
           and m.rate_abs[k] != m.rel[k] + m.rate_abs.get(b['parent'], 0)]
    check('taux absolus = relatifs + parent', not bad, str(bad))
    # 2. contre le solveur indépendant tools/check_kinematics.py
    src = (ROOT / 'tools' / 'check_kinematics.py').read_text().split('rng = np.random.default_rng')[0]
    argv = sys.argv; sys.argv = [argv[0], str(SPEC_PATH)]
    ns = {}
    try:
        exec(src, ns)
    finally:
        sys.argv = argv
    Aref = ns['angles'](T); A = m.local(T); W = m.world(T, A)
    worst = 0.0
    for bid, b in m.bodies.items():
        if bid in ('frame', 'a'):
            continue
        if bid == 'q':
            ref, got = Aref['q_rel'], A['q']
        elif b['parent'] in ('b', 'e_table'):
            ref = Aref.get(bid + '_local', Aref.get(bid)); got = A[bid]
        else:
            ref, got = Aref[bid], W[bid]
        worst = max(worst, float(np.max(np.abs(wrappi(got - ref)))))
    check('état = solveur indépendant (check_kinematics)', worst < 1e-9, 'max %.1e rad' % worst)
    # 3. contre les expressions de drivers générées pour Blender (build/am/expr.py)
    try:
        sys.path.insert(0, str(ROOT / 'build'))
        from am import expr as EX, spec as SS
        spec = SS.Spec(m.S)
        ex = EX.build(spec); sl = EX.slider_exprs(spec)
        w2 = 0.0; ws = 0.0
        for t in list(T[:60]) + [2026.5, -2204.25, 3000.125]:
            vals = EX.eval_all(ex, float(t)); Am = m.local(t)
            for bid, v in vals.items():
                w2 = max(w2, abs(float(wrappi(v - Am[bid]))))
            for which, s in sl.items():
                ws = max(ws, abs(EX.evaluate(s['expr'], {'c': float(t)}) - float(m.psi_spiral(which, t))))
        check('état = expressions des drivers Blender (am/expr.py)', w2 < 1e-9 and ws < 1e-9,
              'max %.1e rad, curseurs %.1e' % (w2, ws))
    except ImportError as e:  # pragma: no cover
        check('expressions des drivers (am/expr.py) importables', False, str(e))
    # 4. valeurs connues
    q0 = float(m.local(0.0)['q'])
    check('phase de la Lune à t=0 = −0.0773916', abs(q0 + 0.0773916) < 1e-6, '%.7f' % q0)
    tt = np.linspace(0, 1, 200001); lts = np.unwrap(m.longitudes(tt)['soleil_vrai'])
    apo = math.degrees(lts[np.argmin(np.gradient(lts, tt))]) % 360
    check('apogée du Soleil vrai (Hipparque) ≈ 65.5°', abs(apo - 65.5) < 0.05, '%.3f°' % apo)
    tl = np.linspace(0, 19, 400001); lm = np.unwrap(m.longitudes(tl)['lune'])
    slope = np.polyfit(tl, lm, 1)[0] / TAU
    check('mouvement moyen de la Lune = 254/19 tour/an', abs(slope - 254 / 19) < 1e-4, '%.6f' % slope)
    # 5. calendriers
    check('JD(2000-01-01 12:00) = 2451545.0', jd_from_date(2000, 1, 1, 12.0) == JD_J2000)
    check('JD(-4712-01-01 12:00 julien) = 0', jd_from_date(-4712, 1, 1, 12.0, 'julian') == 0.0)
    check('Nabonassar : JD 1448638 = 26/02/−746 julien, mercredi',
          jd_from_date(-746, 2, 26, 12.0, 'julian') == 1448638.0 and int(1448638 + 1.5) % 7 == 3)
    rt = [abs(parse_date(format_jd(j).split(' (')[0].split(' [')[0].replace(' TT', '').replace(' ', 'T')) - j)
          for j in (2451545.0, 1646679.25, 2461264.75, 2299160.5)]
    check('aller-retour date <-> JD', max(rt) < 1e-3, 'max %.1e j' % max(rt))
    # 6. EYM de Freeth 2014 : 51 glyphes, 38 Σ, 28 Η, glyphe 13 solaire, 149 = Σ Η
    e = freeth2014_eym(); s = e['stats']
    check('EYM Freeth 2014 : 51 cases, 38 Σ, 28 Η', (s['cases_avec_glyphe'], s['lunaires'], s['solaires']) == (51, 38, 28),
          str((s['cases_avec_glyphe'], s['lunaires'], s['solaires'])))
    check('EYM : glyphe 13 = Η, glyphe 149 = Σ Η', e['cells'][12]['solaire'] and e['cells'][148]['glyph'] == 'Σ Η')
    check('EYM : motif lunaire 8-7-8-7-8 (cyclique)', cyclic_equal(s['groupes_lunaires'], [8, 7, 8, 7, 8]),
          str(s['groupes_lunaires']))
    ma = calibrate(jd_from_date(-204, 5, 12, 12.0, 'julian'))
    ta = ma.saros_cycle_start_before(ma.calibration['t_epoch'] + 0.5 * ma.month)
    cmp_ = compare_tables(e, glyph_table(ma, ta, 'freeth2014'))['sans_decalage']['glyphes_communs']
    check('machine calée en 205 av. J.-C. + règle EYM : ≥ 60 des 66 prédictions de Freeth 2014 aux mêmes cases',
          cmp_ >= 60, '%d/66' % cmp_)
    # 7. glyphes du modèle (t = 0 : Soleil au nœud à la 1re nouvelle lune)
    g = glyph_table(m, 0.0, 'limits')
    check('modèle t=0 : case 1 = éclipse de Soleil', g['cells'][0]['solaire'], g['cells'][0]['glyph'])
    # 8. calage J2000
    mc = calibrate()
    el = mean_elements(JD_J2000)
    A0 = mc.local(0.0); L0 = mc.longitudes(0.0, A0)
    errs = {
        'soleil': wrappi(L0['soleil_moyen'] - math.radians(el['sun_L0'])),
        'lune_moyenne': wrappi((A0['e_table'] - A0['k']) - math.radians(el['moon_L'])),
        'noeud': wrappi(L0['noeud_ascendant'] - math.radians(el['moon_Omega'])),
    }
    for body, key in (('t_mars', 'mars'), ('t_jupiter', 'jupiter'), ('t_saturn', 'saturn')):
        pin = mc.pin_slots[mc.out_of_slot[body]]['pin']
        errs[key] = wrappi(-(mc.lin('b', 0.0)) + A0[pin] - mc.marker[body] - math.radians(el[key]))
    worst = max(abs(float(v)) for v in errs.values())
    check('calage J2000 : éléments moyens exacts', worst < 1e-9, 'max %.1e rad' % worst)
    tt = np.linspace(-0.5, 0.5, 200001); lts = np.unwrap(mc.longitudes(tt)['soleil_vrai'])
    apo = math.degrees(lts[np.argmin(np.gradient(lts, tt))]) % 360
    check('calage J2000 : apogée solaire = %.2f°' % (el['sun_apogee'] % 360), abs(apo - el['sun_apogee'] % 360) < 0.05, '%.3f°' % apo)
    # anomalie lunaire : Lune vraie − moyenne ≈ +asin(e/r)·sin M'
    Mp = math.radians(el['moon_M'])
    dl = float(wrappi(L0['lune'] - (A0['e_table'] - A0['k'])))
    p = mc.pin_slots['kp']
    check('calage J2000 : équation du centre lunaire au bon signe',
          abs(dl - math.atan2(p['e'] * math.sin(Mp), p['r'] - p['e'] * math.cos(Mp))) < 1e-9,
          '%.3f° (réel ≈ 6.289·sin M\' = %.3f°)' % (math.degrees(dl), 6.289 * math.sin(Mp)))
    # Mercure/Vénus : élongation = modèle circulaire héliocentrique
    for body, key, fr in (('t_mercury', 'mercury', 'mercure'), ('t_venus', 'venus', 'venus')):
        f = mc.followers[body]; ls, lp = math.radians(el['sun_L0']), math.radians(el[key])
        ref = math.atan2(f['d'] * math.sin(lp - ls), f['i'] + f['d'] * math.cos(lp - ls))
        check('calage J2000 : élongation de %s (modèle héliocentrique circulaire)' % fr,
              abs(float(wrappi(L0[fr] - L0['soleil_moyen'] - ref))) < 1e-9)
    # 9. syzygie et éclipse réelle : NM du 12 août 2026 à moins d'un jour
    ts = float(t_from_jd(parse_date('2026-08-12T17:47:05')))
    tn = float(mc.syzygy(ts, 0.0))
    check('calé : nouvelle lune de la machine près de l\'éclipse du 12/08/2026', abs(tn - ts) * YEAR_DAYS < 1.0,
          '%.2f h' % ((tn - ts) * YEAR_DAYS * 24))
    # 10. Jeux
    r28 = mc.read(t_from_date('2028-07-21'))['jeux']; r29 = mc.read(t_from_date('2029-08-01'))['jeux']
    r776 = mc.read(t_from_date('-775-08-01'))['jeux']
    check('Jeux : ΟΛΥΜΠΙΑ en 2029 et en 776 av. J.-C., ΝΕΜΕΑ ΑΛΙΕΙΑ en 2028',
          r29['inscription'] == 'ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ' and r776['inscription'] == 'ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ'
          and r28['inscription'] == 'ΝΕΜΕΑ ΑΛΙΕΙΑ' and r776['olympiade_numero'] == 1, '%s / %s / %s' % (r29, r776, r28))
    # ordre des Jeux dans le temps (secteurs parcourus) = paires historiques des années 1 à 4 (Freeth et al. 2008 SI,
    # Iversen 2017), et l'année calculée de chaque secteur = spec label_years
    rd = [mc.read(t_from_date('%d-08-01' % y))['jeux'] for y in range(2029, 2033)]
    order = [r['inscription'] for r in rd]
    og = mc.subsidiary['olympiad']
    years_ok = all(og['label_years'][r['secteur'] - 1] == r['annee_de_l_olympiade'] == i + 1 for i, r in enumerate(rd))
    check('Jeux : ordre ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ → ΝΕΜΕΑ ΝΑΑ → ΙΣΘΜΙΑ ΠΥΘΙΑ → ΝΕΜΕΑ ΑΛΙΕΙΑ (années 1 à 4 = label_years)',
          order == ['ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ', 'ΝΕΜΕΑ ΝΑΑ', 'ΙΣΘΜΙΑ ΠΥΘΙΑ', 'ΝΕΜΕΑ ΑΛΙΕΙΑ'] and years_ok, str(order))
    # 11. cases du cadran de Saros calé : bornes au 1er croissant
    t_b = mc.saros_cycle_start_before(0.0)
    e_b = mc.sun_moon_node(t_b)
    el_b = math.degrees(float(wrappi(e_b['moon_mean'] - e_b['sun'])))
    # (écart 2e-4° : Meeus L'(47.1) − L0(25.2) ≠ D(47.2) à 2e-4° près, théories différentes)
    check('calé : case 1 du Saros commence au 1er croissant (+2/38 mois)', abs(el_b - 360 * 2 / 38) < 1e-3, '%.5f°' % el_b)
    # 12. lecture complète
    r = mc.read(t_from_date('2026-09-25'))
    check('lecture : structure', all(k in r for k in ('soleil', 'lune', 'planetes', 'metonique', 'saros', 'jeux',
                                                        'exeligmos', 'callippique', 'calendrier_egyptien', 'aiguille_du_dragon')))
    nfail = sum(1 for _, c, _ in ok if not c)
    print('\nSELFTEST %s (%d/%d)' % ('OK' if nfail == 0 else 'FAILED', len(ok) - nfail, len(ok)))
    return nfail == 0


# ============================================================================= CLI
def _print_read(r, indent=0):
    pad = '  ' * indent
    for k, v in r.items():
        if isinstance(v, dict):
            if 'texte' in v:
                extra = [('%s=%s' % (kk, vv)) for kk, vv in v.items() if kk not in ('texte', 'longitude_deg', 'signe_grec',
                                                                                      'signe_fr', 'degre_dans_le_signe')]
                print('%s%s : %s%s' % (pad, k, v['texte'], ('  [' + ', '.join(extra) + ']') if extra else ''))
            else:
                print('%s%s :' % (pad, k)); _print_read(v, indent + 1)
        else:
            print('%s%s : %s' % (pad, k, v))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--selftest', action='store_true')
    sub = ap.add_subparsers(dest='cmd')
    p = sub.add_parser('read', help='lecture de la machine à une date ou à un temps de manivelle')
    p.add_argument('--date'); p.add_argument('--t', type=float); p.add_argument('--model', action='store_true',
                                                                               help='machine non calée (am.blend)')
    p.add_argument('--json', action='store_true')
    p = sub.add_parser('events', help='événements de la machine calée')
    p.add_argument('--from', dest='d0', default='2026-01-01'); p.add_argument('--to', dest='d1', default='2028-12-31')
    p.add_argument('--rule', default='limits', choices=['limits', 'freeth2014'])
    p.add_argument('--no-syzygies', action='store_true')
    sub.add_parser('glyphs', help='écrit build/out/explainer/glyphs.json')
    sub.add_parser('report', help='dérive, éclipses 2026-2028 vs NASA, Olympiades -> report.json')
    sub.add_parser('export', help='écrit engine_export.json (et glyphs.json)')
    sub.add_parser('all', help='glyphs + report + export')
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if a.cmd == 'read':
        m = Machine() if a.model else calibrate()
        t = a.t if a.t is not None else t_from_date(a.date or _dt.date.today().isoformat())
        r = m.read(t)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=1, default=_json_default))
        else:
            _print_read(r)
        return 0
    if a.cmd == 'events':
        for e in machine_events(a.d0, a.d1, a.rule):
            if a.no_syzygies and e['type'] in ('nouvelle lune', 'pleine lune'):
                continue
            extra = {k: v for k, v in e.items() if k not in ('type', 't', 'jd', 'date')}
            print('%-28s %-24s %s' % (e['date'], e['type'], json.dumps(extra, ensure_ascii=False)))
        return 0
    if a.cmd in ('glyphs', 'export', 'all'):
        g = glyphs_payload()
        print('écrit', write_json(OUT_DIR / 'glyphs.json', g))
        for k, v in g['comparaisons'].items():
            print('  %-45s %s' % (k, v))
        if a.cmd in ('export', 'all'):
            print('écrit', write_json(OUT_DIR / 'engine_export.json', export_payload(g)))
    if a.cmd in ('report', 'all'):
        rep = report_payload()
        print('écrit', write_json(OUT_DIR / 'report.json', rep))
        print(json.dumps({k: rep[k] for k in ('derive_par_siecle', 'jeux_olympiques')}, ensure_ascii=False, indent=1))
        for row in rep['eclipses_2026_2028_regle_limites']['eclipses']:
            print(row)
    if a.cmd is None:
        ap.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
