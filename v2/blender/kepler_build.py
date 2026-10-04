"""Anticythère 2.0 — tours de Kepler dans la maquette (phase K2) : v2/spec/kepler.json → objets Blender.

INACTIF tant que la spec n'existe pas : build_v2.py, animate.py et check.py font alors exactement ce qu'ils faisaient
(aucun objet, aucune clé de rapport en plus). Contrat de la spec : v2/tools/kepler/CONTRACT.md (§ 3 angles, § 4 API,
§ 5 pièces) ; conventions Blender : CONTRACT.md § 8.

Chemins, dans cet ordre : arguments après « -- » (--kepler-spec F, --kepler-tools D), variables d'environnement
V2_KEPLER_SPEC et V2_KEPLER_TOOLS, chemins enregistrés dans la scène par build_v2 (animate, check), sinon
v2/spec/kepler.json et v2/tools/kepler. Une spec donnée explicitement mais absente est une erreur.
API : motion.pose(part, state) → (x, y, θ) (repère machine, mm, θ trigonométrique autour de +z, pièce au pivot) ;
state_from_jours(tour, jours) → {"L", "LT"} (de motion.py s'il l'expose, sinon de frame.py). Le dossier est importé
par sys.path (paquet `<dossier>.motion` s'il a un __init__.py, sinon modules `motion` et `frame`).

- prepare_scene : retire de scene.json les blocs remplacés (uak_<p>, mod_<p> ; terre_maitre pour la tour de la Terre ;
  ou la liste towers.<p>.replaces ; plus les overrides {"remove": true}), ôte leurs noms des links/meshes_with/engages
  et applique les overrides (champs c, z, p, q, r, r_in, width, axis, phase ; une pièce `synth` coaxiale à sa
  `source` déplacée suit le nouveau centre) ;
- build_kepler : un objet par pièce dans V2_Kepler/V2_Kepler_<tour>, enfant d'un Empty fixe « V2_K_<tour> » posé à
  l'origine de la tour (positions clés petites, donc précises en float32) ; origine au pivot, z au milieu de [z0, z1] ;
  pose de repos = pose au 2026-01-01 ; matériau selon `kind` ;
- roue de la scène engrenée par une roue Kepler à pivot fixe : menée (motion « kepler », kepler_follow = id de la
  menante, θ = follow_ratio · θ_menante + follow_offset ; phase : une dent dans un creux sur la ligne des centres).
"""
import copy
import importlib
import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kepler_geom as KG  # noqa: E402
import parts as P  # noqa: E402

DEFAULT_SPEC = os.path.join(V2, 'spec', 'kepler.json')
DEFAULT_TOOLS = os.path.join(V2, 'tools', 'kepler')
COLL, ROOT_PREFIX, START = 'V2_Kepler', 'V2_K_', (2026, 1, 1)
EARTH = ('earth', 'terre', 'terre_maitre', 'earth_master')
OVERRIDE_KEYS = ('c', 'z', 'p', 'q', 'r', 'r_in', 'width', 'axis', 'phase')
KIND_MATERIAL = {'gear': 'brass', 'slotted_arm': 'brass', 'crank': 'brass', 'arm': 'brass', 'rack': 'brass',
                 'tube': 'brass', 'pin': 'steel', 'arbor': 'steel', 'slider': 'steel', 'follower': 'steel',
                 'oldham_disc': 'bronze', 'bush': 'bronze', 'plate_bush': 'bronze'}
TWO_PI = 2.0 * math.pi


# ------------------------------------------------------------------ chemins, spec, API
def paths(argv=None):
    """{'spec', 'tools'} : chemins explicites (arguments après « -- », puis environnement) ou None."""
    argv = sys.argv if argv is None else argv
    a = argv[argv.index('--') + 1:] if '--' in argv else []

    def arg(flag, env):
        v = a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else os.environ.get(env)
        return os.path.abspath(v) if v else None
    return {'spec': arg('--kepler-spec', 'V2_KEPLER_SPEC'), 'tools': arg('--kepler-tools', 'V2_KEPLER_TOOLS')}


