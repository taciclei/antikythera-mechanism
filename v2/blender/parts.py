"""Anticythère 2.0 — constructeurs de pièces Blender (un objet par pièce de scene.json).

Contrat : v2/blender/CONTRACT.md. 1 unité = 1 mm ; X droite, Y haut, Z vers l'observateur (face avant).
- `materials()` : matériaux PBR de la v2 (laiton, bronze, acier, verre, chêne, bloc translucide, cadran, texte).
- `build_part(part, colls, mats, index=None)` : objet Blender d'une pièce de scene.json (tout `kind`).

Conventions de maillage et de rotation (utiles à animate.py et check.py) :
- le maillage est construit autour de l'origine locale ; l'objet est placé au centre de la pièce, de sorte que
  l'axe de rotation passe par l'origine (roues, arbres : (cx, cy, z milieu) ; tringles : milieu de p-q à z milieu) ;
- pièce d'axe ±Z : `spin` = 'Z', `spin_index` = 2, `spin_sign` = ±1, `rotation_euler` = (0, 0, ±angle) (maillage
  le long de +Z ; une rotation d'angle a autour de −Z est une rotation de −a autour de +Z, comme dans animate.py) ;
- autre axe (tringles, coniques couchées) : le maillage est construit le long de +X local, `spin` = 'X',
  `spin_index` = 0, `rotation_euler` = (angle, beta, gamma) en mode 'XYZ' ; (beta, gamma) orientent X local sur
  l'axe et ne changent jamais : seule la composante `spin_index` est animée (angle = −2π·phys·|taux|·jours + phase) ;
- couronne (`crown`) : dents sur la face +Z (`face` = −1 : sur −Z, en repère monde), axe des pignons couchés à
  z = 0 local (milieu de la couche ; pignon droit `gear` d'axe radial, largeur `width` ou 10 m) ; conique
  (`bevel`) : SOMMET du cône à l'origine (= `apex_point`), corps du côté −`apex`·axe (`apex` rapporté à l'axe,
  comme dans scene.json), de sorte que deux coniques placées au concours de leurs axes engrènent ;
- la phase n'est appliquée que par la rotation de l'objet (jamais dans le maillage) : dent 0 sur +X local
  (sur +Y local en mode 'X' ; pour une couronne intérieure, sa dent 0, pas son creux). animate.py pilote
  directement rotation_euler[spin_index] et y REMPLACE la phase de repos (sinon elle compterait deux fois) ;
- phases d'engrènement hors roues droites (à calculer par scene_model ; vérifiées sur la vraie scène) :
  couronne (angle θc, face f) et pignon couché à l'azimut g depuis l'axe de la couronne, d'axe s·radial (s = ±1) :
  φ ≡ f·s·(π/24 + 4·(θc − g)) (mod 2π/24), et dφ = 4·f·s·dθc ; onglets au concours (verticale V d'axe +Z, angle
  θV, `apex` aV ; couchée L d'axe u, `apex` aL ; g = azimut de −aL·u) : φL ≡ −aV·aL·(π/24 + θV − g) (mod 2π/24),
  et dφL = −aV·aL·dθV ;
- alésage : plus gros support vertical coaxial qui traverse la pièce (lié ou non, d'après `index`) + 0,05 ; un
  tube est toujours creux (`r_in`, sinon support intérieur + 0,05, sinon 2,05).
Les maillages identiques (même dents, module, épaisseur, alésage, sorte, axe) sont partagés (doublons liés).
"""
import math
import os
import sys
import time

import bpy
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from lib.involute import Involute  # noqa: E402
from lib.meshing import Builder, MeshError, triangulate  # noqa: E402
from lib.outline import ccw, circle, cw, gear_windows, rounded_rect  # noqa: E402

TWO_PI = 2.0 * math.pi
J_BACKLASH = 0.03        # jeu circonférentiel des roues droites (mm), architecture.json « jeu »
Z_GAP = 0.4              # épaisseur d'une roue = étendue z de la pièce moins 0,4 mm
BORE_CLEAR = 0.05        # alésage = rayon de l'arbre + 0,05 mm
ARBOR_R = 2.0            # rayon d'arbre par défaut (arch_layout.SHAFT_R)
ROD_R = 1.5              # rayon de tringle par défaut (arch_layout.ROD_R)
CROWN_TEETH, CROWN_M = 96, 0.4
BEVEL_TEETH, BEVEL_M = 24, 0.4
N_FLANK = 10             # points par flanc de développante
SUPPORT_KINDS = ('arbor', 'axis', 'tube', 'rod', 'misc')
DEFAULT_MATERIAL = {'gear': 'brass', 'crown': 'brass', 'bevel': 'bronze', 'arbor': 'steel', 'axis': 'steel',
                    'tube': 'brass', 'rod': 'steel', 'plate': 'bronze', 'block': 'block_translucent',
                    'misc': 'steel'}
DEFAULT_COLLECTION = 'V2_Pieces'

STATS = {}               # kind -> {'n': objets, 'built': maillages construits, 'shared': réutilisés, 's': secondes}
_MESH_CACHE = {}         # clé -> nom du maillage partagé


# ---------------------------------------------------------------------------------------------------------------
# Matériaux
# ---------------------------------------------------------------------------------------------------------------

def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _set(pb, name, value):
    """Règle une entrée du BSDF principié si elle existe (noms de Blender 4.x/5.x)."""
    if name in pb.inputs:
        pb.inputs[name].default_value = value


def _material(name, color, metallic=0.0, roughness=0.5, alpha=1.0):
    """Matériau principié simple (couleur linéaire) ; réutilise un matériau existant du même nom."""
    full = 'V2_' + name
    mat = bpy.data.materials.get(full)
    if mat is not None:
        return mat, False
    mat = bpy.data.materials.new(full)
    pb = _principled(mat)
    _set(pb, 'Base Color', tuple(color) + (1.0,))
    _set(pb, 'Metallic', metallic)
    _set(pb, 'Roughness', roughness)
    _set(pb, 'Alpha', alpha)
    mat.diffuse_color = tuple(color) + (alpha,)      # couleur de l'aperçu Workbench
    mat.metallic = metallic
    mat.roughness = roughness
    return mat, True


