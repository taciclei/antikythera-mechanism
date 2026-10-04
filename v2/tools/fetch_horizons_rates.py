#!/usr/bin/env python3
"""Fetch DE441 osculating heliocentric elements (JPL Horizons API) for the
planetary system barycenters over 2000-2100 and fit linear mean rates.

Output: v2/research/sources/horizons/*.csv.gz (raw rows, reproducible)
        v2/research/sources/horizons/horizons_rates_2000_2100.json (fits)
These fits are an independent check of the mean motions in the actual target
window of the machine; build_constants.py reads the JSON if it exists.

Run with Blender's Python (numpy):
  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 v2/tools/fetch_horizons_rates.py
"""
from __future__ import annotations

import gzip
import json
import subprocess
import urllib.parse
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[1]
OUT = V2 / "research" / "sources" / "horizons"
BODIES = {"mercury": "1", "venus": "2", "earth": "3", "mars": "4", "jupiter": "5",
          "saturn": "6", "uranus": "7", "neptune": "8", "pluto": "9"}
START, STOP, STEP = "2000-01-01", "2100-01-01", "10 d"
API = "https://ssd.jpl.nasa.gov/api/horizons.api"


def query(cmd: str, center: str = "500@10") -> str:
    params = {
        "format": "text", "COMMAND": f"'{cmd}'", "OBJ_DATA": "'NO'", "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'ELEMENTS'", "CENTER": f"'{center}'", "START_TIME": f"'{START}'",
        "STOP_TIME": f"'{STOP}'", "STEP_SIZE": f"'{STEP}'", "REF_PLANE": "'ECLIPTIC'",
        "REF_SYSTEM": "'ICRF'", "CSV_FORMAT": "'YES'", "OUT_UNITS": "'AU-D'",
    }
    url = API + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    txt = subprocess.run(["curl", "-sS", "-m", "120", url], check=True, capture_output=True, text=True).stdout
    return url, txt


def parse(txt: str):
    body = txt.split("$$SOE")[1].split("$$EOE")[0]
    rows = []
    for line in body.strip().splitlines():
        c = [x.strip() for x in line.split(",")]
        # JDTDB, date, EC, QR, IN, OM, W, Tp, N, MA, TA, A, AD, PR
        rows.append((float(c[0]), float(c[2]), float(c[4]), float(c[5]), float(c[6]), float(c[9]), float(c[11])))
    return np.array(rows)


def fit(t_cy, y):
    A = np.vstack([t_cy, np.ones_like(t_cy)]).T
    (slope, icpt), *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - (slope * t_cy + icpt)
    return float(slope), float(icpt), float(np.sqrt(np.mean(res ** 2))), float(np.max(np.abs(res)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"source": "JPL Horizons API (DE441), osculating heliocentric elements of the system barycenters, ecliptic & mean equinox of J2000, TDB",
               "api": API, "span": [START, STOP], "step": STEP, "bodies": {}}
    for name, cmd in BODIES.items():
        url, txt = query(cmd)
        if "$$SOE" not in txt:
            raise SystemExit(f"Horizons error for {name}: {txt[:500]}")
        a = parse(txt)
        jd, ec, inc, om, w, ma, sma = a.T
        L = np.unwrap(np.radians(om + w + ma))
        varpi = np.unwrap(np.radians(om + w))
        node = np.unwrap(np.radians(om))
        t = (jd - 2451545.0) / 36525.0
        sL, iL, rmsL, maxL = fit(t, np.degrees(L))
        sP, iP, rmsP, _ = fit(t, np.degrees(varpi))
        sN, iN, rmsN, _ = fit(t, np.degrees(node))
        results["bodies"][name] = {
            "command": cmd, "query_url": url, "n_rows": int(len(jd)),
            "L_rate_deg_per_cy": sL, "L_at_J2000_deg": iL % 360, "L_fit_rms_deg": rmsL, "L_fit_max_deg": maxL,
            "varpi_rate_deg_per_cy": sP, "varpi_at_J2000_deg": iP % 360, "varpi_fit_rms_deg": rmsP,
            "Omega_rate_deg_per_cy": sN, "Omega_at_J2000_deg": iN % 360, "Omega_fit_rms_deg": rmsN,
            "e_mean": float(np.mean(ec)), "e_rate_per_cy": fit(t, ec)[0],
            "i_mean_deg": float(np.mean(inc)), "a_mean_au": float(np.mean(sma)),
        }
        with gzip.open(OUT / f"horizons_{name}_2000_2100.csv.gz", "wt") as f:
            f.write("# " + url + "\n# JDTDB,EC,IN,OM,W,MA,A\n")
            for r in a:
                f.write(",".join(f"{v:.10f}" for v in r) + "\n")
        if name in ("jupiter", "saturn", "uranus", "neptune", "pluto"):
            # barycentric osculating elements (centre = solar-system barycentre): no solar wobble
            urlb, txtb = query(cmd, "500@0")
            b = parse(txtb)
            tb = (b[:, 0] - 2451545.0) / 36525.0
            Lb = np.degrees(np.unwrap(np.radians(b[:, 3] + b[:, 4] + b[:, 5])))
            sb, ib, rmsb, maxb = fit(tb, Lb)
            results["bodies"][name]["barycentric"] = {"query_url": urlb, "L_rate_deg_per_cy": sb,
                                                       "L_at_J2000_deg": ib % 360, "L_fit_rms_deg": rmsb}
            results["bodies"][name]["L_rate_uncertainty_deg_per_cy"] = abs(sb - sL)
            print(f"{name:8s} L' = {sL:.6f} (helio, rms {rmsL:.3f})  {sb:.6f} (bary, rms {rmsb:.3f}) deg/cy")
        else:
            print(f"{name:8s} L' = {sL:.6f} deg/cy  rms {rmsL:.3f} deg  (n={len(jd)})")
    (OUT / "horizons_rates_2000_2100.json").write_text(json.dumps(results, indent=1) + "\n")


if __name__ == "__main__":
    main()
