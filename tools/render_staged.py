"""Run the build's render.py modes with the museum staging (ground, lights, world, AgX) applied.
Blender -b out/am.blend --python-exit-code 1 -P render_staged.py -- <render.py mode args>   (e.g. frames 1 120 | stills all cycles)
Wraps render.set_visibility (-> staging.stage_visibility) and render.engine_setup (-> staging.finish, EEVEE samples)."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parent.parent)   # repository root
import bpy, os, sys, importlib.util
sys.path.insert(0, f'{ROOT}/build/blender_scripts')
spec = importlib.util.spec_from_file_location('staging', f'{ROOT}/tools/staging_museum.py')
staging = importlib.util.module_from_spec(spec); spec.loader.exec_module(staging)
if 'AM_STAGE' not in bpy.data.collections: staging.apply(bpy.context.scene)
SAMPLES = int(os.environ.get('AM_SAMPLES', '64'))
argv = sys.argv[sys.argv.index('--') + 1:]
sys.argv = [sys.argv[0], '--'] + argv           # render.py parses its own args after '--'
import render
_sv, _es = render.set_visibility, render.engine_setup
def set_visibility(mode):
    _sv(mode); staging.stage_visibility('front34' if mode == 'anim' else mode)
def engine_setup(sc, engine, samples=256, res=(1920, 1080)):
    ok = _es(sc, engine, samples, res); staging.finish(sc, engine)
    if engine != 'cycles': sc.eevee.taa_render_samples = SAMPLES
    return ok
render.set_visibility, render.engine_setup = set_visibility, engine_setup
mode = argv[0]
if mode == 'frames': render.frames(int(argv[1]), int(argv[2]))
elif mode == 'stills': render.stills(argv[1], argv[2] if len(argv) > 2 else 'cycles')
elif mode == 'encode': render.encode()
elif mode == 'verify': render.verify()
