"""Mutation test of the Lean proofs: Lean must REJECT a wrong mechanism.

Each mutant is a standalone Lean file (Kinematics + Targets, or Geometry) with one deliberate error, compiled with
`lake env lean`. The test passes only if EVERY mutant fails to compile and the unmutated control compiles.
Needs the built project in lean/ (lake exe cache get && lake build). Takes a few minutes.
"""
import json, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEAN = ROOT / 'lean'
SRC = LEAN / 'Antikythera'
TMP = Path(tempfile.mkdtemp(prefix='am_mut_'))
OPTS = ['-DwarningAsError=true', '-DrelaxedAutoImplicit=false', '-DmaxSynthPendingDepth=3']

def standalone(kin, tgt):
    return kin + '\n' + tgt.replace('import Antikythera.Kinematics\n', '')

def sub(text, old, new):
    assert text.count(old) >= 1, f'pattern not found: {old}'
    return text.replace(old, new, 1)

def spec_mutant(gear, teeth):
    spec = json.loads((ROOT / 'spec' / 'antikythera.json').read_text())
    next(g for g in spec['gears'] if g['id'] == gear)['teeth'] = teeth
    d = TMP / f'spec_{gear}'; d.mkdir()
    (d / 'spec.json').write_text(json.dumps(spec))
    subprocess.run([sys.executable, str(ROOT / 'tools' / 'make_lean.py'), '--spec', str(d / 'spec.json'),
                    '--out', str(d), '--skip-declared-check'], check=True, capture_output=True)
    return standalone((d / 'Kinematics.lean').read_text(), (d / 'Targets.lean').read_text())

K, T, G = (SRC / 'Kinematics.lean').read_text(), (SRC / 'Targets.lean').read_text(), (SRC / 'Geometry.lean').read_text()
KT = standalone(K, T)
MUTANTS = {
    'control (unmutated, must compile)': KT,
    'tooth count c1 38 -> 39 in the b2~c1 contact': sub(KT, '64 * (ω .b - ω .frame) + 38 * (ω .c', '64 * (ω .b - ω .frame) + 39 * (ω .c'),
    'Willis sign flipped on the Olympiad mesh n3~o1': sub(KT, '+ 60 * (ω .o - ω .frame) = 0', '- 60 * (ω .o - ω .frame) = 0'),
    'wrong carrier on the Dragon Hand mesh nd64~nd48': sub(KT, '64 * (ω .spB - ω .b) + 48 * (ω .t_nodes - ω .b) = 0',
                                                              '64 * (ω .spB - ω .frame) + 48 * (ω .t_nodes - ω .frame) = 0'),
    'rate table: k 55688/4237 -> 55689/4237': sub(KT, '| .k => 55688 / 4237', '| .k => 55689 / 4237'),
    'target: Moon 254/19 -> 253/19': re.sub(r'(ω \.moon = )254 / 19', r'\g<1>253 / 19', KT, count=1),
    'target: Saros -940/4237 -> -941/4237': sub(KT, 'ω .g = -940 / 4237', 'ω .g = -941 / 4237'),
    'spec end-to-end: Metonic gear n1 53 -> 54 teeth': spec_mutant('n1', 54),
    'spec end-to-end: Olympiad gear o1 60 -> 61 teeth': spec_mutant('o1', 61),
    'geometry: axis of o1 moved 1e-5 mm along the n3~o1 line': G.replace('(-24.40035)', '(-24.40036)'),
}
assert MUTANTS['geometry: axis of o1 moved 1e-5 mm along the n3~o1 line'] != G, 'geometry pattern not found'

def run(item):
    i, (name, text) = item
    f = TMP / f'm{i:02d}.lean'; f.write_text(text)
    r = subprocess.run(['lake', 'env', 'lean', *OPTS, str(f)], cwd=LEAN, capture_output=True, text=True)
    first = next((l for l in (r.stdout + r.stderr).splitlines() if 'error' in l), '')
    return name, r.returncode, first

with ThreadPoolExecutor(3) as ex:
    results = list(ex.map(run, enumerate(MUTANTS.items())))
bad = 0
for name, code, first in results:
    control = name.startswith('control')
    ok = (code == 0) if control else (code != 0)
    bad += not ok
    status = ('compiles' if code == 0 else 'REJECTED') if ok else ('FAILED TO COMPILE' if control else 'SURVIVED')
    print(f"{'OK ' if ok else 'BAD'} {status:9} {name}" + (f"\n      {first.split(': error: ')[-1][:110]}" if code and not control else ''))
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{len(MUTANTS) - 1} of {len(MUTANTS) - 1} mutants rejected by Lean" if not bad else f"\n{bad} problem(s)")
sys.exit(1 if bad else 0)
