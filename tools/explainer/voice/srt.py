"""Construit narration.srt (texte ORIGINAL) à partir des horodatages Whisper par mot
de chaque prise retenue, placés dans la chronologie de narration_full.wav."""
import json, pathlib, re
import textnorm as T

W = pathlib.Path(__file__).parent
OUT = pathlib.Path('/Users/tsousa/antikythera/build/out/explainer/voice')
asm = json.loads((W / 'assembly.json').read_text())
timing = json.loads((OUT / 'timing.json').read_text())
chstart = {c['n']: c['start'] for c in timing['chapters']}
chdur = {c['n']: c['duration'] for c in timing['chapters']}
MAXL = 42
OPEN = set('«“(')
WEAK = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'en', 'à', 'au', 'aux', 'et', 'sur', 'dans', 'pour',
        'par', 'ne', 'ce', 'ces', 'sa', 'son', 'ses', 'leurs', 'notre', 'y', 'où', 'quand', 'ni', 'mais', 'puis',
        "l'", "d'", 'qu', 'il', 'on', 'cette', 'deux', 'trois', 'cinq', 'quatre', 'plus', 'petit', 'petite', 'petites',
        'avec', 'tes', 'lui', 'ou', 'comme', 'pas'}


def hyp_tokens(stt):
    out = []
    for w in stt['words']:
        toks = T.words(w['word'])
        if not toks: continue
        d = (w['end'] - w['start']) / len(toks)
        for k, t in enumerate(toks):
            out.append((t, w['start'] + k * d, w['start'] + (k + 1) * d))
    return out


def map_times(ref_toks, hyp):
    """Aligne ref_toks sur hyp=(tok,s,e) ; renvoie [(s,e)] par jeton de ref, interpolé si absent."""
    S, D, I, ops = T.align(ref_toks, [h[0] for h in hyp])
    res, hi = [], 0
    for o, r, h in ops:
        if o in '=S':
            res.append((hyp[hi][1], hyp[hi][2])); hi += 1
        elif o == 'D':
            res.append(None)
        else:
            hi += 1
    # interpolation des trous
    n = len(res)
    for i in range(n):
        if res[i] is None:
            prev = next((res[k][1] for k in range(i - 1, -1, -1) if res[k]), None)
            nxt = next((res[k][0] for k in range(i + 1, n) if res[k]), None)
            if prev is None and nxt is None: prev = nxt = 0.0
            if prev is None: prev = nxt
            if nxt is None: nxt = prev
            res[i] = (prev, max(prev, nxt))
    return res


def display_words(orig):
    """Mots affichés : la ponctuation isolée s'accroche au mot voisin."""
    raw = orig.split()
    words = []
    pending_open = ''
    for w in raw:
        if not T.words(w):
            if w in OPEN:
                pending_open += w + ' '
            elif words:
                words[-1] += ' ' + w      # « boîte : », « matin. »
            else:
                pending_open += w + ' '
            continue
        words.append(pending_open + w); pending_open = ''
    return words


items = []   # (texte, début, fin, chapitre, fin_de_phrase)
plan = {p['id']: p for p in json.loads((W / 'plan.json').read_text())}
for u in asm:
    pl = plan[u['id']]
    tts_toks = T.words(u['tts'])
    tts_t = [tuple(x) for x in pl['tok_times']]
    assert len(tts_t) == len(tts_toks), u['id']
    dws = display_words(u['orig'])
    otoks, owner = [], []
    for i, dw in enumerate(dws):
        for t in T.words(dw):
            otoks.append(t); owner.append(i)
    o_t = map_times(otoks, [(t, s, e) for t, (s, e) in zip(tts_toks, tts_t)])
    base = chstart[u['ch']] + u['start'] - u['trim_start']
    lo, hi = chstart[u['ch']] + u['start'], chstart[u['ch']] + u['start'] + u['dur']
    for i, dw in enumerate(dws):
        ts = [o_t[k] for k in range(len(otoks)) if owner[k] == i]
        s = min(x[0] for x in ts) + base; e = max(x[1] for x in ts) + base
        s = min(max(s, lo), hi); e = min(max(e, s + 0.05), hi)
        last = i == len(dws) - 1
        items.append(dict(text=dw, s=s, e=e, ch=u['ch'], sent=last or bool(re.search(r'[.!?]( »)?$', dw)),
                          unit=u['id']))

