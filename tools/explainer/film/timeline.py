"""Master timeline of the explainer film « Le ciel dans une boîte » (25 fps, 1920x1080, about 2 min 40 s).

    PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
    $PY tools/explainer/film/timeline.py              # writes build/out/explainer/film/timeline.json,
                                                      #   subtitles_film.srt, audio_placement.json, then runs
                                                      #   verify_beats.py (verification.json ; exit 1 on ERROR)
    $PY tools/explainer/film/timeline.py --no-verify  # outputs only
    $PY tools/explainer/film/timeline.py --blend      # + object / text checks in am_atelier.blend (read-only)

Inputs (nothing else is read ; am.blend / am_atelier.blend are never opened for writing):
  voice/timing.json (7 chapter files, durations), voice/narration.srt (46 cues, times in narration_full.wav),
  film/words.json (STT word times per chapter file, words.py), diagrams/timing.json (+ the PNG sequences),
  tools/explainer/inserts.py metadata (inserts/timing.json once rendered, else inserts.timing() run in the venv
  ~/voxtral-tts/bin/python, nothing rendered), tools/explainer/overlay.py (box sizes of the callouts, same venv),
  and tools/explainer/engine.py (instants the story needs : Games sector entry, Saros cell entries, Mars stations).

How the film is laid out
  * the seven chapter files are placed whole : 0.6 s pre-roll, a gap after each chapter chosen for the picture
    (reassembly of 1.4, the white phase ball of 3.4, the split screen 4.3 + the 180° orbit of 5.1 ...), and a silent
    end card of END_CARD s after chapter 7 ; cue times of narration.srt keep their offset inside their chapter file ;
  * every shot of script.md is laid out inside its chapter ; shot changes and key moves are tied to WORDS of the
    narration (W(ch, 'olympia') = film time of that word), cuts LEAD the word by CUT_LEAD s ;
  * AM_Controller crank / explode / patina are key lists {f, v, ipo, ease} with Blender's own interpolations ;
    filmlib.eval_keys reproduces Blender, so the value of every frame is known here (frames[], float32) ;
  * where a 2D sequence shows the same crank as the machine (diagram retrograde_split in 4.3, inserts « phases » in
    3.4 and « games_banner » in 5.3) the crank follows the sequence's column « manivelle » image by image ;
  * cameras are pose lists interpolated with easings (baked per frame by build_film.py) ;
  * highlights are emission keys on duplicated materials ; callouts are French texts with in/out frames, assigned
    to the stacks (zones) of the overlay charter (overlay.py), measured, and checked for overlaps.

timeline.json (every frame range is INCLUSIVE ; frame f starts at t = (f - 1) / 25 s)
  title, fps, resolution, frame_start (1), frame_end, total_seconds, conventions (the rules below, in short)
  audio[]        = audio_placement.json clips : {chapter, file, start_s, start_frame, start_sample_24k/48k,
                   duration_s, end_s}
  chapters[]     {n, audio_start_s, audio_start_frame, audio_end_s, frames [a, b], seconds, shots [ids]}
  segments[]     one per shot, contiguous over 1..frame_end :
                 {id '4.2', chapter, kind 3d|split|diagram|map|card, t0, t1, frames, seconds, render_3d, mode
                  case|front|back|front_to_back|wide, cadrage (FR), camera {name, poses[]}, inset? (second camera
                  rendered into rect_px), diagram? {sequence, dir, pattern, placement, map [[film_frame, image]],
                  rect_px?}, inset_until?, callouts[], texts_in_picture?, flags : labels (AM_LABELS), mars_trail,
                  ghost_b1, counter (False = hidden), counter_from, flash, crank_note, sunbeam, card ...}
      pose       {f, target, az, el, dist, lens, up, shift, ease} : camera = target + dist * (cos el cos az,
                  cos el sin az, sin el) (world, degrees, mm), looking at target, roll from up ; target = [x, y, z]
                  | {anchor, crank} (anchor position at that crank) | {track: anchor} (followed per frame) ;
                  ease = easing of the move to the next pose (SINE_IN_OUT, SINE_IN, SINE_OUT, LINEAR)
      callout    {text, in, out, style, anchor?, pos?, honesty?, kind normal|hyp|modele|illustration|exemple,
                  zone haut_droite|haut_gauche|bas_gauche|bas_droite, stack (rank in the zone, top first),
                  item {text|sub, kind} (= overlay.render_callouts item), size_px [w, h], clamped_from?}
  overlays[]     2D layers of inserts.py : {sequence, segment, dir, pattern, images, rgba, box_px, placement,
                  frames, map [[film_frame, image]], anchor?, crank_sync?, background?, texts?}
  overlays_source, layout {counter_box_px, zones, stack_gap_px}
  anchors{}      name -> {type center|point|radial|tip|at_crank, object, ...} (projected per frame by anchors.py)
  controller     {crank|explode|patina: [{f, v (float32), ipo CONSTANT|LINEAR|SINE|QUAD|CUBIC, ease EASE_IN|
                  EASE_OUT|EASE_IN_OUT}]} : the ipo/ease of a key applies to the span AFTER it ; set the easing
                  explicitly in Blender (AUTO is not EASE_IN_OUT for every type)
  highlights[]   {id, targets (objects ; FILM_* to create in the working copy), kind glow|sweep|ghost, color,
                  keys [{f, v}], sweep?, width_deg?}
  blinks_6_1[]   {cell, glyph, frame_entry, crank_entry} (Saros cells with a computed sign crossed during 6.1)
  beats[]        {id, segment, frame, crank, check, params, expect, word, word_frames, window, hold} : what the
                  machine must show on that frame, checked against engine.py by verify_beats.py
  engine_instants {olympia_entry, saros_entry {cell: crank}, mars_stations, mars_opposition}
  subtitles[]    {i, chapter, start, end (film s), in, out (frames), text, segments, over, burn_in}
  frames[]       {f, seg, crank (float32, what Blender evaluates), explode, patina, counter (text or null)}

subtitles_film.srt : narration.srt shifted to film time (46 cues, all of them ; burn_in says which to burn).
audio_placement.json : clips + an ffmpeg command (adelay per chapter, padded to the film length, 48 kHz).
"""
import json
import math
import pathlib
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import filmlib as L  # noqa: E402

sys.path.insert(0, str(L.ROOT / 'tools' / 'explainer'))

FPS = L.FPS
PREROLL = 0.6
GAP_AFTER = {1: 1.4, 2: 1.0, 3: 1.0, 5: 1.0, 6: 1.0}     # gap after chapter 4 = end of the split 4.3 + orbit lead
END_CARD = 4.0
CUT_LEAD = 0.08                 # picture cuts 2 frames before the word
GOLD = (1.0, 0.70, 0.28)
MARS_RED = (1.0, 0.22, 0.10)
SILVER = (0.85, 0.90, 1.0)

# ----------------------------------------------------------------------------- inputs
VT = json.loads((L.VOICE / 'timing.json').read_text())
WORDS = json.loads((L.FILM / 'words.json').read_text())['chapters']
DIAG = json.loads((L.DIAGRAMS / 'timing.json').read_text())
CH = {c['n']: c for c in VT['chapters']}
CUE_CHAPTER = {}                # srt cue index -> chapter
for n, (a, b) in {1: (1, 5), 2: (6, 9), 3: (10, 16), 4: (17, 21), 5: (22, 27), 6: (28, 35), 7: (36, 46)}.items():
    for i in range(a, b + 1):
        CUE_CHAPTER[i] = n


def parse_srt(path):
    cues = []
    for block in re.split(r'\n\s*\n', path.read_text(encoding='utf-8').strip()):
        lines = block.strip().splitlines()
        idx = int(lines[0])
        a, b = [x.strip() for x in lines[1].split('-->')]
        sec = lambda s: int(s[0:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8]) + int(s[9:12]) / 1000
        cues.append({'i': idx, 'start': sec(a), 'end': sec(b), 'text': '\n'.join(lines[2:])})
    return cues


CUES = parse_srt(L.VOICE / 'narration.srt')

# 2D inserts of tools/explainer/inserts.py : their timing.json once rendered, else the same metadata computed by
# inserts.timing() in the venv (matplotlib ; nothing is rendered or written)
VENV_PY = pathlib.Path.home() / 'voxtral-tts' / 'bin' / 'python'
INSERTS_DIR = L.EXPLAINER / 'inserts'


def _insert_timing():
    path = INSERTS_DIR / 'timing.json'
    if path.exists():
        return json.loads(path.read_text()), 'build/out/explainer/inserts/timing.json'
    code = ('import sys, json; sys.path.insert(0, %r); import inserts; '
            'sys.stdout.write(json.dumps(inserts.timing(), ensure_ascii=False))' % str(L.ROOT / 'tools' / 'explainer'))
    out = subprocess.run([str(VENV_PY), '-c', code], capture_output=True, text=True, cwd=str(L.ROOT))
    if out.returncode:
        raise SystemExit('inserts.timing() a échoué :\n' + out.stderr[-1500:])
    return json.loads(out.stdout), 'tools/explainer/inserts.py timing() (séquences pas encore rendues)'


INS, INS_SOURCE = _insert_timing()

# ----------------------------------------------------------------------------- chapter offsets (film time)
A = {1: PREROLL}
A[2] = A[1] + CH[1]['duration'] + GAP_AFTER[1]
A[3] = A[2] + CH[2]['duration'] + GAP_AFTER[2]
A[4] = A[3] + CH[3]['duration'] + GAP_AFTER[3]


def _norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn' and (c.isalnum() or c == "'"))


def W(ch, key, n=1, end=False):
    """Film time of the n-th word of chapter ch whose normalised spelling starts with key (STT spelling)."""
    k = _norm(key)
    hits = [w for w in WORDS[str(ch)] if _norm(w['w']) == k]           # whole word first ('en' != 'enfermé')
    if not hits:
        hits = [w for w in WORDS[str(ch)] if _norm(w['w']).startswith(k)]
    if len(hits) < n:
        raise KeyError('word %r #%d not found in chapter %d' % (key, n, ch))
    return A[ch] + hits[n - 1]['end' if end else 'start']


def CUE(i, end=False):
    """Film time of srt cue i (for the one sentence the STT skipped)."""
    c = CUES[i - 1]
    ch = CUE_CHAPTER[i]
    return A[ch] + (c['end' if end else 'start'] - CH[ch]['start'])


# gap after chapter 4 : the split 4.3 (diagram images 29-151 = 123 frames) starts on « comme dans le ciel »
T_43 = W(4, 'comme') - CUT_LEAD
SPLIT_IMAGES = (29, 151)
T_51 = T_43 + (SPLIT_IMAGES[1] - SPLIT_IMAGES[0] + 1) / FPS
A[5] = T_51 + 0.2               # « Retournons » 0.32 s later, during the orbit
A[6] = A[5] + CH[5]['duration'] + GAP_AFTER[5]
A[7] = A[6] + CH[6]['duration'] + GAP_AFTER[6]
T_END = A[7] + CH[7]['duration'] + END_CARD
N_FRAMES = int(math.ceil(T_END * FPS))

F = L.frame_of
cut = lambda t: t - CUT_LEAD

# ----------------------------------------------------------------------------- engine instants
import engine as E  # noqa: E402
M = E.get_machine(False)


def _bisect(fun, a, b):
    fa = fun(a)
    for _ in range(64):
        c = 0.5 * (a + b)
        if fun(c) == fa:
            a = c
        else:
            b = c
    return 0.5 * (a + b)


import numpy as _np  # noqa: E402
T_OLYMPIA = _bisect(lambda t: int(M.olympiad_sector(_np.array([t]))[0]), 5.85, 5.95)       # 5.91111
SAROS_ENTRY = {}
_t = 5.5
for _n in range(70, 115):
    _t = SAROS_ENTRY[_n] = _bisect(lambda x: int(M.saros_cell(_np.array([x]))[0]) >= _n, _t, _t + 0.2)
