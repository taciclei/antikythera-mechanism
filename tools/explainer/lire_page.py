#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page web « Comment lire la machine d'Anticythère » (docs/lire/index.html).

Utiliser le Python de Blender (numpy) :
    PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
    $PY tools/explainer/lire_page.py inject   # réécrit le bloc <script type="application/json" id="am-data">
    $PY tools/explainer/lire_page.py check    # moteur JavaScript de la page (node) contre engine.py

`inject` ne touche qu'au bloc de données de la page ; il le recalcule à partir de engine.py
(qui ne lit que spec/antikythera.json) et de build/out/explainer/engine_export.json.
`check` extrait le moteur JavaScript de la page (<script id="am-engine">), l'exécute avec node
sur les mêmes dates que le moteur Python et compare les lectures. Rapport :
build/out/explainer/lire_crosscheck.json. Code de sortie 1 si un écart dépasse la tolérance.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402

PAGE = ROOT / 'docs' / 'lire' / 'index.html'
EXPORT = E.OUT_DIR / 'engine_export.json'
REPORT = E.OUT_DIR / 'lire_crosscheck.json'
DATA_RE = re.compile(r'(<script type="application/json" id="am-data">)(.*?)(</script>)', re.S)
ENGINE_RE = re.compile(r'<script id="am-engine">(.*?)</script>', re.S)

# Visibilité des éclipses 2026-2028 (NASA/GSFC, F. Espenak ; résumé de build/out/explainer/faits.md, partie 6)
NASA_WHERE = {
    '2026-02-17': 'annulaire en Antarctique ; partielle dans le sud de l’Argentine et du Chili, en Afrique australe',
    '2026-03-03': 'est de l’Asie, Australie, Pacifique, Amériques',
    '2026-08-12': 'totale dans l’Arctique, au Groenland, en Islande et en Espagne ; partielle en Europe',
    '2026-08-28': 'est du Pacifique, Amériques, Europe, Afrique',
    '2027-02-06': 'annulaire au Chili, en Argentine et dans l’Atlantique',
    '2027-02-20': 'Amériques, Europe, Afrique, Asie',
    '2027-07-18': 'est de l’Afrique, Asie, Australie, Pacifique',
    '2027-08-02': 'totale au Maroc, dans le sud de l’Espagne, en Algérie, en Libye, en Égypte et en Arabie',
    '2027-08-17': 'Pacifique, Amériques',
    '2028-01-12': 'Amériques, Europe, Afrique',
    '2028-01-26': 'annulaire en Équateur, au Pérou, au Brésil, en Espagne et au Portugal',
    '2028-07-06': 'Europe, Afrique, Asie, Australie',
    '2028-07-22': 'totale en Australie et en Nouvelle-Zélande',
    '2028-12-31': 'Europe, Afrique, Asie, Australie, Pacifique',
}


def srgb_hex(rgb_linear):
    def enc(c):
        c = max(0.0, min(1.0, c))
        v = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        return int(round(v * 255))
    return '#%02X%02X%02X' % tuple(enc(c) for c in rgb_linear)


