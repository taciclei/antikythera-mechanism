"""Resumable EEVEE renderer of the film's 3D frames (Blender 5.2) : film.blend (build_film.py) -> PNG frames.

    BL=/Applications/Blender.app/Contents/MacOS/Blender
    $BL -b build/out/explainer/film/film.blend --factory-startup --python-exit-code 1 \
        -P tools/explainer/film/render_frames.py -- --res 1920x1080 --out build/out/explainer/film/frames \
        --start 1 --end 4009
    # options : --samples N (default below) · --frames 127,1446,2834 (explicit list) · --no-inset · --only-inset
    #           --overwrite · --bench N (warm-up + N timed frames at --res, files overwritten, report in DIR/bench.json)
    #           --set key=value (override one of DEFAULTS, e.g. --set rt_resolution_scale=1 ; repeatable)

Which frames : only the frames of the segments of timeline.json whose render_3d is true (kinds 3d, split and the end
card, whose background is the 3D orbit) ; map / diagram frames are skipped.  The inset camera of shot 3.4
(CAM_3_4_ball, scene FILM_inset_3_4, 480 x 480 at full size) is rendered too, into DIR/inset_3_4/, unless --no-inset.

Resumable : a frame is skipped when DIR/NNNN.png exists and is not empty ; every frame is written to a temporary name
first, then renamed, so an interrupted run never leaves a truncated PNG.  Several processes may share a range only
if they get disjoint --start/--end.  One line per rendered frame is appended to DIR/render_log.jsonl.

Output : DIR/NNNN.png (NNNN = film frame, 1-based, 4 digits), PNG RGB 8 bits, colour management of the atelier
(Khronos PBR Neutral, exposure +0.15).  --res 960x540 renders at 50 % (same framing, anchors scale by 0.5).

EEVEE settings (DEFAULTS, chosen by --bench at 1920x1080 on the Mac M4, see tools/explainer/film/README.md) : they
are written into film.blend by build_film.py and applied again here before rendering.
"""
import json
import os
import pathlib
import sys
import time

import bpy

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import filmlib as L  # noqa: E402

INSET_SCENE = 'FILM_inset_3_4'
INSET_DIR = 'inset_3_4'

# final settings, chosen with --bench at 1920x1080 on the Mac M4 (MacBook Air, fanless : a long render runs
# THROTTLED, about 1.35-1.9x slower than a cold machine ; « hot » = after several minutes of rendering), 26 Sep. 2026,
# 13 frames spread over every kind of shot (bench_hot*.log) :
#   samples, ray tracing / fast GI / shadows                       cold s/image   hot s/image
#   16, half resolution, light GI and shadows                          1.39            -        grain on wide shots
#   24, full resolution (= staging_atelier.tune_eevee but samples)       -            3.57      light grain (lid, bench)
#   28, full resolution                                                  -            4.10      <- kept (diff. to 48 : 0.3-1.0 / 255)
#   32, shadow steps 8, GI steps 6                                       -            4.26      noisier than 28 full
#   32, full resolution                                                2.37           4.57
#   48, full resolution                                                3.39           6.58      reference
DEFAULTS = {
    'samples': 28,
    'filter_size': 1.5,
    # ray tracing (reflections of the polished bronze) : screen space, full resolution, denoised
    'use_raytracing': True,
    'ray_tracing_method': 'SCREEN',
    'rt_resolution_scale': '1',
    'rt_trace_max_roughness': 0.55,
    'rt_screen_trace_quality': 0.6,
    'rt_screen_trace_thickness': 2.0,
    'rt_denoise': True,
    # fast GI (bounce light of the sunlit bench)
    'use_fast_gi': True,
    'fast_gi_method': 'GLOBAL_ILLUMINATION',
    'fast_gi_resolution': '2',
    'fast_gi_step_count': 8,
    'fast_gi_ray_count': 2,
    'fast_gi_quality': 0.5,
    'fast_gi_distance': 120.0,
    # shadows (virtual shadow maps ; the soft 2.5° sun needs the samples above)
    'shadow_ray_count': 1,
    'shadow_step_count': 16,
    'shadow_resolution_scale': 1.0,
    'shadow_pool_size': '1024',
    'light_threshold': 0.01,
    'clamp_surface_indirect': 10.0,
}


def _set(obj, attr, value):
    if hasattr(obj, attr):
        try:
            setattr(obj, attr, value)
        except (TypeError, ValueError) as ex:
            print('[render] cannot set %s = %r : %s' % (attr, value, ex))
    else:
        print('[render] missing property', attr)


