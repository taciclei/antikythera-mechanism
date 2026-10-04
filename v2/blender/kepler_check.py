"""Anticythère 2.0 — contrôle des tours de Kepler dans Blender : section « kepler » de check.py (CONTRACT.md § 8).

Seulement si la scène contient des pièces Kepler (propriété `kepler` = 1) ; sinon check.py n'ajoute rien.
(1) maillages : toutes les pièces Kepler sont des variétés fermées valides, quel que soit leur `kind` ;
(2) relecture : aux images entières de 2026 (clés exactes), la pose évaluée (matrix_world) égale
    motion_api.pose(pièce, state_from_jours(tour, jours)) à --kepler-tol-mm / --kepler-tol-rad près (images clés et
    matrix_world sont en float32) ; roue menée : θ = follow_ratio · θ_menante + follow_offset ;
(3) interférences sur l'espace d'état : au moins --kepler-states états (L, LT) sur une grille régulière de [0, 2π)²
    construits à la main (état de state_from_jours(tour, j0) dont L et LT sont remplacés ; L décalé d'une fraction
    du tour propre à chaque tour pour décorréler les tours ; L = LT gardé pour une tour dont L vaut LT), plus
    --kepler-traj instants de la vraie trajectoire 2026. À chaque état, chaque pièce Kepler mobile est posée
    directement (matrice monde T(x, y, z milieu)·Rz(θ) en double, sans les images clés) et l'on cherche par BVH les
    recouvrements entre pièces Kepler non liées (links/meshes_with, dans un sens ou l'autre) dont les z se
    recouvrent, et entre une pièce Kepler et une autre pièce de la scène non liée (axes, tubes, roues de prise,
    tringles…, à leur pose de la première image) dont les z se recouvrent. Une pièce noyée dans un solide fermé
    compte aussi (parité de rayons) ; un contact avec un bloc translucide est signalé seulement.
"""
import math
import time

import numpy as np

import check_lib as CL

GOLD = (math.sqrt(5.0) - 1.0) / 2.0
TWO_PI = 2.0 * math.pi
ZEPS = 1e-6              # mm : des z qui se touchent seulement ne se recouvrent pas
READ_DAYS = (0, 1, 57, 183, 300, 365)


def is_kepler(o):
    return bool(int(o.get('kepler', 0) or 0))


def pose_matrix(x, y, z, th):
    c, s = math.cos(th), math.sin(th)
    return np.array([[c, -s, 0.0, x], [s, c, 0.0, y], [0.0, 0.0, 1.0, z], [0.0, 0.0, 0.0, 1.0]])


def grid_states(api, towers, j0, n):
    """[(étiquette, {tour: état})] : grille nL × nLT ≥ n de [0, 2π)², états construits à la main."""
    nl = int(math.ceil(math.sqrt(n)))
    nt = int(math.ceil(n / nl))
    base = {t: dict(api.state_from_jours(t, j0)) for t in towers}
    out = []
    for i in range(nl):
        for k in range(nt):
            L, LT = TWO_PI * i / nl, TWO_PI * k / nt
            st = {}
            for ti, t in enumerate(towers):
                s = dict(base[t])
                same = abs(CL.wrap(float(s.get('L', 0.0)) - float(s.get('LT', 0.0)))) < 1e-12
                s['LT'] = LT
                s['L'] = LT if same else (L + TWO_PI * ((ti * GOLD) % 1.0)) % TWO_PI
                st[t] = s
            out.append(({'kind': 'grille', 'L': round(L, 6), 'LT': round(LT, 6)}, st))
    return out, [nl, nt]


def traj_states(api, towers, j0, span, n):
    js = [j0 + span * (q + 0.5) / n for q in range(n)]
    return [({'kind': 'trajectoire', 'jours': round(j, 4)}, {t: api.state_from_jours(t, j) for t in towers})
            for j in js]


