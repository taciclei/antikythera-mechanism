import json, sys, numpy as np, textnorm as T
srt = open('/Users/tsousa/antikythera/build/out/explainer/voice/narration.srt').read().strip().split('\n\n')
def sec(t): h,m,s = t.split(':'); return int(h)*3600+int(m)*60+float(s.replace(',','.'))
toks, owner, cues = [], [], []
for k, b in enumerate(srt):
    L = b.split('\n'); a, e = L[1].split(' --> '); cues.append((sec(a), sec(e), ' / '.join(L[2:])))
    for t in T.pwords(' '.join(L[2:])): toks.append(t); owner.append(k)
for ext in sys.argv[1:]:
    ws = json.load(open(f'final/narration_full.{ext}.json'))['words']
    hyp = [(t, w['start'], w['end']) for w in ws for t in T.pwords(w['word'])]
    S, D, I, ops = T.align(toks, [h[0] for h in hyp])
    ri = hi = 0; first = {}; last = {}
    for o, r, h in ops:
        if o == '=': first.setdefault(owner[ri], hyp[hi][1]); last[owner[ri]] = hyp[hi][2]
        if o in '=S': ri += 1; hi += 1
        elif o == 'D': ri += 1
        else: hi += 1
    ds = [first[k] - cues[k][0] for k in first]
    print(ext, 'WER vs sous-titres %.1f%%' % (100 * (S + D + I) / len(toks)),
          '| début mot - début sous-titre : médiane %.2f s, min %.2f, max %.2f (n=%d/%d)' % (np.median(ds), min(ds), max(ds), len(ds), len(cues)))
    for k in first:
        if first[k] - cues[k][0] < -0.15 or first[k] - cues[k][0] > 0.5 or last[k] > cues[k][1] + 0.1:
            print('   ', k + 1, f'{cues[k][0]:.2f}-{cues[k][1]:.2f}', f'mots {first[k]:.2f}-{last[k]:.2f}', cues[k][2][:50])
