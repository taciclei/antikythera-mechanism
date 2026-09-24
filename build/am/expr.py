"""Driver expressions (Blender 'simple expression' subset, <= 255 chars) for every body, and a
restricted Python evaluator reproducing them. Variable 'c' = AM_Controller["crank"] (years);
other variables are SINGLE_PROP reads of another body Empty's rotation_euler[i]."""
import ast
import math
import random
from fractions import Fraction

from . import kinematics as K
from . import spiral as SP

ALLOWED_FUNCS = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'asin': math.asin, 'acos': math.acos,
    'atan': math.atan, 'atan2': math.atan2, 'sqrt': math.sqrt, 'pow': math.pow, 'exp': math.exp,
    'log': math.log, 'fmod': math.fmod, 'floor': math.floor, 'ceil': math.ceil, 'trunc': math.trunc,
    'round': round, 'int': int, 'abs': abs, 'fabs': math.fabs, 'min': min, 'max': max,
    'radians': math.radians, 'degrees': math.degrees,
}
ALLOWED_CONSTS = {'pi': math.pi, 'True': 1.0, 'False': 0.0}
MAX_LEN = 255


def lin(rate):
    """theta = -2*pi*fmod(c*rate, 1) as a string with exact integer fractions."""
    r = Fraction(rate)
    if r == 0:
        return '0.0'
    n, d = abs(r.numerator), r.denominator
    arg = 'c' if (n, d) == (1, 1) else ('c*%d' % n if d == 1 else ('c/%d' % d if n == 1 else 'c*%d/%d' % (n, d)))
    return ('-2*pi*fmod(%s,1)' if r > 0 else '2*pi*fmod(%s,1)') % arg


def num(x):
    return repr(float(x))


def plus(x):
    """'+x' or '-|x|' for appending a constant."""
    return ('+' + num(x)) if x >= 0 else ('-' + num(-x))


def body_empty(b):
    return 'B_' + b


def build(spec):
    """Return {body: {'expr', 'index', 'vars': {name: (object_name, data_path)}}} for all bodies."""
    L = K.Laws(spec)
    out = {}
    ctl = ('AM_Controller', '["crank"]')

    def rot(b, i=2):
        return (body_empty(b), 'rotation_euler[%d]' % i)

    for b in spec['bodies']:
        bid = b['id']
        if b['kind'] == 'revolute':
            out[bid] = {'expr': lin(L.rel[bid]), 'index': 2, 'vars': {'c': ctl}}
    out['a'] = {'expr': lin(L.crank_rate), 'index': 0, 'vars': {'c': ctl}}
    for s, (p, e, r, beta, _) in L.ps.items():
        ex = 'p+atan2(%s*sin(p%s),%s-%s*cos(p%s))' % (num(e), plus(-beta), num(r), num(e), plus(-beta))
        out[s] = {'expr': ex, 'index': 2, 'vars': {'p': rot(p)}}
    out['e_inner'] = {'expr': lin(L.rel['e_table']) + '-k', 'index': 2,
                      'vars': {'c': ctl, 'k': rot('kp')}}
    out['moon'] = {'expr': '-e', 'index': 2, 'vars': {'e': rot('e_inner')}}
    for o, slot in L.out_of_slot.items():
        out[o] = {'expr': lin(L.rel['b']) + '-s', 'index': 2, 'vars': {'c': ctl, 's': rot(slot)}}
    for fb, (epi, i, d, g0, ph) in L.fol.items():
        P = ph - g0
        ex = '%s%s+atan2(%s*sin(x%s),%s+%s*cos(x%s))' % (lin(L.rel['b']), plus(g0), num(d), plus(P),
                                                        num(i), num(d), plus(P))
        out[fb] = {'expr': ex, 'index': 2, 'vars': {'c': ctl, 'x': rot(epi)}}
    out['q'] = {'expr': lin(L.rel['b']) + '-m', 'index': 0, 'vars': {'c': ctl, 'm': rot('moon')}}
    return out