def readback(kobs, ctx, clock, tol_mm, tol_rad):
    """Pose évaluée (images clés) contre motion_api aux images entières READ_DAYS."""
    api, kp = ctx['api'], ctx['parts']
    worst = {'err_mm': 0.0, 'err_rad': 0.0}
    days = [d for d in READ_DAYS if d <= clock.span]
    for d in days:
        dg = clock.set(clock.j0 + d)
        j = clock.now
        for o in kobs:
            lead = o.get('kepler_follow')
            part = kp.get(str(lead if lead is not None else o.get('part_id')))
            if part is None or str(o.get('motion')) != 'kepler':
                continue
            M = CL.world_matrix(o, dg)
            th = math.atan2(M[1, 0], M[0, 0])
            xe, ye, te = api.pose(part, api.state_from_jours(part['tower'], j))
            if lead is not None:
                te, xe, ye = float(o['follow_ratio']) * te + float(o['follow_offset']), M[0, 3], M[1, 3]
            e_mm, e_rad = math.hypot(M[0, 3] - xe, M[1, 3] - ye), abs(CL.wrap(th - te))
            if e_mm > worst['err_mm']:
                worst.update(err_mm=e_mm, object_mm=o.name, jours_mm=j)
            if e_rad > worst['err_rad']:
                worst.update(err_rad=e_rad, object_rad=o.name, jours_rad=j)
    worst.update(days=days, objects=sum(1 for o in kobs if str(o.get('motion')) == 'kepler'),
                 tol_mm=tol_mm, tol_rad=tol_rad)
    worst['ok'] = worst['err_mm'] <= tol_mm and worst['err_rad'] <= tol_rad
    return worst


def check_kepler(parts, clock, opts):
    """Section « kepler » du rapport de check.py (voir le docstring du module). Un contrôle impossible (spec ou API
    introuvable, exception) est un échec, jamais un succès par défaut."""
    t0 = time.time()
    try:
        return _check(parts, clock, opts, t0)
    except Exception as e:  # noqa: BLE001
        import traceback
        return {'parts': sum(1 for o in parts.obs if is_kepler(o)), 'states': {'total': 0},
                'pairs': {'kepler_kepler': 0, 'kepler_scene': 0}, 'bvh_tests': 0, 'collisions_count': 0,
                'collisions': [], 'failures': ['contrôle Kepler impossible : %r' % e], 'ok': False,
                'traceback': traceback.format_exc(), 'seconds': round(time.time() - t0, 3)}


def _check(parts, clock, opts, t0):
    import kepler_build as KB
    fails = []
    ctx = KB.context_from_scene()
    api, kp = ctx['api'], ctx['parts']
    kobs = [o for o in parts.obs if is_kepler(o) and len(parts.local[o.name][1])]
    kall = [o for o in parts.obs if is_kepler(o) or o.get('kepler_follow') is not None]
    sec = {'spec': ctx['spec_path'], 'tools': ctx['tools_path'], 'parts': len(kobs)}
    missing = [o.name for o in kobs if str(o.get('part_id')) not in kp]
    if missing:
        fails.append('pièces Kepler absentes de la spec : %s' % ', '.join(missing[:5]))
    kobs = [o for o in kobs if o.name not in missing]
    bad = [dict(parts.mesh_rep[o.name], name=o.name) for o in kobs if not parts.mesh_rep[o.name]['ok']]
    sec['meshes'] = {'checked': len(kobs), 'failed': bad}
    if bad:
        fails.append('maillages Kepler invalides : %s' % ', '.join(b['name'] for b in bad[:5]))
    sec['readback'] = readback(kall, ctx, clock, opts.kepler_tol_mm, opts.kepler_tol_rad)
    if not sec['readback']['ok']:
        fails.append('relecture Kepler : %.3g mm, %.3g rad' % (sec['readback']['err_mm'], sec['readback']['err_rad']))
    towers = sorted({str(kp[o['part_id']]['tower']) for o in kobs})
    grid, shape = grid_states(api, towers, clock.j0, opts.kepler_states)
    states = grid + traj_states(api, towers, clock.j0, clock.span, opts.kepler_traj)
    sec['states'] = {'grid': len(grid), 'grid_shape': shape, 'trajectory': opts.kepler_traj, 'total': len(states)}
    sec.update(interference(parts, clock, kobs, kp, api, states))
    if sec['collisions_count']:
        fails.append('recouvrements Kepler sur l\'espace d\'état : %d paires (%s)' % (
            sec['collisions_count'], ', '.join('%s/%s' % (c['a'], c['b']) for c in sec['collisions'][:5])))
    sec['failures'], sec['ok'] = fails, not fails
    sec['seconds'] = round(time.time() - t0, 3)
    return sec


def _boxes(alo, ahi, blo, bhi, pad=1e-6):
    """(na, nb) : boîtes alignées qui se coupent."""
    out = np.ones((len(alo), len(blo)), bool)
    for k in range(3):
        out &= (alo[:, None, k] <= bhi[None, :, k] + pad) & (ahi[:, None, k] >= blo[None, :, k] - pad)
    return out


def _closed(rep):
    return rep['non_manifold'] == 0 and rep['boundary'] == 0 and rep['wire'] == 0 and rep['volume'] > 0


