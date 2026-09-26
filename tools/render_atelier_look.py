"""Preview stills of the ATELIER look (tools/staging_atelier.py) + comparison with the museum look.
Never saves any .blend.  Output: build/out/explainer/look/

  BL=/Applications/Blender.app/Contents/MacOS/Blender
  $BL -b --factory-startup build/out/am_atelier.blend --python-exit-code 1 -P tools/render_atelier_look.py -- atelier
  $BL -b --factory-startup build/out/am.blend         --python-exit-code 1 -P tools/render_atelier_look.py -- museum
  $BL -b --factory-startup                             --python-exit-code 1 -P tools/render_atelier_look.py -- compose

atelier : CAM_front34 / CAM_front_close / CAM_back_close, Cycles (Metal, AM_CYCLES_SAMPLES=96, OIDN)
          and EEVEE (AM_EEVEE_SAMPLES=64, ray tracing on), 1280x720, crank 0.37, patina = the staging
          default; one warm-up render per engine, then the timed stills -> render_times.json.
          Also: hero at patina 0.06 and 0.30 in both engines (patina/), and the same EEVEE hero
          and front close-up saved with AgX / Khronos PBR Neutral / Standard (transforms/).
museum  : the current museum staging (in am.blend) from the same three cameras, Cycles, same
          samples (the close-up cameras are created in memory with the atelier definitions).
compose : compare.jpg (museum | atelier, one row per camera, Cycles) and transform_compare.jpg,
          with French captions rendered by Workbench.
"""
import json
import os
import pathlib
import sys
import time
import importlib.util

import bpy

ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
OUT = os.path.join(ROOT, 'build', 'out', 'explainer', 'look')
sys.path.insert(0, f'{ROOT}/build/blender_scripts')
CS = int(os.environ.get('AM_CYCLES_SAMPLES', '96'))
ES = int(os.environ.get('AM_EEVEE_SAMPLES', '64'))
RES = (1280, 720)
CRANK = 0.37
SHOTS = [('CAM_front34', 'front34'), ('CAM_front_close', 'close_front'), ('CAM_back_close', 'close_back')]
CAPTIONS = {'CAM_front34': 'vue 3/4 (héros)', 'CAM_front_close': 'cadran avant (gros plan)',
            'CAM_back_close': 'cadrans arrière (gros plan)'}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _log(*a):
    print('[look]', *a, flush=True)


def _controller(patina):
    ctl = bpy.data.objects['AM_Controller']
    if ctl.animation_data:
        ctl.animation_data.action = None
    ctl['crank'] = CRANK
    ctl['patina'] = patina
    ctl['explode'] = 0.0
    ctl.update_tag()
    bpy.context.view_layer.update()


def _render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t