class MotionAPI:
    """Façade de v2/tools/kepler : pose(part, state) → (x, y, θ) en flottants, state_from_jours(tour, jours)."""

    def __init__(self, motion, frame=None, tools=None):
        self.motion, self.frame, self.tools = motion, frame, tools
        self._state = getattr(motion, 'state_from_jours', None) or getattr(frame, 'state_from_jours', None)
        if self._state is None:
            raise ImportError('state_from_jours introuvable dans motion.py et frame.py (%s)' % tools)

    def pose(self, part, state):
        x, y, th = tuple(self.motion.pose(part, state))[:3]
        return float(x), float(y), float(th)

    def state_from_jours(self, tower, jours):
        return self._state(tower, float(jours))


def load_api(tools):
    """Importe motion.py et frame.py du dossier `tools` (sys.path) ; oublie d'éventuels homonymes d'un autre dossier."""
    tools = os.path.abspath(tools)
    if not os.path.isdir(tools):
        raise FileNotFoundError('dossier de l\'API Kepler absent : %s' % tools)
    pkg = os.path.basename(tools) if os.path.isfile(os.path.join(tools, '__init__.py')) else None
    base = os.path.dirname(tools) if pkg else tools
    if base in sys.path:
        sys.path.remove(base)
    sys.path.insert(0, base)
    for n in list(sys.modules):
        f = os.path.abspath(getattr(sys.modules[n], '__file__', None) or os.sep)
        if (n in ('motion', 'frame') or (pkg and n.split('.')[0] == pkg)) and not f.startswith(tools + os.sep):
            del sys.modules[n]
    names = ['%s.motion' % pkg, '%s.frame' % pkg] if pkg else ['motion', 'frame']
    motion = importlib.import_module(names[0])
    try:
        frame = importlib.import_module(names[1])
    except ImportError:
        frame = None
    return MotionAPI(motion, frame, tools)


def load_spec(path):
    with open(path) as f:
        spec = json.load(f)
    if not isinstance(spec.get('towers'), dict):
        raise ValueError('%s : clé « towers » absente' % path)
    return spec


def kepler_parts(spec):
    """Pièces de toutes les tours (copies superficielles, « tower » rempli), dans l'ordre de la spec."""
    out = []
    for t, tw in spec['towers'].items():
        for p in tw.get('parts', []) or []:
            q = dict(p)
            q.setdefault('tower', t)
            out.append(q)
    return out


def context(spec_path, tools_path):
    """Contexte Kepler : spec, API, index id → pièce, chemins."""
    spec = load_spec(spec_path)
    return {'spec_path': os.path.abspath(spec_path), 'tools_path': os.path.abspath(tools_path), 'spec': spec,
            'api': load_api(tools_path), 'parts': {p['id']: p for p in kepler_parts(spec)}}


def activate(argv=None):
    """Contexte si la spec existe (chemin explicite ou v2/spec/kepler.json), None sinon (chaîne inchangée)."""
    x = paths(argv)
    spec = x['spec'] or DEFAULT_SPEC
    if not os.path.isfile(spec):
        if x['spec']:
            raise FileNotFoundError('spec Kepler absente : %s' % spec)
        return None
    return context(spec, x['tools'] or DEFAULT_TOOLS)


def remember(scene, ctx):
    """Enregistre les chemins dans la scène (relus par animate.py et check.py)."""
    scene['v2_kepler_spec'], scene['v2_kepler_tools'] = ctx['spec_path'], ctx['tools_path']


def context_from_scene(scene=None, argv=None):
    """Contexte pour animate.py et check.py : chemins explicites, sinon ceux de la scène, sinon par défaut."""
    sc = scene or bpy.context.scene
    x = paths(argv)
    spec = x['spec'] or sc.get('v2_kepler_spec') or DEFAULT_SPEC
    return context(spec, x['tools'] or sc.get('v2_kepler_tools') or DEFAULT_TOOLS)


