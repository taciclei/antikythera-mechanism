"""Deuxième avis STT : Parakeet TDT 0.6B v3 (multilingue, dont le français), horodatage par mot.
Usage: stt2.py a.wav ...  -> a.pk.json"""
import sys, json, time, pathlib
import numpy as np, soundfile as sf, soxr
import mlx.core as mx
from mlx_audio.stt.utils import load

t0 = time.time()
model = load("mlx-community/parakeet-tdt-0.6b-v3")
print(f"parakeet chargé en {time.time()-t0:.1f}s", flush=True)
for p in sys.argv[1:]:
    p = pathlib.Path(p)
    a, sr = sf.read(p, dtype='float32')
    if a.ndim > 1: a = a.mean(1)
    a = soxr.resample(a, sr, 16000)
    pad = np.zeros(8000, np.float32)
    a = np.concatenate([pad, a, pad])
    import os
    ck = float(os.environ.get("PK_CHUNK", "0")) or None
    r = model.generate(mx.array(a), chunk_duration=ck, overlap_duration=2.0 if ck else None)
    words = []
    for s in r.sentences:
        for t in s.tokens:
            txt = t.text
            if not words or txt.startswith(' ') or txt.startswith('▁'):
                words.append(dict(word=txt.replace('▁', ' '), start=t.start - 0.5, end=t.end - 0.5))
            else:
                words[-1]['word'] += txt; words[-1]['end'] = t.end - 0.5
    for w in words:
        w['start'] = round(w['start'], 3); w['end'] = round(w['end'], 3); w['p'] = 1.0
    p.with_suffix('.pk.json').write_text(json.dumps(dict(file=p.name, text=r.text.strip(), words=words), ensure_ascii=False, indent=1))
    print(f"{p.name}: {r.text.strip()}", flush=True)
print('FIN', flush=True)
