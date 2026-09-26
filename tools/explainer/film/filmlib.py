"""Shared helpers of the film pipeline (pure Python 3, no Blender, no numpy): paths, time <-> frame, and an EXACT
re-implementation of Blender's F-curve key interpolation (CONSTANT, LINEAR and the Robert Penner easings SINE /
QUAD / CUBIC of source/blender/blenlib/intern/easing.cc), so that timeline.py knows, frame by frame, the value
Blender will evaluate for AM_Controller["crank"] / ["explode"] / ["patina"] (keys are placed on whole frames).

Film time: frame f (1-based, Blender) starts at t = (f - 1) / FPS seconds.
"""
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
EXPLAINER = ROOT / 'build' / 'out' / 'explainer'
FILM = EXPLAINER / 'film'
VOICE = EXPLAINER / 'voice'
DIAGRAMS = EXPLAINER / 'diagrams'
FPS = 25
WIDTH, HEIGHT = 1920, 1080


def frame_of(t):
    """Film frame (1-based) that starts closest to film time t (s).  Halves round UP (not Python's round-half-even,
    which made F(t + n / FPS) differ from F(t) + n), with a 1e-6 frame tolerance for float noise."""
    return int(math.floor(t * FPS + 0.5 + 1e-6)) + 1


def time_of(f):
    return (f - 1) / FPS


def fmt_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return '%02d:%02d:%02d,%03d' % (h, m, s, ms)


def f32(x):
    """Round to IEEE float32 (Blender stores key values and reads driver variables in float32)."""
    import struct
    return struct.unpack('f', struct.pack('f', float(x)))[0]


# ----------------------------------------------------------------------------- Blender easing (easing.cc)
def _sine(t, b, c, d, mode):
    if mode == 'EASE_IN':
        return -c * math.cos(t / d * (math.pi / 2)) + c + b
    if mode == 'EASE_OUT':
        return c * math.sin(t / d * (math.pi / 2)) + b
    return -c / 2 * (math.cos(math.pi * t / d) - 1) + b


def _quad(t, b, c, d, mode):
    if mode == 'EASE_IN':
        t /= d
        return c * t * t + b
    if mode == 'EASE_OUT':
        t /= d
        return -c * t * (t - 2) + b
    t /= d / 2
    if t < 1.0:
        return c / 2 * t * t + b
    t -= 1.0
    return -c / 2 * (t * (t - 2) - 1) + b


def _cubic(t, b, c, d, mode):
    if mode == 'EASE_IN':
        t /= d
        return c * t * t * t + b
    if mode == 'EASE_OUT':
        t = t / d - 1
        return c * (t * t * t + 1) + b
    t /= d / 2
    if t < 1.0:
        return c / 2 * t * t * t + b
    t -= 2.0
    return c / 2 * (t * t * t + 2) + b


EASERS = {'SINE': _sine, 'QUAD': _quad, 'CUBIC': _cubic}


def eval_keys(keys, frame):
    """keys: sorted list of dicts {f: int frame, v: value, ipo: CONSTANT|LINEAR|SINE|QUAD|CUBIC,
    ease: EASE_IN|EASE_OUT|EASE_IN_OUT} ; the interpolation of a key applies to the span AFTER it (Blender).
    Constant extrapolation outside."""
    if frame <= keys[0]['f']:
        return keys[0]['v']
    if frame >= keys[-1]['f']:
        return keys[-1]['v']
    lo, hi = 0, len(keys) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if keys[mid]['f'] <= frame:
            lo = mid
        else:
            hi = mid
    a, b = keys[lo], keys[hi]
    if frame == a['f']:
        return a['v']
    ipo = a.get('ipo', 'LINEAR')
    t = frame - a['f']
    d = b['f'] - a['f']
    if ipo == 'CONSTANT':
        return a['v']
    if ipo == 'LINEAR':
        return a['v'] + (b['v'] - a['v']) * t / d
    return EASERS[ipo](t, a['v'], b['v'] - a['v'], d, a.get('ease', 'EASE_IN_OUT'))


def ease01(u, kind='SINE_IN_OUT'):
    """Normalised easing 0..1 -> 0..1 for camera moves (same curves as the key interpolations)."""
    u = min(max(u, 0.0), 1.0)
    if kind == 'LINEAR':
        return u
    ipo, _, mode = kind.partition('_')
    mode = mode or 'IN_OUT'
    return EASERS[ipo](u, 0.0, 1.0, 1.0, 'EASE_' + mode)


def counter_text(crank):
    """Compteur du film : « Temps écoulé : X ans Y j » (Y = partie décimale x 365,2422, arrondie à l'entier inférieur) ;
    mêmes arrondis que overlay.counter_text, qui dessine la valeur."""
    c = max(0.0, float(crank))
    y = int(math.floor(c))
    d = min(int(math.floor((c - y) * 365.2422 + 1e-9)), 365)
    return 'Temps écoulé : %d %s %d j' % (y, 'an' if y < 2 else 'ans', d)