# ------------------------------------------------------------------ scène : blocs remplacés, overrides
def overrides_of(tw):
    """{id: champs} depuis towers.<p>.overrides (liste de {"id"|"item": ...} ou dictionnaire id → champs)."""
    ov = tw.get('overrides') or {}
    items = ov.items() if isinstance(ov, dict) else [(o.get('id', o.get('item')), o) for o in ov]
    return {str(k): dict(v) for k, v in items if k is not None and isinstance(v, dict)}


def replaced_ids(spec):
    """Ids de scene.json que les tours remplacent (blocs et pièces retirées)."""
    out = set()
    for t, tw in spec['towers'].items():
        if tw.get('replaces') is not None:
            out.update(str(x) for x in tw['replaces'])
        elif str(t).lower() in EARTH:
            out.add('terre_maitre')
        else:
            out.update(('uak_%s' % t, 'mod_%s' % t))
        out.update(k for k, v in overrides_of(tw).items() if v.get('remove') or v.get('replaced_by'))
    return out


def prepare_scene(scene_parts, spec):
    """(pièces de scène à construire, rapport) : blocs remplacés retirés, noms retirés des liens, overrides appliqués."""
    drop = replaced_ids(spec)
    ovs = {}
    for tw in spec['towers'].values():
        ovs.update({k: v for k, v in overrides_of(tw).items() if not (v.get('remove') or v.get('replaced_by'))})
    by_id = {p['id']: p for p in scene_parts}
    out, applied = [], []
    for p in scene_parts:
        if p['id'] in drop:
            continue
        q = copy.deepcopy(p)
        for key in ('links', 'meshes_with', 'engages'):
            if q.get(key):
                q[key] = [x for x in q[key] if x not in drop]
        ov, src = ovs.get(q['id']), ovs.get(str(q.get('source')))
        if ov is not None:
            q.update({k: copy.deepcopy(ov[k]) for k in OVERRIDE_KEYS if k in ov})
            applied.append(q['id'])
        elif q.get('synth') and src is not None and 'c' in src and q.get('c') is not None:
            old = by_id.get(q['source'], {}).get('c')
            if old is not None and math.dist(old[:2], q['c'][:2]) < 1e-6:
                q['c'] = [float(src['c'][0]), float(src['c'][1])]
                applied.append('%s (suit %s)' % (q['id'], q['source']))
        out.append(q)
    return out, {'replaced': sorted(drop & set(by_id)), 'replaced_absent': sorted(drop - set(by_id)),
                 'overrides_applied': applied, 'overrides_unknown': sorted(set(ovs) - set(by_id))}


# ------------------------------------------------------------------ construction
def pivot(part):
    m = part.get('motion') or {}
    pv = m.get('pivot') or [0.0, 0.0]
    return float(pv[0]), float(pv[1])


def law(part):
    return str((part.get('motion') or {}).get('law', 'fixed'))


def tower_origin(spec, tower, index=None):
    """Origine de la tour : towers.<p>.origin|center|c, sinon le centre de axe_<p> (scene.json), sinon (0, 0)."""
    tw = spec['towers'].get(tower, {})
    for k in ('origin', 'center', 'c'):
        v = tw.get(k)
        if isinstance(v, (list, tuple)) and len(v) >= 2 and all(isinstance(x, (int, float)) for x in v[:2]):
            return float(v[0]), float(v[1])
    a = (index or {}).get('axe_%s' % tower)
    return (float(a['c'][0]), float(a['c'][1])) if a and a.get('c') else (0.0, 0.0)


