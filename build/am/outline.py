"""2D outlines: circles with clearance-driven side counts, slots, arms, windows, gear loops.
Convention: loops[0] = outer boundary CCW, loops[1:] = holes CW. Units mm."""
import math

import numpy as np

from .involute import Involute, dedupe

TWO_PI = 2.0 * math.pi


def n_sides(R, g, nmin=64):
    """Sides of a polygon circle facing a radial clearance g (spec shafts.rules)."""
    if g <= 0 or R <= 0:
        return nmin
    return max(nmin, int(math.ceil(math.pi / math.acos(R / (R + g)))) + 8)


def signed_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def ccw(p):
    return p if signed_area(p) > 0 else p[::-1].copy()


def cw(p):
    return p if signed_area(p) < 0 else p[::-1].copy()


def circle(cx, cy, r, n=64, start=0.0):
    a = start + np.arange(n) * TWO_PI / n
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)


def arc(cx, cy, r, a0, a1, step=math.radians(3.0), include_end=True):
    n = max(1, int(math.ceil(abs(a1 - a0) / step)))
    a = np.linspace(a0, a1, n + 1)
    if not include_end:
        a = a[:-1]
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)


def rect(x0, y0, x1, y1):
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float)


def rounded_rect(x0, y0, x1, y1, r, step=math.radians(10.0)):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -math.pi / 2), (x1 - r, y1 - r, 0.0),
                       (x0 + r, y1 - r, math.pi / 2), (x0 + r, y0 + r, math.pi)):
        pts.append(arc(cx, cy, r, a0, a0 + math.pi / 2, step))
    return dedupe(np.vstack(pts))


def stadium(x0, x1, hw, y=0.0, step=math.radians(10.0)):
    """Slot along x with extent x0..x1 (round ends included), half-width hw. CCW."""
    c0, c1 = x0 + hw, x1 - hw
    a = arc(c1, y, hw, -math.pi / 2, math.pi / 2, step)
    b = arc(c0, y, hw, math.pi / 2, 3 * math.pi / 2, step)
    return dedupe(np.vstack([a, b]))