def run_atelier():
    import render
    st = _load('staging_atelier', f'{ROOT}/tools/staging_atelier.py')
    sc = bpy.context.scene
    if 'AM_ATELIER' not in bpy.data.collections:
        st.apply(sc)
    os.makedirs(os.path.join(OUT, 'patina'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'transforms'), exist_ok=True)
    times = {'resolution': list(RES), 'cycles_samples': CS, 'eevee_samples': ES, 'device': None,
             'patina': st.PATINA, 'crank': CRANK, 'seconds': {}}

    def visibility(mode):
        render.set_visibility('back' if mode == 'close_back' else ('front34' if mode.startswith('close') else mode))
        st.stage_visibility(mode)

    for engine in ('cycles', 'eevee'):
        ok = render.engine_setup(sc, engine, CS, RES)
        st.finish(sc, engine)
        if engine == 'cycles':
            prefs = bpy.context.preferences.addons['cycles'].preferences
            times['device'] = [d.name for d in prefs.devices if d.use] if ok else 'CPU'
        else:
            sc.eevee.taa_render_samples = ES
        # warm-up (kernel / shader compilation), not timed
        _controller(st.PATINA)
        visibility('front34')
        sc.camera = bpy.data.objects['CAM_front34']
        sc.render.resolution_percentage = 25
        _render(os.path.join(OUT, '_warmup.png'))
        sc.render.resolution_percentage = 100
        for cam, mode in SHOTS:
            _controller(st.PATINA)
            visibility(mode)
            sc.camera = bpy.data.objects[cam]
            dt = _render(os.path.join(OUT, f'{cam}_{engine}.png'))
            times['seconds'][f'{cam}_{engine}'] = round(dt, 2)
            _log(cam, engine, '%.1f s' % dt)
        # patina test on the hero
        visibility('front34')
        sc.camera = bpy.data.objects['CAM_front34']
        for pat in (0.06, 0.30):
            _controller(pat)
            dt = _render(os.path.join(OUT, 'patina', f'CAM_front34_patina{pat:.2f}_{engine}.png'))
            times['seconds'][f'patina{pat:.2f}_{engine}'] = round(dt, 2)
        # view transforms (EEVEE only; same render re-saved)
        if engine == 'eevee':
            vs = sc.view_settings
            keep = (vs.view_transform, vs.look, vs.exposure)
            for cam, mode in SHOTS[:2]:
                _controller(st.PATINA)
                visibility(mode)
                sc.camera = bpy.data.objects[cam]
                bpy.ops.render.render()
                img = bpy.data.images['Render Result']
                for tag, vt, look in (('agx', 'AgX', 'AgX - Punchy'), ('khronos', 'Khronos PBR Neutral', 'None'),
                                      ('standard', 'Standard', 'None')):
                    vs.view_transform = vt
                    vs.look = look
                    img.save_render(os.path.join(OUT, 'transforms', f'{cam}_{tag}.png'), scene=sc)
                vs.view_transform, vs.look, vs.exposure = keep
    try:
        os.remove(os.path.join(OUT, '_warmup.png'))
    except OSError:
        pass
    tot = times['seconds']
    times['summary'] = {
        'cycles_mean_s_per_frame': round(sum(tot[f'{c}_cycles'] for c, _ in SHOTS) / 3, 2),
        'eevee_mean_s_per_frame': round(sum(tot[f'{c}_eevee'] for c, _ in SHOTS) / 3, 2),
    }
    for eng in ('cycles', 'eevee'):
        m = times['summary'][f'{eng}_mean_s_per_frame']
        times['summary'][f'{eng}_hours_for_3000_frames'] = round(m * 3000 / 3600, 2)
    with open(os.path.join(OUT, 'render_times.json'), 'w') as f:
        json.dump(times, f, indent=1, ensure_ascii=False)
    _log('times', json.dumps(times['summary']))


def run_museum():
    import render
    sm = _load('staging_museum', f'{ROOT}/tools/staging_museum.py')
    st = _load('staging_atelier', f'{ROOT}/tools/staging_atelier.py')
    sc = bpy.context.scene
    if 'AM_STAGE' not in bpy.data.collections:
        sm.apply(sc)
    st.ensure_cameras(sc)                      # in memory only (this script never saves)
    os.makedirs(os.path.join(OUT, 'museum'), exist_ok=True)
    render.engine_setup(sc, 'cycles', CS, RES)
    sm.finish(sc, 'cycles')
    times = {}
    for cam, mode in SHOTS:
        m = {'front34': 'front34', 'close_front': 'front34', 'close_back': 'back'}[mode]
        render.set_visibility(m)
        sm.stage_visibility(m)
        _controller(sm.PATINA)
        sc.camera = bpy.data.objects[cam]
        times[cam] = round(_render(os.path.join(OUT, 'museum', f'{cam}_cycles.png')), 2)
    _log('museum', times)


# ----------------------------------------------------------------------------- compose
def _caption(text, w, h, path, size=0.42):
    """White text on a dark bar, rendered with Workbench (no font library needed)."""
    sc = bpy.data.scenes.new('caption')
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.display_settings.display_device = 'sRGB'
    sc.view_settings.view_transform = 'Standard'
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'SINGLE'
    sh.single_color = (1.0, 1.0, 1.0)
    w_ = bpy.data.worlds.new('caption')
    w_.color = (0.012, 0.011, 0.010)
    sc.world = w_
    cu = bpy.data.curves.new('caption', 'FONT')
    cu.body = text
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new('caption', cu)
    sc.collection.objects.link(ob)
    cam = bpy.data.objects.new('caption_cam', bpy.data.cameras.new('caption_cam'))
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = w / h
    cam.location = (0.0, 0.0, 5.0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = path
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)


