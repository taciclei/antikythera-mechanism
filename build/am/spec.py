"""Load, fingerprint and validate the specification (single source of truth)."""
import hashlib
import json
import os
from fractions import Fraction

from . import ROOT

SPEC_PATH = os.path.join(ROOT, 'spec', 'antikythera.json')
EXPECTED_SHA256 = '18934c80264941ed315ced4273d0b16d733132a296d64e25300bea5576ab86b3'
SECTION_SHA16 = {
    'meta': '77963810ccaa7144', 'conventions': 'af4c802d9ae056bf', 'tooth': '93fb0961a01aa09a',
    'crowns': '8a954c9370248f11', 'tubes': '944b9da8a04324e3', 'shafts': '9148da89bf733376',
    'layers': '83c07f497ff003e1', 'structure': 'f006f499597321c3', 'dials': 'ba888f45f7eee551',
    'materials': 'd65e7385e381163e', 'collections': 'cbb11ec44a0b52fa',
    'print_profiles': '9da46f0dab38ee62', 'render': '5b70c502b4cf2144', 'sources': '25ab64b512ef9546',
    'reference_values_days': '95a6e4108910d168', 'unresolved_defaults': 'bf1cae6e62624373',
    'gears': '37752b74f1ce9551', 'bodies': 'c26ea54b7bf3bcc5', 'meshes': 'a9fec5db88e1f6a8',
    'pin_slots': 'c725ddbf931ff550', 'followers': '212f41ca5b8917ed', 'targets': 'c2c1ccd0cf1098a0',
    'axes_world_xy': '6b172d0f645b5386', 'axes_e3_local_xy': '3b4aed434f19bbb3',
}
STATUSES = ('SURVIVING', 'RECONSTRUCTED', 'HYPOTHETICAL')


def canonical_hash(obj):
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode()).hexdigest()


def frac(s):
    return None if s is None else Fraction(s)


class Spec:
    """Typed access to the JSON spec. Values are never modified."""

    def __init__(self, data):
        self.d = data
        self.gears = {g['id']: g for g in data['gears']}
        self.bodies = {b['id']: b for b in data['bodies']}
        self.meshes = data['meshes']
        self.external_meshes = [m for m in data['meshes'] if m['type'] == 'external']
        self.crown_meshes = [m for m in data['meshes'] if m['type'] == 'crown']
        self.pin_slots = data['pin_slots']
        self.followers = data['followers']
        self.targets = data['targets']
        self.tubes = {t['id']: t for t in data['tubes']}
        self.shaft_items = {s['id']: s for s in data['shafts']['items']}
        self.pins = {p['id']: p for p in data['shafts']['pins']}
        self.structure = {s['id']: s for s in data['structure']}
        self.crowns = data['crowns']
        self.tooth = data['tooth']
        self.dials = data['dials']

    def __getitem__(self, k):
        return self.d[k]

    def parent(self, body):
        return self.bodies[body]['parent']

    def body_of(self, gear):
        return self.gears[gear]['body']

    def axis_world(self, body):
        """World XY of a z-axis body's axis at crank = 0 (carrier angles are 0 at crank 0)."""
        b = self.bodies[body]
        if b['axis_xy_in_parent'] is None:
            return (0.0, 0.0)
        x, y = b['axis_xy_in_parent']
        p = b['parent']
        if p in (None, 'frame'):
            return (x, y)
        px, py = self.axis_world(p)
        return (px + x, py + y)

    def gear_axis_carrier(self, gear, carrier):
        """Axis XY of a gear's body in the frame of `carrier` at crank 0."""
        wx, wy = self.axis_world(self.body_of(gear))
        cx, cy = (0.0, 0.0) if carrier in ('frame', 'b', 'moon') else self.axis_world(carrier)
        return (wx - cx, wy - cy)

    def status_of_body(self, body):
        st = [self.gears[g]['status'] for g in self.bodies[body]['gears']]
        for s in STATUSES[::-1]:
            if s in st:
                return s
        return 'HYPOTHETICAL'


def load(path=SPEC_PATH):
    with open(path, encoding='utf-8') as f:
        return Spec(json.load(f))


def fingerprint_report(data):
    full = canonical_hash(data)
    sections = {k: canonical_hash(data[k])[:16] == v if k in data else False
                for k, v in SECTION_SHA16.items()}
    return {'sha256': full, 'ok': full == EXPECTED_SHA256, 'sections': sections,
            'extra_keys': sorted(set(data) - set(SECTION_SHA16))}


def validate(data):
    """Structural validation. Returns a list of error strings (empty = valid)."""
    err = []
    for k in SECTION_SHA16:
        if k not in data:
            err.append('missing section %s' % k)
    if err:
        return err
    body_ids = {b['id'] for b in data['bodies']}
    gear_ids = set()
    for g in data['gears']:
        for key in ('id', 'teeth', 'module', 'body', 'z', 'kind', 'status', 'bore_radius', 'mount'):
            if key not in g:
                err.append('gear %s: missing %s' % (g.get('id'), key))
        if g['id'] in gear_ids:
            err.append('duplicate gear %s' % g['id'])
        gear_ids.add(g['id'])
        if not isinstance(g['teeth'], int) or g['teeth'] < 8:
            err.append('gear %s: bad teeth' % g['id'])
        if g['body'] not in body_ids:
            err.append('gear %s: unknown body %s' % (g['id'], g['body']))
        if not (len(g['z']) == 2 and g['z'][0] < g['z'][1]):
            err.append('gear %s: bad z' % g['id'])
        if g['status'] not in STATUSES:
            err.append('gear %s: bad status' % g['id'])
    for b in data['bodies']:
        if b['parent'] is not None and b['parent'] not in body_ids:
            err.append('body %s: unknown parent' % b['id'])
        for g in b['gears']:
            if g not in gear_ids:
                err.append('body %s: unknown gear %s' % (b['id'], g))
            elif next(x for x in data['gears'] if x['id'] == g)['body'] != b['id']:
                err.append('body %s: gear %s owned elsewhere' % (b['id'], g))
        for key in ('rate_abs_mean', 'rate_rel_parent_mean'):
            if b[key] is not None:
                try:
                    Fraction(b[key])
                except ValueError:
                    err.append('body %s: bad %s' % (b['id'], key))
    for m in data['meshes']:
        for k in ('driver', 'driven'):
            if m[k] not in gear_ids:
                err.append('mesh: unknown gear %s' % m[k])
        if m['carrier'] not in body_ids:
            err.append('mesh: unknown carrier %s' % m['carrier'])
    for ps in data['pin_slots']:
        for k in ('pin_gear', 'slot_gear'):
            if ps[k] not in gear_ids:
                err.append('pin_slot %s: unknown %s' % (ps['id'], k))
    for f in data['followers']:
        if f['body'] not in body_ids or f['epicycle_body'] not in body_ids:
            err.append('follower %s: unknown body' % f['id'])
    for t in data['targets']:
        try:
            Fraction(t['value'])
        except ValueError:
            err.append('target %s: bad value' % t['name'])
    for s in data['shafts']['items']:
        if s['owner'] not in body_ids or s['axis_body'] not in body_ids:
            err.append('shaft %s: unknown body' % s['id'])
    for t in data['tubes']:
        if t['body'] not in body_ids:
            err.append('tube %s: unknown body' % t['id'])
    if len(data['gears']) != 69:
        err.append('expected 69 gears, got %d' % len(data['gears']))
    return err
