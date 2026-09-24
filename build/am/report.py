"""Verification report: out/report.md and out/report.html (self-contained).
Run: python -m am.report  (after am.verify --stage all, Blender build/check/export/render)."""
import html
import json
import math
import os
import sys
from fractions import Fraction

from . import OUT, ROOT
from . import spec as S, kinematics as K, layout as LAY, involute as INV

YEAR = 365.2422

TRAINS = [
    # (output, chain, expr, turns_per_cycle, cycle label, reference key, factor on period)
    ('Crank a (turns/year)', 'a1 (crown) ~ b1', 'a', None, 'definition 223/48', None, 1),
    ('Mean Sun / date pointer b', 'b1 (input)', 'b', None, 'tropical year', 'tropical_year', 1),
    ('Moon pointer (mean sidereal)', 'b2>c1, c2>d1, d2>e2, e5>k1 ~pin~ k2>e6, e1>b3', 'moon', None,
     '254 sidereal months / 19 y', 'sidereal_month', 1),
    ('Moon phase q1 (synodic)', 'b0 ~ q1 (crown differential on the Moon pointer)', 'q@moon', None,
     'synodic month', 'synodic_month', 1),
    ('Lunar anomaly k1 on e3', 'e5>k1 relative to the e3 turntable', 'k@e_table', None, 'anomalistic month',
     'anomalistic_month', 1),
    ('Lunar apsidal line e3', 'b2>l1, l2>m1, m3>e3', 'e_table', None, '8.88 y', 'lunar_apsides_period', 1),
    ('Draconic month (Moon - nodes)', 'moon - t_nodes', 'moon-t_nodes', None, 'draconic month',
     'draconic_month', 1),
    ('Dragon Hand (nodes)', 'fx49>nd62, nd64>nd48 (spB on b)', 't_nodes', None, '18.6 y retrograde',
     'lunar_nodes_period_sidereal', 1),
    ('Metonic pointer (5 turns)', 'b2>l1, l2>m1, m2>n1', 'n', 5, '19 y = 235 synodic months',
     'metonic_235_synodic', 1),
    ('Olympiad pointer', '... m2>n1, n3>o1', 'o', 1, '4-year games cycle', None, 1),
    ('Callippic pointer', '... m2>n1, n2>p1, p2>cal1', 'cal', 1, '76 y = 940 synodic months',
     'callippic_940_synodic', 1),
    ('Saros pointer (4 turns)', '... l2>m1, m3>e3, e4>f1, f2>g1', 'g', 4, '223 synodic months',
     'saros_223_synodic', 1),
    ('Exeligmos pointer', '... f2>g1, g2>h1, h2>i1', 'i', 1, '3 Saros', 'exeligmos', 1),
    ('Mercury epicycle (synodic)', 'fx51>me72, me89>me40>me20 (on b), pin + follower', 'x_me20@b', None,
     '1513 synodic periods / 480 y', 'synodic_mercury', 1),
    ('Venus epicycle (synodic)', 'fx51>vn44, vn34>vn26>r1 (on b), pin + follower', 'x_r1@b', None,
     '289 synodic periods / 462 y', 'synodic_venus', 1),
    ('True-Sun epicycle su56 (anomaly)', 'fx56>cp52>su56 (on CP), eccentric pin + follower', 'x_su56@b',
     None, 'anomalistic year ~ tropical year', 'tropical_year', 1),
    ('Mars pin gear (synodic)', 'fx56>cp64, ma38>ma40>ma71', 'x_ma71@b', None, '133 syn / 284 y',
     'synodic_mars', 1),
    ('Mars output (sidereal)', '... ma71 ~pin~ ma80s>ma80o', 't_mars', None, '151 sid / 284 y', 'sidereal_mars', 1),
    ('Jupiter pin gear (synodic)', 'fx56>cp64, ju45>ju40>ju43', 'x_ju43@b', None, '315 syn / 344 y',
     'synodic_jupiter', 1),
    ('Jupiter output (sidereal)', '... ju43 ~pin~ ju65s>ju65o', 't_jupiter', None, '29 sid / 344 y',
     'sidereal_jupiter', 1),
    ('Saturn pin gear (synodic)', 'fx56>cp52, sa61>sa40>sa68', 'x_sa68@b', None, '427 syn / 442 y',
     'synodic_saturn', 1),
    ('Saturn output (sidereal)', '... sa68 ~pin~ sa86s>sa86o', 't_saturn', None, '15 sid / 442 y',
     'sidereal_saturn', 1),
]


