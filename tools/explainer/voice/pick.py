"""Découpe les prises « chapitre entier » en unités (phrases), note chaque unité avec deux
STT (Whisper large-v3-turbo et Parakeet TDT v3), et choisit la meilleure source par unité.
Sortie : plan.json (+ rapport à l'écran)."""
import json, pathlib, re, sys
import numpy as np, soundfile as sf
import textnorm as T, units as U

W = pathlib.Path(__file__).parent
TK = W / 'takes'
SR = 24000
us = U.units()
ENG = (('whisper', 'stt'), ('parakeet', 'pk'))


def hyp_tokens(path):
    st = json.loads(path.read_text())
    out = []
    for w in st['words']:
        toks = T.pwords(w['word'])
        if not toks: continue
        d = (w['end'] - w['start']) / len(toks)
        for k, t in enumerate(toks):
            out.append((t, w['start'] + k * d, w['start'] + (k + 1) * d))
    return out


def env(a):
    hop = int(0.01 * SR); n = len(a) // hop
    return 20 * np.log10(np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)


def analyse(wav, cu):
    """cu = unités contenues dans le fichier (dans l'ordre). Renvoie une liste de candidats."""
    a, sr = sf.read(wav, dtype='float32'); assert sr == SR
    dur = len(a) / SR
    ref, owner = [], []
    for k, u in enumerate(cu):
        for t in T.pwords(u['tts']): ref.append(t); owner.append(k)
    R = {}
    for eng, ext in ENG:
        p = wav.with_suffix(f'.{ext}.json')
        if not p.exists(): continue
        hyp = hyp_tokens(p)
        S, D, I, ops = T.align(ref, [h[0] for h in hyp])
        times = [None] * len(ref); errs = [0] * len(cu); ins = []; exact = [False] * len(ref)
        ri = hi = 0
        detail = [[] for _ in cu]
        for o, r, h in ops:
            if o in '=S':
                times[ri] = (hyp[hi][1], hyp[hi][2]); exact[ri] = o == '='
                if o == 'S': errs[owner[ri]] += 1; detail[owner[ri]].append(f'{r}->{h}')
                ri += 1; hi += 1
            elif o == 'D':
                errs[owner[ri]] += 1; detail[owner[ri]].append(f'-{r}'); ri += 1
            else:
                ins.append(((hyp[hi][1] + hyp[hi][2]) / 2, h)); hi += 1
        R[eng] = dict(times=times, errs=errs, ins=ins, exact=exact, detail=detail,
                      text=json.loads(p.read_text())['text'])
    # bornes des unités
    rdb = env(a)
    thr = max(-55.0, np.percentile(rdb, 95) - 38)
    quiet = rdb < thr
    cuts = [0.0]
    for k in range(len(cu) - 1):
        ends, starts = [], []
        for eng in R:
            tk = [i for i, o in enumerate(owner) if o == k and R[eng]['times'][i]]
            tn = [i for i, o in enumerate(owner) if o == k + 1 and R[eng]['times'][i]]
            if tk: ends.append(R[eng]['times'][tk[-1]][1])
            if tn: starts.append(R[eng]['times'][tn[0]][0])
        e_k = float(np.median(ends)) if ends else None
        s_n = float(np.median(starts)) if starts else None
        if e_k is None: e_k = s_n
        if s_n is None: s_n = e_k
        lo = max(cuts[-1] + 0.1, min(e_k, s_n) - 0.25); hi = min(dur - 0.05, max(e_k, s_n) + 0.25)
        f0, f1 = int(lo * 100), int(hi * 100)
        # plus longue plage silencieuse dans la fenêtre
        best, run = None, None
        for f in range(f0, f1 + 1):
            if f < len(quiet) and quiet[f]:
                run = (run[0], f) if run else (f, f)
            else:
                if run and (best is None or run[1] - run[0] > best[1] - best[0]): best = run
                run = None
        if run and (best is None or run[1] - run[0] > best[1] - best[0]): best = run
        if best and best[1] - best[0] >= 3:
            c = (best[0] + best[1] + 1) / 2 / 100
        else:
            c = (f0 + int(np.argmin(rdb[f0:f1 + 1]))) / 100 + 0.005
        cuts.append(c)
    cuts.append(dur)
    # Début de prise : Voxtral produit souvent un petit bruit (premières trames du codec)
    # avant la parole. S'il est séparé de la parole par un silence (>= 80 ms), on coupe
    # à la fin de ce silence.
    firsts = []
    for eng in R:
        t0 = next((R[eng]['times'][i][0] for i in range(len(ref)) if R[eng]['times'][i]), None)
        if t0 is not None: firsts.append(max(0.0, t0))
    head_cut = 0.0
    if firsts:
        lim = int((min(firsts) + 0.15) * 100)
        f, runs = 0, []
        while f < min(lim, len(quiet)):
            if quiet[f]:
                g = f
                while g < len(quiet) and quiet[g]: g += 1
                if g - f >= 8: runs.append((f, g))
                f = g
            else:
                f += 1
        if runs:
            head_cut = max(0.0, runs[-1][1] / 100 - 0.03)
            cuts[0] = head_cut
    cands = []
    for k, u in enumerate(cu):
        s, e = cuts[k], cuts[k + 1]
        c = dict(id=u['id'], src=str(wav.relative_to(W)), s=round(s, 3), e=round(e, 3), errs={}, detail={}, hyp={}, head_cut=round(head_cut, 3) if k == 0 else 0.0)
        best_eng, best_err = None, 1e9
        # Parakeet d'abord : ses débuts de mots sont plus justes (Whisper avale les pauses)
        for eng in sorted(R, key=lambda x: x != 'parakeet'):
            err = R[eng]['errs'][k] + sum(1 for t, h in R[eng]['ins'] if s <= t < e)
            c['errs'][eng] = err
            c['detail'][eng] = R[eng]['detail'][k] + [f'+{h}' for t, h in R[eng]['ins'] if s <= t < e]
            idx = [i for i, o in enumerate(owner) if o == k]
            if err < best_err: best_eng, best_err = eng, err
        # horodatage des jetons TTS de l'unité (moteur le plus juste), interpolé si trou
        idx = [i for i, o in enumerate(owner) if o == k]
        tt = [R[best_eng]['times'][i] for i in idx]
        for i in range(len(tt)):
            if tt[i] is None:
                prev = next((tt[j][1] for j in range(i - 1, -1, -1) if tt[j]), s)
                nxt = next((tt[j][0] for j in range(i + 1, len(tt)) if tt[j]), prev)
                tt[i] = (prev, max(prev, nxt))
        c['engine'] = best_eng
        c['tok_times'] = [(round(max(s, min(e, x)), 3), round(max(s, min(e, y)), 3)) for x, y in tt]
        c['min_err'] = min(c['errs'].values()); c['max_err'] = max(c['errs'].values())
        # débit : caractères par seconde de parole
        seg = a[int(s * SR):int(e * SR)]
        r = env(seg); voiced = np.sum(r > thr) / 100
        c['speech_s'] = round(float(voiced), 2)
        c['cps'] = round(len(u['tts']) / max(voiced, 0.1), 1)
        cands.append(c)
    return cands