GLYPHS = {c['case']: c['glyph'] for c in M.engraved_table()['cells'] if c['glyph']}
# Mars stations = sign changes of the displayed longitude rate (engine: 2.21342 and 2.41314, opposition 2.3133)
MARS_STATIONS = (_bisect(lambda t: bool(M.rate('mars', t) > 0), 2.15, 2.30),
                 _bisect(lambda t: bool(M.rate('mars', t) > 0), 2.35, 2.48))
# fastest retrogradation = minimum of the rate (= opposition to the mean Sun, 2.3133, in this model)
T_MARS_OPPOSITION = _bisect(lambda t: bool(M.rate('mars', t + 1e-4) < M.rate('mars', t - 1e-4)), 2.25, 2.38)

# ----------------------------------------------------------------------------- key helpers
def key(t, v, ipo='LINEAR', ease='EASE_IN_OUT'):
    return {'f': F(t), 'v': v, 'ipo': ipo, 'ease': ease}


def accel_split(v0, v1, d1, d2):
    """Value where a QUAD ease-in span (duration d1) hands over to a SINE ease-out span (d2) with equal speed."""
    # 2 (vs - v0) / d1 = (pi/2) (v1 - vs) / d2
    a, b = 2.0 / d1, (math.pi / 2) / d2
    return (a * v0 + b * v1) / (a + b)


def cruise(t0, t1, v0, v1, d_in, d_out):
    """Keys of a ramp v0 -> v1 over [t0, t1] with a constant cruising speed : QUAD ease-in during d_in, LINEAR, SINE
    ease-out during d_out ; the speed is continuous at both hand-overs (lower peak speed than one SINE span, so the
    fast front pointers strobe less)."""
    speed = (v1 - v0) / ((t1 - t0) - d_in / 2.0 - d_out * (1.0 - 2.0 / math.pi))
    va = v0 + speed * d_in / 2.0
    vb = v1 - speed * d_out * 2.0 / math.pi
    return [key(t0, v0, 'QUAD', 'EASE_IN'), key(t0 + d_in, va, 'LINEAR'), key(t1 - d_out, vb, 'SINE', 'EASE_OUT'),
            key(t1, v1, 'CONSTANT')]


# ----------------------------------------------------------------------------- anchors (callouts + camera targets)
# type center : bbox centre of object (crank 0, explode 0) ; point : world point at crank 0, carried by object ;
# radial : direction of the object's centre from the front axis, at radius r / height z ; tip : farthest vertex from
# the axis (cx, cy) ; at_crank : the object's centre evaluated at a crank, then fixed.
ANCHORS = {
    'case_lid': {'type': 'point', 'object': 'case_cover_front', 'world': [0.0, -10.0, 67.0]},
    'b1_rim': {'type': 'point', 'object': 'b1', 'world': [49.8, -41.8, 6.6]},
    'machine_center': {'type': 'point', 'object': 'front_plate', 'world': [0.0, -10.0, 41.5]},
    'crank_knob': {'type': 'center', 'object': 'crank_knob'},
    'dial_center': {'type': 'point', 'object': 'front_plate', 'world': [0.0, 0.0, 44.0]},
    'calendar_ring': {'type': 'point', 'object': 'calendar_ring', 'world': [48.2, -57.5, 42.4]},
    'zodiac_ring': {'type': 'point', 'object': 'zodiac_ring', 'world': [62.0, -22.6, 41.6]},
    'sun_sphere': {'type': 'center', 'object': 'marker_trueSun'},
    'date_on_calendar': {'type': 'point', 'object': 'date_pointer', 'world': [74.5, 0.0, 43.0]},
    'sign_under_sun': {'type': 'radial', 'object': 'marker_trueSun', 'radius': 66.0, 'z': 41.7},
    'moon_tip': {'type': 'tip', 'object': 'moon_pointer', 'axis': [0.0, 0.0], 'frac': 0.93},
    'moon_mid': {'type': 'tip', 'object': 'moon_pointer', 'axis': [0.0, 0.0], 'frac': 0.55},
    'phase_ball': {'type': 'point', 'object': 'phase_sphere_dark', 'world': [13.0, 1.0, 52.7]},
    'dragon_head': {'type': 'point', 'object': 'dragon_hand', 'world': [28.5, 0.0, 46.8]},
    'dragon_tail': {'type': 'point', 'object': 'dragon_hand', 'world': [-28.5, 0.0, 46.8]},
    'mars_marker': {'type': 'center', 'object': 'marker_mars'},
    'metonic_slider': {'type': 'center', 'object': 'metonic_slider'},
    'metonic_spiral': {'type': 'point', 'object': 'metonic_cells', 'world': [-52.0, 105.0, -16.5]},
    'games_sector': {'type': 'center', 'object': 'txt_olympiad_1'},
    'games_pointer': {'type': 'tip', 'object': 'olympiad_pointer', 'axis': [-24.40035, 62.976], 'frac': 0.9},
    'saros_slider': {'type': 'center', 'object': 'saros_slider'},
    'saros_spiral': {'type': 'point', 'object': 'saros_cells', 'world': [-60.0, -100.0, -16.5]},
    'empty_cells': {'type': 'at_crank', 'object': 'saros_slider', 'crank': round(SAROS_ENTRY[110] + 0.04, 4)},
    'glyph_112': {'type': 'center', 'object': 'txt_saros_glyph_112'},
    'exeligmos_pointer': {'type': 'tip', 'object': 'exeligmos_pointer', 'axis': [-0.26, -107.52], 'frac': 0.8},
    'exeligmos_dial': {'type': 'point', 'object': 'exeligmos_dial', 'world': [-0.26, -107.52, -16.5]},
    'parapegma_top': {'type': 'center', 'object': 'parapegma_1'},
    'parapegma_bottom': {'type': 'center', 'object': 'parapegma_2'},
    'pachon': {'type': 'center', 'object': 'txt_month_08'},
    'window': {'type': 'point', 'object': 'ATL_window_sky', 'world': [-562.5, 80.1, 546.7]},
}

# ----------------------------------------------------------------------------- camera poses
BACK_UP = (0.0, 1.0, 0.0)
GAMES_UP = (-0.6018, -0.7986, 0.0)
Z_UP = (0.0, 0.0, 1.0)


def pose(t, target, az, el, dist, lens=85.0, up=Z_UP, shift=(0.0, 0.0), ease='SINE_IN_OUT'):
    """Camera pose at film time t: camera at target + dist * dir(az, el) (degrees, world), looking at target.
    ease = easing of the move from this pose to the next one."""
    return {'f': F(t), 'target': target, 'az': az, 'el': el, 'dist': dist, 'lens': lens, 'up': list(up),
            'shift': list(shift), 'ease': ease}


def at(anchor, crank):
    return {'anchor': anchor, 'crank': crank}


# ----------------------------------------------------------------------------- the shots
SEG = []


def seg(sid, ch, kind, t0, t1, **kw):
    d = {'id': sid, 'chapter': ch, 'kind': kind, 't0': t0, 't1': t1}
    d.update(kw)
    SEG.append(d)
    return d


def co(text, t_in, t_out, anchor=None, pos=None, style='label', **kw):
    d = {'text': text, 'in': F(t_in), 'out': F(t_out), 'style': style}
    if anchor:
        d['anchor'] = anchor
    if pos:
        d['pos'] = list(pos)
    d.update(kw)
    return d


crank_keys, explode_keys, patina_keys = [], [], []
HL = []                        # highlights


def hl(hid, targets, kind, keys, color=GOLD, **kw):
    d = {'id': hid, 'targets': targets, 'kind': kind, 'color': list(color),
         'keys': [{'f': F(t), 'v': v} for t, v in keys]}
    d.update(kw)
    HL.append(d)
    return d


def pulse(t_on, t_off, peak, rise=0.35, fall=0.5):
    return [(t_on - 0.01, 0.0), (t_on + rise, peak), (t_off - fall, peak), (t_off, 0.0)]


OVL = []                       # 2D layers from tools/explainer/inserts.py, composited over the picture


def ovl(name, sid, f0, images, placement, source=None, **kw):
    """Insert sequence `name` shown from film frame f0, one image number per film frame (images list)."""
    meta = INS[source or name]
    base = INS[meta['identique_a']] if 'identique_a' in meta else meta
    d = {'sequence': name, 'segment': sid, 'dir': 'build/out/explainer/inserts/' + name, 'pattern': '%04d.png',
         'images': meta.get('images', base['images']), 'rgba': meta.get('rgba', base.get('rgba', True)),
         'box_px': base.get('boite'), 'placement': placement, 'frames': [f0, f0 + len(images) - 1],
         'map': [[f0 + i, int(img)] for i, img in enumerate(images)]}
    d.update(kw)
    OVL.append(d)
    return d


def column(name):
    """Crank column of an insert : {image: crank}."""
    return {r['image']: r['manivelle'] for r in INS[name]['manivelle_par_image']}


# ======================================================================== CHAPTER 1
t12 = cut(W(1, 'eclipse'))
t12b = cut(W(1, 'face'))            # « phases » (STT: face)
t12c = cut(W(1, 'planete'))
t12d = cut(W(1, 'jeux'))
t13 = cut(W(1, 'en', 1))            # « En 1900 »
t14 = cut(W(1, 'en', 2))            # « En 1902 »
t_app = W(1, 'apprenons')
t21 = cut(W(2, 'sur'))              # « Sur le côté, une manivelle »

seg('1.1', 1, '3d', 0.0, t12, mode='case', crank_note='0 (boîtier fermé)',
    cadrage="Atelier en lumière du jour, boîtier en bois fermé sur l'établi, lent travelling avant ; un rai de soleil "
            "(fente devant la fenêtre) glisse sur le couvercle",
    camera={'name': 'CAM_1_1', 'poses': [pose(0.0, [0.0, -10.0, 20.0], -46.0, 24.0, 1080.0, 50.0),
                                         pose(t12, [0.0, -10.0, 26.0], -52.0, 28.0, 800.0, 50.0)]},
    sunbeam={'keys': [[F(0.0), -0.55], [F(t12), 0.45]], 'slit_mm': 190.0,
             'note': 'FILM_sunblind: panneau percé d\'une fente, hors de la fenêtre, visible des seules ombres'},
    callouts=[])
seg('1.2a', 1, '3d', t12, t12b, mode='front', flash='éclipses', crank_note='9.014 : Soleil, Lune et aiguille du Dragon alignés',
    cadrage='Éclair 1 : face avant, centre du cadran serré',
    camera={'name': 'CAM_1_2a', 'poses': [pose(t12, [0.0, 0.0, 49.0], -50.0, 70.0, 440.0),
                                          pose(t12b, [0.0, 0.0, 49.0], -50.0, 70.0, 405.0)]})
seg('1.2b', 1, '3d', t12b, t12c, mode='front', flash='phases', crank_note='0.99 : boule des phases à moitié claire',
    cadrage='Éclair 2 : très gros plan sur la boule des phases',
    camera={'name': 'CAM_1_2b', 'poses': [pose(t12b, at('phase_ball', 0.99), -50.0, 48.0, 150.0, 100.0),
                                          pose(t12c, at('phase_ball', 0.99), -50.0, 48.0, 132.0, 100.0)]})
seg('1.2c', 1, '3d', t12c, t12d, mode='front', labels=True, flash='planètes', crank_note='2.31 : sphères et étiquettes',
    cadrage='Éclair 3 : les sphères des planètes et leurs étiquettes',
    camera={'name': 'CAM_1_2c', 'poses': [pose(t12c, [0.0, 0.0, 46.0], -38.0, 58.0, 560.0),
                                          pose(t12d, [0.0, 0.0, 46.0], -42.0, 58.0, 515.0)]})
