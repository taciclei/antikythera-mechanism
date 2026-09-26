import json, sys, numpy as np, soundfile as sf
from scipy.signal import stft
def word(src, eng, pat, nth=0):
    ws = json.load(open(f'takes/{src}.{eng}.json'))['words']
    m = [w for w in ws if pat in w['word'].lower()]
    return m[nth] if len(m) > nth else None
def prof(src, s, e):
    a, sr = sf.read(f'takes/{src}.wav'); seg = a[int(max(0,s)*sr):int(e*sr)]
    f, t, Z = stft(seg, sr, nperseg=480, noverlap=240)
    P = np.abs(Z)**2
    tot = P.sum(0)+1e-12; low = P[f < 400].sum(0); hi = P[f > 3500].sum(0)
    en = 10*np.log10(tot/ tot.max())
    out = ''
    for k in range(P.shape[1]):
        if en[k] < -30: out += '.'
        elif hi[k]/tot[k] > 0.4: out += 'Z' if low[k]/tot[k] > 0.1 else 'S'
        else: out += 'v'
    return out
for src, eng, pat, n in [('ch1_t2','pk','phases',0),('ch1_t1','pk','face',0),('ch1_t2','stt','face',0),('c1u01_t1','pk','phases',0),
                         ('ch3_t2','pk','zodiaque',0),('ch3_t2','pk','superpos',0),('ch3_t2','pk','sphère',0),('ch4_t1','pk','sphères',0),('ch3_t2','pk','opposée',0)]:
    w = word(src, eng, pat, n)
    if w: print(f"{src:9s} {pat:10s} {w['start']:.2f}-{w['end']:.2f}", prof(src, w['start']-0.05, w['end']+0.08))
    else: print(src, pat, 'absent')
