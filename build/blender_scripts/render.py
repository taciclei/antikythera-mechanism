"""Cameras/lights (used by build.py) and rendering (step 8).
Run: Blender -b --factory-startup --python-exit-code 1 -P blender_scripts/render.py -- <mode> [args]
 modes: stills [warmup|front34|front|back|exploded|all] [cycles|eevee]
        frames <start> <end>        (EEVEE PNG frames into out/renders/frames)
        encode                      (sequencer -> out/renders/antikythera.mp4)
        verify                      (movie clip frame count)"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bootstrap  # noqa: E402
from bootstrap import OUT, log  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

CENTER = Vector((0.0, -10.0, 15.0))
CAMS = {
    'front34': {'loc': (215.0, -265.0, 185.0), 'target': (0.0, -18.0, 12.0), 'lens': 50.0},
    'front': {'loc': (0.0, 0.0, 420.0), 'target': (0.0, 0.0, 0.0), 'ortho': 290.0},
    'back': {'loc': (0.0, -10.0, -420.0), 'target': (0.0, -10.0, 0.0), 'ortho': 335.0},
    'exploded': {'loc': (440.0, -570.0, 290.0), 'target': (0.0, -10.0, 42.0), 'lens': 40.0},
}


def look_at(ob, target, up=(0, 1, 0)):
    d = Vector(target) - ob.location
    rot = d.to_track_quat('-Z', 'Y')
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = rot
    ob.rotation_mode = 'XYZ'


def setup_cameras_lights(sc, coll):
    for name, c in CAMS.items():
        cam = bpy.data.cameras.new('CAM_' + name)
        cam.clip_start = 1.0
        cam.clip_end = 10000.0
        if 'ortho' in c:
            cam.type = 'ORTHO'
            cam.ortho_scale = c['ortho']
        else:
            cam.lens = c['lens']
        ob = bpy.data.objects.new('CAM_' + name, cam)
        coll.objects.link(ob)
        ob.location = c['loc']
        if name == 'back':
            ob.rotation_euler = (0.0, math.pi, math.pi / 2)
        elif name == 'front':
            ob.rotation_euler = (0.0, 0.0, 0.0)
        else:
            look_at(ob, c['target'])
    sc.camera = bpy.data.objects['CAM_front34']
    for name, loc, energy, size in (('LIGHT_key', (250, -200, 400), 2.0e6, 200.0),
                                    ('LIGHT_fill', (-300, -100, 250), 7.0e5, 300.0),
                                    ('LIGHT_back', (-100, 250, -350), 9.0e5, 300.0),
                                    ('LIGHT_rim', (300, 300, 100), 5.0e5, 150.0)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.size = size
        ob = bpy.data.objects.new(name, ld)
        coll.objects.link(ob)
        ob.location = loc
        look_at(ob, (0, -10, 10))
    w = bpy.data.worlds.new('AM_world')
    w.color = (0.03, 0.03, 0.035)
    bg = next((n for n in w.node_tree.nodes if n.type == 'BACKGROUND'), None)
    if bg:
        bg.inputs['Color'].default_value = (0.22, 0.22, 0.24, 1.0)
        bg.inputs['Strength'].default_value = 1.0
    sc.world = w


def set_visibility(mode):
    """Hide case covers always; hide the whole case for dial and exploded views."""
    for ob in bpy.data.objects:
        if ob.name.startswith('case_cover'):
            ob.hide_render = True
        elif ob.name.startswith('case_'):
            ob.hide_render = mode in ('front34', 'front', 'back', 'exploded', 'anim')


def explode(factor=3.0):
    """Exploded view: every part moved so that its z becomes factor * z (by layer)."""
    import numpy as np
    for ob in bpy.data.objects:
        if ob.type not in ('MESH', 'FONT') or ob.parent is None:
            continue
        if ob.type == 'MESH':
            co = np.empty(len(ob.data.vertices) * 3, np.float32)
            ob.data.vertices.foreach_get('co', co)
            co = co.reshape(-1, 3)
            M = ob.matrix_world
            zc = (M @ Vector(co.mean(0).tolist())).z
        else:
            zc = ob.matrix_world.translation.z
        dz = (factor - 1.0) * zc
        mw = ob.matrix_world.copy()
        mw.translation.z += dz
        ob.matrix_world = mw


def engine_setup(sc, engine, samples=256, res=(1920, 1080)):
    r = sc.render
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.image_settings.media_type = 'IMAGE'
    r.image_settings.file_format = 'PNG'
    if engine == 'cycles':
        r.engine = 'CYCLES'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        n = 0
        for d in prefs.devices:
            d.use = d.type == 'METAL'
            n += d.use
        sc.cycles.device = 'GPU' if n else 'CPU'
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        sc.cycles.denoising_use_gpu = True
        log('cycles devices:', [(d.name, d.type, d.use) for d in prefs.devices])
        return n > 0
    r.engine = 'BLENDER_EEVEE'
    try:
        sc.eevee.taa_render_samples = 32
    except AttributeError:
        pass
    return True


def stills(which, engine, pct=100):
    sc = bpy.context.scene
    ok = engine_setup(sc, engine)
    if engine == 'cycles' and not ok:
        log('METAL unavailable -> CPU')
    os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)
    names = ['front34', 'front', 'back', 'exploded'] if which == 'all' else [which]
    for name in names:
        if name == 'warmup':
            sc.render.resolution_percentage = 10
            sc.camera = bpy.data.objects['CAM_front34']
            set_visibility('front34')
            sc.render.filepath = os.path.join(OUT, 'renders', '_warmup.png')
            bpy.ops.render.render(write_still=True)
            continue
        sc.render.resolution_percentage = pct
        set_visibility(name)
        ctl = bpy.data.objects['AM_Controller']
        if ctl.animation_data:
            ctl.animation_data.action = None
        ctl['crank'] = 0.37
        ctl['patina'] = 0.06
        ctl.update_tag()
        bpy.context.view_layer.update()
        if name == 'exploded':
            explode(3.0)
        sc.camera = bpy.data.objects['CAM_' + name]
        sc.render.filepath = os.path.join(OUT, 'renders', ('%s.png' if pct == 100 else 'preview_%s.png') % name)
        bpy.ops.render.render(write_still=True)
        log('rendered', sc.render.filepath)


def frames(start, end):
    sc = bpy.context.scene
    engine_setup(sc, 'eevee', res=(1280, 720))
    set_visibility('front34')
    sc.camera = bpy.data.objects['CAM_front34']
    d = os.path.join(OUT, 'renders', 'frames')
    os.makedirs(d, exist_ok=True)
    for f in range(start, end + 1):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(d, 'f_%04d.png' % f)
        bpy.ops.render.render(write_still=True)
    log('frames', start, end, 'done')


def encode():
    d = os.path.join(OUT, 'renders', 'frames')
    src = bpy.context.scene
    enc = bpy.data.scenes.new('encode')
    enc.render.resolution_x = 1280
    enc.render.resolution_y = 720
    enc.render.resolution_percentage = 100
    enc.render.fps = 24
    enc.frame_start, enc.frame_end = 1, 480
    se = enc.sequence_editor_create()
    st = se.strips.new_image(name='f', filepath=os.path.join(d, 'f_0001.png'), channel=1, frame_start=1)
    for f in range(2, 481):
        st.elements.append('f_%04d.png' % f)
    enc.render.use_sequencer = True
    r = enc.render
    r.image_settings.media_type = 'VIDEO'
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'HIGH'
    r.filepath = os.path.join(OUT, 'renders', 'antikythera.mp4')
    with bpy.context.temp_override(scene=enc):
        bpy.ops.render.render(animation=True, scene=enc.name)
    del src
    log('encoded', r.filepath)


def verify():
    path = os.path.join(OUT, 'renders', 'antikythera.mp4')
    clip = bpy.data.movieclips.load(path)
    log('movie frames', clip.frame_duration)
    if clip.frame_duration != 480:
        sys.exit(1)


if __name__ == '__main__':
    a = bootstrap.args()
    mode = a[0] if a else 'stills'
    if mode in ('stills', 'frames'):
        bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'am.blend'))
    if mode == 'stills':
        stills(a[1] if len(a) > 1 else 'all', a[2] if len(a) > 2 else 'cycles', int(a[3]) if len(a) > 3 else 100)
    elif mode == 'frames':
        frames(int(a[1]), int(a[2]))
    elif mode == 'encode':
        encode()
    elif mode == 'verify':
        verify()
