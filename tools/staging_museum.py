"""MUSEE (low-key) staging for the Antikythera Mechanism scene (Blender 5.2, 1 BU = 1 mm).

Dark charcoal seamless cyclorama, warm key softbox from the upper left, cool rim strip to
outline the edges, soft fill, a subtle warm pool of light on the dial, a dark "museum room"
world whose non-camera part gives the bronze something warm to reflect, AgX colour
management and quality EEVEE settings.

Idempotent: everything lives in the collection AM_STAGE (and datablocks prefixed STAGE_),
which is removed and rebuilt on every run.  The old LIGHT_* objects are disabled
(hide_render + hide_viewport), never deleted.  Nothing of the mechanism (drivers, B_*
bodies, parts, constraints) is touched; only the shared AM_bronze roughness and the
AM_Controller["patina"] default are adjusted.

Usage
  "$BL" -b am.blend -P staging.py                       (applies the staging in memory)
  import staging; staging.apply(bpy.context.scene)      (from another script)
  staging.stage_visibility(mode)                        before each render
     mode in 'front34' | 'front' | 'back' | 'exploded' | 'anim' | 'case' ...
  staging.finish(scene, 'eevee'|'cycles') must run AFTER render.engine_setup() (which
  resets taa_render_samples to 32): EEVEE quality settings, or the Cycles exposure
  offset.  apply() already calls tune_eevee() once.
  Lights use the mode-specific rig: 'front' swaps the dial pool spot for a zenith spot
  (the ortho camera sees the plate reflect the zenith), 'back' hides the backdrop and all
  top lights and uses two under-lights; every other mode uses the front34 rig.
Call apply() on the assembled mechanism (before render.explode()); the ground is placed
below the lowest point of the assembled AND the 3x exploded mechanism, so it never
intersects the mechanism for any explode factor between 1 and 3 (z moves linearly).
"""
import math

import bpy
import numpy as np
from mathutils import Vector

STAGE = 'AM_STAGE'
PREFIX = 'STAGE_'
GAP = 6.0                 # mm between the lowest part and the ground
EXPLODE_FACTOR = 3.0      # render.explode() default
CENTER = Vector((0.0, -10.0, 20.0))

# look / grade
VIEW_TRANSFORM = 'AgX'
LOOK = 'AgX - High Contrast'
EXPOSURE = 0.0
# Cycles shows the big softboxes' GGX tails ~2x brighter than EEVEE's LTC area lights
# (measured on the plate at equal settings): finish(scene, 'cycles') compensates.
CYCLES_EXPOSURE_OFFSET = -1.0
BRONZE_ROUGHNESS = 0.30   # was 0.35: crisper highlights
PATINA = 0.06             # default patina kept (stills use 0.06)
EEVEE_SAMPLES = 32        # = render.engine_setup() default; ~2 s / 1280x720 frame on M4

# cyclorama (azimuth of the "back" of the room = mean viewing direction of the cameras)
CYC_AZIMUTH = math.degrees(math.atan2(0.771, -0.637))   # ~129.6 deg
CYC_WALL = 420.0          # horizontal distance centre -> start of the sweep
CYC_RADIUS = 260.0        # sweep radius
CYC_FRONT = 1800.0        # floor length towards the cameras
CYC_HEIGHT = 1400.0       # wall height above the floor
CYC_WIDTH = 3200.0

# colours
CHARCOAL = (0.034, 0.031, 0.029, 1.0)       # linear, warm charcoal
WORLD_CAMERA = (0.0045, 0.0044, 0.0045, 1.0)


# ----------------------------------------------------------------------------- helpers
def _log(*a):
    print('[stage]', *a, flush=True)


def _look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def _dir(az_deg, el_deg):
    a, e = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def _stage_collection(scene):
    coll = bpy.data.collections.new(STAGE)
    scene.collection.children.link(coll)
    return coll


