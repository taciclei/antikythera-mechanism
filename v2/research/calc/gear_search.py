"""Exhaustive search of compound gear trains (teeth 10..220) approximating a ratio."""
import numpy as np
from functools import lru_cache

ZMIN, ZMAX = 10, 220

@lru_cache(maxsize=None)
def _products(k):
    """Boolean table: which integers are a product of k factors in [ZMIN, ZMAX]."""
    z = np.arange(ZMIN, ZMAX + 1, dtype=np.int64)
    vals = z.copy()
    for _ in range(k - 1):
        vals = np.unique((vals[:, None]*z[None, :]).ravel())
    table = np.zeros(int(vals.max()) + 1, dtype=bool); table[vals] = True
    return table, vals

def factorise(n, k):
    """One factorisation of n into k factors in [ZMIN, ZMAX] (descending), or None."""
    if k == 1:
        return [n] if ZMIN <= n <= ZMAX else None
    for f in range(ZMAX, ZMIN - 1, -1):
        if n % f == 0:
            rest = factorise(n//f, k - 1)
            if rest: return [f] + rest
    return None

def best_trains(r, k, top=5):
    """Best k-pair trains for ratio r = (driver teeth product)/(driven teeth product)."""
    table, vals = _products(k)
    Q = vals.astype(np.float64)
    N = np.rint(r*Q).astype(np.int64)
    ok = (N >= ZMIN**k) & (N < table.size)
    ok[ok] = table[N[ok]]
    Qs, Ns = vals[ok], N[ok]
    err = np.abs(Ns/Qs - r)/r
    idx = np.argsort(err)[:top*4]
    out, seen = [], set()
    for i in idx:
        n, q = int(Ns[i]), int(Qs[i])
        from math import gcd
        g = gcd(n, q)
        if (n//g, q//g) in seen: continue
        seen.add((n//g, q//g))
        out.append({'num': n, 'den': q, 'drivers': factorise(n, k), 'driven': factorise(q, k), 'rel_err': float(err[i])})
        if len(out) >= top: break
    return out
