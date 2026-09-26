"""Checks of the film timeline against the astronomy engine, the voice and the subtitles.

    PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
    $PY tools/explainer/film/verify_beats.py            # reads film/timeline.json (+ audio_placement.json,
                                                        #   subtitles_film.srt), writes film/verification.json
    $PY tools/explainer/film/verify_beats.py --blend    # + opens build/out/am_atelier.blend in a background
                                                        #   Blender, read-only (nothing saved) : object names, texts
    $PY tools/explainer/film/verify_beats.py --audio    # + renders the voice track with the ffmpeg command of
                                                        #   audio_placement.json (temporary file) and measures it

timeline.py runs it at the end (exit code 1 if an ERROR is found).  Every reading of the machine goes through
tools/explainer/engine.py (identical to the Blender drivers) with the crank Blender will evaluate on that frame
(frames[].crank, float32), recomputed here from the controller keys with filmlib.eval_keys.

Levels : ERROR = the film would show or say something false / out of sync ; WARN = to look at (layout, pacing) ;
INFO = measured values.
"""
import json
import math
import re
import subprocess
import sys
import unicodedata
import wave

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import filmlib as L  # noqa: E402

sys.path.insert(0, str(L.ROOT / 'tools' / 'explainer'))
import engine as E  # noqa: E402

BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'
BLEND = L.ROOT / 'build' / 'out' / 'am_atelier.blend'
MIN_HOLD_S = 2.0                # overlay_style.json animation.tenue_min_s
COUNTER_BOX = (0.05, 0.05, 0.303, 0.122)   # overlay_style.json compteur.boite_px / 1920x1080
REQUIRED_TEXTS = [              # script.md « Mentions d'honnêteté obligatoires » (callouts ; the rest is in the inserts)
    "Sphère dorée : citée par l'inscription · son engrenage : hypothèse", 'Hypothèse · Freeth et al. 2021',
    'Couleurs modernes', 'Signe calculé par notre modèle', 'Aiguille du Dragon : hypothèse',
    'Signes calculés par notre modèle', 'Pas un instrument de navigation', 'Végèce (IVe-Ve s. apr. J.-C.)',
    'taciclei']
FORBIDDEN = ['premier ordinateur', 'archimède', 'date exacte', '1901']

M = E.get_machine(False)
RESULTS = []


def rep(level, cid, ok, detail):
    RESULTS.append({'level': level if not ok else 'OK', 'check': cid, 'detail': detail})
    return ok


def err(cid, ok, detail):
    return rep('ERROR', cid, ok, detail)


def warn(cid, ok, detail):
    return rep('WARN', cid, ok, detail)


def info(cid, detail):
    RESULTS.append({'level': 'INFO', 'check': cid, 'detail': detail})


# ----------------------------------------------------------------------------- engine readings (float crank)
def wrap180(d):
    return (d + 180.0) % 360.0 - 180.0


def lon(c, key):
    return math.degrees(float(M.longitudes(float(c))[key])) % 360.0


def sign(c, key):
    z = E.zodiac_read(M.zodiac, lon(c, key))
    return z['signe_grec'], z['degre_dans_le_signe']


def elong(c):
    return math.degrees(float(M.sun_moon_node(float(c))['q'])) % 360.0


def fraction(c):
    return (1.0 - math.cos(math.radians(elong(c)))) / 2.0


def node_dist(c):
    return float(M.node_distance(float(c), 'FM')[0])


def mars_rate(c):
    return float(M.rate('mars', float(c)))


def games(c):
    return M.subsidiary['olympiad']['labels'][int(M.olympiad_sector(float(c)))]


def saros(c):
    return int(M.saros_cell(float(c)))


def glyph(cell):
    return M.engraved_table()['cells'][cell - 1]['glyph'] or ''


def exeligmos_hours(c):
    return M.read_back(float(c))['exeligmos']['heures_a_ajouter']


# ----------------------------------------------------------------------------- helpers
def load():
    T = json.loads((L.FILM / 'timeline.json').read_text())
    return T


def crank_of(T):
    return {x['f']: x['crank'] for x in T['frames']}


def seg_of(T):
    return {x['f']: x['seg'] for x in T['frames']}


def segment(T, sid):
    return next(s for s in T['segments'] if s['id'] == sid)


def fs(f):
    return '%d (%.2f s)' % (f, L.time_of(f))


# ----------------------------------------------------------------------------- 1. keys -> frames, structure
def check_keys(T):
    ctl = T['controller']
    bad = []
    for x in T['frames']:
        c = L.f32(L.eval_keys(ctl['crank'], x['f']))
        if c != x['crank']:
            bad.append(x['f'])
    err('keys->frames.crank', not bad, 'frames[].crank = eval des clés (float32) sur les %d images%s'
        % (len(T['frames']), '' if not bad else ' ; écarts aux images %s' % bad[:10]))
    for name in ('crank', 'explode', 'patina'):
        keys = ctl[name]
        fr = [k['f'] for k in keys]
        ok = fr == sorted(set(fr)) and all(k['ipo'] in ('CONSTANT', 'LINEAR', 'SINE', 'QUAD', 'CUBIC') for k in keys)
        err('keys.%s' % name, ok, '%d clés triées, une par image, interpolations Blender connues' % len(keys))
    ex = [x['explode'] for x in T['frames']]
    pa = [x['patina'] for x in T['frames']]
    err('explode/patina bornés', all(0 <= v <= 1 for v in ex + pa), 'explode et patina dans [0, 1]')


