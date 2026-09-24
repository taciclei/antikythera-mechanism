"""Parts catalogue: every modelled piece as 2D islands extruded along z (or x), in its body frame.
Used by the pre-filter (pure Python) and by the Blender build / print export.
Body-local frame: origin at the body axis (z-bodies), world z; 'a': (x, y, z - axis_z);
'q': (u, v, z - 52.70) in the Moon frame; frame/b/moon: world axes."""
import math

import numpy as np

from . import involute as INV
from . import spiral as SP
from .outline import (arm, ccw, circle, cw, gear_loops, n_sides, rect, rotate, rounded_rect,
                      stadium, translate)

TWO_PI = 2.0 * math.pi
DEG = math.pi / 180.0


class Profile:
    """Geometry profile. Values in MODEL units (mm at scale 1); coordinates are multiplied by
    `scale` at the end. Scholarly = the spec model."""

    def __init__(self, name='scholarly', scale=1.0, backlash=0.03, clearance=None, n_flank=24):
        self.name = name
        self.s = float(scale)
        self.printing = clearance is not None
        self.j = backlash / self.s
        self.c = (clearance / self.s) if self.printing else 0.05
        self.n_flank = n_flank

    def hole(self, r_in, r_sch):
        return r_sch if not self.printing else max(r_sch, r_in + self.c)

    @property
    def slot_hw(self):
        return 0.55 if not self.printing else 0.5 + self.c

    @property
    def groove_hw(self):
        return 0.6 if not self.printing else 0.5 + self.c


def print_profiles(spec):
    out = []
    for name in ('resin_x1', 'resin_x1_5', 'fdm_x2'):
        p = spec['print_profiles'][name]
        out.append((Profile(name, p['scale'], p['backlash_mm'], p['bore_clearance_mm']), p))
    return out


def ann_foot(cx, cy, r1, r2):
    return {'ann': (float(cx), float(cy), float(r1), float(r2), True)}