def run_compose():
    import numpy as np
    import OpenImageIO as oiio
    tmp = os.path.join(OUT, '_cap')
    os.makedirs(tmp, exist_ok=True)

    def read(p, w, h):
        buf = oiio.ImageBuf(p)
        spec = buf.spec()
        if (spec.width, spec.height) != (w, h):
            buf = oiio.ImageBufAlgo.resize(buf, roi=oiio.ROI(0, w, 0, h, 0, 1, 0, 3))
        return buf.get_pixels(oiio.FLOAT)[..., :3]

    def cap(text, w, h, size):
        p = os.path.join(tmp, '%08x.png' % (abs(hash((text, w, h, size))) & 0xffffffff))
        _caption(text, w, h, p, size)
        return read(p, w, h)

    def write(img, path):
        out = oiio.ImageBuf(oiio.ImageSpec(img.shape[1], img.shape[0], 3, oiio.FLOAT))
        out.set_pixels(oiio.ROI(), np.ascontiguousarray(img))
        out.set_write_format(oiio.UINT8)
        out.specmod().attribute('Compression', 'jpeg:92')
        out.write(path)
        _log('wrote', path)

    W, H = 960, 540
    gap = np.full((H, 8, 3), 0.012, np.float32)
    rows = [np.concatenate([cap('Musée (actuel)', W, 64, 0.42), gap[:64],
                            cap('Atelier à la lumière du jour (proposé)', W, 64, 0.42)], 1)]
    for cam, _ in SHOTS:
        m = read(os.path.join(OUT, 'museum', f'{cam}_cycles.png'), W, H)
        a = read(os.path.join(OUT, f'{cam}_cycles.png'), W, H)
        rows.append(np.concatenate([m, gap, a], 1))
        rows.append(np.concatenate([cap(CAPTIONS[cam] + ' - Cycles %d échantillons' % CS, W * 2 + 8, 44, 0.34)], 1))
    write(np.concatenate(rows, 0), os.path.join(OUT, 'compare.jpg'))
    # view transforms
    rows = [np.concatenate([cap(t, W, 56, 0.4) if i == 0 else np.concatenate([gap[:56], cap(t, W, 56, 0.4)], 1)
                            for i, t in enumerate(('AgX (Punchy)', 'Khronos PBR Neutral (retenu)', 'Standard'))], 1)]
    for cam, _ in SHOTS[:2]:
        ims = [read(os.path.join(OUT, 'transforms', f'{cam}_{t}.png'), W, H) for t in ('agx', 'khronos', 'standard')]
        rows.append(np.concatenate([ims[0], gap, ims[1], gap, ims[2]], 1))
    write(np.concatenate(rows, 0), os.path.join(OUT, 'transform_compare.jpg'))
    # patina
    rows = [np.concatenate([cap('patine 0,06 (actuelle)', W, 56, 0.4), gap[:56], cap('patine 0,30', W, 56, 0.4)], 1)]
    for eng, label in (('cycles', 'Cycles %d échantillons' % CS), ('eevee', 'EEVEE %d échantillons' % ES)):
        ims = [read(os.path.join(OUT, 'patina', f'CAM_front34_patina{p}_{eng}.png'), W, H) for p in ('0.06', '0.30')]
        rows.append(np.concatenate([ims[0], gap, ims[1]], 1))
        rows.append(cap(label, W * 2 + 8, 44, 0.34))
    write(np.concatenate(rows, 0), os.path.join(OUT, 'patina_compare.jpg'))
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['atelier']
    os.makedirs(OUT, exist_ok=True)
    {'atelier': run_atelier, 'museum': run_museum, 'compose': run_compose}[argv[0]]()