def apply_settings(scene, s=None, res=(L.WIDTH, L.HEIGHT), pct=100):
    """EEVEE + output settings of the film (both scenes : main and inset)."""
    s = dict(DEFAULTS, **(s or {}))
    r = scene.render
    r.engine = 'BLENDER_EEVEE'
    if scene.name != INSET_SCENE:
        r.resolution_x, r.resolution_y = res
    r.resolution_percentage = pct
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0
    r.fps, r.fps_base = L.FPS, 1.0
    r.use_motion_blur = False
    r.film_transparent = False
    r.filter_size = s['filter_size']
    r.use_compositing = False
    r.use_sequencer = False
    r.use_file_extension = False
    im = r.image_settings
    im.media_type = 'IMAGE'
    im.file_format = 'PNG'
    im.color_mode = 'RGB'
    im.color_depth = '8'
    im.compression = 15
    e = scene.eevee
    _set(e, 'taa_render_samples', int(s['samples']))
    _set(e, 'use_raytracing', s['use_raytracing'])
    _set(e, 'ray_tracing_method', s['ray_tracing_method'])
    rt = e.ray_tracing_options
    _set(rt, 'resolution_scale', s['rt_resolution_scale'])
    _set(rt, 'trace_max_roughness', s['rt_trace_max_roughness'])
    _set(rt, 'screen_trace_quality', s['rt_screen_trace_quality'])
    _set(rt, 'screen_trace_thickness', s['rt_screen_trace_thickness'])
    _set(rt, 'use_denoise', s['rt_denoise'])
    _set(rt, 'denoise_spatial', s['rt_denoise'])
    _set(rt, 'denoise_temporal', s['rt_denoise'])
    _set(rt, 'denoise_bilateral', s['rt_denoise'])
    _set(e, 'use_fast_gi', s['use_fast_gi'])
    _set(e, 'fast_gi_method', s['fast_gi_method'])
    _set(e, 'fast_gi_resolution', s['fast_gi_resolution'])
    _set(e, 'fast_gi_step_count', s['fast_gi_step_count'])
    _set(e, 'fast_gi_ray_count', s['fast_gi_ray_count'])
    _set(e, 'fast_gi_quality', s['fast_gi_quality'])
    _set(e, 'fast_gi_distance', s['fast_gi_distance'])
    _set(e, 'use_shadows', True)
    _set(e, 'shadow_ray_count', s['shadow_ray_count'])
    _set(e, 'shadow_step_count', s['shadow_step_count'])
    _set(e, 'shadow_resolution_scale', s['shadow_resolution_scale'])
    _set(e, 'shadow_pool_size', s['shadow_pool_size'])
    _set(e, 'light_threshold', s['light_threshold'])
    _set(e, 'clamp_surface_indirect', s['clamp_surface_indirect'])
    return s


def timeline():
    return json.loads((L.FILM / 'timeline.json').read_text())


def render_frames_of(T):
    """Film frames to render (segments with render_3d) and the frames of the 3.4 inset."""
    main, inset = [], []
    for s in T['segments']:
        if s.get('render_3d'):
            main += list(range(s['frames'][0], s['frames'][1] + 1))
        if s.get('inset'):
            inset += list(range(s['frames'][0], s['frames'][1] + 1))
    return main, inset


def _done(path):
    return path.exists() and path.stat().st_size > 0


def render_one(scene, f, path):
    """Renders film frame f of scene into path (temporary name, then rename) ; returns seconds."""
    tmp = path.with_name('.%s.part.png' % path.stem)
    scene.frame_set(f)
    scene.render.filepath = str(tmp)
    t = time.time()
    with bpy.context.temp_override(scene=scene):
        bpy.ops.render.render(write_still=True, scene=scene.name)
    dt = time.time() - t
    os.replace(tmp, path)
    return dt


def _arg(argv, key, default=None, cast=str):
    return cast(argv[argv.index(key) + 1]) if key in argv else default