def _oak_grain(mat, color):
    """Veinage du chêne : texture d'ondes -> rampe de couleurs (comme le bois de la v1)."""
    nt = mat.node_tree
    pb = _principled(mat)
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.location = (-600, 200)
    wave.inputs['Scale'].default_value = 0.08
    wave.inputs['Distortion'].default_value = 6.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-350, 200)
    ramp.color_ramp.elements[0].color = tuple(c * 0.7 for c in color) + (1.0,)
    ramp.color_ramp.elements[1].color = tuple(min(1.0, c * 1.25) for c in color) + (1.0,)
    nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], pb.inputs['Base Color'])


def materials():
    """Dictionnaire des matériaux bpy de la v2 (créés une seule fois, préfixe « V2_ »)."""
    out = {}
    out['brass'], _ = _material('brass', (0.80, 0.55, 0.22), 1.0, 0.28)
    out['bronze'], _ = _material('bronze', (0.55, 0.33, 0.16), 1.0, 0.38)
    out['steel'], _ = _material('steel', (0.62, 0.63, 0.66), 1.0, 0.22)
    out['dial_dark'], _ = _material('dial_dark', (0.02, 0.025, 0.045), 0.2, 0.45)
    out['text'], _ = _material('text', (0.85, 0.65, 0.25), 1.0, 0.30)
    mat, new = _material('glass', (0.95, 0.97, 1.0), 0.0, 0.02, 1.0)
    if new:
        pb = _principled(mat)
        _set(pb, 'Transmission Weight', 1.0)
        _set(pb, 'IOR', 1.5)
        mat.diffuse_color = (0.9, 0.95, 1.0, 0.15)
        if hasattr(mat, 'use_raytrace_refraction'):
            mat.use_raytrace_refraction = True
    out['glass'] = mat
    mat, new = _material('oak', (0.42, 0.25, 0.12), 0.0, 0.55)
    if new:
        _oak_grain(mat, (0.42, 0.25, 0.12))
    out['oak'] = mat
    mat, new = _material('block_translucent', (0.80, 0.90, 1.0), 0.0, 0.30, 0.25)
    if new:
        if hasattr(mat, 'surface_render_method'):
            mat.surface_render_method = 'BLENDED'
        if hasattr(mat, 'use_transparency_overlap'):
            mat.use_transparency_overlap = False
        mat.use_backface_culling = False
    out['block_translucent'] = mat
    return out


# ---------------------------------------------------------------------------------------------------------------
# Repère d'une pièce
# ---------------------------------------------------------------------------------------------------------------

def obj_name(pid):
    """Nom d'objet Blender d'une pièce : '#' devient '.'."""
    return str(pid).replace('#', '.')


def _unit(v):
    v = np.asarray(v, float)
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        raise ValueError('axe nul')
    return v / n


def spin_frame(axis):
    """('Z', 0, 0, ±1) pour un axe ±Z ; sinon ('X', beta, gamma, 1) tels que Rz(gamma)·Ry(beta)·ex = axe."""
    a = _unit(axis)
    if abs(a[0]) < 1e-9 and abs(a[1]) < 1e-9:
        return 'Z', 0.0, 0.0, (1 if a[2] > 0 else -1)
    beta = -math.asin(max(-1.0, min(1.0, float(a[2]))))
    gamma = math.atan2(float(a[1]), float(a[0]))
    return 'X', beta, gamma, 1


def part_axis(part):
    """Axe de rotation d'une pièce : `axis` s'il est donné ; tringle : direction p -> q ; sinon +Z."""
    if part.get('axis') is not None:
        return [float(x) for x in _unit(part['axis'])]
    if part.get('kind') == 'rod' or ('p' in part and 'q' in part):
        d = np.asarray(part['q'], float)[:2] - np.asarray(part['p'], float)[:2]
        return [float(x) for x in _unit([d[0], d[1], 0.0])]
    return [0.0, 0.0, 1.0]


def n_circle(r, step=0.5, nmin=32, nmax=256):
    """Nombre de côtés d'un cercle de rayon r (corde d'environ `step` mm)."""
    return int(max(nmin, min(nmax, math.ceil(TWO_PI * r / step))))


def prop_list(obj, key):
    """Liste Python d'une propriété (liste native, tableau ou chaîne « a,b,c »)."""
    v = obj.get(key)
    if v is None:
        return []
    if isinstance(v, str):
        return [s for s in v.split(',') if s]
    return [str(s) for s in v]


# ---------------------------------------------------------------------------------------------------------------
# Géométrie (construite le long de +Z local, centrée en z = 0)
# ---------------------------------------------------------------------------------------------------------------

def clean_loop(p, tol_d=2e-4, tol_area=1e-7):
    """Retire d'une boucle les points quasi confondus et les points alignés avec leurs voisins : la triangulation
    n'y crée plus de triangles d'aire nulle (côtés droits des fenêtres, raccords de pied)."""
    p = np.asarray(p, dtype=float)
    changed = True
    while changed and len(p) > 3:
        changed = False
        keep = []
        n = len(p)
        for i in range(n):
            a, b, c = p[i - 1], p[i], p[(i + 1) % n]
            if np.hypot(*(b - a)) < tol_d:
                changed = True
                continue
            area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
            if area2 < tol_area * max(np.hypot(*(c - a)), 1e-9):
                changed = True
                continue
            keep.append(i)
        p = p[keep]
    return p