seg('1.2d', 1, '3d', t12d, t13, mode='back', flash='Jeux', crank_note='5.95 : aiguille dans ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ',
    cadrage='Éclair 4 : cadran des Jeux (CAM_games_close)',
    camera={'name': 'CAM_1_2d', 'poses': [pose(t12d, [-24.40035, 62.976, -16.5], -70.0, -74.0, 320.0, 120.0, GAMES_UP),
                                          pose(t13, [-24.40035, 62.976, -16.5], -70.0, -74.0, 290.0, 120.0, GAMES_UP)]})
seg('1.3', 1, 'map', t13, t14, render_3d=False, insert='map',
    cadrage='Carte animée plein écran (incrustation « map » de inserts.py, opaque) : Péloponnèse, Cythère, '
            'Anticythère, Crète ; un point « épave » pulse près d\'Anticythère ; les textes « Printemps 1900 », '
            '« Pêcheurs d\'éponges de Symi », « 40–50 m de fond » sont dans l\'incrustation',
    callouts=[])
_n13 = F(t14) - F(t13)
ovl('map', '1.3', F(t13), [min(i + 1, INS['map']['images']) for i in range(_n13)], 'plein cadre, opaque (remplace la 3D)',
    texts=INS['map']['textes'])
t14_pull = W(1, 'bronze')
seg('1.4', 1, '3d', t14, t21, mode='front', patina_note='1 puis 0,15 sur « Apprenons »',
    cadrage="Gros plan en lumière rasante sur la grande roue b1 corrodée (vue éclatée), recul jusqu'à la vue éclatée "
            "entière, puis, pendant le remontage, jusqu'au trois-quarts avant (front34)",
    camera={'name': 'CAM_1_4', 'poses': [
        pose(t14, [26.0, -30.0, 19.0], -34.0, 16.0, 250.0, 85.0),
        pose(t14_pull, [22.0, -26.0, 22.0], -40.0, 18.0, 290.0, 85.0),
        pose(t_app - 0.2, [0.0, -10.0, 52.0], -50.0, 22.0, 820.0, 40.0),
        pose(t_app + 2.9, [0.0, -18.0, 13.0], -49.0, 27.8, 380.0, 50.0, ease='LINEAR'),
        pose(t21, [0.0, -16.0, 14.0], -47.0, 28.5, 360.0, 50.0)]},
    callouts=[co('1902 : une roue dentée', W(1, 'en', 2) + 0.2, t14_pull + 1.6, anchor='b1_rim', style='title'),
              co('82 fragments · ≈ 1/3', W(1, 'bronze'), t_app - 0.3, pos=(0.06, 0.80)),
              co('30 roues dentées conservées', W(1, 'apparait'), t_app - 0.3, pos=(0.06, 0.87)),
              co('Notre reconstruction · 69 roues', t_app + 1.6, t21 - 0.1, anchor='machine_center', style='title')])
crank_keys += [key(0.0, 0.0, 'CONSTANT'), key(t12, 9.014, 'CONSTANT'), key(t12b, 0.99, 'CONSTANT'),
               key(t12c, 2.31, 'CONSTANT'), key(t12d, 5.95, 'CONSTANT'), key(t13, 0.0, 'CONSTANT')]
patina_keys += [key(0.0, 0.15, 'CONSTANT'), key(t14, 1.0, 'CONSTANT'), key(t_app, 1.0, 'SINE'),
                key(t_app + 2.6, 0.15, 'CONSTANT')]
explode_keys += [key(0.0, 0.0, 'CONSTANT'), key(t14, 1.0, 'CONSTANT'), key(t_app, 1.0, 'SINE'),
                 key(t_app + 2.6, 0.0, 'CONSTANT')]

# ======================================================================== CHAPTER 2
t_tourn = W(2, 'tournez')
t22 = cut(W(2, 'en', 1))            # « En avant »
t_arr = W(2, 'en', 2)               # « en arrière »
t23 = cut(W(2, 'un'))               # « Un peu plus de quatre tours et demi »
t31 = A[3] + 0.1
seg('2.1', 2, '3d', t21, t22, mode='front', counter_from=t_tourn,
    cadrage='Gros plan sur la manivelle (côté droit, arbre a), puis recul qui découvre les aiguilles',
    camera={'name': 'CAM_2_1', 'poses': [
        pose(t21, [104.0, 0.0, 30.0], -18.0, 20.0, 250.0, 85.0),
        pose(W(2, 'toutes') - 0.4, [100.0, -2.0, 31.0], -24.0, 24.0, 270.0, 85.0),
        pose(t22, [30.0, -8.0, 38.0], -42.0, 36.0, 560.0, 55.0)]},
    counter_note='le compteur « Temps écoulé » entre sur « Tournez-la » (counter_from) et reste jusqu\'au plan 7.5 '
                 '(sauf 4.3, schémas plein écran et carton)',
    callouts=[co('La manivelle = le temps', W(2, 'une'), t22 - 0.05, anchor='crank_knob', style='title')])
hl('crank', ['crank_knob', 'crank_arm'], 'glow', pulse(W(2, 'une'), t_tourn + 1.2, 1.2))
crank_keys += [key(t21, 0.0, 'CONSTANT'), key(t_tourn, 0.0, 'LINEAR'), key(t22, 0.6, 'LINEAR')]
seg('2.2', 2, '3d', t22, t23, mode='front',
    cadrage='Trois-quarts avant, toutes les aiguilles dans le champ',
    camera={'name': 'CAM_2_2', 'poses': [pose(t22, [0.0, -8.0, 32.0], -47.0, 37.0, 480.0, 50.0),
                                         pose(t23, [0.0, -8.0, 32.0], -51.0, 38.0, 455.0, 50.0)]},
    callouts=[co('En arrière : le passé', t_arr, t23 - 0.05, pos=(0.06, 0.82), style='title')])
crank_keys += [key(t22, 0.6, 'SINE'), key(t_arr - 0.1, 0.7, 'SINE'), key(t23 - 0.1, 0.3, 'CONSTANT')]
_d1, _d2 = (t31 - 0.35 - 0.8) - (t23 + 0.15), 0.8
_vs = accel_split(0.3, 0.972, _d1, _d2)
seg('2.3', 2, '3d', t23, t31, mode='front', ghost_b1=True,
    cadrage='Face avant ; la grande roue b1 apparaît en fantôme doré derrière le cadran et tourne une fois',
    # the crank knob (anchor of « ≈ 4,6 tours = 1 an ») stays in the picture while it turns (y <= 1050 px)
    camera={'name': 'CAM_2_3', 'poses': [pose(t23, [18.0, -8.0, 34.0], -50.0, 72.0, 660.0),
                                         pose(t31, [18.0, -8.0, 34.0], -50.0, 71.0, 630.0)]},
    callouts=[co('≈ 4,6 tours = 1 an', t23 + 0.3, t31 - 0.05, anchor='crank_knob', style='label'),
              co('Grande roue : 1 tour/an', t23 + 0.9, t31 - 0.05, anchor='dial_center', style='title')])
hl('b1_ghost', ['FILM_b1_ghost'], 'ghost', [(t23 + 0.05, 0.0), (t23 + 0.5, 0.5), (t31 - 0.35, 0.5), (t31, 0.0)])
crank_keys += [key(t23 + 0.15, 0.3, 'QUAD', 'EASE_IN'), key(t31 - 0.35 - 0.8, _vs, 'SINE', 'EASE_OUT'),
               key(t31 - 0.35, 0.972, 'CONSTANT')]

# ======================================================================== CHAPTER 3
t32 = cut(W(3, 'la', 1))            # « La sphère dorée »
t33 = cut(W(3, 'la', 3))            # « La Lune fait le tour »
t34 = cut(W(3, 'sa'))               # « Sa petite boule »
t_sup = CUE(15)                     # « Aiguilles superposées : noire, nouvelle lune » (absent de l'STT)
t_opp = W(3, 'opposee')
t_bl = W(3, 'blanche')
t41 = A[4]
seg('3.1', 3, '3d', t31, t32, mode='front',
    cadrage='Face avant rapprochée (CAM_front_close) ; un reflet balaie l\'anneau extérieur (calendrier), puis '
            'l\'anneau intérieur (zodiaque)',
    camera={'name': 'CAM_3_1', 'poses': [pose(t31, [0.0, 0.0, 44.0], -50.4, 68.0, 760.0),
                                         pose(t32, [2.0, -1.0, 44.0], -50.4, 68.0, 660.0, ease='LINEAR')]},
    callouts=[co('Calendrier égyptien · 365 j', W(3, 'calendrier'), t32 - 0.05, anchor='calendar_ring'),
              co('Zodiaque · 12 signes', W(3, 'et', 1), t32 - 0.05, anchor='zodiac_ring')])
hl('ring_calendar', ['calendar_ring'], 'sweep', pulse(W(3, 'calendrier') - 0.1, W(3, 'et', 1) + 0.2, 1.6, 0.3, 0.4),
   sweep=[[F(W(3, 'calendrier') - 0.1), 90.0], [F(W(3, 'et', 1) + 0.2), 90.0 - 400.0]], width_deg=38.0)
hl('ring_zodiac', ['zodiac_ring'], 'sweep', pulse(W(3, 'et', 1), t32 + 0.3, 1.6, 0.3, 0.4),
   sweep=[[F(W(3, 'et', 1)), 90.0], [F(t32 + 0.3), 90.0 - 400.0]], width_deg=38.0)
crank_keys += [key(t31, 0.972, 'CONSTANT')]
seg('3.2', 3, '3d', t32, t33, mode='front',
    cadrage='Même cadrage, léger rapprochement : la sphère dorée et l\'aiguille de date s\'allument ; deux traits fins '
            '(montage) vers l\'anneau extérieur (date) et l\'anneau intérieur (signe)',
    camera={'name': 'CAM_3_2', 'poses': [pose(t32, [2.0, -1.0, 44.0], -50.4, 68.0, 660.0, ease='LINEAR'),
                                         pose(t33, [8.0, -4.0, 45.0], -50.4, 67.0, 590.0)]},
    lines_2d=[{'from': 'sun_sphere', 'to': 'date_on_calendar', 'in': F(W(3, 'date')), 'out': F(t33)},
              {'from': 'sun_sphere', 'to': 'sign_under_sun', 'in': F(W(3, 'signe')), 'out': F(t33)}],
    callouts=[co('Soleil : date + signe', W(3, 'sphere') + 0.2, t33 - 0.05, anchor='sun_sphere', style='title'),
              co('Sphère dorée : citée par l\'inscription · son engrenage : hypothèse', W(3, 'soleil') + 0.3,
                 t33 - 0.05, pos=(0.05, 0.90), style='small', honesty=True)])
hl('sun', ['marker_trueSun', 'date_pointer'], 'glow', pulse(W(3, 'sphere'), t33 + 0.2, 2.0))
seg('3.3', 3, '3d', t33, t34, mode='front',
    cadrage="L'aiguille de la Lune, surlignée (superposée au Soleil à 0,972)",
    camera={'name': 'CAM_3_3', 'poses': [pose(t33, at('moon_mid', 0.972), -50.0, 64.0, 430.0),
                                         pose(t34, at('moon_mid', 0.972), -52.0, 64.0, 385.0)]},
    overlays_2d=[{'what': 'courbe de vitesse de la Lune sur un mois (option, non fournie)', 'in': F(W(3, 'vitesse')),
                  'out': F(t34)}],
    callouts=[co('Lune : 1 tour/mois', W(3, 'lune', 1) + 0.2, t34 - 0.05, anchor='moon_tip', style='title'),
              co('Vitesse variable (Hipparque)', W(3, 'vitesse'), t34 - 0.05, pos=(0.06, 0.86))])
