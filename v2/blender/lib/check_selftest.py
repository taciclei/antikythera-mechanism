"""Scène synthétique pour `check.py --selftest`.

Contenu (1 unité = 1 mm, contrôleur `V2_Controleur` animé de 1 jour par image comme dans le contrat) :
  roue_A (20 dents) ~ roue_B (30 dents) : couple propre, entraxe 25, phases calées (dent dans un creux) ;
  roue_C ~ roue_D : même couple mais entraxe 22,5 (collision volontaire, attrapée par le contrôle 2) ;
  roue_E ~ roue_F : entraxe juste mais roue_F décalée d'un demi-pas (dent sur dent, attrapée par le contrôle 2) ;
  arbre_A : arbre traversant roue_A, déclaré dans les `links` de roue_A par son `part_id` « arbre#A » (convention
    de parts.py, doit être résolu puis ignoré) ;
  tige_intruse : tringle traversant roue_B sans déclaration (attrapée par le contrôle 3) ;
  platine + cale_noyee : cube entièrement noyé dans la platine (attrapé par le test de parité) ;
  bloc : enveloppe translucide qui coupe roue_B (signalée seulement) ;
  platine_ouverte : un simple quadrilatère de type plate (attrapé par le contrôle 1) ;
  platine_degeneree : prisme fermé dont un triangle de face a ses trois sommets alignés (coordonnées ~ 40 mm : en
    float32 son aire résiduelle dépasse ZERO_AREA, seule l'épaisseur le révèle ; attrapé par le contrôle 1).
roue_A est masquée (hide_viewport) et roue_B rangée dans une collection exclue : check.py doit les rendre évaluables.
roue_A tourne par un pivot (Empty « V2_Pivot_roue_A » piloté, convention d'animate.py) : sa relecture doit rester
active. Les pilotes sont ceux d'animate.py (fmod) et les roues rapides (3 tours/jour) : la relecture n'est juste à
1e-3 rad près que si check.py pose des instants exacts en float32.
Les dents sont trapézoïdales (pas de développante) et assez fines pour engrener sans contact à l'entraxe juste.
"""
import math

import bpy
import numpy as np

J_START = 9496.5          # 2026-01-01 00:00 UTC, en jours depuis J2000.0 (sans ΔT, valeur de démonstration)
TAU = 2.0 * math.pi


def toothed_outline(z, m):
    """Contour CCW d'une roue de z dents, module m : creux à r − 1,25 m, sommet à r + m, dent centrée sur 0."""
    r = z * m / 2.0
    rr, ra, p = r - 1.25 * m, r + m, TAU / z
    pts = []
    for k in range(z):
        c = k * p
        for f, rad in ((-0.22, rr), (-0.10, ra), (0.10, ra), (0.22, rr), (0.5, rr)):
            a = c + f * p
            pts.append((rad * math.cos(a), rad * math.sin(a)))
    return pts