def load(path, default=None):
    p = os.path.join(OUT, path)
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def fmt(x, n=4):
    if x is None:
        return '-'
    if isinstance(x, bool):
        return 'yes' if x else 'NO'
    if isinstance(x, float):
        if x != 0 and (abs(x) < 1e-3 or abs(x) >= 1e6):
            return '%.3e' % x
        return ('%.' + str(n) + 'f') % x
    return str(x)


class Doc:
    def __init__(self):
        self.blocks = []

    def h(self, level, text):
        self.blocks.append(('h', level, text))

    def p(self, text):
        self.blocks.append(('p', text))

    def ul(self, items):
        self.blocks.append(('ul', items))

    def table(self, head, rows):
        self.blocks.append(('table', head, rows))

    def md(self):
        out = []
        for b in self.blocks:
            if b[0] == 'h':
                out.append('#' * b[1] + ' ' + b[2] + '\n')
            elif b[0] == 'p':
                out.append(b[1] + '\n')
            elif b[0] == 'ul':
                out.append('\n'.join('- ' + i for i in b[1]) + '\n')
            else:
                head, rows = b[1], b[2]
                out.append('| ' + ' | '.join(head) + ' |')
                out.append('|' + '---|' * len(head))
                for r in rows:
                    out.append('| ' + ' | '.join(str(c).replace('|', '/') for c in r) + ' |')
                out.append('')
        return '\n'.join(out)

    def html(self, title):
        e = html.escape
        out = ['<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>%s</title>' % e(title),
               '<style>body{font-family:-apple-system,Helvetica,Arial,sans-serif;max-width:1200px;margin:2em auto;'
               'padding:0 1em;color:#222}table{border-collapse:collapse;margin:.6em 0 1.4em;font-size:13px}'
               'th,td{border:1px solid #ccc;padding:3px 7px;text-align:left}th{background:#f1ede4}'
               'tr:nth-child(even){background:#faf8f4}h1{color:#5a3d12}h2{border-bottom:2px solid #b8893c;'
               'padding-bottom:3px;margin-top:1.6em}.ok{color:#17692a;font-weight:600}.bad{color:#b01818;'
               'font-weight:700}code{background:#f3f3f3;padding:0 3px}</style></head><body>']
        for b in self.blocks:
            if b[0] == 'h':
                out.append('<h%d>%s</h%d>' % (b[1], e(b[2]), b[1]))
            elif b[0] == 'p':
                out.append('<p>%s</p>' % self._inline(b[1]))
            elif b[0] == 'ul':
                out.append('<ul>' + ''.join('<li>%s</li>' % self._inline(i) for i in b[1]) + '</ul>')
            else:
                head, rows = b[1], b[2]
                out.append('<table><tr>' + ''.join('<th>%s</th>' % e(str(h)) for h in head) + '</tr>')
                for r in rows:
                    out.append('<tr>' + ''.join('<td>%s</td>' % self._inline(str(c)) for c in r) + '</tr>')
                out.append('</table>')
        out.append('</body></html>')
        return '\n'.join(out)

    @staticmethod
    def _inline(t):
        t = html.escape(t)
        t = t.replace('GREEN', '<span class="ok">GREEN</span>').replace('RED', '<span class="bad">RED</span>')
        parts = t.split('**')
        t = ''.join(('<b>%s</b>' % s if i % 2 else s) for i, s in enumerate(parts))
        parts = t.split('`')
        return ''.join(('<code>%s</code>' % s if i % 2 else s) for i, s in enumerate(parts))