def slider_exprs(spec):
    """psi_mod drivers of the spiral sliders (spec 5.7) and their lookup tables."""
    res = {}
    for which, body in (('metonic', 'n'), ('saros', 'g')):
        d = spec.dials['back'][which]
        L = K.Laws(spec)
        r = Fraction(L.rel[body])          # world rate of the pointer (psi = +theta)
        turns = d['turns']
        # psi = theta_n = -2*pi*rate*c ; psi_mod = 2*pi*turns*frac(-rate*c/turns)
        q = -r / turns
        n, dd = q.numerator, q.denominator
        arg = 'c/%d' % dd if n == 1 else 'c*%d/%d' % (n, dd)
        ex = '%d*pi*fmod(fmod(%s,1)+1,1)' % (2 * turns, arg)
        psi, rho = SP.lookup(d['r_start'], d['pitch'], turns, 250)
        res[which] = {'expr': ex, 'vars': {'c': ('AM_Controller', '["crank"]')}, 'body': body,
                      'psi': psi.tolist(), 'rho': rho.tolist()}
    return res


# ---------------------------------------------------------------- restricted evaluator
def validate(expr):
    """True if expr only uses the simple-expression subset."""
    tree = ast.parse(expr, mode='eval')
    ok_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load, ast.Constant,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd, ast.Compare, ast.IfExp,
                ast.BoolOp, ast.And, ast.Or, ast.Not, ast.Lt, ast.Gt, ast.LtE, ast.GtE, ast.Eq,
                ast.NotEq, ast.Mod, ast.Pow)
    for node in ast.walk(tree):
        if not isinstance(node, ok_nodes):
            return False
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS or node.keywords:
                return False
    return True


def evaluate(expr, variables):
    if not validate(expr):
        raise ValueError('not a simple expression: ' + expr)
    env = dict(ALLOWED_FUNCS)
    env.update(ALLOWED_CONSTS)
    env.update(variables)
    return float(eval(compile(expr, '<driver>', 'eval'), {'__builtins__': {}}, env))


ORDER = None


def eval_all(ex, t):
    """Evaluate every body expression at crank t (float64), resolving variables in order."""
    vals = {}
    pending = dict(ex)
    while pending:
        progress = False
        for b, e in list(pending.items()):
            env = {}
            ready = True
            for v, (obj, path) in e['vars'].items():
                if obj == 'AM_Controller':
                    env[v] = t
                else:
                    src = obj[2:]
                    if src not in vals:
                        ready = False
                        break
                    env[v] = vals[src]
            if ready:
                vals[b] = evaluate(e['expr'], env)
                del pending[b]
                progress = True
        if not progress:
            raise RuntimeError('cyclic driver dependencies: %s' % list(pending))
    return vals


def check(spec, n=200, seed=20260924):
    ex = build(spec)
    L = K.Laws(spec)
    rnd = random.Random(seed)
    ts = [rnd.uniform(-50, 50) for _ in range(n - 4)] + [-50.0, 0.0, 1e-3, 50.0]
    worst, worst_at = 0.0, None
    for t in ts:
        v = eval_all(ex, t)
        A = L.local(t)
        for b, val in v.items():
            e = abs(K.wrap(val - A[b]))
            if e > worst:
                worst, worst_at = e, (b, t)
    sl = slider_exprs(spec)
    worst_sl = 0.0
    for t in ts:
        W = L.world_z(t)
        for which, s in sl.items():
            psi = evaluate(s['expr'], {'c': t})
            worst_sl = max(worst_sl, abs(K.wrap(psi - W[s['body']])))
            assert 0.0 <= psi < 2 * math.pi * spec.dials['back'][which]['turns'] + 1e-9
    lengths = {b: len(e['expr']) for b, e in ex.items()}
    simple = all(validate(e['expr']) for e in ex.values()) and all(validate(s['expr']) for s in sl.values())
    rep = {'max_err': worst, 'worst_at': worst_at, 'samples': len(ts), 'bodies': len(ex),
           'max_len': max(lengths.values()), 'all_simple': simple, 'slider_max_err': worst_sl,
           'exprs': {b: e['expr'] for b, e in ex.items()},
           'slider_exprs': {w: s['expr'] for w, s in sl.items()}}
    ok = worst < 1e-9 and worst_sl < 1e-9 and rep['max_len'] <= MAX_LEN and simple and len(ex) == 47
    rep['ok'] = ok
    return ok, rep
