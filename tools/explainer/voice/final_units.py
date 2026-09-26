"""QA finale phrase par phrase : découpe chaque unité dans ch1..ch7.wav FINAUX (positions
d'assembly.json), transcrit avec les deux STT, WER agrégé par chapitre."""
import json, pathlib, subprocess, sys
import numpy as np, soundfile as sf
import textnorm as T

W = pathlib.Path(__file__).parent
OUT = pathlib.Path('/Users/tsousa/antikythera/build/out/explainer/voice')
D = W / 'final' / 'units'; D.mkdir(parents=True, exist_ok=True)
PY = '/Users/tsousa/voxtral-tts/bin/python'
asm = json.loads((W / 'assembly.json').read_text())
files = []
for u in asm:
    a, sr = sf.read(OUT / f"ch{u['ch']}.wav", dtype='float32')
    s = max(0, int((u['start'] - 0.1) * sr)); e = min(len(a), int((u['start'] + u['dur'] + 0.1) * sr))
    p = D / f"{u['id']}.wav"; sf.write(p, a[s:e], sr, subtype='PCM_16'); files.append(str(p))
if '--skip' not in sys.argv:
    subprocess.run([PY, str(W / 'stt.py')] + files, check=True, capture_output=True)
    subprocess.run([PY, str(W / 'stt2.py')] + files, check=True, capture_output=True)
res = {}
for u in asm:
    r = res.setdefault(u['ch'], dict(n=0, whisper=0, parakeet=0, best=0, whisper_o=0, parakeet_o=0, errs=[]))
    ref = T.pwords(u['tts']); r['n'] += len(ref)
    e = {}
    for eng, ext in (('whisper', 'stt'), ('parakeet', 'pk')):
        hyp = json.loads((D / f"{u['id']}.{ext}.json").read_text())['text']
        S, Dl, I, ops = T.align(ref, T.pwords(hyp))
        e[eng] = S + Dl + I; r[eng] += e[eng]
        r[eng + '_o'] += round(T.wer(u['tts'], hyp)['wer'] * len(T.words(u['tts'])))
        if e[eng]: r['errs'].append((u['id'], eng, [(o, a_, b) for o, a_, b in ops if o != '='], hyp))
    r['best'] += min(e.values())
(W / 'qa_final_units.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
tot = dict(n=0, whisper=0, parakeet=0, best=0)
for ch, r in sorted(res.items()):
    for k in tot: tot[k] += r[k]
    print(f"ch{ch}: {r['n']} mots | WER phon Whisper {100*r['whisper']/r['n']:.1f}% Parakeet {100*r['parakeet']/r['n']:.1f}% "
          f"meilleur des deux {100*r['best']/r['n']:.1f}% | WER ortho W {100*r['whisper_o']/r['n']:.1f}% P {100*r['parakeet_o']/r['n']:.1f}%")
    for x in r['errs']: print('     ', x)
print('TOTAL', {k: (f"{100*v/tot['n']:.1f}%" if k != 'n' else v) for k, v in tot.items()})