def gear_loops(teeth, m, bore=None, mesh='external', r_out=None, j=J_BACKLASH, n_flank=N_FLANK):
    """Boucles 2D d'une roue droite à développante de 30° (dent 0 sur +x), amincie du jeu j.
    Extérieure : denture + alésage (absent si l'arbre ne laisse pas 0,3 mm de voile : pignon taillé dans
    l'arbre) + fenêtres d'allègement si le rayon primitif dépasse 12 mm (règles de gear_loops v1).
    Intérieure : couronne ; son creux est la dent d'une roue extérieure virtuelle (saillie 1,25 m, creux 1 m)
    épaissie de j/2, décalée d'un demi-pas pour que la DENT 0 de la couronne soit sur +x, comme pour toutes les
    roues (phase = angle de la dent 0). Renvoie (boucles, info)."""
    if mesh == 'internal':
        ha = 1.25
        g = Involute(teeth, m, ha=ha, hf=1.0, j=-j)
        while g.tip_land() < 0.1 * m and ha > 0.6:          # creux pointu : on réduit la profondeur
            ha -= 0.05
            g = Involute(teeth, m, ha=ha, hf=1.0, j=-j)
        R = max(float(r_out or 0.0), g.ra + max(2.0, 4.0 * m))
        loops = [ccw(circle(0.0, 0.0, R, n_circle(R, 0.4, 64, 512))), cw(g.outline(math.pi / teeth, n_flank))]
        loops = [clean_loop(lp) for lp in loops]
        return loops, {'r': g.r, 'ra': g.rf, 'rf': g.ra, 'r_out': R, 'bore': None, 'n_windows': 0}
    g = Involute(teeth, m, j=j)
    loops = [ccw(g.outline(0.0, n_flank))]
    has_bore = bore is not None and bore < g.rf - 0.3
    if has_bore:
        loops.append(cw(circle(0.0, 0.0, bore, n_circle(bore, 0.3, 32, 128))))
    windows = []
    if g.r > 12.0:
        r_hub = (bore if has_bore else ARBOR_R) + 2.0
        r_rim = g.rf - max(1.5, 2.0 * m)
        if r_rim - r_hub >= 2.0:
            n = 6 if r_rim >= 15 else (5 if r_rim >= 10 else 4)
            aw = max(1.5, 0.12 * g.r)
            windows = gear_windows(r_hub, r_rim, n, [aw] * n)
    loops += windows
    loops = [clean_loop(lp) for lp in loops]
    return loops, {'r': g.r, 'ra': g.ra, 'rf': g.rf, 'r_out': g.ra, 'bore': bore if has_bore else None,
                   'n_windows': len(windows)}


def loft(B, sections):
    """Solide fermé entre sections de même topologie [(boucles, z), ...] (z croissants) : parois en quadrangles,
    bouchons triangulés (CDT) aux deux bouts."""
    counts = [len(lp) for lp in sections[0][0]]
    n = sum(counts)
    V = [np.column_stack([np.vstack(lps), np.full(n, z)]) for lps, z in sections]
    base = B.add_verts(np.vstack(V))
    B.add_polys(triangulate(sections[0][0])[:, ::-1].tolist(), base)
    B.add_polys((triangulate(sections[-1][0]) + n * (len(sections) - 1)).tolist(), base)
    for s in range(len(sections) - 1):
        lo, hi, off = base + s * n, base + (s + 1) * n, 0
        for L in counts:
            for i in range(L):
                a, b = off + i, off + (i + 1) % L
                B.P.append([lo + a, lo + b, hi + b, hi + a])
            off += L


def crown_builder(B, teeth, m, t, bore, j=J_BACKLASH, pin_teeth=BEVEL_TEETH, n_st=24):
    """Couronne de champ (roue de face) pour un pignon droit couché d'axe radial, à z = 0 local (milieu de la
    couche, donc pignon centré sur la couche) : disque percé, dents sur la face +Z. À chaque rayon r, la section
    de la denture est la crémaillère conjuguée du pignon à développante qui roule au rayon ρ = r / i
    (i = dents / pin_teeth) : angle de pression acos(rb / ρ), épaisseur = pas local − épaisseur du pignon en ρ
    − j/2 (le pignon porte l'autre j/2). Dents de r_t0 (sans dépouille : ρ > 1,03 rb) à r_out = rp + 2 m.
    Solide balayé autour de Z d'une section dont le dessus suit la denture (une seule coque)."""
    pin = Involute(pin_teeth, m)
    ir = teeth / float(pin_teeth)
    rp = m * teeth / 2.0
    r_out = rp + 2.0 * m
    r_t0 = max(rp - 10.0 * m, bore + 1.5, ir * pin.rb * 1.03)
    zb = -t / 2.0
    zt, zr = -(pin.rf + 0.25 * m), -(pin.ra + 0.25 * m)      # jeu de fond 0,25 m des deux côtés
    zh = zr - 0.2
    if zh < zb + 0.8:                                         # couche trop mince : on remonte la denture
        zt, zr, zh = zt + (zb + 0.8 - zh), zr + (zb + 0.8 - zh), zb + 0.8
    if zt > t / 2.0 or r_t0 >= r_out - 0.5:
        raise MeshError('couronne : enveloppe trop petite (t=%.2f, alésage=%.2f)' % (t, bore))
    pa = TWO_PI / teeth
    rs = np.linspace(r_t0, r_out, n_st + 1)
    a_tip, a_root = [], []
    for r in rs:
        rho = r / ir
        ta = math.tan(math.acos(min(1.0, pin.rb / rho)))
        s_t = r * pa - 2.0 * rho * float(pin.psi(rho)) - j / 2.0
        w_tip = s_t / 2.0 - (zt + rho) * ta                    # ligne primitive locale à z = −ρ
        w_root = min(s_t / 2.0 - (zr + rho) * ta, r * pa / 2.0 - 0.01)
        w_tip = max(min(w_tip, w_root - 0.01), 0.02)
        a_tip.append(w_tip / r)
        a_root.append(w_root / r)
    a_tip, a_root = np.array(a_tip), np.array(a_root)
    th = (np.arange(teeth) * pa)[:, None, None] + np.stack([-a_root, -a_tip, a_tip, a_root])[None, :, :]
    th = th.reshape(-1, n_st + 1)                             # (K, stations) : 4 points par dent
    zz = np.tile([zr, zt, zt, zr], teeth)
    K, ns = th.shape[0], n_st + 1
    # section (sens trigonométrique dans le plan (r, z)) : alésage bas, bord bas, dessus de r_out à r_t0,
    # moyeu, alésage haut
    R = np.concatenate([[bore, r_out], rs[::-1], [r_t0, bore]])
    T = np.column_stack([th[:, 0], th[:, -1], th[:, ::-1], th[:, 0], th[:, 0]])
    Z = np.column_stack([np.full(K, zb), np.full(K, zb), np.repeat(zz[:, None], ns, 1), np.full(K, zh),
                         np.full(K, zh)])
    nv = len(R)
    V = np.stack([R[None, :] * np.cos(T), R[None, :] * np.sin(T), Z], axis=-1)
    base = B.add_verts(V.reshape(-1, 3))
    for i in range(K):
        i1 = (i + 1) % K
        for e in range(nv):
            a, b = e, (e + 1) % nv
            B.P.append([base + i * nv + a, base + i1 * nv + a, base + i1 * nv + b, base + i * nv + b])
    return {'r': rp, 'ra': r_out, 'r_teeth': [float(r_t0), float(r_out)], 'bore': bore}