hl('moon', ['moon_pointer'], 'glow', pulse(t33 + 0.1, t34 + 0.1, 1.6), color=SILVER)
# 3.4 : the insert « phases » drives the crank (its column « manivelle », image by image) ; image 91 (start of the ramp
# 0.972 -> 1.009) on « Opposées », as its timing.json asks ; the ball is white (1.009) at image 141, on « pleine lune »
PH = INS['phases']
_ph_col = column('phases')
_ph_go, _ph_arr = PH['segments']['manivelle_0972_1009']
f_ph_go = F(t_opp)
f_ph1 = f_ph_go - (_ph_go - 1)
t_full = L.time_of(f_ph_go + (_ph_arr - _ph_go))
seg('3.4', 3, '3d', t34, t41, mode='front',
    cadrage='Gros plan sur le centre du cadran : aiguilles et boule des phases ; en incrustation (caméra 2), très '
            'gros plan sur la boule qui passe du noir au blanc',
    camera={'name': 'CAM_3_4', 'poses': [pose(t34, [9.0, 0.0, 50.0], -50.0, 63.0, 380.0),
                                         pose(t41, [7.0, 0.0, 50.0], -52.0, 63.0, 540.0, shift=(-0.03, 0.05))]},   # pulled back: ΧΗΛΑΙ and the Moon tip stay in frame for the « Lune dans ΧΗΛΑΙ » callout
    inset={'name': 'CAM_3_4_ball', 'rect_px': [96, 396, 480, 480], 'resolution': [480, 480],
           'poses': [pose(t34, {'track': 'phase_ball'}, -50.0, 52.0, 70.0, 100.0),
                     pose(t41, {'track': 'phase_ball'}, -50.0, 52.0, 62.0, 100.0)],
           'note': 'incrustation carrée en bas à gauche (x 96-576, y 396-876, cadre crème fin au montage) : la droite '
                   'est occupée par l\'incrustation « phases »'},
    callouts=[co('Lune dans ΧΗΛΑΙ (Balance)', t_full + 0.2, t41 - 0.05, anchor='moon_tip')])
ovl('phases', '3.4', f_ph1, range(1, PH['images'] + 1), 'incrustation transparente, boîte %s (droite) ; image %d sur '
    '« Opposées » ; la légende « Superposées : nouvelle lune » / « Opposées : pleine lune » est dans l\'incrustation'
    % (PH['boite'], _ph_go), crank_sync='la manivelle suit la colonne « manivelle » de l\'incrustation, image par image')
hl('phase_ring', ['FILM_phase_halo'], 'glow', pulse(t34 + 0.2, t41, 2.0))
crank_keys += [{'f': f_ph1 + img - 1, 'v': _ph_col[img], 'ipo': 'LINEAR' if img < _ph_arr else 'CONSTANT',
                'ease': 'EASE_IN_OUT'} for img in range(_ph_go, _ph_arr + 1)]

# ======================================================================== CHAPTER 4
t42 = cut(W(4, 'regardez'))
t_hyp = W(4, 'leurs')
t_rec = W(4, 'recule')
# 4.2 : ONE QUAD ease-in span 2.10 -> MARS_42_END between the first and the last frame of the shot (the crank keeps
# turning, it only accelerates ; 4.1 ends with zero speed at 2.10, so the speed is continuous).  The span puts the
# 1st station inside « s'arrête… », the fastest retrogradation (opposition) on « recule » and the 2nd station just
# before the cut to the split 4.3, which then replays 2.10 -> 2.52 with the diagram.  A key on the last frame is
# required: on the next frame the split's first key (2.10) takes over.
MARS_42_START, MARS_42_END = 2.10, 2.42
_f42a, _f42b = F(t42), F(W(4, 'comme') - CUT_LEAD) - 1


def _t_on_quad(v):
    """Film time where the 4.2 QUAD ease-in span reaches crank v."""
    u = math.sqrt((v - MARS_42_START) / (MARS_42_END - MARS_42_START))
    return L.time_of(_f42a + u * (_f42b - _f42a))


t_stop = _t_on_quad(MARS_STATIONS[0])            # ≈ W(4, "s'arrête") + 0.33
seg('4.1', 4, '3d', t41, t42, mode='front', labels=True,
    cadrage='Face avant rapprochée, étiquettes des planètes visibles (AM_LABELS)',
    camera={'name': 'CAM_4_1', 'poses': [pose(t41, [0.0, 0.0, 45.0], -50.0, 66.0, 700.0),
                                         pose(t42, [-4.0, 8.0, 45.0], -50.0, 64.0, 620.0)]},
    callouts=[co('Planètes : lire sur le zodiaque', W(4, 'autour'), t_hyp - 0.1, pos=(0.05, 0.15), style='title'),
              co('Hypothèse · Freeth et al. 2021', t_hyp, t42 - 0.05, pos=(0.05, 0.15), style='hypothesis', honesty=True),
              co('Couleurs modernes', W(4, "c'est"), t42 - 0.05, pos=(0.05, 0.22), style='small', honesty=True)])
crank_keys += [key(t41, 1.009, 'CONSTANT'), key(t41 + 0.3, 1.009, 'SINE'), key(t42, 2.10, 'LINEAR')]
seg('4.2', 4, '3d', t42, T_43, mode='front', labels=True, mars_trail=True,
    cadrage='Cadrage serré sur la sphère rouge de Mars et son anneau ; une traînée lumineuse suit l\'aller-retour',
    camera={'name': 'CAM_4_2', 'poses': [pose(t42, at('mars_marker', 2.31), -50.0, 62.0, 185.0),
                                         pose(T_43, at('mars_marker', 2.31), -50.0, 62.0, 160.0)]},
    crank_note='2,10 -> 2,42 (QUAD, accélère) : 1re station %.4f sur « s\'arrête », opposition %.4f sur « recule », '
               '2e station %.4f juste avant la coupe' % (MARS_STATIONS[0], T_MARS_OPPOSITION, MARS_STATIONS[1]),
    callouts=[co('Station', t_stop - 0.25, T_43 - 0.05, anchor='mars_marker', style='title'),
              co('Rétrogradation', t_stop + 0.3, T_43 - 0.05, pos=(0.06, 0.80), style='title'),
              co('« stêrigmos » dans l\'inscription', t_stop + 0.3, T_43 - 0.05, pos=(0.06, 0.88), style='small')])
hl('mars', ['marker_mars'], 'glow', pulse(t42 + 0.1, T_43 + 5.0, 1.8), color=MARS_RED)
crank_keys += [{'f': _f42a, 'v': MARS_42_START, 'ipo': 'QUAD', 'ease': 'EASE_IN'},
               {'f': _f42b, 'v': MARS_42_END, 'ipo': 'CONSTANT', 'ease': 'EASE_IN_OUT'}]
# 4.3 : split screen, crank = column « manivelle » of the diagram, image by image
retro = {r['image']: r['manivelle'] for r in DIAG['retrograde']['manivelle_par_image']}
split_map = []
for i, img in enumerate(range(SPLIT_IMAGES[0], SPLIT_IMAGES[1] + 1)):
    split_map.append([F(T_43) + i, img])
seg('4.3', 4, 'split', T_43, T_51, mode='front', labels=True, mars_trail=True, counter=False,
    cadrage='Écran partagé : la machine (Mars et son anneau) composée dans la moitié gauche (décentrement '
            'shift_x = 0,25), le schéma retrograde_split à droite ; même plage de manivelle, image par image',
    diagram={'sequence': 'retrograde_split', 'dir': 'build/out/explainer/diagrams/retrograde_split',
             'pattern': '%04d.png', 'placement': 'plein cadre par-dessus la 3D (moitié gauche transparente)',
             'map': split_map},
    camera={'name': 'CAM_4_3', 'poses': [pose(T_43, at('mars_marker', 2.31), -50.0, 62.0, 300.0, 85.0, shift=(0.25, 0.0)),
                                         pose(T_51, at('mars_marker', 2.31), -50.0, 62.0, 285.0, 85.0, shift=(0.25, 0.0))]},
    texts_in_picture=['VUE DU DESSUS', 'Terre : 1 tour en 1 an', 'Mars : 1 tour en 1,88 an', 'Soleil', 'Terre', 'Mars',
                      'La Terre dépasse Mars', 'VUE DE LA TERRE', 'Station', 'Mars recule : rétrogradation'],
    callouts=[co('Vue de la Terre', T_43 + 0.3, T_51 - 0.05, pos=(0.05, 0.15), style='title')])
crank_keys += [{'f': f, 'v': retro[img], 'ipo': 'LINEAR', 'ease': 'EASE_IN_OUT'} for f, img in split_map]

# ======================================================================== CHAPTER 5
t52 = T_51 + 2.5
t53 = cut(W(5, 'dedans'))
t61 = A[6] - 0.2
# 5.3 : the insert « games_banner » drives the crank (column « manivelle » 3.0 -> 5.95, fast then slow) ; its image 95
# (the pointer enters ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ) 2 frames after the start of « Olympia »
GB = INS['games_banner']
_gb_col = column('games_banner')
_gb_arr = GB['segments']['arrivee_an_1']
_gb_r0, _gb_r1 = GB['segments']['manivelle_3_595']
f_gb_arr = F(W(5, 'olympia')) + 2
f_gb1 = f_gb_arr - (_gb_arr - 1)
t_oly = L.time_of(f_gb_arr)
seg('5.1', 5, '3d', T_51, t52, mode='front_to_back',
    cadrage='Orbite de 180° par le côté de la manivelle (axe y), de la face avant au dos ; bascule de l\'éclairage '
            '(rig arrière) à mi-course, caméra au ras de la tranche ; fin sur CAM_back_close',
    camera={'name': 'CAM_5_1', 'poses': [
        pose(T_51, [0.0, 25.0, 42.0], 0.0, 62.0, 560.0, 85.0, BACK_UP, ease='SINE_IN'),
        pose(T_51 + 1.25, [0.0, 40.0, 12.0], -8.0, 0.0, 300.0, 85.0, BACK_UP, ease='SINE_OUT'),
        pose(t52, [0.0, 60.0, -17.0], -70.0, -68.0, 760.0, 85.0, BACK_UP)]},
    transition={'type': 'bascule_eclairage', 'note': 'au passage el = 0 : option fondu 3 images au montage'},
    callouts=[])
crank_keys += [key(T_51, 2.52, 'LINEAR'), key(t52, 2.6, 'LINEAR')]
seg('5.2', 5, '3d', t52, t53, mode='back',
    cadrage='Spirale du haut (Méton), le curseur surligné dans le sillon, lent rapprochement',
    camera={'name': 'CAM_5_2', 'poses': [pose(t52, [0.0, 60.0, -17.0], -70.0, -68.0, 760.0, 85.0, BACK_UP, ease='LINEAR'),
                                         pose(t53, [8.0, 78.0, -17.0], -70.0, -70.0, 540.0, 85.0, BACK_UP)]},
    callouts=[co('235 mois = 19 ans', W(5, '235'), t53 - 0.05, anchor='metonic_spiral', style='title'),
              co('1 case = 1 mois', W(5, 'chaque'), t53 - 0.05, anchor='metonic_slider')])
# case agrandie « Phoinikaios… an 1 » (insert metonic_cell, « nom du mois (corinthien) » inside) : in 0.8 s before
# « Chaque case », played 1:1 until its hold, then its exit on the last frames of 5.2
MC = INS['metonic_cell']
_mc_x0, _mc_x1 = MC['segments']['sortie']
_mc_f0 = max(F(W(5, 'chaque')) - 20, F(t52))
_mc_n = F(t53) - _mc_f0 - (_mc_x1 - _mc_x0 + 1)
assert _mc_n >= MC['segments']['mention_illustration'][1] + 3, 'metonic_cell : mention « illustration » coupée'
ovl('metonic_cell', '5.2', _mc_f0, [min(i, MC['segments']['tenue'][1]) for i in range(1, _mc_n + 1)] +
    list(range(_mc_x0, _mc_x1 + 1)), 'incrustation transparente, boîte %s (droite)' % MC['boite'],
    anchor_hint='metonic_slider')