def circle(r, n=32):
    return [(r * math.cos(TAU * i / n), r * math.sin(TAU * i / n)) for i in range(n)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def prism_mesh(name, outline, z0, z1):
    """Prisme fermé : contour CCW extrudé de z0 à z1 (faces n-gones aux deux bouts)."""
    n = len(outline)
    V = [(x, y, z0) for x, y in outline] + [(x, y, z1) for x, y in outline]
    F = [tuple(range(n, 2 * n)), tuple(reversed(range(n)))]
    F += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.update(calc_edges=True)
    me.validate()
    return me


def add(name, me, kind, loc=(0.0, 0.0, 0.0), **props):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob['kind'] = kind
    ob['source'] = 'selftest:' + name
    ob['motion'] = props.pop('motion', 'fixed')
    ob['axis'] = [0.0, 0.0, 1.0]
    for k, v in props.items():
        ob[k] = v
    return ob


def expression(ob):
    """Expression du pilote, comme animate.py : fmod(−2π·phys·|rate|·j + phase, 2π)."""
    return 'fmod(%.17g*j+(%.17g),2*pi)' % (-TAU * ob['phys'] * abs(ob['rate']), ob['phase'])


def drive(ob, ctl, target=None):
    """Pilote `linear` : angle = −2π·phys·|rate|·jours + phase autour de +Z (convention du contrat), posé sur l'objet
    ou sur son pivot `target`."""
    fc = (target or ob).driver_add('rotation_euler', 2)
    d = fc.driver
    d.type = 'SCRIPTED'
    v = d.variables.new()
    v.name, v.type = 'j', 'SINGLE_PROP'
    v.targets[0].id = ctl
    v.targets[0].data_path = '["jours"]'
    d.expression = expression(ob)


def gear(name, ctl, z, m, loc, rate, phys, phase, partner, links=(), pivot=False):
    ob = add(name, prism_mesh(name, toothed_outline(z, m), 0.0, 5.0), 'gear', loc, motion='linear',
             rate=rate, phys=phys, phase=phase, teeth=z, m=m, meshes_with=[partner], links=list(links))
    piv = None
    if pivot:                                   # pivot piloté, parent de la roue (animate.py, _ensure_pivot)
        piv = bpy.data.objects.new('V2_Pivot_' + name, None)
        bpy.context.scene.collection.objects.link(piv)
        piv.location = loc
        piv['v2_pivot_of'] = name
        piv['axis'] = [0.0, 0.0, 1.0]
        ob.parent = piv
        ob.location = (0.0, 0.0, 0.0)
    drive(ob, ctl, piv)
    return ob


def collinear_plate(name):
    """Prisme fermé de faces triangulaires dont le premier triangle de chaque face a trois sommets alignés."""
    pts = [(40.1, 0.3), (40.4, 0.6), (40.7, 0.9), (40.7, 3.0), (40.1, 3.0)]
    n = len(pts)
    V = [(x, y, 0.0) for x, y in pts] + [(x, y, 2.0) for x, y in pts]
    F = [(n, n + k, n + k + 1) for k in range(1, n - 1)] + [(k + 1, k, 0) for k in range(1, n - 1)]
    F += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.update(calc_edges=True)
    return me


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    us = sc.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'MILLIMETERS', 0.001
    sc.frame_start, sc.frame_end = 1, 366
    ctl = bpy.data.objects.new('V2_Controleur', None)
    sc.collection.objects.link(ctl)
    for f, j in ((1, J_START), (367, J_START + 366.0)):
        ctl['jours'] = j
        ctl.keyframe_insert('["jours"]', frame=f)
    from bpy_extras import anim_utils
    ad = ctl.animation_data
    for fc in anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves:
        fc.extrapolation = 'LINEAR'
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    za, zb, m = 20, 30, 1.0
    ra, rb = 3.0, 3.0 * za / zb                      # tours/jour ; vitesses primitives égales
    ph_b = math.pi - math.pi / zb                     # un creux de B face à la dent de A à jours = 0
    gear('roue_A', ctl, za, m, (0.0, 0.0, 0.0), ra, 1, 0.0, 'roue_B', links=['arbre#A'], pivot=True)
    gear('roue_B', ctl, zb, m, (25.0, 0.0, 0.0), rb, -1, ph_b, 'roue_A')
    gear('roue_C', ctl, za, m, (0.0, 60.0, 0.0), ra, 1, 0.0, 'roue_D')
    gear('roue_D', ctl, zb, m, (22.5, 60.0, 0.0), rb, -1, ph_b, 'roue_C')
    gear('roue_E', ctl, za, m, (0.0, -60.0, 0.0), ra, 1, 0.0, 'roue_F')
    gear('roue_F', ctl, zb, m, (25.0, -60.0, 0.0), rb, -1, ph_b + math.pi / zb, 'roue_E')
    bpy.data.objects['roue_A'].hide_viewport = True          # pièces masquées : check.py doit les évaluer
    hid = bpy.data.collections.new('V2_Masquee')
    sc.collection.children.link(hid)
    sc.collection.objects.unlink(bpy.data.objects['roue_B'])
    hid.objects.link(bpy.data.objects['roue_B'])
    bpy.context.view_layer.layer_collection.children['V2_Masquee'].exclude = True
    add('arbre_A', prism_mesh('arbre_A', circle(2.0), -4.0, 9.0), 'arbor', part_id='arbre#A')
    add('tige_intruse', prism_mesh('tige_intruse', circle(1.5), -3.0, 8.0), 'rod', (25.0, 8.0, 0.0))
    add('platine', prism_mesh('platine', rect(-20, -20, 50, 80), -10.0, -8.0), 'plate')
    add('cale_noyee', prism_mesh('cale_noyee', rect(-1, -1, 1, 1), -9.5, -8.5), 'misc', (0.0, 30.0, 0.0))
    add('bloc', prism_mesh('bloc', rect(30, -5, 45, 5), 2.0, 12.0), 'block', label='à dessiner')
    me = bpy.data.meshes.new('platine_ouverte')
    me.from_pydata([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)], [], [(0, 1, 2, 3)])
    add('platine_ouverte', me, 'plate', (100.0, 100.0, 0.0))
    add('platine_degeneree', collinear_plate('platine_degeneree'), 'plate', (150.0, -150.0, 0.0))
    sc.frame_set(1)


def clean():
    """Corrige les défauts volontaires : la scène doit alors passer tous les contrôles."""
    for n in ('tige_intruse', 'cale_noyee', 'platine_ouverte', 'platine_degeneree'):
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    bpy.data.objects['roue_D'].location.x = 25.0
    f = bpy.data.objects['roue_F']
    f['phase'] = f['phase'] - math.pi / f['teeth']
    f.animation_data.drivers[0].driver.expression = expression(f)