class Catalog:
    def __init__(self, spec, laws, prof=None, phases=None):
        self.spec = spec
        self.laws = laws
        self.p = prof or Profile()
        self.phases = phases if phases is not None else INV.compute_phases(spec, laws)[0]
        self.parts = []
        self.names = set()
        self.intended = []          # (name_a, name_b, reason)
        self.gear_info = {}
        self.axes = spec['axes_world_xy']

    # ------------------------------------------------------------------ helpers
    def local(self, body, xy):
        ax = self.spec.axis_world(body) if body not in ('frame', 'a', 'q') else (0.0, 0.0)
        return (xy[0] - ax[0], xy[1] - ax[1])

    def add(self, name, body, islands, z, status, coll, role='', kind='prism', axis='z',
            material='bronze', foot=None, foot_body=None, fz=None, gear=None, extra=None,
            sources='', printable=True, extruded=True):
        assert name not in self.names, name
        self.names.add(name)
        part = {'name': name, 'body': body, 'islands': islands, 'z': (float(z[0]), float(z[1])),
                'status': status, 'coll': coll, 'role': role, 'kind': kind, 'axis': axis,
                'material': material, 'gear': gear, 'sources': sources, 'print': printable,
                'extruded': extruded and kind == 'prism', 'extra': extra or {},
                'foot': foot if foot is not None else {'islands': islands},
                'foot_body': foot_body or body,
                'fz': tuple(fz) if fz is not None else (float(z[0]), float(z[1]))}
        g = self.spec.gears.get(gear) if gear else None
        part['teeth'] = g['teeth'] if g else 0
        part['module'] = g['module'] if g else 0.0
        self.parts.append(part)
        return part

    def circ(self, cx, cy, r, g=0.05, n=None):
        return ccw(circle(cx, cy, r, n or n_sides(r, g)))

    def disc_part(self, name, body, cxy, r, z, status, coll, role='', g=0.05, material='bronze',
                  r_in=0.0, g_in=0.05, n=None):
        cx, cy = self.local(body, cxy) if body not in ('frame',) else cxy
        if r_in > 0:
            r_in = self.p.hole(r_in - g_in, r_in)
        outer = self.circ(cx, cy, r, g, n)
        isl = [outer]
        if r_in > 0:
            isl.append(cw(circle(cx, cy, r_in, n_sides(r_in, g_in) if n is None else n)))
        nn = n or n_sides(r, g)
        foot = ann_foot(cx, cy, r_in * math.cos(math.pi / (n_sides(r_in, g_in) if n is None else n))
                        if r_in > 0 else 0.0, r)
        return self.add(name, body, [isl], z, status, coll, role, material=material, foot=foot,
                        extra={'n': nn})

    def status_body(self, body):
        return self.spec.status_of_body(body) if self.spec.bodies[body]['gears'] else 'HYPOTHETICAL'

    # ------------------------------------------------------------------ gears
    def gear(self, gid):
        g = self.spec.gears[gid]
        p = self.p
        clr = p.c if p.printing else None
        loops, info = gear_loops(self.spec, gid, self.phases.get(gid, 0.0), j=p.j, n_flank=p.n_flank,
                                 bore_clearance=clr, slot_clearance=p.c)
        self.gear_info[gid] = info
        nb = len(loops[1])
        foot = ann_foot(0, 0, info['bore'] * math.cos(math.pi / nb), info['ra'])
        src = '; '.join(a['source'] for a in g['alternatives']) or 'F06/F21'
        self.add(gid, g['body'], [loops], g['z'], g['status'], 'AM_' + g['status'], g['role'],
                 gear=gid, foot=foot, sources=src)

    # ------------------------------------------------------------------ build all
    def build(self):
        self.build_frame()
        self.build_crank()
        self.build_b()
        self.build_b_children()
        self.build_moon_q()
        self.build_front_outputs()
        self.build_rear()
        self.build_back_dials()
        self.build_front_dials()
        self.build_case()
        self.build_intended()
        return self

    # ------------------------------------------------------------------ frame
    def plate_outline(self):
        return ccw(rounded_rect(-88.0, -160.0, 88.0, 140.0, 4.0))

    def build_frame(self):
        S, A = self.spec, self.axes
        p = self.p
        h105 = p.hole(1.0, 1.05)
        # Main Plate
        holes = [cw(circle(0, 0, p.hole(1.2, 1.4), 64))]
        trav = ['moon_arbor']
        for key, sh in (('D', 'shaft_d'), ('M', 'shaft_m'), ('E', 'shaft_e_inner'), ('F', 'shaft_f'),
                        ('G', 'shaft_g'), ('H', 'shaft_h'), ('I', 'shaft_i'), ('N', 'shaft_n'),
                        ('O', 'shaft_o'), ('P', 'shaft_p'), ('cal', 'shaft_cal')):
            holes.append(cw(circle(*A[key], h105, n_sides(1.0, h105 - 1.0))))
            trav.append(sh)
        self.add('main_plate', 'frame', [[self.plate_outline()] + holes], (-2.0, 0.0), 'SURVIVING',
                 'AM_STRUCTURE', 'Main Plate', extra={'traversal': trav})
        # Back plate with spiral grooves
        holes = []
        trav = []
        for key, sh in (('N', 'shaft_n'), ('G', 'shaft_g'), ('O', 'shaft_o'), ('cal', 'shaft_cal'),
                        ('I', 'shaft_i'), ('M', 'shaft_m'), ('E', 'shaft_e_inner'), ('F', 'shaft_f'),
                        ('H', 'shaft_h'), ('P', 'shaft_p')):
            holes.append(cw(circle(*A[key], h105, n_sides(1.0, h105 - 1.0))))
            trav.append(sh)
        for which in ('metonic', 'saros'):
            d, c = SP.dial(S, which)
            holes.append(SP.groove_loop(c, d['r_start'], d['pitch'], d['turns'], p.groove_hw))
            trav.append(which + '_slider_pin')
        self.add('back_plate', 'frame', [[self.plate_outline()] + holes], (-16.5, -15.0),
                 'RECONSTRUCTED', 'AM_STRUCTURE', 'Back plate with Metonic and Saros spiral grooves',
                 extra={'traversal': trav})
        # Front plate
        hc = S.dials['front']['calendar_ring']['hole_circle']
        holes = [cw(circle(0, 0, self.p.hole(7.5, 7.8), 128))]
        for k in range(hc['count']):
            a = TWO_PI * k / hc['count']
            holes.append(cw(circle(hc['radius'] * math.cos(a), hc['radius'] * math.sin(a),
                                   hc['hole_diameter'] / 2, 12)))
        self.add('front_plate', 'frame', [[self.plate_outline()] + holes], (40.0, 41.5),
                 'RECONSTRUCTED', 'AM_STRUCTURE', 'Front plate (calendar hole circle 354)',
                 extra={'traversal': ['t_date']})
        fp = S.structure['frame_pillars']
        for k, (x, y) in enumerate(fp['xy']):
            self.disc_part('frame_pillar_%d' % (k + 1), 'frame', (x, y), fp['radius'], fp['z'],
                           fp['status'], 'AM_' + fp['status'], 'Frame pillar')
        # crank bracket (extruded along x; 2D = (y, z))
        zc = S.crowns['a1']['axis_z']
        hb = p.hole(1.5, 1.55)
        isl = [ccw(rect(-4.0, 0.0, 4.0, 21.5)), cw(circle(0.0, zc, hb, n_sides(1.5, hb - 1.5)))]
        self.add('crank_bracket', 'frame', [isl], (80.0, 84.0), 'HYPOTHETICAL', 'AM_HYPOTHETICAL',
                 'Crank bracket (bearing of the crank shaft)', axis='x',
                 foot={'islands': [[ccw(rect(80.0, -4.0, 84.0, 4.0))]]}, fz=(0.0, 21.5),
                 extra={'traversal': ['a_shaft']})
        t = S.tubes['fixed_tube']
        self.disc_part('fixed_tube', 'frame', (0, 0), t['r_out'], t['z'], 'HYPOTHETICAL',
                       'AM_STRUCTURE', 'Fixed central tube (carries fx51, fx49)', r_in=t['r_in'])
        for sid in ('stud_c', 'stud_l'):
            it = S.shaft_items[sid]
            self.disc_part(sid, 'frame', S.axis_world(it['axis_body']), it['r'], it['z'],
                           self.status_body(it['axis_body']), 'AM_STRUCTURE', 'Stud (frame)')
        for gid in ('fx51', 'fx49', 'fx56'):
            self.gear(gid)
        sp = S.structure['sub_plate']
        self.add('sub_plate', 'frame', [[ccw(circle(0, 0, 60.0, 256)), cw(circle(0, 0, self.p.hole(7.5, 7.8), 128))]],
                 sp['z'], 'HYPOTHETICAL', 'AM_HYPOTHETICAL', 'Sub-Plate',
                 extra={'traversal': ['t_date']})
        self.disc_part('spacer_ring', 'frame', (0, 0), 12.0, (37.30, 37.45), 'HYPOTHETICAL',
                       'AM_STRUCTURE', 'Spacer ring fx56 - Sub-Plate', r_in=7.8, g_in=0.3)
        for k, a in enumerate((90.0, 210.0, 330.0)):
            self.disc_part('standoff_%d' % (k + 1), 'frame',
                           (57.0 * math.cos(a * DEG), 57.0 * math.sin(a * DEG)), 2.0, (38.65, 40.0),
                           'HYPOTHETICAL', 'AM_STRUCTURE', 'Sub-Plate standoff')

    # ------------------------------------------------------------------ crank (body a)
    def build_crank(self):
        S = self.spec
        c = S.crowns['a1']
        zc = c['axis_z']

        def xfoot(x0, x1, R):
            return ({'islands': [[ccw(rect(x0, -R, x1, R))]]}, (zc - R, zc + R))

        R = max(c['disc']['r_out'], max(c['envelope']['rho_levels']))
        f, fz = xfoot(min(c['envelope']['tip_s_min'], c['disc']['x'][0]), c['disc']['x'][1], R)
        self.add('a1', 'a', [], c['disc']['x'], 'SURVIVING', 'AM_SURVIVING',
                 S.gears['a1']['role'], kind='crown', axis='x', gear='a1', foot=f, foot_body='frame',
                 fz=fz, extra={'crown': 'a1'}, sources='Wright limits', extruded=False)
        r = c['shaft']['radius']
        isl = [self.circ(0.0, 0.0, r, 0.05)]
        f, fz = xfoot(c['shaft']['x'][0], c['shaft']['x'][1], r)
        self.add('a_shaft', 'a', [isl], c['shaft']['x'], 'SURVIVING', 'AM_STRUCTURE',
                 'Crank shaft', axis='x', foot=f, foot_body='frame', fz=fz)
        isl = [ccw(rect(-2.0, 0.0, 2.0, 25.0))]
        f, fz = xfoot(99.0, 101.0, math.hypot(2.0, 25.0))
        self.add('crank_arm', 'a', [isl], (99.0, 101.0), 'HYPOTHETICAL', 'AM_STRUCTURE',
                 'Crank arm', axis='x', foot=f, foot_body='frame', fz=fz)
        isl = [ccw(circle(0.0, 23.0, 3.0, 64))]
        f, fz = xfoot(101.0, 111.0, 26.0)
        self.add('crank_knob', 'a', [isl], (101.0, 111.0), 'HYPOTHETICAL', 'AM_STRUCTURE',
                 'Crank knob', axis='x', foot=f, foot_body='frame', fz=fz)

    # ------------------------------------------------------------------ body b (rigid parts)
    def build_b(self):
        S = self.spec
        for gid in ('b1', 'b2', 'b0'):
            self.gear(gid)
        bs = S.structure['b1_structure']
        self.disc_part('b1_hub', 'b', (0, 0), bs['hub_radius'], (6.65, bs['hub_top_z']),
                       'SURVIVING', 'AM_SURVIVING', 'b1 hub and rivets', r_in=3.2)
        for tid in ('b_hub', 't_meanSun', 't_date'):
            t = S.tubes[tid]
            st = 'SURVIVING' if tid == 'b_hub' else 'HYPOTHETICAL'
            self.disc_part(tid, 'b', (0, 0), t['r_out'], t['z'], st, 'AM_STRUCTURE',
                           'Tube ' + tid, r_in=t['r_in'], g_in=0.2)
        # mean-Sun bar (collar + bar + end block) and post
        Db = self.axes['Dblock']
        ang = math.atan2(Db[1], Db[0])
        L = math.hypot(*Db)
        o = rotate(arm([(0.0, 3.4), (L, 2.2)], 1.5, 0.0, L), ang)
        self.add('mean_sun_bar', 'b', [[o, cw(circle(0, 0, self.p.hole(1.2, 1.4), 64))]], (10.3, 11.3), 'HYPOTHETICAL',
                 'AM_HYPOTHETICAL', 'Mean-Sun bar (drives t_meanSun from spoke D)')
        self.disc_part('mean_sun_post', 'b', Db, 1.5, (6.65, 10.3), 'HYPOTHETICAL',
                       'AM_HYPOTHETICAL', 'Mean-Sun bar post on spoke D')
        # pillars (small dimension radial)
        sp = S.structure['short_pillars']
        for k, (r, a) in enumerate(sp['polar']):
            self.pillar('short_pillar_%d' % (k + 1), r, a, sp['section'], sp['z'], sp['status'])
            self.pillar('short_tenon_%d' % (k + 1), r, a, (2.4, 3.0), (sp['z'][1], sp['tenon_to']),
                        sp['status'])
        lp = S.structure['long_pillars']
        for k, (r, a) in enumerate(lp['polar']):
            self.pillar('long_pillar_%d' % (k + 1), r, a, lp['section'], lp['z'], lp['status'])
            self.pillar('long_tenon_%d' % (k + 1), r, a, (4.0, 5.0), (lp['z'][1], lp['tenon_to']),
                        lp['status'])
        # Strap
        st = S.structure['strap']
        a = -19.0 * DEG
        holes = [cw(circle(0, 0, self.p.hole(7.5, 7.8), 128))]
        for (r, ad) in sp['polar']:
            holes.append(cw(self.pillar_loop(r, ad, (2.4, 3.0))))
        o = ccw(rotate(rect(-61.5, -12.4, 61.5, 12.4), a))
        self.add('strap', 'b', [[o] + holes], st['z'], 'HYPOTHETICAL', 'AM_HYPOTHETICAL',
                 'Strap (carries the me40/me20 studs)', extra={'traversal': ['t_venus']})
        # D-plate and its posts
        dp = S.structure['d_plate']
        a = 161.0 * DEG
        o = ccw(rotate(rect(5.0, -12.65, 34.0, 12.65), a))
        self.add('d_plate', 'b', [[o]], dp['z'], dp['status'], 'AM_' + dp['status'],
                 'D-plate (carries the vn26 and r1 studs)')
        for k, w in enumerate((8.0, -8.0)):
            x, y = rotate(np.array([[22.0, w]]), a)[0]
            self.disc_part('d_post_%d' % (k + 1), 'b', (x, y), 1.0, (18.8, 22.85), dp['status'],
                           'AM_' + dp['status'], 'D-plate post')
        # CP
        cp = S.structure['cp']
        holes = [cw(circle(0, 0, self.p.hole(6.8, 7.0), 128))]
        trav = ['t_saturn']
        for bid in ('x_cp52', 'x_cp64', 'x_su56'):
            h = self.p.hole(1.0, 1.05)
            holes.append(cw(circle(*S.axis_world(bid), h, n_sides(1.0, h - 1.0))))
            trav.append('shaft_' + bid[2:])
        for (r, ad) in lp['polar']:
            holes.append(cw(self.pillar_loop(r, ad, (4.0, 5.0))))
        self.add('cp', 'b', [[ccw(circle(0, 0, 65.0, 512))] + holes], cp['z'], 'HYPOTHETICAL',
                 'AM_HYPOTHETICAL', 'CP (plate carrying the true-Sun and planet trains)',
                 extra={'traversal': trav})
        # studs / bosses owned by b
        for it in S['shafts']['items']:
            if it['owner'] == 'b':
                self.disc_part(it['id'], 'b', S.axis_world(it['axis_body']), it['r'], it['z'],
                               self.status_body(it['axis_body']), 'AM_STRUCTURE',
                               'Stud/boss on b for ' + it['axis_body'])
        # date pointer
        dp = S.dials['front']['date_pointer']
        o = arm([(0.0, 9.0)], dp['width'] / 2, 0.0, dp['length'], tip1='point', tip_len=3.0)
        self.add('date_pointer', 'b', [[o, cw(circle(0, 0, self.p.hole(6.8, 7.0), 128))]], dp['z'], 'RECONSTRUCTED',
                 'AM_DIALS', 'Date pointer / mean Sun (b, local +x)')

    def pillar_loop(self, r, a_deg, section):
        rad, tang = section
        return ccw(rotate(rect(r - rad / 2, -tang / 2, r + rad / 2, tang / 2), a_deg * DEG))

    def pillar(self, name, r, a_deg, section, z, status):
        self.add(name, 'b', [[self.pillar_loop(r, a_deg, section)]], z, status, 'AM_' + status,
                 'Pillar on b1')

    # ------------------------------------------------------------------ b children
    def hub(self, sid):
        it = self.spec.shaft_items[sid]
        body = it['owner']
        ri = self.p.hole(it['r_in'] - 0.05, it['r_in'])
        self.add(sid, body, [[self.circ(0, 0, it['r'], 0.05), cw(circle(0, 0, ri, n_sides(0.8, 0.05)))]],
                 it['z'], self.status_body(body), 'AM_STRUCTURE', 'Hub of ' + body,
                 foot=ann_foot(0, 0, ri * math.cos(math.pi / n_sides(0.8, 0.05)), it['r']))

    def shaft(self, sid):
        it = self.spec.shaft_items[sid]
        body = it['owner']
        if 'r_in' in it:
            self.disc_part(sid, body, self.spec.axis_world(it['axis_body']), it['r'], it['z'],
                           self.status_body(body), 'AM_STRUCTURE', 'Shaft/pipe of ' + body,
                           r_in=it['r_in'], g_in=0.2)
        else:
            self.disc_part(sid, body, self.spec.axis_world(it['axis_body']), it['r'], it['z'],
                           self.status_body(body), 'AM_STRUCTURE', 'Shaft of ' + body)

    def pin(self, pid, body, xy, z, status, coll='AM_STRUCTURE'):
        r = 0.5
        isl = [ccw(circle(xy[0], xy[1], r, 64))]
        self.add(pid, body, [isl], z, status, coll, 'Pin (tenon) r 0.5',
                 foot=ann_foot(xy[0], xy[1], 0.0, r))

    def build_b_children(self):
        S = self.spec
        for bid in ('spA', 'spB', 'spC', 'x_me40', 'x_me20', 'x_vn26', 'x_r1', 'x_cp52', 'x_cp64',
                    'x_su56', 'x_sa40', 'x_sa68', 'x_sa86s', 'x_ju40', 'x_ju43', 'x_ju65s',
                    'x_ma40', 'x_ma71', 'x_ma80s'):
            for gid in S.bodies[bid]['gears']:
                self.gear(gid)
        for it in S['shafts']['items']:
            if it['owner'] in S.bodies and S.bodies[it['owner']]['parent'] == 'b':
                if it['id'].startswith('hub_'):
                    self.hub(it['id'])
                else:
                    self.shaft(it['id'])
        for sid in ('mercury_disk', 'venus_disk'):
            d = S.structure[sid]
            ri = self.p.hole(0.8, 0.85)
            self.add(sid, d['body'], [[self.circ(0, 0, d['radius'], 0, 256),
                                       cw(circle(0, 0, ri, n_sides(0.8, 0.05)))]], d['z'],
                     d['status'], 'AM_' + d['status'], 'Epicycle disk carrying the pin',
                     foot=ann_foot(0, 0, ri * math.cos(math.pi / n_sides(0.8, 0.05)), d['radius']))
        for p in S['shafts']['pins']:
            body = p['owner']
            if body in ('k',):
                continue
            if 'local_xy' in p:
                xy = p['local_xy']
            else:
                f = next(f for f in S.followers if f['id'] == 'trueSun')
                a = f['pin_phase_deg'] * DEG
                xy = (f['pin_d'] * math.cos(a), f['pin_d'] * math.sin(a))
            self.pin(p['id'], body, xy, p['z'], 'HYPOTHETICAL' if body != 'x_r1' else 'SURVIVING')
        self.intended_pins = [(p['id'], p['slot_in']) for p in S['shafts']['pins']]

    # ------------------------------------------------------------------ Moon and q
    def build_moon_q(self):
        S = self.spec
        self.gear('b3')
        t = S.tubes['moon_arbor']
        self.disc_part('moon_arbor', 'moon', (0, 0), t['r_out'], t['z'], 'SURVIVING',
                       'AM_STRUCTURE', 'Central Moon arbor')
        mp = S.dials['front']['moon_pointer']
        w = mp['window']
        o = arm([(0.0, 3.0), (w['centre_u'], w['ring_boss_r_out'])], mp['width'] / 2, 0.0,
                mp['length'], tip1='point', tip_len=3.0)
        self.add('moon_pointer', 'moon', [[o, cw(circle(w['centre_u'], 0, w['diameter'] / 2, 128))]],
                 mp['arm_z'], 'HYPOTHETICAL', 'AM_DIALS', 'Moon pointer with phase window')
        q1 = S.crowns['q1']
        zc = q1['axis_z']
        hr = self.p.hole(q1['arbor']['radius'], 0.65)
        nq = n_sides(q1['arbor']['radius'], hr - q1['arbor']['radius'])
        for k, (u0, u1) in enumerate(((2.3, 2.9), (16.8, 17.4))):
            isl = [ccw(rect(-1.2, 51.4, 1.2, 58.6)), cw(circle(0.0, zc, hr, nq))]
            self.add('moon_hanger_%d' % (k + 1), 'moon', [isl], (u0, u1), 'HYPOTHETICAL',
                     'AM_STRUCTURE', 'Hanger bracket of the q1 arbor', axis='x',
                     foot={'islands': [[ccw(rect(u0, -1.2, u1, 1.2))]]}, fz=(51.4, 58.6),
                     extra={'traversal': ['q_arbor']})

        def qfoot(u0, u1, R):
            return {'islands': [[ccw(rect(u0, -R, u1, R))]]}, (zc - R, zc + R)

        R = max(q1['disc']['r_out'], max(q1['envelope']['rho_levels']))
        f, fz = qfoot(q1['envelope']['tip_s_min'], q1['disc']['u'][1], R)
        self.add('q1', 'q', [], q1['disc']['u'], 'SURVIVING', 'AM_SURVIVING', S.gears['q1']['role'],
                 kind='crown', axis='x', gear='q1', foot=f, foot_body='moon', fz=fz,
                 extra={'crown': 'q1'}, extruded=False)
        ra = q1['arbor']['radius']
        f, fz = qfoot(q1['arbor']['u'][0], q1['arbor']['u'][1], ra)
        self.add('q_arbor', 'q', [[ccw(circle(0.0, 0.0, ra, nq))]], q1['arbor']['u'], 'SURVIVING',
                 'AM_STRUCTURE', 'Radial arbor of q1', axis='x', foot=f, foot_body='moon', fz=fz)
        ps = q1['phase_sphere']
        f, fz = qfoot(ps['centre_u'] - ps['radius'], ps['centre_u'] + ps['radius'], ps['radius'])
        for name, up, mat in (('phase_sphere_dark', 1, 'dark'), ('phase_sphere_silver', -1, 'silver')):
            self.add(name, 'q', [], (0, 0), 'HYPOTHETICAL', 'AM_DIALS', 'Moon-phase sphere half',
                     kind='hemisphere', material=mat, foot=f, foot_body='moon', fz=fz,
                     extra={'center': (ps['centre_u'], 0.0, ps['centre_z'] - zc), 'radius': ps['radius'],
                            'up': up}, extruded=False)

    # ------------------------------------------------------------------ front outputs
    def build_front_outputs(self):
        S = self.spec
        self.gear('nd48')
        t = S.tubes['t_nodes']
        self.disc_part('t_nodes', 't_nodes', (0, 0), t['r_out'], t['z'], 'HYPOTHETICAL',
                       'AM_STRUCTURE', 'Tube of the Dragon Hand', r_in=t['r_in'], g_in=0.2)
        dh = S.dials['front']['dragon_hand']
        o = arm([(0.0, 3.5)], 1.0, -dh['half_length'], dh['half_length'], tip0='point', tip1='point',
                tip_len=2.5)
        self.add('dragon_hand', 't_nodes', [[o, cw(circle(0, 0, self.p.hole(1.9, 2.1), 64))]], dh['z'], dh['status'],
                 'AM_DIALS', 'Dragon Hand (lunar nodes)')
        fol = {f['body']: f for f in S.followers}
        levers = {'t_mercury': ('mercury_follower', 4.5), 't_venus': ('venus_follower', 5.2),
                  't_trueSun': ('true_sun_follower', 6.0)}
        rings = {r['body']: r for r in S.dials['front']['cosmos_rings']}
        for bid in ('t_mercury', 't_venus', 't_trueSun', 't_mars', 't_jupiter', 't_saturn'):
            t = S.tubes[bid]
            self.disc_part(bid, bid, (0, 0), t['r_out'], t['z'], 'HYPOTHETICAL', 'AM_STRUCTURE',
                           'Output tube ' + bid, r_in=t['r_in'], g_in=0.2)
            for gid in S.bodies[bid]['gears']:
                self.gear(gid)
            if bid in levers:
                name, rh = levers[bid]
                st = S.structure[name]
                f = fol[bid]
                r_end = {'mercury_follower': 52.0, 'venus_follower': 49.5,
                         'true_sun_follower': 43.5}[name]
                o = arm([(0.0, rh)], 1.5, 0.0, r_end, tip1='round')
                hw = self.p.slot_hw
                s0 = f['i'] - f['pin_d'] - 0.6 - (hw - 0.55)
                s1 = f['i'] + f['pin_d'] + 0.6 + (hw - 0.55)
                isl = [o, cw(circle(0, 0, self.p.hole(t['r_in'] - 0.2, t['r_in']), 64)), cw(stadium(s0, s1, hw))]
                x, y = f['epicycle_axis_xy_in_b']
                g0 = math.atan2(y, x)
                amp = math.asin(f['pin_d'] / f['i'])
                self.add(name, bid, [isl], st['z'], st['status'], 'AM_' + st['status'],
                         'Follower lever with radial slot',
                         extra={'lever': (g0 - amp, g0 + amp), 'r_max': r_end})
            rg = rings[bid]
            self.add('ring_' + bid[2:], bid, [[ccw(circle(0, 0, rg['radii'][1], 256)),
                                               cw(circle(0, 0, self.p.hole(t['r_in'] - 0.2, t['r_in']), 64))]], rg['z'],
                     'HYPOTHETICAL', 'AM_DIALS', 'Cosmos ring (%s), LOW-confidence radii' % rg['label'],
                     foot=ann_foot(0, 0, t['r_in'] * math.cos(math.pi / 64), rg['radii'][1]))
            gold = bid == 't_trueSun'
            rr = 1.6 if gold else 1.2
            a = rg['marker_local_deg'] * DEG
            cx, cy = rg['marker_r'] * math.cos(a), rg['marker_r'] * math.sin(a)
            cz = rg['z'][1] + rr
            self.add('marker_' + bid[2:], bid, [], (cz - rr, cz + rr), 'HYPOTHETICAL', 'AM_DIALS',
                     'Marker sphere resting on the ring', kind='sphere',
                     material='gold' if gold else 'stone', foot=ann_foot(cx, cy, 0.0, rr),
                     extra={'center': (cx, cy, cz), 'radius': rr}, extruded=False)

    # ------------------------------------------------------------------ rear trains
    def build_rear(self):
        S = self.spec
        for bid in ('c', 'd', 'e_pipe', 'e_table', 'e_inner', 'k', 'kp', 'l', 'm', 'f', 'g', 'h',
                    'i', 'n', 'o', 'p', 'cal'):
            for gid in S.bodies[bid]['gears']:
                self.gear(gid)
        rear = ('c', 'd', 'e_pipe', 'e_inner', 'l', 'm', 'f', 'g', 'h', 'i', 'n', 'o', 'p', 'cal')
        for it in S['shafts']['items']:
            if it['owner'] in rear:
                self.shaft(it['id'])
        for bid in ('c', 'l'):
            z1 = max(S.gears[g]['z'][1] for g in S.bodies[bid]['gears'])
            ri = self.p.hole(1.2, 1.25)
            self.add('hub_' + bid, bid, [[self.circ(0, 0, 2.5, 0.05),
                                          cw(circle(0, 0, ri, n_sides(1.2, 0.05)))]], (0.15, z1),
                     'SURVIVING', 'AM_STRUCTURE', 'Hub joining the two wheels of ' + bid,
                     foot=ann_foot(0, 0, ri * math.cos(math.pi / n_sides(1.2, 0.05)), 2.5))
        # e_table: boss_k, stud_kp, e4 spacers
        K = S['axes_e3_local_xy']['K']
        Kp = S['axes_e3_local_xy']['Kp']
        it = S.shaft_items['boss_k']
        self.add('boss_k', 'e_table', [[self.circ(K[0], K[1], it['r'])]], it['z'], 'SURVIVING',
                 'AM_STRUCTURE', 'Boss of k1 on e3', foot=ann_foot(K[0], K[1], 0, it['r']))
        it = S.shaft_items['stud_kp']
        self.add('stud_kp', 'e_table', [[self.circ(Kp[0], Kp[1], it['r'])]], it['z'], 'SURVIVING',
                 'AM_STRUCTURE', 'Stud of k2 on e3', foot=ann_foot(Kp[0], Kp[1], 0, it['r']))
        isl = []
        for k in range(6):
            a = k * 60.0 * DEG
            isl.append([ccw(circle(46.0 * math.cos(a), 46.0 * math.sin(a), 1.0, 32))])
        self.add('e4_spacers', 'e_table', isl, (-6.60, -6.45), 'SURVIVING', 'AM_STRUCTURE',
                 'Spacers joining e4 to e3', foot={'islands': [[ccw(circle(0, 0, 47.0, 128)),
                                                                cw(circle(0, 0, 45.0, 128))]]})
        self.pin('pin_lunar', 'k', S.pins['pin_lunar']['local_xy'], S.pins['pin_lunar']['z'],
                 'SURVIVING')
        # back pointers
        back = S.dials['back']
        for which in ('metonic', 'saros'):
            d = back[which]
            body = d['pointer_body']
            o = rotate(arm([(0.0, 2.5)], 1.0, 0.0, d['pointer']['length'], tip1='point', tip_len=3.0),
                       math.pi / 2)
            self.add(which + '_pointer', body, [[ccw(o)]], d['pointer']['z'], d['status'], 'AM_DIALS',
                     '%s spiral pointer (local +y)' % which.capitalize())
            self.slider(which, d, body)
        for sd in back['subsidiary']:
            body = sd['pointer_body']
            o = rotate(arm([(0.0, 2.0)], 0.75, 0.0, sd['pointer']['length'], tip1='point',
                           tip_len=2.0), math.pi / 2)
            self.add(sd['id'] + '_pointer', body, [[ccw(o)]], sd['pointer']['z'], sd['status'],
                     'AM_DIALS', '%s pointer (local +y)' % sd['id'].capitalize())

    def slider(self, which, d, body):
        S = self.spec
        psi, rho = SP.lookup(d['r_start'], d['pitch'], d['turns'], 250)
        rmin, rmax = float(rho.min()), float(rho.max())
        z0 = d['pointer']['z'][0] - 0.15
        z1 = d['pointer']['z'][1]
        blk = ccw(rect(-1.6, -1.5, 1.6, 1.5))
        foot = {'islands': [[ccw(rect(-1.6, rmin - 1.5, 1.6, rmax + 1.5))]]}
        ex = {'slider': which, 'rho_range': (rmin, rmax)}
        self.add(which + '_slider', body, [[blk]], (z0, z1), d['status'], 'AM_DIALS',
                 'Radial slider of the %s pointer' % which, foot=foot, extra=ex)
        _, c = SP.dial(S, which)
        band = SP.spiral_band_loop(c, d['r_start'], d['pitch'], d['turns'], 0.5, math.radians(1.0))
        self.add(which + '_slider_pin', body, [[ccw(circle(0, 0, 0.5, 64))]], (z1, -15.6), d['status'],
                 'AM_DIALS', 'Slider pin riding in the %s groove' % which,
                 foot={'islands': [[band]]}, foot_body='frame', extra=dict(ex))

    # ------------------------------------------------------------------ back dial marks
    def build_back_dials(self):
        S = self.spec
        back = S.dials['back']
        z = (-16.8, -16.5)
        for which in ('metonic', 'saros'):
            d, c = SP.dial(S, which)
            marks = SP.cell_marks(c, d['r_start'], d['pitch'], d['turns'], d['cells'], 0.6)
            self.add(which + '_cells', 'frame', [[m] for m in marks], z, d['status'], 'AM_DIALS',
                     '%s cells (%d)' % (which, d['cells']), material='text')
            self.add(which + '_rim', 'frame', [[ccw(circle(c[0], c[1], 71.7, 512)),
                                                cw(circle(c[0], c[1], 71.2, 512))]], z, d['status'],
                     'AM_DIALS', '%s dial rim' % which, material='text')
        for sd in back['subsidiary']:
            c = S['axes_world_xy'][sd['centre']]
            R = sd['radius']
            L = sd['pointer']['length']
            isl = [[ccw(circle(c[0], c[1], R + 0.15, 256)), cw(circle(c[0], c[1], R - 0.15, 256))]]
            tilt = sd.get('sector_tilt_deg', 0.0)
            for k in range(sd['sectors']):
                psi = (tilt + 360.0 * k / sd['sectors']) * DEG
                dvec = np.array([-math.sin(psi), math.cos(psi)])
                pvec = np.array([math.cos(psi), math.sin(psi)])
                r0, r1 = L + 0.3, R + 0.5
                q = np.array([c + r0 * dvec - 0.15 * pvec, c + r0 * dvec + 0.15 * pvec,
                              c + r1 * dvec + 0.15 * pvec, c + r1 * dvec - 0.15 * pvec])
                isl.append([ccw(q)])
            self.add(sd['id'] + '_dial', 'frame', isl, z, sd['status'], 'AM_DIALS',
                     '%s subsidiary dial (%d sectors)' % (sd['id'], sd['sectors']), material='text')

    # ------------------------------------------------------------------ front dials
    def build_front_dials(self):
        S = self.spec
        fr = S.dials['front']
        zr = fr['zodiac_ring']
        r0, r1 = zr['radii']
        self.add('zodiac_ring', 'frame', [[ccw(circle(0, 0, r1, 720)), cw(circle(0, 0, r0, 720))]],
                 (zr['z_face'], zr['z_face'] + 0.1), zr['status'], 'AM_DIALS', 'Zodiac ring (360 deg)')
        isl = []
        for k in range(zr['divisions']):
            major = k % 30 == 0
            a = -k * DEG            # longitudes increase clockwise seen from the front
            w = 0.3 if major else 0.12
            ra = r0 + 0.3 if major else r1 - 1.6
            isl.append([ccw(rotate(rect(ra, -w / 2, r1 - 0.3, w / 2), a))])
        self.add('zodiac_marks', 'frame', isl, (zr['z_face'] + 0.1, zr['z_face'] + 0.15),
                 zr['status'], 'AM_DIALS', 'Zodiac degree marks and sign boundaries', material='text')
        cr = fr['calendar_ring']
        r0, r1 = cr['radii']
        self.add('calendar_ring', 'frame', [[ccw(circle(0, 0, r1, 720)), cw(circle(0, 0, r0, 720))]],
                 cr['z'], cr['status'], 'AM_DIALS', 'Egyptian calendar ring (modelled fixed)')
        isl = []
        for k in range(cr['day_divisions']):
            major = (k % 30 == 0 and k <= 360)
            a = -k * TWO_PI / cr['day_divisions']
            w = 0.3 if major else 0.1
            ra = r0 + 0.4 if major else r1 - 1.5
            isl.append([ccw(rotate(rect(ra, -w / 2, r1 - 0.3, w / 2), a))])
        self.add('calendar_marks', 'frame', isl, (cr['z'][1], cr['z'][1] + 0.05), cr['status'],
                 'AM_DIALS', 'Calendar day marks (365) and month boundaries', material='text')
        pp = fr['parapegma']
        for k, pl in enumerate(pp['plates']):
            y0, y1 = pl['y']
            self.add('parapegma_%d' % (k + 1), 'frame',
                     [[ccw(rect(pp['x'][0], y0, pp['x'][1], y1))]], pp['z'], pp['status'], 'AM_DIALS',
                     'Parapegma plate (placeholder)')
            isl = []
            for col in range(2):
                xa = pp['x'][0] + 4.0 + col * 80.0
                n_lines = int((y1 - y0 - 6.0) // 4.0)
                for ln in range(n_lines):
                    yy = y1 - 4.0 - ln * 4.0
                    L = 60.0 - 11.0 * ((ln * 7 + col * 3) % 4)
                    isl.append([ccw(rect(xa, yy - 0.2, xa + L, yy + 0.2))])
            self.add('parapegma_lines_%d' % (k + 1), 'frame', isl, (pp['z'][1], pp['z'][1] + 0.05),
                     pp['status'], 'AM_DIALS', 'Parapegma engraved lines (placeholder)', material='text')

    # ------------------------------------------------------------------ case
    def build_case(self):
        zc = self.spec.crowns['a1']['axis_z']
        z = (-24.0, 62.0)
        W = 5.0
        st = 'RECONSTRUCTED'
        self.add('case_left', 'frame', [[ccw(rect(-92.0 - W, -164.0 - W, -92.0, 144.0 + W))]], z, st,
                 'AM_CASE', 'Case wall', material='wood')
        self.add('case_bottom', 'frame', [[ccw(rect(-92.0, -164.0 - W, 92.0, -164.0))]], z, st,
                 'AM_CASE', 'Case wall', material='wood')
        self.add('case_top', 'frame', [[ccw(rect(-92.0, 144.0, 92.0, 144.0 + W))]], z, st,
                 'AM_CASE', 'Case wall', material='wood')
        h = self.p.hole(1.5, 1.55)
        isl = [ccw(rect(-164.0 - W, z[0], 144.0 + W, z[1])), cw(circle(0.0, zc, h, n_sides(1.5, h - 1.5)))]
        self.add('case_right', 'frame', [isl], (92.0, 92.0 + W), st, 'AM_CASE',
                 'Case wall with crank-shaft hole', axis='x', material='wood',
                 foot={'islands': [[ccw(rect(92.0, -164.0 - W, 92.0 + W, 144.0 + W))]]}, fz=z,
                 extra={'traversal': ['a_shaft']})
        for name, zz in (('case_cover_front', (62.0, 67.0)), ('case_cover_back', (-29.0, -24.0))):
            self.add(name, 'frame', [[ccw(rect(-92.0 - W, -164.0 - W, 92.0 + W, 144.0 + W))]], zz,
                     st, 'AM_CASE', 'Case cover (hidden by default)', material='wood',
                     extra={'hidden': True})

    # ------------------------------------------------------------------ intended contacts
    def build_intended(self):
        S = self.spec
        for m in S.meshes:
            self.intended.append((m['driver'], m['driven'], 'mesh'))
        for pid, slot in self.intended_pins:
            self.intended.append((pid, slot, 'pin-slot'))
        for which in ('metonic', 'saros'):
            self.intended.append((which + '_slider_pin', which + '_cells', 'pin-groove dial'))
        for p in self.parts:
            for t in p['extra'].get('traversal', []):
                self.intended.append((t, p['name'], 'shaft-plate'))
        names = {p['name'] for p in self.parts}
        for a, b, _ in self.intended:
            assert a in names and b in names, (a, b)

    def by_name(self):
        return {p['name']: p for p in self.parts}


def build(spec, laws, prof=None, phases=None):
    return Catalog(spec, laws, prof, phases).build()


def scaled(part, s):
    """Scale a part's geometry (for print export)."""
    if s == 1.0:
        return part
    q = dict(part)
    q['islands'] = [[l * s for l in isl] for isl in part['islands']]
    q['z'] = (part['z'][0] * s, part['z'][1] * s)
    ex = dict(part['extra'])
    if 'center' in ex:
        ex['center'] = tuple(c * s for c in ex['center'])
        ex['radius'] = ex['radius'] * s
    q['extra'] = ex
    return q