hl('metonic', ['metonic_slider', 'metonic_slider_pin', 'metonic_pointer'], 'glow', pulse(t52 + 0.2, t53 + 0.1, 1.6))
crank_keys += [key(t52, 2.6, 'LINEAR'), key(t53, 3.0, 'CONSTANT')]
seg('5.3', 5, '3d', t53, t61, mode='back',
    cadrage='Petit cadran des Jeux en gros plan (CAM_games_close), étiquettes historiques par paires ; le secteur '
            'ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ s\'illumine quand l\'aiguille y entre',
    camera={'name': 'CAM_5_3', 'poses': [pose(t53, [-24.40035, 62.976, -16.5], -70.0, -74.0, 340.0, 120.0, GAMES_UP),
                                         pose(t61, [-24.40035, 62.976, -16.5], -70.0, -74.0, 292.0, 120.0, GAMES_UP)]},
    callouts=[co('1 tour = 4 ans', W(5, 'tour'), t_oly - 0.1, anchor='games_pointer', style='title'),
              co('Olympia : année des Jeux', t_oly, t61 - 0.05, anchor='games_sector', style='title'),
              co("L'année, pas le jour", W(5, "l'annee"), t61 - 0.05, pos=(0.05, 0.15))])
_gb_x0, _gb_x1 = GB['segments']['sortie']
_gb_n = F(t61) - f_gb1 - (_gb_x1 - _gb_x0 + 1)
ovl('games_banner', '5.3', f_gb1, [min(i, GB['segments']['tenue'][1]) for i in range(1, _gb_n + 1)] +
    list(range(_gb_x0, _gb_x1 + 1)), 'bandeau transparent, boîte %s (bas, au-dessus des sous-titres) ; image %d = '
    'entrée dans ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ sur « Olympia »' % (GB['boite'], _gb_arr),
    crank_sync='la manivelle suit la colonne « manivelle » de l\'incrustation, image par image')
hl('games_sector', ['txt_olympiad_1', 'FILM_games_wedge'], 'glow', pulse(t_oly, t61 + 0.2, 2.2, 0.25, 0.3))
crank_keys += [{'f': f_gb1 + img - 1, 'v': _gb_col[img], 'ipo': 'LINEAR' if img < _gb_r1 else 'CONSTANT',
                'ease': 'EASE_IN_OUT'} for img in range(_gb_r0, _gb_r1 + 1)]

# ======================================================================== CHAPTER 6
t62 = cut(W(6, 'la', 1))            # « La plupart des cases sont vides »
t_une = W(6, 'une', 1)              # « Une case gravée ! »
t_entry = t_une + 0.25
t63 = cut(W(6, 'puis', 2))          # « Puis l'heure »
t64 = cut(W(6, 'devant'))
t_dragon = W(6, 'dragon')
t65 = cut(W(6, 'attention'))
ECL_IMAGES = (147, 238)
t65b = t65 + (ECL_IMAGES[1] - ECL_IMAGES[0] + 1) / FPS
t71 = A[7]
seg('6.1', 6, '3d', t61, t62, mode='back',
    cadrage='Spirale du bas (Saros) entière ; l\'aiguille court, les cases gravées calculées clignotent à son passage '
            '(la dernière : case 107, Η)',
    camera={'name': 'CAM_6_1', 'poses': [pose(t61, [0.0, -82.5, -16.5], -70.0, -72.0, 720.0, 85.0, BACK_UP),
                                         pose(t62, [4.0, -70.0, -16.5], -70.0, -72.0, 640.0, 85.0, BACK_UP)]},
    callouts=[co('Saros : 223 mois', W(6, 'en') + 0.2, t62 - 0.05, anchor='saros_spiral', style='title'),
              co('≈ 18 ans 11 jours', W(6, '223') + 0.4, t62 - 0.05, pos=(0.05, 0.15)),
              co('Cycle babylonien', W(6, 'puis', 1), t62 - 0.05, pos=(0.05, 0.22), style='small')])
crank_keys += [key(t61, 5.95, 'CONSTANT'), key(t61 + 0.35, 5.95, 'SINE'), key(t62, 8.66, 'LINEAR')]
seg('6.2', 6, '3d', t62, t63, mode='back',
    cadrage='Même spirale, plus serré sur l\'aiguille (CAM_saros_close) : les cases vides 108 à 111 défilent, puis '
            'l\'aiguille entre dans la case 112 et le signe « Σ Η » s\'allume',
    camera={'name': 'CAM_6_2', 'poses': [pose(t62, [26.0, -36.0, -16.5], -70.0, -74.0, 300.0, 120.0, BACK_UP),
                                         pose(t_entry, [12.0, -30.0, -16.5], -70.0, -74.0, 250.0, 120.0, BACK_UP),
                                         pose(t63, [8.0, -27.0, -16.5], -70.0, -74.0, 225.0, 120.0, BACK_UP)]},
    callouts=[co("Case vide : pas d'éclipse", W(6, 'la', 1) + 0.2, t_entry - 0.1, anchor='empty_cells'),
              co('Σ = éclipse de Lune', W(6, 'sigma'), t63 - 0.05, pos=(0.06, 0.78), style='title'),
              co('Η = éclipse de Soleil', W(6, 'etat'), t63 - 0.05, pos=(0.06, 0.85), style='title'),
              co('Signe calculé par notre modèle', t_entry + 0.2, t63 - 0.05, anchor='glyph_112', style='small',
                 honesty=True)])
_sar_entry = SAROS_ENTRY[112]
crank_keys += [key(t62, 8.66, 'LINEAR'), key(t_entry, _sar_entry + 0.0006, 'SINE', 'EASE_OUT'),
               key(t_entry + 0.7, 8.98, 'CONSTANT')]
hl('saros_pointer', ['saros_pointer', 'saros_slider', 'saros_slider_pin'], 'glow',
   pulse(t61 + 0.3, t63 + 0.1, 1.3))
seg('6.3', 6, '3d', t63, t64, mode='back',
    cadrage='Très gros plan sur le signe de la case 112, puis panoramique vers le petit cadran Exeligmos (secteur vide)',
    camera={'name': 'CAM_6_3', 'poses': [pose(t63, [0.2, -21.6, -16.5], -70.0, -76.0, 150.0, 120.0, BACK_UP),
                                         pose(W(6, 'ce') - 0.1, [0.2, -22.0, -16.5], -70.0, -76.0, 135.0, 120.0, BACK_UP),
                                         pose(W(6, 'zero') - 0.1, [-0.26, -106.0, -16.5], -70.0, -74.0, 210.0, 120.0, BACK_UP),
                                         pose(t64, [-0.26, -106.5, -16.5], -70.0, -74.0, 200.0, 120.0, BACK_UP)]},
    # in on « y ajoute » : the pan from the sign brings the Exeligmos dial into the picture then (anchors.json)
    callouts=[co('Exeligmos : +0, +8, +16 h', W(6, 'y'), t64 - 0.05, anchor='exeligmos_dial', style='title'),
              co('Ici : +0 h', W(6, 'zero') + 0.3, t64 - 0.05, anchor='exeligmos_pointer')])
# anatomie d'un signe marquée « exemple » (insert glyph_anatomy : « ΩΡ + chiffre = heure », « Lettre d'index → détails »)
GA = INS['glyph_anatomy']
_ga_x0, _ga_x1 = GA['segments']['sortie']
_ga_n = F(t64) - F(t63) - (_ga_x1 - _ga_x0 + 1)
assert _ga_n >= GA['segments']['notes'][1], 'glyph_anatomy : textes coupés'
ovl('glyph_anatomy', '6.3', F(t63), [min(i, GA['segments']['tenue'][1]) for i in range(1, _ga_n + 1)] +
    list(range(_ga_x0, _ga_x1 + 1)), 'incrustation transparente, boîte %s (droite), marquée « exemple »' % GA['boite'])
hl('glyph_112', ['txt_saros_glyph_112'], 'glow', [(t_entry - 0.02, 0.0), (t_entry + 0.2, 3.0), (t64 - 0.3, 3.0),
                                                 (t64, 0.0)])
hl('exeligmos', ['exeligmos_pointer'], 'glow', pulse(W(6, 'zero'), t64 + 0.1, 1.6))
seg('6.4', 6, '3d', t64, t65, mode='front',
    cadrage='Face avant rapprochée : la Lune vient se poser sur un bout de l\'aiguille du Dragon, le Soleil est à '
            'l\'autre bout, l\'aiguille s\'illumine ; la boule passe du noir au blanc',
    camera={'name': 'CAM_6_4', 'poses': [pose(t64, [0.0, 0.0, 48.0], -50.0, 68.0, 470.0),
                                         pose(t65, [0.0, 0.0, 48.0], -52.0, 68.0, 425.0)]},
    callouts=[co('Aiguille du Dragon : hypothèse', W(6, "l'aiguille"), t65 - 0.05, anchor='dragon_head',
                 style='hypothesis', honesty=True),
              co('Dragon = nœuds de la Lune', W(6, 'hypothetique'), t65 - 0.05, pos=(0.06, 0.82)),
              co('Pleine lune sur le Dragon : éclipse possible', W(6, 'une', 2), t65 - 0.05, pos=(0.06, 0.89),
                 style='title')])
hl('dragon', ['dragon_hand'], 'glow', pulse(W(6, "l'aiguille"), t71 - 0.2, 2.2))
crank_keys += [key(t64 + 0.1, 8.98, 'SINE'), key(t_dragon + 0.1, 9.014, 'CONSTANT')]
seg('6.5a', 6, 'diagram', t65, t65b,
    cadrage='Schéma plein écran : éclipse de Lune (la Lune traverse l\'ombre de la Terre), aiguille du Dragon',
    diagram={'sequence': 'eclipse', 'dir': 'build/out/explainer/diagrams/eclipse', 'pattern': '%04d.png',
             'placement': 'plein cadre', 'map': [[F(t65) + i, img] for i, img in
                                                  enumerate(range(ECL_IMAGES[0], ECL_IMAGES[1] + 1))]},
    callouts=[co('Signes calculés par notre modèle', t65 + 0.2, t71 - 0.1, pos=(0.05, 0.90), style='small',
                 honesty=True)])
seg('6.5b', 6, '3d', t65b, t71, mode='front',
    cadrage='Retour sur la machine, trois-quarts avant, aiguille du Dragon encore allumée',
    camera={'name': 'CAM_6_5', 'poses': [pose(t65b, [0.0, -10.0, 32.0], -46.0, 36.0, 520.0, 50.0),
                                         pose(t71, [0.0, -10.0, 32.0], -49.0, 37.0, 480.0, 50.0)]},
    callouts=[co('Possible · pas le lieu', W(6, 'et', 1), t71 - 0.05, pos=(0.06, 0.82), style='title')])

# ======================================================================== CHAPTER 7
t72 = cut(W(7, 'mais'))
t_ksi = W(7, 'quand', 1)
t73 = cut(W(7, 'bien'))
LEVER = (61, 150)
t73b = t73 + 60 / FPS
t74 = cut(W(7, 'deja'))
t_la_mach = W(7, 'la', 5)           # « La machine ne disait pas où aller »
t75 = cut(W(7, 'voici')) - 0.25
t76 = cut(W(7, 'et'))
seg('7.1', 7, '3d', t71, t72, mode='wide',
    cadrage='Plan large de l\'atelier (mode wide), trois-quarts avant, fenêtre ouverte sur le ciel et les collines',
    camera={'name': 'CAM_7_1', 'poses': [pose(t71, [-120.0, 60.0, 150.0], -52.0, 13.0, 1850.0, 32.0),
                                         pose(t72, [-110.0, 55.0, 140.0], -50.0, 13.0, 1650.0, 32.0)]},
    callouts=[co('Pas un instrument de navigation', W(7, 'non'), t72 - 0.05, pos=(0.05, 0.15), style='title',
                 honesty=True),
              co('Ni viseur, ni latitude, ni longitude', W(7, 'viseur'), t72 - 0.05, pos=(0.05, 0.22)),
              co('Calculateur du ciel', W(7, 'calculateur'), t72 - 0.05, anchor='machine_center', style='title')])