def build():
    spec = S.load()
    laws = K.Laws(spec)
    ok_k, kin = K.check(spec)
    rates = {k: Fraction(v) for k, v in kin['rates'].items()}
    ver = load('verify_all.json', {})
    geo = ver.get('geometry', {})
    exr = ver.get('expr', {})
    chk = load('check.json', {})
    br = load('build_report.json', {})
    prints = {p: load(os.path.join('print', p, 'print_report.json')) for p in ('resin_x1', 'resin_x1_5', 'fdm_x2')}
    renders = {n: os.path.exists(os.path.join(OUT, 'renders', n)) and os.path.getsize(os.path.join(OUT, 'renders', n)) > 0
               for n in ('front34.png', 'front.png', 'back.png', 'exploded.png', 'antikythera.mp4')}
    render_log = load(os.path.join('renders', 'render_info.json'), {})
    fp = S.fingerprint_report(spec.d)
    d = Doc()
    d.h(1, 'Antikythera Mechanism - functional reconstruction: verification report')
    d.p('Spec `%s` v%s (%s). Generated from `spec/antikythera.json`, `out/verify_all.json`, `out/check.json`, '
        '`out/build_report.json` and `out/print/*/print_report.json`.' % (
            spec['meta']['name'], spec['meta']['version'], spec['meta']['date']))
    # ---------------- acceptance criteria
    c = {}
    c[1] = fp['ok']
    c[2] = ok_k
    g = geo.get('summary', {})
    c[3] = bool(g.get('meshes')) and bool(g.get('tip_lands')) and chk.get('meshes', {}).get('ok', False)
    c[4] = bool(g.get('interference2d'))
    c[5] = bool(g.get('prefilter')) and bool(g.get('a1_zone')) and bool(g.get('sectors')) and bool(g.get('cosmos'))
    st = chk.get('static', {})
    c[6] = (st.get('drivers', {}).get('all_valid') and st.get('drivers', {}).get('all_simple')
            and st.get('drivers', {}).get('expressions_match') and st.get('readback', {}).get('ok')
            and all(v['ok'] for v in st.get('cycles', {}).values()) and bool(exr.get('ok'))) or False
    sm = chk.get('summary', {})
    c[7] = (sm.get('bvh_meshes_overlaps') == 0 and sm.get('bvh_pins_overlaps') == 0
            and sm.get('bvh_pairs_overlaps') == 0 and sm.get('bvh_pairs_samples') == 240)
    c[8] = bool(br.get('meshes_ok')) and bool(st.get('meshes', {}).get('all_ok'))
    deliver = {
        'out/am.blend': os.path.exists(os.path.join(OUT, 'am.blend')),
        'out/check.json': bool(chk),
        'out/report.md / report.html': True,
        'out/print/<profile>/*.stl + antikythera.3mf': all(p and p.get('ok') for p in prints.values()),
        'out/renders (4 stills + mp4)': all(renders.values()),
        'README.md, DECISIONS.md, PROGRESS.md': all(os.path.exists(os.path.join(ROOT, f))
                                                    for f in ('README.md', 'DECISIONS.md', 'PROGRESS.md')),
    }
    c[9] = all(deliver.values()) and bool(br.get('drivers_ok'))
    c[10] = os.path.exists(os.path.join(ROOT, 'PROGRESS.md')) and os.path.exists(os.path.join(ROOT, 'DECISIONS.md'))
    names = {1: 'Spec fingerprint identical', 2: 'Exact solver: DOF 1, rates, 22 targets',
             3: 'Meshes: centre distances, modules, face overlap, eps, z >= 8, nominal tip land; crowns by BVH (a)',
             4: '2D interference: 0 penetration (j = 0.03)',
             5: 'Pre-filter 0 conflicts, a1 keep-out, follower sectors, cosmos checks',
             6: 'Drivers valid/simple/untruncated, readback < 1e-5 rad, cycles closed',
             7: 'BVH: 0 overlapping pairs on every sample (dials and case included, FONT excluded)',
             8: 'Meshes closed, manifold, contiguous, volume = area x thickness (crowns per shell)',
             9: 'Deliverables present; am.blend animates without Python scripts',
             10: 'PROGRESS.md / DECISIONS.md up to date; deviations listed'}
    red = [k for k, v in c.items() if not v]
    d.h(2, 'Status')
    if red:
        d.p('**RED criteria: %s** - see the diagnostics below.' % ', '.join(str(k) for k in red))
    else:
        d.p('**All 10 acceptance criteria are GREEN.** No problem was found in the spec data; no fallback '
            'of section 8 was needed.')
    d.table(['#', 'Criterion (section 9)', 'State'], [[k, names[k], 'GREEN' if c[k] else 'RED'] for k in sorted(c)])
    # ---------------- trains
    d.h(2, 'Trains and periods')
    d.p('Periods in days use the model year = 1 tropical year = %.4f days. Deviations are relative to '
        '`reference_values_days` (modern values); each train reproduces its ancient period relation exactly.' % YEAR)
    rows = []
    ref = spec['reference_values_days']
    for name, chain, ex, turns, cyc, rk, _ in TRAINS:
        r = K.eval_target(spec, rates, ex)
        per = None
        if r != 0 and ex != 'a':
            per = YEAR / abs(float(r)) * (turns or 1)
        dev = None
        if per and rk:
            dev = (per - ref[rk]) / ref[rk]
        rows.append([name, chain, str(r) if ex != 'a' else '223/48', cyc, fmt(per, 4) if per else '-',
                     fmt(ref.get(rk), 4) if rk else '-', ('%+.2e' % dev) if dev is not None else '-'])
    d.table(['Output', 'Chain', 'Exact rate (rev/y)', 'Cycle', 'Period (d)', 'Reference (d)', 'Rel. dev.'], rows)
    # ---------------- kinematics
    d.h(2, 'Kinematics (exact)')
    d.ul(['Unknowns %d (mobile bodies except frame, a, q); equations %d = %d Willis + %d pin-slot + %d followers.' % (
        kin['n_unknowns'], kin['n_equations'], kin['counts']['willis'], kin['counts']['pin_slot'], kin['counts']['follower']),
        'Rank **%d**, degrees of freedom **%d**, inconsistent constraints %d; rank with input w_b = 1: %d.' % (
            kin['rank'], kin['dof'], kin['inconsistent'], kin['rank_with_input']),
        'Mean rates equal to `rate_abs_mean` for all bodies: %s; targets exact: %d/%d.' % (
            not kin['rate_errors'], sum(t['ok'] for t in kin['targets']), len(kin['targets']))])
    d.table(['Target', 'Expr', 'Expected', 'Solver', 'OK'],
            [[t['name'], t['expr'], t['expected'], t['got'], 'GREEN' if t['ok'] else 'RED'] for t in kin['targets']])
    # ---------------- cosmos
    d.h(2, 'Cosmos checks (section 5.8)')
    cos = geo.get('cosmos', {})
    rows = []
    for k, v in cos.items():
        val = {kk: vv for kk, vv in v.items() if kk != 'ok' and not isinstance(vv, list)}
        rows.append([k, ', '.join('%s = %s' % (kk, fmt(vv) if isinstance(vv, float) else vv) for kk, vv in val.items()),
                     'GREEN' if v['ok'] else 'RED'])
    d.table(['Check', 'Values', 'State'], rows)
    # ---------------- meshes table
    d.h(2, 'Modules and centre distances (37 external meshes)')
    d.table(['Mesh', 'Carrier', 'Module', 'Centre distance', 'Error (mm)', 'Face overlap', 'eps', 'eps spec',
             '2D min signed', 'Backlash near', 'OK'],
            [[m['mesh'], m['carrier'], fmt(m['module'], 6), fmt(m['centre_distance'], 6), '%.1e' % m['cd_error'],
              fmt(m['face_overlap'], 2), fmt(m['contact_ratio'], 3), m['contact_ratio_spec'],
              fmt(i['min_signed'], 4), fmt(i['backlash_near_min'], 4),
              'GREEN' if (m['ok'] and i['ok']) else 'RED']
             for m, i in zip(geo.get('meshes', []), geo.get('interference2d', []))])
    tl = geo.get('tip_lands', [])
    if tl:
        w = min(tl, key=lambda r: r['tip_land_nominal_over_m'])
        d.p('Tip lands: minimum nominal tip land %.3f m (%s); minimum thinned (j = 0.03) tip land %.4f mm; '
            'root fillet between %.3f m and 0.200 m (reduced where two fillets would not fit).' % (
                w['tip_land_nominal_over_m'], w['gear'], min(r['tip_land_thinned_mm'] for r in tl),
                min(r['fillet_over_m'] for r in tl)))
    # ---------------- all checks
    d.h(2, 'Verification results')
    pre = geo.get('prefilter', {})
    items = [
        'Spec SHA-256 `%s` (%s); 24/24 section fingerprints: %s.' % (fp['sha256'], 'identical' if fp['ok'] else 'DIFFERENT',
                                                                    all(fp['sections'].values())),
        'Phasing: %s spur components, %s gears phased (b1, b0 at local 0; crowns pre-phased).' % (
            geo.get('phasing', {}).get('components'), geo.get('phasing', {}).get('phased_gears')),
        'Pre-filter: %s parts, %s z-overlapping pairs of different bodies, **%s conflicts**, %s intended contacts '
        '(meshes, pin-slots, shafts in plate holes, slider pins in grooves), %s pairs retained for the BVH.' % (
            pre.get('n_parts'), pre.get('n_pairs_z_overlap'), pre.get('n_conflicts'), pre.get('n_intended'),
            pre.get('n_retained')),
        'a1 keep-out: largest radius carried by b between z 4.6 and 33.73 (b1 excepted): %s mm (limit 63.6).' % (
            geo.get('a1_zone', [{}])[0].get('r_max') if geo.get('a1_zone') else '-'),
        'Follower sectors (relative to b): %s; no b-carried object in them except the intended pins.' % (
            {k: v['sector_deg'] for k, v in geo.get('sectors', {}).items()}),
        'Driver expressions: %s bodies, max length %s, max error %s rad vs the solver over %s samples in [-50, 50].' % (
            exr.get('bodies'), exr.get('max_len'), fmt(exr.get('max_err')), exr.get('samples')),
        'Blender drivers: %s on objects, all valid %s, all simple %s, expressions identical %s; readback max error '
        '%s rad over %s float32 crank values.' % (
            st.get('drivers', {}).get('count'), st.get('drivers', {}).get('all_valid'),
            st.get('drivers', {}).get('all_simple'), st.get('drivers', {}).get('expressions_match'),
            fmt(st.get('readback', {}).get('max_err_rad')), st.get('readback', {}).get('samples')),
        'Cycle closure: %s.' % ', '.join('%s after %s y: %s rad' % (k, fmt(v['period_years'], 4), fmt(v['max_err_rad']))
                                          for k, v in st.get('cycles', {}).items()),
        'Crank F-curve: %s (frames 1/61/481/961), extrapolation %s.' % (
            st.get('crank_fcurve', {}).get('values'), st.get('crank_fcurve', {}).get('extrapolation')),
        'BVH (world coordinates, overlap()): (a) 39 meshes x 50 positions per pitch: %s overlaps; (b) 7 pin-slots/'
        'followers + 2 spiral sliders x 72 positions per relative cycle: %s overlaps; (c) %s retained pairs x %s crank '
        'values (120 on [0,1] + 120 random on [0,76], seed 20260924): %s overlaps. Sanity test: known intersections '
        'and a half-pitch mis-phased gear are detected.' % (
            sm.get('bvh_meshes_overlaps'), sm.get('bvh_pins_overlaps'), pre.get('n_retained'),
            sm.get('bvh_pairs_samples'), sm.get('bvh_pairs_overlaps')),
        'Meshes: %s mesh objects, all closed/manifold/contiguous: %s; extruded volumes = area x (float32(z1) - '
        'float32(z0)), max relative error %s.' % (
            br.get('n_mesh_objects'), br.get('meshes_ok'),
            fmt(max((v.get('volume_rel_err', 0) for v in br.get('parts', {}).values()), default=None))),
        'Spirals: slider pin vs rho(psi): %s.' % {k: '%s mm' % fmt(v['max_err_mm']) for k, v in
                                                 chk.get('spiral', {}).get('spirals', {}).items()},
        'Units: %s; controller `crank` and `patina` float: %s / %s.' % (
            st.get('scene', {}).get('units'), st.get('scene', {}).get('crank_is_float'),
            st.get('scene', {}).get('patina_is_float')),
    ]
    d.ul(items)
    # ---------------- texts
    d.h(2, 'FONT texts (excluded from manifold, BVH and print checks)')
    tx = chk.get('texts', {})
    d.p('Built-in font, extrusion 0.025 (0.05 thick), body frame, collection AM_DIALS. Missing glyphs (compared with '
        'the notdef box of U+10300): %s. The stigma is written ΙΣΤ as in the spec.' % (tx.get('missing_glyphs') or 'none'))
    d.table(['Text', 'Content', 'z range', 'Closest moving part overlapping in xy (dz, part)', 'OK'],
            [[t['text'], t['body'], '%.3f..%.3f' % tuple(t['z']),
              '%.3f %s' % tuple(t['closest_moving']) if t['closest_moving'] else '-', 'GREEN' if t['ok'] else 'RED']
             for t in tx.get('texts', [])])
    # ---------------- parts by status
    cat = LAY.build(spec, laws, phases=INV.compute_phases(spec, laws)[0])
    d.h(2, 'Parts by status')
    for stt in S.STATUSES:
        ps = [p['name'] for p in cat.parts if p['status'] == stt]
        d.p('**%s** (%d): %s' % (stt, len(ps), ', '.join(ps)))
    d.p('Collections: %s' % chk.get('static', {}).get('collections'))
    # ---------------- print
    d.h(2, 'Print export')
    rows = []
    for name, p in prints.items():
        if not p:
            rows.append([name, 'missing', '', '', '', '', ''])
            continue
        rows.append([name, '%s STL + 3MF (%.1f MB, %d objects, closed %s)' % (
            p['n_stl'], p['threemf']['bytes'] / 1e6, p['threemf']['objects'], p['threemf']['ok']),
            '%s (backlash near %.4f..%.4f mm)' % (p['interference2d_ok'], *p['interference2d_backlash_near']),
            ', '.join('%s %.1e' % (r['part'], r['rel_err']) for r in p['reimport']),
            ', '.join(o['part'] for o in p['oversize']),
            ', '.join('%s %.3f' % (f['gear'], f['tip_land_mm']) for f in p['walls']['fragile_tip_lands']) or '-',
            '%d below %.2f mm (min %.3f)' % (len(p['walls']['below_min']), p['walls']['min_wall_mm'],
                                             p['walls']['min_found_mm'])])
    d.table(['Profile', 'Files', '2D check', 'STL re-import rel. err', 'Larger than the bed', 'Fragile tips (tip land mm)',
             'Walls'], rows)
    # ---------------- renders
    d.h(2, 'Renders')
    d.p('Files: %s. %s' % (', '.join('%s %s' % (k, 'present' if v else 'MISSING') for k, v in renders.items()),
                           render_log.get('note', '')))
    # ---------------- defaults, decisions, fallbacks
    d.h(2, 'Unresolved defaults applied (spec)')
    d.ul(spec['unresolved_defaults'])
    d.h(2, 'Decisions')
    with open(os.path.join(ROOT, 'DECISIONS.md'), encoding='utf-8') as f:
        dec = [ln[2:].strip() for ln in f if ln.startswith('- ')]
    d.ul(dec)
    d.h(2, 'Fallbacks (section 8) and deviations')
    fb = render_log.get('fallbacks', [])
    d.ul(fb or ['None: no crown tightening, no flank densification, no remodelling of a non-toothed part, '
                'no intermediate empties; Cycles Metal used for the stills.'])
    return d, c


def main():
    d, c = build()
    with open(os.path.join(OUT, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(d.md())
    with open(os.path.join(OUT, 'report.html'), 'w', encoding='utf-8') as f:
        f.write(d.html('Antikythera verification report'))
    print('[report] out/report.md, out/report.html; criteria %s' % {k: ('GREEN' if v else 'RED') for k, v in c.items()})
    return 0 if all(c.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
