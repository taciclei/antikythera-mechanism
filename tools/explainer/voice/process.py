"""Assemble les prises choisies en ch1..ch7.wav, narration_full.wav et timing.json.
- passe-haut 60 Hz, découpe du silence, fondus 5 ms
- nivellement partiel entre unités (75 % de l'écart à la médiane, borné à ±3 dB)
- pauses entre phrases (units.py), 0,15 s de silence en tête et en fin de chapitre
- une seule correction de gain pour tout le film : -16 LUFS intégrés, crête vraie <= -1 dBTP
Écrit aussi work/assembly.json (position de chaque unité dans son chapitre)."""
import json, pathlib
import numpy as np, soundfile as sf, soxr, pyloudnorm as pyln
from scipy.signal import butter, sosfiltfilt
from scipy.ndimage import minimum_filter1d, uniform_filter1d
import units as U

W = pathlib.Path(__file__).parent
OUT = pathlib.Path('/Users/tsousa/antikythera/build/out/explainer/voice')
SR = 24000
LEAD = TAIL = 0.15
GAP = 0.8
TARGET = -16.0
TP_MAX = -1.0
FADE = int(0.005 * SR)
meter = pyln.Meter(SR)



def db(x):
    return 20 * np.log10(np.maximum(x, 1e-10))


def trim(a):
    """Renvoie (début, fin) en échantillons de la parole, avec marges."""
    hop = int(0.01 * SR)
    n = len(a) // hop
    rms = np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    rdb = db(rms)
    thr = max(-55.0, rdb.max() - 42.0)
    idx = np.where(rdb > thr)[0]
    s = max(0, idx[0] * hop - int(0.03 * SR))
    e = min(len(a), (idx[-1] + 1) * hop + int(0.07 * SR))
    return s, e


def fade(a):
    r = np.linspace(0, 1, FADE, dtype=np.float32)
    a = a.copy(); a[:FADE] *= r; a[-FADE:] *= r[::-1]
    return a


def true_peak_db(a):
    up = soxr.resample(a.astype(np.float64), SR, SR * 4)
    return db(np.abs(up).max())


def limit(a, thr_db):
    """Limiteur à anticipation : gain <= requis à chaque échantillon, sans saut."""
    thr = 10 ** (thr_db / 20)
    g = np.minimum(1.0, thr / np.maximum(np.abs(a), 1e-9))
    w = int(0.004 * SR) * 2 + 1
    g = minimum_filter1d(g, w, mode='nearest')
    g = uniform_filter1d(g, w, mode='nearest')
    rel = int(0.05 * SR) * 2 + 1          # relâchement plus doux
    g2 = uniform_filter1d(minimum_filter1d(g, rel, mode='nearest'), rel, mode='nearest')
    gg = np.minimum(g, g2)
    GR.append((float(np.mean(gg < 0.891)), float(np.mean(gg < 0.708)), float(20 * np.log10(gg.min()))))
    return a * gg


GR = []
sos = butter(2, 60, 'highpass', fs=SR, output='sos')
units = U.units()
plan = {p['id']: p for p in json.loads((W / 'plan.json').read_text())}
_cache = {}


def source(path):
    if path not in _cache:
        a, sr = sf.read(W / path, dtype='float32'); assert sr == SR
        _cache[path] = sosfiltfilt(sos, a).astype(np.float32)
    return _cache[path]


proc = {}
for u in units:
    pl = plan[u['id']]
    assert pl['tts'] == u['tts'], u['id']
    src = source(pl['src'])
    s0, e0 = int(round(pl['s'] * SR)), int(round(pl['e'] * SR))
    a = src[s0:e0]
    s, e = trim(a)
    seg = fade(a[s:e])
    L = meter.integrated_loudness(np.concatenate([seg, np.zeros(int(0.4 * SR), np.float32)]) if len(seg) < 0.4 * SR else seg)
    proc[u['id']] = dict(a=seg, take=pl['src'], trim_start=(s0 + s) / SR, lufs=L)

# 1) chaque prise source est ramenée à la médiane (écarts de niveau entre prises du TTS)
# 2) correction résiduelle douce par phrase : 50 % de l'écart, bornée à ±2 dB
take_lufs = {}
for v in proc.values():
    if v['take'] not in take_lufs:
        take_lufs[v['take']] = meter.integrated_loudness(sf.read(W / v['take'], dtype='float32')[0])