crank_keys += [key(t65b, 9.014, 'CONSTANT')]
seg('7.2', 7, '3d', t72, t73, mode='front',
    cadrage='Face avant entière, grand axe à l\'horizontale : les deux plaques du parapegme surlignées ; le Soleil '
            'avance jusqu\'à 17° du Taureau ; Ξ et la ligne « La Pléiade se lève le matin » en surimpression (montage)',
    camera={'name': 'CAM_7_2', 'poses': [pose(t72, [0.0, -10.0, 42.0], -50.0, 74.0, 860.0, 85.0, (-1.0, 0.0, 0.0)),
                                         pose(t73, [0.0, -6.0, 42.0], -50.0, 74.0, 790.0, 85.0, (-1.0, 0.0, 0.0))]},
    callouts=[co('Parapegme : calendrier des étoiles', W(7, 'calendrier'), t73 - 0.05, anchor='parapegma_bottom',
                 style='title'),
              co('Ξ : la Pléiade se lève', W(7, 'xi'), t73 - 0.05, anchor='sign_under_sun'),
              co('Ξ et ligne du parapegme : illustration', W(7, 'xi') + 0.2, t73 - 0.05, pos=(0.05, 0.15),
                 style='small', honesty=True, kind='illustration')])
# Ξ (insert parapegma_xi, centred on (960, 540) : translate onto the anchor) fully in on « ksi » ; the line (insert
# parapegma_ligne) writes itself on « on lit : La Pléiade se lève le matin » and stays complete (image 74, before the
# insert's own « illustration » mention, which 7.2 is too short to show : the callout above carries it)
PP = INS['parapegma_line']
_pp_xi1 = PP['segments']['repere_xi'][1]
_pp_w0, _pp_w1 = PP['segments']['ecriture']
_f72e = F(t73) - 1
_f_xi = F(W(7, 'xi')) - 4
ovl('parapegma_xi', '7.2', _f_xi, [min(i, _pp_xi1) for i in range(1, _f72e - _f_xi + 2)], 'repère Ξ seul (centré sur '
    '(960, 540) dans l\'image) : translater sur l\'ancre sign_under_sun (échelle du zodiaque, sous le Soleil)',
    source='parapegma_line', anchor='sign_under_sun', anchor_px_in_image=[960, 540])
_f_on = F(W(7, 'on'))
ovl('parapegma_ligne', '7.2', _f_on, [min(_pp_w0 + i, _pp_w1 + 1) for i in range(_f72e - _f_on + 1)],
    'ligne seule (ligne de base y = %d dans l\'image) : translater sur la plaque du haut (ancre parapegma_top)'
    % PP['ligne_de_base_y'], source='parapegma_line', anchor='parapegma_top')
hl('parapegma', ['parapegma_1', 'parapegma_2', 'parapegma_lines_1', 'parapegma_lines_2'], 'glow',
   pulse(W(7, 'plaques') - 0.2, t73 + 0.1, 1.0))
crank_keys += [key(t_ksi - 0.1, 9.014, 'SINE'), key(W(7, 'xi') + 0.3, 9.13, 'CONSTANT')]
seg('7.3a', 7, 'diagram', t73, t73b,
    cadrage='Schéma plein écran : aube de mai, les Pléiades se lèvent à l\'est ; barre de saison (Végèce)',
    diagram={'sequence': 'pleiades_lever', 'dir': 'build/out/explainer/diagrams/pleiades_lever', 'pattern': '%04d.png',
             'placement': 'plein cadre',
             'map': [[F(t73) + i, int(round(LEVER[0] + (LEVER[1] - LEVER[0]) * i / 59))] for i in range(60)]},
    texts_in_picture=["Aube de mai : les Pléiades se lèvent à l'est, avant le Soleil", 'Pléiades', 'EST',
                      'Saison de navigation selon Végèce (IVe-Ve s. apr. J.-C.)', 'ΠΑΧΩΝ : mois cité par Végèce',
                      'Mer sûre : 27 mai–14 sept.', 'lever des Pléiades', 'Végèce, Epitoma rei militaris IV, 39'],
    callouts=[])
seg('7.3b', 7, '3d', t73b, t74, mode='front',
    cadrage='Bref retour sur l\'anneau égyptien : ΠΑΧΩΝ s\'illumine',
    camera={'name': 'CAM_7_3', 'poses': [pose(t73b, [-22.0, 70.4, 42.5], -50.0, 64.0, 250.0),
                                         pose(t74, [-22.0, 70.4, 42.5], -52.0, 64.0, 222.0)]},
    callouts=[co('ΠΑΧΩΝ : mois cité par Végèce', t73b + 0.1, t74 - 0.05, anchor='pachon', style='title')])
hl('pachon', ['txt_month_08'], 'glow', pulse(t73b + 0.05, t74 + 0.1, 3.0, 0.25, 0.2))
COUCHER = (15, 200)
_n_in = F(t_la_mach) - F(t74)
seg('7.4', 7, 'split', t74, t75, mode='front', inset_until=F(t_la_mach),
    cadrage='Face avant, cadran composé à gauche (shift_x 0,25) sous le schéma en incrustation à droite ; le Soleil va '
            'jusqu\'au ΣΚΟΡΠΙΟΣ ; sur « La machine ne disait pas… » le schéma sort et le cadran revient au centre',
    diagram={'sequence': 'pleiades_coucher', 'dir': 'build/out/explainer/diagrams/pleiades_coucher',
             'pattern': '%04d.png', 'placement': 'incrustation rect_px [936, 252, 936, 527] (échelle 0,4875), '
                                                   'jusqu\'à la fin de la carte (inset_until)',
             'rect_px': [936, 252, 936, 527],
             'map': [[F(t74) + i, int(round(COUCHER[0] + (COUCHER[1] - COUCHER[0]) * i / (_n_in - 1)))]
                     for i in range(_n_in)]},
    # split : the whole dial inside the left 936 px (x 44-927 px at 820-800 mm ; the diagram inset starts at x 936)
    camera={'name': 'CAM_7_4', 'poses': [pose(t74, [0.0, 0.0, 44.0], -50.0, 68.0, 820.0, 85.0, shift=(0.25, 0.0)),
                                         pose(t_la_mach, [0.0, 0.0, 44.0], -50.0, 68.0, 800.0, 85.0, shift=(0.25, 0.0)),
                                         pose(t_la_mach + 1.1, [0.0, 0.0, 44.0], -50.0, 68.0, 600.0, 85.0),
                                         pose(t75, [0.0, 0.0, 44.0], -50.0, 68.0, 580.0, 85.0)]},
    callouts=[co('Hésiode, Les Travaux et les Jours', t74 + 0.1, t_la_mach - 0.05, pos=(0.05, 0.15), style='small'),
              co('Fin oct.–début nov. : quitter la mer', W(7, 'quand', 2), t_la_mach - 0.05, pos=(0.05, 0.22)),
              co('Végèce : mer fermée du 11 nov. au 10 mars', W(7, 'rentrent'), t_la_mach - 0.05, pos=(0.05, 0.29),
                 style='small'),
              co('Pas où aller : quand partir', t_la_mach, t75 - 0.05, anchor='sun_sphere', style='title')])
# the Sun reaches ΣΚΟΡΠΙΟΣ (Pleiades' morning setting, late Oct.-early Nov.) on « tombent dans la noire mer », where
# the callouts say « Fin oct.–début nov. » and « mer fermée du 11 nov. », then holds 9.60 up to 7.5
t_scorpion = W(7, 'mer', 2, end=True) + 0.1
crank_keys += cruise(t74 + 0.2, t_scorpion, 9.13, 9.60, 0.6, 0.9)
seg('7.5', 7, '3d', t75, t76, mode='wide',
    cadrage='Plan large de l\'atelier au soleil, lente orbite ; la machine « respire » (explode 0 → 0,3 → 0), la '
            'manivelle tourne doucement',
    camera={'name': 'CAM_7_5', 'poses': [pose(t75, [0.0, -10.0, 40.0], -64.0, 22.0, 1180.0, 40.0, ease='LINEAR'),
                                         pose(T_END, [0.0, -10.0, 40.0], -26.0, 27.0, 1040.0, 40.0)]},
    callouts=[co('69 roues · 30 conservées', W(7, 'voici'), t76 - 0.05, pos=(0.06, 0.78), style='title'),
              co('Rapports prouvés (Lean 4)', W(7, 'prouves'), t76 - 0.05, pos=(0.06, 0.85)),
              co('Code et modèle libres · GitHub', W(7, 'mathematiquement'), t76 - 0.05, pos=(0.06, 0.92)),
              co('taciclei', W(7, 'acces'), t76 - 0.05, pos=(0.94, 0.94), style='credit')])
_e0 = W(7, 'voici')
explode_keys += [key(_e0, 0.0, 'SINE'), key(_e0 + 1.9, 0.3, 'SINE'), key(_e0 + 3.9, 0.0, 'CONSTANT')]
crank_keys += [key(t75, 9.60, 'LINEAR'), key(T_END, 9.72, 'LINEAR')]
seg('7.6', 7, 'card', t76, T_END, render_3d=True, bg_camera='CAM_7_5', mode='wide', counter=False,
    cadrage='Carton final sur fond crème, la machine en fondu derrière (suite de l\'orbite 7.5, rendue en 3D)',
    card={'items': ['1. Tournez la manivelle', '2. Soleil : date, saison', '3. Lune : place, phase',
                    '4. Planètes : place (hypothèse)', '5. Dos : mois, Jeux', '6. Signe : éclipse, heure'],
          'question': 'Et vous, quelle date ?', 'items_in': F(t76 + 0.1), 'question_in': F(W(7, 'quelle')),
          'background': '#F3EAD8', 'machine_fade': [F(t76), F(t76 + 1.2), 0.25],
          'credit': 'taciclei'},
    callouts=[])

# end card : insert end_card_texte over end_card_fond.png and the machine at 25 % ; the 6 steps with the cut (« Et
# vous »), the question (image 45) on « quelle », then the credits
EC = INS['end_card']
_ec_steps = EC['segments']['etapes'][1]
_ec_q = EC['segments']['question'][0]
_f76, _f_q = F(t76), F(W(7, 'quelle'))
ovl('end_card_texte', '7.6', _f76, [min(i + 1, _ec_steps) for i in range(_f_q - _f76)] +
    [min(_ec_q + i, EC['images']) for i in range(N_FRAMES - _f_q + 1)],
    'textes transparents du carton sur end_card_fond.png (parchemin + vignettage), la machine (CAM_7_5) en fondu à '
    '25 %% entre les deux ; image %d (la question) sur « quelle »' % _ec_q, source='end_card',
    background='build/out/explainer/inserts/end_card_fond.png', texts=EC['textes'])

# chapter titles (inserts chapter_title_N, bottom left above the subtitles) 0.2 s into the first shot of each chapter
for _n in range(1, 8):
    _s0 = min((s for s in SEG if s['chapter'] == _n), key=lambda s: s['t0'])
    _f = F(_s0['t0']) + 5
    ovl('chapter_title_%d' % _n, _s0['id'], _f, range(1, INS['chapter_titles']['images'] + 1),
        'titre de chapitre en bas à gauche, boîte %s' % INS['chapter_titles']['boite'], source='chapter_titles',
        text=INS['chapter_titles']['textes'][_n - 1])

# ----------------------------------------------------------------------------- consolidation
SEG.sort(key=lambda s: s['t0'])
for a, b in zip(SEG, SEG[1:]):
    assert abs(a['t1'] - b['t0']) < 1e-9, (a['id'], b['id'])
for s in SEG:
    s['frames'] = [F(s['t0']), F(s['t1']) - 1]
    s['seconds'] = [round(s['t0'], 3), round(s['t1'], 3)]
    s['render_3d'] = s.get('render_3d', s['kind'] in ('3d', 'split'))
SEG[-1]['frames'][1] = N_FRAMES

# callouts : clamp to the shot, then the charter of overlay.py (zone of the stack, nature, text / secondary line)
RIGHT_INSERTS = ('phases', 'metonic_cell', 'glyph_anatomy')