def remove_stage():
    """Remove a previous AM_STAGE collection and every STAGE_ datablock."""
    coll = bpy.data.collections.get(STAGE)
    if coll:
        for ob in list(coll.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(coll)
    for ob in [o for o in bpy.data.objects if o.name.startswith(PREFIX)]:
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in [c for c in bpy.data.collections if c.name.startswith(PREFIX)]:
        bpy.data.collections.remove(c)
    for w in [w for w in bpy.data.worlds if w.name.startswith(PREFIX)]:
        bpy.data.worlds.remove(w)          # also when still assigned to the scene
    for bank in (bpy.data.lights, bpy.data.meshes, bpy.data.materials, bpy.data.worlds):
        for idb in [i for i in bank if i.name.startswith(PREFIX) and i.users == 0]:
            bank.remove(idb)


# ----------------------------------------------------------------------------- ground height
def _world_z_min(ob, dg):
    ev = ob.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        return None
    n = len(me.vertices)
    if n == 0:
        ev.to_mesh_clear()
        return None
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world)
    return float((co @ M[2, :3] + M[2, 3]).min())


def _explode_dz(ob, factor):
    """Same displacement as render.explode(factor) (parented MESH/FONT only)."""
    if ob.type not in ('MESH', 'FONT') or ob.parent is None:
        return 0.0
    if ob.type == 'MESH':
        n = len(ob.data.vertices)
        if n == 0:
            return 0.0
        co = np.empty(n * 3, np.float32)
        ob.data.vertices.foreach_get('co', co)
        zc = (ob.matrix_world @ Vector(co.reshape(-1, 3).mean(0).tolist())).z
    else:
        zc = ob.matrix_world.translation.z
    return (factor - 1.0) * zc


def lowest_points(scene, factor=EXPLODE_FACTOR):
    """Lowest z of the render-visible mechanism at crank 0: (assembled, exploded).
    The case (hidden in most modes) is included as well, so the ground is also safe in
    the 'case' views."""
    ctl = bpy.data.objects.get('AM_Controller')
    saved = None
    if ctl is not None:
        ad = ctl.animation_data
        saved = (ad.action if ad else None, ctl.get('crank', 0.0), scene.frame_current)
        if ad:
            ad.action = None
        ctl['crank'] = 0.0
        ctl.update_tag()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    z_asm = z_exp = float('inf')
    for ob in scene.objects:
        if ob.type not in ('MESH', 'FONT') or ob.name.startswith(PREFIX):
            continue
        if ob.name.startswith('case_cover'):
            continue          # render.set_visibility() always hides the covers
        if ob.hide_render and not ob.name.startswith('case_'):
            continue          # the case walls count: they are shown in the 'case' views
        z = _world_z_min(ob, dg)
        if z is None:
            continue
        z_asm = min(z_asm, z)
        z_exp = min(z_exp, z + _explode_dz(ob, factor))
    if ctl is not None:
        action, crank, frame = saved
        if action is not None:
            ctl.animation_data.action = action
        ctl['crank'] = crank
        ctl.update_tag()
        scene.frame_set(frame)
    bpy.context.view_layer.update()
    return z_asm, z_exp


# ----------------------------------------------------------------------------- cyclorama
def _cyclorama_mesh(name):
    """Floor + quarter-circle sweep + wall, in local space: u towards the back wall, v width,
    z up; floor at z=0; sweep starts at u=CYC_WALL."""
    prof = []
    for i in range(12):
        prof.append((-CYC_FRONT + (CYC_FRONT + CYC_WALL) * i / 11.0, 0.0))
    n_arc = 24
    for i in range(1, n_arc + 1):
        t = (math.pi / 2) * i / n_arc
        prof.append((CYC_WALL + CYC_RADIUS * math.sin(t), CYC_RADIUS * (1.0 - math.cos(t))))
    for i in range(1, 9):
        prof.append((CYC_WALL + CYC_RADIUS, CYC_RADIUS + (CYC_HEIGHT - CYC_RADIUS) * i / 8.0))
    nv = 16
    vs = [(-CYC_WIDTH / 2 + CYC_WIDTH * j / nv) for j in range(nv + 1)]
    verts = [(u, v, z) for (u, z) in prof for v in vs]
    faces = []
    w = nv + 1
    for i in range(len(prof) - 1):
        for j in range(nv):
            a = i * w + j
            faces.append((a, a + 1, a + w + 1, a + w))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    # UVs not needed; the material is procedural
    return me


def _charcoal_material():
    mat = bpy.data.materials.new(PREFIX + 'charcoal')
    nt = mat.node_tree
    pb = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    pb.inputs['Base Color'].default_value = CHARCOAL
    pb.inputs['Roughness'].default_value = 0.62
    pb.inputs['Specular IOR Level'].default_value = 0.35
    # faint fabric-like grain so the dark gradients never band
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.35
    nz.inputs['Detail'].default_value = 8.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = 0.55
    mr.inputs['To Max'].default_value = 0.72
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], pb.inputs['Roughness'])
    return mat