def main(argv):
    T = timeline()
    res = tuple(int(v) for v in _arg(argv, '--res', '%dx%d' % (L.WIDTH, L.HEIGHT)).split('x'))
    pct = int(round(100.0 * res[0] / L.WIDTH))
    if (res[0] * L.HEIGHT) != (res[1] * L.WIDTH):
        raise SystemExit('--res doit garder le rapport 16:9 (%s)' % (res,))
    samples = _arg(argv, '--samples', DEFAULTS['samples'], int)
    over = {'samples': samples}
    for i, a in enumerate(argv):                      # --set key=value (any key of DEFAULTS, for tests)
        if a == '--set':
            k, _, v = argv[i + 1].partition('=')
            ref = DEFAULTS[k]
            over[k] = (v.lower() in ('1', 'true', 'yes')) if isinstance(ref, bool) else type(ref)(v)
    out = pathlib.Path(_arg(argv, '--out', str(L.FILM / 'frames'))).resolve()
    start = _arg(argv, '--start', 1, int)
    end = _arg(argv, '--end', T['frame_end'], int)
    bench = _arg(argv, '--bench', 0, int)
    overwrite = '--overwrite' in argv or bench > 0
    main_frames, inset_frames = render_frames_of(T)
    if '--frames' in argv:
        want = sorted({int(x) for x in _arg(argv, '--frames').split(',') if x})
        skipped = [f for f in want if f not in main_frames]
        if skipped:
            print('[render] images sans 3D ignorées :', skipped)
        todo = [f for f in want if f in main_frames]
        todo_inset = [f for f in want if f in inset_frames]
    else:
        todo = [f for f in main_frames if start <= f <= end]
        todo_inset = [f for f in inset_frames if start <= f <= end]
    if '--no-inset' in argv:
        todo_inset = []
    if '--only-inset' in argv:
        todo = []
    sc = bpy.data.scenes.get('Antikythera') or bpy.context.scene
    isc = bpy.data.scenes.get(INSET_SCENE)
    settings = apply_settings(sc, over, (L.WIDTH, L.HEIGHT), pct)
    if isc is not None:
        apply_settings(isc, over, None, pct)
    elif todo_inset:
        print('[render] scène %s absente : pas d\'incrustation' % INSET_SCENE)
        todo_inset = []
    out.mkdir(parents=True, exist_ok=True)
    (out / INSET_DIR).mkdir(exist_ok=True)
    log = open(out / 'render_log.jsonl', 'a')
    jobs = [(sc, f, out / ('%04d.png' % f)) for f in todo] + \
           [(isc, f, out / INSET_DIR / ('%04d.png' % f)) for f in todo_inset]
    if bench:
        jobs = [j for j in jobs if j[0] is sc][:bench + 1]
    if not overwrite:
        jobs = [j for j in jobs if not _done(j[2])]
    print('[render] %d images à rendre (%d principales, %d incrustation) -> %s, %dx%d, %d échantillons'
          % (len(jobs), sum(j[0] is sc for j in jobs), sum(j[0] is not sc for j in jobs), out,
             L.WIDTH * pct // 100, L.HEIGHT * pct // 100, samples), flush=True)
    times = []
    t_all = time.time()
    for i, (scene, f, path) in enumerate(jobs):
        dt = render_one(scene, f, path)
        times.append((scene.name, f, dt))
        log.write(json.dumps({'frame': f, 'scene': scene.name, 'file': path.name, 's': round(dt, 2),
                              'res': [L.WIDTH * pct // 100, L.HEIGHT * pct // 100], 'samples': samples,
                              'time': time.strftime('%Y-%m-%d %H:%M:%S')}) + '\n')
        log.flush()
        eta = (time.time() - t_all) / (i + 1) * (len(jobs) - i - 1)
        print('[render] %s %04d  %.2f s  (%d/%d, reste ~%.0f min)' % (scene.name, f, dt, i + 1, len(jobs), eta / 60),
              flush=True)
    log.close()
    if bench and times:
        timed = [t for t in times[1:]] or times
        mean = sum(t[2] for t in timed) / len(timed)
        n_main, n_inset = len(main_frames), len(inset_frames)
        rep = {'resolution': [L.WIDTH * pct // 100, L.HEIGHT * pct // 100], 'samples': samples,
               'settings': settings, 'warmup_s': round(times[0][2], 2),
               'frames': [{'frame': f, 's': round(dt, 2)} for _, f, dt in timed],
               's_per_frame': round(mean, 2), 'frames_3d_in_film': n_main, 'frames_inset': n_inset,
               'estimate_hours_main': round(mean * n_main / 3600, 2)}
        (out / 'bench.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False))
        print('[bench] %.2f s/image (%s) ; %d images 3D -> %.2f h' % (mean, [round(t[2], 2) for t in timed],
                                                                       n_main, mean * n_main / 3600))
    print('[render] fini en %.1f min' % ((time.time() - t_all) / 60))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