# recalage sur l'audio final : un début (ou une fin) de mot placé dans un silence
# est déplacé jusqu'à la parole la plus proche (au plus 0,6 s)
import numpy as np, soundfile as sf
ENV = {}
for ch in range(1, 8):
    a, sr = sf.read(OUT / f'ch{ch}.wav', dtype='float32'); hop = sr // 100; n = len(a) // hop
    r = 20 * np.log10(np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
    ENV[ch] = (r, max(-50.0, float(np.percentile(r, 95)) - 35.0))
for w in items:
    r, thr = ENV[w['ch']]
    s0 = int((w['s'] - chstart[w['ch']]) * 100); e0 = int((w['e'] - chstart[w['ch']]) * 100)
    if 0 <= s0 < len(r) and r[s0] < thr:
        f = next((f for f in range(s0, min(len(r), s0 + 60)) if r[f] >= thr), None)
        if f is not None and f < e0: w['s'] = chstart[w['ch']] + f / 100
    if 0 < e0 <= len(r) and r[e0 - 1] < thr:
        f = next((f for f in range(e0 - 1, max(-1, e0 - 61), -1) if r[f] >= thr), None)
        if f is not None and chstart[w['ch']] + (f + 1) / 100 > w['s']: w['e'] = chstart[w['ch']] + (f + 1) / 100

# monotonie
for a, b in zip(items, items[1:]):
    if b['s'] < a['s']: b['s'] = a['s']
    if a['e'] > b['s'] and a['unit'] == b['unit']: a['e'] = max(a['s'] + 0.05, b['s'])


def brk(w):
    """Qualité d'une coupure après le mot w (0 = idéale)."""
    t = w['text']
    if w['sent']: return 0.0
    if re.search(r'[:;…]$', t): return 0.3
    if t.endswith(','): return 0.6
    return 1.5


def split_lines(ws):
    txt = ' '.join(w['text'] for w in ws)
    if len(txt) <= MAXL: return [txt], 0.0
    best = None
    for k in range(1, len(ws)):
        l1 = ' '.join(w['text'] for w in ws[:k]); l2 = ' '.join(w['text'] for w in ws[k:])
        if len(l1) > MAXL or len(l2) > MAXL: continue
        c = abs(len(l1) - len(l2)) / 30 + brk(ws[k - 1])
        lw = ws[k - 1]['text'].lower().split()[-1]
        if lw in WEAK or lw.endswith("'"): c += 3
        if best is None or c < best[0]: best = (c, [l1, l2])
    if best is None: return None, None
    return best[1], best[0]


def cue_cost(ws):
    lines, lc = split_lines(ws)
    if lines is None: return None
    dur = ws[-1]['e'] - ws[0]['s']
    if dur > 5.6: return None
    last = ws[-1]
    c = 1.0 + lc + {0.0: 0.0, 0.3: 0.5, 0.6: 1.5, 1.5: 4.0}[brk(last)]
    if last['text'].lower().split()[-1] in WEAK: c += 6
    if dur < 1.0: c += 3.0
    elif dur < 1.3: c += 0.5
    inner = [i for i, w in enumerate(ws[:-1]) if w['sent']]
    if inner:
        c += 0.3 * len(inner)
        if not last['sent']: c += 5          # ne pas finir au milieu de la phrase suivante
        if len(lines) == 2:
            k = inner[0] + 1
            if len(inner) > 1 or lines[0] != ' '.join(w['text'] for w in ws[:k]): c += 5
    return c, lines


cues = []
for ch in range(1, 8):
    ws = [w for w in items if w['ch'] == ch]
    n = len(ws)
    best = [(0.0, None)] + [(1e9, None)] * n
    for j in range(1, n + 1):
        for i in range(max(0, j - 20), j):
            cc = cue_cost(ws[i:j])
            if cc is None: continue
            v = best[i][0] + cc[0]
            if v < best[j][0]: best[j] = (v, (i, cc[1]))
    j, seq = n, []
    while j > 0:
        i, lines = best[j][1]
        seq.append((ws[i]['s'], ws[j - 1]['e'], lines, ch)); j = i
    cues += seq[::-1]

# temps d'affichage : +0,25 s de tenue, 1 s minimum, pas de chevauchement (écart 0,04 s)
final = []
for k, (s, e, lines, ch) in enumerate(cues):
    nxt = cues[k + 1][0] if k + 1 < len(cues) else s + 99
    prev_end = final[-1][1] if final else 0.0
    s = max(s - 0.1, prev_end + 0.04)
    lim = nxt - 0.04
    if k + 1 < len(cues) and cues[k + 1][3] != ch:
        lim = min(lim, chstart[ch] + chdur[ch] + 0.5)
    e = min(e + 0.25, lim)
    if e - s < 1.0:
        e = min(s + 1.0, lim)
    if e - s < 1.0:
        s = max(prev_end + 0.04, e - 1.0)
    final.append((s, e, lines, ch))


def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s_, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s_:02d},{ms:03d}"


srt = []
for k, (s, e, lines, ch) in enumerate(final, 1):
    srt.append(f"{k}\n{ts(s)} --> {ts(e)}\n" + '\n'.join(lines) + '\n')
(OUT / 'narration.srt').write_text('\n'.join(srt), encoding='utf-8')

# contrôles
durs = [e - s for s, e, _, _ in final]
maxline = max(len(l) for _, _, ls, _ in final for l in ls)
print(f"{len(final)} sous-titres ; durée {min(durs):.2f}-{max(durs):.2f} s ; ligne max {maxline} car.")
bad = [(k, round(d, 2)) for k, d in enumerate(durs, 1) if d < 1.0 or d > 6.0]
print('hors bornes :', bad)
# le texte des sous-titres doit être exactement le texte original
joined = ' '.join(' '.join(ls) for _, _, ls, _ in final)
orig = ' '.join(u['orig'] for u in asm)
print('texte identique à narration.txt :', re.sub(r'\s+', ' ', joined) == re.sub(r'\s+', ' ', orig))