def page_data():
    X = json.loads(EXPORT.read_text())
    m0 = E.Machine()
    S = m0.S
    rel = {k: [m0.rel[k].numerator, m0.rel[k].denominator] for k in m0.revolute}
    colors = {p['label']: srgb_hex(p['rgb_linear']) for p in S['dials']['front']['planet_display']['planets']}
    cal = X['calage_J2000']
    sub = {}
    for sid, s in X['cadrans_secondaires'].items():
        sub[sid] = {'pointer_body': s['pointer_body'], 'sectors': s['sectors'],
                    'labels': s.get('labels'), 'tilt_deg': s.get('sector_tilt_deg', 0.0), 'radius': s['radius']}
    axes = S['axes_world_xy']
    nasa = []
    for kind, iso, typ, saros in E.NASA_ECLIPSES_2026_2028:
        nasa.append({'kind': kind, 'td': iso, 'jd': E.parse_date(iso), 'type': typ, 'saros': saros,
                     'where': NASA_WHERE[iso[:10]]})
    return {
        'genere_par': 'tools/explainer/lire_page.py inject (depuis tools/explainer/engine.py)',
        'spec_sha256': m0.spec_sha256,
        'year_days': E.YEAR_DAYS, 'jd_j2000': E.JD_J2000, 'synodic_real': E.SYNODIC_REAL,
        'month_years': m0.month,
        'crank': [m0.crank_rate.numerator, m0.crank_rate.denominator],
        'lin_bodies': list(m0.revolute),
        'rel': rel,
        'pin_slots': {s: {'pin': p['pin'], 'e': p['e'], 'r': p['r'], 'beta': p['beta']} for s, p in m0.pin_slots.items()},
        'out_of_slot': m0.out_of_slot,
        'followers': {b: {'epi': f['epi'], 'i': f['i'], 'd': f['d'], 'g0': f['g0'], 'ph': f['ph']}
                      for b, f in m0.followers.items()},
        'markers': m0.marker,
        'spirals': {w: {'body': s['body'], 'turns': s['turns'], 'cells': s['cells'], 'r_start': s['r_start'],
                        'pitch': s['pitch'], 'q': [s['q'].numerator, s['q'].denominator]}
                    for w, s in m0.spirals.items()},
        'subsidiary': sub,
        'back_centres': {k: axes[k] for k in ('N', 'G', 'O', 'cal', 'I')},
        'labels': dict(X['libelles'], jeux_fr=E.GAMES_FR),
        'planet_colors': colors,
        'limits': {'solar': E.LIMITS['solar_deg'], 'lunar': E.LIMITS['lunar_deg']},
        'eyu_deg': E.EYU_DEG,
        'meeus': {k: list(v) for k, v in E.MEEUS.items()},
        'jpl': {k: [list(a), list(b)] for k, (a, b) in E.JPL_1800_2050.items()},
        'anchors': E.ANCHORS,
        'cal_j2000': {'name': 'J2000', 'epoch_jd': cal['epoch_jd'], 't_epoch': cal['t_epoch'],
                      'phases': X['phases']['cale_J2000'],
                      'cycles': {w: {'offset': c['offset']} for w, c in cal['cycles'].items()},
                      'olympiad': {'t_start': cal['olympiad']['t_start'],
                                   'number_at_start': cal['olympiad']['number_at_start']},
                      'glyphs': X['glyphes']['cale_J2000_limites'],
                      't_cycle_start': X['glyphes']['cale_J2000_t_debut_cycle']},
        'drift': {k: v['derive_deg_par_siecle'] for k, v in X['derive'].items() if not k.startswith('_')},
        'drift_summary': X['derive']['_resume'],
        'nasa': nasa,
    }


def inject():
    html = PAGE.read_text()
    data = json.dumps(page_data(), ensure_ascii=False, separators=(',', ':'))
    assert '</' not in data
    new, n = DATA_RE.subn(lambda m: m.group(1) + data + m.group(3), html)
    if n != 1:
        raise SystemExit('bloc am-data introuvable dans %s' % PAGE)
    PAGE.write_text(new)
    print('écrit %s (%d octets de données, page %d octets)' % (PAGE, len(data.encode()), len(new.encode())))


# ============================================================================= vérification croisée
DATES = ['2026-09-25T12:00', '2026-08-12T13:52', '2026-03-03T02:08', '2027-08-02T07:34', '2028-07-21T12:00',
         '2028-12-31T17:02', '2000-01-01T12:00', '1969-07-20T20:17', '1900-04-04T00:00', '1582-10-04T12:00',
         '1582-10-15T00:00', '1054-07-04T06:00', '0001-01-01T00:00', '-204-05-12T12:00', '-329-06-28T12:00',
         '-775-08-01T00:00', '2500-06-01T00:00', '3000-01-01T00:00', '-2000-03-21T18:30', '2029-08-01T00:00']
RECAL_EPOCHS = ['-204-05-12T12:00', '1000-01-01T00:00', '2000-01-01T12:00', '3000-06-15T00:00']
MODEL_T = [0.0, 1.0, 3.3, -7.25, 26.73, -2204.4, 1234.5678]
LON_KEYS = ['soleil_moyen', 'soleil_vrai', 'lune', 'noeud_ascendant', 'phase', 'mercure', 'venus', 'mars',
            'jupiter', 'saturne']