def build_cyclorama(coll, ground_z):
    me = _cyclorama_mesh(PREFIX + 'cyclorama')
    me.materials.append(_charcoal_material())
    ob = bpy.data.objects.new(PREFIX + 'cyclorama', me)
    coll.objects.link(ob)
    ob.location = (CENTER.x, CENTER.y, ground_z)
    ob.rotation_euler = (0.0, 0.0, math.radians(CYC_AZIMUTH))
    # Cycles: the backdrop is not seen in glossy rays so the bronze reflects the designed
    # museum-room world (as EEVEE does through its world probe) -> both engines match.
    ob.visible_glossy = False
    ob.hide_probe_sphere = True
    return ob


# ----------------------------------------------------------------------------- lights
# Each light: type, azimuth/elevation (deg) + distance (mm) from its target, power (W, mm
# scene), colour temperature (K); optional spec/diff factors, 'only' (mode that uses it),
# floor=True (light-linked to the backdrop only) or nofloor=True (backdrop excluded).  Metal only shows specular, so the
# powers are set from the radiance each source shows in reflection (~P / (pi * area)).
RIG = {
    # warm key softbox from the upper left: broad warm gradient over the left of the
    # plate, highlights on everything facing up-left (pillars, teeth, crank, moon arm)
    'key': dict(type='AREA', az=188.0, el=44.0, dist=600.0, target=(0.0, -10.0, 0.0),
                energy=4.0e5, kelvin=3300, size=(480.0, 300.0)),
    # cool rim strip behind-right, low: outlines teeth, plate edges and pointers
    'rim': dict(type='AREA', az=72.0, el=12.0, dist=520.0, target=(0.0, -10.0, 10.0),
                energy=4.0e5, kelvin=9500, size=(520.0, 70.0),
                nofloor=True),
    # second cool rim from the far left
    'rim2': dict(type='AREA', az=215.0, el=12.0, dist=520.0, target=(0.0, -10.0, 10.0),
                 energy=1.6e5, kelvin=9000, size=(420.0, 60.0),
                 nofloor=True),
    # soft fill from the camera side (front-right), large and weak
    'fill': dict(type='AREA', az=-40.0, el=30.0, dist=650.0, target=(0.0, -10.0, 10.0),
                 energy=9.0e4, kelvin=5000, size=(700.0, 500.0)),
    # subtle warm pool on the dial: spot at the mirror direction of the front34 camera,
    # so its blurred reflection sits on the centre of the front dial
    'pool': dict(type='SPOT', az=129.6, el=30.0, dist=620.0, target=(0.0, 0.0, 0.0),
                 energy=3.0e5, kelvin=2900, radius=45.0, spot=26.0, blend=0.85),
    # warm spot from straight above, 'front' view only: the ortho camera sees the plate
    # reflect the zenith, so this big soft spot becomes the warm pool on the dial
    'top': dict(type='SPOT', loc=(-35.0, 10.0, 650.0), target=(-35.0, 10.0, 0.0),
                energy=2.5e5, kelvin=3000, radius=25.0, spot=40.0, blend=0.9, only='front'),
    # large dim warm wash low behind the object (a lit museum wall): every horizontal
    # plate seen from the front34 / exploded cameras reflects it as a soft warm sheen
    'wash': dict(type='AREA', az=130.0, el=22.0, dist=650.0, target=(0.0, -10.0, 20.0),
                 energy=4.0e5, kelvin=3000, size=(900.0, 260.0)),
    # warm pool of light on the charcoal floor around the object (backdrop only)
    'floorpool': dict(type='SPOT', az=150.0, el=78.0, dist=900.0, target=(0.0, -10.0, 0.0),
                      energy=6.0e6, kelvin=3000, radius=80.0, spot=48.0, blend=1.0, floor=True),
    # exploded view only: soft fill from the camera side and a soft top light aimed at the centre of
    # the opened stack, so the gear layers between the plates stay readable (added for the exploded video)
    'xfill': dict(type='AREA', az=-70.0, el=22.0, dist=720.0, target=(0.0, -10.0, 60.0),
                  energy=3.3e5, kelvin=3500, size=(800.0, 600.0), only='exploded', nofloor=True),
    'xtop': dict(type='AREA', az=150.0, el=68.0, dist=720.0, target=(0.0, -10.0, 60.0),
                 energy=3.5e5, kelvin=3300, size=(600.0, 600.0), only='exploded', nofloor=True),
    # under-lights for the 'back' view only (from -z)
    'under_key': dict(type='AREA', az=200.0, el=-62.0, dist=600.0, target=(0.0, -10.0, -18.0),
                      energy=9.0e5, kelvin=3300, size=(520.0, 360.0), only='back'),
    'under_rim': dict(type='AREA', az=20.0, el=-20.0, dist=520.0, target=(0.0, -10.0, -18.0),
                      energy=4.0e5, kelvin=9000, size=(520.0, 80.0), only='back'),
}