def _kind(c):
    if c.get('kind'):
        return c['kind']
    if c.get('style') == 'hypothesis':
        return 'hyp'
    if c.get('honesty'):
        low = c['text'].lower()
        if 'modèle' in low:
            return 'modele'
        if 'hypothèse' in low:
            return 'hyp'
        if 'couleurs modernes' in low or 'illustration' in low:
            return 'illustration'
    return 'normal'


def _zone(c, s):
    if c.get('zone'):
        return c['zone']
    if c.get('style') == 'credit':
        return 'bas_droite'
    p = c.get('pos')
    if p:
        return ('haut_' if p[1] < 0.5 else 'bas_') + ('gauche' if p[0] < 0.5 else 'droite')
    right_taken = (s['kind'] == 'split' and c['in'] < s.get('inset_until', 10 ** 9)) or any(
        o['sequence'] in RIGHT_INSERTS and o['frames'][0] <= c['out'] and c['in'] <= o['frames'][1] for o in OVL)
    return 'haut_gauche' if right_taken else 'haut_droite'


for s in SEG:
    for i, c in enumerate(s.get('callouts', [])):
        want = (c['in'], c['out'])
        c['in'] = max(c['in'], s['frames'][0])
        c['out'] = min(c['out'], s['frames'][1])
        if want != (c['in'], c['out']):
            c['clamped_from'] = list(want)
        c['kind'] = _kind(c)
        c['zone'] = _zone(c, s)
        secondary = c.get('style') in ('small', 'hypothesis', 'credit') or (c.get('honesty') and c.get('style') != 'title')
        c['item'] = {('sub' if secondary else 'text'): c['text'], 'kind': c['kind']}
        c['_i'] = i
    for z in {c['zone'] for c in s.get('callouts', [])}:
        cs = sorted((c for c in s['callouts'] if c['zone'] == z), key=lambda c: ((c.get('pos') or [0, 0])[1], c['in'],
                                                                                  c['_i']))
        for k, c in enumerate(cs):
            c['stack'] = k
    for c in s.get('callouts', []):
        del c['_i']


def _measure():
    """Box sizes (px) of every callout, of the counter and of the chapter titles, measured by overlay.py itself
    (Pillow + the charter fonts, venv python) : used by verify_beats.py for the layout checks."""
    items = [c['item'] for s in SEG for c in s.get('callouts', [])]
    titles = [o['text'] for o in OVL if o['sequence'].startswith('chapter_title_')]
    code = ('import sys, json; sys.path.insert(0, %r); import overlay as O; d = json.loads(sys.stdin.read()); '
            'n = lambda t: t.split(" · ", 1); '
            'sys.stdout.write(json.dumps({"callouts": [O.callout_size(i) for i in d["items"]], '
            '"counter": O.counter_box()[0], "titles": [34 + O.text_width(n(t)[0], "display", 56) + '
            'O.text_width("  ·  ", "display", 56) + O.text_width(n(t)[1], "display", 56) + 40 for t in d["titles"]], '
            '"zones": O.ZONES, "gap": O.STACK_GAP}))' % str(L.ROOT / 'tools' / 'explainer'))
    out = subprocess.run([str(VENV_PY), '-c', code], input=json.dumps({'items': items, 'titles': titles}),
                         capture_output=True, text=True, cwd=str(L.ROOT))
    if out.returncode:
        raise SystemExit('overlay.py (mesure des boîtes) a échoué :\n' + out.stderr[-1500:])
    m = json.loads(out.stdout)
    it = iter(m['callouts'])
    for s in SEG:
        for c in s.get('callouts', []):
            c['size_px'] = [int(v) for v in next(it)]
    it = iter(m['titles'])
    for o in OVL:
        if o['sequence'].startswith('chapter_title_'):
            ib = INS['chapter_titles']['boite']
            o['box_px'] = [ib[0], ib[1], int(round(ib[0] + next(it))), ib[3]]
    return {'counter_box_px': [int(round(v)) for v in m['counter']], 'zones': m['zones'], 'stack_gap_px': m['gap']}


LAYOUT = _measure()


def dedupe(keys):
    """One key per frame (the later one wins), sorted."""
    d = {}
    for k in keys:
        d[k['f']] = k
    return [d[f] for f in sorted(d)]


crank_keys = dedupe(crank_keys)
explode_keys = dedupe(explode_keys)
patina_keys = dedupe(patina_keys)
for kl in (crank_keys, explode_keys, patina_keys):
    for k in kl:
        k['v'] = L.f32(k['v'])


def seg_at(f):
    for s in SEG:
        if s['frames'][0] <= f <= s['frames'][1]:
            return s
    return SEG[-1]


frames = []
for f in range(1, N_FRAMES + 1):
    s = seg_at(f)
    c = L.f32(L.eval_keys(crank_keys, f))
    counter = s['chapter'] >= 2 and s['kind'] in ('3d', 'split') and s.get('counter', True)
    if s['id'] == '2.1':
        counter = f >= F(s['counter_from'])
    frames.append({'f': f, 'seg': s['id'], 'crank': c, 'explode': round(L.eval_keys(explode_keys, f), 6),
                   'patina': round(L.eval_keys(patina_keys, f), 6),
                   'counter': L.counter_text(c) if counter else None})

# ---------------------------------------------------------------- blinking glyph cells (6.1) from the crank per frame
s61 = next(s for s in SEG if s['id'] == '6.1')
s62 = next(s for s in SEG if s['id'] == '6.2')
blinks = []
for cell, glyph in sorted(GLYPHS.items()):
    te = SAROS_ENTRY.get(cell)
    if te is None:
        continue
    fr = [x for x in frames if s61['frames'][0] <= x['f'] <= s62['frames'][1] and x['crank'] >= te]
    if not fr or cell >= 112:
        continue
    f_in = fr[0]['f']
    if f_in == s61['frames'][0] and frames[f_in - 2]['crank'] >= te:
        continue                    # already passed before the shot
    blinks.append({'cell': cell, 'glyph': glyph, 'frame_entry': f_in, 'crank_entry': round(te, 5)})
    HL.append({'id': 'blink_%03d' % cell, 'targets': ['txt_saros_glyph_%03d' % cell], 'kind': 'glow',
               'color': list(GOLD), 'keys': [{'f': f_in - 1, 'v': 0.0}, {'f': f_in + 1, 'v': 3.2},
                                             {'f': f_in + 12, 'v': 0.0}]})
f_112 = next(x['f'] for x in frames if x['f'] >= s62['frames'][0] and x['crank'] >= SAROS_ENTRY[112])
f_oly = next(x['f'] for x in frames if x['seg'] == '5.3' and x['crank'] >= T_OLYMPIA)

# ---------------------------------------------------------------- beats (checked against engine.py by verify_beats.py)
# A beat = one frame where the picture must show a given reading of the machine.  'check' names the test of
# verify_beats.py, 'params' its arguments ; 'window' = frames where the beat may fall to stay in sync with the voice
# (word_frames = [first, last] frame of the words) ; 'hold' = frames over which the crank must stay at the beat value.
def _seg(sid):
    return next(s for s in SEG if s['id'] == sid)


def _first(sid, cond):
    return next(x['f'] for x in frames if x['seg'] == sid and cond(x['crank']))


def WF(ch, k1, n1=1, k2=None, n2=1):
    """[first, last] frame of the words k1 .. k2 of chapter ch."""
    return [F(W(ch, k1, n1)), F(W(ch, k2 or k1, n2, end=True))]


def beat(bid, sid, frame, check, expect, word=None, word_frames=None, window='words', hold=None, **params):
    return {'id': bid, 'segment': sid, 'frame': frame, 'crank': frames[frame - 1]['crank'], 'check': check,
            'params': params, 'expect': expect, 'word': word, 'word_frames': word_frames,
            'window': word_frames if window == 'words' else window, 'hold': hold}


f_sup = F(t_sup)
f_full = F(t_full)
f_dr = F(t_dragon + 0.1)
f_s1 = _first('4.2', lambda c: c >= MARS_STATIONS[0])
f_opp = _first('4.2', lambda c: c >= T_MARS_OPPOSITION)
f_s2 = _first('4.2', lambda c: c >= MARS_STATIONS[1])
f_scorpion = F(t_scorpion)
beats = [
    beat('flash_eclipse', '1.2a', F(t12) + 5, 'dragon', "9,014 : pleine lune sur l'aiguille du Dragon (Soleil à "
         "l'autre bout), sans signe d'éclipse", 'éclipses', WF(1, 'eclipse'), window=[F(t12), F(t12b) - 1],
         hold=[F(t12), F(t12b) - 1], node_max_deg=1.0),
    beat('flash_phase', '1.2b', F(t12b) + 5, 'fraction', '0,99 : boule des phases à moitié claire', 'phases',
         WF(1, 'face'), window=[F(t12b), F(t12c) - 1], hold=[F(t12b), F(t12c) - 1], lo=0.4, hi=0.6),
    beat('flash_jeux', '1.2d', F(t12d) + 5, 'games', '5,95 : aiguille des Jeux dans ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ', 'Jeux',
         WF(1, 'jeux'), window=[F(t12d), F(t13) - 1], hold=[F(t12d), F(t13) - 1], label='ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ'),
    beat('nouvelle_lune', '3.4', f_sup, 'phase', '0,972 : nouvelle lune, aiguilles Lune et Soleil superposées, boule '
         'noire (tenue de 3.1 à « Opposées »)', 'Aiguilles superposées (cue 15, absente de l\'STT)',
         [F(CUE(15)), F(CUE(15, end=True))], window=[F(CUE(15)), F(CUE(15, end=True))],
         hold=[F(t31), f_ph_go], target_deg=0.0, tol_deg=7.5, frac_max=0.01, sun_moon_max_deg=3.0),
    beat('pleine_lune_3_4', '3.4', f_full, 'phase', '1,009 : pleine lune, Lune dans ΧΗΛΑΙ, Soleil (aiguille de date et '
         'sphère dorée) dans ΚΡΙΟΣ', 'Opposées : blanche… pleine lune', WF(3, 'opposee', 1, 'lune', 2),
         window=[F(W(3, 'blanche')), F(W(3, 'lune', 2, end=True))], hold=[f_full, _seg('3.4')['frames'][1]],
         target_deg=180.0, tol_deg=7.5, frac_min=0.99, moon_sign='ΧΗΛΑΙ', sun_sign='ΚΡΙΟΣ'),
    beat('mars_station_1', '4.2', f_s1, 'mars_station', "Mars s'arrête (1re station %.4f) : sa vitesse change de signe"
         % MARS_STATIONS[0], "s'arrête", WF(4, "s'arrete"), n=1),
    beat('mars_retro_max', '4.2', f_opp, 'mars_retro', 'Mars recule au plus vite (opposition %.4f)' % T_MARS_OPPOSITION,
         'puis recule', WF(4, 'puis', 1, 'recule')),
    beat('mars_retro', '4.2', F(t_rec), 'mars_retro', 'Mars rétrograde sur « recule »', 'recule', WF(4, 'recule')),
    beat('mars_station_2', '4.2', f_s2, 'mars_station', 'Mars repart (2e station %.4f) juste avant la coupe vers 4.3'
         % MARS_STATIONS[1], 'recule', WF(4, 'recule'), window=[F(W(4, 'recule')), _seg('4.2')['frames'][1]], n=2),
    beat('mars_reprise_4_3', '4.3', _seg('4.3')['frames'][0], 'mars_replay', 'reprise 2,10 -> 2,52 avec le schéma : '
         'les deux stations repassent, image par image avec retrograde_split', 'comme dans le ciel',
         WF(4, 'comme', 1, 'mars', 2), window=None),
    beat('olympia', '5.3', f_oly, 'games_entry', "l'aiguille des Jeux entre dans ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ (%.4f)" % T_OLYMPIA,
         'Olympia', WF(5, 'olympia'), window=[F(W(5, 'olympia')) - 2, F(W(5, 'olympia', end=True))],
         label='ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ', stay=True),
    beat('saros_112', '6.2', f_112, 'saros_entry', "l'aiguille du Saros entre dans la case 112 (signe calculé Σ Η) "
         "après les cases vides 108-111", 'Une case gravée', WF(6, 'une', 1, 'gravee'), cell=112, glyph='Σ Η',
         empty=[108, 109, 110, 111]),
    beat('exeligmos_0h', '6.3', _seg('6.3')['frames'][0], 'exeligmos', "aiguille de l'Exeligmos dans le secteur vide "
         "(+0 h) pendant tout le plan", 'zéro', WF(6, 'zero'), window=None, hold=list(_seg('6.3')['frames']),
         hours=0),
    beat('boule_noire_6_4', '6.4', _seg('6.4')['frames'][0], 'fraction', 'début de 6.4 : boule presque noire (8,98)',
         'Devant', WF(6, 'devant'), window=None, lo=0.0, hi=0.05),
    beat('dragon_full_moon', '6.4', f_dr, 'dragon', "9,014 : pleine lune sur l'aiguille du Dragon (≤ 1°), boule "
         "blanche ; tenue jusqu'à la fin de 7.1", 'la pleine lune tombe sur l\'aiguille du Dragon',
         WF(6, 'tombe', 1, 'dragon'), hold=[f_dr, _seg('7.1')['frames'][1]], node_max_deg=1.0),
    beat('soleil_taureau', '7.2', F(W(7, 'xi') + 0.3), 'sun_sign', 'Soleil vers 47° : 17° dans ΤΑΥΡΟΣ (lever du matin '
         'des Pléiades)', 'ksi', WF(7, 'xi'), window=[F(W(7, 'xi')), F(W(7, 'matin', end=True))],
         hold=[F(W(7, 'xi') + 0.3), F(t74 + 0.2)], sign='ΤΑΥΡΟΣ', deg_lo=16.0, deg_hi=18.0),
    beat('soleil_scorpion', '7.4', f_scorpion, 'sun_sign', 'Soleil vers 216° : ΣΚΟΡΠΙΟΣ (coucher du matin des '
         'Pléiades, fin oct.-début nov.)', 'tombent dans la noire mer', WF(7, 'tombent', 1, 'mer', 2),
         window=[F(W(7, 'tombent')), F(W(7, 'navires', end=True))], hold=[f_scorpion, _seg('7.4')['frames'][1]],
         sign='ΣΚΟΡΠΙΟΣ', entry=True),
]