HARNESS = r"""
const fs = require('fs');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const src = fs.readFileSync(process.argv[3], 'utf8');
const Q = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const makeEngine = new Function(src + '\nreturn makeEngine;')();
const AM = makeEngine(D);
const cal = AM.calJ2000;
const out = {reads: [], model: [], recal: [], events: null, sky: [], dates: []};
for (const s of Q.dates) {
  const jd = AM.parseDate(s);
  out.reads.push({date: s, jd, read: AM.read(AM.tFromJd(jd), cal)});
  out.dates.push({date: s, jd, back: AM.parseDate(AM.formatJd(jd).split(' (')[0].split(' [')[0].replace(' TT', '').replace(' ', 'T')),
                  fmt: AM.formatJd(jd), sky: AM.realSky(jd)});
}
for (const t of Q.model_t) {
  const A = AM.local(t, {});
  const L = AM.lons(A);
  const st = AM.state(t, {phases: {}});
  out.model.push({t, lon: L, psi: st.psi});
}
const t0 = AM.tFromJd(AM.parseDate('2026-01-01')), t1 = AM.tFromJd(AM.parseDate('2029-12-31'));
out.events = AM.machineEvents(t0, t1, cal).map(e => Object.assign({}, e, {date: AM.formatJd(AM.jdFromT(e.t))}));
out.glyphJ2000 = AM.glyphTable(cal, cal.t_cycle_start);
for (const s of Q.recal) {
  const jd = AM.parseDate(s);
  const c = AM.calibrate(jd);
  const reads = Q.recal_offsets.map(dy => ({dy, read: AM.read(c.t_epoch + dy, c)}));
  out.recal.push({epoch: s, jd, phases: c.phases, cycles: c.cycles, olympiad: c.olympiad, t_cycle_start: c.t_cycle_start,
                  glyphs: c.glyphs, reads});
}
const tn = AM.tFromJd(AM.parseDate('2026-09-25T12:00'));
out.next = {full: AM.nextSyzygy(tn, Math.PI, cal), newm: AM.nextSyzygy(tn, 0, cal), eclipse: AM.nextEclipse(tn, cal),
            games: AM.nextGamesEntry(tn, cal), olympia: AM.nextGamesEntry(tn, cal, 'ΟΛΥΜΠΙΑ'),
            mars: AM.nextStation('mars', tn, cal, 'début')};
process.stdout.write(JSON.stringify(out));
"""


def angdiff_deg(a, b):
    return abs(((a - b + 180.0) % 360.0) - 180.0)