def build_lights(coll, backdrop):
    # light-linking collections (not linked to the scene)
    receivers = bpy.data.collections.new(PREFIX + 'floor_only')
    receivers.objects.link(backdrop)
    excluders = bpy.data.collections.new(PREFIX + 'floor_excluded')
    excluders.objects.link(backdrop)
    excluders.collection_objects[0].light_linking.link_state = 'EXCLUDE'
    obs = {}
    for key, c in RIG.items():
        name = PREFIX + key
        ld = bpy.data.lights.new(name, c['type'])
        ld.energy = c['energy']
        ld.use_temperature = True
        ld.temperature = c['kelvin']
        ld.color = (1.0, 1.0, 1.0)
        ld.use_shadow = True
        ld.specular_factor = c.get('spec', 1.0)
        ld.diffuse_factor = c.get('diff', 1.0)
        if c['type'] == 'AREA':
            ld.shape = 'RECTANGLE'
            ld.size, ld.size_y = c['size']
            # keep the full 180 deg spread: EEVEE ignores 'spread' while Cycles
            # concentrates the power (x2.4 on axis at 120 deg) -> engines would disagree
            ld.spread = math.pi
        else:
            ld.shadow_soft_size = c['radius']
            ld.spot_size = math.radians(c['spot'])
            ld.spot_blend = c['blend']
        ob = bpy.data.objects.new(name, ld)
        coll.objects.link(ob)
        tgt = Vector(c['target'])
        if 'loc' in c:
            ob.location = c['loc']
        else:
            ob.location = tgt + _dir(c['az'], c['el']) * c['dist']
        _look_at(ob, tgt)
        ob.visible_camera = False
        ob['stage_only'] = c.get('only', '')
        if c.get('floor'):
            ob.light_linking.receiver_collection = receivers
        elif c.get('nofloor'):
            ob.light_linking.receiver_collection = excluders   # no cold streak on the floor
        obs[key] = ob
    return obs


def disable_old_lights():
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT' and ob.name.startswith('LIGHT_'):
            ob.hide_render = True
            ob.hide_viewport = True