# ----------------------------------------------------------------------------- subtitles + audio
subs = []
for c in CUES:
    ch = CUE_CHAPTER[c['i']]
    a = A[ch] + c['start'] - CH[ch]['start']
    b = A[ch] + c['end'] - CH[ch]['start']
    under = sorted({x['seg'] for x in frames[F(a) - 1:F(b) - 1]})
    kinds = sorted({s['kind'] for s in SEG if s['id'] in under} - {'3d', 'split'})
    subs.append({'i': c['i'], 'chapter': ch, 'start': round(a, 3), 'end': round(b, 3), 'in': F(a), 'out': F(b) - 1,
                 'text': c['text'], 'segments': under, 'over': kinds,
                 # the end card carries the question itself and its credits at the bottom (inserts timing.json)
                 'burn_in': 'card' not in kinds})
srt = []
for s in subs:
    srt += [str(s['i']), '%s --> %s' % (L.fmt_srt(s['start']), L.fmt_srt(s['end'])), s['text'], '']
(L.FILM / 'subtitles_film.srt').write_text('\n'.join(srt), encoding='utf-8')

audio = {'fps': FPS, 'total_seconds': round(N_FRAMES / FPS, 3), 'total_frames': N_FRAMES,
         'sample_rate_source': VT['sample_rate'], 'loudness_lufs_integrated_source': VT['loudness_lufs_integrated'],
         'note': 'Chaque fichier est posé entier à start_s (film) ; aucune coupe, aucun fondu dans la voix. Musique / '
                 'ambiance éventuelles : sous -18 dB par rapport à la voix. Fin : carton muet de %.1f s.' % END_CARD,
         'clips': [{'chapter': n, 'file': 'build/out/explainer/voice/' + CH[n]['file'], 'start_s': round(A[n], 3),
                    'start_frame': F(A[n]), 'start_sample_24k': int(round(A[n] * VT['sample_rate'])),
                    'start_sample_48k': int(round(A[n] * 48000)), 'duration_s': CH[n]['duration'],
                    'end_s': round(A[n] + CH[n]['duration'], 3)} for n in range(1, 8)],
         'ffmpeg_hint': ('ffmpeg ' + ' '.join('-i build/out/explainer/voice/ch%d.wav' % n for n in range(1, 8)) +
                         ' -filter_complex "' + ';'.join('[%d]adelay=%d:all=1[a%d]' % (n - 1, int(round(A[n] * 1000)), n)
                                                         for n in range(1, 8)) +
                         ';' + ''.join('[a%d]' % n for n in range(1, 8)) +
                         'amix=inputs=7:normalize=0,apad=whole_dur=%.3f[out]" -map "[out]" -ar 48000 voice_film.wav'
                         % (N_FRAMES / FPS))}
(L.FILM / 'audio_placement.json').write_text(json.dumps(audio, ensure_ascii=False, indent=1))

# ----------------------------------------------------------------------------- write
chapters = []
for n in range(1, 8):
    ss = [s for s in SEG if s['chapter'] == n]
    chapters.append({'n': n, 'audio_start_s': round(A[n], 3), 'audio_start_frame': F(A[n]),
                     'audio_end_s': round(A[n] + CH[n]['duration'], 3), 'frames': [ss[0]['frames'][0], ss[-1]['frames'][1]],
                     'seconds': [ss[0]['seconds'][0], ss[-1]['seconds'][1]], 'shots': [s['id'] for s in ss]})
out = {
    'title': "Le ciel dans une boîte : comment lire la machine d'Anticythère",
    'fps': FPS, 'resolution': [L.WIDTH, L.HEIGHT], 'frame_start': 1, 'frame_end': N_FRAMES,
    'total_seconds': round(N_FRAMES / FPS, 3),
    'conventions': {
        'frame': 'frame f (1-based) starts at t = (f - 1) / 25 s ; frame ranges are inclusive',
        'keys': 'AM_Controller keys {f, v, ipo, ease} : interpolation of a key applies to the span after it '
                '(Blender) ; values float32 ; frames[].crank = exact value Blender evaluates',
        'camera_pose': 'camera = target + dist * (cos el cos az, cos el sin az, sin el), world degrees, looking at '
                       'target, roll from the up vector ; target = [x, y, z] | {anchor, crank} (anchor position at that '
                       'crank) | {track: anchor} (followed frame by frame) ; shift = Blender lens shift ; the move from a '
                       'pose to the next uses the pose\'s ease ; baked per frame by build_film.py',
        'modes': "case : boîtier fermé (murs + couvercles) ; front : machine seule, rig avant ; back : rig arrière "
                 "(établi miroir au-dessus, lumières et monde miroir) ; front_to_back : bascule à el = 0 ; wide : "
                 "atelier entier, rig avant",
        'kinds': "segments[].kind : 3d (rendu Blender plein cadre) | split (3D décentrée + schéma à droite) | diagram "
                 "(schéma plein cadre, pas de 3D) | map (incrustation opaque plein cadre, pas de 3D) | card (carton "
                 "final sur la 3D en fondu)",
        'callouts': 'in/out = film frames (inclusive, recadrées sur le plan ; clamped_from = demande initiale) ; '
                    'item = {text | sub, kind} à passer tel quel à overlay.render_callouts(items, zone) ; zone = pile '
                    'de la charte (haut_droite, haut_gauche, bas_gauche, bas_droite ; stack = rang dans la pile, du '
                    'haut vers le bas) ; kind = normal | hyp | modele | illustration | exemple ; size_px = boîte '
                    'mesurée par overlay.callout_size ; anchor = objet visé (anchors, pour un filet éventuel) ; '
                    'pos = position voulue à l\'origine (normalisée), ne sert plus qu\'au choix de la zone ; style : '
                    'title | label | small | hypothesis | credit ; honesty = mention obligatoire',
        'overlays': 'calques 2D de tools/explainer/inserts.py : map = [film_frame, image] pour chaque image de '
                    'frames ; box_px = boîte occupée [x0, y0, x1, y1] ; anchor = ancre sur laquelle translater le '
                    'calque (parapegma_*) ; crank_sync = la manivelle suit la colonne « manivelle » du calque',
        'layout': 'boîte du compteur, zones et écart des piles de callouts (overlay.py), en px',
        'beats': 'image où la machine doit montrer une lecture (check + params, testés par verify_beats.py avec '
                 'engine.py) ; window = images permises pour rester synchrone avec la voix (word_frames = premiers '
                 'et derniers mots) ; hold = images où la manivelle reste à la valeur du beat',
        'subtitles': 'start/end en s film (= narration.srt décalé par chapitre), in/out en images incluses ; '
                     'burn_in = false sous le carton final (il porte la question et les crédits) ; over = plans '
                     'plein écran sans 3D sous la réplique',
        'highlights': 'glow : emission added to a duplicated material, keys = strength ; sweep : a moving highlight '
                      'around the ring (sweep = angle keys, degrees) ; ghost : alpha of a translucent copy ; '
                      'targets FILM_* = objets à créer dans la copie de travail',
        'diagram_map': '[film_frame, image number of the sequence] for each frame of the segment (split 7.4 : '
                       'jusqu\'à inset_until - 1)',
        'units': 'mm (1 BU = 1 mm), angles in degrees'},
    'audio': audio['clips'],
    'chapters': chapters,
    'segments': SEG,
    'overlays': OVL,
    'overlays_source': INS_SOURCE,
    'layout': LAYOUT,
    'anchors': ANCHORS,
    'controller': {'crank': crank_keys, 'explode': explode_keys, 'patina': patina_keys},
    'highlights': HL,
    'blinks_6_1': blinks,
    'beats': beats,
    'engine_instants': {'olympia_entry': T_OLYMPIA, 'saros_entry': {str(k): v for k, v in SAROS_ENTRY.items()},
                        'mars_stations': MARS_STATIONS, 'mars_opposition': T_MARS_OPPOSITION},
    'subtitles': subs,
    'frames': frames,
}
(L.FILM / 'timeline.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))

# ----------------------------------------------------------------------------- summary
print('total %.2f s (%d min %05.2f s), %d frames -> %s' % (N_FRAMES / FPS, N_FRAMES // FPS // 60,
                                                         N_FRAMES / FPS % 60, N_FRAMES, L.FILM / 'timeline.json'))
for n in range(1, 8):
    c = chapters[n - 1]
    print('ch%d  voice %7.3f-%7.3f s (frame %4d)  pictures %4d-%4d  %s' % (n, A[n], A[n] + CH[n]['duration'], F(A[n]),
                                                                          c['frames'][0], c['frames'][1],
                                                                          ' '.join(c['shots'])))
for s in SEG:
    print('  %-5s %-8s %5d-%5d  %7.2f-%7.2f s  %-13s crank %.3f -> %.3f' % (
        s['id'], s['kind'], s['frames'][0], s['frames'][1], s['t0'], s['t1'], s.get('mode', ''),
        frames[s['frames'][0] - 1]['crank'], frames[s['frames'][1] - 1]['crank']))
print('overlays', ', '.join('%s %d-%d' % (o['sequence'], o['frames'][0], o['frames'][1]) for o in OVL))
print('blinks 6.1', [(b['cell'], b['glyph'], b['frame_entry']) for b in blinks])

# ----------------------------------------------------------------------------- verification (engine, voice, layout)
if '--no-verify' not in sys.argv:
    import verify_beats  # noqa: E402
    sys.exit(1 if verify_beats.main([a for a in sys.argv[1:] if a != '--no-verify'], quiet=True) else 0)
