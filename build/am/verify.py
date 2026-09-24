"""CLI: python -m am.verify --stage {spec,kinematics,geometry,expr,all}. Exit code != 0 on failure."""
import argparse
import json
import os
import sys
import time

from . import OUT, spec as S, kinematics as K


def stage_spec(s, res):
    fp = S.fingerprint_report(s.d)
    errs = S.validate(s.d)
    ok = fp['ok'] and all(fp['sections'].values()) and not errs
    res['spec'] = {'ok': ok, 'sha256': fp['sha256'], 'sections_ok': all(fp['sections'].values()),
                   'structure_errors': errs}
    print('[spec] sha256 %s %s; structure errors: %d' % (fp['sha256'], 'OK' if fp['ok'] else 'MISMATCH', len(errs)))
    return ok


def stage_kinematics(s, res):
    ok, rep = K.check(s)
    res['kinematics'] = rep
    print('[kinematics] unknowns %d, equations %d %s, rank %d, DOF %d, inconsistent %d'
          % (rep['n_unknowns'], rep['n_equations'], rep['counts'], rep['rank'], rep['dof'], rep['inconsistent']))
    print('[kinematics] rate errors: %d; targets ok: %d/%d'
          % (len(rep['rate_errors']), sum(t['ok'] for t in rep['targets']), len(rep['targets'])))
    for t in rep['targets']:
        if not t['ok']:
            print('   TARGET FAIL', t)
    return ok


def stage_geometry(s, res):
    from . import geomcheck
    ok, rep = geomcheck.run(s)
    res['geometry'] = rep
    return ok


def stage_expr(s, res):
    from . import expr
    ok, rep = expr.check(s)
    res['expr'] = rep
    print('[expr] max error %.3e rad over %d samples, max length %d -> %s'
          % (rep['max_err'], rep['samples'], rep['max_len'], 'OK' if ok else 'FAIL'))
    return ok


STAGES = {'spec': stage_spec, 'kinematics': stage_kinematics, 'geometry': stage_geometry,
          'expr': stage_expr}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all', choices=list(STAGES) + ['all'])
    a = ap.parse_args(argv)
    s = S.load()
    names = list(STAGES) if a.stage == 'all' else [a.stage]
    res, allok = {}, True
    for n in names:
        t0 = time.time()
        ok = STAGES[n](s, res)
        print('[%s] %s (%.1f s)' % (n, 'PASS' if ok else 'FAIL', time.time() - t0))
        allok &= ok
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'verify_%s.json' % a.stage)
    with open(path, 'w') as f:
        json.dump(res, f, indent=1, default=str)
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main())