def all_candidates():
    out = {}
    for ch in range(1, 8):
        cu = [u for u in us if u['ch'] == ch]
        for wav in sorted(TK.glob(f'ch{ch}_t*.wav')):
            meta = json.loads(wav.with_suffix('.json').read_text())
            if meta['text'] != ' '.join(u['tts'] for u in cu):
                continue   # prise faite avec un ancien texte
            for c in analyse(wav, cu):
                c['kind'] = 'chapitre'; out.setdefault(c['id'], []).append(c)
    for u in us:
        for wav in sorted(TK.glob(f"{u['id']}_t*.wav")):
            meta = json.loads(wav.with_suffix('.json').read_text())
            if meta['text'] != u['tts']:
                continue
            if not wav.with_suffix('.pk.json').exists() or not wav.with_suffix('.stt.json').exists():
                continue
            for c in analyse(wav, [u]):
                c['kind'] = 'phrase'; out.setdefault(u['id'], []).append(c)
    return out


if __name__ == '__main__':
    cands = all_candidates()
    forced = json.loads((W / 'force.json').read_text()) if (W / 'force.json').exists() else {}
    plan = []
    for ch in range(1, 8):
        cu = [u for u in us if u['ch'] == ch]
        takes = sorted({c['src'] for u in cu for c in cands.get(u['id'], []) if c['kind'] == 'chapitre'})
        score = {t: (sum(1 for u in cu for c in cands[u['id']] if c['src'] == t and c['min_err'] == 0),
                     -sum(c['min_err'] + c['max_err'] for u in cu for c in cands[u['id']] if c['src'] == t)) for t in takes}
        # à égalité, la prise la plus régulière (écart-type du niveau des phrases le plus faible)
        import pyloudnorm as pyln
        meter = pyln.Meter(SR)
        def steadiness(t):
            a = sf.read(W / t, dtype='float32')[0]; ls = []
            for u in cu:
                c = next(c for c in cands[u['id']] if c['src'] == t)
                seg = a[int(c['s'] * SR):int(c['e'] * SR)]
                if len(seg) < 0.4 * SR: seg = np.concatenate([seg, np.zeros(int(0.4 * SR), np.float32)])
                ls.append(meter.integrated_loudness(seg))
            return -float(np.std(ls))
        primary = max(takes, key=lambda t: (score[t], steadiness(t))) if takes else None
        print(f"\n=== chapitre {ch} : prise principale {primary}  {score}")
        for u in cu:
            cs = cands.get(u['id'], [])
            if u['id'] in forced:
                pick = next(c for c in cs if c['src'] == forced[u['id']])
            else:
                def key(c):
                    return (c['min_err'], c['max_err'], 0 if c['src'] == primary else (1 if c['kind'] == 'chapitre' else 2))
                pick = min(cs, key=key)
            flag = '' if pick['min_err'] == 0 else '   <<< À REPRENDRE'
            print(f"{u['id']} <- {pick['src']:22s} [{pick['s']:6.2f}-{pick['e']:6.2f}] err W{pick['errs'].get('whisper')} P{pick['errs'].get('parakeet')} "
                  f"{pick['cps']:5.1f} car/s{flag}")
            for eng, d in pick['detail'].items():
                if d: print(f"      {eng}: {d}")
            others = [f"{c['src']}:W{c['errs'].get('whisper')}P{c['errs'].get('parakeet')}" for c in cs if c is not pick]
            print('      autres :', ' '.join(others))
            plan.append(dict(pick, ch=u['ch'], tts=u['tts'], orig=u['orig'], pause=u['pause']))
    (W / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    rates = [p['cps'] for p in plan]
    print('\ndébit médian', np.median(rates), 'car/s ; extrêmes', min(rates), max(rates))