def check_structure(T):
    segs = T['segments']
    N = T['frame_end']
    ok = segs[0]['frames'][0] == 1 and segs[-1]['frames'][1] == N and all(
        a['frames'][1] + 1 == b['frames'][0] for a, b in zip(segs, segs[1:])) and all(
        s['frames'][0] <= s['frames'][1] for s in segs)
    err('segments contigus', ok, '%d plans couvrent les images 1-%d sans trou ni chevauchement' % (len(segs), N))
    err('frames[]', [x['f'] for x in T['frames']] == list(range(1, N + 1)), 'une entrée par image')
    info('durée', '%d images = %.2f s (%d min %05.2f s)' % (N, N / L.FPS, int(N / L.FPS // 60), N / L.FPS % 60))
    # diagram maps
    dtim = json.loads((L.DIAGRAMS / 'timing.json').read_text())
    for s in segs:
        d = s.get('diagram')
        if not d:
            continue
        seq = d['sequence']
        meta = dtim[seq]
        n_img = meta['images'] if 'images' in meta else dtim[meta['identique_a']]['images']
        mframes = [m[0] for m in d['map']]
        last = (s['inset_until'] - 1) if s.get('inset_until') else s['frames'][1]
        want = list(range(s['frames'][0], last + 1))
        imgs = [m[1] for m in d['map']]
        missing = [i for i in sorted(set(imgs)) if not (L.ROOT / d['dir'] / (d['pattern'] % i)).exists()]
        err('schéma %s (%s)' % (s['id'], seq), mframes == want and all(1 <= i <= n_img for i in imgs) and not missing
            and imgs == sorted(imgs),
            'une image du schéma par image du film (%d-%d), images %d-%d croissantes, fichiers présents%s'
            % (want[0], want[-1], imgs[0], imgs[-1], '' if not missing else ' ; MANQUANTS %s' % missing[:5]))
    # callouts
    anchors = T['anchors']
    short, clamp, bad_anchor, overlap_counter = [], [], [], []
    counter_on = {x['f'] for x in T['frames'] if x['counter']}
    texts = []
    for s in segs:
        for c in s.get('callouts', []):
            texts.append(c['text'])
            if c.get('anchor') and c['anchor'] not in anchors:
                bad_anchor.append((s['id'], c['text'], c['anchor']))
            if c['out'] < c['in']:
                clamp.append((s['id'], c['text'], c['in'], c['out']))
            dur = (c['out'] - c['in'] + 1) / L.FPS
            if dur < MIN_HOLD_S and c.get('style') != 'credit':
                short.append('%s « %s » %.1f s' % (s['id'], c['text'], dur))
            p = c.get('pos')
            if p and p[0] < COUNTER_BOX[2] and p[1] < COUNTER_BOX[3] + 0.015 and any(
                    f in counter_on for f in range(c['in'], c['out'] + 1)):
                overlap_counter.append('%s « %s »' % (s['id'], c['text']))
    err('callouts : ancres', not bad_anchor, 'toutes les ancres existent dans anchors%s'
        % ('' if not bad_anchor else ' ; %s' % bad_anchor))
    err('callouts : in <= out', not clamp, 'aucun callout vide après recadrage sur son plan%s'
        % ('' if not clamp else ' ; %s' % clamp))
    err('callouts : compteur', not overlap_counter, 'aucun callout posé sur le compteur (haut gauche) quand il est '
        'visible%s' % ('' if not overlap_counter else ' ; %s' % overlap_counter))
    warn('callouts : tenue >= %.0f s' % MIN_HOLD_S, not short, '%d callouts plus courts que la tenue minimale de la '
         'charte%s' % (len(short), '' if not short else ' : ' + ' ; '.join(short)))
    pictures = [t for s in segs for t in s.get('texts_in_picture', [])]
    pictures += [t for o in T.get('overlays', []) for t in o.get('texts', [])]
    allt = texts + pictures
    miss = [t for t in REQUIRED_TEXTS if not any(t in x for x in allt)]
    err('mentions obligatoires', not miss, '%d mentions présentes (callouts, textes des schémas et des incrustations)%s'
        % (len(REQUIRED_TEXTS) - len(miss), '' if not miss else ' ; ABSENTES %s' % miss))
    low = ' '.join(allt).lower()
    bad = [w for w in FORBIDDEN if w in low]
    names = sorted({c['text'] for s in segs for c in s.get('callouts', []) if c.get('style') == 'credit'})
    err('textes interdits / crédit', not bad and names == ['taciclei'],
        'aucun texte interdit (callouts, schémas, incrustations) ; crédit = %s' % names)
    clamped = ['%s « %s » %s -> %s' % (s['id'], c['text'], c['clamped_from'], [c['in'], c['out']])
               for s in segs for c in s.get('callouts', []) if c.get('clamped_from')]
    if clamped:
        info('callouts recadrés sur leur plan', ' ; '.join(clamped))
    # cameras : poses inside their segment, sorted
    badcam = []
    for s in segs:
        for cam in [s.get('camera'), s.get('inset')]:
            if not cam:
                continue
            f = [p['f'] for p in cam['poses']]
            if f != sorted(f) or f[0] > s['frames'][0] or f[-1] < s['frames'][1]:
                if not (s['id'] == '7.5' and f[-1] >= s['frames'][1]):
                    badcam.append((s['id'], cam['name'], f))
    err('caméras', not badcam, 'poses triées couvrant chaque plan%s' % ('' if not badcam else ' ; %s' % badcam))


# ----------------------------------------------------------------------------- 2. crank continuity, counter
ALLOWED_BACK = {'2.2'}                      # « en arrière, il remonte »
ALLOWED_JUMP = {'1.2a', '1.2b', '1.2c', '1.2d', '1.3', '4.3'}    # flashes, back to 0, replay of 4.3


def check_crank_path(T):
    cr = crank_of(T)
    sg = seg_of(T)
    first = {s['id']: s['frames'][0] for s in T['segments']}
    back = []
    for f in range(2, T['frame_end'] + 1):
        if cr[f] < cr[f - 1] - 1e-7:
            if sg[f] in ALLOWED_BACK or (sg[f] in ALLOWED_JUMP and f == first[sg[f]]):
                continue
            back.append(f)
    err('manivelle : le temps avance', not back, 'la manivelle ne recule que dans 2.2 (« en arrière ») et aux sauts '
        'des éclairs 1.2, du retour à 0 (1.3) et de la reprise 4.3%s' % ('' if not back else ' ; RECULE aux images %s'
                                                                         % back[:10]))
    info('manivelle', 'de %.3f (image 1) à %.3f (image %d) ; max %.3f'
         % (cr[1], cr[T['frame_end']], T['frame_end'], max(cr.values())))
    # counter
    bad = [x['f'] for x in T['frames'] if x['counter'] and x['counter'] != L.counter_text(x['crank'])]
    err('compteur = manivelle', not bad, 'le texte du compteur suit la manivelle de chaque image%s'
        % ('' if not bad else ' ; %s' % bad[:5]))
    shown = {x['seg'] for x in T['frames'] if x['counter']}
    hidden_ok = all(sid not in shown for sid in ('4.3', '6.5a', '7.3a', '7.6')) and all(
        sid not in shown for sid in ('1.1', '1.2a', '1.4'))
    err('compteur : visibilité', hidden_ok and '2.1' in shown and '7.5' in shown,
        'visible de « Tournez-la » (2.1) à 7.5, masqué au chapitre 1, pendant la reprise 4.3, les schémas plein écran '
        'et le carton')
    # fast pointer speed (strobing) on front views
    front = {s['id'] for s in T['segments'] if s.get('mode') == 'front' and s['kind'] in ('3d', 'split')}
    worst = []
    for sid in sorted(front, key=lambda k: first[k]):
        s = segment(T, sid)
        fr = range(s['frames'][0] + 1, s['frames'][1] + 1)
        dmax = max((abs(cr[f] - cr[f - 1]) for f in fr), default=0.0)
        worst.append((sid, dmax * float(M.rate_abs['moon']) * 360.0))
    fast = ['%s %.0f°/image' % (sid, d) for sid, d in worst if d > 90.0]
    warn('aiguille de la Lune (stroboscope)', not fast, 'vitesse max de l\'aiguille de la Lune sur les plans de face '
         '(> 90°/image = effet de roue de chariot) : %s' % ', '.join('%s %.0f°' % (a, b) for a, b in worst if b > 20))


# ----------------------------------------------------------------------------- 3. beats
def check_beat(T, b):
    cr = crank_of(T)
    f = b['frame']
    c = cr[f]
    p = b['params']
    ck = b['check']
    tag = 'beat %s (%s, image %s, manivelle %.4f)' % (b['id'], b['segment'], fs(f), c)
    res = []
    if seg_of(T)[f] != b['segment']:
        res.append((False, "l'image n'est pas dans le plan %s" % b['segment']))
    if ck == 'phase':
        e = elong(c)
        d = abs(wrap180(e - p['target_deg']))
        fr_ = fraction(c)
        ok = d <= p['tol_deg']
        msg = 'élongation %.2f° (écart %.2f° ≤ %.1f°), boule éclairée à %.4f' % (e, d, p['tol_deg'], fr_)
        if 'frac_max' in p:
            ok &= fr_ <= p['frac_max']
        if 'frac_min' in p:
            ok &= fr_ >= p['frac_min']
        if 'sun_moon_max_deg' in p:
            dm = abs(wrap180(lon(c, 'lune') - lon(c, 'soleil_moyen')))
            dv = abs(wrap180(lon(c, 'lune') - lon(c, 'soleil_vrai')))
            ok &= max(dm, dv) <= p['sun_moon_max_deg']
            msg += ' ; Lune à %.2f° de l\'aiguille de date, %.2f° de la sphère dorée' % (dm, dv)
        if 'moon_sign' in p:
            sgn, dg = sign(c, 'lune')
            ok &= sgn == p['moon_sign']
            msg += ' ; Lune %.1f° dans %s' % (dg, sgn)
        if 'sun_sign' in p:
            s1, d1 = sign(c, 'soleil_moyen')
            s2, d2 = sign(c, 'soleil_vrai')
            ok &= s1 == p['sun_sign'] and s2 == p['sun_sign']
            msg += ' ; aiguille de date %.1f° dans %s, sphère dorée %.1f° dans %s' % (d1, s1, d2, s2)
        res.append((ok, msg))
    elif ck == 'fraction':
        fr_ = fraction(c)
        res.append((p['lo'] <= fr_ <= p['hi'], 'boule éclairée à %.3f (attendu %.2f-%.2f), élongation %.1f°'
                    % (fr_, p['lo'], p['hi'], elong(c))))
    elif ck == 'dragon':
        e, nd = elong(c), node_dist(c)
        res.append((abs(wrap180(e - 180)) <= 1.0 and nd <= p['node_max_deg'],
                    'pleine lune (élongation %.3f°), Lune à %.3f° du nœud (≤ %.1f°), boule éclairée à %.4f'
                    % (e, nd, p['node_max_deg'], fraction(c))))
    elif ck == 'games':
        g = games(c)
        res.append((g == p['label'], 'secteur des Jeux sous l\'aiguille : %s' % g))
    elif ck == 'games_entry':
        g0, g1 = games(cr[f - 1]), games(c)
        res.append((g1 == p['label'] and g0 != p['label'], 'secteur %s -> %s entre les images %d et %d'
                    % (g0, g1, f - 1, f)))
        if p.get('stay'):
            s = segment(T, b['segment'])
            later = {games(cr[x]) for x in range(f, s['frames'][1] + 1)}
            res.append((later == {p['label']}, 'reste dans %s jusqu\'à la fin du plan (image %d)'
                        % (sorted(later), s['frames'][1])))
    elif ck == 'saros_entry':
        c0, c1 = saros(cr[f - 1]), saros(c)
        s = segment(T, b['segment'])
        cells = sorted({saros(cr[x]) for x in range(s['frames'][0], f)})
        ok = c0 == p['cell'] - 1 and c1 == p['cell'] and glyph(c1) == p['glyph']
        ok &= all(glyph(k) == '' for k in p['empty']) and all(k in cells for k in p['empty'])
        res.append((ok, 'case %d -> %d (signe « %s ») ; cases parcourues avant dans le plan : %s (sans signe : %s)'
                    % (c0, c1, glyph(c1), cells, [k for k in cells if not glyph(k)])))
    elif ck == 'exeligmos':
        s = segment(T, b['segment'])
        hrs = {exeligmos_hours(cr[x]) for x in range(s['frames'][0], s['frames'][1] + 1)}
        res.append((hrs == {p['hours']}, 'heures à ajouter sur tout le plan : %s' % sorted(hrs)))
    elif ck == 'mars_station':
        r0, r1 = mars_rate(cr[f - 1]), mars_rate(c)
        ok = (r0 > 0 >= r1) if p['n'] == 1 else (r0 < 0 <= r1)
        res.append((ok, 'vitesse de Mars %.1f -> %.1f °/an de manivelle entre les images %d et %d'
                    % (math.degrees(r0), math.degrees(r1), f - 1, f)))
    elif ck == 'mars_retro':
        r = mars_rate(c)
        res.append((r < 0, 'vitesse de Mars %.1f °/an (rétrograde)' % math.degrees(r)))
    elif ck == 'mars_replay':
        s = segment(T, b['segment'])
        dtim = json.loads((L.DIAGRAMS / 'timing.json').read_text())
        col = {r['image']: r['manivelle'] for r in dtim['retrograde']['manivelle_par_image']}
        lock = all(cr[fm] == L.f32(col[img]) for fm, img in s['diagram']['map'])
        rng = [cr[x] for x in range(s['frames'][0], s['frames'][1] + 1)]
        st = [x for x in range(s['frames'][0] + 1, s['frames'][1] + 1)
              if (mars_rate(cr[x - 1]) > 0) != (mars_rate(cr[x]) > 0)]
        res.append((lock and len(st) == 2 and min(rng) <= 2.1 + 1e-6 and max(rng) >= 2.52 - 1e-6,
                    'manivelle = colonne du schéma image par image (%s) ; plage %.3f-%.3f ; stations aux images %s'
                    % ('oui' if lock else 'NON', min(rng), max(rng), [fs(x) for x in st])))
    elif ck == 'sun_sign':
        s1, d1 = sign(c, 'soleil_moyen')
        s2, d2 = sign(c, 'soleil_vrai')
        ok = s1 == p['sign'] and s2 == p['sign']
        if 'deg_lo' in p:
            ok &= p['deg_lo'] <= d1 <= p['deg_hi']
        msg = 'aiguille de date %.2f° dans %s (%.1f°), sphère dorée %.1f° dans %s' % (d1, s1, lon(c, 'soleil_moyen'),
                                                                                   d2, s2)
        if p.get('entry'):
            s = segment(T, b['segment'])
            fe = next((x for x in range(s['frames'][0], s['frames'][1] + 1)
                       if sign(cr[x], 'soleil_moyen')[0] == p['sign']), None)
            ok &= fe is not None and (b['window'] is None or b['window'][0] <= fe <= b['window'][1])
            msg += ' ; entrée de l\'aiguille de date dans %s à l\'image %s' % (p['sign'], fs(fe) if fe else '-')
        res.append((ok, msg))
    else:
        res.append((False, 'test inconnu %s' % ck))
    # sync with the voice
    if b.get('window'):
        a, z = b['window']
        res.append((a <= f <= z, 'synchro : image %d dans [%d, %d] (« %s », mots %s)'
                    % (f, a, z, b['word'], b['word_frames'])))
    # hold
    if b.get('hold'):
        a, z = b['hold']
        vals = {cr[x] for x in range(a, z + 1)}
        res.append((len(vals) == 1 and c in vals, 'manivelle tenue à %.4f des images %d à %d' % (c, a, z)))
    ok = all(r[0] for r in res)
    err(tag, ok, b['expect'] + ' — ' + ' | '.join(('' if r[0] else 'ÉCHEC : ') + r[1] for r in res))
    return ok


def check_blinks(T):
    cr = crank_of(T)
    s1, s2 = segment(T, '6.1'), segment(T, '6.2')
    entries = []
    for f in range(s1['frames'][0], s2['frames'][1] + 1):
        a, b = saros(cr[f - 1]), saros(cr[f])
        for cell in range(a + 1, b + 1):
            if glyph(cell) and cell < 112:
                entries.append((cell, glyph(cell), f))
    got = [(b['cell'], b['glyph'], b['frame_entry']) for b in T['blinks_6_1']]
    err('6.1 : cases gravées qui clignotent', got == entries and entries and entries[-1][:2] == (107, 'Η'),
        'cases à signe traversées par l\'aiguille (moteur) : %s ; la dernière est 107 Η' %
        ', '.join('%d %s @%d' % e for e in entries))
    hl = {h['id']: h for h in T['highlights']}
    miss = [c for c, _, f in entries if 'blink_%03d' % c not in hl or hl['blink_%03d' % c]['keys'][1]['f'] != f + 1]
    err('6.1 : surlignages des cases', not miss, 'un clignotement par case, allumé à son entrée%s'
        % ('' if not miss else ' ; %s' % miss))


# ----------------------------------------------------------------------------- 4. audio + subtitles
def parse_srt(text):
    out = []
    for block in re.split(r'\n\s*\n', text.strip()):
        ln = block.strip().splitlines()
        a, b = [x.strip() for x in ln[1].split('-->')]
        sec = lambda s: int(s[0:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8]) + int(s[9:12]) / 1000
        out.append({'i': int(ln[0]), 'start': sec(a), 'end': sec(b), 'text': '\n'.join(ln[2:])})
    return out


def _norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn' and ch.isalnum())


def check_audio(T):
    AP = json.loads((L.FILM / 'audio_placement.json').read_text())
    clips = AP['clips']
    probs = []
    for c in clips:
        path = L.ROOT / c['file']
        with wave.open(str(path)) as w:
            dur = w.getnframes() / w.getframerate()
            sr = w.getframerate()
        if abs(dur - c['duration_s']) > 0.002 or sr != AP['sample_rate_source']:
            probs.append('%s : %.3f s / %d Hz sur disque' % (c['file'], dur, sr))
        if c['start_frame'] != L.frame_of(c['start_s']) or abs(c['start_sample_24k'] - c['start_s'] * sr) > 1:
            probs.append('%s : départ incohérent' % c['file'])
    err('audio : fichiers', not probs, '7 fichiers WAV présents, durées et fréquence conformes%s'
        % ('' if not probs else ' ; %s' % probs))
    gaps = [round(b['start_s'] - a['end_s'], 3) for a, b in zip(clips, clips[1:])]
    order = [c['chapter'] for c in clips] == list(range(1, 8))
    err('audio : placement', order and all(g >= 0.3 for g in gaps) and clips[0]['start_s'] > 0 and
        clips[-1]['end_s'] <= AP['total_seconds'],
        'chapitres dans l\'ordre, sans chevauchement ; pré-roll %.2f s, silences entre chapitres %s s, fin de la voix '
        '%.2f s, fin du film %.2f s (carton muet %.2f s)' % (clips[0]['start_s'], gaps, clips[-1]['end_s'],
                                                            AP['total_seconds'], AP['total_seconds'] -
                                                            clips[-1]['end_s']))
    ch = {c['n']: c for c in T['chapters']}
    err('audio = timeline', all(abs(ch[c['chapter']]['audio_start_s'] - c['start_s']) < 1e-6 for c in clips) and
        T['audio'] == clips, 'timeline.json audio[] et chapters[].audio_start_s = audio_placement.json')
    dl = [int(x) for x in re.findall(r'adelay=(\d+):all=1', AP['ffmpeg_hint'])]
    err('audio : commande ffmpeg', dl == [int(round(c['start_s'] * 1000)) for c in clips] and
        ('whole_dur=%.3f' % AP['total_seconds']) in AP['ffmpeg_hint'], 'adelay (ms) = départs, piste complétée à la '
        'durée du film')
    # a chapter's voice starts inside that chapter's first shot or after, and every shot of a chapter lies in
    # [previous chapter's voice end, next chapter's voice start + margin]
    offs = []
    for c in clips:
        first_shot = next(s for s in T['segments'] if s['chapter'] == c['chapter'])
        offs.append((c['chapter'], round((first_shot['frames'][0] - c['start_frame']) / L.FPS, 2)))
    warn('audio : voix et premier plan du chapitre', all(-3.0 <= d <= 2.5 for _, d in offs),
         'décalage (s) du premier plan de chaque chapitre par rapport au début de sa voix (négatif = l\'image '
         'précède) : %s' % ', '.join('ch%d %+.2f' % o for o in offs))


def check_subtitles(T):
    src = parse_srt((L.VOICE / 'narration.srt').read_text(encoding='utf-8'))
    film = parse_srt((L.FILM / 'subtitles_film.srt').read_text(encoding='utf-8'))
    VT = json.loads((L.VOICE / 'timing.json').read_text())
    CHS = {c['n']: c for c in VT['chapters']}
    clips = {c['chapter']: c for c in json.loads((L.FILM / 'audio_placement.json').read_text())['clips']}
    subs = T['subtitles']
    ok = len(film) == len(src) == len(subs) == 46 and [c['text'] for c in film] == [c['text'] for c in src]
    ok &= all(abs(a['start'] - b['start']) < 0.0015 and abs(a['end'] - b['end']) < 0.0015 for a, b in zip(film, subs))
    err('sous-titres : fichier', ok, '%d répliques, textes identiques à narration.srt, subtitles_film.srt = '
        'timeline.json subtitles[]' % len(film))
    # each cue keeps its offset inside its chapter file and stays inside the chapter's voice clip
    bad, overl = [], []
    for s, c in zip(subs, src):
        n = s['chapter']
        off_src = c['start'] - CHS[n]['start']
        off_film = s['start'] - clips[n]['start_s']
        if abs(off_src - off_film) > 0.0015 or s['start'] < clips[n]['start_s'] - 1e-6 or \
                s['end'] > clips[n]['end_s'] + 0.1:
            bad.append(s['i'])
    for a, b in zip(subs, subs[1:]):
        if b['start'] < a['end'] - 1e-6:
            overl.append((a['i'], b['i']))
    err('sous-titres : placement', not bad and not overl, 'chaque réplique garde son décalage dans son fichier de '
        'chapitre et reste dans la voix de ce chapitre ; aucune superposition%s'
        % ('' if not (bad or overl) else ' ; %s %s' % (bad, overl)))
    # the STT words (per chapter file) fall inside the cues : checks the chapter offsets of narration_full.wav
    W = json.loads((L.FILM / 'words.json').read_text())['chapters']
    outside, n = [], 0
    for ch, words in W.items():
        ch = int(ch)
        cues = [s for s in subs if s['chapter'] == ch]
        for w in words:
            if not _norm(w['w']):
                continue
            n += 1
            t = clips[ch]['start_s'] + 0.5 * (w['start'] + w['end'])
            if not any(s['start'] - 0.25 <= t <= s['end'] + 0.25 for s in cues):
                outside.append('%s ch%d %.2f' % (w['w'], ch, t))
    err('sous-titres / voix', len(outside) <= 2, '%d mots de la voix (STT) sur %d tombent dans une réplique de leur '
        'chapitre (± 0,25 s)%s' % (n - len(outside), n, '' if not outside else ' ; hors : %s' % outside[:6]))
    # subtitles under the end card
    card = next((s for s in T['segments'] if s['kind'] == 'card'), None)
    if card:
        on = [s['i'] for s in subs if s['out'] >= card['frames'][0]]
        flag = all(not s.get('burn_in', True) for s in subs if s['i'] in on)
        warn('sous-titres : carton final', flag, 'répliques pendant le carton 7.6 : %s (%s)'
             % (on, 'non incrustées : burn_in = false' if flag else 'incrustées par-dessus le carton'))
    over = ['%d (%s)' % (s['i'], '+'.join(s['over'])) for s in subs if s['burn_in'] and s['over']]
    warn('sous-titres sur les schémas plein écran', not over, 'répliques incrustées sur un schéma ou une carte plein '
         'écran, dont le bas porte du texte (monter la boîte ou l\'éclaircir) : %s' % ', '.join(over))
    short = [s['i'] for s in subs if s['end'] - s['start'] < 1.0]
    info('sous-titres', '%d répliques, de %s à %s ; plus courte %.2f s (%s)'
         % (len(subs), L.fmt_srt(subs[0]['start']), L.fmt_srt(subs[-1]['end']),
            min(s['end'] - s['start'] for s in subs), short))


# ----------------------------------------------------------------------------- 5. inserts and screen layout
def check_overlays(T):
    segs = {s['id']: s for s in T['segments']}
    cr = crank_of(T)
    bad = []
    for o in T.get('overlays', []):
        fr = [m[0] for m in o['map']]
        imgs = [m[1] for m in o['map']]
        ok = fr == list(range(o['frames'][0], o['frames'][1] + 1)) and all(1 <= i <= o['images'] for i in imgs)
        ch = segs[o['segment']]['chapter']
        chf = [s['frames'] for s in T['segments'] if s['chapter'] == ch]
        inside = (chf[0][0] <= fr[0] and fr[-1] <= chf[-1][1]) if o['sequence'].startswith('chapter_title_') else \
            (segs[o['segment']]['frames'][0] <= fr[0] and fr[-1] <= segs[o['segment']]['frames'][1])
        if not (ok and inside):
            bad.append(o['sequence'])
    err('incrustations : placement', not bad, '%d calques 2D (inserts.py), une image par image du film, dans leur plan'
        '%s' % (len(T.get('overlays', [])), '' if not bad else ' ; FAUX : %s' % bad))
    rendered = [o['sequence'] for o in T.get('overlays', []) if (L.ROOT / o['dir'] / (o['pattern'] % 1)).exists()]
    warn('incrustations rendues', len(rendered) == len(T.get('overlays', [])), 'séquences présentes sur disque : %d/%d '
         '(source des métadonnées : %s ; rendu : ~/voxtral-tts/bin/python tools/explainer/inserts.py)'
         % (len(rendered), len(T.get('overlays', [])), T.get('overlays_source')))
    # the machine follows the crank column of the synchronised inserts
    tim = None
    for name in ('phases', 'games_banner'):
        o = next((x for x in T.get('overlays', []) if x['sequence'] == name), None)
        if o is None:
            continue
        if tim is None:
            tim = _insert_columns(T)
        col = tim[name]
        diff = max(abs(cr[f] - L.f32(col[img])) for f, img in o['map'])
        err('incrustation %s = machine' % name, diff < 1e-6, 'manivelle de chaque image = colonne « manivelle » de '
            'l\'image affichée (écart max %.1e an)' % diff)


def _insert_columns(T):
    path = L.EXPLAINER / 'inserts' / 'timing.json'
    if path.exists():
        tim = json.loads(path.read_text())
    else:
        code = ('import sys, json; sys.path.insert(0, %r); import inserts; '
                'sys.stdout.write(json.dumps(inserts.timing(), ensure_ascii=False))'
                % str(L.ROOT / 'tools' / 'explainer'))
        out = subprocess.run([str(__import__('pathlib').Path.home() / 'voxtral-tts' / 'bin' / 'python'), '-c', code],
                             capture_output=True, text=True, cwd=str(L.ROOT))
        tim = json.loads(out.stdout)
    return {k: {r['image']: r['manivelle'] for r in tim[k]['manivelle_par_image']} for k in ('phases', 'games_banner')}


def _boxes_at(T, f, stacks):
    """Screen boxes (x0, y0, x1, y1, label) of every 2D element on frame f."""
    lay = T['layout']
    out = []
    x = next(x for x in T['frames'] if x['f'] == f)
    if x['counter']:
        out.append(tuple(lay['counter_box_px']) + ('compteur',))
    for o in T.get('overlays', []):
        if o['frames'][0] <= f <= o['frames'][1] and o.get('box_px'):
            out.append(tuple(o['box_px']) + (o['sequence'],))
    s = next(s for s in T['segments'] if s['frames'][0] <= f <= s['frames'][1])
    ins = s.get('inset')
    if ins:
        r = ins['rect_px']
        out.append((r[0], r[1], r[0] + r[2], r[1] + r[3], ins['name']))
    if s['kind'] == 'split' and f < s.get('inset_until', 10 ** 9):
        d = s['diagram']
        r = d.get('rect_px', [960, 0, 960, 1080])
        out.append((r[0], r[1], r[0] + r[2], r[1] + r[3], 'schéma ' + d['sequence']))
    for zone, items in stacks(s, f).items():
        z = lay['zones'][zone]
        h_tot = sum(c['size_px'][1] for c in items) + lay['stack_gap_px'] * (len(items) - 1)
        y = z['y'] if z['sens'] == 'bas' else z['y'] - h_tot
        for c in items:
            w, h = c['size_px']
            x0 = z['x'] - w if z['ancre'].endswith('droite') else z['x']
            out.append((x0, y, x0 + w, y + h, 'callout « %s »' % c['text']))
            y += h + lay['stack_gap_px']
    return out, s


def check_layout(T):
    def stacks(s, f):
        d = {}
        for c in sorted(s.get('callouts', []), key=lambda c: c['stack']):
            if c['in'] <= f <= c['out']:
                d.setdefault(c['zone'], []).append(c)
        return d

    hits, off = {}, {}
    for f in range(1, T['frame_end'] + 1):
        boxes, s = _boxes_at(T, f, stacks)
        for i, a in enumerate(boxes):
            if a[4].startswith('callout') and (a[0] < 0 or a[1] < 54 or a[2] > 1920 or a[3] > 880):
                off.setdefault((s['id'], a[4]), []).append(f)
            for b in boxes[i + 1:]:
                if not (a[4].startswith('callout') or b[4].startswith('callout') or 'chapter_title' in a[4] + b[4]):
                    continue
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    hits.setdefault((s['id'], a[4], b[4]), []).append(f)
    err('mise en page : chevauchements', not hits, 'callouts empilés dans les zones de la charte (overlay.py, tailles '
        'mesurées) : aucun ne touche un autre callout, le compteur, une incrustation, l\'incrustation 3D ou un '
        'titre de chapitre%s' % ('' if not hits else ' ; ' + ' ; '.join('%s : %s / %s (images %d-%d)'
                                                                        % (k[0], k[1], k[2], v[0], v[-1])
                                                                        for k, v in hits.items())))
    err('mise en page : zone de sécurité', not off, 'callouts entre y = 54 et y = 880 (au-dessus des sous-titres)%s'
        % ('' if not off else ' ; %s' % ['%s %s' % k for k in off]))


def check_audio_render(T):
    """--audio : runs the ffmpeg command of audio_placement.json into a temporary file and measures it : length,
    voice onset of each chapter (10 ms RMS > -40 dBFS), silence between chapters, voice inside every subtitle."""
    import shlex
    import tempfile
    import numpy as np
    AP = json.loads((L.FILM / 'audio_placement.json').read_text())
    ff = str(__import__('pathlib').Path.home() / '.local' / 'bin' / 'ffmpeg')
    with tempfile.TemporaryDirectory() as tmp:
        dst = tmp + '/voice_film.wav'
        args = shlex.split(AP['ffmpeg_hint'])
        args = [ff, '-y', '-loglevel', 'error'] + args[1:-1] + [dst]
        out = subprocess.run(args, capture_output=True, text=True, cwd=str(L.ROOT))
        if out.returncode:
            err('audio : rendu ffmpeg', False, out.stderr[-400:])
            return
        with wave.open(dst) as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768.0
    dur = len(x) / sr
    hop = sr // 100
    env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop]
    thr = 10 ** (-40 / 20)
    onsets, gaps = [], []
    for c in AP['clips']:
        i0, i1 = int(c['start_s'] * 100), int(c['end_s'] * 100)
        onsets.append(round(float(np.argmax(env[i0:i1] > thr)) / 100.0, 2))
        nxt = [d['start_s'] for d in AP['clips'] if d['chapter'] == c['chapter'] + 1] or [AP['total_seconds']]
        g = env[i1 + 2:int(nxt[0] * 100) - 2]
        gaps.append(float(g.max()) if len(g) else 0.0)
    mute = [s['i'] for s in T['subtitles'] if (env[int(s['start'] * 100):int(s['end'] * 100)] > thr).mean() < 0.3]
    ok = abs(dur - AP['total_seconds']) < 0.01 and all(0.0 <= o <= 0.4 for o in onsets) and max(gaps) < thr and \
        not mute and float(np.abs(x).max()) < 0.99
    err('audio : piste voix rendue', ok, 'ffmpeg -> %.2f s à %d Hz, crête %.2f ; la voix démarre %s s après le début de '
        'chaque fichier ; silence entre les chapitres (max %.0f dBFS) ; voix présente sous chaque réplique%s'
        % (dur, sr, float(np.abs(x).max()), onsets, 20 * math.log10(max(gaps) + 1e-9),
           '' if not mute else ' ; répliques muettes %s' % mute))


# ----------------------------------------------------------------------------- 6. optional : names in the .blend
BLEND_EXPR = r'''
import bpy, json
o = {ob.name: (ob.data.body if ob.type == 'FONT' else None) for ob in bpy.data.objects}
print('@@OBJ@@' + json.dumps({'objects': o, 'cameras': [c.name for c in bpy.data.objects if c.type == 'CAMERA'],
      'controller': {k: float(v) for k, v in bpy.data.objects['AM_Controller'].items()
                     if isinstance(v, (int, float))}}, ensure_ascii=False))
'''


def check_blend(T):
    out = subprocess.run([BLENDER, '-b', str(BLEND), '--factory-startup', '--python-expr', BLEND_EXPR],
                         capture_output=True, text=True, timeout=300)
    line = next((ln for ln in out.stdout.splitlines() if ln.startswith('@@OBJ@@')), None)
    if not line:
        err('blend : lecture', False, 'Blender n\'a rien renvoyé : %s' % out.stderr[-400:])
        return
    B = json.loads(line[7:])
    objs = B['objects']
    need = {a['object'] for a in T['anchors'].values()}
    need |= {t for h in T['highlights'] for t in h['targets'] if not t.startswith('FILM_')}
    miss = sorted(n for n in need if n not in objs)
    err('blend : objets', not miss, '%d objets cités (ancres, surlignages) présents dans am_atelier.blend ; les '
        'FILM_* sont à créer par le montage%s' % (len(need), '' if not miss else ' ; ABSENTS %s' % miss))
    films = sorted({t for h in T['highlights'] for t in h['targets'] if t.startswith('FILM_')})
    info('blend : objets à créer', ', '.join(films))
    txt = {k: objs.get(k) for k in ('txt_olympiad_1', 'txt_saros_glyph_112', 'txt_month_08')}
    g107 = objs.get('txt_saros_glyph_107')
    ok = txt['txt_olympiad_1'] is not None and 'ΟΛΥΜΠΙΑ' in txt['txt_olympiad_1'].replace('\n', ' ') and \
        txt['txt_saros_glyph_112'] is not None and txt['txt_saros_glyph_112'].split() == ['Σ', 'Η'] and \
        txt['txt_month_08'] is not None and 'ΠΑΧΩΝ' in txt['txt_month_08']
    err('blend : textes', ok, ('secteur des Jeux « %s », case 112 « %s », case 107 « %s », mois 8 « %s »'
        % (txt['txt_olympiad_1'], txt['txt_saros_glyph_112'], g107, txt['txt_month_08'])).replace('\n', ' / '))
    ctl = B['controller']
    err('blend : AM_Controller', all(k in ctl for k in ('crank', 'explode', 'patina')), 'propriétés %s' % ctl)


# ----------------------------------------------------------------------------- main
def main(argv=None, quiet=False):
    """Runs every check ; returns the number of ERRORs (quiet : prints only what is not OK)."""
    argv = sys.argv[1:] if argv is None else argv
    RESULTS.clear()
    T = load()
    check_keys(T)
    check_structure(T)
    check_crank_path(T)
    for b in T['beats']:
        check_beat(T, b)
    check_blinks(T)
    check_overlays(T)
    check_layout(T)
    check_audio(T)
    check_subtitles(T)
    if '--audio' in argv:
        check_audio_render(T)
    if '--blend' in argv:
        check_blend(T)
    n_err = sum(r['level'] == 'ERROR' for r in RESULTS)
    n_warn = sum(r['level'] == 'WARN' for r in RESULTS)
    n_ok = sum(r['level'] == 'OK' for r in RESULTS)
    (L.FILM / 'verification.json').write_text(json.dumps(
        {'ok': n_err == 0, 'errors': n_err, 'warnings': n_warn, 'passed': n_ok, 'results': RESULTS},
        ensure_ascii=False, indent=1))
    for r in RESULTS:
        if not quiet or r['level'] not in ('OK',):
            print('%-5s %s : %s' % (r['level'], r['check'], r['detail']))
    print('verification : %d OK, %d ERROR, %d WARN -> %s' % (n_ok, n_err, n_warn, L.FILM / 'verification.json'))
    return n_err


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
