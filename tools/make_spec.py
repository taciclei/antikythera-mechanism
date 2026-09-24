"""Build spec/antikythera.json: the single source of truth for the Antikythera reconstruction.

All hard data (teeth, modules, axis positions, z ranges, joints, exact target rates) is defined or
solved here. Run with Blender's bundled python3.13. Exits non-zero if an internal check fails.
"""
import json, math, sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILS = []
def check(cond, msg):
    if not cond: FAILS.append(msg)

def u(deg): return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
def polar(r, deg): c, s = u(deg); return (r*c, r*s)
def add(p, q): return (p[0]+q[0], p[1]+q[1])
def sub(p, q): return (p[0]-q[0], p[1]-q[1])
def dist(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
def rnd(p, n=10): return [round(p[0], n), round(p[1], n)]
def circ_int(c1, r1, c2, r2, pick):
    """Intersection of two circles; pick(point_list) chooses one."""
    d = dist(c1, c2); a = (r1*r1 - r2*r2 + d*d)/(2*d); h = math.sqrt(max(r1*r1 - a*a, 0.0))
    ex = ((c2[0]-c1[0])/d, (c2[1]-c1[1])/d); m = (c1[0]+a*ex[0], c1[1]+a*ex[1])
    sols = [(m[0]-h*ex[1], m[1]+h*ex[0]), (m[0]+h*ex[1], m[1]-h*ex[0])]
    return pick(sols)
def closest_to(t): return lambda s: min(s, key=lambda p: dist(p, t))

# ----------------------------------------------------------------------------------------------
# 1. Modules (one per connected mesh component) and exact centre distances
# ----------------------------------------------------------------------------------------------
M = {}
def setm(names, m):
    for n in names: M[n] = m
setm(['a1', 'b1'], 0.5776)
setm(['b2', 'c1', 'l1'], 0.480)
setm(['c2', 'd1'], 0.4472)
setm(['d2', 'e2'], 0.4855)
setm(['e1', 'b3'], 0.5594)
setm(['l2', 'm1'], 0.4966)
setm(['m3', 'e3'], 0.466)
setm(['e4', 'f1'], 0.5203)
setm(['e5', 'k1'], 0.512)
setm(['k2', 'e6'], 0.534)
setm(['f2', 'g1'], 0.5167)
setm(['g2', 'h1'], 0.4475)
setm(['h2', 'i1'], 0.4347)
setm(['m2', 'n1'], 0.514)
setm(['n3', 'o1'], 0.4171)
setm(['n2', 'p1', 'p2', 'cal1'], 0.5)
setm(['b0', 'q1'], 0.5)
setm(['fx49', 'nd62'], 54/111)          # makes the Spoke B bearing exactly 27.000
setm(['nd64', 'nd48'], 27/56)           # idem, so nd48 is exactly coaxial
setm(['fx51', 'vn44', 'me72'], 51.2/95) # Spoke C hole exactly 25.600
setm(['vn34', 'vn26', 'r1'], 0.521)
setm(['me89', 'me40', 'me20'], 0.5)
setm(['fx56', 'cp52', 'cp64', 'su56', 'sa61', 'sa40', 'sa68', 'sa86s', 'sa86o',
      'ju45', 'ju40', 'ju43', 'ju65s', 'ju65o', 'ma38', 'ma40', 'ma71', 'ma80s', 'ma80o'], 0.48)

Z = dict(a1=48, b1=223, b2=64, b3=32, c1=38, c2=48, d1=24, d2=127, e1=32, e2=32, e3=223, e4=188, e5=50, e6=50,
         k1=50, k2=50, f1=53, f2=30, g1=54, g2=20, h1=60, h2=15, i1=60, l1=38, l2=53, m1=96, m2=15, m3=27,
         n1=53, n2=15, n3=57, o1=60, p1=60, p2=12, cal1=60, q1=20, r1=63, b0=20, fx51=51, fx49=49, nd62=62,
         nd64=64, nd48=48, vn44=44, vn34=34, vn26=26, me72=72, me89=89, me40=40, me20=20, fx56=56, cp52=52,
         cp64=64, su56=56, sa61=61, sa40=40, sa68=68, sa86s=86, sa86o=86, ju45=45, ju40=40, ju43=43, ju65s=65,
         ju65o=65, ma38=38, ma40=40, ma71=71, ma80s=80, ma80o=80)
check(len(Z) == 69, f"gear count {len(Z)} != 69")
check(set(Z) == set(M), f"module table mismatch {set(Z) ^ set(M)}")
def rp(g): return M[g]*Z[g]/2
def a(g1, g2):
    check(abs(M[g1]-M[g2]) < 1e-12, f"mesh {g1}~{g2} has different modules")
    return M[g1]*(Z[g1]+Z[g2])/2

# ----------------------------------------------------------------------------------------------
# 2. Axis layout (front view: x right, y up, mm). Solved so every mesh distance is exact.
# ----------------------------------------------------------------------------------------------
P = {}
P['B'] = (0.0, 0.0)
P['M'] = (0.0, 45.5)                                                      # P74, on the vertical midline
P['E'] = circ_int(P['B'], a('e1','b3'), P['M'], a('m3','e3'), closest_to((14.1, -11.0)))
P['L'] = circ_int(P['B'], a('b2','l1'), P['M'], a('l2','m1'), closest_to((19.9, 14.3)))
P['C'] = polar(a('b2','c1'), 180 + 71.2)                                  # B-C-D line 18.8 deg left of down
P['D'] = circ_int(P['C'], a('c2','d1'), P['E'], a('d2','e2'), closest_to((-13.1, -38.4)))
P['N'] = add(P['M'], (0.0, a('m2','n1')))                                 # Metonic centre on the midline
P['G'] = (0.0, P['N'][1] - 145.5)                                         # Allen 2016 n-g = 145.5
P['F'] = circ_int(P['E'], a('e4','f1'), P['G'], a('f2','g1'), closest_to((19.7, -73.5)))
P['O'] = add(P['N'], (-a('n3','o1'), 0.0))                                # Olympiad: right of n seen from back
P['cal'] = add(P['N'], (a('n3','o1'), 0.0))                               # Callippic: mirror position
P['P'] = circ_int(P['N'], a('n2','p1'), P['cal'], a('p2','cal1'), lambda s: max(s, key=lambda p: p[1]))
P['H'] = add(P['G'], polar(a('g2','h1'), 310.0))                          # keep H angle about G in 140-340
P['I'] = circ_int(P['G'], 25.0, P['H'], a('h2','i1'), closest_to((0.0, -107.5)))
# e3-carried pin-and-slot pair (e3 local frame, relative to E, at crank = 0)
K_DIR = -38.0
P['K_local'] = polar(a('e5','k1'), K_DIR)
P['Kp_local'] = polar(a('k2','e6'), K_DIR)                                # radial offset of 1.1 mm
check(abs(dist(P['K_local'], P['Kp_local']) - 1.1) < 1e-9, "k1/k2 offset must be 1.1")
# b1-carried (b1 local frame = front view at crank 0)
P['spA'] = polar(a('fx51','me72'), 60.0)
P['spB'] = polar(a('fx49','nd62'), -30.0)
P['spC'] = polar(a('fx51','vn44'), 240.0)
check(abs(a('nd64','nd48') - a('fx49','nd62')) < 1e-9, "Spoke B distances must agree")
P['me20'] = polar(36.0, -26.0)                                            # i = 36.0 (Table S9)
P['me40'] = circ_int(P['spA'], a('me89','me40'), P['me20'], a('me40','me20'), closest_to(polar(28.0, -2.7)))
P['r1'] = polar(27.8, 155.0)                                              # i = 27.8 (Table S9)
P['vn26'] = circ_int(P['spC'], a('vn34','vn26'), P['r1'], a('vn26','r1'), closest_to(polar(13.0, -149.1)))
P['Dblock'] = polar(31.8, 150.0)
# CP-carried (same frame as b1)
P['cp52'] = polar(a('fx56','cp52'), 110.0)
P['su56'] = polar(2*a('cp52','su56')*math.cos(math.radians(40.0)), 150.0)
check(abs(dist(P['cp52'], P['su56']) - a('cp52','su56')) < 1e-9, "su56 placement")
P['cp64'] = polar(a('fx56','cp64'), -85.0)
P['sa86s'] = polar(a('sa86s','sa86o'), 60.0)
P['sa68'] = add(P['sa86s'], polar(1.50, 0.0))
P['sa40'] = circ_int(P['cp52'], a('sa61','sa40'), P['sa68'], a('sa40','sa68'), closest_to((-1.1, 47.3)))
P['ju65s'] = polar(a('ju65s','ju65o'), -30.0)
P['ju43'] = add(P['ju65s'], polar(1.58, 0.0))
P['ju40'] = circ_int(P['cp64'], a('ju45','ju40'), P['ju43'], a('ju40','ju43'), closest_to((22.1, -34.4)))
P['ma80s'] = polar(a('ma80s','ma80o'), 240.0)
P['ma71'] = add(P['ma80s'], polar(6.58, 150.0))
P['ma40'] = circ_int(P['cp64'], a('ma38','ma40'), P['ma71'], a('ma40','ma71'), closest_to((-3.9, -46.3)))

# ----------------------------------------------------------------------------------------------
# 3. Z stack (z = 0 is the front face of the Main Plate; +z toward the front viewer)
# ----------------------------------------------------------------------------------------------
ZR = {}
def zr(g, z0, z1): ZR[g] = (round(z0, 3), round(z1, 3))
# front side of the Main Plate, under b1
zr('c2', 0.15, 1.45); zr('d1', 0.15, 2.55); zr('l2', 0.15, 1.65); zr('m1', 0.15, 2.15)
zr('c1', 1.60, 3.10); zr('l1', 1.80, 3.30); zr('b2', 1.80, 3.80)
zr('b1', 3.95, 6.65)
zr('a1', 4.60, 33.73)  # crown (world z extent of the tooth ring); geometry in crowns.a1
# behind the Main Plate (Main Plate is z -2.0 .. 0.0)
zr('b3', -3.45, -2.15); zr('e1', -3.45, -2.15)
zr('d2', -4.90, -3.60); zr('e2', -4.60, -3.60)
zr('e3', -6.45, -5.05); zr('m3', -6.45, -5.05)
zr('e4', -8.10, -6.60); zr('f1', -7.90, -6.60); zr('e5', -7.10, -6.60); zr('k1', -7.20, -6.60)
zr('k2', -7.85, -7.35); zr('e6', -7.95, -7.35)
zr('m2', -8.40, -6.60); zr('n1', -8.10, -6.60)
zr('f2', -9.45, -8.25); zr('g1', -9.75, -8.25)
zr('g2', -11.50, -9.90); zr('h1', -10.90, -9.90)
zr('h2', -13.05, -11.65); zr('i1', -12.85, -11.65)
zr('n3', -9.45, -8.25); zr('o1', -9.35, -8.25)
zr('n2', -11.40, -9.90); zr('p1', -11.20, -9.90)
zr('p2', -13.05, -11.55); zr('cal1', -12.85, -11.55)
# b1-to-Strap zone (b1 hub top 7.85, Strap 22.85..24.45)
zr('fx51', 8.00, 9.00); zr('me72', 8.00, 9.00); zr('vn44', 8.00, 9.00)            # L1
zr('fx49', 9.15, 10.15); zr('nd62', 9.15, 10.15)                                # L2
#                                                                                   L3 mean-Sun bar 10.30..11.30
zr('nd64', 11.45, 12.45); zr('nd48', 11.45, 12.45)                              # L4
#                                                          L5 Mercury follower 12.60..13.60, L6 Venus follower 13.75..14.75
#                                                          L7 me20 disk + r1 disk 14.90..15.90
zr('me89', 16.05, 17.05); zr('me40', 16.05, 17.05); zr('me20', 16.05, 17.05)    # L8
zr('vn34', 16.05, 17.05); zr('vn26', 16.05, 17.05); zr('r1', 16.05, 17.65)
#                                                                                   L9 D-plate 17.80..18.80
# Strap-to-CP zone (Strap top 24.45, CP 34.15..36.15)
#                                                                                   T1 true-Sun follower 24.60..25.40
zr('ma80s', 25.55, 26.55); zr('ma80o', 25.55, 26.55)                            # T2
zr('ma38', 26.70, 27.70); zr('ma40', 26.70, 27.70); zr('ma71', 26.70, 27.70)    # T3
zr('ju65s', 26.70, 27.70); zr('ju65o', 26.70, 27.70)
zr('ju45', 27.85, 28.85); zr('ju40', 27.85, 28.85); zr('ju43', 27.85, 28.85)    # T4
zr('sa86s', 29.00, 30.00); zr('sa86o', 29.00, 30.00)                            # T5
zr('sa61', 30.15, 31.15); zr('sa40', 30.15, 31.15); zr('sa68', 30.15, 31.15)    # T6
zr('fx56', 36.30, 37.30); zr('cp52', 36.30, 37.30); zr('cp64', 36.30, 37.30); zr('su56', 36.30, 37.30)  # C0
zr('b0', 47.20, 48.20)
zr('q1', 47.20, 58.20)  # crown (Moon-frame z extent of the tooth ring); geometry in crowns.q1
check(set(ZR) == set(Z), f"z table mismatch {set(Z) ^ set(ZR)}")

# ----------------------------------------------------------------------------------------------
# 4. Bodies, gears and exact kinematics
# ----------------------------------------------------------------------------------------------
STATUS = dict.fromkeys(['a1','b1','b2','b3','c1','c2','d1','d2','e1','e2','e3','e4','e5','e6','k1','k2','f1','f2',
    'g1','g2','h1','h2','i1','l1','l2','m1','m2','o1','q1','r1'], 'SURVIVING')
STATUS.update(dict.fromkeys(['m3','n1','n2','n3','p1','p2','cal1'], 'RECONSTRUCTED'))
for g in Z: STATUS.setdefault(g, 'HYPOTHETICAL')
check(sum(v == 'SURVIVING' for v in STATUS.values()) == 30, "30 surviving")
check(sum(v == 'RECONSTRUCTED' for v in STATUS.values()) == 7, "7 reconstructed")

ROLE = dict(
 a1="Contrate input pinion on the crank shaft; drives b1 (crank turns 223/48 per year)",
 b1="Main drive wheel, 1 turn = 1 tropical year; carries every front epicyclic train, the Strap and the CP",
 b2="Year input for the rear trains (Moon via c1, calendars and eclipses via l1)", b3="Takes the Moon (with anomaly) from e1 to the central Moon arbor",
 c1="Moon train", c2="Moon train", d1="Moon train (arbor passes through the Main Plate)", d2="Moon train, prime 127 = 254/2",
 e1="Moon output with anomaly, drives b3", e2="Mean sidereal Moon", e3="Turntable: lunar apsidal line, 8.88 yr; carries k1 and k2",
 e4="Annulus with external teeth, drives the Saros/Exeligmos trains", e5="Drives k1", e6="Receives the variable Moon motion from k2",
 k1="Pin gear on the e3 turntable", k2="Slot gear on the e3 turntable (Hipparchan lunar anomaly)", f1="Saros train", f2="Saros train",
 g1="Saros pointer: 4 turns = 223 synodic months", g2="Exeligmos train", h1="Exeligmos train", h2="Exeligmos train",
 i1="Exeligmos pointer: 1 turn = 3 Saros", l1="Metonic/apsides trains (prime 19)", l2="Metonic/apsides trains",
 m1="Split point of the Metonic and Saros trains", m2="Drives n1 (Metonic)", m3="Drives the e3 turntable (count forced by the ratio)",
 n1="Metonic pointer: 5 turns = 19 years", n2="Drives the Callippic train", n3="Drives the Olympiad (Games) dial",
 o1="Games/Olympiad pointer, 4 years (the only anticlockwise back pointer)", p1="Callippic train", p2="Callippic train",
 cal1="Callippic pointer, 76 years", q1="Moon-phase contrate on a radial arbor in the Moon-pointer cap", r1="Venus epicycle (surviving 63-tooth gear)",
 b0="Mean Sun input to the Moon-phase differential", fx51="Fixed gear shared by Mercury and Venus", fx49="Fixed gear of the Nodes train",
 nd62="Nodes train", nd64="Nodes train", nd48="Dragon Hand (lunar nodes, 18.6 yr, retrograde)", vn44="Venus train", vn34="Venus train",
 vn26="Venus idler", me72="Mercury train", me89="Mercury train (prime 89)", me40="Mercury idler", me20="Mercury epicycle",
 fx56="Fixed gear for the true Sun and the superior planets", cp52="True-Sun idler and Saturn g2", cp64="Mars/Jupiter g2",
 su56="True-Sun epicycle (pure translation)", sa61="Saturn g3", sa40="Saturn idler", sa68="Saturn pin gear", sa86s="Saturn slot gear",
 sa86o="Saturn output (29.47 yr)", ju45="Jupiter g3", ju40="Jupiter idler", ju43="Jupiter pin gear", ju65s="Jupiter slot gear",
 ju65o="Jupiter output (11.86 yr)", ma38="Mars g3", ma40="Mars idler", ma71="Mars pin gear", ma80s="Mars slot gear", ma80o="Mars output (1.88 yr)")

ALT = dict(
 b1=[{"value": 224, "source": "F06SI limits 223/224"}, {"value": 225, "source": "Price 1974; V22"}, {"value": "228/229", "source": "V24 (3% shrinkage)"}],
 a1=[{"value": "44-52", "source": "Wright limits"}], c2=[{"value": "47-49", "source": "F06SI"}], e3=[{"value": "217-235", "source": "F06SI CT limits"}],
 e4=[{"value": "180-192", "source": "F06SI"}], e5=[{"value": "50-52", "source": "F06SI; Wright 51"}], e6=[{"value": "49-50", "source": "F06SI; Wright 53"}],
 k1=[{"value": "48-51", "source": "F06SI"}], k2=[{"value": "48-52", "source": "F06SI"}], f1=[{"value": 54, "source": "alternative count"}],
 g1=[{"value": "54-56", "source": "F06SI"}], h1=[{"value": "60-64", "source": "F06SI"}], m1=[{"value": "96-99", "source": "F06SI"}],
 o1=[{"value": "57-61", "source": "F06SI/F08SI"}], r1=[{"value": 64, "source": "rejected by FJ12 and F21SI"}])

# body -> (parent, axis position in parent frame, gears, rate relative to parent [Fraction], kind)
BODIES = {}
def body(bid, parent, pos, gears, rate_rel, kind='revolute', axis='z', **kw):
    BODIES[bid] = dict(id=bid, parent=parent, axis=axis, pos=pos, gears=gears, rate_rel=rate_rel, kind=kind, **kw)
body('frame', None, (0, 0), ['fx51', 'fx49', 'fx56'], F(0), 'fixed',
     note="Main Plate, back plate, front plate, Sub-Plate, fixed central tube (fx51, fx49) and Sub-Plate gear fx56")
body('a', 'frame', (0.0, 0.0), ['a1'], None, 'crank', axis='x',
     note="Axis along +x at y = 0, z = 19.1624. Angle about +x = -2*pi*(223/48)*years (see conventions).")
body('b', 'frame', P['B'], ['b1', 'b2', 'b0'], F(1), note="b1, b2, spokes, pillars, Strap, D-plate, CP, mean-Sun bar and tube (with b0), Date tube")
body('moon', 'frame', P['B'], ['b3'], None)
body('c', 'frame', P['C'], ['c2', 'c1'], None); body('d', 'frame', P['D'], ['d1', 'd2'], None)
body('e_pipe', 'frame', P['E'], ['e2', 'e5'], None); body('e_table', 'frame', P['E'], ['e3', 'e4'], None)
body('e_inner', 'frame', P['E'], ['e1', 'e6'], None, 'pin_slot_driven')
body('k', 'e_table', P['K_local'], ['k1'], None); body('kp', 'e_table', P['Kp_local'], ['k2'], None, 'pin_slot_output')
body('l', 'frame', P['L'], ['l2', 'l1'], None); body('m', 'frame', P['M'], ['m1', 'm3', 'm2'], None)
body('f', 'frame', P['F'], ['f1', 'f2'], None); body('g', 'frame', P['G'], ['g1', 'g2'], None)
body('h', 'frame', P['H'], ['h1', 'h2'], None); body('i', 'frame', P['I'], ['i1'], None)
body('n', 'frame', P['N'], ['n1', 'n3', 'n2'], None); body('o', 'frame', P['O'], ['o1'], None)
body('p', 'frame', P['P'], ['p1', 'p2'], None); body('cal', 'frame', P['cal'], ['cal1'], None)
body('q', 'moon', (0.0, 0.0), ['q1'], None, 'nonlinear_crown', axis='radial',
     note="Radial arbor along the Moon pointer direction (+u = Moon local +x) at z = 52.70. Angle about +u relative to moon = theta_b - theta_moon (NONLINEAR; mean +235/19).")
body('spA', 'b', P['spA'], ['me72', 'me89'], None); body('spB', 'b', P['spB'], ['nd62', 'nd64'], None)
body('spC', 'b', P['spC'], ['vn44', 'vn34'], None)
body('x_me40', 'b', P['me40'], ['me40'], None); body('x_me20', 'b', P['me20'], ['me20'], None)
body('x_vn26', 'b', P['vn26'], ['vn26'], None); body('x_r1', 'b', P['r1'], ['r1'], None)
body('t_nodes', 'frame', P['B'], ['nd48'], None)
body('x_cp52', 'b', P['cp52'], ['cp52', 'sa61'], None); body('x_cp64', 'b', P['cp64'], ['cp64', 'ma38', 'ju45'], None)
body('x_su56', 'b', P['su56'], ['su56'], None)
body('x_sa40', 'b', P['sa40'], ['sa40'], None); body('x_sa68', 'b', P['sa68'], ['sa68'], None)
body('x_sa86s', 'b', P['sa86s'], ['sa86s'], None, 'pin_slot_output')
body('x_ju40', 'b', P['ju40'], ['ju40'], None); body('x_ju43', 'b', P['ju43'], ['ju43'], None)
body('x_ju65s', 'b', P['ju65s'], ['ju65s'], None, 'pin_slot_output')
body('x_ma40', 'b', P['ma40'], ['ma40'], None); body('x_ma71', 'b', P['ma71'], ['ma71'], None)
body('x_ma80s', 'b', P['ma80s'], ['ma80s'], None, 'pin_slot_output')
body('t_saturn', 'frame', P['B'], ['sa86o'], None, 'pin_slot_driven'); body('t_jupiter', 'frame', P['B'], ['ju65o'], None, 'pin_slot_driven')
body('t_mars', 'frame', P['B'], ['ma80o'], None, 'pin_slot_driven')
body('t_mercury', 'frame', P['B'], [], None, 'follower'); body('t_venus', 'frame', P['B'], [], None, 'follower')
body('t_trueSun', 'frame', P['B'], [], None, 'follower')
GEAR_BODY = {g: b for b, v in BODIES.items() for g in v['gears']}
check(set(GEAR_BODY) == set(Z), f"every gear on exactly one body: {set(Z) ^ set(GEAR_BODY)}")

# Meshes: (driver gear, driven gear, carrier body whose frame holds both axes fixed, type)
MESHES = [
 ('a1', 'b1', 'frame', 'crown'), ('b2', 'c1', 'frame', 'external'), ('c2', 'd1', 'frame', 'external'),
 ('d2', 'e2', 'frame', 'external'), ('b2', 'l1', 'frame', 'external'), ('l2', 'm1', 'frame', 'external'),
 ('m3', 'e3', 'frame', 'external'), ('e5', 'k1', 'e_table', 'external'), ('k2', 'e6', 'e_table', 'external'),
 ('e1', 'b3', 'frame', 'external'), ('e4', 'f1', 'frame', 'external'), ('f2', 'g1', 'frame', 'external'),
 ('g2', 'h1', 'frame', 'external'), ('h2', 'i1', 'frame', 'external'), ('m2', 'n1', 'frame', 'external'),
 ('n3', 'o1', 'frame', 'external'), ('n2', 'p1', 'frame', 'external'), ('p2', 'cal1', 'frame', 'external'),
 ('b0', 'q1', 'moon', 'crown'),
 ('fx49', 'nd62', 'b', 'external'), ('nd64', 'nd48', 'b', 'external'),
 ('fx51', 'vn44', 'b', 'external'), ('vn34', 'vn26', 'b', 'external'), ('vn26', 'r1', 'b', 'external'),
 ('fx51', 'me72', 'b', 'external'), ('me89', 'me40', 'b', 'external'), ('me40', 'me20', 'b', 'external'),
 ('fx56', 'cp52', 'b', 'external'), ('cp52', 'su56', 'b', 'external'), ('fx56', 'cp64', 'b', 'external'),
 ('sa61', 'sa40', 'b', 'external'), ('sa40', 'sa68', 'b', 'external'), ('sa86s', 'sa86o', 'b', 'external'),
 ('ju45', 'ju40', 'b', 'external'), ('ju40', 'ju43', 'b', 'external'), ('ju65s', 'ju65o', 'b', 'external'),
 ('ma38', 'ma40', 'b', 'external'), ('ma40', 'ma71', 'b', 'external'), ('ma80s', 'ma80o', 'b', 'external'),
]
# Pin-and-slot joints: mean rates are equal (winding number 1 because offset < pin radius)
PINSLOTS = [
 dict(id='lunar', pin_gear='k1', slot_gear='k2', carrier='e_table', pin_radius=9.6, offset=1.1,
      offset_dir_local_deg=K_DIR, note="Hipparchan lunar anomaly, amplitude asin(1.1/9.6) = 6.58 deg; slot spans 8.5..10.7 from K'"),
 dict(id='saturn', pin_gear='sa68', slot_gear='sa86s', carrier='b', pin_radius=14.37, offset=1.50, offset_dir_local_deg=180.0),
 dict(id='jupiter', pin_gear='ju43', slot_gear='ju65s', carrier='b', pin_radius=8.22, offset=1.58, offset_dir_local_deg=180.0),
 dict(id='mars', pin_gear='ma71', slot_gear='ma80s', carrier='b', pin_radius=10.00, offset=6.58, offset_dir_local_deg=330.0),
]
# offset_dir = direction from the pin-gear axis to the slot-gear axis, in the carrier frame (math angle, deg)
for ps in PINSLOTS:
    pb, sb = GEAR_BODY[ps['pin_gear']], GEAR_BODY[ps['slot_gear']]
    d = sub(BODIES[sb]['pos'], BODIES[pb]['pos'])
    check(abs(math.hypot(*d) - ps['offset']) < 1e-6, f"pin-slot {ps['id']} offset")
    ang = math.degrees(math.atan2(d[1], d[0])) % 360
    check(abs((ang - ps['offset_dir_local_deg'] + 180) % 360 - 180) < 1e-6, f"pin-slot {ps['id']} direction {ang}")
    check(ps['offset'] < ps['pin_radius'], f"pin-slot {ps['id']} winding number")
# Followers (slotted levers on the central axis driven by a pin on an epicycle carried by b)
FOLLOWERS = [
 dict(id='mercury', body='t_mercury', epicycle_body='x_me20', i=dist((0, 0), P['me20']), pin_d=14.04, pin_phase_deg=0.0, layer=(12.60, 13.60),
      pin_layer_span=(12.60, 15.90), note="pin on the me20 disk (L7) pointing back into the L5 slot; slot spans i-d..i+d = 21.96..50.04"),
 dict(id='venus', body='t_venus', epicycle_body='x_r1', i=27.8, pin_d=20.01, pin_phase_deg=0.0, layer=(13.75, 14.75),
      pin_layer_span=(13.75, 15.90), note="pin on the r1 disk (L7) pointing back into the L6 slot; slot spans 7.79..47.81"),
 dict(id='trueSun', body='t_trueSun', epicycle_body='x_su56', i=dist((0, 0), P['su56']), pin_d=dist((0, 0), P['su56'])/24, pin_phase_deg=84.5,
      layer=(24.60, 25.40), pin_layer_span=(24.60, 34.00),
      note="eccentric pin fixed to su56 (C0) reaching back through a CP hole to the T1 follower; d = i/24 (Hipparchus e = 1/24)"),
]

# ---- exact kinematic solve (Willis) ----
rate = {'frame': F(0), 'b': F(1)}          # absolute mean rates, rev/yr, clockwise from the front positive
def gear_rate(g): return rate[GEAR_BODY[g]]
def carrier_rate(c): return rate[c]
# resolve iteratively
pending = list(MESHES)
PS_SLOT = {ps['slot_gear']: ps for ps in PINSLOTS}
for _ in range(100):
    progress = False
    for ps in PINSLOTS:
        pb, sb, cb = GEAR_BODY[ps['pin_gear']], GEAR_BODY[ps['slot_gear']], ps['carrier']
        if pb in rate and cb in rate and sb not in rate:
            rate[sb] = rate[pb]; progress = True   # mean relative rates equal => mean absolute rates equal
    for mesh in list(pending):
        g1, g2, c, kind = mesh
        b1_, b2_ = GEAR_BODY[g1], GEAR_BODY[g2]
        if kind == 'crown':
            pending.remove(mesh); progress = True; continue
        if c in rate and b1_ in rate and b2_ not in rate:
            rate[b2_] = rate[c] - F(Z[g1], Z[g2])*(rate[b1_] - rate[c]); pending.remove(mesh); progress = True
        elif c in rate and b2_ in rate and b1_ not in rate:
            rate[b1_] = rate[c] - F(Z[g2], Z[g1])*(rate[b2_] - rate[c]); pending.remove(mesh); progress = True
    if not progress: break
for fo in FOLLOWERS: rate[fo['body']] = F(1)
rate['q'] = None
unsolved = [b for b in BODIES if b not in rate and b not in ('a', 'q')]
check(not unsolved, f"unsolved bodies {unsolved}")
# consistency: every mesh (redundant ones included) must satisfy Willis exactly
for g1, g2, c, kind in MESHES:
    if kind == 'crown': continue
    lhs = Z[g1]*(gear_rate(g1) - rate[c]); rhs = -Z[g2]*(gear_rate(g2) - rate[c])
    check(lhs == rhs, f"Willis violated on {g1}~{g2}")
for bid in BODIES:
    par = BODIES[bid]['parent']
    if bid in rate and rate[bid] is not None and par is not None and par in rate:
        BODIES[bid]['rate_rel'] = rate[bid] - rate[par] if par not in ('frame',) else rate[bid]
        BODIES[bid]['rate_abs_mean'] = rate[bid]

TARGETS = [
 ("crank", "a", "223/48", "crank turns per year (magnitude)", "definition"),
 ("mean Sun", "b", "1", "tropical year", "F21"),
 ("Moon (mean sidereal)", "moon", "254/19", "254 sidereal months in 19 years", "F06"),
 ("lunar apsidal line", "e_table", "-477/4237", "8.8826 yr", "F06"),
 ("lunar anomaly phase (k1 relative to e3)", "k@e_table", "56165/4237", "anomalistic month", "F06"),
 ("Moon phase (q1 relative to Moon pointer, magnitude)", "q@moon", "235/19", "synodic month", "F06/F21"),
 ("Metonic pointer", "n", "-5/19", "5 turns = 19 years = 235 synodic months", "F06"),
 ("Olympiad pointer", "o", "1/4", "4-year games cycle", "F08"),
 ("Callippic pointer", "cal", "-1/76", "76 years", "F08"),
 ("Saros pointer", "g", "-940/4237", "4 turns = 223 synodic months", "F06"),
 ("Exeligmos pointer", "i", "-235/12711", "1 turn = 3 Saros", "F06"),
 ("Dragon Hand (nodes)", "t_nodes", "-5/93", "18.6 years retrograde", "F21 (hypothetical)"),
 ("draconic month (Moon - nodes)", "moon-t_nodes", "23717/1767", "draconic month", "derived"),
 ("Mercury epicycle relative to b1", "x_me20@b", "1513/480", "1513 synodic periods in 480 years", "F21 (hypothetical)"),
 ("Venus epicycle relative to b1", "x_r1@b", "289/462", "289 synodic periods in 462 years", "F21 (hypothetical)"),
 ("true-Sun epicycle absolute", "x_su56", "0", "translation only; follower mean +1", "F21 (hypothetical)"),
 ("Mars pin gear relative to CP", "x_ma71@b", "133/284", "133 synodic periods in 284 years; output 151/284", "F21 (hypothetical)"),
 ("Jupiter pin gear relative to CP", "x_ju43@b", "315/344", "315 synodic periods in 344 years; output 29/344", "F21 (hypothetical)"),
 ("Saturn pin gear relative to CP", "x_sa68@b", "427/442", "427 synodic periods in 442 years; output 15/442", "F21 (hypothetical)"),
 ("Mars output", "t_mars", "151/284", "sidereal 1.8808 yr", "F21 (hypothetical)"),
 ("Jupiter output", "t_jupiter", "29/344", "sidereal 11.862 yr", "F21 (hypothetical)"),
 ("Saturn output", "t_saturn", "15/442", "sidereal 29.467 yr", "F21 (hypothetical)"),
]
def eval_target(expr):
    if expr == 'a': return F(223, 48)
    if expr == 'q@moon': return F(235, 19)
    if expr == 'moon-t_nodes': return rate['moon'] - rate['t_nodes']
    if '@' in expr:
        x, c = expr.split('@'); return rate[x] - rate[c]
    return rate[expr]
for name, expr, tgt, cyc, src in TARGETS:
    check(eval_target(expr) == F(tgt), f"target {name}: got {eval_target(expr)} expected {tgt}")
# Moon phase check: b0 is on body b (+1), q rides on moon; crown 20:20 gives |rel| = |1 - 254/19| = 235/19
check(abs(rate['b'] - rate['moon']) == F(235, 19), "moon phase")

# ----------------------------------------------------------------------------------------------
# 5. Geometric checks: exact centre distances, contact ratio, in-layer overlaps
# ----------------------------------------------------------------------------------------------
ALPHA = math.radians(30.0); HA = 1.0; HF = 1.25
def world_axis(g):
    b = BODIES[GEAR_BODY[g]]
    if b['parent'] == 'e_table': return add(P['E'], b['pos'])
    return b['pos']
def tip(g): return rp(g) + HA*M[g]
MESH_TABLE = []
for g1, g2, c, kind in MESHES:
    if kind == 'crown': continue
    if c == 'e_table':
        d = dist(BODIES[GEAR_BODY[g1]]['pos'] if GEAR_BODY[g1] not in ('e_pipe', 'e_inner') else (0, 0),
                 BODIES[GEAR_BODY[g2]]['pos'] if GEAR_BODY[g2] not in ('e_pipe', 'e_inner') else (0, 0))
    else:
        d = dist(world_axis(g1), world_axis(g2))
    exact = a(g1, g2)
    check(abs(d - exact) < 1e-6, f"centre distance {g1}~{g2}: {d:.6f} vs {exact:.6f}")
    zo = min(ZR[g1][1], ZR[g2][1]) - max(ZR[g1][0], ZR[g2][0])
    check(zo >= 0.5 - 1e-9, f"face overlap {g1}~{g2} = {zo:.3f} mm")
    r1_, r2_ = rp(g1), rp(g2); rb1, rb2 = r1_*math.cos(ALPHA), r2_*math.cos(ALPHA)
    ra1, ra2 = r1_+HA*M[g1], r2_+HA*M[g2]
    eps = (math.sqrt(ra1**2-rb1**2) + math.sqrt(ra2**2-rb2**2) - exact*math.sin(ALPHA))/(math.pi*M[g1]*math.cos(ALPHA))
    check(eps >= 1.2, f"contact ratio {g1}~{g2} = {eps:.3f}")
    MESH_TABLE.append(dict(driver=g1, driven=g2, carrier=c, type=kind, module=round(M[g1], 12), centre_distance=round(exact, 10),
                           contact_ratio=round(eps, 3), face_overlap=round(zo, 3)))
# undercut: z_min for 30 deg = 2*HA/sin^2(alpha) = 8
check(min(Z.values()) >= 8, "undercut")
# in-layer overlap: gears on the same rigid frame (frame, b, e_table) whose z ranges overlap and that do not mesh
MESHSET = {frozenset((g1, g2)) for g1, g2, c, k in MESHES}
FRAMEGROUP = {}
for g in Z:
    bb = GEAR_BODY[g]; par = BODIES[bb]['parent']
    grp = 'b' if (bb == 'b' or par == 'b') else ('e_table' if (par == 'e_table' or bb == 'e_table') else 'frame')
    FRAMEGROUP[g] = grp
OVERLAPS = []
names = sorted(Z)
for i1 in range(len(names)):
    for i2 in range(i1+1, len(names)):
        g1, g2 = names[i1], names[i2]
        if GEAR_BODY[g1] == GEAR_BODY[g2] or frozenset((g1, g2)) in MESHSET: continue
        if g1 in ('a1', 'q1') or g2 in ('a1', 'q1'): continue
        z0 = max(ZR[g1][0], ZR[g2][0]); z1 = min(ZR[g1][1], ZR[g2][1])
        if z1 <= z0 - 0.1: continue   # 0.1 mm minimum axial gap between distinct parts
        p1, p2 = world_axis(g1), world_axis(g2)
        same_rigid = FRAMEGROUP[g1] == FRAMEGROUP[g2] and FRAMEGROUP[g1] != 'e_table'
        if FRAMEGROUP[g1] == 'e_table' and FRAMEGROUP[g2] == 'e_table': same_rigid = True
        INNER = {'e4': 41.8}
        if same_rigid and (g1 in INNER or g2 in INNER):
            ga, gb = (g1, g2) if g1 in INNER else (g2, g1)
            pa, pb = (p1, p2) if ga == g1 else (p2, p1)
            dd = dist(pa, pb)
            gap = INNER[ga] - (dd + tip(gb)) if dd + tip(gb) < INNER[ga] else dd - tip(ga) - tip(gb)
        elif same_rigid:
            gap = dist(p1, p2) - tip(g1) - tip(g2)
        else:
            # different rotating frames: use swept annuli about the centre of the rotating frame
            def ann(g):
                if FRAMEGROUP[g] == 'b': c = (0.0, 0.0); r = dist(c, p1 if g == g1 else p2); return c, max(r - tip(g), 0), r + tip(g)
                if FRAMEGROUP[g] == 'e_table': c = P['E']; r = dist(c, p1 if g == g1 else p2); return c, max(r - tip(g), 0), r + tip(g)
                return (p1 if g == g1 else p2), 0.0, tip(g)
            c1, a1_, b1_ = ann(g1); c2, a2_, b2_ = ann(g2)
            if g1 in INNER and FRAMEGROUP[g1] == 'e_table': a1_ = INNER[g1]
            if g2 in INNER and FRAMEGROUP[g2] == 'e_table': a2_ = INNER[g2]
            if dist(c1, c2) < 1e-9:
                gap = max(a1_ - b2_, a2_ - b1_)
            else:
                gap = dist(c1, c2) - b1_ - b2_
        if gap < 0.2:
            OVERLAPS.append(f"{g1}/{g2} gap {gap:.2f} mm in z [{z0:.2f},{z1:.2f}]")
for o in OVERLAPS: check(False, "in-layer overlap: " + o)
# a1 keep-out: everything carried by b in z 6.65..33 must stay within r <= 63.3
for g in Z:
    if FRAMEGROUP[g] == 'b' and ZR[g][1] > 6.65 and ZR[g][0] < 33.0 and g not in ('b1',):
        r = dist((0, 0), world_axis(g)) + tip(g)
        check(r <= 63.3, f"a1 keep-out violated by {g}: reach {r:.2f}")

# ----------------------------------------------------------------------------------------------
# 6. Assemble JSON
# ----------------------------------------------------------------------------------------------
def fr(x): return None if x is None else (str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}")
from spec_static import STATIC as _ST
SHAFTS = _ST['shafts']['items']; TUBES = _ST['tubes']
def mount(g):
    if g in ('a1', 'q1'): return 0.0, 'crown (solid disc fused to its shaft)'
    if g == 'fx56': return 7.8, 'fused to the Sub-Plate through the spacer ring (frame); the Date tube passes inside'
    if g == 'e4': return 41.8, 'annulus fixed to e3 by e4_spacers (same body)'
    bd = GEAR_BODY[g]; z0, z1 = ZR[g]
    for t in TUBES:
        if t['body'] == bd and t['z'][0] - 1e-9 <= z0 and z1 <= t['z'][1] + 1e-9: return t['r_out'], f"fused to tube {t['id']}"
    for sh in SHAFTS:
        if 'r' in sh and sh['owner'] == bd and sh['axis_body'] == bd and sh['z'][0] - 1e-9 <= z0 and z1 <= sh['z'][1] + 1e-9:
            return sh['r'], f"fused to {sh['id']}"
    for sh in SHAFTS:
        if 'r' in sh and sh['owner'] != bd and sh['axis_body'] == bd and sh['z'][0] - 1e-9 <= z0 and z1 <= sh['z'][1] + 1e-9:
            return round(sh['r'] + 0.05, 4), f"rides_on {sh['id']} (owner {sh['owner']})"
    if bd == 'e_table': return 1.85, 'rides_on pipe_e (owner e_pipe)'
    check(False, f"no mount for {g}"); return None, None
gears_out = []
for g in Z:
    kind = 'crown' if g in ('a1', 'q1') else ('annulus_external' if g == 'e4' else 'spur')
    entry = dict(id=g, teeth=Z[g], module=round(M[g], 12), pitch_radius=round(rp(g), 10), tip_radius=round(tip(g), 10),
                 root_radius=round(rp(g) - HF*M[g], 10), body=GEAR_BODY[g], z=list(ZR[g]), kind=kind,
                 status=STATUS[g], role=ROLE[g], axis_xy_world_at_crank0=rnd(world_axis(g)) if g not in ('a1', 'q1') else None,
                 bore_radius=mount(g)[0], mount=mount(g)[1],
                 alternatives=ALT.get(g, []))
    if g == 'e4': entry['annulus_inner_radius'] = 41.8
    gears_out.append(entry)
bodies_out = []
for bid, bdef in BODIES.items():
    e = dict(id=bid, parent=bdef['parent'], axis=bdef['axis'], kind=bdef['kind'], gears=bdef['gears'],
             axis_xy_in_parent=rnd(bdef['pos']) if bdef['parent'] else None,
             rate_abs_mean=fr(rate.get(bid)) if bid in rate else None,
             rate_rel_parent_mean=fr(rate[bid] - rate[bdef['parent']]) if (bid in rate and rate[bid] is not None and bdef['parent'] in rate and rate[bdef['parent']] is not None) else None)
    if 'note' in bdef: e['note'] = bdef['note']
    bodies_out.append(e)

sys.path.insert(0, str(ROOT / 'tools'))
from spec_static import STATIC
spec = json.loads(json.dumps(STATIC))
spec['gears'] = gears_out
spec['bodies'] = bodies_out
spec['meshes'] = MESH_TABLE + [dict(driver='a1', driven='b1', carrier='frame', type='crown'), dict(driver='b0', driven='q1', carrier='moon', type='crown')]
spec['pin_slots'] = PINSLOTS
spec['followers'] = [dict(fo, i=round(fo['i'], 6), pin_d=round(fo['pin_d'], 6),
                          epicycle_axis_xy_in_b=rnd(BODIES[fo['epicycle_body']]['pos'])) for fo in FOLLOWERS]
spec['targets'] = [dict(name=n, expr=e, value=t, cycle=c, source=s) for n, e, t, c, s in TARGETS]
spec['axes_world_xy'] = {k: rnd(v) for k, v in P.items() if not k.endswith('_local')}
spec['axes_e3_local_xy'] = {'K': rnd(P['K_local']), 'Kp': rnd(P['Kp_local'])}
if FAILS:
    print("SPEC CHECK FAILURES:"); [print("  -", f) for f in FAILS]; sys.exit(1)
(ROOT / 'spec').mkdir(exist_ok=True)
(ROOT / 'spec' / 'antikythera.json').write_text(json.dumps(spec, indent=1, ensure_ascii=False))
print(f"OK: {len(gears_out)} gears, {len(bodies_out)} bodies, {len(MESH_TABLE)} spur meshes, {len(TARGETS)} targets; all checks passed")
print("axes:", {k: rnd(v, 3) for k, v in P.items()})
print('max |centre distance error| ok (<1e-6)')