def check():
    node = shutil.which('node')
    if not node:
        raise SystemExit('node introuvable')
    html = PAGE.read_text()
    data = DATA_RE.search(html).group(2)
    eng = ENGINE_RE.search(html).group(1)
    tmp = Path(tempfile.mkdtemp(prefix='lire_check_'))
    (tmp / 'data.json').write_text(data)
    (tmp / 'engine.js').write_text(eng)
    (tmp / 'harness.js').write_text(HARNESS)
    offsets = [0.0, 0.37, 5.5, -3.2, 40.0]
    (tmp / 'q.json').write_text(json.dumps({'dates': DATES, 'model_t': MODEL_T, 'recal': RECAL_EPOCHS,
                                            'recal_offsets': offsets}))
    # syntaxe de tous les scripts de la page
    syntax = {}
    for i, m in enumerate(re.finditer(r'<script(?: id="([^"]+)")?>(.*?)</script>', html, re.S)):
        f = tmp / ('script_%d.js' % i)
        f.write_text(m.group(2))
        r = subprocess.run([node, '--check', str(f)], capture_output=True, text=True)
        syntax[m.group(1) or 'script_%d' % i] = 'OK' if r.returncode == 0 else r.stderr.strip()[:400]
    r = subprocess.run([node, str(tmp / 'harness.js'), str(tmp / 'data.json'), str(tmp / 'engine.js'), str(tmp / 'q.json')],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr)
        raise SystemExit('le moteur JavaScript a échoué')
    J = json.loads(r.stdout)
    mc = E.get_machine(True)
    worst = {}
    mism = []

    def upd(k, v):
        worst[k] = max(worst.get(k, 0.0), v)

    def same(ctx, what, a, b):
        if a != b:
            mism.append('%s : %s  JS=%r  PY=%r' % (ctx, what, a, b))

    def cmp_read(ctx, js, py, t, m):
        # longitudes brutes
        st = m.state(t)
        for k in LON_KEYS:
            upd('longitudes (deg)', angdiff_deg(math.degrees(js['lon'][k]), math.degrees(float(st['lon'][k]))))
        for w in ('metonic', 'saros', 'olympiad', 'callippic', 'exeligmos'):
            upd('psi aiguilles arrière (deg)', angdiff_deg(math.degrees(js['psi'][w]), math.degrees(float(st['psi'][w]))))
        same(ctx, 'Soleil moyen', js['soleil']['moyen']['texte'], py['soleil']['moyen (aiguille de date)']['texte'])
        same(ctx, 'Soleil vrai', js['soleil']['vrai']['texte'], py['soleil']['vrai (sphère dorée)']['texte'])
        for ring in ('anneau_fixe', 'anneau_regle'):
            if ring in py['calendrier_egyptien']:
                same(ctx, ring, js['calendrier_egyptien'][ring]['texte'], py['calendrier_egyptien'][ring]['texte'])
        L = py['lune']
        same(ctx, 'Lune', js['lune']['texte'], L['texte'])
        same(ctx, 'phase', js['lune']['phase'], L['phase'])
        Dp = math.degrees(float(st['lon']['phase']))            # valeurs brutes (la lecture Python est arrondie)
        upd('fraction éclairée', abs(js['lune']['fraction_eclairee'] - (1 - math.cos(math.radians(Dp))) / 2))
        upd('âge de la Lune (jours)', abs(js['lune']['age_jours'] - Dp / 360 * m.month * E.YEAR_DAYS))
        for body, key, name in E.PLANETS:
            p = py['planetes'][name]; q = js['planetes'][name]
            same(ctx, name, q['texte'], p['texte'])
            same(ctx, name + ' rétrograde', q['retrograde'], p['retrograde'])
            v = float(m.rate(key, t)) / E.TAU * 360 / E.YEAR_DAYS
            upd('vitesse des planètes (°/jour)', abs(q['vitesse_deg_par_jour'] - v))
        d = py['aiguille_du_dragon']
        same(ctx, 'nœud', js['aiguille_du_dragon']['noeud_ascendant']['texte'], d['noeud_ascendant']['texte'])
        dist, _ = m.node_distance(t, 'NM')
        upd('distance Lune-nœud (deg)', abs(js['aiguille_du_dragon']['lune_distance_au_noeud_deg'] - float(dist)))
        same(ctx, 'Lune au nord', js['aiguille_du_dragon']['lune_au_nord_de_l_ecliptique'], d['lune_au_nord_de_l_ecliptique'])
        for key, fields in (('metonique', ('case', 'spire', 'annee_du_cycle', 'mois_dans_l_annee', 'cycle_numero')),
                            ('callippique', ('secteur',)),
                            ('jeux', ('secteur', 'inscription', 'annee_de_l_olympiade', 'olympiade_numero')),
                            ('saros', ('case', 'spire', 'glyphe', 'cycle_numero')),
                            ('exeligmos', ('secteur', 'inscription', 'heures_a_ajouter'))):
            for f in fields:
                if f in py[key]:
                    same(ctx, key + '.' + f, js[key].get(f), py[key][f])

    for item in J['reads']:
        jd = E.parse_date(item['date'])
        upd('JD (jours)', abs(item['jd'] - jd))
        t = float(E.t_from_jd(jd))
        cmp_read(item['date'], item['read'], mc.read(t), t, mc)
    for item in J['dates']:
        same(item['date'], 'format_jd', item['fmt'], E.format_jd(item['jd']))
        upd('aller-retour date (jours)', abs(item['back'] - item['jd']))
        sky = E.real_sky(item['jd'])
        for k, v in sky.items():
            upd('ciel réel de référence (deg)', angdiff_deg(item['sky'][k], v))
    m0 = E.Machine()
    for item in J['model']:
        st = m0.state(item['t'])
        for k in LON_KEYS:
            upd('modèle non calé : longitudes (deg)', angdiff_deg(math.degrees(item['lon'][k]), math.degrees(float(st['lon'][k]))))
        for w in ('metonic', 'saros'):
            upd('modèle non calé : psi (deg)', angdiff_deg(math.degrees(item['psi'][w]), math.degrees(float(st['psi'][w]))))
    # table de glyphes J2000 recalculée en JS = table exportée
    exported = json.loads(EXPORT.read_text())['glyphes']['cale_J2000_limites']
    same('glyphes J2000', 'table recalculée en JS', J['glyphJ2000'], exported)
    # recalage sur d'autres époques
    for item in J['recal']:
        jd = E.parse_date(item['epoch'])
        ma = E.calibrate(jd)
        for k, v in ma.phases.items():
            upd('phases de calage (rad)', abs(E.wrappi(item['phases'][k] - v)))
        for w in ('saros', 'metonic'):
            same(item['epoch'], 'cycles.%s.offset' % w, item['cycles'][w]['offset'], ma.calibration['cycles'][w]['offset'])
        upd('calage : début des Olympiades (ans)', abs(item['olympiad']['t_start'] - ma.calibration['olympiad']['t_start']))
        same(item['epoch'], 'olympiade de départ', item['olympiad']['number_at_start'], ma.calibration['olympiad']['number_at_start'])
        tab = ma.engraved_table()
        same(item['epoch'], 'table de glyphes', item['glyphs'], [c['glyph'] for c in tab['cells']])
        for r in item['reads']:
            t = ma.calibration['t_epoch'] + r['dy']
            cmp_read('%s %+g an' % (item['epoch'], r['dy']), r['read'], ma.read(t), t, ma)
    # événements 2026-2029
    pe = E.machine_events('2026-01-01', '2029-12-31', machine=mc)
    kinds = ('nouvelle lune', 'pleine lune', 'éclipse de Soleil', 'éclipse de Lune', 'Jeux : nouveau secteur',
             'début de rétrogradation', 'fin de rétrogradation')
    ev_count = {}
    for kind in kinds:
        a = [e for e in J['events'] if e['type'] == kind]
        b = [e for e in pe if e['type'] == kind]
        if kind.endswith('rétrogradation'):
            a = sorted(a, key=lambda e: (e['planete'], e['t'])); b = sorted(b, key=lambda e: (e['planete'], e['t']))
        ev_count[kind] = [len(a), len(b)]
        if len(a) != len(b):
            mism.append('événements %s : %d en JS, %d en Python' % (kind, len(a), len(b)))
            continue
        for x, y in zip(a, b):
            upd('instants des événements (minutes)', abs(x['t'] - y['t']) * E.YEAR_DAYS * 1440)
            if kind.startswith('éclipse'):
                for f in ('case_saros', 'glyphe_case', 'predite_par_aiguille_du_dragon', 'predite_par_cadran_saros', 'lune_au_nord'):
                    same(y['date'], f, x[f], y[f])
                upd('distance au nœud des éclipses (deg)', abs(x['distance_noeud_deg'] - float(mc.node_distance(y['t'], 'NM')[0])))
            if kind.startswith('Jeux'):
                for f in ('inscription', 'annee_de_l_olympiade', 'olympiade_numero'):
                    same(y['date'], f, x[f], y[f])
            if kind.endswith('rétrogradation'):
                same(y['date'], 'planète', x['planete'], y['planete'])
    # « prochain … » depuis le 25/09/2026 12:00
    tn = float(E.t_from_date('2026-09-25T12:00'))
    nx = J['next']
    syz = mc.syzygies(tn + 1e-9, tn + 0.2)
    py_full = next(t for t, k in syz if k == 'FM'); py_new = next(t for t, k in syz if k == 'NM')
    py_ecl = next(e for e in machine_after(mc, tn) if e['type'].startswith('éclipse'))
    py_games = [e for e in E.machine_events(E.format_jd(E.jd_from_t(tn)).split(' ')[0], '2031-01-01', machine=mc)
                if e['type'] == 'Jeux : nouveau secteur' and e['t'] > tn]
    py_oly = next(e for e in py_games if 'ΟΛΥΜΠΙΑ' in e['inscription'].split())   # « ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ »
    py_mars = next(e for e in E.machine_events('2026-09-25', '2030-01-01', machine=mc)
                   if e['type'] == 'début de rétrogradation' and e['planete'] == 'Mars' and e['t'] > tn)
    nexts = {'prochaine pleine lune': (nx['full'], py_full), 'prochaine nouvelle lune': (nx['newm'], py_new),
             'prochaine éclipse': (nx['eclipse']['t'], py_ecl['t']), 'prochains Jeux': (nx['games']['t'], py_games[0]['t']),
             'prochains Jeux olympiques': (nx['olympia']['t'], py_oly['t']),
             'prochaine rétrogradation de Mars': (nx['mars'], py_mars['t'])}
    for k, (a, b) in nexts.items():
        upd('boutons « prochain… » (minutes)', abs(a - b) * E.YEAR_DAYS * 1440)
    same('prochaine éclipse', 'type', nx['eclipse']['type'], py_ecl['type'])
    same('prochains Jeux', 'inscription', nx['games']['inscription'], py_games[0]['inscription'])
    same('prochains Jeux olympiques', 'inscription', nx['olympia']['inscription'], py_oly['inscription'])

    tol = {'longitudes (deg)': 1e-8, 'psi aiguilles arrière (deg)': 1e-8, 'fraction éclairée': 1e-9,
           'âge de la Lune (jours)': 1e-8, 'vitesse des planètes (°/jour)': 1e-6, 'distance Lune-nœud (deg)': 1e-8,
           'JD (jours)': 1e-9, 'aller-retour date (jours)': 1e-3, 'ciel réel de référence (deg)': 1e-8,
           'modèle non calé : longitudes (deg)': 1e-9, 'modèle non calé : psi (deg)': 1e-9,
           'phases de calage (rad)': 1e-9, 'calage : début des Olympiades (ans)': 1e-9,
           'instants des événements (minutes)': 0.01, 'distance au nœud des éclipses (deg)': 1e-6,
           'boutons « prochain… » (minutes)': 0.05}
    bad = [k for k, v in worst.items() if v > tol.get(k, 0)]
    rep = {'page': str(PAGE.relative_to(ROOT)), 'node': subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip(),
           'syntaxe_node_check': syntax, 'dates_lues': len(J['reads']), 'epoques_de_recalage': RECAL_EPOCHS,
           'lectures_recalees': sum(len(x['reads']) for x in J['recal']), 'evenements_2026_2029_js_py': ev_count,
           'ecarts_max': {k: '%.3g' % v for k, v in worst.items()}, 'tolerances': tol,
           'desaccords': mism, 'au_dela_de_la_tolerance': bad,
           'verdict': 'OK' if not mism and not bad and all(v == 'OK' for v in syntax.values()) else 'ÉCHEC'}
    E.write_json(REPORT, rep)
    print('Syntaxe (node --check) :', syntax)
    print('Lectures comparées : %d dates calées J2000 + %d lectures recalées (%d époques) + %d instants du modèle non calé'
          % (len(J['reads']), rep['lectures_recalees'], len(RECAL_EPOCHS), len(J['model'])))
    print('Événements 2026-2029 (JS, Python) :', ev_count)
    for k, v in worst.items():
        print('  %-42s max %.3g   (tolérance %.0e)%s' % (k, v, tol.get(k, 0), '  <-- TROP GRAND' if k in bad else ''))
    print('Désaccords de texte ou de valeurs discrètes : %d' % len(mism))
    for x in mism[:40]:
        print('   ', x)
    print('VERDICT', rep['verdict'], '->', REPORT)
    return rep['verdict'] == 'OK'


def machine_after(m, t):
    jd = float(E.jd_from_t(t))
    return [e for e in E.machine_events(jd, jd + 5 * 365.25, machine=m) if e['t'] > t]


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'inject':
        inject()
    elif cmd == 'check':
        sys.exit(0 if check() else 1)
    else:
        print(__doc__)
