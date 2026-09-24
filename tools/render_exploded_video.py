"""Exploded-view video (in memory, never saves the .blend).
Blender -b out/am.blend --python-exit-code 1 -P render_exploded_video.py -- frames <start> <end> [--staging <staging.py>]
Blender -b out/am.blend --python-exit-code 1 -P render_exploded_video.py -- encode
Timeline (24 fps, 360 frames = 15 s): 1-48 assembled | 48-144 opens | 144-264 exploded, gears turning | 264-336 closes | 336-360 assembled.
The crank turns 0 -> 2 years over the whole clip; the camera orbits 90 deg and pulls back while the mechanism opens."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parent.parent)   # repository root
import bpy, math, os, sys
sys.path.insert(0, f'{ROOT}/build/blender_scripts')
import render  # noqa: E402
from bpy_extras import anim_utils
OUT = f'{ROOT}/build/out/renders'
FR = os.path.join(OUT, 'frames_exploded'); N = 360
SAMPLES = int(os.environ.get('AM_SAMPLES', '64'))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []

def setup_scene(staging=None):
    sc = bpy.context.scene
    st = None
    if staging:
        import importlib.util
        spec = importlib.util.spec_from_file_location('staging', staging); st = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(st); st.apply(sc)
    render.set_visibility('exploded')
    for ob in bpy.data.objects:          # the wooden case never shows in the exploded clip
        if ob.name.startswith('case_'): ob.hide_render = True
    ctl = bpy.data.objects['AM_Controller']
    ad = ctl.animation_data or ctl.animation_data_create()
    act = bpy.data.actions.new('AM_exploded_clip'); ad.action = act
    ctl['patina'] = 0.06
    for f, v in ((1, 0.0), (N, 2.0)):
        ctl['crank'] = v; ctl.keyframe_insert('["crank"]', frame=f)
    for f, v in ((1, 0.0), (48, 0.0), (144, 1.0), (264, 1.0), (336, 0.0), (N, 0.0)):
        ctl['explode'] = v; ctl.keyframe_insert('["explode"]', frame=f)
    cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
    for fc in cb.fcurves:
        if 'crank' in fc.data_path:
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
        else:
            for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
        fc.update()
    # camera rig: pivot (orbit) + target (rises with the exploded stack) + camera (pulls back)
    for n in ('XCAM_pivot', 'XCAM_target', 'XCAM'):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    coll = bpy.data.collections['AM_HELPERS']
    piv = bpy.data.objects.new('XCAM_pivot', None); coll.objects.link(piv); piv.location = (0.0, -10.0, 0.0)
    tgt = bpy.data.objects.new('XCAM_target', None); coll.objects.link(tgt)
    cam = bpy.data.objects.new('XCAM', bpy.data.cameras.new('XCAM')); coll.objects.link(cam)
    cam.data.lens = 45.0; cam.data.clip_start = 1.0; cam.data.clip_end = 10000.0
    cam.parent = piv
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    for f, a in ((1, 10.0), (N, 80.0)):
        piv.rotation_euler = (0, 0, math.radians(a)); piv.keyframe_insert('rotation_euler', index=2, frame=f)
    for f, (z, d, h) in ((1, (18.0, 470.0, 300.0)), (48, (18.0, 470.0, 300.0)), (144, (58.0, 720.0, 150.0)),
                         (264, (58.0, 720.0, 150.0)), (336, (18.0, 470.0, 300.0)), (N, (18.0, 470.0, 300.0))):
        tgt.location = (0.0, -10.0, z); tgt.keyframe_insert('location', index=2, frame=f)
        cam.location = (0.0, -d, h); cam.keyframe_insert('location', frame=f)
    for ob in (piv,):
        cbp = anim_utils.action_get_channelbag_for_slot(ob.animation_data.action, ob.animation_data.action_slot)
        for fc in cbp.fcurves:
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    sc.camera = cam; sc.frame_start, sc.frame_end = 1, N
    return sc, st

def frames(a, b, staging):
    sc, st = setup_scene(staging)
    render.engine_setup(sc, 'eevee', res=(1280, 720))
    if st is not None:
        st.finish(sc, 'eevee'); st.stage_visibility('exploded')
        sc.eevee.taa_render_samples = SAMPLES
    os.makedirs(FR, exist_ok=True)
    for f in range(a, b + 1):
        sc.frame_set(f); sc.render.filepath = os.path.join(FR, 'x_%04d.png' % f)
        bpy.ops.render.render(write_still=True)
    print('[xvideo] frames', a, b, 'done')

def encode():
    enc = bpy.data.scenes.new('encode_x'); r = enc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1280, 720, 100, 24
    enc.frame_start, enc.frame_end = 1, N
    se = enc.sequence_editor_create()
    st = se.strips.new_image(name='x', filepath=os.path.join(FR, 'x_0001.png'), channel=1, frame_start=1)
    for f in range(2, N + 1): st.elements.append('x_%04d.png' % f)
    r.use_sequencer = True
    r.image_settings.media_type = 'VIDEO'; r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'; r.ffmpeg.constant_rate_factor = 'HIGH'
    r.filepath = os.path.join(OUT, 'antikythera_eclate.mp4')
    with bpy.context.temp_override(scene=enc): bpy.ops.render.render(animation=True, scene=enc.name)
    clip = bpy.data.movieclips.load(r.filepath)
    print('[xvideo] encoded', r.filepath, 'frames', clip.frame_duration)

staging = argv[argv.index('--staging') + 1] if '--staging' in argv else None
if argv and argv[0] == 'frames': frames(int(argv[1]), int(argv[2]), staging)
elif argv and argv[0] == 'encode': encode()
