"""Blender 5.2 check of the envelope crowns: BVH overlap + engagement gap over one crown pitch."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parent.parent)   # repository root
import bpy, json, math, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import tessellate_polygon
AL = math.radians(30.0)
E = json.load(open(f'{ROOT}/tools/crown_envelopes.json'))

def involute_outline(z, m, j, phase=0.0, npf=32):
    r = m*z/2; rb = r*math.cos(AL); ra = r + m; rf = r - 1.25*m
    inv = lambda a: math.tan(a) - a
    def psi(rho): return math.pi/(2*z) + inv(AL) - inv(math.acos(min(1.0, rb/rho))) - j/(4*r)
    rs = np.linspace(max(rb, rf), ra, npf)
    pts = []
    for k in range(z):
        c = phase + 2*math.pi*k/z
        for rho in rs: pts.append((rho*math.cos(c - psi(rho)), rho*math.sin(c - psi(rho))))            # rising flank
        for t in np.linspace(c - psi(ra), c + psi(ra), 5)[1:-1]: pts.append((ra*math.cos(t), ra*math.sin(t)))
        for rho in rs[::-1]: pts.append((rho*math.cos(c + psi(rho)), rho*math.sin(c + psi(rho))))      # falling flank
        c2 = c + 2*math.pi/z
        for t in np.linspace(c + psi(rf), c2 - psi(rf), 6)[1:-1]: pts.append((rf*math.cos(t), rf*math.sin(t)))
    return np.array(pts)

def prism(outer, holes, z0, z1):
    loops = [outer] + holes
    V = []; F = []
    tris = tessellate_polygon([[Vector((p[0], p[1], 0)) for p in lp] for lp in loops])
    offs = []; n = 0
    for lp in loops: offs.append(n); n += len(lp)
    allp = np.vstack(loops)
    Vb = np.c_[allp, np.full(len(allp), z0)]; Vt = np.c_[allp, np.full(len(allp), z1)]
    V = np.vstack([Vb, Vt])
    for t in tris: F.append((t[2], t[1], t[0])); F.append((t[0]+n, t[1]+n, t[2]+n))
    for li, lp in enumerate(loops):
        o = offs[li]; L_ = len(lp)
        for q in range(L_):
            a, b = o+q, o+(q+1) % L_
            F.append((a, b, b+n)); F.append((a, b+n, a+n))
    return V, np.array(F)

def circle(r, n=96): return np.array([(r*math.cos(2*math.pi*i/n), r*math.sin(2*math.pi*i/n)) for i in range(n)])

def crown_teeth(env, zc):
    """Tooth shells in crown-local cylindrical data -> list of (s, rho, phi) vertex arrays + faces (box topology)."""
    S = np.array(env['s_grid']); R = np.array(env['rho_levels']); L = np.array(env['phi_lo_rad']); H = np.array(env['phi_hi_rad'])
    ns, nr = S.shape
    def idx(side, i, j): return side*ns*nr + i*nr + j
    F = []
    for i in range(ns-1):
        for j in range(nr-1):
            F.append((idx(0, i, j), idx(0, i+1, j), idx(0, i+1, j+1), idx(0, i, j+1)))
            F.append((idx(1, i, j), idx(1, i, j+1), idx(1, i+1, j+1), idx(1, i+1, j)))
    for i in range(ns-1):
        F.append((idx(0, i, 0), idx(1, i, 0), idx(1, i+1, 0), idx(0, i+1, 0)))
        F.append((idx(0, i, nr-1), idx(0, i+1, nr-1), idx(1, i+1, nr-1), idx(1, i, nr-1)))
    for j in range(nr-1):
        F.append((idx(0, 0, j), idx(0, 0, j+1), idx(1, 0, j+1), idx(1, 0, j)))
        F.append((idx(0, ns-1, j), idx(1, ns-1, j), idx(1, ns-1, j+1), idx(0, ns-1, j+1)))
    tri = []
    for f in F: tri += [(f[0], f[1], f[2]), (f[0], f[2], f[3])]
    teeth = []
    for k in range(zc):
        dk = 2*math.pi*k/zc
        s = np.r_[S.ravel(), S.ravel()]; rho = np.r_[np.tile(R, ns), np.tile(R, ns)]; phi = np.r_[L.ravel(), H.ravel()] + dk
        teeth.append((s, rho, phi))
    return teeth, np.array(tri)

def run(name, env, zc, spur, z_axis, alpha_samples, ratio):
    zs, m, j, spz = spur
    outline = involute_outline(zs, m, j)
    Vs, Fs = prism(outline, [circle(2.0)[::-1]], spz[0], spz[1])
    teeth, Ft = crown_teeth(env, zc)
    # keep only teeth that can come near the spur (|phi| < 60 deg over the sampled range)
    worst_overlap = 0; gaps = []
    for a in alpha_samples:
        th = a*ratio
        c, s_ = math.cos(th), math.sin(th)
        Vw = np.c_[Vs[:, 0]*c - Vs[:, 1]*s_, Vs[:, 0]*s_ + Vs[:, 1]*c, Vs[:, 2]]
        spur_tree = BVHTree.FromPolygons(Vw.tolist(), Fs.tolist(), all_triangles=True)
        allV = []; allF = []; off = 0
        for (sx, rho, phi) in teeth:
            om = phi + a
            if np.min(np.abs((om + math.pi) % (2*math.pi) - math.pi)) > math.radians(70): continue
            V = np.c_[sx, rho*np.sin(om), z_axis - rho*np.cos(om)]
            allV.append(V); allF.append(Ft + off); off += len(V)
        V = np.vstack(allV); F = np.vstack(allF)
        ctree = BVHTree.FromPolygons(V.tolist(), F.tolist(), all_triangles=True)
        ov = ctree.overlap(spur_tree)
        worst_overlap = max(worst_overlap, len(ov))
        d = min(spur_tree.find_nearest(Vector(p))[3] for p in V[::1])
        gaps.append(d)
    print(f"{name}: samples {len(alpha_samples)}, max overlapping triangle pairs {worst_overlap}, "
          f"min gap per sample: min {min(gaps):.4f} max {max(gaps):.4f} mm")
    return worst_overlap, gaps

m1 = 0.5776
pitch_a1 = 2*math.pi/48
ov1, g1 = run('a1/b1', E['a1'], 48, (223, m1, 0.03, (3.95, 6.65)), 5.30 + m1*48/2,
              np.linspace(0, pitch_a1, 61)[:-1], 48/223)
pitch_q1 = 2*math.pi/20
ov2, g2 = run('q1/b0', E['q1'], 20, (20, 0.5, 0.03, (47.20, 48.20)), 52.70,
              np.linspace(0, pitch_q1, 61)[:-1] - 0.0774, 1.0)
ok = ov1 == 0 and ov2 == 0 and max(g1) < 0.15 and max(g2) < 0.15
print("CROWNS OK" if ok else "CROWNS FAIL")
sys.exit(0 if ok else 1)
