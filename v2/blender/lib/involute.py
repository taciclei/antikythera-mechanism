# copié de build/am/involute.py (v1) — docstrings traduites en français, code inchangé
"""Profils de roues droites à développante (30°, sans déport), jeu par amincissement, rapport de conduite,
phase des dents."""
import math

import numpy as np

TWO_PI = 2.0 * math.pi


def inv(x):
    return np.tan(x) - x


class Involute:
    """Géométrie des dents d'une roue droite. j = jeu circonférentiel (amincissement de j/2 par dent)."""

    def __init__(self, z, m, alpha_deg=30.0, ha=1.0, hf=1.25, fillet=0.2, j=0.0):
        self.z, self.m, self.j = int(z), float(m), float(j)
        self.alpha = math.radians(alpha_deg)
        self.r = m * z / 2.0
        self.rb = self.r * math.cos(self.alpha)
        self.ra = self.r + ha * m
        self.rf = self.r - hf * m
        self.rho_fillet = fillet * m
        self.rs = max(self.rb, self.rf)   # plus petit rayon de la développante
        self.pitch = TWO_PI / self.z

    def psi(self, rho):
        """Demi-angle du flanc au rayon rho (rho < rb : prolongement radial, psi(rb))."""
        rho = np.maximum(np.asarray(rho, dtype=float), self.rb)
        return (math.pi / (2 * self.z) + inv(self.alpha) - inv(np.arccos(self.rb / rho))
                - self.j / (4 * self.r))

    def tip_land(self):
        """Largeur de tête (longueur d'arc au rayon ra)."""
        return float(2 * self.psi(self.ra) * self.ra)

    def _flank_point(self, rho):
        a = -self.psi(rho)
        return np.stack([rho * np.cos(a), rho * np.sin(a)], axis=-1)

    def _fillet(self, rho_f):
        """Congé du flanc « moins » de la dent centrée en 0. Renvoie (points de l'arc, du point de tangence
        au pied jusqu'au point de tangence au flanc ; rayon de début du flanc ; angle de tangence au pied)."""
        ps = float(self.psi(self.rs))
        P0 = np.array([self.rf * math.cos(-ps), self.rf * math.sin(-ps)])
        if self.rf < self.rb:
            t = P0 / np.linalg.norm(P0)
        else:
            e = 1e-6
            t = self._flank_point(self.rf + e) - self._flank_point(self.rf)
            t = t / np.linalg.norm(t)
        n = np.array([t[1], -t[0]])            # vers le creux (côté horaire)
        Q = P0 + rho_f * n
        R = self.rf + rho_f
        qt = Q @ t
        a = -qt + math.sqrt(max(qt * qt - Q @ Q + R * R, 0.0))
        O = Q + a * t
        Tf = P0 + a * t
        Tr = O * self.rf / np.linalg.norm(O)
        a0 = math.atan2(*(Tr - O)[::-1])
        a1 = math.atan2(*(Tf - O)[::-1])
        d = (a1 - a0 + math.pi) % TWO_PI - math.pi
        k = 5
        arc = np.array([O + rho_f * np.array([math.cos(a0 + d * i / k), math.sin(a0 + d * i / k)])
                        for i in range(k + 1)])
        return arc, float(np.linalg.norm(Tf)), math.atan2(Tr[1], Tr[0])

    def fillet_radius(self):
        """Plus grand congé <= 0,2 m qui laisse un arc de pied entre les deux congés d'un creux."""
        rf_ = self.rho_fillet
        for _ in range(60):
            _, _, ang = self._fillet(rf_)
            if ang > -self.pitch / 2 + 1e-4 / max(self.rf, 1.0):
                return rf_
            rf_ *= 0.85
        return rf_

    def half_tooth(self, n_flank=24):
        """Demi-dent « moins » de la dent centrée en 0, du milieu du creux (-pas/2) au milieu de la tête
        (angle 0), sens trigonométrique."""
        rho_f = self.fillet_radius()
        arc, rho_t, ang_r = self._fillet(rho_f)
        pts = []
        a_start = -self.pitch / 2
        n_root = max(2, int(math.ceil((ang_r - a_start) / math.radians(1.5))) + 1)
        for a in np.linspace(a_start, ang_r, n_root)[:-1]:
            pts.append((self.rf * math.cos(a), self.rf * math.sin(a)))
        pts.extend(map(tuple, arc[:-1]))
        if self.rf < self.rb:
            ps = float(self.psi(self.rb))
            for rho in np.linspace(rho_t, self.rb, 4)[:-1]:
                pts.append((rho * math.cos(-ps), rho * math.sin(-ps)))
            rhos = np.linspace(self.rb, self.ra, n_flank)
        else:
            rhos = np.linspace(rho_t, self.ra, n_flank)
        pts.extend(map(tuple, self._flank_point(rhos)))
        pt = float(self.psi(self.ra))
        n_tip = max(2, int(math.ceil(pt / math.radians(1.0))) + 1)
        for a in np.linspace(-pt, 0.0, n_tip)[1:]:
            pts.append((self.ra * math.cos(a), self.ra * math.sin(a)))
        return np.array(pts)

    def tooth(self, n_flank=24):
        h = self.half_tooth(n_flank)
        mirror = h[::-1] * np.array([1.0, -1.0])
        return np.vstack([h, mirror[1:]])       # de -pas/2 à +pas/2

    def outline(self, phase=0.0, n_flank=24):
        """Contour fermé trigonométrique (sans point de fermeture répété) de la denture."""
        t = self.tooth(n_flank)[:-1]               # retire +pas/2 (== début de la dent suivante)
        out = []
        for k in range(self.z):
            a = phase + k * self.pitch
            c, s = math.cos(a), math.sin(a)
            out.append(t @ np.array([[c, s], [-s, c]]))
        pts = np.vstack(out)
        return dedupe(pts)

    def inside(self, pts, phase=0.0):
        """Test analytique « point dans la matière » (congés ignorés), points dans le repère de la roue."""
        pts = np.asarray(pts, float)
        rho = np.hypot(pts[:, 0], pts[:, 1])
        ang = np.arctan2(pts[:, 1], pts[:, 0]) - phase
        d = np.mod(ang + self.pitch / 2, self.pitch) - self.pitch / 2
        return (rho <= self.rf) | ((rho <= self.ra) & (np.abs(d) <= self.psi(np.maximum(rho, self.rb))))