def interference(parts, clock, kobs, kp, api, states):
    """Recouvrements BVH Kepler/Kepler et Kepler/scène sur les états donnés (voir le docstring du module)."""
    dg = clock.set(clock.j0)
    others = [o for o in parts.obs if not is_kepler(o) and len(parts.local[o.name][1])]
    S = [parts.world(o.name, dg)[0] for o in others]
    sb = [CL.aabb(W) for W in S]
    slo, shi = np.array([b[0] for b in sb]).reshape(-1, 3), np.array([b[1] for b in sb]).reshape(-1, 3)
    K = []
    for o in kobs:
        part = kp[str(o['part_id'])]
        z0, z1 = (float(v) for v in part['z'])
        moving = str(o.get('motion')) == 'kepler'
        K.append((o, part, z0, z1, moving, None if moving else CL.world_matrix(o, dg)))
    kz = np.array([[k[2], k[3]] for k in K], float).reshape(-1, 2)
    sz = np.column_stack([slo[:, 2], shi[:, 2]])

    def zover(a, b):
        return (a[:, None, 0] < b[None, :, 1] - ZEPS) & (b[:, 0][None, :] < a[:, None, 1] - ZEPS)

    def linked(a, b):
        return b in parts.declared.get(a, ()) or a in parts.declared.get(b, ())
    mkk = np.triu(zover(kz, kz), 1)
    for i, j in zip(*np.nonzero(mkk)):
        mkk[i, j] = not linked(K[i][0].name, K[j][0].name)
    mks = zover(kz, sz)
    for i, j in zip(*np.nonzero(mks)):
        mks[i, j] = not linked(K[i][0].name, others[j].name)
    s_trees, hits, tests = {}, {}, 0

    def s_tree(j):
        if j not in s_trees:
            s_trees[j] = CL.bvh(S[j], parts.tlist[others[j].name])
        return s_trees[j]

    def test(a, Wa, ta, la, ha, b, Wb, tb, lb, hb, label):
        cnt, pt = CL.overlap_info(ta, tb, Wa, parts.local[a.name][1])
        typ = 'surface' if cnt else None
        if not cnt:
            for x, Wx, y, ty, inside in ((a, Wa, b, tb, CL.aabb_inside(la, ha, lb, hb)),
                                         (b, Wb, a, ta, CL.aabb_inside(lb, hb, la, ha))):
                if inside and _closed(parts.mesh_rep[y.name]) and CL.point_inside(ty, Wx[0]):
                    typ, pt = 'contenue : %s' % x.name, [round(float(v), 4) for v in Wx[0]]
                    break
        if typ is None:
            return
        h = hits.setdefault((a.name, b.name), {'a': a.name, 'b': b.name, 'kinds': [str(a.get('kind')),
                            str(b.get('kind'))], 'type': typ, 'states': 0, 'first_state': label,
                            'tri_pairs': 0, 'point': pt})
        h['states'] += 1
        h['tri_pairs'] = max(h['tri_pairs'], cnt)

    for label, st in states:
        W = []
        for o, part, z0, z1, moving, Mfix in K:
            if moving:
                x, y, th = api.pose(part, st[str(part['tower'])])
                M = pose_matrix(x, y, 0.5 * (z0 + z1), th)
            else:
                M = Mfix
            W.append(CL.to_world(parts.local[o.name][0], M))
        bb = [CL.aabb(w) for w in W]
        klo, khi = np.array([b[0] for b in bb]).reshape(-1, 3), np.array([b[1] for b in bb]).reshape(-1, 3)
        k_trees = {}

        def k_tree(i):
            if i not in k_trees:
                k_trees[i] = CL.bvh(W[i], parts.tlist[K[i][0].name])
            return k_trees[i]
        for i, j in zip(*np.nonzero(mkk & _boxes(klo, khi, klo, khi))):
            tests += 1
            test(K[i][0], W[i], k_tree(i), klo[i], khi[i], K[j][0], W[j], k_tree(j), klo[j], khi[j], label)
        for i, j in zip(*np.nonzero(mks & _boxes(klo, khi, slo, shi))):
            tests += 1
            test(K[i][0], W[i], k_tree(i), klo[i], khi[i], others[j], S[j], s_tree(j), slo[j], shi[j], label)
    rows = sorted(hits.values(), key=lambda h: (-h['states'], -h['tri_pairs']))
    col = [h for h in rows if 'block' not in h['kinds']]
    blk = [h for h in rows if 'block' in h['kinds']]
    return {'pairs': {'kepler_kepler': int(mkk.sum()), 'kepler_scene': int(mks.sum())}, 'bvh_tests': tests,
            'collisions_count': len(col), 'collisions': col[:100],
            'block_contacts_count': len(blk), 'block_contacts': blk[:50]}
