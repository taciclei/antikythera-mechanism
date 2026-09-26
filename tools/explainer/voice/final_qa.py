"""QA finale : transcrit ch1..ch7.wav (copies dans final/) avec les deux STT et calcule le WER
par chapitre contre le texte envoyé au TTS (orthographique et phonétique) et contre narration.txt."""
import json, pathlib, shutil, subprocess, sys
import textnorm as T, units as U

W = pathlib.Path(__file__).parent
OUT = pathlib.Path('/Users/tsousa/antikythera/build/out/explainer/voice')
F = W / 'final'; F.mkdir(exist_ok=True)
PY = '/Users/tsousa/voxtral-tts/bin/python'
files = []
for i in range(1, 8):
    shutil.copy(OUT / f'ch{i}.wav', F / f'ch{i}.wav'); files.append(str(F / f'ch{i}.wav'))
if '--skip' not in sys.argv:
    subprocess.run([PY, str(W / 'stt.py')] + files, check=True, capture_output=True)
    subprocess.run([PY, str(W / 'stt2.py')] + files, check=True, capture_output=True)

us = U.units()
est = {1: 24, 2: 14, 3: 24, 4: 17, 5: 18, 6: 30, 7: 38}
timing = json.loads((OUT / 'timing.json').read_text())
rows = []
for i in range(1, 8):
    tts = ' '.join(u['tts'] for u in us if u['ch'] == i)
    orig = ' '.join(u['orig'] for u in us if u['ch'] == i)
    r = dict(ch=i, duree=timing['chapters'][i - 1]['duration'], estimation=est[i])
    for eng, ext in (('whisper', 'stt'), ('parakeet', 'pk')):
        hyp = json.loads((F / f'ch{i}.{ext}.json').read_text())['text']
        strict = T.wer(tts, hyp)
        rp, hp = T.pwords(tts), T.pwords(hyp)
        S, D, I, ops = T.align(rp, hp)
        vs_orig = T.wer(orig, hyp)
        r[eng] = dict(hyp=hyp, wer_ortho=round(strict['wer'], 4), wer_phon=round((S + D + I) / len(rp), 4),
                      n=len(rp), err_phon=[(o, a, b) for o, a, b in ops if o != '='],
                      wer_vs_narration=round(vs_orig['wer'], 4))
    rows.append(r)
(W / 'qa_final.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1))
for r in rows:
    print(f"ch{r['ch']} {r['duree']:5.2f}s (script ~{r['estimation']}s) | "
          + ' | '.join(f"{e}: WER ortho {r[e]['wer_ortho']*100:4.1f}% phon {r[e]['wer_phon']*100:4.1f}%" for e in ('whisper', 'parakeet')))
    for e in ('whisper', 'parakeet'):
        if r[e]['err_phon']: print(f"     {e}: {r[e]['err_phon']}")
tot = {e: sum(len(r[e]['err_phon']) for r in rows) / sum(r[e]['n'] for r in rows) for e in ('whisper', 'parakeet')}
print('WER phonétique global :', {k: f'{v*100:.1f}%' for k, v in tot.items()})