def rest_pose(part, api, j0):
    """Pose (x, y, θ) au 2026-01-01 ; pièce fixe dont la loi n'est pas connue de pose() : (pivot, 0)."""
    try:
        return api.pose(part, api.state_from_jours(part['tower'], j0))
    except Exception:  # noqa: BLE001
        if law(part) != 'fixed':
            raise
        return pivot(part) + (0.0,)


def gear_bore(part, kindex, sindex):
    """Alésage d'une roue : gear.bore, sinon trou rond centré de ses formes, sinon plus gros support coaxial lié
    (cercle centré d'une pièce Kepler de même pivot, ou pièce de scene.json de même centre) + 0,05 ; sinon None."""
    g = part.get('gear') or {}
    if g.get('bore') is not None:
        return float(g['bore'])
    r = KG.centered_hole_radius(part.get('shapes'))
    if r is not None:
        return r
    best, pv = None, pivot(part)
    for lid in part.get('links', []) or []:
        o, s = kindex.get(lid), (sindex or {}).get(lid)
        if o is not None and math.dist(pivot(o), pv) < 1e-6:
            rs = [float(sh['r']) for sh in o.get('shapes', []) if sh.get('type') == 'circle'
                  and math.hypot(*sh.get('c', [0.0, 0.0])) < 1e-6]
            best = max([best or 0.0] + rs)
        if s is not None and s.get('c') is not None and s.get('r') and math.dist(s['c'][:2], pv) < 1e-3:
            best = max(best or 0.0, float(s['r']))
    return best + P.BORE_CLEAR if best else None


def _root(tower, origin, coll):
    ob = bpy.data.objects.new(ROOT_PREFIX + tower, None)
    ob.empty_display_type, ob.empty_display_size = 'PLAIN_AXES', 6.0
    ob.location = (origin[0], origin[1], 0.0)
    ob['kepler_tower'], ob['kepler_origin'] = tower, [origin[0], origin[1]]
    coll.objects.link(ob)
    return ob


def build_one(part, coll, mats, api, j0, kindex, sindex, root):
    """Objet Blender d'une pièce Kepler (voir le docstring du module)."""
    z0, z1 = (float(v) for v in part['z'])
    name = P.obj_name(part['id'])
    if bpy.data.objects.get(name) is not None:
        raise ValueError('nom d\'objet déjà pris : %s' % name)
    g = part.get('gear') if part.get('kind') == 'gear' else None
    if g:
        me, info = KG.gear_mesh('K_' + name, g, z1 - z0, gear_bore(part, kindex, sindex))
    else:
        me, info = KG.shapes_mesh('K_' + name, part.get('shapes'), z1 - z0)
    ob = bpy.data.objects.new(name, me)
    x, y, th = rest_pose(part, api, j0)
    th = (th + math.pi) % TWO_PI - math.pi          # angle de repos ramené dans [−π, π) (float32)
    ox, oy = root['kepler_origin']
    ob.parent = root
    ob.location = (x - ox, y - oy, (z0 + z1) / 2.0)
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = (0.0, 0.0, th)
    mat = (mats or {}).get(part.get('material') or KIND_MATERIAL.get(part.get('kind'), 'steel'))
    if mat is not None:
        me.materials.append(mat)
    ob['part_id'], ob['kind'], ob['tower'], ob['kepler'] = str(part['id']), str(part.get('kind')), part['tower'], 1
    ob['law'], ob['pivot'], ob['z'] = law(part), list(pivot(part)), [z0, z1]
    ob['motion'] = 'fixed' if law(part) == 'fixed' else 'kepler'
    ob['links'] = [P.obj_name(i) for i in part.get('links', []) or []]
    ob['meshes_with'] = [P.obj_name(i) for i in (g or {}).get('mesh_with', []) or []]
    ob['axis'], ob['source'], ob['collection'] = [0.0, 0.0, 1.0], str(part['id']), coll.name
    for k in ('label', 'role'):
        if part.get(k) is not None:
            ob[k] = str(part[k])
    for k in ('teeth', 'm', 'r', 'ra', 'bore', 'n_windows', 'union'):
        if info.get(k) is not None:
            ob['r_pitch' if k == 'r' else k] = info[k]
    coll.objects.link(ob)
    return ob