def bevel_builder(B, teeth, m, bore, apex=1, cone_deg=45.0, j=J_BACKLASH, n_flank=6):
    """Conique simplifiée : tronc de cône denté dont le SOMMET est à l'origine locale (sur l'axe). Section
    transverse = denture plane à développante de la roue droite de même nombre de dents, réduite vers le sommet.
    Deux coniques d'onglet placées au point de concours de leurs axes (comme dans architecture.json) engrènent
    donc d'elles-mêmes. `apex` = +1 : le sommet est du côté +Z du corps (corps vers −Z), −1 : l'inverse."""
    g = Involute(teeth, m, j=j)
    star = ccw(g.outline(0.0, n_flank))
    d = math.radians(cone_deg)
    Rc = g.r / math.sin(d)                 # génératrice primitive (sommet -> cercle primitif du gros bout)
    b = Rc / 3.0                           # largeur de denture
    s = (Rc - b) / Rc                      # réduction au petit bout
    hole = None
    if bore is not None and bore < s * g.rf - 0.3:
        hole = cw(circle(0.0, 0.0, bore, n_circle(bore, 0.3, 32, 96)))

    def lps(k):
        return [star * k] + ([hole] if hole is not None else [])

    loft(B, [(lps(1.0), -Rc * math.cos(d)), (lps(s), -(Rc - b) * math.cos(d))])
    if apex < 0:
        flip_z(B)
    return {'r': g.r, 'ra': g.ra, 'cone_distance': Rc, 'face_width': b, 'apex': apex,
            'bore': bore if hole is not None else None}


def cylinder_builder(B, r, h, r_in=None):
    """Cylindre plein (ou tube si r_in) d'axe Z, de hauteur h centrée en 0."""
    loops = [ccw(circle(0.0, 0.0, r, n_circle(r)))]
    if r_in:
        loops.append(cw(circle(0.0, 0.0, r_in, n_circle(r_in))))
    B.prism([loops], -h / 2.0, h / 2.0)


def to_x_axis(B):
    """Fait passer un maillage construit le long de Z sur l'axe X local : (x, y, z) -> (z, x, y) (rotation propre :
    l'orientation des faces et le sens de rotation sont conservés)."""
    B.V = [np.asarray(v)[:, [2, 0, 1]] for v in B.V]


def flip_z(B):
    """Retourne un maillage face pour face (rotation de 180° autour de X : (x, y, z) -> (x, −y, −z))."""
    B.V = [np.asarray(v) * np.array([1.0, -1.0, -1.0]) for v in B.V]


# ---------------------------------------------------------------------------------------------------------------
# Platines : contour + trous
# ---------------------------------------------------------------------------------------------------------------

def _inside(pt, poly):
    """Point dans un polygone (lancer de rayon)."""
    x, y = pt
    a, b = poly, np.roll(poly, -1, axis=0)
    cond = (a[:, 1] > y) != (b[:, 1] > y)
    with np.errstate(divide='ignore', invalid='ignore'):
        xs = a[:, 0] + (y - a[:, 1]) * (b[:, 0] - a[:, 0]) / (b[:, 1] - a[:, 1])
    return bool(np.count_nonzero(cond & (x < xs)) % 2)