med = float(np.median([v['lufs'] for v in proc.values()]))
ref = float(np.median([v['lufs'] - take_lufs[v['take']] for v in proc.values()]))
for v in proc.values():
    g_take = med - ref - take_lufs[v['take']]
    resid = med - (v['lufs'] + g_take)
    g = float(g_take + np.clip(0.5 * resid, -2, 2))
    v['gain_db'] = g
    v['a'] = v['a'] * 10 ** (g / 20)

chapters, asm = [], []
for ci in range(1, 8):
    cu = [u for u in units if u['ch'] == ci]
    parts = [np.zeros(int(LEAD * SR), np.float32)]
    t = LEAD
    for u in cu:
        v = proc[u['id']]
        a = v['a']
        asm.append(dict(id=u['id'], ch=ci, take=v['take'], start=round(t, 4), dur=round(len(a) / SR, 4),
                        trim_start=round(v['trim_start'], 4), gain_db=round(v['gain_db'], 2),
                        unit_lufs=round(v['lufs'], 2), orig=u['orig'], tts=u['tts']))
        parts.append(a); t += len(a) / SR
        if u['pause'] > 0:
            parts.append(np.zeros(int(round(u['pause'] * SR)), np.float32)); t += int(round(u['pause'] * SR)) / SR
    parts.append(np.zeros(int(TAIL * SR), np.float32))
    chapters.append(np.concatenate(parts))


def full(chs):
    g = np.zeros(int(GAP * SR), np.float32)
    out = []
    for i, c in enumerate(chs):
        if i: out.append(g)
        out.append(c)
    return np.concatenate(out)


# gain global, puis limiteur si besoin, puis réajustement
for it in range(3):
    L = meter.integrated_loudness(full(chapters))
    chapters = [c * 10 ** ((TARGET - L) / 20) for c in chapters]
    tp = max(true_peak_db(c) for c in chapters)
    print(f"passe {it}: {L:.2f} LUFS avant gain, crête vraie après gain {tp:.2f} dBTP")
    if tp <= TP_MAX + 0.05 and abs(L - TARGET) < 0.05:
        break
    chapters = [limit(c, TP_MAX - 0.3) for c in chapters]

print('limiteur (part >1 dB, part >3 dB, max dB) par chapitre et par passe :', [tuple(round(x, 4) for x in g) for g in GR])
rng = np.random.default_rng(7)


def to16(a):
    d = (rng.random(len(a)) - rng.random(len(a))) / 32768.0   # dither TPDF 1 LSB
    return np.clip(np.round((a + d) * 32767), -32768, 32767).astype(np.int16)


OUT.mkdir(parents=True, exist_ok=True)
timing = dict(chapters=[], gap_between_chapters=GAP, sample_rate=SR,
              lead_tail_silence=LEAD, voice='Voxtral-4B-TTS-2603 (MLX bf16), voix fr_female')
t = 0.0
ints = []
for i, c in enumerate(chapters, 1):
    x = to16(c); ints.append(x)
    sf.write(OUT / f'ch{i}.wav', x, SR, subtype='PCM_16')
    d = len(x) / SR
    timing['chapters'].append(dict(n=i, file=f'ch{i}.wav', duration=round(d, 3), start=round(t, 3)))
    t += d + GAP
gap16 = np.zeros(int(GAP * SR), np.int16)
fx = np.concatenate([p for i, x in enumerate(ints) for p in ((gap16, x) if i else (x,))])
sf.write(OUT / 'narration_full.wav', fx, SR, subtype='PCM_16')
ff = fx.astype(np.float32) / 32768
timing['total_duration'] = round(len(fx) / SR, 3)
timing['loudness_lufs_integrated'] = round(meter.integrated_loudness(ff), 2)
timing['true_peak_dbtp'] = round(true_peak_db(ff), 2)
(OUT / 'timing.json').write_text(json.dumps(timing, ensure_ascii=False, indent=1))
(W / 'assembly.json').write_text(json.dumps(asm, ensure_ascii=False, indent=1))
print(json.dumps(timing, ensure_ascii=False, indent=1))