def setup_followers(kparts, kindex, api, j0, sindex=None):
    """Roues de scene.json menées par une roue Kepler à pivot fixe (gear.mesh_with) : motion « kepler » dérivé."""
    out, warn = [], []
    for part in kparts:
        g = part.get('gear') or {}
        for mid in (g.get('mesh_with') or []) if part.get('kind') == 'gear' else []:
            ob = bpy.data.objects.get(P.obj_name(mid))
            if mid in kindex or ob is None or ob.get('kepler'):
                if ob is None and mid not in kindex:
                    warn.append('%s : partenaire %s introuvable' % (part['id'], mid))
                continue
            tw = part['tower']
            cs = [api.pose(part, api.state_from_jours(tw, j0 + d))[:2] for d in range(-36500, 36501, 3650)]
            drift = max(math.dist(c, cs[0]) for c in cs)
            if ob.get('kind') != 'gear' or 'internal' in (str(ob.get('mesh')), str(g.get('mesh'))) or drift > 1e-6:
                warn.append('%s ~ %s : engrènement non pris en charge (roue intérieure, ou pivot mobile de %.3g mm)'
                            % (part['id'], mid, drift))
                continue
            zg, zs, m = int(g['teeth']), int(ob['teeth']), float(g['m'])
            sc = (sindex or {}).get(mid, {}).get('c')
            sx, sy = (float(sc[0]), float(sc[1])) if sc is not None else tuple(ob.location[:2])
            gamma = math.atan2(sy - cs[0][1], sx - cs[0][0])
            k, ps = zg / zs, TWO_PI / zs
            off = (gamma + math.pi + k * gamma - ps / 2.0) % ps
            ob['motion'], ob['kepler_follow'] = 'kepler', str(part['id'])
            ob['follow_ratio'], ob['follow_offset'] = -k, off
            ob.rotation_euler[2] = (-k * rest_pose(part, api, j0)[2] + off + math.pi) % TWO_PI - math.pi
            out.append({'id': mid, 'leader': part['id'], 'ratio': -k, 'offset': off,
                        'center_distance_err_mm': abs(math.dist((sx, sy), cs[0]) - m * (zg + zs) / 2.0)})
    return out, warn


def build_kepler(spec, colls, mats, motion_api, scene_index=None, j0=None):
    """Objets des pièces Kepler (collections V2_Kepler/V2_Kepler_<tour>) et roues menées. Renvoie (objets, rapport)."""
    if j0 is None:
        import animate
        j0 = animate.jours_from_date(*START)
    top = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(top)
    colls[COLL] = top
    kp = kepler_parts(spec)
    kindex = {p['id']: p for p in kp}
    objs, fails, towers, roots = [], [], {}, {}
    for part in kp:
        t = str(part['tower'])
        if t not in roots:
            c = bpy.data.collections.new('%s_%s' % (COLL, t))
            top.children.link(c)
            colls[c.name] = c
            roots[t] = (_root(t, tower_origin(spec, t, scene_index), c), c)
        try:
            objs.append(build_one(part, roots[t][1], mats, motion_api, j0, kindex, scene_index, roots[t][0]))
            towers[t] = towers.get(t, 0) + 1
        except Exception as e:  # noqa: BLE001
            fails.append((str(part.get('id')), repr(e)))
    followers, warns = setup_followers(kp, kindex, motion_api, j0, scene_index)
    kinds = {}
    for o in objs:
        kinds[o['kind']] = kinds.get(o['kind'], 0) + 1
    return objs, {'parts': len(objs), 'towers': towers, 'kinds': kinds, 'failures': fails,
                  'unions': sum(1 for o in objs if o.get('union')), 'followers': followers, 'warnings': warns}
