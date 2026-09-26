"""Transcrit des WAV avec Whisper large-v3-turbo (MLX), en français, horodatage par mot.
Usage: stt.py a.wav b.wav ...   -> a.stt.json ...
Pas de prompt initial ni de hotwords : on ne veut pas aider Whisper à deviner
un mot mal prononcé."""
import sys, json, time, pathlib
import numpy as np, soundfile as sf, soxr
from mlx_audio.stt.utils import load

MODEL = "mlx-community/whisper-large-v3-turbo-asr-fp16"
t0 = time.time()
model = load(MODEL)
print(f"whisper chargé en {time.time()-t0:.1f}s", flush=True)
for p in sys.argv[1:]:
    p = pathlib.Path(p)
    out = p.with_suffix('.stt.json')
    a, sr = sf.read(p, dtype='float32')
    if a.ndim > 1: a = a.mean(1)
    if sr != 16000: a = soxr.resample(a, sr, 16000)
    # 0,5 s de silence de chaque côté : Whisper coupe parfois le premier mot sinon
    pad = np.zeros(8000, np.float32)
    a = np.concatenate([pad, a, pad])
    r = model.generate(a, language='fr', word_timestamps=True, temperature=0.0,
                       condition_on_previous_text=False, verbose=None)
    words = []
    for s in (r.segments or []):
        for w in s.get('words', []) or []:
            words.append(dict(word=w['word'], start=round(float(w['start']) - 0.5, 3),
                              end=round(float(w['end']) - 0.5, 3), p=round(float(w.get('probability', 0)), 3)))
    out.write_text(json.dumps(dict(file=p.name, text=r.text.strip(), words=words), ensure_ascii=False, indent=1))
    print(f"{p.name}: {r.text.strip()}", flush=True)
print('FIN', flush=True)