# ----------------------------------------------------------------------------- world
def build_world(scene):
    """Camera rays: near-black charcoal.  Other rays (reflections / world lighting): a dark
    room with a warm overhead diffuser glow and a faint warm horizon band, so rough
    bronze never reflects a flat grey."""
    w = bpy.data.worlds.new(PREFIX + 'world')
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    out = N.new('ShaderNodeOutputWorld')
    out.location = (900, 0)
    tc = N.new('ShaderNodeTexCoord')
    tc.location = (-900, 0)
    sep = N.new('ShaderNodeSeparateXYZ')
    sep.location = (-700, 0)
    L.new(tc.outputs['Generated'], sep.inputs['Vector'])
    # overhead diffuser: smoothstep on the up component
    dome = N.new('ShaderNodeMapRange')
    dome.location = (-500, 150)
    dome.interpolation_type = 'SMOOTHSTEP'
    dome.inputs['From Min'].default_value = 0.35
    dome.inputs['From Max'].default_value = 0.95
    L.new(sep.outputs['Z'], dome.inputs['Value'])
    # horizon band (|z| small) -> faint warm wall glow
    absz = N.new('ShaderNodeMath')
    absz.operation = 'ABSOLUTE'
    absz.location = (-500, -100)
    L.new(sep.outputs['Z'], absz.inputs[0])
    band = N.new('ShaderNodeMapRange')
    band.location = (-300, -100)
    band.interpolation_type = 'SMOOTHSTEP'
    band.inputs['From Min'].default_value = 0.35
    band.inputs['From Max'].default_value = 0.0
    L.new(absz.outputs[0], band.inputs['Value'])
    # colours
    base = (0.006, 0.0058, 0.0056, 1.0)
    mix1 = N.new('ShaderNodeMix')
    mix1.data_type = 'RGBA'
    mix1.location = (-100, 150)
    mix1.inputs['A'].default_value = base
    mix1.inputs['B'].default_value = (0.07, 0.052, 0.036, 1.0)
    L.new(dome.outputs['Result'], mix1.inputs['Factor'])
    band_s = N.new('ShaderNodeMath')
    band_s.operation = 'MULTIPLY'
    band_s.location = (-100, -100)
    band_s.inputs[1].default_value = 0.35
    L.new(band.outputs['Result'], band_s.inputs[0])
    mix2 = N.new('ShaderNodeMix')
    mix2.data_type = 'RGBA'
    mix2.location = (100, 100)
    mix2.inputs['B'].default_value = (0.05, 0.036, 0.024, 1.0)
    L.new(mix1.outputs['Result'], mix2.inputs['A'])
    L.new(band_s.outputs[0], mix2.inputs['Factor'])
    bg_ref = N.new('ShaderNodeBackground')
    bg_ref.location = (350, 100)
    bg_ref.inputs['Strength'].default_value = 1.0
    L.new(mix2.outputs['Result'], bg_ref.inputs['Color'])
    bg_cam = N.new('ShaderNodeBackground')
    bg_cam.location = (350, -150)
    bg_cam.inputs['Color'].default_value = WORLD_CAMERA
    bg_cam.inputs['Strength'].default_value = 1.0
    lp = N.new('ShaderNodeLightPath')
    lp.location = (350, 350)
    mix = N.new('ShaderNodeMixShader')
    mix.location = (650, 0)
    L.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    L.new(bg_ref.outputs['Background'], mix.inputs[1])
    L.new(bg_cam.outputs['Background'], mix.inputs[2])
    L.new(mix.outputs['Shader'], out.inputs['Surface'])
    w.color = WORLD_CAMERA[:3]
    # EEVEE world probe: no sun extraction (the world is dim and soft)
    w.sun_threshold = 0.0
    w.probe_resolution = '1024'
    old = scene.world
    if old is not None and not old.name.startswith(PREFIX):
        old.use_fake_user = True          # keep AM_world if the file is ever saved
    scene.world = w
    return w


# ----------------------------------------------------------------------------- render settings
def colour_management(scene):
    vs = scene.view_settings
    scene.display_settings.display_device = 'sRGB'
    vs.view_transform = VIEW_TRANSFORM
    try:
        vs.look = LOOK
    except TypeError:
        _log('look not available:', LOOK)
    vs.exposure = EXPOSURE
    vs.gamma = 1.0
    vs.use_curve_mapping = False
    scene.sequencer_colorspace_settings.name = 'sRGB'


def _set(obj, attr, value):
    if hasattr(obj, attr):
        try:
            setattr(obj, attr, value)
            return True
        except (TypeError, ValueError, AttributeError) as ex:
            _log('cannot set', attr, ex)
    else:
        _log('missing property', attr)
    return False