def rotate(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    return p @ np.array([[c, s], [-s, c]])


def translate(p, dx, dy):
    return p + np.array([dx, dy])


def arm(circles, hw, u0, u1, tip0=None, tip1='point', tip_len=None, step=math.radians(4.0)):
    """Union of a bar (along +u, |v| <= hw, u0..u1) and circles [(uc, R)] with R > hw, as one CCW
    loop. An end covered by a circle is capped by that circle; otherwise tip in
    {'point', 'round', 'flat'}. Circles must not overlap each other."""
    circles = sorted(circles)
    tl = tip_len if tip_len is not None else 2.0 * hw

    def covers(c, u):
        uc, R = c
        return abs(u - uc) < math.sqrt(R * R - hw * hw) - 1e-9

    cap0 = next((c for c in circles if covers(c, u0)), None)
    cap1 = next((c for c in circles if covers(c, u1)), None)
    mids = [c for c in circles if c is not cap0 and c is not cap1]
    bottom, top = [], []
    # bottom path, left -> right (y = -hw)
    if cap0 is None:
        if tip0 == 'point':
            bottom += [(u0, 0.0), (u0 + tl, -hw)]
        elif tip0 == 'round':
            bottom += list(map(tuple, arc(u0 + hw, 0.0, hw, math.pi, 1.5 * math.pi, step)))
        else:
            bottom += [(u0, 0.0), (u0, -hw)]
    else:
        uc, R = cap0
        bottom.append((uc + math.sqrt(R * R - hw * hw), -hw))
    for uc, R in mids:
        s = math.sqrt(R * R - hw * hw)
        a0, a1 = math.atan2(-hw, -s), math.atan2(-hw, s)
        bottom += list(map(tuple, arc(uc, 0.0, R, a0, a1, step)))
    if cap1 is None:
        if tip1 == 'point':
            bottom += [(u1 - tl, -hw), (u1, 0.0)]
            top += [(u1 - tl, hw)]
        elif tip1 == 'round':
            bottom += list(map(tuple, arc(u1 - hw, 0.0, hw, -math.pi / 2, math.pi / 2, step)))
        else:
            bottom += [(u1, -hw), (u1, hw)]
    else:
        uc, R = cap1
        s = math.sqrt(R * R - hw * hw)
        bottom += list(map(tuple, arc(uc, 0.0, R, math.atan2(-hw, -s), math.atan2(hw, -s), step)))
    for uc, R in reversed(mids):
        s = math.sqrt(R * R - hw * hw)
        a0, a1 = math.atan2(hw, s), math.atan2(hw, -s)
        top += list(map(tuple, arc(uc, 0.0, R, a0, a1, step)))
    if cap0 is None:
        if tip0 == 'point':
            top += [(u0 + tl, hw)]
        elif tip0 == 'round':
            top += list(map(tuple, arc(u0 + hw, 0.0, hw, 0.5 * math.pi, math.pi, step)))[:-1]
        else:
            top += [(u0, hw)]
    else:
        uc, R = cap0
        s = math.sqrt(R * R - hw * hw)
        top += list(map(tuple, arc(uc, 0.0, R, math.atan2(hw, s), math.atan2(-hw, s) + TWO_PI, step)))[:-1]
    pts = dedupe(np.array(bottom + top, float))
    return ccw(pts)


def window(Rh, Rr, a0, a1, h0, h1, step=math.radians(2.0)):
    """Window between the arm at angle a0 (half-width h0) and the arm at a1 > a0 (half-width h1),
    radially between Rh and Rr. Returns a CW loop (hole) or None if degenerate."""
    u0 = np.array([math.cos(a0), math.sin(a0)])
    n0 = np.array([-math.sin(a0), math.cos(a0)])
    u1 = np.array([math.cos(a1), math.sin(a1)])
    n1 = np.array([-math.sin(a1), math.cos(a1)])
    if h0 >= Rr or h1 >= Rr:
        return None
    o0, o1 = a0 + math.asin(h0 / Rr), a1 - math.asin(h1 / Rr)
    if o1 - o0 < 1e-3:
        return None
    outer = arc(0, 0, Rr, o0, o1, step)
    inner_ok = Rh > max(h0, h1) and (a1 - math.asin(h1 / Rh)) - (a0 + math.asin(h0 / Rh)) > 1e-3
    if inner_ok:
        inner = arc(0, 0, Rh, a1 - math.asin(h1 / Rh), a0 + math.asin(h0 / Rh), step)
        pts = np.vstack([outer, inner])
    else:
        # the two offset lines meet before reaching Rh: p = t0*u0 + h0*n0 = t1*u1 - h1*n1
        A = np.stack([u0, -u1], axis=1)
        t = np.linalg.solve(A, -h1 * n1 - h0 * n0)
        X = t[0] * u0 + h0 * n0
        if np.linalg.norm(X) >= Rr - 0.3:
            return None
        pts = np.vstack([outer, X[None, :]])
    return cw(dedupe(pts))


def gear_windows(r_hub, r_rim, n, widths, offset=0.0):
    """n windows between arms at offset + 2*pi*i/n (widths[i] = full arm width)."""
    out = []
    for i in range(n):
        a0 = offset + TWO_PI * i / n
        a1 = offset + TWO_PI * (i + 1) / n
        w = window(r_hub, r_rim, a0, a1, widths[i] / 2, widths[(i + 1) % n] / 2)
        if w is not None:
            out.append(w)
    return out


PIN_SLOT_GEARS = ('k1', 'k2', 'sa68', 'sa86s', 'ju43', 'ju65s', 'ma71', 'ma80s')


def support_radius(g):
    """Radius of the shaft/stud/boss inside a gear bore."""
    return g['bore_radius'] - 0.05 if g['mount'].startswith('rides_on') else g['bore_radius']


def gear_loops(spec, gid, phase, j=0.03, n_flank=24, scale=1.0, bore_clearance=None,
               slot_clearance=0.05):
    """Outline loops of a spur gear in its body frame (local +x = tooth phase reference).
    Returns (loops, info). scale/bore_clearance are used by the print profiles."""
    g = spec.gears[gid]
    z, m = g['teeth'], g['module'] * scale
    inv_ = Involute(z, m, j=j)
    outer = inv_.outline(phase, n_flank)
    holes = []
    sup = support_radius(g) * scale
    if g['kind'] == 'annulus_external':
        bore = g['annulus_inner_radius'] * scale
        nb = 256
    else:
        bore = g['bore_radius'] * scale if bore_clearance is None else sup + bore_clearance
        nb = n_sides(sup, bore - sup) if bore > sup else 64
    holes.append(cw(circle(0, 0, bore, nb)))
    r = inv_.r
    lw = spec.tooth['lightening']
    windows = []
    if gid == 'b1':
        bs = spec.structure['b1_structure']
        hub = bs['hub_radius'] * scale
        rim = bs['rim_inner_radius'] * scale
        w = bs['spoke_width'] * scale
        angs = sorted(math.radians(s['angle_deg']) % TWO_PI for s in bs['spokes'])
        for i in range(len(angs)):
            a0, a1 = angs[i], angs[(i + 1) % len(angs)] + (TWO_PI if i == len(angs) - 1 else 0)
            win = window(hub, rim, a0, a1, w / 2, w / 2)
            if win is not None:
                windows.append(win)
    elif gid == 'e3':
        k_dir = math.radians(-38.0)
        wid = [9.0 * scale] + [max(1.5, 0.12 * g['pitch_radius']) * scale] * 4
        windows = gear_windows(4.0 * scale, 40.0 * scale, 5, wid, offset=k_dir)
    elif (g['pitch_radius'] > 12 and gid not in PIN_SLOT_GEARS
          and g['kind'] == 'spur'):
        r_hub = bore + 2.0 * scale
        r_rim = inv_.rf - max(1.5 * scale, 2 * m)
        if r_rim - r_hub >= 2.0 * scale:
            n = 6 if r_rim >= 15 * scale else (5 if r_rim >= 10 * scale else 4)
            aw = max(1.5, 0.12 * g['pitch_radius']) * scale
            windows = gear_windows(r_hub, r_rim, n, [aw] * n)
    holes += windows
    slot = None
    for ps in spec.pin_slots:
        if ps['slot_gear'] == gid:
            r0 = (ps['pin_radius'] - ps['offset'] - 0.6) * scale
            r1 = (ps['pin_radius'] + ps['offset'] + 0.6) * scale
            hw = 0.55 * scale if bore_clearance is None else 0.5 * scale + slot_clearance
            ext = hw - 0.55 * scale
            slot = cw(stadium(r0 - ext, r1 + ext, hw))
            holes.append(slot)
    info = {'r': r, 'ra': inv_.ra, 'rf': inv_.rf, 'rb': inv_.rb, 'bore': bore,
            'n_windows': len(windows), 'tip_land': inv_.tip_land(),
            'tip_land_nominal': Involute(z, m).tip_land(), 'fillet': inv_.fillet_radius()}
    return [ccw(outer)] + holes, info
