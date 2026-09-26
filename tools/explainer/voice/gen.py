"""Génère des prises TTS Voxtral (fr_female).
Usage: gen.py JOBS.json   où JOBS = [{"id":..., "take":k, "text":...}, ...]
Sortie: takes/<id>_t<k>.wav (float32, 24 kHz) + .json"""
import sys, time, json, zlib, pathlib
import numpy as np, soundfile as sf
import mlx.core as mx
from mlx_audio.tts.utils import load

W = pathlib.Path(__file__).parent
jobs = json.loads(pathlib.Path(sys.argv[1]).read_text())
VOICE = 'fr_female'
t0 = time.time()
model = load("mlx-community/Voxtral-4B-TTS-2603-mlx-bf16")
print(f"modèle chargé en {time.time()-t0:.1f}s", flush=True)
for j in jobs:
    out = W / 'takes' / f"{j['id']}_t{j['take']}.wav"
    if out.exists() and not j.get('force'):
        print('existe', out.name); continue
    seed = zlib.crc32(f"{j['id']}:{j['take']}".encode()) & 0x7fffffff
    mx.random.seed(seed)
    temp = j.get('temperature', 0.8)
    t1 = time.time(); chunks = []; sr = 24000
    for r in model.generate(text=j['text'], voice=VOICE, temperature=temp):
        chunks.append(np.array(r.audio, dtype=np.float32)); sr = getattr(r, 'sample_rate', sr) or sr
    a = np.concatenate(chunks)
    sf.write(out, a, sr, subtype='FLOAT')
    meta = dict(id=j['id'], take=j['take'], text=j['text'], voice=VOICE, seed=seed,
                temperature=temp, sr=sr, dur=len(a)/sr, gen_s=time.time()-t1)
    out.with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"{out.name}: {len(a)/sr:.2f}s en {time.time()-t1:.1f}s", flush=True)
    mx.clear_cache()
print('FIN', f"{time.time()-t0:.0f}s", flush=True)
