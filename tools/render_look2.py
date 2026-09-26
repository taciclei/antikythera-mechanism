"""Look v2 of the ATELIER staging (bronze, engravings, dial content): EEVEE stills, before/after sheet.
Never saves any .blend.  Output: build/out/explainer/look2/

  BL=/Applications/Blender.app/Contents/MacOS/Blender
  # before: the atelier file as it was (backup), the two new close-up cameras created in memory
  $BL -b --factory-startup build/out/am_atelier_before_polish.blend --python-exit-code 1 -P tools/render_look2.py -- before
  # after: the polished atelier file (tools/staging_atelier.py + tools/dial_content.py applied and saved)
  $BL -b --factory-startup build/out/am_atelier.blend --python-exit-code 1 -P tools/render_look2.py -- after
  $BL -b --factory-startup --python-exit-code 1 -P tools/render_look2.py -- compose
  # preview: apply the staging + dial content in memory on any atelier file and render small stills
  AM_PREVIEW_DIR=/tmp/x AM_RES_PCT=50 $BL -b --factory-startup build/out/am_atelier_before_polish.blend -P tools/render_look2.py -- preview

EEVEE (AM_EEVEE_SAMPLES=64, ray tracing on), 1920x1080.  Crank per camera: 0.37 for the three look
cameras (same as look/), 5.95 for CAM_games_close (pointer on ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ, film shot 5.3) and 8.975
for CAM_saros_close (pointer entering cell 112, film shot 6.2).  One warm-up render, then timed stills
-> render_times.json.
"""
import importlib.util
import json
import os
import pathlib
import sys
import time

import bpy

ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
OUT = os.path.join(ROOT, 'build', 'out', 'explainer', 'look2')
sys.path.insert(0, f'{ROOT}/build/blender_scripts')
ES = int(os.environ.get('AM_EEVEE_SAMPLES', '64'))
RES = (1920, 1080)
SHOTS = [('CAM_front34', 'front34', 0.37), ('CAM_front_close', 'close_front', 0.37),
         ('CAM_back_close', 'close_back', 0.37), ('CAM_games_close', 'close_back', 5.95),
         ('CAM_saros_close', 'close_back', 8.975)]
CAPTIONS = {'CAM_front34': 'vue 3/4 (héros) · manivelle 0,37',
            'CAM_front_close': 'cadran avant (gros plan) · manivelle 0,37',
            'CAM_back_close': 'cadrans arrière (gros plan) · manivelle 0,37',
            'CAM_games_close': 'cadran des Jeux (nouvelle caméra) · manivelle 5,95',
            'CAM_saros_close': 'spirale du Saros, signes calculés (nouvelle caméra) · manivelle 8,975'}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _log(*a):
    print('[look2]', *a, flush=True)


def _controller(crank, patina):
    ctl = bpy.data.objects['AM_Controller']
    if ctl.animation_data:
        ctl.animation_data.action = None
    ctl['crank'] = float(crank)
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


def _visibility(st, mode):
    import render
    render.set_visibility('back' if mode == 'close_back' else ('front34' if mode.startswith('close') else mode))
    st.stage_visibility(mode)


def run(outdir, pct=100, timed=True, apply_look=False, only=None):
    import render
    st = _load('staging_atelier', f'{ROOT}/tools/staging_atelier.py')
    sc = bpy.context.scene
    if apply_look:
        dc = _load('dial_content', f'{ROOT}/tools/dial_content.py')
        st.apply(sc)
        dc.sizes()
        dc.glyphs()
    else:
        st.ensure_cameras(sc)          # creates the new close-up cameras in memory if missing (never saved)
    patina = float(bpy.data.objects['AM_Controller'].get('patina', st.PATINA))
    os.makedirs(outdir, exist_ok=True)
    render.engine_setup(sc, 'eevee', ES, RES)
    st.finish(sc, 'eevee')
    sc.eevee.taa_render_samples = ES
    sc.render.resolution_percentage = pct
    times = {'engine': 'BLENDER_EEVEE', 'resolution': list(RES), 'resolution_percentage': pct,
             'eevee_samples': ES, 'patina': patina, 'file': os.path.relpath(bpy.data.filepath, ROOT),
             'seconds': {}, 'crank': {}}
    shots = [s for s in SHOTS if only is None or s[0] in only]
    # warm-up (shader compilation), not timed
    _controller(0.37, patina)
    _visibility(st, 'front34')
    sc.camera = bpy.data.objects['CAM_front34']
    keep = sc.render.resolution_percentage
    sc.render.resolution_percentage = 25
    _render(os.path.join(outdir, '_warmup.png'))
    sc.render.resolution_percentage = keep
    for cam, mode, crank in shots:
        _controller(crank, patina)
        _visibility(st, mode)
        sc.camera = bpy.data.objects[cam]
        dt = _render(os.path.join(outdir, f'{cam}_eevee.png'))
        times['seconds'][cam] = round(dt, 2)
        times['crank'][cam] = crank
        _log(cam, 'crank', crank, '%.1f s' % dt)
    try:
        os.remove(os.path.join(outdir, '_warmup.png'))
    except OSError:
        pass
    if timed:
        v = list(times['seconds'].values())
        times['summary'] = {'eevee_mean_s_per_frame': round(sum(v) / len(v), 2),
                            'eevee_max_s_per_frame': round(max(v), 2),
                            'eevee_hours_for_3000_frames': round(sum(v) / len(v) * 3000 / 3600, 2)}
        try:
            import gpu
            times['gpu'] = gpu.platform.renderer_get()
        except Exception:                                   # noqa: BLE001
            pass
        with open(os.path.join(outdir, 'render_times.json'), 'w') as f:
            json.dump(times, f, indent=1, ensure_ascii=False)
        _log('times', json.dumps(times['summary']))


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

    W, H = 960, 540
    gap = np.full((H, 8, 3), 0.012, np.float32)
    rows = [np.concatenate([cap('Avant (atelier, look 1)', W, 64, 0.42), gap[:64],
                            cap('Après (bronze, gravures, Jeux, signes du Saros)', W, 64, 0.42)], 1)]
    for cam, _, _ in SHOTS:
        b = read(os.path.join(OUT, 'before', f'{cam}_eevee.png'), W, H)
        a = read(os.path.join(OUT, f'{cam}_eevee.png'), W, H)
        rows.append(np.concatenate([b, gap, a], 1))
        rows.append(cap(CAPTIONS[cam] + ' · EEVEE %d échantillons' % ES, W * 2 + 8, 44, 0.34))
    img = np.concatenate(rows, 0)
    out = oiio.ImageBuf(oiio.ImageSpec(img.shape[1], img.shape[0], 3, oiio.FLOAT))
    out.set_pixels(oiio.ROI(), np.ascontiguousarray(img))
    out.set_write_format(oiio.UINT8)
    out.specmod().attribute('Compression', 'jpeg:92')
    out.write(os.path.join(OUT, 'compare.jpg'))
    _log('wrote', os.path.join(OUT, 'compare.jpg'))
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['after']
    mode = argv[0]
    only = argv[1].split(',') if len(argv) > 1 else None
    if mode == 'before':
        run(os.path.join(OUT, 'before'), timed=True, only=only)
    elif mode == 'after':
        run(OUT, timed=True, only=only)
    elif mode == 'preview':
        run(os.environ['AM_PREVIEW_DIR'], pct=int(os.environ.get('AM_RES_PCT', '50')), timed=False,
            apply_look=True, only=only)
    elif mode == 'compose':
        run_compose()