def _pair(rep, a, b):
    return next((r for r in rep['pairs']['rows'] if {r['a'], r['b']} == {a, b}), None)


def _static(rep, a, b, key='collisions', typ=None):
    return any({c['a'], c['b']} == {a, b} and (typ is None or c['type'] == typ) for c in rep['static'][key])


def expectations(dirty, clean_rep, empty_rep):
    ab, cd = _pair(dirty, 'roue_A', 'roue_B'), _pair(dirty, 'roue_C', 'roue_D')
    cd2 = _pair(clean_rep, 'roue_C', 'roue_D')
    ef, ef2 = _pair(dirty, 'roue_E', 'roue_F'), _pair(clean_rep, 'roue_E', 'roue_F')
    meta = dirty['meta']
    failed = {x['name']: x for x in dirty['meshes']['failed']}
    deg = failed.get('platine_degeneree', {})
    rb = dirty['pairs']['readback']
    return [
        ('horloge : jours = %.1f à la première image, 1 jour par image' % J_START,
         abs(meta['jours_start'] - J_START) < 1e-9 and abs(meta['days_per_frame'] - 1.0) < 1e-9),
        ('(1) seules platine_degeneree et platine_ouverte sont des maillages invalides',
         sorted(failed) == ['platine_degeneree', 'platine_ouverte']),
        ('(1) platine_degeneree : fermée et variété, refusée pour son triangle aux sommets alignés',
         deg.get('thin_faces', 0) + deg.get('zero_area_faces', 0) == 2 and deg.get('non_manifold', 1) == 0
         and deg.get('boundary', 1) == 0 and deg.get('volume', 0.0) > 0),
        ('(2) roue_A~roue_B : aucun recouvrement', ab is not None and ab['overlapping_samples'] == 0),
        ('(2) roue_A~roue_B : jeu positif mesuré', ab is not None and (ab['min_gap_mm'] or 0) > 0),
        ('(2) roue_C~roue_D (entraxe 22,5) : recouvrement détecté', cd is not None and cd['overlapping_samples'] > 0),
        ('(2) roue_E~roue_F (demi-pas de déphasage) : recouvrement détecté',
         ef is not None and ef['overlapping_samples'] > 0),
        ('(2) relecture des rotations juste (6 roues, dont roue_A par son pivot), aucune pièce figée',
         rb['ok'] and not dirty['pairs']['frozen'] and rb['objects'] == 6),
        ('(2) relecture à 1e-3 rad près à 3 tours/jour (instants exacts en float32)', rb['err_rad'] < 1e-3),
        ('(2) aucun nom non résolu (links « arbre#A » trouvé par part_id)', not dirty['pairs']['unresolved_names']),
        ('(3) tige_intruse/roue_B détectée', _static(dirty, 'roue_B', 'tige_intruse', typ='surface')),
        ('(3) cale_noyee noyée dans platine détectée', _static(dirty, 'cale_noyee', 'platine', typ='contained')),
        ('(3) arbre_A/roue_A (links) ignoré', not _static(dirty, 'arbre_A', 'roue_A')),
        ('(3) roue_C/roue_D (meshes_with) ignoré en statique', not _static(dirty, 'roue_C', 'roue_D')),
        ('(3) bloc/roue_B signalé seulement', _static(dirty, 'bloc', 'roue_B', key='block_contacts')
         and not _static(dirty, 'bloc', 'roue_B')),
        ('scène fautive : contrôle en échec', not dirty['summary']['ok'] and len(dirty['summary']['failures']) == 3),
        ('scène corrigée : roue_C~roue_D sans recouvrement', cd2 is not None and cd2['overlapping_samples'] == 0),
        ('scène corrigée : roue_E~roue_F sans recouvrement', ef2 is not None and ef2['overlapping_samples'] == 0),
        ('scène corrigée : contrôle réussi', clean_rep['summary']['ok']),
        ('scène vide : contrôle en échec (rien à contrôler)', not empty_rep['summary']['ok']
         and any('aucune pièce' in f for f in empty_rep['summary']['failures'])),
    ]


def run(opts, run_checks):
    build()
    dirty = run_checks(opts)
    clean()
    clean_rep = run_checks(opts)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    empty_rep = run_checks(opts)
    exp = expectations(dirty, clean_rep, empty_rep)
    for label, ok in exp:
        print('[v2-check] selftest %s %s' % ('ok   ' if ok else 'ÉCHEC', label), flush=True)
    return {'selftest': True, 'ok': all(v for _, v in exp),
            'expectations': [{'label': lab, 'ok': bool(v)} for lab, v in exp],
            'failures': [lab for lab, v in exp if not v], 'dirty': dirty, 'clean': clean_rep, 'empty': empty_rep}
