#!/usr/bin/env python3
"""Anticythere 2.0 -- modern astronomical constants.

Builds  v2/research/constants.json  (machine-readable)  and
        v2/research/constants.md    (French, human-readable)
from values transcribed by hand from the cited sources (kept here as exact
decimal strings), plus derived quantities and cross-source checks.

Run with Blender's Python (numpy):
  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 \
      v2/tools/build_constants.py

Conventions: epoch J2000.0 = JD 2451545.0 TT; T = Julian centuries of 36525 d
from J2000.0 (TT/TDB); "sidereal" rates are referred to the fixed mean ecliptic
and equinox of J2000; "tropical" rates to the mean equinox of date.
Code and keys are in English; free-text notes and the .md are in French.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction as F
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[1]
OUT_JSON = V2 / "research" / "constants.json"
OUT_MD = V2 / "research" / "constants.md"
ACCESSED = "2026-10-03"

JC = F(36525)            # days per Julian century
ARCSEC_PER_TURN = F(1296000)
DEG = math.pi / 180.0

# ----------------------------------------------------------------------------
# Sources
# ----------------------------------------------------------------------------
SOURCES = {
    "JPL_APPROX": {
        "cite": "E.M. Standish & J.G. Williams, 'Keplerian Elements for Approximate Positions of the Major Planets', JPL Solar System Dynamics (tables 1, 2a, 2b)",
        "url": "https://ssd.jpl.nasa.gov/planets/approx_pos.html",
        "snapshot": "v2/research/sources/jpl_approx_pos_2026-10-03.txt",
    },
    "JPL_APPROX_2019": {
        "cite": "Same JPL tables, archived text version that still contained Pluto (Wayback Machine, 2019)",
        "url": "https://web.archive.org/web/2019/https://ssd.jpl.nasa.gov/txt/p_elem_t1.txt",
        "url2": "https://web.archive.org/web/2019/https://ssd.jpl.nasa.gov/txt/p_elem_t2.txt",
        "snapshot": "v2/research/sources/jpl_p_elem_t1_archived_2019.txt",
    },
    "SIMON1994": {
        "cite": "J.-L. Simon, P. Bretagnon, J. Chapront, M. Chapront-Touzé, G. Francou, J. Laskar, 'Numerical expressions for precession formulae and mean elements for the Moon and the planets', A&A 282, 663-683 (1994) -- sect. 3.4-3.5 (Moon), 5.8 (planets, J2000), 5.9 (planets, of date). VSOP87 / JASON84 / ELP 2000-82 mean elements.",
        "url": "https://articles.adsabs.harvard.edu/pdf/1994A%26A...282..663S",
        "url2": "https://ui.adsabs.harvard.edu/abs/1994A&A...282..663S",
    },
    "IERS2010": {
        "cite": "IERS Conventions (2010), IERS Technical Note 36, chapter 5 (G. Petit & B. Luzum eds.): eq. 5.14 (ERA), 5.32 (GMST), 5.39-5.40 (IAU 2006 precession, obliquity), 5.43 (Delaunay arguments, Simon et al. 1994), 5.44 (planetary mean longitudes), table 5.1a (lunar periods), table 5.3a (nutation)",
        "url": "https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf",
    },
    "MEEUS1998": {
        "cite": "J. Meeus, Astronomical Algorithms, 2nd ed., Willmann-Bell (1998): ch. 12, 22, 25, 28, 31 (table 31.A), 44, 47 (tables 47.A/47.B), 49, 54. Book not online: coefficients transcribed through the open-source (MIT) implementation soniakeys/meeus, files planetelements.go, moonposition.go, jupitermoons.go, eqtime.go, nutation.go, solar.go, sidereal.go, moonphase.go, eclipse.go",
        "url": "https://github.com/soniakeys/meeus/tree/master/v3",
    },
    "CAPITAINE2003": {
        "cite": "N. Capitaine, P.T. Wallace, J. Chapront, 'Expressions for IAU 2000 precession quantities', A&A 412, 567 (2003) = IAU 2006 precession (P03); general precession p_A quoted through Wikipedia 'Axial precession'",
        "url": "https://en.wikipedia.org/wiki/Axial_precession",
        "url2": "https://doi.org/10.1051/0004-6361:20031539",
    },
    "LASKAR1986_TY": {
        "cite": "Mean tropical year polynomial (McCarthy & Seidelmann 2009, from Laskar 1986), quoted by Wikipedia 'Tropical year'; also the equinox/solstice years of Meeus & Savoie (1992)",
        "url": "https://en.wikipedia.org/wiki/Tropical_year",
    },
    "CHAPRONT2002": {
        "cite": "J. Chapront, M. Chapront-Touzé, G. Francou, 'A new determination of lunar orbital parameters, precession constant and tidal acceleration from LLR measurements', A&A 387, 700 (2002); month lengths quoted by Wikipedia 'Lunar month'",
        "url": "https://en.wikipedia.org/wiki/Lunar_month",
        "url2": "https://doi.org/10.1051/0004-6361:20020420",
    },
    "NSSDC": {
        "cite": "NASA NSSDCA Planetary Fact Sheets (D.R. Williams; pages updated Jan 2024 - May 2025)",
        "url": "https://nssdc.gsfc.nasa.gov/planetary/factsheet/",
        "snapshot": "v2/research/sources/nssdc_factsheets_extract_2026-10-03.json",
    },
    "NSSDC_MOON": {
        "cite": "NASA NSSDCA Moon Fact Sheet",
        "url": "https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html",
    },
    "NSSDC_JOVSAT": {
        "cite": "NASA NSSDCA Jovian Satellite Fact Sheet",
        "url": "https://nssdc.gsfc.nasa.gov/planetary/factsheet/joviansatfact.html",
    },
    "JPL_SAT": {
        "cite": "JPL SSD, Planetary Satellite Mean Elements (ephemeris JUP365, Jacobson 2021)",
        "url": "https://ssd.jpl.nasa.gov/sats/elem/sep.html",
        "snapshot": "v2/research/sources/jpl_sat_mean_elements_galilean_2026-10-03.txt",
    },
    "LIESKE_E5": {
        "cite": "J.H. Lieske, 'Galilean satellite ephemerides E5', A&A Suppl. 129, 205 (1998); mean longitudes l1..l4 as given in Meeus ch. 44 (soniakeys jupitermoons.go)",
        "url": "https://github.com/soniakeys/meeus/blob/master/v3/jupitermoons/jupitermoons.go",
    },
    "CELLETTI2021": {
        "cite": "A. Celletti et al., 'Laplace-like resonances with tidal effects', A&A (2021), arXiv:2109.02694 -- 'Lieske (1998) observed ... Phi_L = 180 deg up to a libration with small amplitude and period of about 2071 days'",
        "url": "https://arxiv.org/abs/2109.02694",
    },
    "WIKI_RESONANCE": {
        "cite": "Wikipedia 'Orbital resonance' (Laplace resonance; libration amplitude 0.03 deg, period ~2000 d, citing Sinclair 1975)",
        "url": "https://en.wikipedia.org/wiki/Orbital_resonance",
    },
    "NASA_ECL": {
        "cite": "F. Espenak (NASA GSFC eclipse web site): 'Periodicity of Solar Eclipses', 'Periodicity of Lunar Eclipses', 'Saros', 'Eclipses and the Moon's Orbit'",
        "url": "https://eclipse.gsfc.nasa.gov/SEsaros/SEperiodicity.html",
        "url2": "https://eclipse.gsfc.nasa.gov/SEhelp/moonorbit.html",
        "url3": "https://eclipse.gsfc.nasa.gov/SEsaros/SEsaros.html",
        "url4": "https://eclipse.gsfc.nasa.gov/LEsaros/LEperiodicity.html",
    },
    "WIKI_ECL_CYCLE": {
        "cite": "Wikipedia 'Eclipse cycle' (table from Meeus 1991/1997)",
        "url": "https://en.wikipedia.org/wiki/Eclipse_cycle",
    },
    "WIKI_SOLAR_ECLIPSE": {
        "cite": "Wikipedia 'Solar eclipse' (Sun within about 15 to 18 deg of a node; 10 to 12 deg for central eclipses -- Littmann, Espenak & Willcox, Totality)",
        "url": "https://en.wikipedia.org/wiki/Solar_eclipse",
    },
    "WIKI_GAMMA": {
        "cite": "Wikipedia 'Gamma (eclipse)' (central limit 0.9972; partial limit 1.525-1.571; sign conventions; Meeus)",
        "url": "https://en.wikipedia.org/wiki/Gamma_(eclipse)",
    },
    "HOLMES_ECL": {
        "cite": "S. Holmes, 'Eclipses - the theory' (quotes Meeus' major ecliptic limits 18 deg 24' solar, 12 deg 08' lunar). Secondary, non-academic source: used only as an indicator.",
        "url": "https://freehostspace.firstcloudit.com/steveholmes/eclfact1.htm",
    },
    "WIKI_EOT": {
        "cite": "Wikipedia 'Equation of time' (two-sine approximation; component amplitudes 7.66 and 9.87 min; extremes; Hughes et al. 1989, MNRAS 238, 1529)",
        "url": "https://en.wikipedia.org/wiki/Equation_of_time",
    },
    "WIKI_SIDEREAL": {
        "cite": "Wikipedia 'Sidereal time' (Urban & Seidelmann 2013, Explanatory Supplement 3rd ed.)",
        "url": "https://en.wikipedia.org/wiki/Sidereal_time",
    },
    "WIKI_GREGORIAN": {
        "cite": "Wikipedia 'Gregorian calendar'",
        "url": "https://en.wikipedia.org/wiki/Gregorian_calendar",
    },
    "WIKI_AXIAL_TILT": {
        "cite": "Wikipedia 'Axial tilt' (IAU 2006 and IAU 1976/1980 obliquity polynomials; long-term range and 41,040-yr period, Laskar)",
        "url": "https://en.wikipedia.org/wiki/Axial_tilt",
    },
    "WIKI_YEAR": {
        "cite": "Wikipedia 'Year' (sidereal year 365.256363004 d, anomalistic year 365.259636 d, draconic year 346.620075883 d)",
        "url": "https://en.wikipedia.org/wiki/Year",
    },
    "WIKI_LUNAR_THEORY": {
        "cite": "Wikipedia 'Lunar theory' (main longitude terms of E.W. Brown, Tables of the Motion of the Moon, 1919)",
        "url": "https://en.wikipedia.org/wiki/Lunar_theory",
    },
    "AA_LOWPREC": {
        "cite": "Astronomical Almanac low-precision lunar formulae (Brown-based), quoted in D.G. Simpson, 'An alternative lunar ephemeris model for on-board flight software use', NASA GSFC Flight Mechanics Symposium (1999), eq. 1-3",
        "url": "https://caps.gsfc.nasa.gov/simpson/pubs/slunar.pdf",
    },
    "SCHLYTER": {
        "cite": "P. Schlyter, 'Computing planetary positions' (sect. 9-10: lunar perturbations; Jupiter-Saturn great inequality)",
        "url": "https://stjarnhimlen.se/comp/ppcomp.html",
    },
    "JPL_HORIZONS": {
        "cite": "JPL Horizons API, ephemeris DE441: osculating elements of the planetary system barycenters (heliocentric and SSB-centred), ecliptic & equinox J2000, TDB, 2000-01-01 to 2100-01-01 every 10 d; linear least-squares fit of L = Omega + omega + M (v2/tools/fetch_horizons_rates.py)",
        "url": "https://ssd.jpl.nasa.gov/api/horizons.api",
        "snapshot": "v2/research/sources/horizons/horizons_rates_2000_2100.json (+ raw rows *.csv.gz)",
    },
    "USNO_DT": {
        "cite": "USNO, TT-UT predictions (deltat.preds)",
        "url": "https://maia.usno.navy.mil/ser7/deltat.preds",
        "snapshot": "v2/research/sources/usno_deltat_preds.txt",
    },
}


# ----------------------------------------------------------------------------
# French accents for the free-text notes (written in ASCII in this file)
# ----------------------------------------------------------------------------
import re as _re

_ACCENTS = {
    "accelere": "accélère", "ajuste": "ajusté", "annee": "année", "anticythere": "Anticythère",
    "archive": "archivée", "calculee": "calculée", "chaines": "chaînes", "cite": "cité", "completent": "complètent",
    "consequence": "conséquence", "conservees": "conservées", "controle": "contrôle", "decale": "décale",
    "decales": "décalés", "decimales": "décimales", "definition": "définition", "deforme": "déforme", "dela": "delà",
    "derive": "dérivé", "diametre": "diamètre", "difference": "différence", "differente": "différente",
    "differentes": "différentes", "documentee": "documentée", "ecart": "écart", "ecarts": "écarts", "eclipse": "éclipse",
    "eclipses": "éclipses", "ecliptique": "écliptique", "elements": "éléments", "equation": "équation",
    "equinoxe": "équinoxe", "etait": "était", "etoiles": "étoiles", "evection": "évection", "evenement": "événement",
    "excentricite": "excentricité", "fevr": "févr", "geantes": "géantes", "generale": "générale", "geometrie": "géométrie",
    "geometrique": "géométrique", "gregorien": "grégorien", "heliocentriques": "héliocentriques",
    "hemisphere": "hémisphère", "incoherence": "incohérence", "inegalite": "inégalité", "inegalites": "inégalités",
    "lie": "lié", "lumiere": "lumière", "mecanique": "mécanique", "meme": "même", "millenaires": "millénaires",
    "negligeable": "négligeable", "noeud": "nœud", "noeuds": "nœuds", "obliquite": "obliquité",
    "penombrales": "pénombrales", "perigee": "périgée", "perihelie": "périhélie", "perijove": "périjove", "entrainant": "entraînant", "egale": "égale", "force": "forcé", "retrograde": "rétrograde",
    "periode": "période", "periodes": "périodes", "periodique": "périodique", "perturbe": "perturbé",
    "phenomenes": "phénomènes", "planetaire": "planétaire", "planetaires": "planétaires", "planete": "planète",
    "planetes": "planètes", "portee": "portée", "precession": "précession", "pres": "près", "ramene": "ramène",
    "rapportee": "rapportée", "realise": "réalise", "redefinition": "redéfinition", "reduction": "réduction",
    "reference": "référence", "regle": "règle", "repere": "repère", "residu": "résidu", "resonance": "résonance",
    "retiree": "retirée", "retrograde": "rétrograde", "roemer": "Rømer", "separe": "sépare", "seculaire": "séculaire",
    "serie": "série", "sideral": "sidéral", "siderale": "sidérale", "siecle": "siècle", "siecles": "siècles",
    "theorie": "théorie", "tolerance": "tolérance", "touze": "Touzé", "unite": "unité", "utilisee": "utilisée",
    "verifie": "vérifié", "jusqu'a": "jusqu'à", "d'ou": "d'où", "l'annee": "l'année", "l'eclipse": "l'éclipse",
    "l'ecliptique": "l'écliptique", "l'equation": "l'équation", "l'equinoxe": "l'équinoxe", "l'evenement": "l'événement",
    "deduite": "déduite", "realisee": "réalisée", "precision": "précision", "regulier": "régulier",
}


def fr(text: str) -> str:
    """Restore French accents in an ASCII-written note (word-level map + preposition 'a')."""
    if not text:
        return text

    def one(w):
        low = w.lower()
        if low in _ACCENTS:
            rep = _ACCENTS[low]
            return rep[0].upper() + rep[1:] if w[0].isupper() else rep
        return w

    def sub(m):
        w = m.group(0)
        if w.lower() in _ACCENTS or "'" not in w:
            return one(w)
        head, tail = w.split("'", 1)          # d'obliquite -> d' + obliquite
        return head + "'" + one(tail)

    def guarded(m):
        w = m.group(0)
        return w if (w.isupper() and len(w) > 1) else sub(m)

    # whole words only: never touch parts of identifiers (WIKI_RESONANCE, file names, ...)
    out = _re.sub(r"(?<![A-Za-z0-9_.])[A-Za-z]+(?:'[A-Za-z]+)?(?![A-Za-z0-9_])", guarded, text)
    # preposition 'a' -> 'à' (but keep the verb in 'gamma a le signe' and the variable in 'a sin F')
    out = _re.sub(r"(?<=\s)a(?=\s)(?!\s(?:le signe|sin\b))", "à", out)
    return out

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
CHECKS: list[dict] = []


def fl(x) -> float:
    return float(x)


def rnd(x, n=10):
    """Round floats for JSON readability without losing meaningful digits."""
    if isinstance(x, F):
        x = float(x)
    if isinstance(x, float):
        if x == 0 or not math.isfinite(x):
            return x
        return float(f"{x:.{n}g}")
    return x


def check(cid, label, a, src_a, b, src_b, tol, unit, note_fr="", explained=False):
    """Record a cross-source comparison. status: ok / explained / ATTENTION."""
    a_f, b_f = fl(a), fl(b)
    diff = a_f - b_f
    ok = abs(diff) <= tol
    status = "ok" if ok else ("explique" if explained else "ATTENTION")
    label, note_fr, unit = fr(label), fr(note_fr), fr(unit)
    CHECKS.append({
        "id": cid, "label": label, "unit": unit,
        "a": rnd(a_f, 12), "source_a": src_a,
        "b": rnd(b_f, 12), "source_b": src_b,
        "diff_a_minus_b": rnd(diff, 6), "tolerance": tol,
        "status": status, "note": note_fr,
    })
    return status


def period_days(rate_arcsec_per_cy):
    """Exact rational period (days) of an angle growing at rate ''/Julian century."""
    return JC * ARCSEC_PER_TURN / abs(F(rate_arcsec_per_cy))


def kepler_E(M, e):
    E = M + e * np.sin(M)
    for _ in range(30):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    return E


def true_anomaly(M, e):
    E = kepler_E(M, e)
    return 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))


def wrap(x):
    return (x + np.pi) % (2 * np.pi) - np.pi


def eoc_models(e):
    """Max |error| (deg) vs exact Kepler of three mechanisable equation-of-centre models."""
    M = np.linspace(0, 2 * np.pi, 200001)
    nu = true_anomaly(M, e)
    exact_max = float(np.max(np.abs(wrap(nu - M))) / DEG)
    k = 2 * e
    # (a) eccentric circle seen from an offset point = Antikythera pin-and-slot, k = 2e
    pin = np.arctan2(np.sin(M), np.cos(M) - k)
    # (b) bisected equant (Ptolemy): deferent centre at -e, equant at -2e, uniform about equant
    t = e * np.cos(M) + np.sqrt(1 - (e * np.sin(M)) ** 2)
    px, py = -2 * e + t * np.cos(M), t * np.sin(M)
    equant = np.arctan2(py, px)
    # (c) first harmonic only: M + 2e sin M
    first = M + 2 * e * np.sin(M)
    return {
        "exact_max_deg": rnd(exact_max, 6),
        "pin_and_slot_k_2e_max_err_deg": rnd(float(np.max(np.abs(wrap(pin - nu)))) / DEG, 4),
        "bisected_equant_max_err_deg": rnd(float(np.max(np.abs(wrap(equant - nu)))) / DEG, 4),
        "first_harmonic_only_max_err_deg": rnd(float(np.max(np.abs(wrap(first - nu)))) / DEG, 4),
        "series_deg": {   # nu - M = c1 sin M + c2 sin 2M + c3 sin 3M + ...
            "c1": rnd((2 * e - e ** 3 / 4 + 5 * e ** 5 / 96) / DEG, 7),
            "c2": rnd((5 * e ** 2 / 4 - 11 * e ** 4 / 24) / DEG, 7),
            "c3": rnd((13 * e ** 3 / 12 - 43 * e ** 5 / 64) / DEG, 7),
            "c4": rnd((103 * e ** 4 / 96) / DEG, 7),
        },
        "pin_and_slot_series_deg": {   # k sin + k^2/2 sin2 + k^3/3 sin3
            "c1": rnd(k / DEG, 7), "c2": rnd(k ** 2 / 2 / DEG, 7), "c3": rnd(k ** 3 / 3 / DEG, 7),
        },
    }


# ----------------------------------------------------------------------------
# 1. Earth: precession, obliquity, years, rotation
# ----------------------------------------------------------------------------
# IAU 2006 general precession in longitude p_A (Capitaine et al. 2003) ''/cy
PA_IAU2006 = F("5028.796195")
PA_IAU2006_T2 = F("1.1054348")
PA_SIMON1994 = F("5028.8200")        # Simon 1994 eq. (2): 50288.200''/millennium (Williams 1991)
PA_IAU1976 = F("5029.0966")          # IAU 1976 (Lieske 1977), Simon 1994 eq. (1)
# IERS 2010 eq. 5.39-5.40: psi_A, chi_A (''/cy) and eps0
PSI_A_IERS = F("5038.481507")
CHI_A_IERS = F("10.556403")
EPS0_IAU2006 = F("84381.406")         # ''
EPS_RATE_IAU2006 = [F("-46.836769"), F("-0.0001831"), F("0.00200340"), F("-0.000000576"), F("-0.0000000434")]
EPS0_IAU1980 = F("84381.448")         # 23d26'21.448'' (Meeus 22.2)
EPS_RATE_IAU1980 = [F("-46.8150"), F("-0.00059"), F("0.001813")]
F14_IERS_RAD = F("0.02438175")        # IERS eq. 5.44 F14 = p_A (Kinoshita & Souchay 1990), rad/cy

eps0_deg = EPS0_IAU2006 / 3600
pa_from_iers = fl(PSI_A_IERS) - fl(CHI_A_IERS) * math.cos(fl(eps0_deg) * DEG)
check("precession.pA_vs_psiA_chiA", "p_A IAU 2006 vs psi_A - chi_A cos eps0 (IERS 2010)",
      PA_IAU2006, "CAPITAINE2003", pa_from_iers, "IERS2010", 0.01, "''/siecle",
      "Relation geometrique au 1er ordre entre precession lunisolaire (psi_A), precession planetaire (chi_A) et precession generale.")
check("precession.pA_vs_Simon", "p_A IAU 2006 vs Simon 1994 (Williams 1991)",
      PA_IAU2006, "CAPITAINE2003", PA_SIMON1994, "SIMON1994", 0.05, "''/siecle",
      "Ecart de 0,024''/siecle = 2,4 ms d'arc par an : negligeable pour la machine.")
check("precession.pA_vs_IAU1976", "p_A IAU 2006 vs IAU 1976",
      PA_IAU2006, "CAPITAINE2003", PA_IAU1976, "SIMON1994", 0.05, "''/siecle",
      "IAU 1976 (Lieske 1977) etait trop grande de ~0,3''/siecle ; c'est la constante utilisee par Meeus table 31.A (voir ecart Meeus/Simon ci-dessous). Effet : 0,3''/siecle, negligeable.",
      explained=True)
check("precession.pA_vs_IERS_F14", "p_A IAU 2006 vs IERS 2010 F14 (Kinoshita & Souchay 1990, rad/siecle)",
      PA_IAU2006, "CAPITAINE2003", fl(F14_IERS_RAD) * 180 / math.pi * 3600, "IERS2010", 0.05, "''/siecle",
      "F14 de l'IERS est la valeur ancienne (~IAU 1976) utilisee seulement comme argument de nutation planetaire.",
      explained=True)

precession_period_yr = fl(ARCSEC_PER_TURN / (PA_IAU2006 / 100))   # Julian years

# --- years -------------------------------------------------------------------
# Simon 1994 sect. 5.8.3 / 5.9.3: EMB mean longitude rates (''/millennium)
EMB_LAMBDA_J2000 = F("1295977422.83429")
EMB_LAMBDA_DATE = F("1296027711.03429")
EMB_PERI_J2000 = F("11612.35290")
EMB_PERI_DATE = F("61900.55290")
# IERS 2010 eq. 5.43: Delaunay l' (Sun mean anomaly) ''/cy
L_PRIME_IERS = F("129596581.0481")
# Laskar tropical year polynomial (days), T in Julian centuries
TY_LASKAR = [F("365.2421896698"), F("-0.00000615359"), F("-7.29e-10"), F("2.64e-10")]
# JPL Table 1 EM-Bary L rate deg/cy (J2000 frame, 1800-2050 fit)
JPL_EMB_LDOT = F("35999.37244981")

sidereal_year = period_days(EMB_LAMBDA_J2000 / 10)
tropical_year_simon = period_days(EMB_LAMBDA_DATE / 10)
tropical_year_iau2006 = period_days(EMB_LAMBDA_J2000 / 10 + PA_IAU2006)
anomalistic_year = period_days(L_PRIME_IERS)
anomalistic_year_simon = period_days((EMB_LAMBDA_J2000 - EMB_PERI_J2000) / 10)
tropical_year_jpl = JC * 360 / (JPL_EMB_LDOT + PA_IAU2006 / 3600)
sidereal_year_jpl = JC * 360 / JPL_EMB_LDOT
TROPICAL_YEAR = TY_LASKAR[0]          # adopted reference value at J2000 (days of 86400 s TT)

check("year.tropical_laskar_vs_simon", "Annee tropique moyenne : Laskar (J2000) vs Simon 1994 (taux de date)",
      TY_LASKAR[0], "LASKAR1986_TY", tropical_year_simon, "SIMON1994", 2e-6, "jours")
check("year.tropical_laskar_vs_iau2006", "Annee tropique : Laskar vs (taux sideral Simon + p_A IAU 2006)",
      TY_LASKAR[0], "LASKAR1986_TY", tropical_year_iau2006, "SIMON1994+CAPITAINE2003", 2e-6, "jours")
check("year.tropical_laskar_vs_jpl", "Annee tropique : Laskar vs JPL table 1 (EMB, ajustement 1800-2050) + p_A",
      TY_LASKAR[0], "LASKAR1986_TY", tropical_year_jpl, "JPL_APPROX", 2e-5, "jours",
      "Le taux JPL est un ajustement local 1800-2050 (inclut des perturbations a longue periode) : ecart ~1 s/an attendu.")
check("year.sidereal_simon_vs_wiki", "Annee siderale : Simon 1994 vs Wikipedia 'Year'",
      sidereal_year, "SIMON1994", F("365.256363004"), "WIKI_YEAR", 2e-8, "jours")
check("year.sidereal_simon_vs_nssdc", "Annee siderale : Simon 1994 vs NSSDC (3 decimales)",
      sidereal_year, "SIMON1994", F("365.256"), "NSSDC", 6e-4, "jours")
check("year.anomalistic_iers_vs_simon", "Annee anomalistique : l' IERS vs (lambda - varpi) Simon",
      anomalistic_year, "IERS2010", anomalistic_year_simon, "SIMON1994", 1e-7, "jours")
check("year.anomalistic_iers_vs_wiki", "Annee anomalistique : IERS vs Wikipedia 'Year'",
      anomalistic_year, "IERS2010", F("365.259636"), "WIKI_YEAR", 1e-6, "jours")

# --- obliquity ----------------------------------------------------------------
eps_diff = fl(EPS0_IAU2006 - EPS0_IAU1980)
check("obliquity.eps0_2006_vs_1980", "Obliquite J2000 : IAU 2006 (84381,406'') vs IAU 1980 (84381,448'')",
      EPS0_IAU2006, "IERS2010", EPS0_IAU1980, "MEEUS1998", 0.05, "''",
      "Ecart de 0,042'' : redefinition (ecliptique inertielle vs rotationnelle, Chapront 2002). Negligeable.")
check("obliquity.rate_2006_vs_1980", "Taux d'obliquite : IAU 2006 vs IAU 1980",
      EPS_RATE_IAU2006[0], "IERS2010", EPS_RATE_IAU1980[0], "MEEUS1998", 0.05, "''/siecle")

# --- Earth rotation -----------------------------------------------------------
ERA_RATE = F("1.00273781191135448")        # IERS 5.14: turns of ERA per UT1 day (stellar day)
GMST_RATIO_MEEUS = F("1.00273790935")      # Meeus ch.12 (Aoki et al. 1982)
gmst_ratio_iers = ERA_RATE + F("4612.156534") / (JC * ARCSEC_PER_TURN)   # + precession in RA
check("rotation.gmst_ratio", "Rapport temps sideral moyen / temps solaire moyen : IERS (ERA + precession en AR) vs Meeus",
      gmst_ratio_iers, "IERS2010", GMST_RATIO_MEEUS, "MEEUS1998", 2e-12, "sans unite",
      "Ecart 5e-12 (0,4 microseconde par jour) : Meeus arrondit a 11 decimales le rapport d'Aoki et al. 1982 (GMST fonction de UT1), alors que le GMST IAU 2006 separe ERA(UT1) et precession(TT). Sans effet mecanique.",
      explained=True)
mean_sidereal_day_s = 86400 / gmst_ratio_iers
stellar_day_s = 86400 / ERA_RATE
check("rotation.sidereal_day", "Jour sideral moyen (s) : derive IERS vs Wikipedia 86164,0905 s",
      mean_sidereal_day_s, "IERS2010", F("86164.0905"), "WIKI_SIDEREAL", 1e-4, "s")

# --- equation of time ----------------------------------------------------------
E_EARTH = 0.0167086342        # Simon 1994 5.8.3
eps0 = fl(eps0_deg) * DEG
y_eot = math.tan(eps0 / 2) ** 2
eot_terms_min = {      # Smart / Meeus (28.3); E = apparent - mean solar time; minutes = rad * 720/pi
    "y_sin_2L0": y_eot * 720 / math.pi,
    "minus_2e_sin_M": 2 * E_EARTH * 720 / math.pi,
    "4ey_sinM_cos2L0": 4 * E_EARTH * y_eot * 720 / math.pi,
    "minus_half_y2_sin_4L0": 0.5 * y_eot ** 2 * 720 / math.pi,
    "minus_5_4_e2_sin_2M": 1.25 * E_EARTH ** 2 * 720 / math.pi,
}
check("eot.obliquity_amp", "EdT : amplitude du terme d'obliquite (min) -- tan^2(eps/2) vs Wikipedia",
      eot_terms_min["y_sin_2L0"], "MEEUS1998", F("9.863"), "WIKI_EOT", 0.01, "min")
check("eot.eccentricity_amp", "EdT : amplitude du terme d'excentricite (min) -- 2e vs Wikipedia",
      eot_terms_min["minus_2e_sin_M"], "MEEUS1998", F("7.659"), "WIKI_EOT", 0.01, "min")


def eot_smart_minutes(jd):
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) * DEG
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T * T) * DEG
    e = 0.016708634 - 0.000042037 * T
    eps = (84381.406 - 46.836769 * T) / 3600 * DEG
    y = np.tan(eps / 2) ** 2
    E = (y * np.sin(2 * L0) - 2 * e * np.sin(M) + 4 * e * y * np.sin(M) * np.cos(2 * L0)
         - 0.5 * y * y * np.sin(4 * L0) - 1.25 * e * e * np.sin(2 * M))
    return E * 720 / math.pi


jd2026 = 2461041.5 + np.arange(0, 365, 1 / 24)       # 2026-01-01 0h .. 2026-12-31
eot2026 = eot_smart_minutes(jd2026)
i_min, i_max = int(np.argmin(eot2026)), int(np.argmax(eot2026))


def jd_to_date(jd):
    z = int(jd + 0.5); f_ = jd + 0.5 - z
    a = z if z < 2299161 else z + 1 + int((z - 1867216.25) / 36524.25) - int(int((z - 1867216.25) / 36524.25) / 4)
    b = a + 1524; c = int((b - 122.1) / 365.25); d = int(365.25 * c); e_ = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e_) + f_
    month = e_ - 1 if e_ < 14 else e_ - 13
    year = c - 4716 if month > 2 else c - 4715
    return f"{year:04d}-{month:02d}-{int(day):02d}"


eot_min_2026 = (float(eot2026[i_min]), jd_to_date(float(jd2026[i_min])))
eot_max_2026 = (float(eot2026[i_max]), jd_to_date(float(jd2026[i_max])))
check("eot.min", "EdT minimum (min) : formule de Smart 2026 vs Wikipedia (-14 min 15 s, 11 fevr.)",
      eot_min_2026[0], "MEEUS1998", -14.25, "WIKI_EOT", 0.1, "min")
check("eot.max", "EdT maximum (min) : formule de Smart 2026 vs Wikipedia (+16 min 25 s, 3 nov.)",
      eot_max_2026[0], "MEEUS1998", 16 + 25 / 60, "WIKI_EOT", 0.1, "min")

# --- calendar -----------------------------------------------------------------
GREG_YEAR = F(146097, 400)
check("calendar.gregorian_cycle", "Cycle gregorien : 146097 j = 20871 semaines exactement",
      F(146097, 7), "WIKI_GREGORIAN", 20871, "WIKI_GREGORIAN", 0, "semaines")
greg_drift_tropical = 1 / (GREG_YEAR - TY_LASKAR[0])
greg_drift_vernal = 1 / (GREG_YEAR - F("365.242374"))
# day of week: (floor(JD + 1.5)) mod 7, 0 = Sunday
dow_j2000 = int(math.floor(2451545.0 + 1.5)) % 7
check("calendar.j2000_weekday", "Jour de la semaine de JD 2451545.0 (2000-01-01) : 6 = samedi",
      dow_j2000, "MEEUS1998", 6, "WIKI_GREGORIAN", 0, "indice (0 = dimanche)")

# ----------------------------------------------------------------------------
# 2. Planets
# ----------------------------------------------------------------------------
PLANETS = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]
FR = {"mercury": "Mercure", "venus": "Vénus", "earth": "Terre (barycentre Terre-Lune)", "mars": "Mars",
      "jupiter": "Jupiter", "saturn": "Saturne", "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluton"}

# JPL table 1 (1800-2050): a [au], e, I [deg], L [deg], varpi [deg], Omega [deg] ; rates per century
JPL_T1 = {
    "mercury": (("0.38709927", "0.20563593", "7.00497902", "252.25032350", "77.45779628", "48.33076593"),
                ("0.00000037", "0.00001906", "-0.00594749", "149472.67411175", "0.16047689", "-0.12534081")),
    "venus": (("0.72333566", "0.00677672", "3.39467605", "181.97909950", "131.60246718", "76.67984255"),
              ("0.00000390", "-0.00004107", "-0.00078890", "58517.81538729", "0.00268329", "-0.27769418")),
    "earth": (("1.00000261", "0.01671123", "-0.00001531", "100.46457166", "102.93768193", "0.0"),
              ("0.00000562", "-0.00004392", "-0.01294668", "35999.37244981", "0.32327364", "0.0")),
    "mars": (("1.52371034", "0.09339410", "1.84969142", "-4.55343205", "-23.94362959", "49.55953891"),
             ("0.00001847", "0.00007882", "-0.00813131", "19140.30268499", "0.44441088", "-0.29257343")),
    "jupiter": (("5.20288700", "0.04838624", "1.30439695", "34.39644051", "14.72847983", "100.47390909"),
                ("-0.00011607", "-0.00013253", "-0.00183714", "3034.74612775", "0.21252668", "0.20469106")),
    "saturn": (("9.53667594", "0.05386179", "2.48599187", "49.95424423", "92.59887831", "113.66242448"),
               ("-0.00125060", "-0.00050991", "0.00193609", "1222.49362201", "-0.41897216", "-0.28867794")),
    "uranus": (("19.18916464", "0.04725744", "0.77263783", "313.23810451", "170.95427630", "74.01692503"),
               ("-0.00196176", "-0.00004397", "-0.00242939", "428.48202785", "0.40805281", "0.04240589")),
    "neptune": (("30.06992276", "0.00859048", "1.77004347", "-55.12002969", "44.96476227", "131.78422574"),
                ("0.00026291", "0.00005105", "0.00035372", "218.45945325", "-0.32241464", "-0.00508664")),
    "pluto": (("39.48211675", "0.24882730", "17.14001206", "238.92903833", "224.06891629", "110.30393684"),
              ("-0.00031596", "0.00005170", "0.00004818", "145.20780515", "-0.04062942", "-0.01183482")),
}
# JPL table 2a (3000 BC - 3000 AD) and 2b (b, c, s, f) for the outer planets
JPL_T2A = {
    "mercury": (("0.38709843", "0.20563661", "7.00559432", "252.25166724", "77.45771895", "48.33961819"),
                ("0.00000000", "0.00002123", "-0.00590158", "149472.67486623", "0.15940013", "-0.12214182")),
    "venus": (("0.72332102", "0.00676399", "3.39777545", "181.97970850", "131.76755713", "76.67261496"),
              ("-0.00000026", "-0.00005107", "0.00043494", "58517.81560260", "0.05679648", "-0.27274174")),
    "earth": (("1.00000018", "0.01673163", "-0.00054346", "100.46691572", "102.93005885", "-5.11260389"),
              ("-0.00000003", "-0.00003661", "-0.01337178", "35999.37306329", "0.31795260", "-0.24123856")),
    "mars": (("1.52371243", "0.09336511", "1.85181869", "-4.56813164", "-23.91744784", "49.71320984"),
             ("0.00000097", "0.00009149", "-0.00724757", "19140.29934243", "0.45223625", "-0.26852431")),
    "jupiter": (("5.20248019", "0.04853590", "1.29861416", "34.33479152", "14.27495244", "100.29282654"),
                ("-0.00002864", "0.00018026", "-0.00322699", "3034.90371757", "0.18199196", "0.13024619")),
    "saturn": (("9.54149883", "0.05550825", "2.49424102", "50.07571329", "92.86136063", "113.63998702"),
               ("-0.00003065", "-0.00032044", "0.00451969", "1222.11494724", "0.54179478", "-0.25015002")),
    "uranus": (("19.18797948", "0.04685740", "0.77298127", "314.20276625", "172.43404441", "73.96250215"),
               ("-0.00020455", "-0.00001550", "-0.00180155", "428.49512595", "0.09266985", "0.05739699")),
    "neptune": (("30.06952752", "0.00895439", "1.77005520", "304.22289287", "46.68158724", "131.78635853"),
                ("0.00006447", "0.00000818", "0.00022400", "218.46515314", "0.01009938", "-0.00606302")),
    "pluto": (("39.48686035", "0.24885238", "17.14104260", "238.96535011", "224.09702598", "110.30167986"),
              ("0.00449751", "0.00006016", "0.00000501", "145.18042903", "-0.00968827", "-0.00809981")),
}
JPL_T2B = {   # b [deg/cy^2], c, s [deg], f [deg/cy]
    "jupiter": ("-0.00012452", "0.06064060", "-0.35635438", "38.35125000"),
    "saturn": ("0.00025899", "-0.13434469", "0.87320147", "38.35125000"),
    "uranus": ("0.00058331", "-0.97731848", "0.17689245", "7.67025000"),
    "neptune": ("-0.00041348", "0.68346318", "-0.10162547", "7.67025000"),
    "pluto": ("-0.01262724", "0", "0", "0"),
}
# Simon 1994 sect. 5.8 (mean ecliptic & equinox J2000) -- secular mean elements.
# lambda0 [deg], lambda1 [''/millennium], lambda2 [''/millennium^2]; varpi0, varpi1; Omega0, Omega1; i0, i1; e0, e1; a0
SIMON_J2000 = {
    "mercury": dict(a="0.3870983098", l0="252.25090552", l1="5381016286.88982", l2="-1.92789",
                    p0="77.45611904", p1="5719.11590", n0="48.33089304", n1="-4515.21727",
                    i0="7.00498625", i1="-214.25629", e0="0.2056317526", e1="0.0002040653"),
    "venus": dict(a="0.7233298200", l0="181.97980085", l1="2106641364.33548", l2="0.59381",
                  p0="131.56370300", p1="175.48640", n0="76.67992019", n1="-10008.48154",
                  i0="3.39466189", i1="-30.84437", e0="0.0067719164", e1="-0.0004776521"),
    "earth": dict(a="1.0000010178", l0="100.46645683", l1="1295977422.83429", l2="-2.04411",
                  p0="102.93734808", p1="11612.35290", n0="174.87317577", n1="-8679.27034",
                  i0="0", i1="469.97289", e0="0.0167086342", e1="-0.0004203654"),
    "mars": dict(a="1.5236793419", l0="355.43299958", l1="689050774.93988", l2="0.94264",
                 p0="336.06023395", p1="15980.45908", n0="49.55809321", n1="-10620.90088",
                 i0="1.84972648", i1="-293.31722", e0="0.0934006477", e1="0.0009048438"),
    "jupiter": dict(a="5.2026032092", l0="34.35151874", l1="109256603.77991", l2="-30.60378",
                    p0="14.33120687", p1="7758.75163", n0="100.46440702", n1="6362.03561",
                    i0="1.30326698", i1="-71.55890", e0="0.0484979255", e1="0.0016322542"),
    "saturn": dict(a="9.5549091915", l0="50.07744430", l1="43996098.55732", l2="75.61614",
                   p0="93.05723748", p1="20395.49439", n0="113.66550252", n1="-9240.19942",
                   i0="2.48887878", i1="91.85195", e0="0.0555481426", e1="-0.0034664062"),
    "uranus": dict(a="19.2184460618", l0="314.05500511", l1="15424811.93933", l2="-1.75083",
                   p0="173.00529106", p1="3215.56238", n0="74.00595701", n1="2669.15033",
                   i0="0.77319689", i1="-60.72723", e0="0.0463812221", e1="-0.0002729293"),
    "neptune": dict(a="30.1103868694", l0="304.34866548", l1="7865503.20744", l2="0.21103",
                    p0="48.12027554", p1="1050.71912", n0="131.78405702", n1="-221.94322",
                    i0="1.76995259", i1="8.12333", e0="0.0094557470", e1="0.0000603263"),
}
# Simon 1994 sect. 5.9 (mean ecliptic & equinox of date): first-order rates ''/millennium
SIMON_DATE = {
    "mercury": dict(l1="5381066598.20037", p1="56030.42645", n1="42700.01444"),
    "venus": dict(l1="2106691666.31989", p1="50477.47081", n1="32437.57636"),
    "earth": dict(l1="1296027711.03429", p1="61900.55290", n1=None),
    "mars": dict(l1="689101069.33069", p1="66274.84990", n1="27792.68736"),
    "jupiter": dict(l1="109306899.89453", p1="58054.86625", n1="36755.18747"),
    "saturn": dict(l1="44046398.47038", p1="70695.40745", n1="31575.16875"),
    "uranus": dict(l1="15475106.01961", p1="53509.64266", n1="18760.59902"),
    "neptune": dict(l1="7915799.13277", p1="51346.64455", n1="39679.34159"),
}
# Meeus table 31.A (equinox of date, IAU 1976 precession): L rate deg/cy
MEEUS_31A_LDOT = {"mercury": "149474.0722491", "venus": "58519.2130302", "earth": "36000.7698278",
                  "mars": "19141.6964471", "jupiter": "3036.3027748", "saturn": "1223.5110686",
                  "uranus": "429.8640561", "neptune": "219.8833092"}
# IERS 2010 eq. 5.44: mean longitudes, rad/cy (J2000 frame; Souchay 1999 from Simon 1994)
IERS_L_RAD = {"mercury": "2608.7903141574", "venus": "1021.3285546211", "earth": "628.3075849991",
              "mars": "334.0612426700", "jupiter": "52.9690962641", "saturn": "21.3299104960",
              "uranus": "7.4781598567", "neptune": "3.8133035638"}
# Meeus table 31.A (of date) constant terms and first-order rates (deg, deg/cy) -- independent
# transcription of the same VSOP87 mean elements, used to check the Simon 1994 transcription
MEEUS_31A_EL = {   # L0, e0, i0, Omega0, varpi0, varpi1, Omega1, e1
    "mercury": ("252.250906", "0.20563175", "7.004986", "48.330893", "77.456119", "1.5564776", "1.1861883", "0.000020407"),
    "venus": ("181.979801", "0.00677192", "3.394662", "76.67992", "131.563703", "1.4022288", "0.9011206", "-0.000047765"),
    "earth": ("100.466457", "0.01670863", "0", None, "102.937348", "1.7195366", None, "-0.000042037"),
    "mars": ("355.433", "0.09340065", "1.849726", "49.558093", "336.060234", "1.8410449", "0.7720959", "0.000090484"),
    "jupiter": ("34.351519", "0.04849793", "1.303267", "100.464407", "14.331207", "1.6126352", "1.0209774", "0.000163225"),
    "saturn": ("50.077444", "0.05554814", "2.488879", "113.665503", "93.057237", "1.9637613", "0.877088", "-0.000346641"),
    "uranus": ("314.055005", "0.04638122", "0.773197", "74.005957", "173.005291", "1.486379", "0.5211278", "-0.000027293"),
    "neptune": ("304.348665", "0.00945575", "1.769953", "131.784057", "48.120276", "1.4262957", "1.1022039", "0.000006033"),
}
# NASA NSSDC fact sheets: sidereal, tropical, synodic periods (days)
NSSDC = {
    "mercury": ("87.969", "87.968", "115.88"), "venus": ("224.701", "224.695", "583.92"),
    "earth": ("365.256", "365.242", None), "mars": ("686.980", "686.972", "779.94"),
    "jupiter": ("4332.589", "4330.595", "398.88"), "saturn": ("10755.699", "10746.940", "378.09"),
    "uranus": ("30685.400", "30588.740", "369.66"), "neptune": ("60189.018", "59799.900", "367.49"),
    "pluto": ("90560", None, "366.73"),
}
# NASA NSSDC "Mean Orbital Elements (J2000)" (older Standish table): a, e, i, Omega, varpi, L
NSSDC_EL = {
    "mercury": ("0.38709893", "0.20563069", "7.00487", "48.33167", "77.45645", "252.25084"),
    "venus": ("0.72333199", "0.00677323", "3.39471", "76.68069", "131.53298", "181.97973"),
    "earth": ("1.00000011", "0.01671022", "0.00005", "-11.26064", "102.94719", "100.46435"),
    "mars": ("1.52366231", "0.09341233", "1.85061", "49.57854", "336.04084", "355.45332"),
    "jupiter": ("5.20336301", "0.04839266", "1.30530", "100.55615", "14.75385", "34.40438"),
    "saturn": ("9.53707032", "0.05415060", "2.48446", "113.71504", "92.43194", "49.94432"),
    "uranus": ("19.19126393", "0.04716771", "0.76986", "74.22988", "170.96424", "313.23218"),
    "neptune": ("30.06896348", "0.00858587", "1.76917", "131.72169", "44.97135", "304.88003"),
    "pluto": ("39.48168677", "0.24880766", "17.14175", "110.30347", "224.06676", "238.92881"),
}
# Schlyter: great inequalities (deg) -- quoted as an independent amplitude check
GREAT_INEQ_SCHLYTER = {"jupiter": 0.332, "saturn": 0.812}

pa_deg_cy = PA_IAU2006 / 3600
earth_sid_rate_jpl = F(JPL_T1["earth"][1][3])


def fit_rate_2000_2100(name):
    """Least-squares linear rate (deg/cy) and max residual of JPL table 2a(+2b) mean longitude over 2000-2100."""
    el, rt = JPL_T2A[name]
    T = np.linspace(0.0, 1.0, 2001)
    L = float(el[3]) + float(rt[3]) * T
    if name in JPL_T2B:
        b, c, s, f = (float(x) for x in JPL_T2B[name])
        L = L + b * T * T + c * np.cos(f * T * DEG) + s * np.sin(f * T * DEG)
    A = np.vstack([T, np.ones_like(T)]).T
    (slope, icpt), *_ = np.linalg.lstsq(A, L, rcond=None)
    resid = L - (slope * T + icpt)
    return float(slope), float(np.max(np.abs(resid)))


HZ_PATH = V2 / "research" / "sources" / "horizons" / "horizons_rates_2000_2100.json"
HZ = json.loads(HZ_PATH.read_text()) if HZ_PATH.exists() else None


def recommended_rate(name):
    """Design rate (deg/cy, J2000 frame) for the 2000-2100 window: DE441 fit if available."""
    if HZ and name in HZ["bodies"]:
        b = HZ["bodies"][name]
        if "barycentric" in b:
            return (F(repr(b["barycentric"]["L_rate_deg_per_cy"])),
                    "JPL_HORIZONS (DE441, elements barycentriques, ajustement 2000-2100)",
                    b["L_rate_uncertainty_deg_per_cy"])
        return F(repr(b["L_rate_deg_per_cy"])), "JPL_HORIZONS (DE441, elements heliocentriques, ajustement 2000-2100)", 0.005
    return F(JPL_T1[name][1][3]), "JPL_APPROX table 1", None


earth_rec_rate = recommended_rate("earth")[0]
check("year.tropical_laskar_vs_de441", "Annee tropique : Laskar vs (taux EMB DE441 2000-2100 + p_A)",
      TY_LASKAR[0], "LASKAR1986_TY", JC * 360 / (earth_rec_rate + PA_IAU2006 / 3600), "JPL_HORIZONS+CAPITAINE2003", 2e-5, "jours",
      "Ajustement d'elements osculateurs sur 100 ans : ecart attendu ~1e-6 j.")
planets_out = {}
for name in PLANETS + ["pluto"]:
    el1, rt1 = JPL_T1[name]
    ldot_t1 = F(rt1[3])                        # deg/cy, J2000 frame, 1800-2050 fit
    ldot_sid, rec_src, rec_unc = recommended_rate(name)
    ldot_trop = ldot_sid + pa_deg_cy           # deg/cy, equinox of date (approx.: + p_A)
    e = float(el1[1])
    entry = {
        "name_fr": FR[name],
        "optional_flag": name == "pluto",
        "jpl_table1_1800_2050": {
            "source": "JPL_APPROX" if name != "pluto" else "JPL_APPROX_2019",
            "frame": "ecliptique et equinoxe moyens J2000",
            "elements": dict(zip(["a_au", "e", "i_deg", "L_deg", "varpi_deg", "Omega_deg"], [float(x) for x in el1])),
            "rates_per_century": dict(zip(["a_au", "e", "i_deg", "L_deg", "varpi_deg", "Omega_deg"], [float(x) for x in rt1])),
            "exact_strings": {"elements": list(el1), "rates": list(rt1)},
        },
        "jpl_table2a_3000BC_3000AD": {
            "source": "JPL_APPROX" if name != "pluto" else "JPL_APPROX_2019",
            "elements": dict(zip(["a_au", "e", "i_deg", "L_deg", "varpi_deg", "Omega_deg"], [float(x) for x in JPL_T2A[name][0]])),
            "rates_per_century": dict(zip(["a_au", "e", "i_deg", "L_deg", "varpi_deg", "Omega_deg"], [float(x) for x in JPL_T2A[name][1]])),
            "table2b_M_terms": (dict(zip(["b_deg_per_cy2", "c_deg", "s_deg", "f_deg_per_cy"], [float(x) for x in JPL_T2B[name]]))
                                if name in JPL_T2B else None),
        },
    }
    # mean motions
    turns_per_day_sid = ldot_sid / 360 / JC
    turns_per_day_trop = ldot_trop / 360 / JC
    mm = {
        "basis": f"{rec_src} ; tropique = sideral + p_A (IAU 2006)",
        "rate_uncertainty_deg_per_century": rec_unc,
        "deg_per_century_sidereal": rnd(ldot_sid, 14),
        "deg_per_century_tropical": rnd(ldot_trop, 14),
        "deg_per_day_sidereal": rnd(ldot_sid / JC, 14),
        "turns_per_day_sidereal": rnd(turns_per_day_sid, 14),
        "turns_per_day_tropical": rnd(turns_per_day_trop, 14),
        "turns_per_tropical_year_sidereal": rnd(turns_per_day_sid * TROPICAL_YEAR, 14),
        "turns_per_tropical_year_tropical": rnd(turns_per_day_trop * TROPICAL_YEAR, 14),
        "sidereal_period_days": rnd(JC * 360 / ldot_sid, 12),
        "tropical_period_days": rnd(JC * 360 / ldot_trop, 12),
        "sidereal_period_tropical_years": rnd(JC * 360 / ldot_sid / TROPICAL_YEAR, 12),
        # gear-ratio precision needed so that the mean-longitude error stays < 1 deg per century
        "relative_ratio_precision_for_1deg_per_century": rnd(1 / abs(ldot_sid), 4) if ldot_sid else None,
    }
    if name != "earth":
        syn = 1 / abs(1 / (JC * 360 / ldot_sid) - 1 / (JC * 360 / earth_rec_rate))
        mm["synodic_period_days"] = rnd(syn, 10)
    entry["mean_motion"] = mm
    entry["mean_motion_jpl_table1"] = {
        "deg_per_century_sidereal": rnd(ldot_t1, 14),
        "turns_per_day_sidereal": rnd(ldot_t1 / 360 / JC, 14),
        "sidereal_period_days": rnd(JC * 360 / ldot_t1, 12),
    }
    if HZ and name in HZ["bodies"]:
        b = HZ["bodies"][name]
        entry["horizons_DE441_fit_2000_2100"] = {
            "source": "JPL_HORIZONS",
            "heliocentric": {"L_rate_deg_per_cy": b["L_rate_deg_per_cy"], "L_at_J2000_deg": b["L_at_J2000_deg"],
                             "L_fit_rms_deg": b["L_fit_rms_deg"], "varpi_rate_deg_per_cy": b["varpi_rate_deg_per_cy"],
                             "Omega_rate_deg_per_cy": b["Omega_rate_deg_per_cy"], "e_mean": b["e_mean"],
                             "i_mean_deg": b["i_mean_deg"], "a_mean_au": b["a_mean_au"]},
            "barycentric": b.get("barycentric"),
        }
        check(f"{name}.L_rate_t1_vs_de441", f"{FR[name]} : taux de L (deg/siecle), JPL T1 (1800-2050) vs DE441 ajuste 2000-2100",
              ldot_t1, "JPL_APPROX", ldot_sid, "JPL_HORIZONS", 0.1, "deg/siecle",
              "Tolerance 0,1 deg/siecle = 1/10 de l'objectif de la machine.")
    # Secular (Simon 1994) vs local (JPL)
    if name in SIMON_J2000:
        s = SIMON_J2000[name]
        l1_cy = F(s["l1"]) / 10 / 3600            # deg/cy
        entry["simon1994_secular_J2000"] = {
            "source": "SIMON1994",
            "a_au": float(s["a"]), "e": float(s["e0"]), "e_rate_per_cy": float(F(s["e1"]) / 10),
            "i_deg": float(s["i0"]), "i_rate_arcsec_per_cy": float(F(s["i1"]) / 10),
            "lambda_deg": float(s["l0"]), "lambda_rate_deg_per_cy": rnd(l1_cy, 14),
            "lambda_t2_arcsec_per_millennium2": float(s["l2"]),
            "varpi_deg": float(s["p0"]), "varpi_rate_deg_per_cy": rnd(F(s["p1"]) / 10 / 3600, 10),
            "Omega_deg": float(s["n0"]), "Omega_rate_deg_per_cy": rnd(F(s["n1"]) / 10 / 3600, 10),
            "exact_strings_arcsec_per_millennium": {"lambda": s["l1"], "varpi": s["p1"], "Omega": s["n1"]},
            "sidereal_period_days": rnd(period_days(F(s["l1"]) / 10), 12),
        }
        sd = SIMON_DATE[name]
        entry["simon1994_of_date"] = {
            "source": "SIMON1994",
            "lambda_rate_deg_per_cy": rnd(F(sd["l1"]) / 36000, 14),
            "varpi_rate_deg_per_cy": rnd(F(sd["p1"]) / 36000, 10),
            "Omega_rate_deg_per_cy": rnd(F(sd["n1"]) / 36000, 10) if sd["n1"] else None,
            "tropical_period_days": rnd(period_days(F(sd["l1"]) / 10), 12),
        }
        # cross-checks
        if HZ and name in HZ["bodies"]:
            check(f"{name}.L_rate_de441_vs_simon", f"{FR[name]} : taux de L (deg/siecle), DE441 2000-2100 vs Simon (seculaire)",
                  ldot_sid, "JPL_HORIZONS", l1_cy, "SIMON1994", 0.1, "deg/siecle",
                  "Sur 2000-2100 la grande inegalite Jupiter-Saturne accelere Saturne et ralentit Jupiter par rapport a leur mouvement seculaire." if name in ("jupiter", "saturn") else "",
                  explained=name in ("jupiter", "saturn"))
        check(f"{name}.L_rate_jpl_vs_simon", f"{FR[name]} : taux de L (deg/siecle), JPL T1 (local 1800-2050) vs Simon (seculaire)",
              ldot_t1, "JPL_APPROX", l1_cy, "SIMON1994", 0.01, "deg/siecle",
              "Ecart = pente locale des grandes inegalites (Jupiter-Saturne ~900 ans, Uranus-Neptune ~4700 ans)." if name in ("jupiter", "saturn", "uranus", "neptune") else "",
              explained=name in ("jupiter", "saturn", "uranus", "neptune"))
        check(f"{name}.L_rate_simon_vs_iers", f"{FR[name]} : taux de L Simon 5.8 vs IERS 2010 eq. 5.44",
              l1_cy, "SIMON1994", F(IERS_L_RAD[name]) * 180 / F(math.pi), "IERS2010", 2e-6, "deg/siecle")
        meeus = F(MEEUS_31A_LDOT[name])
        d_meeus = fl(F(sd["l1"]) / 36000 - meeus)
        check(f"{name}.L_rate_date_simon_vs_meeus", f"{FR[name]} : taux de L de date, Simon 5.9 vs Meeus 31.A",
              F(sd["l1"]) / 36000, "SIMON1994", meeus, "MEEUS1998", 1e-4, "deg/siecle",
              "Meeus 31.A ajoute ici la difference de constante de precession IAU 1976 - Williams 1991 (+0,277''/siecle = +7,7e-5 deg/siecle) ; pour Jupiter-Neptune il reprend Simon a l'identique." if abs(d_meeus) > 5e-5 else "",
              explained=True)
        # Simon 'of date' rate vs sidereal + p_A (difference = ecliptic motion effect on lambda)
        check(f"{name}.L_rate_date_minus_J2000", f"{FR[name]} : (taux de date - taux J2000) Simon vs constante de precession de Simon",
              (F(sd["l1"]) - F(s["l1"])) / 10, "SIMON1994", PA_SIMON1994, "SIMON1994", 2.5, "''/siecle",
              "Passer du repere J2000 au repere de date n'ajoute pas exactement p_A a lambda (mouvement de l'ecliptique, inclinaison et noeud) : jusqu'a 2,3''/siecle (Mercure). Negligeable (<0,001 deg/siecle).")
        # transcription checks: Simon 1994 (read from the scanned paper) vs Meeus 31.A
        mL0, me0, mi0, mO0, mp0, mp1, mO1, me1 = MEEUS_31A_EL[name]

        def half_ulp(x):
            return 0.5 * 10 ** -len(x.split(".")[1]) + 1e-9 if "." in x else 0.5

        for lab_, sv, mv in (("L0", s["l0"], mL0), ("e0", s["e0"], me0), ("i0", s["i0"], mi0),
                             ("Omega0", s["n0"], mO0), ("varpi0", s["p0"], mp0)):
            if mv is None or (lab_ == "i0" and name == "earth"):
                continue
            check(f"{name}.transcription_{lab_}", f"{FR[name]} : {lab_} a J2000, Simon 1994 (transcrit) vs Meeus 31.A",
                  F(sv), "SIMON1994", F(mv), "MEEUS1998", rnd(half_ulp(mv), 3), "deg" if lab_ != "e0" else "",
                  "Tolerance = demi-unite du dernier chiffre de Meeus.")
        check(f"{name}.transcription_e1", f"{FR[name]} : de/dT, Simon 1994 (transcrit) vs Meeus 31.A",
              F(s["e1"]) / 10, "SIMON1994", F(me1), "MEEUS1998", rnd(half_ulp(me1), 3), "/siecle")
        check(f"{name}.transcription_varpi1", f"{FR[name]} : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A",
              F(sd["p1"]) / 36000, "SIMON1994", F(mp1), "MEEUS1998", 1e-4, "deg/siecle",
              "Ecart possible de 7,7e-5 deg/siecle (constante de precession IAU 1976 chez Meeus).")
        if mO1 is not None and sd["n1"]:
            check(f"{name}.transcription_Omega1", f"{FR[name]} : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A",
                  F(sd["n1"]) / 36000, "SIMON1994", F(mO1), "MEEUS1998", 1e-4, "deg/siecle",
                  "Ecart possible de 7,7e-5 deg/siecle (constante de precession IAU 1976 chez Meeus).")
        c2000, res2000 = fit_rate_2000_2100(name)
        entry["rate_fit_2000_2100_from_jpl_table2"] = {
            "deg_per_century_sidereal": rnd(c2000, 12),
            "max_residual_from_linear_deg": rnd(res2000, 4),
            "note": "Pente moyenne 2000-2100 de L(T) des tables JPL 2a+2b (inclut le terme periodique de M) ; residu = ecart maximal a une droite (ce qu'un engrenage a rapport constant ne peut pas suivre).",
        }
        cand = [fl(ldot_sid), fl(ldot_t1), c2000, fl(l1_cy)]
        entry["rate_candidates_deg_per_century_sidereal"] = {
            "recommended_de441_fit_2000_2100": rnd(ldot_sid, 12),
            "jpl_table1_1800_2050": rnd(ldot_t1, 12),
            "jpl_table2_fit_2000_2100": rnd(c2000, 12),
            "simon1994_secular": rnd(l1_cy, 12),
            "spread_deg_per_century": rnd(max(cand) - min(cand), 4),
            "t1_minus_recommended": rnd(fl(ldot_t1) - fl(ldot_sid), 4),
            "secular_minus_recommended": rnd(fl(l1_cy) - fl(ldot_sid), 4),
        }
    # NASA periods
    sid, trop, synp = NSSDC[name]
    entry["nssdc"] = {"source": "NSSDC", "sidereal_period_days": float(sid),
                      "tropical_period_days": float(trop) if trop else None,
                      "synodic_period_days": float(synp) if synp else None,
                      "mean_elements_J2000": dict(zip(["a_au", "e", "i_deg", "Omega_deg", "varpi_deg", "L_deg"], [float(x) for x in NSSDC_EL[name]]))}
    psid = JC * 360 / ldot_t1
    rel = 2e-5 if name not in ("saturn", "uranus", "neptune", "pluto") else 1e-3
    sid_note = {
        "saturn": "NSSDC (mise a jour 2025) : 10755,70 j, proche du taux local JPL (10755,93 j) ; l'ancienne valeur NSSDC 10759,22 j (utilisee dans la v1) est la periode seculaire (Simon : 10759,23 j).",
        "jupiter": "NSSDC donne la periode seculaire (Simon 1994 : 4332,589 j), pas le taux local 1800-2050.",
    }.get(name, "")
    check(f"{name}.sidereal_period_jpl_vs_nssdc", f"{FR[name]} : periode siderale (j), JPL T1 vs NSSDC",
          psid, "JPL_APPROX", F(sid), "NSSDC", fl(psid) * rel, "jours", sid_note, explained=bool(sid_note))
    if name in SIMON_J2000 and name in ("jupiter", "saturn", "uranus", "neptune"):
        p_sec = period_days(F(SIMON_J2000[name]["l1"]) / 10)
        check(f"{name}.sidereal_period_nssdc_vs_simon", f"{FR[name]} : periode siderale (j), NSSDC vs Simon 1994 seculaire",
              F(sid), "NSSDC", p_sec, "SIMON1994", 0.01, "jours",
              "Les periodes NSSDC des planetes geantes ne suivent pas une regle unique (Jupiter = seculaire ; Saturne, Uranus, Neptune = ni seculaire ni exactement le taux JPL T1) : origine non documentee. Pour la machine, utiliser les taux JPL explicites, pas ces periodes.",
              explained=True)
    if synp:
        check(f"{name}.synodic_period_vs_nssdc", f"{FR[name]} : periode synodique (j), calculee (DE441 2000-2100) vs NSSDC",
              mm["synodic_period_days"], "JPL_HORIZONS", F(synp), "NSSDC", 0.02, "jours")
    if trop:
        trop_note = {
            "mars": "Definition differente : la 'periode tropique' NSSDC de Mars (686,972 j) est l'annee tropique martienne, rapportee a l'equinoxe de Mars (precession propre ~170 000 ans) ; rapportee a l'equinoxe terrestre elle vaut 686,930 j.",
            "jupiter": "NSSDC donne pour Jupiter la periode seculaire (Simon 1994 : 4332,589 j) et non le taux local 1800-2050 (4332,817 j) ; voir le controle jupiter.sidereal_period_nssdc_vs_simon.",
        }.get(name, "")
        p_trop_t1 = JC * 360 / (ldot_t1 + pa_deg_cy)
        check(f"{name}.tropical_period_jpl_vs_nssdc", f"{FR[name]} : periode tropique (j), JPL T1 + p_A vs NSSDC",
              p_trop_t1, "JPL_APPROX+CAPITAINE2003", F(trop), "NSSDC", fl(p_trop_t1) * rel, "jours",
              trop_note, explained=bool(trop_note))
    # J2000 elements: JPL T1 vs NSSDC (older Standish values)
    a_n, e_n, i_n, O_n, w_n, L_n = (float(x) for x in NSSDC_EL[name])
    check(f"{name}.e_jpl_vs_nssdc", f"{FR[name]} : excentricite J2000, JPL T1 vs NSSDC",
          float(el1[1]), "JPL_APPROX", e_n, "NSSDC", 6e-4, "")
    L_j = float(el1[3]) % 360
    dL = ((L_j - L_n + 180) % 360) - 180
    check(f"{name}.L_jpl_vs_nssdc", f"{FR[name]} : longitude moyenne J2000 (deg), JPL T1 vs NSSDC",
          L_n + dL, "JPL_APPROX", L_n, "NSSDC", 0.7, "deg",
          "Les deux sont des ajustements (pas des elements moyens au sens strict) ; les grandes inegalites expliquent les ecarts pour les planetes geantes." if name in ("jupiter", "saturn", "uranus", "neptune") else "",
          explained=name in ("jupiter", "saturn", "uranus", "neptune"))
    # Equation of centre and mechanisable approximations
    entry["equation_of_centre"] = eoc_models(e)
    planets_out[name] = entry

# Earth / Sun equation of centre: Meeus solar.go coefficients vs Kepler
SUN_EOC_MEEUS = (1.914602, 0.019993, 0.000289)
check("sun.eoc_c1", "Soleil : 1er terme de l'equation du centre (deg), Meeus vs serie de Kepler (e Simon)",
      SUN_EOC_MEEUS[0], "MEEUS1998", (2 * E_EARTH - E_EARTH ** 3 / 4) / DEG, "SIMON1994", 2e-4, "deg")
check("sun.eoc_c2", "Soleil : 2e terme de l'equation du centre (deg), Meeus vs 5/4 e^2",
      SUN_EOC_MEEUS[1], "MEEUS1998", 1.25 * E_EARTH ** 2 / DEG, "SIMON1994", 1e-5, "deg")
# Great inequality amplitude: JPL 2b vs Schlyter
for p_ in ("jupiter", "saturn"):
    b, c, s, f = (float(x) for x in JPL_T2B[p_])
    check(f"{p_}.great_inequality_amp", f"{FR[p_]} : amplitude de la grande inegalite (deg), JPL 2b vs Schlyter",
          math.hypot(c, s), "JPL_APPROX", GREAT_INEQ_SCHLYTER[p_], "SCHLYTER", 0.08, "deg",
          "JPL 2b est un ajustement de M (perturbation globale) sur 6000 ans ; Schlyter donne le seul terme 2Mj-5Ms. Meme ordre de grandeur.",
          explained=True)
great_ineq = {}
for p_ in ("jupiter", "saturn", "uranus", "neptune"):
    b, c, s, f = (float(x) for x in JPL_T2B[p_])
    great_ineq[p_] = {"amplitude_deg": rnd(math.hypot(c, s), 4), "period_years": rnd(36000 / f, 5),
                      "max_rate_deg_per_century": rnd(math.hypot(c, s) * f * DEG, 4)}

# ----------------------------------------------------------------------------
# 3. Moon
# ----------------------------------------------------------------------------
# Meeus ch. 47 (ELP 2000-82 based), mean equinox of date, T in Julian centuries TT
MOON_MEEUS = {
    "L_prime": ["218.3164477", "481267.88123421", "-0.0015786", "1/538841", "-1/65194000"],
    "D": ["297.8501921", "445267.1114034", "-0.0018819", "1/545868", "-1/113065000"],
    "M_sun": ["357.5291092", "35999.0502909", "-0.0001536", "1/24490000", "0"],
    "M_prime": ["134.9633964", "477198.8675055", "0.0087414", "1/69699", "-1/14712000"],
    "F": ["93.2720950", "483202.0175233", "-0.0036539", "-1/3526000", "1/863310000"],
    "Omega": ["125.0445479", "-1934.1362891", "0.0020754", "1/467441", "-1/60616000"],
    "perigee": ["83.3532465", "4069.0137287", "-0.01032", "-1/80053", "1/18999000"],
}
# IERS 2010 eq. 5.43 = Simon 1994 3.5(b) (''/cy) and Simon 3.4 (b.1)/(b.3)
DELAUNAY_IERS = {
    "l": ("134.96340251", "1717915923.2178", "31.8792"),
    "l_prime": ("357.52910918", "129596581.0481", "-0.5532"),
    "F": ("93.27209062", "1739527262.8478", "-12.7512"),
    "D": ("297.85019547", "1602961601.2090", "-6.3706"),
    "Omega": ("125.04455501", "-6962890.5431", "7.4722"),
}
MOON_SIMON = {   # Simon 1994 3.4 (b.1) J2000 and (b.3) of date with P = 5028.82''/cy ; ''/cy
    "lambda_J2000": ("218.31664563", "1732559343.48470"),
    "lambda_date": ("218.31664563", "1732564372.30470"),
    "varpi_J2000": ("83.35324312", "14643420.2669"),
    "varpi_date": ("83.35324312", "14648449.0869"),
    "Omega_J2000": ("125.04455501", "-6967919.3631"),
    "Omega_date": ("125.04455501", "-6962890.5431"),
    "i_mean_deg": "5.15668983",
    "a_km": "383397.7725", "e": "0.055545526",
}
MONTHS_CHAPRONT2002 = {   # days, + coefficient of T (days per century)
    "draconic": ("27.212220815", "4.14e-7"), "tropical": ("27.321582252", "1.82e-7"),
    "sidereal": ("27.321661554", "2.17e-7"), "anomalistic": ("27.554549886", "-1.007e-6"),
    "synodic": ("29.530588861", "2.52e-7"),
}

dl = {k: F(v[1]) for k, v in DELAUNAY_IERS.items()}
lam_sid = F(MOON_SIMON["lambda_J2000"][1])
lam_trop = F(MOON_SIMON["lambda_date"][1])
months = {
    "sidereal": period_days(lam_sid),
    "tropical": period_days(lam_trop),
    "synodic": period_days(dl["D"]),
    "anomalistic": period_days(dl["l"]),
    "draconic": period_days(dl["F"]),
}
for k, v in months.items():
    check(f"moon.month_{k}", f"Mois {k} (j) : Simon 1994 / IERS vs Chapront et al. 2002",
          v, "SIMON1994", F(MONTHS_CHAPRONT2002[k][0]), "CHAPRONT2002", 2e-8, "jours",
          "Simon 1994 (ajustement DE200/LE200) vs Chapront 2002 (tirs laser-Lune) : ecart <1e-8 j, soit <1 ms par mois.")
# Meeus vs IERS rates
moon_meeus_rates = {k: F(v[1]) for k, v in MOON_MEEUS.items()}
pairs = [("D", "D"), ("M_prime", "l"), ("F", "F"), ("Omega", "Omega"), ("M_sun", "l_prime")]
for mk, ik in pairs:
    check(f"moon.rate_{mk}", f"Lune : taux de {mk} (deg/siecle), Meeus ch. 47 vs IERS 2010 (Simon 1994)",
          moon_meeus_rates[mk], "MEEUS1998", dl[ik] / 3600, "IERS2010", 2e-4, "deg/siecle",
          "Meeus 47 provient d'ELP 2000-82 / Chapront-Touze & Chapront 1991 ; ecarts de quelques 1e-5 deg/siecle.")
check("moon.rate_Lprime", "Lune : taux de L' (deg/siecle, de date), Meeus vs Simon (b.3)",
      moon_meeus_rates["L_prime"], "MEEUS1998", lam_trop / 3600, "SIMON1994", 2e-4, "deg/siecle")
check("moon.rate_perigee", "Lune : taux du perigee (deg/siecle, de date), Meeus vs Simon (b.3)",
      moon_meeus_rates["perigee"], "MEEUS1998", F(MOON_SIMON["varpi_date"][1]) / 3600, "SIMON1994", 1e-3, "deg/siecle")
check("moon.synodic_meeus49", "Mois synodique de Meeus (49.1) vs Chapront 2002",
      F("29.530588861"), "MEEUS1998", F(MONTHS_CHAPRONT2002["synodic"][0]), "CHAPRONT2002", 1e-9, "jours")
check("moon.sidereal_nssdc", "Mois sideral : Simon vs NSSDC 27,3217",
      months["sidereal"], "SIMON1994", F("27.3217"), "NSSDC_MOON", 6e-5, "jours")

node_trop = period_days(F(MOON_SIMON["Omega_date"][1]))
node_sid = period_days(F(MOON_SIMON["Omega_J2000"][1]))
apse_trop = period_days(F(MOON_SIMON["varpi_date"][1]))
apse_sid = period_days(F(MOON_SIMON["varpi_J2000"][1]))
check("moon.node_trop_iers", "Periode des noeuds (tropique, j) : Simon vs IERS table 5.1a (6798,3837)",
      node_trop, "SIMON1994", F("6798.3837"), "IERS2010", 1e-3, "jours")
check("moon.node_sid_nasa", "Periode des noeuds (siderale, j) : Simon vs NASA (6793,48)",
      node_sid, "SIMON1994", F("6793.48"), "NASA_ECL", 0.01, "jours")
check("moon.apse_trop_iers", "Periode du perigee (tropique, j) : Simon vs IERS table 5.1a (3231,4956)",
      apse_trop, "SIMON1994", F("3231.4956"), "IERS2010", 1e-3, "jours")
check("moon.apse_nasa", "Periode du perigee (j) : Simon (siderale) vs NASA (3231,6 j, dite 'par rapport aux etoiles')",
      apse_sid, "SIMON1994", F("3231.6"), "NASA_ECL", 0.1, "jours",
      "La valeur NASA (0,11140 deg/j) est en fait le taux par rapport a l'equinoxe (tropique : 3231,50 j) ; la periode siderale est 3232,60 j. Incoherence de la page NASA.",
      explained=True)
eclipse_year = period_days(dl["F"] - dl["D"])
check("moon.eclipse_year", "Annee draconitique (j) : (F - D) IERS vs Wikipedia 'Year' 346,620075883",
      eclipse_year, "IERS2010", F("346.620075883"), "WIKI_YEAR", 5e-6, "jours")

# periodic terms (longitude, degrees). key: (D, M, M', F)
MOON_TERMS_LON = [
    # name, (D, M, Mp, F), Meeus 47.A (1e-6 deg), Brown via Wikipedia (''), AA low-prec (deg), Schlyter (deg)
    ("equation_du_centre", (0, 0, 1, 0), 6288774, 22639, 6.29, None),
    ("evection", (2, 0, -1, 0), 1274027, 4586, 1.27, 1.274),
    ("variation", (2, 0, 0, 0), 658314, 2370, 0.66, 0.658),
    ("equation_du_centre_2e_harmonique", (0, 0, 2, 0), 213618, 769, 0.21, None),
    ("equation_annuelle", (0, 1, 0, 0), -185116, -668, -0.19, -0.186),
    ("reduction_a_l_ecliptique", (0, 0, 0, 2), -114332, -412, -0.11, None),
    ("terme_2D_moins_2Mp", (2, 0, -2, 0), 58793, None, None, 0.059),
    ("terme_2D_moins_M_moins_Mp", (2, -1, -1, 0), 57066, None, None, 0.057),
    ("terme_2D_plus_Mp", (2, 0, 1, 0), 53322, None, None, 0.053),
    ("terme_2D_moins_M", (2, -1, 0, 0), 45758, None, None, 0.046),
    ("terme_M_moins_Mp", (0, 1, -1, 0), -40923, None, None, -0.041),
    ("inegalite_parallactique", (1, 0, 0, 0), -34720, -125, None, -0.035),
    ("terme_M_plus_Mp", (0, 1, 1, 0), -30383, None, None, -0.031),
]
MOON_TERMS_LAT = [
    # name, (D, M, Mp, F), Meeus 47.B (1e-6 deg), AA (deg), Schlyter (deg; sign normalised to Meeus argument)
    ("terme_principal_sinF", (0, 0, 0, 1), 5128122, 5.13, None),
    ("Mp_plus_F", (0, 0, 1, 1), 280602, 0.28, None),
    ("Mp_moins_F", (0, 0, 1, -1), 277693, 0.28, None),
    ("evection_en_latitude_2D_moins_F", (2, 0, 0, -1), 173237, 0.17, 0.173),
    ("2D_moins_Mp_plus_F", (2, 0, -1, 1), 55413, None, 0.055),
    ("2D_moins_Mp_moins_F", (2, 0, -1, -1), 46271, None, 0.046),
    ("2D_plus_F", (2, 0, 0, 1), 32573, None, 0.033),
    ("2Mp_plus_F", (0, 0, 2, 1), 17198, None, 0.017),
]
# full Meeus 47.A longitude table (D, M, M', F, sigma_l 1e-6 deg) for the error-budget reference
MEEUS_47A = [
    (0, 0, 1, 0, 6288774), (2, 0, -1, 0, 1274027), (2, 0, 0, 0, 658314), (0, 0, 2, 0, 213618),
    (0, 1, 0, 0, -185116), (0, 0, 0, 2, -114332), (2, 0, -2, 0, 58793), (2, -1, -1, 0, 57066),
    (2, 0, 1, 0, 53322), (2, -1, 0, 0, 45758), (0, 1, -1, 0, -40923), (1, 0, 0, 0, -34720),
    (0, 1, 1, 0, -30383), (2, 0, 0, -2, 15327), (0, 0, 1, 2, -12528), (0, 0, 1, -2, 10980),
    (4, 0, -1, 0, 10675), (0, 0, 3, 0, 10034), (4, 0, -2, 0, 8548), (2, 1, -1, 0, -7888),
    (2, 1, 0, 0, -6766), (1, 0, -1, 0, -5163), (1, 1, 0, 0, 4987), (2, -1, 1, 0, 4036),
    (2, 0, 2, 0, 3994), (4, 0, 0, 0, 3861), (2, 0, -3, 0, 3665), (0, 1, -2, 0, -2689),
    (2, 0, -1, 2, -2602), (2, -1, -2, 0, 2390), (1, 0, 1, 0, -2348), (2, -2, 0, 0, 2236),
    (0, 1, 2, 0, -2120), (0, 2, 0, 0, -2069), (2, -2, -1, 0, 2048), (2, 0, 1, -2, -1773),
    (2, 0, 0, 2, -1595), (4, -1, -1, 0, 1215), (0, 0, 2, 2, -1110), (3, 0, -1, 0, -892),
    (2, 1, 1, 0, -810), (4, -1, -2, 0, 759), (0, 2, -1, 0, -713), (2, 2, -1, 0, -700),
    (2, 1, -2, 0, 691), (2, -1, 0, -2, 596), (4, 0, 1, 0, 549), (0, 0, 4, 0, 537),
    (4, -1, 0, 0, 520), (1, 0, -2, 0, -487), (2, 1, 0, -2, -399), (0, 0, 2, -2, -381),
    (1, 1, 1, 0, 351), (3, 0, -2, 0, -340), (4, 0, -3, 0, 330), (2, -1, 2, 0, 327),
    (0, 2, 1, 0, -323), (1, 1, -1, 0, 299), (2, 0, 3, 0, 294),
]
MEEUS_47B = [
    (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693), (2, 0, 0, -1, 173237),
    (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271), (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198),
    (2, 0, 1, -1, 9266), (0, 0, 2, -1, 8822), (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324),
    (2, 0, 1, 1, 4200), (2, 1, 0, -1, -3359), (2, -1, -1, 1, 2463), (2, -1, 0, 1, 2211),
    (2, -1, -1, -1, 2065), (0, 1, -1, -1, -1870), (4, 0, -1, -1, 1828), (0, 1, 0, 1, -1794),
    (0, 0, 0, 3, -1749), (0, 1, -1, 1, -1565), (1, 0, 0, 1, -1491), (0, 1, 1, 1, -1475),
    (0, 1, 1, -1, -1410), (0, 1, 0, -1, -1344), (1, 0, 0, -1, -1335), (0, 0, 3, 1, 1107),
    (4, 0, 0, -1, 1021), (4, 0, -1, 1, 833),
]
for name, arg, me, br, aa, sc in MOON_TERMS_LON:
    if br is not None:
        check(f"moon.lon.{name}.brown", f"Lune, longitude, {name} (deg) : Meeus 47.A vs Brown (Wikipedia)",
              me * 1e-6, "MEEUS1998", br / 3600, "WIKI_LUNAR_THEORY", 6e-4, "deg",
              "Equation annuelle : Meeus la multiplie en plus par E = 1 - 0,002516 T." if name == "equation_annuelle" else "")
    if aa is not None:
        check(f"moon.lon.{name}.aa", f"Lune, longitude, {name} (deg) : Meeus 47.A vs Almanach (2 decimales)",
              me * 1e-6, "MEEUS1998", aa, "AA_LOWPREC", 0.006, "deg")
    if sc is not None and br is None:
        check(f"moon.lon.{name}.schlyter", f"Lune, longitude, {name} (deg) : Meeus 47.A vs Schlyter (3 decimales)",
              me * 1e-6, "MEEUS1998", sc, "SCHLYTER", 6e-4, "deg",
              "Schlyter n'est pas un simple arrondi de Meeus (autre theorie, elements osculateurs) : ecart de 0,0006 deg, sans consequence.",
              explained=True)
for name, arg, me, aa, sc in MOON_TERMS_LAT:
    if aa is not None:
        check(f"moon.lat.{name}.aa", f"Lune, latitude, {name} (deg) : Meeus 47.B vs Almanach",
              me * 1e-6, "MEEUS1998", aa, "AA_LOWPREC", 0.006, "deg")
    if sc is not None:
        check(f"moon.lat.{name}.schlyter", f"Lune, latitude, {name} (deg) : Meeus 47.B vs Schlyter",
              me * 1e-6, "MEEUS1998", sc, "SCHLYTER", 6e-4, "deg")

# argument rates and periods of the lunar terms (from Meeus mean rates, deg/cy)
rD, rM, rMp, rF = (fl(moon_meeus_rates[k]) for k in ("D", "M_sun", "M_prime", "F"))


def arg_period(arg):
    d, m, mp, f = arg
    rate = d * rD + m * rM + mp * rMp + f * rF
    return 36525 * 360 / abs(rate) if rate else None


# --- error budget of truncated lunar longitude (reference: full Meeus 47.A + additive terms) ---
def moon_budget():
    jd = 2451545.0 + np.arange(0, 36525.0 * 1.0, 0.05)    # 2000-2100
    T = (jd - 2451545.0) / 36525.0

    def poly(c):
        out = np.zeros_like(T)
        for k, cc in enumerate(c):
            out += float(F(cc)) * T ** k
        return out * DEG

    Lp, D_, M_, Mp_, F_ = (poly(MOON_MEEUS[k]) for k in ("L_prime", "D", "M_sun", "M_prime", "F"))
    E = 1 - 0.002516 * T - 0.0000074 * T * T
    A1 = (119.75 + 131.849 * T) * DEG
    A2 = (53.09 + 479264.29 * T) * DEG

    def term(row):
        d, m, mp, f, s = row
        fac = E ** abs(m)
        return s * 1e-6 * fac * np.sin(d * D_ + m * M_ + mp * Mp_ + f * F_)

    full = sum(term(r) for r in MEEUS_47A) + 1e-6 * (3958 * np.sin(A1) + 1962 * np.sin(Lp - F_) + 318 * np.sin(A2))
    subsets = [
        ("longitude moyenne seule", []),
        ("+ équation du centre (6,289 sin M′)", [(0, 0, 1, 0)]),
        ("+ 2ᵉ harmonique (0,214 sin 2M′)", [(0, 0, 1, 0), (0, 0, 2, 0)]),
        ("+ évection (1,274)", [(0, 0, 1, 0), (0, 0, 2, 0), (2, 0, -1, 0)]),
        ("+ variation (0,658)", [(0, 0, 1, 0), (0, 0, 2, 0), (2, 0, -1, 0), (2, 0, 0, 0)]),
        ("+ équation annuelle (0,186)", [(0, 0, 1, 0), (0, 0, 2, 0), (2, 0, -1, 0), (2, 0, 0, 0), (0, 1, 0, 0)]),
        ("+ réduction à l'écliptique (0,114)", [(0, 0, 1, 0), (0, 0, 2, 0), (2, 0, -1, 0), (2, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 2)]),
        ("+ 4 termes suivants (2D − 2M′, 2D − M − M′, 2D + M′, 2D − M)", [(0, 0, 1, 0), (0, 0, 2, 0), (2, 0, -1, 0), (2, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 2),
                                                                  (2, 0, -2, 0), (2, -1, -1, 0), (2, 0, 1, 0), (2, -1, 0, 0)]),
        ("+ M − M′, inégalité parallactique, M + M′", [(0, 0, 1, 0), (0, 0, 2, 0), (2, 0, -1, 0), (2, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 2),
                                         (2, 0, -2, 0), (2, -1, -1, 0), (2, 0, 1, 0), (2, -1, 0, 0), (0, 1, -1, 0), (1, 0, 0, 0), (0, 1, 1, 0)]),
    ]
    rows = []
    for label, keys in subsets:
        part = sum((term(r) for r in MEEUS_47A if (r[0], r[1], r[2], r[3]) in keys), np.zeros_like(T))
        err = (full - part)
        rows.append({"model": label, "max_abs_err_deg": rnd(float(np.max(np.abs(err))), 3),
                     "rms_err_deg": rnd(float(np.sqrt(np.mean(err ** 2))), 3)})
    # variant: equation of centre realised by a pin-and-slot with k = 6.288774 deg (in rad)
    k = 6.288774 * DEG
    keys = [(2, 0, -1, 0), (2, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 2)]
    part = sum((term(r) for r in MEEUS_47A if (r[0], r[1], r[2], r[3]) in keys), np.zeros_like(T))
    pin = (np.arctan2(np.sin(Mp_), np.cos(Mp_) - k) - Mp_)
    pin = (pin + np.pi) % (2 * np.pi) - np.pi
    err = full - part - pin / DEG
    rows.append({"model": "tenon-mortaise (k = 6,2888°) + évection + variation + annuelle + réduction",
                 "max_abs_err_deg": rnd(float(np.max(np.abs(err))), 3), "rms_err_deg": rnd(float(np.sqrt(np.mean(err ** 2))), 3)})
    # latitude
    fullb = sum(s * 1e-6 * E ** abs(m) * np.sin(d * D_ + m * M_ + mp * Mp_ + f * F_) for d, m, mp, f, s in MEEUS_47B)
    fullb = fullb + 1e-6 * (-2235 * np.sin(Lp) + 175 * np.sin(A1 - F_) + 175 * np.sin(A1 + F_) + 127 * np.sin(Lp - Mp_) - 115 * np.sin(Lp + Mp_))
    lat_rows = []
    for label, keys in [("5,128 sin F seul", [(0, 0, 0, 1)]),
                        ("+ M′ + F, M′ − F", [(0, 0, 0, 1), (0, 0, 1, 1), (0, 0, 1, -1)]),
                        ("+ 2D − F (évection en latitude)", [(0, 0, 0, 1), (0, 0, 1, 1), (0, 0, 1, -1), (2, 0, 0, -1)])]:
        part = sum((s * 1e-6 * np.sin(d * D_ + m * M_ + mp * Mp_ + f * F_) for d, m, mp, f, s in MEEUS_47B if (d, m, mp, f) in keys), np.zeros_like(T))
        err = fullb - part
        lat_rows.append({"model": label, "max_abs_err_deg": rnd(float(np.max(np.abs(err))), 3),
                         "rms_err_deg": rnd(float(np.sqrt(np.mean(err ** 2))), 3)})
    # inclination view: amplitude of the single sinF term if one uses i = 5.145 deg
    return rows, lat_rows


moon_lon_budget, moon_lat_budget = moon_budget()

moon_out = {
    "frame_note": "Meeus ch. 47 : equinoxe moyen de la date (tropique). Retirer p_A pour le repere sideral (orrery).",
    "mean_arguments_meeus47_deg": {
        k: {"c0": v[0], "c1_deg_per_cy": v[1], "c2": v[2], "c3": v[3], "c4": v[4]} for k, v in MOON_MEEUS.items()},
    "delaunay_iers2010_arcsec": {k: {"c0_deg": v[0], "c1_arcsec_per_cy": v[1], "c2_arcsec_per_cy2": v[2]} for k, v in DELAUNAY_IERS.items()},
    "simon1994_mean_elements": MOON_SIMON,
    "mean_motion": {
        "L_deg_per_day_tropical": rnd(moon_meeus_rates["L_prime"] / JC, 14),
        "L_turns_per_day_tropical": rnd(moon_meeus_rates["L_prime"] / JC / 360, 14),
        "L_turns_per_day_sidereal": rnd(lam_sid / 3600 / JC / 360, 14),
        "L_turns_per_tropical_year_tropical": rnd(moon_meeus_rates["L_prime"] / JC / 360 * TROPICAL_YEAR, 14),
        "L_turns_per_tropical_year_sidereal": rnd(lam_sid / 3600 / JC / 360 * TROPICAL_YEAR, 14),
        "relative_ratio_precision_for_1deg_per_century": rnd(1 / fl(moon_meeus_rates["L_prime"]), 4),
    },
    "months_days": {k: rnd(v, 14) for k, v in months.items()},
    "months_chapront2002_days": {k: {"value": float(v[0]), "T_coeff_days_per_cy": float(v[1])} for k, v in MONTHS_CHAPRONT2002.items()},
    "node_period_days": {"tropical": rnd(node_trop, 10), "sidereal": rnd(node_sid, 10),
                         "tropical_years": rnd(node_trop / TROPICAL_YEAR, 8)},
    "perigee_period_days": {"tropical": rnd(apse_trop, 10), "sidereal": rnd(apse_sid, 10),
                            "tropical_years": rnd(apse_trop / TROPICAL_YEAR, 8)},
    "eclipse_year_days": rnd(eclipse_year, 12),
    "evection_period_days": rnd(arg_period((2, 0, -1, 0)), 8),
    "periodic_terms_longitude": [
        {"name": n, "argument_D_M_Mp_F": list(a), "amplitude_deg_meeus": me * 1e-6,
         "amplitude_deg_brown": rnd(br / 3600, 6) if br is not None else None,
         "amplitude_deg_almanac": aa, "amplitude_deg_schlyter": sc,
         "argument_period_days": rnd(arg_period(a), 8)}
        for n, a, me, br, aa, sc in MOON_TERMS_LON],
    "periodic_terms_latitude": [
        {"name": n, "argument_D_M_Mp_F": list(a), "amplitude_deg_meeus": me * 1e-6,
         "amplitude_deg_almanac": aa, "amplitude_deg_schlyter": sc, "argument_period_days": rnd(arg_period(a), 8)}
        for n, a, me, aa, sc in MOON_TERMS_LAT],
    "annual_equation_E_factor": "E = 1 - 0.002516 T - 0.0000074 T^2 (Meeus 47.6), multiplie les termes en M (|M|=1) ; E^2 pour |M|=2",
    "meeus_table_47A_full": [list(r) for r in MEEUS_47A],
    "meeus_table_47A_additive": "+3958 sin A1 + 1962 sin(L'-F) + 318 sin A2 (1e-6 deg), A1 = 119.75 + 131.849 T, A2 = 53.09 + 479264.29 T",
    "meeus_table_47B_first30": [list(r) for r in MEEUS_47B],
    "error_budget_longitude_2000_2100": moon_lon_budget,
    "error_budget_latitude_2000_2100": moon_lat_budget,
    "inclination_deg": {
        "classic_mean_inclination": 5.145396, "classic_source": "NSSDC_MOON (5.145) / NASA_ECL (5.145)",
        "sinF_coefficient": 5.128122, "sinF_source": "MEEUS1998 (5.13 AA_LOWPREC)",
        "simon_mean_osculating": float(MOON_SIMON["i_mean_deg"]),
        "osculating_range": [5.00, 5.30], "range_source": "NASA_ECL (moonorbit.html, fig. 4-10)",
        "note": "Trois 'inclinaisons' differentes : 5,128 deg est le coefficient a utiliser pour beta = a sin F (les termes M'+-F et 2D-F completent) ; 5,145 deg est l'inclinaison moyenne classique ; 5,157 deg la moyenne de l'inclinaison osculatrice (Simon). L'inclinaison oscille entre ~5,0 et 5,3 deg (periode 173 j, demi-annee draconitique).",
    },
    "parallax_deg": {"mean": 0.9508, "first_term_cosMp": 0.0518, "second_cos_2D_minus_Mp": 0.0095, "third_cos_2D": 0.0078,
                     "range_deg": [0.898, 1.025], "source": "AA_LOWPREC (eq. 3)",
                     "note": "Parallaxe horizontale ~53,9' a 61,5' ; demi-diametre ~0,2725 x parallaxe (14,7' a 16,8')."},
}
check("moon.parallax_mean", "Lune : parallaxe moyenne (deg), Almanach vs asin(6378,14/385000,56) Meeus",
      0.9508, "AA_LOWPREC", math.asin(6378.14 / 385000.56) / DEG, "MEEUS1998", 0.002, "deg")

# ----------------------------------------------------------------------------
# 4. Eclipses
# ----------------------------------------------------------------------------
syn, drac, anom, sidm = (months[k] for k in ("synodic", "draconic", "anomalistic", "sidereal"))
cycles_def = {"saros": 223, "inex": 358, "exeligmos": 669, "metonic": 235, "tritos": 135, "callippic": 940}
cycles = {}
for cname, n in cycles_def.items():
    days = n * syn
    frac = fl(days) - math.floor(fl(days))
    cycles[cname] = {
        "synodic_months": n, "days": rnd(days, 12),
        "draconic_months": rnd(days / drac, 8), "anomalistic_months": rnd(days / anom, 8),
        "eclipse_years": rnd(days / eclipse_year, 8), "tropical_years": rnd(days / TROPICAL_YEAR, 8),
        "day_fraction": rnd(frac, 6),
        "geographic_shift_deg_west": rnd(((frac + 0.5) % 1 - 0.5) * 360, 4),
        "node_mismatch_deg": rnd(((fl(days / drac) + 0.5) % 1 - 0.5) * 360, 4),
    }
check("eclipse.saros_days_wiki", "Saros (j) : 223 x mois synodique vs Wikipedia 'Eclipse cycle'",
      cycles["saros"]["days"], "CHAPRONT2002", 6585.32, "WIKI_ECL_CYCLE", 0.006, "jours")
check("eclipse.saros_days_nasa", "Saros (j) : 223 x mois synodique vs NASA (6585,3223)",
      cycles["saros"]["days"], "CHAPRONT2002", 6585.3223, "NASA_ECL", 0.002, "jours",
      "La page NASA donne 6585,3223 j alors que 223 x 29,530589 = 6585,3213 j : coquille de la page (ecart 1,4 min).",
      explained=True)
check("eclipse.saros_draconic_nasa", "242 mois draconitiques (j) vs NASA 6585,3575",
      242 * drac, "SIMON1994", 6585.3575, "NASA_ECL", 0.001, "jours")
check("eclipse.saros_anomalistic_nasa", "239 mois anomalistiques (j) vs NASA 6585,5375",
      239 * anom, "SIMON1994", 6585.5375, "NASA_ECL", 0.001, "jours")
check("eclipse.inex_nasa", "Inex (j) : 358 x mois synodique vs NASA 10571,9509",
      cycles["inex"]["days"], "CHAPRONT2002", 10571.9509, "NASA_ECL", 0.001, "jours")
check("eclipse.exeligmos_wiki", "Exeligmos (j) vs Wikipedia 19755,96",
      cycles["exeligmos"]["days"], "CHAPRONT2002", 19755.96, "WIKI_ECL_CYCLE", 0.006, "jours")
check("eclipse.metonic_wiki", "Cycle de Meton 235 lunaisons (j) vs Wikipedia 6939,69",
      cycles["metonic"]["days"], "CHAPRONT2002", 6939.69, "WIKI_ECL_CYCLE", 0.006, "jours")


def ecl_limit(beta_lim_deg, incl_deg):
    return math.asin(math.tan(beta_lim_deg * DEG) / math.tan(incl_deg * DEG)) / DEG


# geometric ecliptic-limit estimate (inputs: parallax 53.9'-61.5', Moon SD 14.7'-16.8', Sun SD 15.8'-16.3', i 4.99-5.30)
sol_max = ecl_limit((61.5 - 0.15 + 16.8 + 16.3) / 60, 4.99)
sol_min = ecl_limit((53.9 - 0.15 + 14.7 + 15.8) / 60, 5.30)
lun_max = ecl_limit((1.02 * (61.5 + 0.15 - 15.8) + 16.8) / 60, 4.99)
lun_min = ecl_limit((1.02 * (53.9 + 0.15 - 16.3) + 14.7) / 60, 5.30)
check("eclipse.solar_limit_max", "Limite ecliptique solaire max (deg) : geometrie vs NASA (18,59)",
      sol_max, "calcul", 18.59, "NASA_ECL", 0.4, "deg",
      "Calcul statique (Lune immobile) ; la NASA tient compte du mouvement relatif pendant l'evenement.")
check("eclipse.solar_limit_min", "Limite ecliptique solaire min (deg) : geometrie vs NASA (15,39)",
      sol_min, "calcul", 15.39, "NASA_ECL", 0.3, "deg")
check("eclipse.lunar_limit_max", "Limite ecliptique lunaire (ombre) max (deg) : geometrie vs Meeus via Holmes (12 deg 08')",
      lun_max, "calcul", 12 + 8 / 60, "HOLMES_ECL", 0.3, "deg")

eclipses_out = {
    "cycles": cycles,
    "eclipse_year_days": rnd(eclipse_year, 12),
    "eclipse_season_mean_interval_days": rnd(eclipse_year / 2, 8),
    "ecliptic_limits_deg": {
        "solar_partial": {"min": 15.39, "max": 18.59, "source": "NASA_ECL",
                          "also": "WIKI_SOLAR_ECLIPSE : ~15 a 18 deg ; HOLMES_ECL (Meeus) : max 18 deg 24'"},
        "solar_central": {"min": 10.0, "max": 12.0, "approx": True, "source": "WIKI_SOLAR_ECLIPSE"},
        "lunar_umbral_partial": {"min": rnd(lun_min, 3), "max": rnd(lun_max, 3), "source": "calcul geometrique (ci-dessous)",
                                 "also": "HOLMES_ECL (Meeus) : max 12 deg 08' ; valeur classique ~9,5 a 12,2 deg"},
        "lunar_penumbral": {"min": 15.3, "max": 17.1, "source": "NASA_ECL (LEperiodicity.html)",
                            "note": "La page NASA lunaire donne 15,3-17,1 deg pour 'une eclipse de Lune visible' : il s'agit des eclipses penombrales (incluses dans le catalogue NASA)."},
        "geometric_estimate": {
            "solar": [rnd(sol_min, 4), rnd(sol_max, 4)], "lunar_umbral": [rnd(lun_min, 4), rnd(lun_max, 4)],
            "formula": "sin(dLambda) = tan(beta_lim)/tan(i) ; beta_lim(sol) = pi_L - pi_S + s_L + s_S ; beta_lim(lune, ombre) = 1,02 (pi_L + pi_S - s_S) + s_L",
            "inputs": "pi_L 53,9'-61,5', pi_S 0,15', s_L 14,7'-16,8', s_S 15,8'-16,3', i 4,99-5,30 deg",
        },
    },
    "gamma_model_meeus54": {
        "source": "MEEUS1998 (ch. 54, eclipse.go) ; seuils confirmes par WIKI_GAMMA",
        "gamma_approx": "gamma ~ (P cos F1 + Q sin F1)(1 - 0,0048 |cos F1|), Q = 5,2207 - 0,3299 cos M' + ..., P = 0,207 sin M - 0,0392 sin M' + ... ; soit gamma ~ 5,22 sin F (rayons terrestres)",
        "Q0_earth_radii": 5.2207, "Q_cosMp_coeff": -0.3299, "P_sinM_coeff": 0.207,
        "no_eclipse_if_abs_sinF_gt": 0.36,
        "solar_central_if_abs_gamma_lt": 0.9972,
        "solar_any_if_abs_gamma_lt": "1,5433 + u (u ~ 0,0059 + 0,0046 cos M - 0,0182 cos M')",
        "solar_partial_magnitude": "(1,5433 + u - |gamma|) / (0,5461 + 2u)",
        "lunar_umbral_magnitude": "(1,0128 - u - |gamma|) / 0,5450",
        "lunar_penumbral_magnitude": "(1,5573 + u - |gamma|) / 0,5450",
        "sign_convention": "Eclipse de Soleil : gamma > 0 = axe de l'ombre au nord du centre de la Terre (hemisphere nord) ; eclipse de Lune : gamma > 0 = Lune au sud de l'axe de l'ombre (WIKI_GAMMA). gamma a le signe de sin F au voisinage du noeud.",
        "partial_limit_range_wiki": [1.525, 1.571],
    },
    "saros_longitude_shift_note": "Chaque Saros decale l'eclipse de ~0,32 j (~8 h) donc d'environ 116 deg vers l'ouest ; l'Exeligmos (3 Saros) ramene a ~-14 deg pres la meme longitude.",
}

# ----------------------------------------------------------------------------
# 5. Galilean satellites
# ----------------------------------------------------------------------------
E5 = {"io": "203.48895579", "europa": "101.374724735", "ganymede": "50.317609207", "callisto": "21.571071177"}  # deg/day
MEEUS_SYN = {"io": "203.4058646", "europa": "101.2916335", "ganymede": "50.234518", "callisto": "21.48798"}  # deg/day vs Sun direction
NSSDC_GAL = {"io": "1.769138", "europa": "3.551181", "ganymede": "7.154553", "callisto": "16.689017"}
JPLSAT = {"io": ("421800", "0.004", "1.762732", "1.333", "0.000"), "europa": ("671100", "0.009", "3.525463", "1.394", "30.202"),
          "ganymede": ("1070400", "0.001", "7.155588", "68.301", "137.812"), "callisto": ("1882700", "0.007", "16.690440", "277.921", "577.264")}
jup_rate_day = F(JPL_T1["jupiter"][1][3]) / JC     # deg/day (sidereal, local)
gal = {}
for m in ("io", "europa", "ganymede", "callisto"):
    n = F(E5[m])
    psid = 360 / n
    psyn = 360 / (n - jup_rate_day)
    a_km, ecc, P_jpl, Paps, Pnode = JPLSAT[m]
    gal[m] = {
        "mean_motion_deg_per_day_E5": float(n), "sidereal_period_days": rnd(psid, 12),
        "synodic_period_days_vs_sun": rnd(psyn, 12),
        "turns_per_day_sidereal": rnd(n / 360, 14),
        "a_km": float(a_km), "e_jpl": float(ecc),
        "jpl_mean_elements_P_days": float(P_jpl), "apsidal_period_years": float(Paps), "nodal_period_years": float(Pnode),
    }
    check(f"galilean.{m}.sidereal_vs_nssdc", f"{m} : periode siderale (j), Lieske E5 vs NSSDC",
          psid, "LIESKE_E5", F(NSSDC_GAL[m]), "NSSDC_JOVSAT", 2e-6, "jours")
    ndec = len(MEEUS_SYN[m].split(".")[1])
    tol_syn = fl(psyn) ** 2 / 360 * 0.5 * 10 ** (-ndec) + 2e-6   # rounding of Meeus' rate + Jupiter-rate choice
    check(f"galilean.{m}.synodic_vs_meeus", f"{m} : periode synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44",
          psyn, "LIESKE_E5+JPL_APPROX", 360 / F(MEEUS_SYN[m]), "MEEUS1998", rnd(tol_syn, 2), "jours",
          f"Tolerance = arrondi du taux de Meeus ({ndec} decimales) + choix du taux de Jupiter.")
    # JPL 'P' is the anomalistic period for the precessing-ellipse fit
    if float(Paps) > 0:
        n_anom = n - F(360) / (F(Paps) * F("365.25"))
        check(f"galilean.{m}.jpl_P_is_anomalistic", f"{m} : 'P' de la table JPL = periode anomalistique ? (360/(n - varpi'))",
              360 / n_anom if m in ("ganymede", "callisto") else 360 / (n + F(360) / (F(Paps) * F("365.25"))),
              "LIESKE_E5+JPL_SAT", F(P_jpl), "JPL_SAT", 2e-3, "jours",
              "La colonne P du JPL est la periode de l'anomalie moyenne (ellipse en precession), pas la periode siderale. Pour Io et Europe le perijove force retrograde en ~1,3-1,4 an (lie a la resonance), d'ou P plus courte de 0,4-0,7 %.",
              explained=True)
    gal[m]["note_jpl_P"] = "P (JPL) = periode anomalistique, a ne pas utiliser comme periode siderale."
lap = F(E5["io"]) - 3 * F(E5["europa"]) + 2 * F(E5["ganymede"])
check("galilean.laplace_rates", "Relation de Laplace n1 - 3 n2 + 2 n3 (deg/j), E5",
      lap, "LIESKE_E5", 0, "theorie", 1e-6, "deg/jour")
galilean_out = {
    "moons": gal,
    "laplace": {
        "relation": "n_Io - 3 n_Europe + 2 n_Ganymede = 0 ; Phi_L = lambda_Io - 3 lambda_Europe + 2 lambda_Ganymede = 180 deg (libration)",
        "residual_deg_per_day_E5": rnd(lap, 6),
        "n1_minus_2n2_deg_per_day": rnd(F(E5["io"]) - 2 * F(E5["europa"]), 10),
        "n2_minus_2n3_deg_per_day": rnd(F(E5["europa"]) - 2 * F(E5["ganymede"]), 10),
        "period_ratios": {"europa_over_io": rnd(F(E5["io"]) / F(E5["europa"]), 10),
                          "ganymede_over_europa": rnd(F(E5["europa"]) / F(E5["ganymede"]), 10),
                          "callisto_over_ganymede": rnd(F(E5["ganymede"]) / F(E5["callisto"]), 10)},
        "io_europa_synodic_days": rnd(360 / (F(E5["io"]) - F(E5["europa"])), 10),
        "europa_ganymede_synodic_days": rnd(360 / (F(E5["europa"]) - F(E5["ganymede"])), 10),
        "conjunction_line_regression_period_days": rnd(360 / (F(E5["io"]) - 2 * F(E5["europa"])), 10),
        "conjunction_note": "Les conjonctions Io-Europe ont lieu tous les 3,5255 j ; leur longitude retrograde de 0,7395 deg/j (tour complet en 486,8 j), entrainant le perijove force d'Io et d'Europe : c'est pourquoi la periode anomalistique d'Europe (JPL 'P' = 3,525463 j) egale la periode synodique Io-Europe. Une triple conjonction est impossible (Phi_L = 180 deg).",
        "libration": {
            "period_days": 2071, "period_source": "CELLETTI2021 (Lieske 1998) ; terme Phi_lambda = 199,6766 + 0,1737919 t de E5 (Meeus 44) => 2071,4 j",
            "amplitude_deg": [0.03, 0.066],
            "amplitude_sources": "0,03 deg : WIKI_RESONANCE (Sinclair 1975, periode ~2000 j) ; 0,066 deg : Lieske (cite par Celletti et al., non verifie dans le texte original)",
            "note": "Libration hors de portee d'un engrenage (< 0,1 deg) : la machine realise Phi_L = 180 deg exactement.",
        },
    },
    "earth_view": {
        "light_time_minutes_range": [rnd((5.2026 * (1 - 0.0484) - 1.0167) * 499.004784 / 60, 4),
                                      rnd((5.2026 * (1 + 0.0484) + 1.0167) * 499.004784 / 60, 4)],
        "max_sun_earth_angle_at_jupiter_deg": rnd(math.asin(1.0167 / (5.2026 * (1 - 0.0484))) / DEG, 4),
        "note": "Vu de la Terre, les phenomenes (eclipses, passages) sont decales par le temps de lumiere (Roemer, ~+-8 min) et par l'angle Soleil-Terre vu de Jupiter (jusqu'a ~12 deg) : pour Io (8,5 deg/h) cela fait jusqu'a ~1,4 h. La periode synodique moyenne (/Soleil) est la reference.",
    },
}

# ----------------------------------------------------------------------------
# 6. Pluto (optional)
# ----------------------------------------------------------------------------
pl = planets_out["pluto"]
check("pluto.sidereal_period", "Pluton : periode siderale (j), JPL T1 (archive) vs NSSDC",
      pl["mean_motion"]["sidereal_period_days"], "JPL_APPROX_2019", F("90560"), "NSSDC", 300, "jours",
      "Le taux JPL est local (1800-2050) ; Pluton est fortement perturbe par Neptune (resonance 3:2).", explained=True)
pl["neptune_resonance_ratio"] = rnd(planets_out["pluto"]["mean_motion"]["sidereal_period_days"] /
                                    planets_out["neptune"]["mean_motion"]["sidereal_period_days"], 6)
pl["flag_fr"] = "OPTIONNEL : planete naine (UAI 2006) ; e = 0,249 et i = 17,1 deg ; 3:2 avec Neptune. Retiree des tables JPL actuelles."

# ----------------------------------------------------------------------------
# 7. Assemble JSON
# ----------------------------------------------------------------------------
n_ok = sum(c["status"] == "ok" for c in CHECKS)
n_exp = sum(c["status"] == "explique" for c in CHECKS)
n_att = sum(c["status"] == "ATTENTION" for c in CHECKS)

data = {
    "meta": {
        "title": "Anticythere 2.0 -- constantes astronomiques modernes",
        "generated_by": "v2/tools/build_constants.py",
        "accessed": ACCESSED,
        "checks_summary": {"total": len(CHECKS), "ok": n_ok, "explained": n_exp, "attention": n_att},
    },
    "conventions": {
        "epoch": "J2000.0 = JD 2451545.0 TT = 2000-01-01 12:00 TT",
        "time_argument": "T = (JD_TT - 2451545.0) / 36525 (siecles juliens) ; t (Simon 1994) = millenaires juliens",
        "time_scale": "TT (~TDB). La machine compte des jours solaires moyens (UT1) : TT - UT1 = DeltaT ~ 69,1 s en 2026 (USNO_DT), effet < 0,01 deg sur la Lune.",
        "frames": {"sidereal": "ecliptique et equinoxe moyens fixes J2000 (inertiel ; pour l'orrery)",
                   "tropical": "equinoxe moyen de la date (pour le cadran zodiacal avant ; difference = precession p_A)"},
        "units": "deg, '' (seconde d'arc), jours de 86400 s, siecles juliens de 36525 j, au, km",
        "values_as_strings": "Les valeurs transcrites des sources sont conservees en chaines decimales exactes (exact_strings) pour des conversions Fraction / Lean sans perte.",
    },
    "sources": {**SOURCES, "accessed": ACCESSED},
    "earth": {
        "years_days": {
            "tropical_mean_laskar": {"value": float(TY_LASKAR[0]), "poly_T": [float(x) for x in TY_LASKAR], "source": "LASKAR1986_TY",
                                     "note": "jours de 86400 s SI (TT) ; ~365,24217 jours solaires moyens"},
            "tropical_from_simon_of_date": rnd(tropical_year_simon, 13),
            "tropical_from_simon_plus_pA_IAU2006": rnd(tropical_year_iau2006, 13),
            "tropical_from_jpl_table1_plus_pA": rnd(tropical_year_jpl, 13),
            "vernal_equinox_year_2000": {"value": 365.242374, "source": "LASKAR1986_TY (Meeus & Savoie 1992)",
                                         "others": {"june_solstice": 365.241626, "september_equinox": 365.242018, "december_solstice": 365.242740}},
            "sidereal": {"value": rnd(sidereal_year, 13), "source": "SIMON1994", "check": 365.256363004},
            "sidereal_from_jpl_table1": rnd(sidereal_year_jpl, 13),
            "anomalistic": {"value": rnd(anomalistic_year, 13), "source": "IERS2010 (l')"},
            "draconic_eclipse_year": rnd(eclipse_year, 12),
            "gregorian": {"value": 365.2425, "exact": "146097/400"},
            "julian": 365.25,
        },
        "precession": {
            "pA_arcsec_per_cy_IAU2006": float(PA_IAU2006), "pA_T2_arcsec_per_cy2": float(PA_IAU2006_T2),
            "pA_arcsec_per_year": rnd(PA_IAU2006 / 100, 10), "pA_deg_per_cy": rnd(pa_deg_cy, 12),
            "period_julian_years": rnd(precession_period_yr, 8),
            "turns_per_tropical_year": rnd(PA_IAU2006 / 100 / ARCSEC_PER_TURN * TROPICAL_YEAR / F("365.25"), 10),
            "alternatives": {"Simon1994_Williams1991": float(PA_SIMON1994), "IAU1976": float(PA_IAU1976),
                             "IERS_F14_rad_per_cy": float(F14_IERS_RAD)},
            "psi_A_arcsec_per_cy": float(PSI_A_IERS), "chi_A_arcsec_per_cy": float(CHI_A_IERS),
            "source": "CAPITAINE2003 / IERS2010",
            "sidereal_minus_tropical_year_minutes": rnd((sidereal_year - TY_LASKAR[0]) * 1440, 6),
        },
        "obliquity": {
            "eps0_arcsec_IAU2006": float(EPS0_IAU2006), "eps0_deg_IAU2006": rnd(eps0_deg, 12),
            "poly_arcsec_T1_to_T5_IAU2006": [float(x) for x in EPS_RATE_IAU2006],
            "eps0_arcsec_IAU1980": float(EPS0_IAU1980), "poly_IAU1980": [float(x) for x in EPS_RATE_IAU1980],
            "rate_deg_per_cy": rnd(EPS_RATE_IAU2006[0] / 3600, 10),
            "long_term_range_deg": [22.0425, 24.5044], "long_term_period_years": 41040,
            "source": "IERS2010 ; WIKI_AXIAL_TILT ; MEEUS1998",
        },
        "rotation": {
            "era_turns_per_ut1_day": float(ERA_RATE), "gmst_ratio_sidereal_per_solar": rnd(gmst_ratio_iers, 16),
            "mean_sidereal_day_s": rnd(mean_sidereal_day_s, 12), "stellar_day_s": rnd(stellar_day_s, 12),
            "sidereal_days_per_tropical_year": rnd(TY_LASKAR[0] + 1, 12),
            "gmst_IAU2006": "GMST = ERA(UT1) + 0,014506'' + 4612,156534'' t + 1,3915817'' t^2 - ... (IERS 5.32)",
            "era_formula": "ERA = 2 pi (0,7790572732640 + 1,00273781191135448 Tu), Tu = JD(UT1) - 2451545,0 (IERS 5.14)",
            "delta_T_2026_s": 69.1, "delta_T_source": "USNO_DT",
            "source": "IERS2010 ; MEEUS1998 ; WIKI_SIDEREAL",
        },
        "equation_of_time": {
            "model": "E = y sin 2L0 - 2e sin M + 4ey sin M cos 2L0 - y^2/2 sin 4L0 - 5/4 e^2 sin 2M (radians ; x 720/pi -> minutes) ; y = tan^2(eps/2) ; E = temps solaire vrai - temps solaire moyen",
            "source": "MEEUS1998 (28.3, Smart) ; WIKI_EOT",
            "y": rnd(y_eot, 10), "e": E_EARTH,
            "term_amplitudes_min": {k: rnd(v, 6) for k, v in eot_terms_min.items()},
            "two_sine_approx_wiki": "Dt = -7,659 sin D + 9,863 sin(2D + 3,5932) min, D = 6,240040 + 0,01720197 (365,25 (y - 2000) + d)",
            "extremes_2026": {"min_minutes": rnd(eot_min_2026[0], 5), "min_date": eot_min_2026[1],
                              "max_minutes": rnd(eot_max_2026[0], 5), "max_date": eot_max_2026[1]},
            "secular_drift": "Le perihelie avance de 1,72 deg/siecle par rapport a l'equinoxe (Meeus 31.A : 1,7195) : la courbe se deforme lentement ; e baisse de 4,2e-5/siecle (-0,02 min d'amplitude).",
            "perihelion_longitude_deg_J2000": 102.93734808, "perihelion_rate_deg_per_cy_of_date": rnd(F(SIMON_DATE["earth"]["p1"]) / 36000, 8),
        },
        "sun_equation_of_centre_meeus_deg": {"c1": "1.914602 - 0.004817 T - 0.000014 T^2", "c2": "0.019993 - 0.000101 T", "c3": "0.000289"},
        "calendar": {
            "rule": "annee bissextile si divisible par 4, sauf si divisible par 100 et non par 400",
            "cycle_400y_days": 146097, "cycle_400y_weeks": 20871, "leap_years_per_400": 97,
            "mean_year_days": 365.2425,
            "drift_vs_mean_tropical_years_per_day": rnd(greg_drift_tropical, 6),
            "drift_vs_vernal_equinox_year_years_per_day": rnd(greg_drift_vernal, 6),
            "day_of_week": "dow = floor(JD + 1,5) mod 7 (0 = dimanche) ; 2000-01-01 = samedi",
            "source": "WIKI_GREGORIAN ; MEEUS1998 ch. 7",
        },
    },
    "planets": planets_out,
    "great_inequalities_jpl_table2b": great_ineq,
    "moon": moon_out,
    "eclipses": eclipses_out,
    "galilean": galilean_out,
    "negligible_or_out_of_reach": [
        {"effect": "nutation en longitude", "amplitude": "17,2'' (18,6 ans)", "deg": 0.0048, "source": "IERS2010 table 5.3a"},
        {"effect": "aberration annuelle", "amplitude": "20,5''", "deg": 0.0057, "source": "MEEUS1998"},
        {"effect": "Terre vs barycentre Terre-Lune", "amplitude": "~6'' sur la longitude du Soleil", "deg": 0.002, "source": "calcul (4670 km / 1 au)"},
        {"effect": "DeltaT (TT - UT1) en 2026", "amplitude": "69 s -> 0,6' sur la Lune", "deg": 0.0105, "source": "USNO_DT"},
        {"effect": "libration de la resonance de Laplace", "amplitude": "0,03-0,066 deg", "deg": 0.066, "source": "WIKI_RESONANCE / CELLETTI2021"},
        {"effect": "termes lunaires < 0,03 deg (au-dela des 13 premiers)", "amplitude": "somme quadratique ~0,05 deg", "deg": 0.05, "source": "MEEUS1998"},
        {"effect": "ecart repere de date vs (J2000 + p_A) pour lambda planetaire", "amplitude": "≤ 2,3''/siecle", "deg": 0.0007, "source": "SIMON1994"},
        {"effect": "perturbations planetaires autres que les grandes inegalites", "amplitude": "< 0,06 deg (Jupiter), < 0,23 deg (Saturne)", "deg": 0.23, "source": "SCHLYTER"},
    ],
    "cross_checks": CHECKS,
}

SKIP_KEYS = {"url", "url2", "url3", "url4", "snapshot", "cite", "query_url", "command", "api", "generated_by",
             "name", "source", "source_a", "source_b", "id", "exact_strings", "exact_strings_arcsec_per_millennium",
             "c0", "c1_deg_per_cy", "c2", "c3", "c4", "c0_deg", "c1_arcsec_per_cy", "c2_arcsec_per_cy2", "exact"}


def fr_tree(o, key=None):
    if isinstance(o, dict):
        return {k: (v if k in SKIP_KEYS else fr_tree(v, k)) for k, v in o.items()}
    if isinstance(o, list):
        return [fr_tree(v, key) for v in o]
    if isinstance(o, str) and key not in SKIP_KEYS:
        return fr(o)
    return o


data = {k: (v if k in ("sources", "cross_checks") else fr_tree(v)) for k, v in data.items()}
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# ----------------------------------------------------------------------------
# 8. Markdown (French)
# ----------------------------------------------------------------------------
def frnum(s):
    """French number formatting: decimal comma, true minus sign."""
    s = str(s).replace(".", ",")
    return "\u2212" + s[1:] if s.startswith("-") else s


def f_(x, n=6):
    if x is None:
        return "—"
    if isinstance(x, (F,)):
        x = float(x)
    if isinstance(x, float):
        s = f"{x:.{n}f}"
    else:
        s = str(x)
    return frnum(s)


def g_(x, n=8):
    if x is None:
        return "—"
    return frnum(f"{float(x):.{n}g}")


md = []
A = md.append
A("# Anticythère 2.0 — constantes astronomiques modernes\n")
A(f"*Fichier généré par `v2/tools/build_constants.py` (ne pas éditer à la main). Données : `constants.json`. Sources consultées le {ACCESSED}.*\n")
A("## Conventions\n")
A("- **Époque** : J2000.0 = JD 2451545,0 **TT** (1er janvier 2000, 12 h TT). **T** = siècles juliens de 36 525 jours depuis J2000.0 ; Simon et al. (1994) utilisent *t* en millénaires.")
A("- **Unités** : degrés (°), secondes d'arc (″), jours de 86 400 s, unités astronomiques (au).")
A("- **Deux repères** : *sidéral* = écliptique et équinoxe **fixes** de J2000 (c'est ce que doit reproduire l'orrery du dessus) ; *tropique* = équinoxe **de la date** (c'est ce que lit un zodiaque attaché à l'équinoxe, comme sur le cadran avant). La différence entre les deux est la précession générale p_A ≈ 1,397° par siècle — **plus que l'objectif de 1°/siècle** : il faut donc soit tout entraîner en sidéral et faire tourner lentement l'anneau zodiacal (1 tour en 25 772 ans), soit ajouter p_A à chaque rapport.")
A("- **Temps** : les éphémérides sont en TT ; la manivelle compte des jours solaires moyens (UT1). ΔT = TT − UT1 ≈ 69,1 s en 2026 (USNO) : 0,6′ sur la Lune, négligeable.")
A(f"- **Vérifications croisées** : {len(CHECKS)} comparaisons entre au moins deux sources ; **{n_ok} conformes**, **{n_exp} écarts expliqués**, **{n_att} à surveiller** (liste complète en fin de document).\n")

A("## 0. Synthèse pour la conception\n")
_mmJ = planets_out["jupiter"]["mean_motion"]; _mmS = planets_out["saturn"]["mean_motion"]
A(f"- **Moyens mouvements planétaires** : viser les taux DE441 ajustés sur 2000–2100 (§ 2.2) ; JPL table 1 est équivalente à < 0,1°/siècle près. Les taux séculaires classiques (VSOP87/Simon, Meeus) sont faux de {f_(abs(planets_out['saturn']['rate_candidates_deg_per_century_sidereal']['secular_minus_recommended']),2)}°/siècle pour Saturne sur ce siècle (grande inégalité).")
A("- **Deux repères** : l'orrery (dessus) tourne en sidéral ; le zodiaque (avant) lit des longitudes tropiques. Écart = précession 1,397°/siècle, à mécaniser (anneau zodiacal : 1 tour en 25 772 ans) ou à intégrer aux rapports.")
A(f"- **Lune** (objectif ~0,5°) : équation du centre + évection + variation + équation annuelle → erreur max {f_(moon_lon_budget[5]['max_abs_err_deg'],2)}° ; + réduction à l'écliptique → {f_(moon_lon_budget[6]['max_abs_err_deg'],2)}°. Latitude : 5,128 sin F + 3 termes → {f_(moon_lat_budget[2]['max_abs_err_deg'],2)}°.")
A(f"- **Équation du centre des planètes** : tenon-mortaise (k = 2e) suffisant sauf Mars ({f_(planets_out['mars']['equation_of_centre']['pin_and_slot_k_2e_max_err_deg'],2)}°) et Mercure ({f_(planets_out['mercury']['equation_of_centre']['pin_and_slot_k_2e_max_err_deg'],2)}°) ; l'équant ramène Mars à {f_(planets_out['mars']['equation_of_centre']['bisected_equant_max_err_deg'],2)}° mais laisse Mercure à {f_(planets_out['mercury']['equation_of_centre']['bisected_equant_max_err_deg'],2)}°.")
A("- **Temps** : jour sidéral moyen 86 164,0905 s (366,2422 jours sidéraux par année tropique) ; équation du temps = 9,86 min × (½ an) + 7,66 min × (1 an) + termes < 0,7 min ; calendrier grégorien 146 097 j / 400 ans = 20 871 semaines exactes.")
A("- **Éclipses** : Saros 223 lunaisons (6585,321 j) ≈ 242 mois draconitiques ≈ 239 anomalistiques ; γ ≈ 5,22 sin F rayons terrestres donne magnitude et hémisphère (signe de γ).")
A(f"- **Satellites galiléens** : n_Io − 3 n_Europe + 2 n_Ganymède = 0 (à 1e-9 °/j près) ; périodes sidérales 1,769138 / 3,551181 / 7,154553 / 16,689018 j ; conjonctions Io–Europe tous les {f_(360/(F(E5['io'])-F(E5['europa'])),4)} j, ligne des conjonctions en rotation rétrograde en {f_(360/(F(E5['io'])-2*F(E5['europa'])),1)} j.")
A("- **Hors de portée / négligeable** (§ 7) : nutation (17″), aberration (20″), ΔT (~1 min), libration de Laplace (< 0,07°), perturbations planétaires à courte période (jusqu'à 0,23° pour Saturne).\n")
A("## 1. Terre : années, précession, obliquité, rotation\n")
A("| Grandeur | Valeur | Source principale | Contrôle |")
A("|---|---|---|---|")
A(f"| Année tropique moyenne (J2000) | {f_(TY_LASKAR[0],10)} j (= 365 j 5 h 48 min 45,19 s) − 6,15×10⁻⁶ T | Laskar 1986 via McCarthy & Seidelmann 2009 | Simon 1994 (taux de date) : {f_(tropical_year_simon,10)} ; Simon + p_A IAU 2006 : {f_(tropical_year_iau2006,10)} |")
A(f"| Année de l'équinoxe de mars (2000) | 365,242374 j | Meeus & Savoie 1992 | — (c'est elle qui compte pour le calendrier) |")
A(f"| Année sidérale | {f_(sidereal_year,9)} j | Simon 1994 (λ J2000) | Wikipedia « Year » 365,256363004 ; NSSDC 365,256 |")
A(f"| Année anomalistique | {f_(anomalistic_year,9)} j | IERS 2010 (l′) | Simon (λ − ϖ) {f_(anomalistic_year_simon,9)} ; Wikipedia 365,259636 |")
A(f"| Année draconitique (des éclipses) | {f_(eclipse_year,8)} j | IERS 2010 (F − D) | Wikipedia 346,620075883 |")
A(f"| Année grégorienne | 365,2425 j = 146097/400 | règle 4/100/400 | 146 097 j = 20 871 semaines exactement |")
A(f"| Précession générale p_A (IAU 2006) | 5028,796195″/siècle + 1,1054348″ T² = 50,288″/an | Capitaine et al. 2003 | ψ_A − χ_A cos ε₀ (IERS) = {f_(pa_from_iers,4)} ; Simon 1994 : 5028,82 ; IAU 1976 : 5029,0966 |")
A(f"| Période de précession | {f_(precession_period_yr,1)} ans | 1 296 000″ / 50,28796″ | Wikipedia 25 771,6 ans |")
A(f"| Obliquité moyenne ε₀ (IAU 2006) | 84 381,406″ = 23° 26′ 21,406″ = {f_(eps0_deg,8)}° | IERS 2010 éq. 5.40 | IAU 1980 (Meeus) : 84 381,448″ (écart 0,042″) |")
A(f"| Variation de l'obliquité | −46,836769″/siècle (−0,01301°/siècle) | IERS 2010 | IAU 1980 : −46,8150″ ; long terme 22,04°–24,50°, période 41 040 ans |")
A(f"| Jour sidéral moyen (équinoxe) | {f_(mean_sidereal_day_s,4)} s = 23 h 56 min 4,0905 s | IERS (ERA + précession en AR) | Wikipedia 86 164,0905 s |")
A(f"| Jour stellaire (ERA, étoiles fixes) | {f_(stellar_day_s,4)} s | IERS 2010 éq. 5.14 | +8,4 ms vs jour sidéral |")
A(f"| Rapport temps sidéral / solaire moyen | {f_(gmst_ratio_iers,12)} | IERS 2010 | Meeus (Aoki 1982) 1,00273790935 |")
A(f"| Jours sidéraux par année tropique | {f_(TY_LASKAR[0]+1,7)} | exact (un tour de plus) | — |")
A("")
A(f"**Calendrier grégorien.** Bissextile si divisible par 4, sauf les siècles non divisibles par 400 (97 bissextiles en 400 ans). Dérive : 1 jour en {f_(greg_drift_tropical,0)} ans par rapport à l'année tropique moyenne, 1 jour en {f_(greg_drift_vernal,0)} ans par rapport à l'année de l'équinoxe de mars (Wikipedia donne ~3 236 ans avec 365,2422). Jour de la semaine : floor(JD + 1,5) mod 7 (0 = dimanche) ; le 1er janvier 2000 était un samedi.\n")
A("**Équation du temps** (E = temps solaire vrai − temps solaire moyen ; formule de Smart reprise par Meeus 28.3) :\n")
A("E = y sin 2L₀ − 2e sin M + 4ey sin M cos 2L₀ − ½y² sin 4L₀ − 5/4 e² sin 2M, avec y = tan²(ε/2).\n")
A("| Terme | Amplitude | Période |")
A("|---|---|---|")
A(f"| y sin 2L₀ (obliquité) | {f_(eot_terms_min['y_sin_2L0'],3)} min | ½ année |")
A(f"| −2e sin M (excentricité) | {f_(eot_terms_min['minus_2e_sin_M'],3)} min | année anomalistique |")
A(f"| 4ey sin M cos 2L₀ | {f_(eot_terms_min['4ey_sinM_cos2L0'],3)} min | mixte |")
A(f"| −½y² sin 4L₀ | {f_(eot_terms_min['minus_half_y2_sin_4L0'],3)} min | ¼ année |")
A(f"| −5/4 e² sin 2M | {f_(eot_terms_min['minus_5_4_e2_sin_2M'],3)} min | ½ année anomalistique |")
A("")
A(f"Extrêmes 2026 (formule ci-dessus) : {f_(eot_min_2026[0],2)} min le {eot_min_2026[1]} et +{f_(eot_max_2026[0],2)} min le {eot_max_2026[1]} (Wikipedia : −14 min 15 s le 11 février, +16 min 25 s le 3 novembre). Les deux termes principaux (Wikipedia : 7,66 et 9,87 min) se mécanisent avec deux cames ou deux tenons-mortaises (1 tour/an et 2 tours/an). La courbe dérive lentement : le périhélie avance de 1,72°/siècle par rapport à l'équinoxe.\n")

A("## 2. Planètes : éléments, moyens mouvements, périodes\n")
A("Quatre jeux de taux, qui ne se valent pas pour le même usage :\n")
A("- **DE441 ajusté sur 2000–2100** (JPL Horizons, éléments osculateurs, ajustement linéaire de L = Ω + ω + M ; barycentriques pour Jupiter–Pluton afin d'éliminer l'oscillation du Soleil autour du barycentre) : **taux recommandé pour la machine** (fenêtre visée 2000–2100).")
A("- **JPL table 1** (Standish & Williams) : ajustement *local* 1800–2050 ; éléments de départ (a, e, i, ϖ, Ω) et contrôle principal du taux.")
A("- **JPL tables 2a + 2b** : ajustement 3000 av. J.-C. – 3000 apr. J.-C., avec un terme périodique en M pour Jupiter–Neptune (grandes inégalités).")
A("- **Simon et al. 1994** (VSOP87/JASON84) : éléments moyens *séculaires* ; ils ne contiennent pas les grandes inégalités.\n")
A("### 2.1 Éléments J2000 (JPL table 1, repère J2000) et taux par siècle\n")
A("| Planète | a (au) | e | i (°) | L (°) | ϖ (°) | Ω (°) | L̇ (°/siècle) | ϖ̇ (°/siècle) | Ω̇ (°/siècle) |")
A("|---|---|---|---|---|---|---|---|---|---|")
for name in PLANETS + ["pluto"]:
    el, rt = JPL_T1[name]
    A(f"| {FR[name]}{' (optionnel)' if name=='pluto' else ''} | " + " | ".join(frnum(v) for v in (el[0], el[1], el[2], el[3], el[4], el[5], rt[3], rt[4], rt[5])) + " |")
A("\n*ė, i̇, ȧ : voir `constants.json`. Pluton : table JPL archivée (2019), retirée depuis des tables actuelles.*\n")
A("### 2.2 Moyens mouvements recommandés pour les rapports d'engrenages\n")
A("Base : DE441 ajusté 2000–2100 (repère J2000 = sidéral). Tropique = sidéral + p_A (IAU 2006). « Précision relative » = erreur relative de rapport qui produit 1° d'erreur de longitude moyenne par siècle.\n")
A("| Planète | °/siècle (sidéral) | tours/jour (sidéral) | tours/année tropique (sidéral, orrery) | tours/année tropique (tropique, zodiaque) | Période sidérale (j) | Période synodique (j) | Précision relative pour 1°/siècle |")
A("|---|---|---|---|---|---|---|---|")
for name in PLANETS + ["pluto"]:
    mm = planets_out[name]["mean_motion"]
    A(f"| {FR[name]} | {f_(mm['deg_per_century_sidereal'],5)} | {g_(mm['turns_per_day_sidereal'],12)} | {g_(mm['turns_per_tropical_year_sidereal'],12)} | {g_(mm['turns_per_tropical_year_tropical'],12)} | {f_(mm['sidereal_period_days'],4)} | {f_(mm.get('synodic_period_days'),3)} | {g_(mm['relative_ratio_precision_for_1deg_per_century'],2)} |")
A("")
A("### 2.3 Quel taux viser ? (écart entre jeux d'éléments, °/siècle, repère J2000)\n")
A("| Planète | DE441 2000–2100 (recommandé) | Incertitude d'ajustement | JPL T1 (1800–2050) | JPL 2a+2b sur 2000–2100 | Simon 1994 séculaire | T1 − DE441 | Séculaire − DE441 | Résidu non linéaire 2000–2100 (°) |")
A("|---|---|---|---|---|---|---|---|---|")
for name in PLANETS:
    rc = planets_out[name]["rate_candidates_deg_per_century_sidereal"]
    res = planets_out[name]["rate_fit_2000_2100_from_jpl_table2"]["max_residual_from_linear_deg"]
    unc = planets_out[name]["mean_motion"]["rate_uncertainty_deg_per_century"]
    A(f"| {FR[name]} | {f_(rc['recommended_de441_fit_2000_2100'],4)} | {'±' + f_(unc,3) if name in ('jupiter','saturn','uranus','neptune') else '≤ 0,005'} | {f_(rc['jpl_table1_1800_2050'],4)} | {f_(rc['jpl_table2_fit_2000_2100'],4)} | {f_(rc['simon1994_secular'],4)} | {f_(rc['t1_minus_recommended'],3)} | {f_(rc['secular_minus_recommended'],3)} | {f_(res,3)} |")
A("")
t1max = max(abs(planets_out[n]["rate_candidates_deg_per_century_sidereal"]["t1_minus_recommended"]) for n in PLANETS)
secJ = planets_out["jupiter"]["rate_candidates_deg_per_century_sidereal"]["secular_minus_recommended"]
secS = planets_out["saturn"]["rate_candidates_deg_per_century_sidereal"]["secular_minus_recommended"]
sg = lambda x, n=2: ("+" if x >= 0 else "") + f_(x, n)
A(f"**Lecture.** JPL table 1 et DE441 (2000–2100) s'accordent à mieux que {f_(t1max,2)}°/siècle pour toutes les planètes : l'un ou l'autre convient pour l'objectif de 1°/siècle. Les taux *séculaires* (Simon 1994) s'en écartent de {sg(secJ)}°/siècle pour Jupiter et de {sg(secS)}°/siècle pour Saturne : sur 2000–2100 la *grande inégalité* Jupiter–Saturne (période ~900 ans) ralentit Jupiter et accélère Saturne. Ces écarts restent sous l'objectif mais en consomment près de la moitié pour Saturne : il faut viser le taux *local*. « Incertitude d'ajustement » = écart entre éléments osculateurs héliocentriques et barycentriques (Jupiter–Pluton ; ≤ 0,005°/siècle estimé pour les planètes intérieures, dont l'ajustement a un résidu RMS ≤ 0,006°) ; « résidu non linéaire » = ce qu'aucun rapport constant ne peut suivre sur le siècle (négligeable).\n")
A("| Grande inégalité (JPL 2b) | Amplitude (°) | Période (ans) | Pente max (°/siècle) |")
A("|---|---|---|---|")
for p_, v in great_ineq.items():
    A(f"| {FR[p_]} | {f_(v['amplitude_deg'],3)} | {f_(v['period_years'],0)} | {f_(v['max_rate_deg_per_century'],3)} |")
A("\n*Schlyter donne pour le seul terme 2M_J − 5M_S : 0,332° (Jupiter) et 0,812° (Saturne), période 918 ans.*\n")
A("### 2.4 Équation du centre (Kepler) et ce qu'un mécanisme en fait\n")
A("Série de Kepler : ν − M = c₁ sin M + c₂ sin 2M + c₃ sin 3M + … avec c₁ = 2e − e³/4, c₂ = 5/4 e², c₃ = 13/12 e³. Le tenon-mortaise d'Anticythère (cercle excentrique vu d'un point décalé, k = 2e) donne k sin M + k²/2 sin 2M + k³/3 sin 3M : le 2ᵉ harmonique vaut 2e² au lieu de 1,25 e². L'équant « bissecté » de Ptolémée (centre décalé de e, point d'équant à 2e) est exact au 2ᵉ ordre en e.\n")
A("| Planète | e | Max ν − M (°) | c₁ (°) | c₂ (°) | Erreur max tenon-mortaise k=2e (°) | Erreur max équant (°) | Erreur max 1er harmonique seul (°) |")
A("|---|---|---|---|---|---|---|---|")
for name in PLANETS + ["pluto"]:
    eo = planets_out[name]["equation_of_centre"]
    A(f"| {FR[name]} | {frnum(JPL_T1[name][0][1])} | {f_(eo['exact_max_deg'],4)} | {f_(eo['series_deg']['c1'],4)} | {f_(eo['series_deg']['c2'],4)} | {f_(eo['pin_and_slot_k_2e_max_err_deg'],4)} | {f_(eo['bisected_equant_max_err_deg'],4)} | {f_(eo['first_harmonic_only_max_err_deg'],4)} |")
A("")
eoc = {n: planets_out[n]["equation_of_centre"] for n in PLANETS}
small = [FR[n] for n in PLANETS if eoc[n]["pin_and_slot_k_2e_max_err_deg"] < 0.15]
A(f"**Conséquence.** Le tenon-mortaise simple (k = 2e) reste sous 0,15° pour {', '.join(small)}. Pour **Mars** il laisse {f_(eoc['mars']['pin_and_slot_k_2e_max_err_deg'],2)}° (équant : {f_(eoc['mars']['bisected_equant_max_err_deg'],2)}°) et pour **Mercure** {f_(eoc['mercury']['pin_and_slot_k_2e_max_err_deg'],2)}° (équant : {f_(eoc['mercury']['bisected_equant_max_err_deg'],2)}°) : Mercure demande un mécanisme plus fidèle que l'équant (3ᵉ harmonique, ou ellipse réelle). Ce sont des erreurs *héliocentriques* : vues de la Terre elles sont amplifiées ou réduites selon le rapport des distances (rapport r/Δ : Mars à l'opposition ×2,5 à ×3,6 ; Mercure ×0,2 à ×0,9).\n")

A("## 3. Lune\n")
A("### 3.1 Arguments moyens (Meeus ch. 47, équinoxe de la date ; T en siècles juliens)\n")
A("| Argument | Valeur à J2000 (°) | Taux (°/siècle) | Contrôle IERS 2010 / Simon 1994 (°/siècle) |")
A("|---|---|---|---|")
ctrl = {"L_prime": lam_trop / 3600, "D": dl["D"] / 3600, "M_sun": dl["l_prime"] / 3600, "M_prime": dl["l"] / 3600,
        "F": dl["F"] / 3600, "Omega": dl["Omega"] / 3600, "perigee": F(MOON_SIMON["varpi_date"][1]) / 3600}
lab = {"L_prime": "L′ longitude moyenne", "D": "D élongation", "M_sun": "M anomalie moyenne du Soleil", "M_prime": "M′ anomalie moyenne de la Lune",
       "F": "F argument de latitude", "Omega": "Ω nœud ascendant", "perigee": "ϖ périgée"}
for k, v in MOON_MEEUS.items():
    A(f"| {lab[k]} | {frnum(v[0])} | {frnum(v[1])} | {f_(ctrl[k],7)} |")
A("")
A("### 3.2 Mois et périodes\n")
A("| Période | Simon 1994 / IERS 2010 (j) | Chapront et al. 2002 (j) | Autre contrôle |")
A("|---|---|---|---|")
other = {"sidereal": "NSSDC 27,3217", "tropical": "IERS table 5.1a : 27,321582", "synodic": "Meeus 49.1 : 29,530588861", "anomalistic": "NASA : 27,554550", "draconic": "IERS table 5.1a : 27,212221"}
MONTH_FR = {"sidereal": "sidéral", "tropical": "tropique", "synodic": "synodique", "anomalistic": "anomalistique", "draconic": "draconitique"}
for k in ("sidereal", "tropical", "synodic", "anomalistic", "draconic"):
    tc = float(MONTHS_CHAPRONT2002[k][1])
    A(f"| Mois {MONTH_FR[k]} | {f_(months[k],9)} | {frnum(MONTHS_CHAPRONT2002[k][0])} {'+' if tc >= 0 else '−'} {frnum(f'{abs(tc):.3g}')} T | {other[k]} |")
A(f"| Révolution des nœuds (tropique) | {f_(node_trop,4)} ({f_(node_trop/TROPICAL_YEAR,4)} ans) | — | IERS 6798,3837 |")
A(f"| Révolution des nœuds (sidérale) | {f_(node_sid,4)} | — | NASA 6793,48 |")
A(f"| Révolution du périgée (tropique) | {f_(apse_trop,4)} ({f_(apse_trop/TROPICAL_YEAR,4)} ans) | — | IERS 3231,4956 |")
A(f"| Révolution du périgée (sidérale) | {f_(apse_sid,4)} | — | NASA dit 3231,6 « par rapport aux étoiles » : c'est en fait la valeur tropique |")
A(f"| Période de l'évection (2D − M′) | {f_(arg_period((2,0,-1,0)),4)} | — | — |")
A("")
A("### 3.3 Inégalités périodiques en longitude (degrés)\n")
A("| Terme | Argument | Meeus 47.A | Brown 1919 | Almanach | Schlyter | Période de l'argument (j) |")
A("|---|---|---|---|---|---|---|")
def argname(a):
    out = ""
    for c, sym in zip(a, ("D", "M", "M′", "F")):
        if not c:
            continue
        mag = "" if abs(c) == 1 else str(abs(c))
        if not out:
            out = ("−" if c < 0 else "") + mag + sym
        else:
            out += (" − " if c < 0 else " + ") + mag + sym
    return out or "—"


TERM_FR = {
    "equation_du_centre": "équation du centre", "evection": "évection", "variation": "variation",
    "equation_du_centre_2e_harmonique": "équation du centre (2ᵉ harmonique)", "equation_annuelle": "équation annuelle",
    "reduction_a_l_ecliptique": "réduction à l'écliptique", "inegalite_parallactique": "inégalité parallactique",
    "terme_principal_sinF": "terme principal", "evection_en_latitude_2D_moins_F": "évection en latitude",
}
for n, a, me, br, aa, sc in MOON_TERMS_LON:
    A(f"| {TERM_FR.get(n, 'terme ' + argname(a))} | {argname(a)} | {f_(me*1e-6,6)} | {f_(br/3600,4) if br is not None else '—'} | {f_(aa,2) if aa is not None else '—'} | {f_(sc,3) if sc is not None else '—'} | {f_(arg_period(a),3)} |")
A("\n*Les termes en M sont multipliés par E = 1 − 0,002516 T (excentricité terrestre décroissante).*\n")
A("### 3.4 Latitude (degrés)\n")
A("| Terme | Argument | Meeus 47.B | Almanach | Schlyter |")
A("|---|---|---|---|---|")
for n, a, me, aa, sc in MOON_TERMS_LAT:
    A(f"| {TERM_FR.get(n, 'terme ' + argname(a))} | {argname(a)} | {f_(me*1e-6,6)} | {f_(aa,2) if aa is not None else '—'} | {f_(sc,3) if sc is not None else '—'} |")
A("\n**Inclinaison : trois valeurs à ne pas confondre.** 5,128° est le coefficient de sin F (à utiliser pour β) ; 5,145° est l'inclinaison moyenne classique (NASA) ; 5,157° est la moyenne de l'inclinaison osculatrice (Simon 1994). L'inclinaison réelle oscille entre ~5,0° et 5,3° (période 173 j).\n")
A("### 3.5 Budget d'erreur de la longitude lunaire (2000–2100)\n")
A("Référence : série complète de Meeus 47.A (60 termes + 3 additifs, précision ~10″). On retire progressivement des termes et on mesure l'erreur restante (pas de 0,05 j sur 100 ans).\n")
A("| Modèle mécanisé | Erreur max (°) | Erreur RMS (°) |")
A("|---|---|---|")
for r in moon_lon_budget:
    A(f"| {r['model']} | {f_(r['max_abs_err_deg'],3)} | {f_(r['rms_err_deg'],3)} |")
A("")
A("| Latitude | Erreur max (°) | Erreur RMS (°) |")
A("|---|---|---|")
for r in moon_lat_budget:
    A(f"| {r['model']} | {f_(r['max_abs_err_deg'],3)} | {f_(r['rms_err_deg'],3)} |")
b_ann, b_red, b_pin = moon_lon_budget[5], moon_lon_budget[6], moon_lon_budget[-1]
A(f"\n**Lecture.** Avec équation du centre (2 harmoniques) + évection + variation + équation annuelle, l'erreur reste sous {f_(b_ann['max_abs_err_deg'],2)}° (RMS {f_(b_ann['rms_err_deg'],2)}°) : l'objectif « ~0,5° » est tenu. La réduction à l'écliptique la ramène à {f_(b_red['max_abs_err_deg'],2)}°, les quatre termes suivants à {f_(moon_lon_budget[7]['max_abs_err_deg'],2)}°. Réaliser l'équation du centre par un tenon-mortaise (comme à Anticythère) au lieu des deux harmoniques exacts coûte {f_(b_pin['max_abs_err_deg'] - b_red['max_abs_err_deg'],2)}° d'erreur max ({f_(b_red['max_abs_err_deg'],2)} → {f_(b_pin['max_abs_err_deg'],2)}°), à cause de son 2ᵉ harmonique trop fort (0,345° au lieu de 0,214°).\n")

A("## 4. Éclipses\n")
A("| Cycle | Lunaisons | Jours | Mois draconitiques | Mois anomalistiques | Années tropiques | Décalage géographique (°, + = vers l'ouest) |")
A("|---|---|---|---|---|---|---|")
for cname, c in cycles.items():
    A(f"| {cname.capitalize()} | {c['synodic_months']} | {f_(c['days'],4)} | {f_(c['draconic_months'],3)} | {f_(c['anomalistic_months'],3)} | {f_(c['tropical_years'],4)} | {f_(c['geographic_shift_deg_west'],1)} |")
A("")
A(f"Contrôles : Saros 6585,32 j (Wikipedia), 6585,3223 j (page NASA : coquille, 223 × 29,530589 = 6585,3213) ; 242 mois draconitiques = 6585,3575 j et 239 anomalistiques = 6585,5375 j (NASA) ; Inex 10 571,9509 j (NASA). Année draconitique : {f_(eclipse_year,6)} j ; saison d'éclipses tous les {f_(eclipse_year/2,2)} j.\n")
A("**Limites écliptiques** (distance Soleil–nœud à la syzygie) :\n")
A("| Type | Min (°) | Max (°) | Source |")
A("|---|---|---|---|")
A("| Éclipse de Soleil (partielle) | 15,39 | 18,59 | NASA (Espenak) ; Wikipedia « 15 à 18° » ; Meeus (via Holmes) 18° 24′ |")
A("| Éclipse de Soleil centrale | ~10 | ~12 | Wikipedia (Littmann, Espenak & Willcox) |")
A(f"| Éclipse de Lune (ombre) | {f_(lun_min,1)} | {f_(lun_max,1)} | calcul géométrique ; Meeus (via Holmes) 12° 08′ |")
A("| Éclipse de Lune pénombrale | 15,3 | 17,1 | NASA (page des éclipses lunaires) |")
A(f"\nEstimation géométrique (sin Δλ = tan β_lim / tan i) : Soleil {f_(sol_min,2)}–{f_(sol_max,2)}°, Lune (ombre) {f_(lun_min,2)}–{f_(lun_max,2)}° — cohérent avec les sources.\n")
A("**Magnitude et hémisphère (Meeus ch. 54).** γ (distance de l'axe de l'ombre au centre de la Terre, en rayons terrestres) ≈ 5,22 sin F + petits termes (Q = 5,2207 − 0,3299 cos M′ ; P = 0,207 sin M − 0,0392 sin M′). Pas d'éclipse si |sin F| > 0,36. Soleil : éclipse centrale si |γ| < 0,9972 ; partielle si |γ| < 1,5433 + u ; magnitude partielle = (1,5433 + u − |γ|)/(0,5461 + 2u). Lune : magnitude d'ombre = (1,0128 − u − |γ|)/0,5450 ; pénombrale = (1,5573 + u − |γ|)/0,5450 (u ≈ 0,0059 + 0,0046 cos M − 0,0182 cos M′). **Signe de γ (donc de sin F près du nœud) = hémisphère** : γ > 0, ombre au nord pour une éclipse de Soleil (Wikipedia « Gamma »). C'est mécanisable : sin F s'obtient par une manivelle–coulisse sur l'arbre draconitique.\n")
A("Chaque Saros décale l'éclipse de ~8 h, soit ~116° vers l'ouest ; l'Exeligmos (3 Saros) la ramène presque à la même longitude.\n")

A("## 5. Satellites galiléens\n")
GAL_FR = {"io": "Io", "europa": "Europe", "ganymede": "Ganymède", "callisto": "Callisto"}
A("| Satellite | n (°/j, Lieske E5) | Période sidérale (j) | NSSDC (j) | Période synodique / Soleil (j) | P du JPL (j) — anomalistique | Périjove (ans) |")
A("|---|---|---|---|---|---|---|")
for m in ("io", "europa", "ganymede", "callisto"):
    gm = gal[m]
    A(f"| {GAL_FR[m]} | {frnum(E5[m])} | {f_(gm['sidereal_period_days'],6)} | {NSSDC_GAL[m].replace('.',',')} | {f_(gm['synodic_period_days_vs_sun'],6)} | {f_(gm['jpl_mean_elements_P_days'],6)} | {f_(gm['apsidal_period_years'],3)} |")
A("")
A(f"**Résonance de Laplace** : n_Io − 3 n_Europe + 2 n_Ganymède = {g_(lap,3)} °/j (E5) ; Φ_L = λ_Io − 3λ_Europe + 2λ_Ganymède = 180° ± libration. n_Io − 2 n_Europe = n_Europe − 2 n_Ganymède = {f_(F(E5['io'])-2*F(E5['europa']),6)} °/j : la ligne des conjonctions Io–Europe rétrograde en {f_(360/(F(E5['io'])-2*F(E5['europa'])),1)} j (conjonctions Io–Europe tous les {f_(360/(F(E5['io'])-F(E5['europa'])),4)} j, Europe–Ganymède tous les {f_(360/(F(E5['europa'])-F(E5['ganymede'])),4)} j ; jamais de triple conjonction). Rapports de périodes : Europe/Io = {f_(F(E5['io'])/F(E5['europa']),5)}, Ganymède/Europe = {f_(F(E5['europa'])/F(E5['ganymede']),5)}, Callisto/Ganymède = {f_(F(E5['ganymede'])/F(E5['callisto']),5)} (hors résonance). Libration : période ~2071 j (Lieske 1998, cité par Celletti et al. 2021), amplitude 0,03° (Sinclair 1975, Wikipedia) à 0,066° (Lieske, cité de seconde main) — **désaccord entre sources, et de toute façon hors de portée d'un engrenage**.\n")
A("**Attention :** la colonne « P » des éléments moyens du JPL (Io 1,762732 j, Europe 3,525463 j) n'est *pas* la période sidérale : c'est la période de l'anomalie moyenne d'une ellipse en précession rapide (périjove forcé d'Io et d'Europe : 1,33 et 1,39 an). Les périodes sidérales sont 1,769138 et 3,551181 j.\n")
ev = galilean_out["earth_view"]
A(f"**Vu de la Terre** : temps de lumière {f_(ev['light_time_minutes_range'][0],1)}–{f_(ev['light_time_minutes_range'][1],1)} min (effet Rømer : ~16,6 min d'écart entre opposition et conjonction) ; l'angle Soleil–Terre vu de Jupiter atteint {f_(ev['max_sun_earth_angle_at_jupiter_deg'],1)}°, ce qui décale les phénomènes d'Io jusqu'à ~1,4 h. Le suiveur héliocentrique → géocentrique de l'orrery peut reproduire ce décalage angulaire, pas le temps de lumière.\n")

A("## 6. Pluton (optionnel, signalé)\n")
plm = planets_out["pluto"]["mean_motion"]
A(f"Planète naine depuis 2006, retirée des tables JPL actuelles (valeurs : table JPL archivée de 2019). e = 0,2488, i = 17,14° ; période sidérale (DE441 2000–2100, barycentrique) {f_(plm['sidereal_period_days'],0)} j vs 90 560 j (NSSDC) et {f_(planets_out['pluto']['mean_motion_jpl_table1']['sidereal_period_days'],0)} j (JPL T1 archivée) ; rapport Pluton/Neptune = {f_(planets_out['pluto']['neptune_resonance_ratio'],4)} (résonance 3:2). Équation du centre max {f_(planets_out['pluto']['equation_of_centre']['exact_max_deg'],2)}° : le tenon-mortaise simple ferait {f_(planets_out['pluto']['equation_of_centre']['pin_and_slot_k_2e_max_err_deg'],1)}° d'erreur.\n")

A("## 7. Ce qui est négligeable ou hors de portée\n")
A("| Effet | Amplitude | ≈ degrés |")
A("|---|---|---|")
for x in data["negligible_or_out_of_reach"]:
    A(f"| {fr(x['effect'])} | {fr(x['amplitude'])} | {f_(x['deg'],4)} |")
A("")

A("## 8. Écarts entre sources (à retenir)\n")
A("1. **Saturne : période sidérale 10 759 j ou 10 756 j ?** Le NSSDC (mis à jour en 2025) donne 10 755,70 j, proche du taux *local* (JPL T1 : 10 755,93 j ; DE441 2000–2100 : 10 755,18 j) ; la v1 utilisait l'ancienne valeur NSSDC 10 759,22 j, qui correspond au taux séculaire (Simon 1994 : 10 759,2 j). Les deux sont « justes » : la grande inégalité Jupiter–Saturne fait varier la vitesse apparente.")
A("2. **Meeus table 31.A vs Simon 1994** : +0,277″/siècle sur certaines planètes (Meeus garde la constante de précession IAU 1976). Négligeable.")
A("3. **Repère de date ≠ J2000 + p_A** pour λ planétaire : jusqu'à 2,3″/siècle (Mercure), dû au mouvement de l'écliptique. Négligeable.")
A("4. **Obliquité** : IAU 2006 (84 381,406″) vs IAU 1980 (84 381,448″) : 0,042″, redéfinition de l'écliptique.")
A("5. **Mois lunaires** : Simon 1994 vs Chapront 2002 : < 1×10⁻⁸ j.")
A("6. **Périgée lunaire** : la page NASA donne 3231,6 j « par rapport aux étoiles », mais c'est la période tropique (3231,50 j) ; la période sidérale est 3232,60 j.")
A("7. **Saros** : la page NASA écrit 6585,3223 j au lieu de 6585,3213 j (coquille de 1,4 min).")
A("8. **Inclinaison lunaire** : 5,128° (coefficient de sin F), 5,145° (moyenne classique), 5,157° (moyenne osculatrice).")
A("9. **Libration de Laplace** : 0,03° (Sinclair 1975) vs 0,066° (Lieske, de seconde main) ; période 2071 j.")
A("10. **JPL « P » des satellites** : période anomalistique, pas sidérale (Io −0,36 %, Europe −0,72 %).")
A("11. **Limites écliptiques** : les valeurs publiées dépendent des définitions (nœud vrai/moyen, mouvement pendant l'éclipse, pénombre) : 15,4–18,6° (Soleil), ~9,6–12,2° (Lune, ombre), 15,3–17,1° (Lune, pénombre).")
A("12. **F14 de l'IERS (p_A = 0,02438175 rad/siècle = 5029,10″)** est l'ancienne valeur, gardée seulement comme argument de nutation.\n")

A("**Valeurs à une seule source (non recoupées)** : année de l'équinoxe de mars 365,242374 j (Meeus & Savoie via Wikipedia) ; plage d'obliquité à long terme 22,04°–24,50° et période 41 040 ans (Laskar via Wikipedia) ; plage d'inclinaison lunaire 5,0°–5,3° (NASA) ; ΔT 2026 = 69,1 s (USNO, prédiction) ; limites d'éclipse centrale ~10–12° (Wikipedia) et pénombrale 15,3–17,1° (NASA) ; amplitude de libration de Laplace (deux valeurs discordantes). Les coefficients γ de Meeus ch. 54 ne sont recoupés que pour les seuils (0,9972 ; ~1,55).\n")
A("**Régénérer** : `python3.13 v2/tools/fetch_horizons_rates.py` (réseau, JPL Horizons) puis `python3.13 v2/tools/build_constants.py` (hors ligne), avec le Python de Blender.\n")
A("## 9. Toutes les vérifications croisées\n")
A("| Statut | Comparaison | A | Source A | B | Source B | A − B | Tolérance | Unité |")
A("|---|---|---|---|---|---|---|---|---|")
icon = {"ok": "ok", "explique": "expliqué", "ATTENTION": "**à surveiller**"}
for c in CHECKS:
    A(f"| {icon[c['status']]} | {c['label']} | {g_(c['a'],12)} | {c['source_a']} | {g_(c['b'],12)} | {c['source_b']} | {g_(c['diff_a_minus_b'],3)} | {g_(c['tolerance'],2)} | {c['unit']} |")
A("")
notes = [c for c in CHECKS if c["note"]]
if notes:
    A("**Notes sur les écarts :**\n")
    for c in notes:
        A(f"- *{c['label']}* — {c['note']}")
    A("")
A("## 10. Sources\n")
for k, s in SOURCES.items():
    urls = " ; ".join(s[u] for u in ("url", "url2", "url3", "url4") if u in s)
    snap = f" — copie locale : `{s['snapshot']}`" if "snapshot" in s else ""
    A(f"- **{k}** — {s['cite'].rstrip('.')}. {urls}{snap}")
A("")
OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

print(f"wrote {OUT_JSON} ({OUT_JSON.stat().st_size} bytes)")
print(f"wrote {OUT_MD} ({OUT_MD.stat().st_size} bytes)")
print(f"checks: {len(CHECKS)} total, {n_ok} ok, {n_exp} explained, {n_att} ATTENTION")
for c in CHECKS:
    if c["status"] != "ok":
        print(f"  [{c['status']}] {c['id']}: a={c['a']} b={c['b']} diff={c['diff_a_minus_b']} tol={c['tolerance']}")