def tune_eevee(scene, samples=EEVEE_SAMPLES):
    """EEVEE (5.2) quality settings, scaled for a millimetre scene.  Call after
    render.engine_setup() (which forces taa_render_samples = 32)."""
    e = scene.eevee
    _set(e, 'taa_render_samples', samples)
    _set(e, 'taa_samples', 16)
    _set(e, 'use_taa_reprojection', True)
    # screen-space ray tracing for the bronze reflections (rough ones fall back to probes)
    _set(e, 'use_raytracing', True)
    _set(e, 'ray_tracing_method', 'SCREEN')
    rt = e.ray_tracing_options
    _set(rt, 'resolution_scale', '1')
    _set(rt, 'trace_max_roughness', 0.55)
    _set(rt, 'screen_trace_quality', 0.6)
    _set(rt, 'screen_trace_thickness', 2.0)      # mm
    _set(rt, 'use_denoise', True)
    _set(rt, 'denoise_spatial', True)
    _set(rt, 'denoise_temporal', True)
    _set(rt, 'denoise_bilateral', True)
    # horizon scan GI / AO (fast GI), distances in mm
    _set(e, 'use_fast_gi', True)
    _set(e, 'fast_gi_method', 'GLOBAL_ILLUMINATION')
    _set(e, 'fast_gi_resolution', '2')
    _set(e, 'fast_gi_step_count', 8)
    _set(e, 'fast_gi_ray_count', 2)
    _set(e, 'fast_gi_quality', 0.5)
    _set(e, 'fast_gi_distance', 60.0)
    _set(e, 'fast_gi_thickness_near', 3.0)
    _set(e, 'fast_gi_bias', 0.05)
    # virtual shadow maps
    _set(e, 'use_shadows', True)
    _set(e, 'shadow_pool_size', '1024')
    # 1 ray x 16 steps: the default 2 x 8 over-occludes the large softboxes at this
    # scale (plates came out ~40 % too dark vs Cycles); more steps fix it, 1 ray is enough
    _set(e, 'shadow_ray_count', 1)
    _set(e, 'shadow_step_count', 16)
    _set(e, 'shadow_resolution_scale', 1.0)
    _set(e, 'light_threshold', 0.01)
    _set(e, 'clamp_surface_indirect', 10.0)
    scene.render.filter_size = 1.5
    scene.render.film_transparent = False


def finish(scene, engine=None):
    """Call after render.engine_setup(): engine-specific settings + exposure."""
    if engine is None:
        engine = 'cycles' if scene.render.engine == 'CYCLES' else 'eevee'
    if engine == 'cycles':
        cy = scene.cycles
        _set(cy, 'sample_clamp_indirect', 10.0)
        _set(cy, 'blur_glossy', 1.0)
        scene.view_settings.exposure = EXPOSURE + CYCLES_EXPOSURE_OFFSET
    else:
        tune_eevee(scene)
        scene.view_settings.exposure = EXPOSURE


def bronze_tweak():
    mat = bpy.data.materials.get('AM_bronze')
    if mat is None:
        return
    pb = mat.node_tree.nodes.get('Principled BSDF')
    if pb is not None and pb.type == 'BSDF_PRINCIPLED':
        pb.inputs['Roughness'].default_value = BRONZE_ROUGHNESS
    ctl = bpy.data.objects.get('AM_Controller')
    if ctl is not None:
        ctl['patina'] = PATINA


# ----------------------------------------------------------------------------- visibility
def stage_visibility(mode):
    """Per-view stage state.  The backdrop and the top lights are hidden for the 'back'
    camera (it looks up from -z through where the ground is); the under-lights are only
    used for 'back'."""
    coll = bpy.data.collections.get(STAGE)
    if coll is None:
        return
    back = mode == 'back'
    # list(): changing hide_viewport invalidates the all_objects cache while iterating
    for ob in list(coll.all_objects):
        only = ob.get('stage_only', '')
        if ob.type == 'MESH':
            hide = back
        elif only:
            hide = only != mode
        else:
            hide = back
        ob.hide_render = hide
        ob.hide_viewport = hide
    # ortho front view: the plate reflects the zenith, so the 'top' spot (only='front')
    # makes the pool there; the perspective views get it from the 'pool' spot.
    pool = bpy.data.objects.get(PREFIX + 'pool')
    if pool is not None and not back:
        pool.hide_render = pool.hide_viewport = mode == 'front'


# ----------------------------------------------------------------------------- entry point
def apply(scene=None, ground_z=None):
    scene = scene or bpy.context.scene
    remove_stage()
    coll = _stage_collection(scene)
    if ground_z is None:
        z_asm, z_exp = lowest_points(scene)
        ground_z = min(z_asm, z_exp) - GAP
        _log('lowest z assembled %.2f exploded(x%.0f) %.2f -> ground %.2f'
             % (z_asm, EXPLODE_FACTOR, z_exp, ground_z))
    scene['am_stage_ground_z'] = ground_z
    backdrop = build_cyclorama(coll, ground_z)
    build_lights(coll, backdrop)
    disable_old_lights()
    build_world(scene)
    colour_management(scene)
    tune_eevee(scene)
    bronze_tweak()
    stage_visibility('front34')
    bpy.context.view_layer.update()
    return coll


if __name__ == '__main__':
    apply(bpy.context.scene)