def dedupe(pts, tol=1e-9):
    """Retire les points consécutifs confondus (cyclique)."""
    keep = np.ones(len(pts), bool)
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    keep[1:] = d > tol
    pts = pts[keep]
    if len(pts) > 1 and np.linalg.norm(pts[0] - pts[-1]) <= tol:
        pts = pts[:-1]
    return pts


def contact_ratio(z1, z2, m, alpha_deg=30.0):
    a = m * (z1 + z2) / 2
    al = math.radians(alpha_deg)
    g1, g2 = Involute(z1, m, alpha_deg), Involute(z2, m, alpha_deg)
    num = (math.sqrt(g1.ra ** 2 - g1.rb ** 2) + math.sqrt(g2.ra ** 2 - g2.rb ** 2) - a * math.sin(al))
    return num / (math.pi * m * math.cos(al))


def mesh_phase(phi1, beta12, z1, z2):
    """Angle de la dent 0 de la roue 2 pour qu'elle s'intercale avec la roue 1 (dent 0 en phi1)."""
    return beta12 + math.pi + math.pi / z2 - (z1 / z2) * (phi1 - beta12)


def compute_phases(spec, laws):
    """Phase (angle local de la dent 0) de chaque roue droite de la forêt des engrènements extérieurs (v1).
    Renvoie (dictionnaire des phases, liste des composantes)."""
    A0 = laws.local(0.0)
    W0 = laws.world_z(0.0, A0)
    ext = spec.external_meshes
    adj = {}
    for m in ext:
        adj.setdefault(m['driver'], []).append(m)
        adj.setdefault(m['driven'], []).append(m)

    def carrier_angle(gear, carrier):
        return W0[spec.body_of(gear)] - (W0[carrier] if carrier != 'frame' else 0.0)

    phases, comps = {}, []
    for m in ext:
        root = m['driver'] if m['driver'] not in phases else None
        if root is None or root in phases:
            continue
        phases[root] = 0.0
        comp, stack = [root], [root]
        while stack:
            g = stack.pop()
            for e in adj[g]:
                other = e['driven'] if e['driver'] == g else e['driver']
                if other in phases:
                    continue
                C = e['carrier']
                x1, y1 = spec.axis_world(spec.body_of(g))
                x2, y2 = spec.axis_world(spec.body_of(other))
                beta = math.atan2(y2 - y1, x2 - x1)
                z1, z2 = spec.gears[g]['teeth'], spec.gears[other]['teeth']
                phi1 = carrier_angle(g, C) + phases[g]
                phi2 = mesh_phase(phi1, beta, z1, z2)
                ph = phi2 - carrier_angle(other, C)
                p = TWO_PI / z2
                phases[other] = ph - p * math.floor(ph / p)
                comp.append(other)
                stack.append(other)
        comps.append(comp)
    return phases, comps