def _dist_to_poly(pt, poly):
    """Distance d'un point au bord d'un polygone fermé."""
    a, b = poly, np.roll(poly, -1, axis=0)
    ab = b - a
    t = np.clip(((pt - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-18), 0.0, 1.0)
    return float(np.min(np.linalg.norm(a + t[:, None] * ab - pt, axis=1)))


def merge_circles(cs, web=0.3):
    """Fusionne les trous ronds [x, y, r] qui se touchent (voile < web) en leur cercle englobant, jusqu'à ce
    qu'il n'y ait plus de recouvrement. Renvoie (cercles, nombre de fusions)."""
    cs = [list(map(float, c)) for c in cs]
    merged = 0
    while len(cs) > 1:
        A = np.array(cs)
        d = np.hypot(A[:, None, 0] - A[None, :, 0], A[:, None, 1] - A[None, :, 1])
        bad = np.triu(d < A[:, None, 2] + A[None, :, 2] + web, 1)
        if not bad.any():
            break
        i, k = map(int, np.argwhere(bad)[0])
        (xi, yi, ri), (xk, yk, rk), dd = cs[i], cs[k], float(d[i, k])
        if dd + rk <= ri:
            new = cs[i]
        elif dd + ri <= rk:
            new = cs[k]
        else:
            R = (dd + ri + rk) / 2.0
            u = (R - ri) / dd
            new = [xi + (xk - xi) * u, yi + (yk - yi) * u, R]
        cs = [c for n, c in enumerate(cs) if n not in (i, k)] + [new]
        merged += 1
    return cs, merged


def plate_outline(part):
    """Contour extérieur (repère machine) : `outline` [[x, y], ...], ou `x`/`y` (rectangle, coins `corner`),
    ou `c`/`r` (disque)."""
    if part.get('outline') is not None:
        return ccw(np.asarray(part['outline'], float)[:, :2])
    if part.get('x') is not None and part.get('y') is not None:
        (x0, x1), (y0, y1) = part['x'], part['y']
        rc = float(part.get('corner', 4.0))
        return ccw(rounded_rect(x0, y0, x1, y1, rc) if rc > 0 else np.array(
            [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float))
    c, r = part.get('c', [0.0, 0.0]), float(part['r'])
    return ccw(circle(c[0], c[1], r, n_circle(r, 1.0, 64, 512)))


def plate_loops(part, web=0.3):
    """Boucles d'une platine dans le repère machine : contour + trous. `holes` : {'c': [x, y], 'r': r},
    [x, y, r] ou une boucle [[x, y], ...]. Les trous ronds qui se recouvrent sont fusionnés ; ceux qui
    sortent du contour sont ignorés. Renvoie (boucles, avertissements)."""
    outer = plate_outline(part)
    circles, polys, warn = [], [], []
    for h in part.get('holes', []) or []:
        if isinstance(h, dict):
            circles.append([h['c'][0], h['c'][1], h['r']])
        elif len(h) == 3 and np.isscalar(h[0]):
            circles.append(list(h))
        else:
            polys.append(cw(np.asarray(h, float)[:, :2]))
    if part.get('r_in') and part.get('outline') is None and part.get('x') is None:
        c = part.get('c', [0.0, 0.0])
        circles.append([c[0], c[1], part['r_in']])
    circles, merged = merge_circles(circles, web)
    if merged:
        warn.append('%d trous fusionnés' % merged)
    holes = []
    for x, y, r in circles:
        if not _inside((x, y), outer) or _dist_to_poly(np.array([x, y]), outer) < r + web:
            warn.append('trou (%.1f, %.1f, r %.2f) hors du contour : ignoré' % (x, y, r))
            continue
        holes.append(cw(circle(x, y, r, n_circle(r, 0.4, 24, 160))))
    return [outer] + holes + polys, warn


# ---------------------------------------------------------------------------------------------------------------
# Construction d'une pièce
# ---------------------------------------------------------------------------------------------------------------

def _q(x):
    return None if x is None else round(float(x), 4)


def _zr(part):
    z = part.get('z', [0.0, 0.0])
    return float(z[0]), float(z[1])


_SUPPORTS = {'index': None, 'n': -1, 'list': []}   # supports verticaux du dernier index vu


def _vertical_supports(index):
    """Supports verticaux (cylindres d'axe Z avec `c` et `r`) d'un index, mis en cache pour cet index (on garde
    une référence à l'index lui-même : pas de confusion avec un autre dictionnaire de même id)."""
    if _SUPPORTS['index'] is not index or _SUPPORTS['n'] != len(index):
        _SUPPORTS['list'] = [o for o in index.values()
                             if o.get('kind') in SUPPORT_KINDS and 'p' not in o and o.get('c') is not None
                             and o.get('r') is not None and o.get('z') is not None
                             and abs(float((o.get('axis') or [0, 0, 1])[2])) > 1.0 - 1e-9]
        _SUPPORTS['index'], _SUPPORTS['n'] = index, len(index)
    return _SUPPORTS['list']


def coaxial_supports(part, index):
    """Supports verticaux coaxiaux à la pièce (centre à 1e-3 mm près) dont l'étendue z recouvre strictement la
    sienne : ceux de `links` ET tous ceux de l'index (un tube qui traverse la roue impose l'alésage, même s'il
    n'est pas listé dans `links`). La pièce elle-même est exclue."""
    c = part.get('c')
    if not index or c is None:
        return []
    z0, z1 = _zr(part)
    out = []
    for o in _vertical_supports(index):
        if o is part or o.get('id') == part.get('id'):
            continue
        oz = o['z']
        if math.dist(c[:2], o['c'][:2]) < 1e-3 and oz[0] < z1 - 1e-9 and oz[1] > z0 + 1e-9:
            out.append(o)
    return out


def bore_radius(part, index=None, mode='Z', default_r=None):
    """Rayon d'alésage : `bore`, sinon `arbor_r` + 0,05, sinon le plus gros support coaxial qui traverse la pièce
    (arbre, axe, tube, lié ou non ; tringle dont un bout est au centre pour une pièce couchée) + 0,05, sinon
    `default_r` + 0,05."""
    if part.get('bore') is not None:
        return float(part['bore'])
    for k in ('arbor_r', 'arbor_radius'):
        if part.get(k) is not None:
            return float(part[k]) + BORE_CLEAR
    rod = _rod_of(part, index) if mode == 'X' else None
    if rod is not None and rod.get('r') is not None:
        return float(rod['r']) + BORE_CLEAR
    best, c = None, part.get('c')
    if index and c is not None:
        for lid in part.get('links', []) or []:
            o = index.get(lid)
            if (mode == 'X' and o and o.get('kind') in SUPPORT_KINDS and o.get('r') is not None
                    and 'p' in o and 'q' in o
                    and min(math.dist(c[:2], o['p'][:2]), math.dist(c[:2], o['q'][:2])) < 1e-3):
                best = max(best or 0.0, float(o['r']))
        if mode == 'Z':
            for o in coaxial_supports(part, index):
                best = max(best or 0.0, float(o['r']))
    if best is None and default_r is None:
        default_r = ROD_R if mode == 'X' else ARBOR_R
    return (best if best else default_r) + BORE_CLEAR


def tube_inner_radius(part, index=None):
    """Rayon intérieur d'un tube : `r_in`, sinon le plus gros support coaxial plus fin qui le traverse + 0,05,
    sinon l'arbre par défaut (2 mm) + 0,05. Un tube n'est jamais plein (un arbre tourne dedans)."""
    if part.get('r_in') is not None:
        return float(part['r_in'])
    r = float(part.get('r', ARBOR_R))
    inner = [float(o['r']) for o in coaxial_supports(part, index) if float(o['r']) < r - 1e-9]
    return (max(inner) if inner else ARBOR_R) + BORE_CLEAR


def _rod_of(part, index):
    """Tringle porteuse : clé `rod`, sinon une tringle liée dont un bout est au centre de la pièce."""
    if not index or part.get('c') is None:
        return None
    if part.get('rod') in index:
        return index[part['rod']]
    for lid in part.get('links', []) or []:
        o = index.get(lid)
        if o and 'p' in o and 'q' in o and min(math.dist(part['c'][:2], o['p'][:2]),
                                               math.dist(part['c'][:2], o['q'][:2])) < 1e-3:
            return o
    return None


def _bevel_apex(part, index, axis):
    """Côté du sommet d'une conique LE LONG DE SON AXE (convention de scene.json : +1 = sommet côté +axe, corps
    vers −axe) : `apex`, sinon le corps va vers sa tringle porteuse (vers le bout éloigné) ou le long de son arbre
    coaxial lié, sinon +1."""
    if part.get('apex') is not None:
        return 1 if float(part['apex']) >= 0 else -1
    c = part.get('c')
    lying = abs(axis[2]) < 1.0 - 1e-9
    rod = _rod_of(part, index) if lying else None
    if rod is not None:
        far = max((rod['p'], rod['q']), key=lambda e: math.dist(c[:2], e[:2]))
        side = (far[0] - c[0]) * axis[0] + (far[1] - c[1]) * axis[1]
        return -1 if side > 0 else 1
    if index and c is not None and not lying:            # axe ±Z : maillage le long de +Z monde
        z0, z1 = _zr(part)
        zm = (z0 + z1) / 2.0
        for lid in part.get('links', []) or []:
            o = index.get(lid)
            if (o and o.get('kind') in SUPPORT_KINDS and o.get('c') is not None and 'p' not in o
                    and math.dist(c[:2], o['c'][:2]) < 1e-3):
                below, above = zm - float(o['z'][0]), float(o['z'][1]) - zm
                up = 1 if below >= above else -1          # sommet côté +Z monde
                return up if axis[2] > 0 else -up         # ... rapporté à l'axe (±Z)
    return 1


def engage_phase(a, b, index=None):
    """Contact hors roues droites (couronne + pignon couché, ou paire d'onglet au concours des axes) entre les
    pièces a et b de scene.json : (id de la pièce menée par la formule, sa phase, k) avec dφ = k·dθ de l'autre.
    `apex` absent : déduit comme à la construction (_bevel_apex, d'où `index`).
    La pièce de référence (couronne, ou conique verticale d'axe +Z) garde sa phase. Formules du docstring du module,
    valables pour 96/24 et 24/24 (pas de la pièce couchée 2π/24)."""
    def wrap(x, p):
        return x - p * math.floor(x / p)
    pz = TWO_PI / BEVEL_TEETH
    if 'crown' in (a.get('kind'), b.get('kind')):
        c, p = (a, b) if a.get('kind') == 'crown' else (b, a)
        f = 1 if float(c.get('face', 1)) >= 0 else -1
        d = (p['c'][0] - c['c'][0], p['c'][1] - c['c'][1])
        g = math.atan2(d[1], d[0])
        ax = part_axis(p)
        s = 1 if ax[0] * d[0] + ax[1] * d[1] > 0 else -1
        k = f * s * float(c.get('teeth', CROWN_TEETH)) / float(p.get('teeth', BEVEL_TEETH))
        th = float(c.get('phase', 0.0) or 0.0)
        return p['id'], wrap(f * s * (pz / 2.0) + k * (th - g), pz), k
    V, L = (a, b) if abs(part_axis(a)[2]) > 0.5 else (b, a)
    aV, aL, u = _bevel_apex(V, index, part_axis(V)), _bevel_apex(L, index, part_axis(L)), part_axis(L)
    if part_axis(V)[2] < 0:
        raise ValueError('engage_phase : conique verticale d\'axe −Z non prise en charge')
    g = math.atan2(-aL * u[1], -aL * u[0])
    k = -aV * aL
    th = float(V.get('phase', 0.0) or 0.0)
    return L['id'], wrap(k * (pz / 2.0 + th - g), pz), k


def _shared_mesh(key, name, make, mode):
    """Maillage partagé entre pièces identiques ; `make(B)` remplit un Builder le long de Z.
    Renvoie (maillage, réutilisé, info)."""
    entry = _MESH_CACHE.get(key)
    if entry is not None:
        me = bpy.data.meshes.get(entry[0])
        if me is not None and me.get('v2_key') == repr(key):   # pas un homonyme après réinitialisation
            return me, True, entry[1]
    B = Builder()
    info = make(B) or {}
    if mode == 'X':
        to_x_axis(B)
    me = B.to_mesh(name)
    me['v2_key'] = repr(key)
    _MESH_CACHE[key] = (me.name, info)
    return me, False, info


def _geometry(part, mode, index):
    """(maillage, position, réutilisé, info) d'une pièce, selon son `kind`."""
    kind = part.get('kind', 'misc')
    z0, z1 = _zr(part)
    zm, h = (z0 + z1) / 2.0, z1 - z0
    c = part.get('c', [0.0, 0.0])
    loc = (float(c[0]), float(c[1]), zm)
    if kind == 'gear':
        teeth, m, mk = int(part['teeth']), float(part['m']), part.get('mesh', part.get('mesh_kind', 'external'))
        t = h - Z_GAP if h - Z_GAP > 0.2 else max(0.8 * h, 0.2)
        if mode == 'X':
            t = min(t, 10.0 * m)          # pignon couché : largeur 10 m (l'étendue z est celle de la couche)
        if mode == 'X':                   # largeur donnée par la scène (`width`) si elle est plus petite
            t = min(t, float(part.get('width') or t))
        bore = bore_radius(part, index, mode) if mk != 'internal' else None
        r_out = part.get('r_out', part.get('r')) if mk == 'internal' else None
        j = float(part.get('j', J_BACKLASH))
        key = ('gear', mk, teeth, _q(m), _q(t), _q(bore), _q(r_out), _q(j), mode)

        def make(B):
            loops, info = gear_loops(teeth, m, bore, mk, r_out, j)
            B.prism([loops], -t / 2.0, t / 2.0)
            return info
        me, shared, info = _shared_mesh(key, 'G_%s_z%d_m%g_t%g' % (mk[:3], teeth, m, t), make, mode)
        warn = []
        if bore is not None and info.get('bore') is None and bore > ARBOR_R + BORE_CLEAR + 1e-6:
            warn.append('alésage %.2f impossible sous le pied (r %.2f) : roue dessinée pleine' % (bore, info['rf']))
        return me, shared, dict(info, warnings=warn), loc
    if kind == 'crown':
        teeth, m = int(part.get('teeth', CROWN_TEETH)), float(part.get('m', CROWN_M))
        t, bore, face = h - Z_GAP, bore_radius(part, index, mode), 1 if float(part.get('face', 1)) >= 0 else -1
        zp = int(part.get('pin_teeth', BEVEL_TEETH))
        key = ('crown', teeth, _q(m), _q(t), _q(bore), face, zp, mode)

        def make(B):
            info = crown_builder(B, teeth, m, t, bore, pin_teeth=zp)
            if face < 0:
                flip_z(B)
            return info
        return _shared_mesh(key, 'C_z%d_m%g_t%g' % (teeth, m, t), make, mode) + (loc,)
    if kind == 'bevel':
        teeth, m = int(part.get('teeth', BEVEL_TEETH)), float(part.get('m', BEVEL_M))
        bore = bore_radius(part, index, mode)
        axis = part_axis(part)
        apex = _bevel_apex(part, index, axis)
        cone = float(part.get('pitch_angle_deg', part.get('cone_deg', 45.0)))
        # maillage le long de +Z local : en mode 'X', +Z local devient l'axe ; en mode 'Z' d'axe −Z, le maillage
        # reste le long de +Z monde, donc le côté du sommet s'inverse
        mesh_apex = apex if (mode == 'X' or axis[2] > 0) else -apex
        key = ('bevel', teeth, _q(m), _q(bore), mesh_apex, _q(cone), mode)
        me, shared, info = _shared_mesh(key, 'B_z%d_m%g' % (teeth, m),
                                        lambda B: bevel_builder(B, teeth, m, bore, mesh_apex, cone), mode)
        return me, shared, dict(info, apex=apex), loc
    if kind == 'rod' or (kind == 'misc' and 'p' in part and 'q' in part):
        p, q = np.asarray(part['p'], float)[:2], np.asarray(part['q'], float)[:2]
        L, r = float(np.linalg.norm(q - p)), float(part.get('r', ROD_R))
        key = ('cyl', _q(r), None, _q(L), mode)
        loc = (float((p[0] + q[0]) / 2), float((p[1] + q[1]) / 2), zm)
        return _shared_mesh(key, 'R_r%g_L%g' % (r, L), lambda B: cylinder_builder(B, r, L), mode) + (loc,)
    if kind == 'plate':
        loops, warn = plate_loops(part)
        x0, y0 = loops[0].min(0)
        x1, y1 = loops[0].max(0)
        cc = part.get('c') or [(x0 + x1) / 2.0, (y0 + y1) / 2.0]
        sh = np.array([cc[0], cc[1]], float)
        B = Builder()
        B.prism([[lp - sh for lp in loops]], -h / 2.0, h / 2.0)
        return B.to_mesh('P_' + obj_name(part['id'])), False, {'warnings': warn}, (float(sh[0]), float(sh[1]), zm)
    r, r_in = float(part.get('r', ARBOR_R)), part.get('r_in')
    warn = []
    if kind == 'tube':
        r_in = tube_inner_radius(part, index)
        if r_in >= r - 0.3:
            warn.append('tube r %.2f : paroi impossible autour de r_in %.2f, dessiné plein' % (r, r_in))
            r_in = None
    hh = h - 0.2 if kind == 'block' and h > 0.4 else h
    key = ('cyl', _q(r), _q(r_in), _q(hh), mode)
    me, shared, info = _shared_mesh(key, 'Y_r%g_h%g' % (r, hh), lambda B: cylinder_builder(B, r, hh, r_in), mode)
    return me, shared, dict(info, r_in=r_in, warnings=warn), loc


def _collection(part, colls):
    """Collection de la pièce : `colls` (collection unique, ou dictionnaire nom -> collection : `collection` de la
    pièce, sinon la clé '_default', sinon une collection créée, liée à la scène et ajoutée au dictionnaire)."""
    if isinstance(colls, bpy.types.Collection):
        return colls
    name = part.get('collection') or DEFAULT_COLLECTION
    if isinstance(colls, dict):
        if name in colls:
            return colls[name]
        if colls.get('_default') is not None:
            return colls['_default']
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if coll.users == 0:
        bpy.context.scene.collection.children.link(coll)
    if isinstance(colls, dict):
        colls[name] = coll
    return coll


def _set_props(obj, part, axis, mode, sign, info):
    """Recopie les propriétés de mouvement de la pièce dans les propriétés personnalisées de l'objet."""
    kind = part.get('kind', 'misc')
    motion = str(part.get('motion', 'fixed'))
    obj['part_id'] = str(part['id'])
    obj['kind'] = kind
    obj['motion'] = motion
    obj['rate'] = float(part.get('rate', 0.0) or 0.0)
    obj['phys'] = int(part['phys']) if part.get('phys') is not None else 1
    obj['phase'] = float(part.get('phase', 0.0) or 0.0)
    obj['axis'] = [float(x) for x in axis]
    if part.get('scale') is not None:
        obj['scale'] = float(part['scale'])
    elif motion.startswith('ephem:'):
        obj['scale'] = -1.0
    obj['source'] = str(part.get('source', '') or '')
    obj['meshes_with'] = [obj_name(x) for x in part.get('meshes_with', []) or []]
    obj['links'] = [obj_name(x) for x in part.get('links', []) or []]
    obj['engages'] = [obj_name(x) for x in part.get('engages', []) or []]   # couronnes, onglets (scene.json)
    obj['spin'] = mode
    obj['spin_index'] = 2 if mode == 'Z' else 0
    obj['spin_sign'] = int(sign)
    for k in ('label', 'collection', 'mesh'):
        if part.get(k) is not None:
            obj[k] = str(part[k])
    for k in ('teeth', 'm'):
        if part.get(k) is not None:
            obj[k] = part[k]
    for k in ('r', 'ra', 'bore', 'r_in', 'n_windows', 'apex'):
        if info.get(k) is not None:
            obj['r_pitch' if k == 'r' else k] = float(info[k])
    if info.get('warnings'):
        obj['warnings'] = '; '.join(info['warnings'])


def _assign_material(obj, mat):
    """Matériau de l'objet : sur le maillage partagé s'il n'en a pas, sinon par objet s'il diffère."""
    if mat is None:
        return
    me = obj.data
    if len(me.materials) == 0:
        me.materials.append(mat)
    elif me.materials[0] != mat:
        slot = obj.material_slots[0]
        slot.link = 'OBJECT'
        slot.material = mat


CHAR_W, LINE_H = 0.62, 1.3      # largeur d'un caractère et interligne, en tailles de police (marge comprise)


def label_box(r, r_in=0.0):
    """Boîte (largeur, hauteur, y du centre) de l'étiquette d'un bloc, dans l'empreinte du bloc : carré inscrit
    du disque ; pour un anneau, rectangle inscrit dans la bande, en haut (+Y)."""
    if not r_in:
        return 1.3 * r, 1.3 * r, 0.0
    H = 0.8 * (r - r_in)
    yc = (r + r_in) / 2.0
    W = 2.0 * math.sqrt(max(r * r - (yc + H / 2.0) ** 2, 0.0))
    return W, H, yc


def fit_label(text, W, H, s_max=8.0, s_min=0.6):
    """(lignes, taille) : plus grande taille ≤ s_max telle que le texte, coupé aux mots, tienne dans W × H ; à la
    taille minimale, les lignes en trop sont coupées (« … »)."""
    import textwrap
    s = s_max
    while True:
        n = max(4, int(W / (CHAR_W * s)))
        lines = []
        for para in str(text).split('\n'):
            lines += textwrap.wrap(para, n, break_long_words=True) or ['']
        if len(lines) * LINE_H * s <= H or s <= s_min:
            break
        s = max(s_min, s * 0.9)
    k = max(1, int(H / (LINE_H * s)))
    if len(lines) > k:
        lines = lines[:k]
        lines[-1] = lines[-1][:max(1, n - 1)].rstrip() + '…'
    return lines, s


def _block_label(obj, part, coll, mats, h):
    """Petite étiquette (texte plat, coupé aux mots) posée sur la face avant du bloc, enfant du bloc ; elle tient
    dans l'empreinte du bloc (label_box), quelle que soit la longueur du `label`."""
    r, r_in = float(part.get('r', 10.0)), float(part.get('r_in') or 0.0)
    txt = str(part['id'])
    if part.get('label') and str(part['label']) != txt:
        txt += '\n' + str(part['label'])
    W, H, yc = label_box(r, r_in)
    lines, size = fit_label(txt, W, H, s_max=min(8.0, max(2.0, 0.15 * r)))
    cu = bpy.data.curves.new(obj.name + '_label', 'FONT')
    cu.body = '\n'.join(lines)
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.size = size
    lo = bpy.data.objects.new(obj.name + '_label', cu)
    lo.parent = obj
    lo.location = (0.0, yc, h / 2.0 + 0.2)
    lo['label_box'] = [float(W), float(H)]
    lo['kind'] = 'label'
    lo['motion'] = 'fixed'
    lo['label_of'] = str(part['id'])     # pas « part_id » : le bloc seul doit répondre à son id (check.py)
    if mats and mats.get('text') is not None:
        cu.materials.append(mats['text'])
    coll.objects.link(lo)
    return lo


SCENE_JSON = os.path.join(os.path.dirname(_HERE), 'spec', 'scene.json')
_SCENE = {'mtime': None, 'index': None}


def scene_index(path=SCENE_JSON):
    """Index id -> pièce de spec/scene.json (relu si le fichier change), ou None s'il est absent."""
    try:
        mt = os.path.getmtime(path)
    except OSError:
        return None
    if _SCENE['mtime'] != mt:
        import json
        with open(path) as f:
            _SCENE['index'] = {p['id']: p for p in json.load(f).get('parts', [])}
        _SCENE['mtime'] = mt
    return _SCENE['index']


def build_part(part, colls=None, mats=None, index=None):
    """Objet Blender d'une pièce de scene.json (tout `kind`). `colls` : collection, ou dictionnaire
    nom -> collection (une collection absente est créée et liée à la scène) ; `mats` : dictionnaire de
    materials() ; `index` (facultatif) : dictionnaire id -> pièce, pour trouver les supports coaxiaux (alésage,
    tube creux) et le côté du sommet des coniques. Sans `index`, si la pièce est telle quelle dans
    spec/scene.json, l'index de ce fichier est utilisé (sinon : rayons par défaut). Nom = id ('#' -> '.'),
    rotation_mode 'XYZ', phase dans la rotation seulement."""
    t0 = time.perf_counter()
    kind = part.get('kind', 'misc')
    if index is None:
        si = scene_index()
        if si is not None and si.get(part.get('id')) == part:
            index = si
    axis = part_axis(part)
    if kind == 'rod' and part.get('axis') is None and abs(axis[0]) < 1e-9:
        axis = [0.0, 1.0, 0.0]                             # tringle verticale : +Y (contrat § 2)
    mode, beta, gamma, sign = spin_frame(axis)
    me, shared, info, loc = _geometry(part, mode, index)
    name = obj_name(part['id'])
    obj = bpy.data.objects.new(name, me)
    obj.location = loc
    obj.rotation_mode = 'XYZ'
    phase = float(part.get('phase', 0.0) or 0.0)
    obj.rotation_euler = (0.0, 0.0, sign * phase) if mode == 'Z' else (phase, beta, gamma)
    mats = mats or {}
    _assign_material(obj, mats.get(part.get('material') or DEFAULT_MATERIAL.get(kind, 'steel')))
    _set_props(obj, part, axis, mode, sign, info)
    coll = _collection(part, colls)
    coll.objects.link(obj)
    if kind == 'block':
        z0, z1 = _zr(part)
        _block_label(obj, part, coll, mats, (z1 - z0) - 0.2)
    st = STATS.setdefault(kind, {'n': 0, 'built': 0, 'shared': 0, 's': 0.0})
    st['n'] += 1
    st['shared' if shared else 'built'] += 1
    st['s'] += time.perf_counter() - t0
    return obj


def reset_cache():
    """Oublie les maillages partagés et les statistiques (nouvelle scène)."""
    _MESH_CACHE.clear()
    STATS.clear()
    _SUPPORTS.update(index=None, n=-1, list=[])


def stats_text():
    """Résumé des temps de construction par sorte de pièce."""
    rows = ['%-6s %4d objets, %4d maillages, %4d partagés, %7.3f s' % (k, v['n'], v['built'], v['shared'], v['s'])
            for k, v in sorted(STATS.items())]
    return '\n'.join(rows)
